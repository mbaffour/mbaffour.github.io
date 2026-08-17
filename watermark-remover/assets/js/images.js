/* images.js — container-level metadata removal for PNG, JPEG, WebP and GIF.
   ---------------------------------------------------------------------------
   The important design choice here: this is *surgery, not re-encoding*. We
   parse the container, drop the chunks and segments that carry metadata, and
   copy every remaining byte through untouched. The pixels that come out are
   bit-identical to the pixels that went in, which is the opposite of what you
   get from the usual "draw it to a canvas and re-export" trick — that quietly
   recompresses your image and throws away the alpha, the colour profile and
   any chance of a byte-for-byte comparison.

   What this removes: EXIF, XMP, IPTC, C2PA/JUMBF content credentials, text
   chunks (which is where Stable Diffusion writes your prompt, and where a
   number of generators write their own name), timestamps and trailing data
   appended after the end of the image.

   What this cannot remove: anything encoded in the pixels themselves. SynthID
   and its relatives live there. See the honesty note in the UI — we say so
   rather than pretending the file is clean.
   ========================================================================= */
(function (global) {
    'use strict';

    var WMR = global.WMR || (global.WMR = {});
    var B = WMR.bytes;

    /* ---------------------------------------------------------------------
       A finding is one thing we found, what we did about it, and — where we
       can read it — what it actually said.
    --------------------------------------------------------------------- */
    function finding(label, action, severity, detail, size) {
        return {
            label: label,
            action: action,          // 'removed' | 'kept' | 'noted'
            severity: severity,      // confirmed | probable | informational | likely-false-positive
            detail: detail || '',
            size: size || 0
        };
    }

    /* Does this blob look like C2PA / content credentials? */
    function looksC2PA(buf) {
        return B.indexOfBytes(buf, B.asciiBytes('c2pa'), 0) !== -1 ||
               B.indexOfBytes(buf, B.asciiBytes('jumb'), 0) !== -1 ||
               B.indexOfBytes(buf, B.asciiBytes('urn:uuid:'), 0) !== -1 &&
               B.indexOfBytes(buf, B.asciiBytes('claim'), 0) !== -1;
    }

    /* Pull anything human-readable out of a metadata blob for the report. */
    function readable(buf, max) {
        var text = B.utf8Text(buf.subarray(0, Math.min(buf.length, max || 4000)));
        var runs = text.match(/[\x20-\x7E]{6,}/g);
        if (!runs) return '';
        return B.preview(runs.slice(0, 6).join(' · '));
    }

    /* =====================================================================
       PNG
       Chunks are [len:4][type:4][data:len][crc:4]. We keep the ones that
       decode the image and drop the ones that describe it.
    ===================================================================== */
    var PNG_SIG = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A];

    // Everything a decoder needs. Anything not in here is metadata.
    var PNG_KEEP = {
        IHDR: 1, PLTE: 1, IDAT: 1, IEND: 1, tRNS: 1, gAMA: 1, cHRM: 1,
        sRGB: 1, sBIT: 1, bKGD: 1, hIST: 1, pHYs: 1, sPLT: 1,
        acTL: 1, fcTL: 1, fdAT: 1,        // APNG animation
        cICP: 1, mDCv: 1, cLLi: 1         // colour / HDR signalling
    };

    var PNG_LABELS = {
        tEXt: 'Text chunk', zTXt: 'Compressed text chunk', iTXt: 'International text chunk',
        eXIf: 'EXIF block', tIME: 'Last-modification time', caBX: 'C2PA content credentials',
        iCCP: 'Embedded ICC colour profile', dSIG: 'Digital signature', prVW: 'Embedded preview',
        orNT: 'Orientation', vpAg: 'Virtual page size'
    };

    function cleanPNG(buf, opts) {
        var findings = [], out = [], pos = 8;
        out.push(buf.subarray(0, 8));

        while (pos + 8 <= buf.length) {
            var len = (buf[pos] << 24 | buf[pos + 1] << 16 | buf[pos + 2] << 8 | buf[pos + 3]) >>> 0;
            var type = B.ascii(buf, pos + 4, 4);
            var end = pos + 12 + len;
            if (len > buf.length || end > buf.length) {
                findings.push(finding('Truncated chunk "' + type + '"', 'noted', 'informational',
                    'The file ends mid-chunk. Copied the remaining bytes unchanged.'));
                out.push(buf.subarray(pos));
                pos = buf.length;
                break;
            }
            var data = buf.subarray(pos + 8, pos + 8 + len);
            var whole = buf.subarray(pos, end);

            if (type === 'IEND') {
                out.push(whole);
                pos = end;
                // Anything after IEND is not part of the image.
                if (pos < buf.length) {
                    findings.push(finding('Trailing data after end of image', 'removed', 'confirmed',
                        B.formatBytes(buf.length - pos) + ' appended past IEND. ' + readable(buf.subarray(pos), 2000),
                        buf.length - pos));
                }
                break;
            }

            if (PNG_KEEP[type]) {
                if (type === 'iCCP' && opts.stripICC) {
                    findings.push(finding('ICC colour profile', 'removed', 'informational',
                        'Removed because "strip colour profiles" is on. Colours may shift in wide-gamut viewers.', len));
                } else {
                    out.push(whole);
                }
                pos = end;
                continue;
            }

            // Metadata chunk.
            var label = PNG_LABELS[type] || 'Ancillary chunk "' + type + '"';
            var detail = '';
            if (type === 'tEXt' || type === 'iTXt') {
                var txt = B.utf8Text(data);
                var nul = txt.indexOf('\u0000');
                var key = nul > 0 ? txt.slice(0, nul) : '';
                // tEXt is keyword\u0000value. iTXt inserts a compression flag,
                // a method byte, a language tag and a translated keyword before
                // the value, all NUL-separated — flatten the lot for the report.
                var val = nul > 0 ? txt.slice(nul + 1) : txt;
                val = val.replace(/\u0000/g, ' ').replace(/^[\u0001\s]+/, '');
                detail = (key ? key + ': ' : '') + B.preview(val);
                label = label + (key ? ' (' + key + ')' : '');
            } else if (type === 'zTXt') {
                detail = 'Keyword "' + B.utf8Text(data).split('\u0000')[0] + '", deflate-compressed.';
            } else if (type === 'eXIf') {
                detail = readable(data);
            } else if (type === 'caBX' || looksC2PA(data)) {
                label = 'C2PA content credentials';
                detail = 'Signed provenance manifest (who made this file, with what, and when).';
            }
            findings.push(finding(label, 'removed',
                type === 'tIME' ? 'informational' : 'confirmed', detail, len));
            pos = end;
        }

        return { bytes: B.concat(out), findings: findings };
    }

    /* =====================================================================
       JPEG
       Marker segments until SOS, then entropy-coded data straight to EOI.
    ===================================================================== */
    function cleanJPEG(buf, opts) {
        var findings = [], out = [], pos = 2;
        out.push(buf.subarray(0, 2));   // SOI

        while (pos + 4 <= buf.length) {
            if (buf[pos] !== 0xFF) {                       // desynced — bail out safely
                findings.push(finding('Unexpected byte where a marker was expected', 'noted', 'informational',
                    'Stopped parsing at offset ' + pos + ' and copied the rest unchanged.'));
                out.push(buf.subarray(pos));
                pos = buf.length;
                break;
            }
            var marker = buf[pos + 1];

            if (marker === 0xD8 || (marker >= 0xD0 && marker <= 0xD7) || marker === 0x01) {
                out.push(buf.subarray(pos, pos + 2));
                pos += 2;
                continue;
            }
            if (marker === 0xDA) {                          // start of scan
                var rest = buf.subarray(pos);
                out.push(rest);
                // Look for trailing bytes past EOI.
                var eoi = -1;
                for (var s = buf.length - 2; s > pos; s--) {
                    if (buf[s] === 0xFF && buf[s + 1] === 0xD9) { eoi = s + 2; break; }
                }
                if (eoi !== -1 && eoi < buf.length) {
                    var extra = buf.length - eoi;
                    if (extra > 2) {
                        findings.push(finding('Trailing data after end of image', 'removed', 'confirmed',
                            B.formatBytes(extra) + ' appended past the EOI marker. ' + readable(buf.subarray(eoi), 2000), extra));
                        out[out.length - 1] = buf.subarray(pos, eoi);
                    }
                }
                pos = buf.length;
                break;
            }

            var segLen = (buf[pos + 2] << 8) | buf[pos + 3];
            var segEnd = pos + 2 + segLen;
            if (segLen < 2 || segEnd > buf.length) {
                out.push(buf.subarray(pos));
                pos = buf.length;
                break;
            }
            var payload = buf.subarray(pos + 4, segEnd);
            var tag = B.ascii(payload, 0, 20);
            var drop = false, label = '', detail = '', severity = 'confirmed';

            if (marker === 0xE1) {                          // APP1
                if (/^Exif/.test(tag)) { drop = true; label = 'EXIF block'; detail = readable(payload); }
                else if (/^http:\/\/ns\.adobe\.com\/xap/.test(tag)) {
                    drop = true; label = 'XMP metadata'; detail = readable(payload);
                } else if (/^http:\/\/ns\.adobe\.com\/xmp\/extension/.test(tag)) {
                    drop = true; label = 'Extended XMP metadata'; detail = readable(payload);
                } else { drop = true; label = 'APP1 segment'; detail = readable(payload); }
            } else if (marker === 0xE2) {                   // APP2
                if (/^ICC_PROFILE/.test(tag)) {
                    if (opts.stripICC) {
                        drop = true; label = 'ICC colour profile'; severity = 'informational';
                        detail = 'Removed because "strip colour profiles" is on.';
                    }
                } else if (/^urn:uuid/.test(tag) || looksC2PA(payload)) {
                    drop = true; label = 'C2PA content credentials (APP2)';
                    detail = 'Signed provenance manifest.';
                } else { drop = true; label = 'APP2 segment'; detail = readable(payload); }
            } else if (marker === 0xEB) {                   // APP11 — JUMBF, where C2PA usually lives
                drop = true; label = 'C2PA / JUMBF box (APP11)';
                detail = 'Content credentials: origin, tool and edit history.';
            } else if (marker === 0xED) {                   // APP13 — Photoshop / IPTC
                drop = true; label = 'IPTC / Photoshop resource block'; detail = readable(payload);
            } else if (marker === 0xEE) {                   // APP14 — Adobe colour transform
                if (opts.stripICC) { drop = true; label = 'Adobe APP14 colour marker'; severity = 'informational'; }
            } else if (marker === 0xE0) {                   // APP0 — JFIF, structural
                drop = false;
            } else if (marker >= 0xE0 && marker <= 0xEF) {  // any other APPn
                drop = true; label = 'APP' + (marker - 0xE0) + ' segment'; detail = readable(payload);
            } else if (marker === 0xFE) {                   // COM
                drop = true; label = 'Comment segment'; detail = B.preview(B.utf8Text(payload));
            }

            if (drop) {
                findings.push(finding(label, 'removed', severity, detail, segLen));
            } else {
                out.push(buf.subarray(pos, segEnd));
            }
            pos = segEnd;
        }

        return { bytes: B.concat(out), findings: findings };
    }

    /* =====================================================================
       WebP
       RIFF container. Metadata rides in EXIF / XMP chunks, which are also
       announced by flag bits in VP8X — so dropping the chunk means clearing
       the flag too, or strict decoders complain.
    ===================================================================== */
    function cleanWebP(buf, opts) {
        var findings = [], kept = [], pos = 12;
        var hadExif = false, hadXmp = false;

        while (pos + 8 <= buf.length) {
            var fourcc = B.ascii(buf, pos, 4);
            var size = (buf[pos + 4] | (buf[pos + 5] << 8) | (buf[pos + 6] << 16) | (buf[pos + 7] << 24)) >>> 0;
            var padded = size + (size % 2);
            var end = pos + 8 + padded;
            if (end > buf.length) { end = buf.length; padded = end - pos - 8; }
            var data = buf.subarray(pos + 8, pos + 8 + Math.min(size, buf.length - pos - 8));

            if (fourcc === 'EXIF') {
                hadExif = true;
                findings.push(finding('EXIF block', 'removed', 'confirmed', readable(data), size));
            } else if (fourcc === 'XMP ') {
                hadXmp = true;
                findings.push(finding('XMP metadata', 'removed', 'confirmed', readable(data), size));
            } else if (fourcc === 'C2PA' || looksC2PA(data.subarray(0, 256))) {
                findings.push(finding('C2PA content credentials', 'removed', 'confirmed',
                    'Signed provenance manifest.', size));
            } else if (fourcc === 'ICCP' && opts.stripICC) {
                findings.push(finding('ICC colour profile', 'removed', 'informational',
                    'Removed because "strip colour profiles" is on.', size));
            } else {
                kept.push(buf.subarray(pos, end));
            }
            pos = end;
        }

        // Rebuild: clear the EXIF (0x08) and XMP (0x04) flags in VP8X.
        var body = B.concat(kept);
        if (body.length >= 8 && B.ascii(body, 0, 4) === 'VP8X' && (hadExif || hadXmp)) {
            body = body.slice();
            if (hadExif) body[8] &= ~0x08;
            if (hadXmp) body[8] &= ~0x04;
        }
        var header = new Uint8Array(12);
        header.set(B.asciiBytes('RIFF'), 0);
        var total = body.length + 4;
        header[4] = total & 0xFF; header[5] = (total >> 8) & 0xFF;
        header[6] = (total >> 16) & 0xFF; header[7] = (total >> 24) & 0xFF;
        header.set(B.asciiBytes('WEBP'), 8);

        return { bytes: B.concat([header, body]), findings: findings };
    }

    /* =====================================================================
       GIF
       Comment extensions and application extensions, except the loop block
       that actually drives the animation.
    ===================================================================== */
    function cleanGIF(buf) {
        var findings = [], out = [], pos = 0;

        // Header + logical screen descriptor + global colour table
        var gct = buf[10];
        var headerEnd = 13 + ((gct & 0x80) ? 3 * (1 << ((gct & 0x07) + 1)) : 0);
        out.push(buf.subarray(0, headerEnd));
        pos = headerEnd;

        function skipSubBlocks(p) {
            while (p < buf.length) {
                var n = buf[p];
                if (n === 0) return p + 1;
                p += 1 + n;
            }
            return buf.length;
        }
        function readSubBlocks(p) {
            var parts = [];
            while (p < buf.length) {
                var n = buf[p];
                if (n === 0) break;
                parts.push(buf.subarray(p + 1, p + 1 + n));
                p += 1 + n;
            }
            return B.concat(parts);
        }

        while (pos < buf.length) {
            var b = buf[pos];
            if (b === 0x3B) { out.push(buf.subarray(pos, pos + 1)); pos += 1; break; }   // trailer

            if (b === 0x21) {                                    // extension introducer
                var label = buf[pos + 1];
                if (label === 0xFE) {                            // comment
                    var text = B.utf8Text(readSubBlocks(pos + 2));
                    var endC = skipSubBlocks(pos + 2);
                    findings.push(finding('Comment extension', 'removed', 'confirmed',
                        B.preview(text), endC - pos));
                    pos = endC;
                    continue;
                }
                if (label === 0xFF) {                            // application extension
                    var appId = B.ascii(buf, pos + 3, 11);
                    var endA = skipSubBlocks(pos + 3 + buf[pos + 2]);
                    if (/^NETSCAPE|^ANIMEXTS/.test(appId)) {
                        out.push(buf.subarray(pos, endA));       // loop control — structural
                    } else {
                        findings.push(finding('Application extension "' + appId.trim() + '"', 'removed', 'confirmed',
                            /^XMP/.test(appId) ? 'XMP metadata embedded as a GIF application block.'
                                               : B.preview(B.utf8Text(readSubBlocks(pos + 3 + buf[pos + 2]))),
                            endA - pos));
                    }
                    pos = endA;
                    continue;
                }
                // Graphic control / plain text / anything else: structural, keep.
                // Generic: [21][label][blocksize][data…] then sub-blocks.
                var endX = skipSubBlocks(pos + 3 + buf[pos + 2]);
                out.push(buf.subarray(pos, endX));
                pos = endX;
                continue;
            }

            if (b === 0x2C) {                                    // image descriptor
                var lct = buf[pos + 9];
                var p2 = pos + 10 + ((lct & 0x80) ? 3 * (1 << ((lct & 0x07) + 1)) : 0);
                p2 += 1;                                         // LZW minimum code size
                var endI = skipSubBlocks(p2);
                out.push(buf.subarray(pos, endI));
                pos = endI;
                continue;
            }

            // Unknown byte — copy the remainder verbatim rather than guess.
            out.push(buf.subarray(pos));
            pos = buf.length;
        }

        if (pos < buf.length) {
            findings.push(finding('Trailing data after end of file', 'removed', 'confirmed',
                B.formatBytes(buf.length - pos) + ' appended past the GIF trailer.', buf.length - pos));
        }
        return { bytes: B.concat(out), findings: findings };
    }

    /* =====================================================================
       Format sniffing and dispatch
    ===================================================================== */
    function sniff(buf) {
        if (B.startsWith(buf, PNG_SIG)) return 'png';
        if (buf[0] === 0xFF && buf[1] === 0xD8) return 'jpeg';
        if (B.ascii(buf, 0, 4) === 'RIFF' && B.ascii(buf, 8, 4) === 'WEBP') return 'webp';
        if (B.ascii(buf, 0, 3) === 'GIF') return 'gif';
        if ((buf[0] === 0x49 && buf[1] === 0x49 && buf[2] === 0x2A) ||
            (buf[0] === 0x4D && buf[1] === 0x4D && buf[2] === 0x00)) return 'tiff';
        if (buf[0] === 0x42 && buf[1] === 0x4D) return 'bmp';
        return null;
    }

    function clean(buf, opts) {
        opts = opts || {};
        var kind = sniff(buf);
        switch (kind) {
            case 'png': return Object.assign({ format: 'PNG' }, cleanPNG(buf, opts));
            case 'jpeg': return Object.assign({ format: 'JPEG' }, cleanJPEG(buf, opts));
            case 'webp': return Object.assign({ format: 'WebP' }, cleanWebP(buf, opts));
            case 'gif': return Object.assign({ format: 'GIF' }, cleanGIF(buf));
            case 'tiff':
                return {
                    format: 'TIFF', bytes: buf,
                    findings: [finding('TIFF is metadata all the way down', 'noted', 'informational',
                        'In TIFF the image data is addressed through the same IFD tables that hold EXIF, so there is no ' +
                        'safe chunk to drop. Re-encode to PNG below, or use exiftool.')]
                };
            case 'bmp':
                return {
                    format: 'BMP', bytes: buf,
                    findings: [finding('BMP carries no metadata container', 'noted', 'likely-false-positive',
                        'Nothing to strip: the format has no EXIF, XMP or C2PA structure.')]
                };
            default: return null;
        }
    }

    /* Re-encode through a canvas. Destructive and lossy — offered as the
       blunt option for formats we cannot parse, and clearly labelled. */
    function reencode(blob, type, quality) {
        return new Promise(function (resolve, reject) {
            var url = URL.createObjectURL(blob);
            var img = new Image();
            img.onload = function () {
                var c = document.createElement('canvas');
                c.width = img.naturalWidth; c.height = img.naturalHeight;
                c.getContext('2d').drawImage(img, 0, 0);
                c.toBlob(function (out) {
                    URL.revokeObjectURL(url);
                    out ? resolve(out) : reject(new Error('Canvas export failed.'));
                }, type || 'image/png', quality || 0.92);
            };
            img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('Could not decode this image.')); };
            img.src = url;
        });
    }

    WMR.images = { clean: clean, sniff: sniff, reencode: reencode, finding: finding, readable: readable };
})(typeof window !== 'undefined' ? window : globalThis);
