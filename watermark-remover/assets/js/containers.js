/* containers.js — ZIP-backed documents (DOCX, PPTX, XLSX, EPUB, ODT) and SVG.
   ---------------------------------------------------------------------------
   Office documents and EPUBs are ZIP archives of XML. The identifying material
   is in three places: the property parts (who wrote it, on what, for how long,
   in how many revisions), the ZIP directory itself (a modification timestamp
   per entry, which survives every "remove personal information" button I have
   tried), and the document body, where invisible characters travel exactly as
   they do in plain text.

   Deflate comes from the platform — DecompressionStream/CompressionStream are
   in every current browser — so this file adds no dependency to unzip and
   rezip a document. Where the platform lacks them we fall back to storing
   entries uncompressed, which produces a larger but perfectly valid file.
   ========================================================================= */
(function (global) {
    'use strict';

    var WMR = global.WMR || (global.WMR = {});
    var B = WMR.bytes;
    var f = WMR.images.finding;

    var HAS_DEFLATE = (typeof CompressionStream !== 'undefined') &&
                      (typeof DecompressionStream !== 'undefined');

    /* =====================================================================
       ZIP reading
    ===================================================================== */
    function u16(b, o) { return b[o] | (b[o + 1] << 8); }
    function u32(b, o) { return ((b[o] | (b[o + 1] << 8) | (b[o + 2] << 16)) + (b[o + 3] * 0x1000000)); }

    function readZip(buf) {
        // End-of-central-directory, searching back over the optional comment.
        var eocd = -1;
        for (var i = buf.length - 22; i >= 0 && i > buf.length - 22 - 65536; i--) {
            if (buf[i] === 0x50 && buf[i + 1] === 0x4B && buf[i + 2] === 0x05 && buf[i + 3] === 0x06) { eocd = i; break; }
        }
        if (eocd === -1) throw new Error('Not a ZIP archive (no end-of-central-directory record).');

        var count = u16(buf, eocd + 10);
        var cdOffset = u32(buf, eocd + 16);
        if (cdOffset === 0xFFFFFFFF || u16(buf, eocd + 8) === 0xFFFF) throw new Error('ZIP64 archives are not supported.');

        var entries = [], p = cdOffset;
        for (var n = 0; n < count && p + 46 <= buf.length; n++) {
            if (!(buf[p] === 0x50 && buf[p + 1] === 0x4B && buf[p + 2] === 0x01 && buf[p + 3] === 0x02)) break;
            var flags = u16(buf, p + 8);
            var method = u16(buf, p + 10);
            var time = u16(buf, p + 12), date = u16(buf, p + 14);
            var crc = u32(buf, p + 16);
            var csize = u32(buf, p + 20), usize = u32(buf, p + 24);
            var nameLen = u16(buf, p + 28), extraLen = u16(buf, p + 30), commentLen = u16(buf, p + 32);
            var localAt = u32(buf, p + 42);
            var name = B.utf8Text(buf.subarray(p + 46, p + 46 + nameLen));

            // Local header tells us where the payload actually starts.
            var lNameLen = u16(buf, localAt + 26), lExtraLen = u16(buf, localAt + 28);
            var dataAt = localAt + 30 + lNameLen + lExtraLen;

            entries.push({
                name: name, method: method, flags: flags, time: time, date: date,
                crc: crc, csize: csize, usize: usize,
                data: buf.subarray(dataAt, dataAt + csize)
            });
            p += 46 + nameLen + extraLen + commentLen;
        }
        return entries;
    }

    function inflate(entry) {
        if (entry.method === 0) return Promise.resolve(entry.data.slice());
        if (entry.method !== 8) return Promise.reject(new Error('Unsupported compression method ' + entry.method));
        if (!HAS_DEFLATE) return Promise.reject(new Error('This browser has no DecompressionStream.'));
        var stream = new Response(entry.data).body.pipeThrough(new DecompressionStream('deflate-raw'));
        return new Response(stream).arrayBuffer().then(function (ab) { return new Uint8Array(ab); });
    }

    function deflate(bytes) {
        if (!HAS_DEFLATE) return Promise.resolve(null);
        var stream = new Response(bytes).body.pipeThrough(new CompressionStream('deflate-raw'));
        return new Response(stream).arrayBuffer().then(function (ab) { return new Uint8Array(ab); });
    }

    /* =====================================================================
       ZIP writing
    ===================================================================== */
    function writeZip(items) {
        // items: [{name, bytes, store:bool, time, date}]
        var chunks = [], central = [], offset = 0;

        items.forEach(function (it) {
            var nameBytes = B.utf8Bytes(it.name);
            var payload = it.store ? it.bytes : (it.deflated || it.bytes);
            var method = (it.store || !it.deflated) ? 0 : 8;
            var crc = B.crc32(it.bytes);
            var utf8Flag = /[^\x20-\x7E]/.test(it.name) ? 0x800 : 0;

            var lh = new Uint8Array(30);
            var dv = new DataView(lh.buffer);
            dv.setUint32(0, 0x04034b50, true);
            dv.setUint16(4, 20, true);
            dv.setUint16(6, utf8Flag, true);
            dv.setUint16(8, method, true);
            dv.setUint16(10, it.time, true);
            dv.setUint16(12, it.date, true);
            dv.setUint32(14, crc, true);
            dv.setUint32(18, payload.length, true);
            dv.setUint32(22, it.bytes.length, true);
            dv.setUint16(26, nameBytes.length, true);
            dv.setUint16(28, 0, true);

            chunks.push(lh, nameBytes, payload);

            var cd = new Uint8Array(46);
            var cv = new DataView(cd.buffer);
            cv.setUint32(0, 0x02014b50, true);
            cv.setUint16(4, 20, true);
            cv.setUint16(6, 20, true);
            cv.setUint16(8, utf8Flag, true);
            cv.setUint16(10, method, true);
            cv.setUint16(12, it.time, true);
            cv.setUint16(14, it.date, true);
            cv.setUint32(16, crc, true);
            cv.setUint32(20, payload.length, true);
            cv.setUint32(24, it.bytes.length, true);
            cv.setUint16(28, nameBytes.length, true);
            cv.setUint16(30, 0, true);
            cv.setUint16(32, 0, true);
            cv.setUint16(34, 0, true);
            cv.setUint16(36, 0, true);
            cv.setUint32(38, 0, true);
            cv.setUint32(42, offset, true);
            central.push(cd, nameBytes);

            offset += lh.length + nameBytes.length + payload.length;
        });

        var cdBytes = B.concat(central);
        var eocd = new Uint8Array(22);
        var ev = new DataView(eocd.buffer);
        ev.setUint32(0, 0x06054b50, true);
        ev.setUint16(8, items.length, true);
        ev.setUint16(10, items.length, true);
        ev.setUint32(12, cdBytes.length, true);
        ev.setUint32(16, offset, true);
        return B.concat([B.concat(chunks), cdBytes, eocd]);
    }

    /* A tiny public helper: bundle finished files into a stored (uncompressed)
       ZIP so "download everything" is one click and no library. */
    function bundle(files) {
        return writeZip(files.map(function (x) {
            return { name: x.name, bytes: x.bytes, store: true, time: 0, date: 0x21 };
        }));
    }

    /* =====================================================================
       XML property scrubbing
    ===================================================================== */
    function blankTags(xml, tags, report, partName) {
        tags.forEach(function (tag) {
            var re = new RegExp('<((?:[\\w.-]+:)?' + tag + ')(\\s[^>]*)?>([\\s\\S]*?)</\\1>', 'g');
            xml = xml.replace(re, function (whole, name, attrs, inner) {
                if (!inner.trim()) return whole;
                report.push(f(partName + ' · <' + name + '>', 'removed', 'confirmed', B.preview(inner), inner.length));
                return '<' + name + (attrs || '') + '></' + name + '>';
            });
        });
        return xml;
    }

    function blankSelfClosingMeta(xml, attrPairs, report, partName) {
        // ODT-style <meta:generator>, <dc:date> handled above; this covers
        // attribute-carried values such as meta:editing-cycles.
        attrPairs.forEach(function (attr) {
            var re = new RegExp('(' + attr + '=")([^"]*)(")', 'g');
            xml = xml.replace(re, function (whole, a, val, c) {
                if (!val) return whole;
                report.push(f(partName + ' · ' + attr, 'removed', 'confirmed', B.preview(val), val.length));
                return a + c;
            });
        });
        return xml;
    }

    /* Which parts get which treatment. Keyed by exact name or a matcher. */
    var OOXML_CORE = ['creator', 'lastModifiedBy', 'lastPrinted', 'revision',
                      'created', 'modified', 'category', 'keywords', 'description',
                      'contentStatus', 'identifier', 'language', 'version'];
    var OOXML_APP = ['Company', 'Manager', 'Application', 'AppVersion', 'Template',
                     'TotalTime', 'LastAuthor', 'HyperlinkBase'];
    var ODT_META = ['initial-creator', 'creator', 'creation-date', 'date', 'generator',
                    'editing-cycles', 'editing-duration', 'printed-by', 'print-date'];

    function isBodyPart(name) {
        return /^word\/(document|header\d*|footer\d*|footnotes|endnotes|comments)\.xml$/.test(name) ||
               /^ppt\/(slides|notesSlides)\/[^/]+\.xml$/.test(name) ||
               /^xl\/(sharedStrings|comments\d*)\.xml$/.test(name) ||
               /^content\.xml$/.test(name) ||
               /\.(xhtml|html|htm|opf|ncx)$/i.test(name) ||
               /^OEBPS\/.*\.(xhtml|html)$/i.test(name);
    }

    function kindOf(entries) {
        var names = entries.map(function (e) { return e.name; });
        if (names.indexOf('word/document.xml') !== -1) return { label: 'Word document (DOCX)', family: 'ooxml' };
        if (names.some(function (n) { return /^ppt\/presentation\.xml$/.test(n); })) return { label: 'PowerPoint deck (PPTX)', family: 'ooxml' };
        if (names.some(function (n) { return /^xl\/workbook\.xml$/.test(n); })) return { label: 'Excel workbook (XLSX)', family: 'ooxml' };
        if (names.indexOf('mimetype') !== -1 && names.some(function (n) { return /\.opf$/.test(n); })) return { label: 'EPUB book', family: 'epub' };
        if (names.indexOf('meta.xml') !== -1 || names.indexOf('content.xml') !== -1) return { label: 'OpenDocument file', family: 'odf' };
        return { label: 'ZIP archive', family: 'zip' };
    }

    /* =====================================================================
       clean(buf, opts) — async because inflate/deflate are streams.
    ===================================================================== */
    function clean(buf, opts) {
        opts = opts || {};
        var textOpts = opts.text || {};
        var entries;
        try { entries = readZip(buf); }
        catch (e) {
            return Promise.resolve({ format: 'ZIP', bytes: buf, findings: [f('Could not read archive', 'noted', 'informational', e.message)] });
        }

        var kind = kindOf(entries);
        var findings = [];
        var dropped = {};

        // docProps/custom.xml is pure user-defined metadata — drop the part
        // outright, then unhook it from the content types and relationships.
        var hasCustom = entries.some(function (e) { return e.name === 'docProps/custom.xml'; });
        if (hasCustom && kind.family === 'ooxml') {
            dropped['docProps/custom.xml'] = true;
            findings.push(f('docProps/custom.xml', 'removed', 'confirmed',
                'Custom document properties removed in full, along with its content-type override and relationship.'));
        }

        var jobs = entries.map(function (entry) {
            if (dropped[entry.name]) return Promise.resolve(null);
            return inflate(entry).then(function (raw) {
                var name = entry.name;
                var text = null, changed = false;

                function asText() {
                    if (text === null) text = B.utf8Text(raw);
                    return text;
                }

                if (kind.family === 'ooxml' && name === 'docProps/core.xml') {
                    var before = asText();
                    text = blankTags(before, OOXML_CORE, findings, 'core.xml');
                    changed = text !== before;
                } else if (kind.family === 'ooxml' && name === 'docProps/app.xml') {
                    var beforeA = asText();
                    text = blankTags(beforeA, OOXML_APP, findings, 'app.xml');
                    changed = text !== beforeA;
                } else if (kind.family === 'odf' && name === 'meta.xml') {
                    var beforeM = asText();
                    text = blankTags(beforeM, ODT_META, findings, 'meta.xml');
                    text = blankSelfClosingMeta(text, ['meta:editing-cycles', 'meta:name'], findings, 'meta.xml');
                    changed = text !== beforeM;
                } else if (kind.family === 'ooxml' && name === '[Content_Types].xml' && hasCustom) {
                    text = asText().replace(/<Override[^>]*docProps\/custom\.xml[^>]*\/>/g, '');
                    changed = true;
                } else if (kind.family === 'ooxml' && name === '_rels/.rels' && hasCustom) {
                    text = asText().replace(/<Relationship[^>]*Target="docProps\/custom\.xml"[^>]*\/>/g, '');
                    changed = true;
                } else if (kind.family === 'epub' && /\.opf$/.test(name)) {
                    // The author and title of a book are content, not a mark.
                    // Only the packaging tool's fingerprints come out.
                    var beforeO = asText();
                    text = beforeO.replace(/<meta[^>]*(?:property="dcterms:modified"|name="calibre:timestamp")[^>]*>[\s\S]*?(?:<\/meta>|)/g, function (m) {
                        findings.push(f('OPF packaging timestamp', 'removed', 'informational', B.preview(m), m.length));
                        return '';
                    });
                    text = text.replace(/<dc:contributor[^>]*>([\s\S]*?)<\/dc:contributor>/g, function (m, inner) {
                        findings.push(f('OPF contributor (packaging tool)', 'removed', 'confirmed', B.preview(inner), inner.length));
                        return '';
                    });
                    changed = text !== beforeO;
                    findings.push(f('OPF title and author kept', 'kept', 'likely-false-positive',
                        'dc:title and dc:creator describe the book, not the file. Left in place.'));
                }

                // Invisible-character sweep across every body part.
                if (isBodyPart(name) && opts.cleanBodyText !== false) {
                    var body = text === null ? asText() : text;
                    var res = WMR.text.scan(body, textOpts);
                    if (res.stats.changed > 0) {
                        text = res.cleaned;
                        changed = true;
                        res.findings.filter(function (x) { return x.action !== 'kept'; }).forEach(function (x) {
                            findings.push(f(name + ' · ' + x.code + ' ' + x.name, x.action, x.severity,
                                x.count + '×' + (x.replacement ? ' → ' + JSON.stringify(x.replacement) : ''), x.count));
                        });
                        res.payloads.forEach(function (p) {
                            findings.push(f('Hidden payload in ' + name, 'removed', 'confirmed',
                                p.kind + ': “' + B.preview(p.decoded, 160) + '”', p.chars));
                        });
                    }
                }

                var outBytes = changed ? B.utf8Bytes(text) : raw;
                return {
                    name: name,
                    bytes: outBytes,
                    store: name === 'mimetype',        // EPUB requires this stored & first
                    time: opts.normalizeTimestamps === false ? entry.time : 0,
                    date: opts.normalizeTimestamps === false ? entry.date : 0x21   // 1980-01-01
                };
            }).catch(function (err) {
                findings.push(f('Could not process ' + entry.name, 'noted', 'informational', err.message));
                return null;
            });
        });

        return Promise.all(jobs).then(function (items) {
            items = items.filter(Boolean);
            if (opts.normalizeTimestamps !== false) {
                var stamped = entries.filter(function (e) { return e.time || e.date !== 0x21; }).length;
                if (stamped) {
                    findings.push(f('ZIP entry timestamps', 'removed', 'probable',
                        stamped + ' entr' + (stamped === 1 ? 'y' : 'ies') + ' carried a modification date and time. ' +
                        'Normalised to 1980-01-01, which is what reproducible builds use.', stamped));
                }
            }
            // Compress everything we can; store what we cannot.
            return Promise.all(items.map(function (it) {
                if (it.store) return Promise.resolve(it);
                return deflate(it.bytes).then(function (d) {
                    if (d && d.length < it.bytes.length) it.deflated = d;
                    return it;
                }).catch(function () { return it; });
            })).then(function (ready) {
                if (!findings.length) {
                    findings.push(f('No document metadata found', 'noted', 'likely-false-positive',
                        'No property parts, timestamps or invisible characters to remove.'));
                }
                return { format: kind.label, bytes: writeZip(ready), findings: findings };
            });
        });
    }

    /* =====================================================================
       SVG — an XML text format, so it gets the text pass plus its own
       metadata elements.
    ===================================================================== */
    function cleanSVG(text, opts) {
        var findings = [];
        var out = text;

        out = out.replace(/<metadata[\s\S]*?<\/metadata>/gi, function (m) {
            findings.push(f('<metadata> block', 'removed', 'confirmed', B.preview(m), m.length));
            return '';
        });
        out = out.replace(/<!--[\s\S]*?-->/g, function (m) {
            findings.push(f('XML comment', 'removed', 'probable', B.preview(m), m.length));
            return '';
        });
        out = out.replace(/<desc>[\s\S]*?<\/desc>/gi, function (m) {
            findings.push(f('<desc> element', 'removed', 'informational', B.preview(m), m.length));
            return '';
        });
        // Editor bookkeeping attributes and namespaces.
        out = out.replace(/\s(?:inkscape|sodipodi|xmlns:inkscape|xmlns:sodipodi|xmlns:dc|xmlns:cc|xmlns:rdf):[\w.-]+="[^"]*"/g, function (m) {
            findings.push(f('Editor attribute', 'removed', 'informational', B.preview(m.trim(), 90), m.length));
            return '';
        });

        var res = WMR.text.scan(out, opts || {});
        out = res.cleaned;
        res.findings.filter(function (x) { return x.action !== 'kept'; }).forEach(function (x) {
            findings.push(f(x.code + ' ' + x.name, x.action, x.severity, x.count + '×', x.count));
        });

        if (!findings.length) findings.push(f('No SVG metadata found', 'noted', 'likely-false-positive', ''));
        return { format: 'SVG', text: out, findings: findings, payloads: res.payloads };
    }

    WMR.containers = {
        clean: clean,
        cleanSVG: cleanSVG,
        bundle: bundle,
        readZip: readZip,
        writeZip: writeZip,
        hasDeflate: HAS_DEFLATE
    };
})(typeof window !== 'undefined' ? window : globalThis);
