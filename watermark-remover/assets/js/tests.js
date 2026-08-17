/* tests.js — assertions for every rule that has a right answer.
   Runs in the browser (tests.html) and under Node (tests.node.js), so the
   claims the UI makes about behaviour are checkable rather than asserted.
   ========================================================================= */
(function (global) {
    'use strict';

    var WMR = global.WMR;
    var B = WMR.bytes;
    var T = [];

    function test(name, fn) { T.push({ name: name, fn: fn }); }
    function eq(actual, expected, what) {
        if (actual !== expected) {
            throw new Error((what || 'value') + ': expected ' + JSON.stringify(expected) +
                ', got ' + JSON.stringify(actual));
        }
    }
    function ok(cond, what) { if (!cond) throw new Error(what || 'expected truthy'); }

    var ZWSP = '\u200B', ZWNJ = '\u200C', ZWJ = '\u200D', NBSP = '\u00A0';
    var RLO = '\u202E', POP = '\u202C', FE0F = '\uFE0F';

    function tagged(s) {
        return s.split('').map(function (c) { return String.fromCodePoint(0xE0000 + c.charCodeAt(0)); }).join('');
    }
    function vsBytes(s) {
        return Array.from(B.utf8Bytes(s)).map(function (b) {
            return b < 16 ? String.fromCodePoint(0xFE00 + b) : String.fromCodePoint(0xE0100 + b - 16);
        }).join('');
    }
    function zwBits(s) {
        var bits = '';
        for (var i = 0; i < s.length; i++) {
            var b = s.charCodeAt(i).toString(2);
            while (b.length < 8) b = '0' + b;
            bits += b;
        }
        return bits.split('').map(function (x) { return x === '0' ? ZWSP : ZWNJ; }).join('');
    }

    /* =================================================== Layer A — text */

    test('zero-width space is removed', function () {
        var r = WMR.text.scan('he' + ZWSP + 'llo');
        eq(r.cleaned, 'hello', 'cleaned');
        eq(r.stats.changed, 1, 'change count');
    });

    test('a zero-width joiner inside an emoji sequence is kept', function () {
        var family = '\u{1F468}' + ZWJ + '\u{1F469}' + ZWJ + '\u{1F467}';
        var r = WMR.text.scan('family ' + family);
        eq(r.cleaned, 'family ' + family, 'emoji survives intact');
        ok(r.findings.some(function (f) { return f.action === 'kept' && f.cp === 0x200D; }), 'reported as kept');
    });

    test('a zero-width joiner between Latin letters is removed', function () {
        var r = WMR.text.scan('mar' + ZWJ + 'gin');
        eq(r.cleaned, 'margin', 'cleaned');
    });

    test('a regional flag emoji built from tag characters survives', function () {
        var scotland = '\u{1F3F4}' + tagged('gbsct') + '\u{E007F}';
        var r = WMR.text.scan('flag ' + scotland);
        eq(r.cleaned, 'flag ' + scotland, 'flag intact');
    });

    test('tag characters are removed and their payload decoded', function () {
        var r = WMR.text.scan('Report' + tagged('doc-id:7741') + ' attached.');
        eq(r.cleaned, 'Report attached.', 'cleaned');
        eq(r.payloads.length, 1, 'payload count');
        eq(r.payloads[0].decoded, 'doc-id:7741', 'decoded payload');
    });

    test('emoji presentation selector is kept, a run of selectors is decoded', function () {
        var kept = WMR.text.scan('warning \u26A0' + FE0F);
        eq(kept.cleaned, 'warning \u26A0' + FE0F, 'FE0F after a pictograph is kept');

        var hidden = WMR.text.scan('Friday' + vsBytes('MBA'));
        eq(hidden.cleaned, 'Friday', 'selector run removed');
        eq(hidden.payloads[0].decoded, 'MBA', 'decoded selector payload');
    });

    test('zero-width binary is decoded', function () {
        var r = WMR.text.scan('Regards,' + zwBits('traced'));
        eq(r.cleaned, 'Regards,', 'cleaned');
        eq(r.payloads.length, 1, 'payload count');
        eq(r.payloads[0].decoded, 'traced', 'decoded bits');
    });

    test('a homoglyph inside a Latin word is folded', function () {
        var r = WMR.text.scan('rep\u043Ert');           // Cyrillic o
        eq(r.cleaned, 'report', 'folded to Latin');
    });

    test('a word entirely in another script is left alone', function () {
        var word = '\u043E\u043F\u0435\u0440\u0430\u0442\u043E\u0440';   // 'operator' in Russian
        var r = WMR.text.scan('the word ' + word);
        eq(r.cleaned, 'the word ' + word, 'Russian untouched');
    });

    test('exotic spaces normalise, but ideographic space survives in CJK', function () {
        eq(WMR.text.scan('a' + NBSP + 'b').cleaned, 'a b', 'NBSP');
        var cjk = '\u65E5\u672C\u8A9E\u3000\u30C6\u30B9\u30C8';   // CJK with an ideographic space
        eq(WMR.text.scan(cjk).cleaned, cjk, 'U+3000 kept in CJK');
        eq(WMR.text.scan('a\u3000b').cleaned, 'a b', 'U+3000 normalised outside CJK');
    });

    test('bidi overrides are removed', function () {
        var r = WMR.text.scan('safe ' + RLO + 'reversed' + POP + ' end');
        eq(r.cleaned, 'safe reversed end', 'cleaned');
    });

    test('styled letterforms fold to plain when the rule is on', function () {
        var styled = '\u{1D400}\u{1D401}';               // 𝐀𝐁
        eq(WMR.text.scan(styled, { compat: true }).cleaned, 'AB', 'folded');
        eq(WMR.text.scan(styled, { compat: false }).cleaned, styled, 'left alone when off');
    });

    test('typography rewriting is off unless asked for', function () {
        var s = '\u201Cquoted\u201D \u2014 yes\u2026';
        eq(WMR.text.scan(s).cleaned, s, 'default leaves style alone');
        eq(WMR.text.scan(s, { typography: true }).cleaned, '"quoted" - yes...', 'on request');
    });

    test('cleaning is idempotent', function () {
        var dirty = 'a' + ZWSP + 'b' + tagged('x') + NBSP + 'c' + RLO + 'd';
        var once = WMR.text.scan(dirty).cleaned;
        var twice = WMR.text.scan(once).cleaned;
        eq(twice, once, 'second pass is a no-op');
        eq(WMR.text.scan(once).stats.changed, 0, 'nothing left to find');
    });

    test('clean text produces no findings', function () {
        var r = WMR.text.scan('Perfectly ordinary sentence, with punctuation!');
        eq(r.stats.changed, 0, 'changes');
        eq(r.payloads.length, 0, 'payloads');
    });

    test('disabling a rule reports the finding but keeps the character', function () {
        var r = WMR.text.scan('he' + ZWSP + 'llo', { invisible: false });
        eq(r.cleaned, 'he' + ZWSP + 'llo', 'unchanged');
        ok(r.findings.some(function (f) { return f.action === 'kept'; }), 'still reported');
    });

    /* ================================================== images — PNG */

    function pngChunk(type, data) {
        var len = data.length;
        var out = new Uint8Array(12 + len);
        out[0] = (len >>> 24) & 255; out[1] = (len >>> 16) & 255;
        out[2] = (len >>> 8) & 255; out[3] = len & 255;
        out.set(B.asciiBytes(type), 4);
        out.set(data, 8);
        var crc = B.crc32(out.subarray(4, 8 + len));
        out[8 + len] = (crc >>> 24) & 255; out[9 + len] = (crc >>> 16) & 255;
        out[10 + len] = (crc >>> 8) & 255; out[11 + len] = crc & 255;
        return out;
    }

    function makePNG(extra) {
        var sig = new Uint8Array([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
        var ihdr = pngChunk('IHDR', new Uint8Array([0, 0, 0, 1, 0, 0, 0, 1, 8, 6, 0, 0, 0]));
        var idat = pngChunk('IDAT', new Uint8Array([0x78, 0x9C, 0x63, 0x00, 0x00, 0x00, 0x02, 0x00, 0x01]));
        var iend = pngChunk('IEND', new Uint8Array(0));
        return B.concat([sig, ihdr].concat(extra || []).concat([idat, iend]));
    }

    test('PNG text chunks are removed and the image data is byte-identical', function () {
        var text = pngChunk('tEXt', B.concat([B.asciiBytes('parameters'), new Uint8Array([0]),
            B.asciiBytes('a photo of an astronaut, seed 1234')]));
        var dirty = makePNG([text]);
        var clean = makePNG([]);
        var res = WMR.images.clean(dirty, {});
        eq(res.format, 'PNG', 'format');
        eq(res.bytes.length, clean.length, 'output size matches a chunk-free build');
        for (var i = 0; i < clean.length; i++) eq(res.bytes[i], clean[i], 'byte ' + i);
        ok(/parameters/.test(res.findings[0].label + res.findings[0].detail), 'keyword reported');
        ok(/astronaut/.test(res.findings[0].detail), 'value reported');
    });

    test('PNG data appended after IEND is removed', function () {
        var dirty = B.concat([makePNG([]), B.asciiBytes('TRACKINGID=abc123')]);
        var res = WMR.images.clean(dirty, {});
        eq(res.bytes.length, makePNG([]).length, 'trailing bytes gone');
        ok(res.findings.some(function (f) { return /Trailing data/.test(f.label); }), 'reported');
    });

    test('PNG colour chunks survive unless asked otherwise', function () {
        var srgb = pngChunk('sRGB', new Uint8Array([0]));
        var res = WMR.images.clean(makePNG([srgb]), {});
        eq(res.bytes.length, makePNG([srgb]).length, 'sRGB kept');
    });

    /* ================================================== images — JPEG */

    function jpegSegment(marker, payload) {
        var len = payload.length + 2;
        return B.concat([new Uint8Array([0xFF, marker, (len >> 8) & 255, len & 255]), payload]);
    }

    function makeJPEG(segments) {
        var soi = new Uint8Array([0xFF, 0xD8]);
        var jfif = jpegSegment(0xE0, B.concat([B.asciiBytes('JFIF'), new Uint8Array([0, 1, 1, 0, 0, 1, 0, 1, 0, 0])]));
        var sos = new Uint8Array([0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00]);
        var scan = new Uint8Array([0x12, 0x34, 0x56]);
        var eoi = new Uint8Array([0xFF, 0xD9]);
        return B.concat([soi, jfif].concat(segments || []).concat([sos, scan, eoi]));
    }

    test('JPEG EXIF and comment segments are removed, JFIF and scan data are not', function () {
        var exif = jpegSegment(0xE1, B.concat([B.asciiBytes('Exif'), new Uint8Array([0, 0]),
            B.asciiBytes('MM\0*\0\0\0\bCanon EOS 5D')]));
        var comment = jpegSegment(0xFE, B.asciiBytes('made with something'));
        var res = WMR.images.clean(makeJPEG([exif, comment]), {});
        eq(res.format, 'JPEG', 'format');
        var expected = makeJPEG([]);
        eq(res.bytes.length, expected.length, 'size');
        for (var i = 0; i < expected.length; i++) eq(res.bytes[i], expected[i], 'byte ' + i);
        eq(res.findings.length, 2, 'two findings');
    });

    test('JPEG ICC profile is kept by default and removed on request', function () {
        var icc = jpegSegment(0xE2, B.concat([B.asciiBytes('ICC_PROFILE'), new Uint8Array([0, 1, 1]), new Uint8Array(16)]));
        eq(WMR.images.clean(makeJPEG([icc]), {}).bytes.length, makeJPEG([icc]).length, 'kept by default');
        eq(WMR.images.clean(makeJPEG([icc]), { stripICC: true }).bytes.length, makeJPEG([]).length, 'removed on request');
    });

    test('JPEG data appended after EOI is removed', function () {
        var dirty = B.concat([makeJPEG([]), B.asciiBytes('appended payload here')]);
        var res = WMR.images.clean(dirty, {});
        eq(res.bytes.length, makeJPEG([]).length, 'trailing bytes gone');
    });

    /* ================================================== images — WebP */

    function riffChunk(fourcc, data) {
        var pad = data.length % 2;
        var out = new Uint8Array(8 + data.length + pad);
        out.set(B.asciiBytes(fourcc), 0);
        var n = data.length;
        out[4] = n & 255; out[5] = (n >> 8) & 255; out[6] = (n >> 16) & 255; out[7] = (n >>> 24) & 255;
        out.set(data, 8);
        return out;
    }

    function makeWebP(extra) {
        var vp8x = riffChunk('VP8X', new Uint8Array([0x0C, 0, 0, 0, 0, 0, 0, 0, 0, 0]));  // EXIF+XMP flags set
        var vp8 = riffChunk('VP8 ', new Uint8Array([1, 2, 3, 4]));
        var body = B.concat([vp8x].concat(extra || []).concat([vp8]));
        var header = new Uint8Array(12);
        header.set(B.asciiBytes('RIFF'), 0);
        var total = body.length + 4;
        header[4] = total & 255; header[5] = (total >> 8) & 255;
        header[6] = (total >> 16) & 255; header[7] = (total >>> 24) & 255;
        header.set(B.asciiBytes('WEBP'), 8);
        return B.concat([header, body]);
    }

    test('WebP EXIF and XMP chunks are removed and the VP8X flags cleared', function () {
        var exif = riffChunk('EXIF', B.asciiBytes('MM\0*camera model'));
        var xmp = riffChunk('XMP ', B.asciiBytes('<x:xmpmeta>author</x:xmpmeta>'));
        var res = WMR.images.clean(makeWebP([exif, xmp]), {});
        eq(res.format, 'WebP', 'format');
        eq(B.ascii(res.bytes, 8, 4), 'WEBP', 'still a WebP');
        eq(res.bytes[20] & 0x0C, 0, 'EXIF and XMP flag bits cleared');
        // RIFF size field must match the new body length.
        var declared = res.bytes[4] | (res.bytes[5] << 8) | (res.bytes[6] << 16) | (res.bytes[7] * 0x1000000);
        eq(declared, res.bytes.length - 8, 'RIFF size field');
        eq(res.findings.length, 2, 'two findings');
    });

    /* =================================================== images — GIF */

    function makeGIF(extra) {
        var header = B.concat([B.asciiBytes('GIF89a'), new Uint8Array([1, 0, 1, 0, 0x80, 0, 0]),
            new Uint8Array([0, 0, 0, 255, 255, 255])]);                       // 2-colour GCT
        var loop = new Uint8Array([0x21, 0xFF, 0x0B]);
        loop = B.concat([loop, B.asciiBytes('NETSCAPE2.0'), new Uint8Array([0x03, 0x01, 0x00, 0x00, 0x00])]);
        var image = new Uint8Array([0x2C, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0x02, 0x02, 0x44, 0x01, 0x00]);
        var trailer = new Uint8Array([0x3B]);
        return B.concat([header, loop].concat(extra || []).concat([image, trailer]));
    }

    test('GIF comment blocks go, the animation loop block stays', function () {
        var body = B.asciiBytes('made by tool');
        var comment = B.concat([new Uint8Array([0x21, 0xFE, body.length]), body, new Uint8Array([0])]);
        var res = WMR.images.clean(makeGIF([comment]), {});
        eq(res.format, 'GIF', 'format');
        eq(res.bytes.length, makeGIF([]).length, 'comment removed, nothing else');
        ok(B.indexOfBytes(res.bytes, B.asciiBytes('NETSCAPE2.0'), 0) !== -1, 'loop block kept');
        ok(B.indexOfBytes(res.bytes, B.asciiBytes('made by tool'), 0) === -1, 'comment gone');
    });

    /* ========================================================== PDF */

    function makePDF(author) {
        var body =
            '%PDF-1.4\n' +
            '1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n' +
            '2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\n' +
            '3 0 obj\n<< /Title (Quarterly figures) /Author (' + author + ') /Producer (SomeWriter 4.2) >>\nendobj\n' +
            'trailer\n<< /Size 4 /Root 1 0 R /Info 3 0 R /ID [<ABCDEF0123456789><ABCDEF0123456789>] >>\n' +
            '%%EOF\n';
        return B.asciiBytes(body);
    }

    test('PDF Info strings are blanked without changing the file length', function () {
        var input = makePDF('Michael Baffour Awuah');
        var res = WMR.pdf.clean(input, { pdfClearId: true });
        eq(res.bytes.length, input.length, 'length preserved');
        var text = B.ascii(res.bytes, 0, res.bytes.length);
        ok(text.indexOf('Michael Baffour Awuah') === -1, 'author gone');
        ok(text.indexOf('Quarterly figures') === -1, 'title gone');
        ok(text.indexOf('SomeWriter 4.2') === -1, 'producer gone');
        ok(text.indexOf('/Author (') !== -1, 'dictionary structure intact');
        ok(text.indexOf('ABCDEF0123456789') === -1, 'document ID zeroed');
        ok(res.findings.some(function (f) { return /author/i.test(f.label); }), 'author reported');
    });

    test('PDF XMP packets are blanked in place', function () {
        var xmp = '<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>' +
            '<x:xmpmeta><rdf:RDF><xmp:CreatorTool>Acme Writer</xmp:CreatorTool></rdf:RDF></x:xmpmeta>' +
            '<?xpacket end="w"?>';
        var input = B.concat([B.asciiBytes('%PDF-1.4\n'), B.asciiBytes(xmp), B.asciiBytes('\n%%EOF\n')]);
        var res = WMR.pdf.clean(input, {});
        eq(res.bytes.length, input.length, 'length preserved');
        var text = B.ascii(res.bytes, 0, res.bytes.length);
        ok(text.indexOf('Acme Writer') === -1, 'creator tool gone');
        ok(text.indexOf('<?xpacket begin') !== -1, 'packet markers left in place');
        ok(res.findings.some(function (f) { return /Acme Writer/.test(f.detail); }), 'value reported before removal');
    });

    test('an encrypted PDF is refused rather than corrupted', function () {
        var input = B.asciiBytes('%PDF-1.4\ntrailer\n<< /Encrypt 9 0 R /Info 3 0 R >>\n%%EOF\n');
        var res = WMR.pdf.clean(input, {});
        eq(res.bytes.length, input.length, 'untouched');
        ok(res.findings.some(function (f) { return /Encrypted/.test(f.label); }), 'reported');
    });

    /* =================================================== ZIP containers */

    test('ZIP round-trip preserves file contents', function () {
        var payload = B.utf8Bytes('<?xml version="1.0"?><doc>hello</doc>');
        var zip = WMR.containers.writeZip([
            { name: 'a.xml', bytes: payload, store: true, time: 0, date: 0x21 }
        ]);
        var back = WMR.containers.readZip(zip);
        eq(back.length, 1, 'entry count');
        eq(back[0].name, 'a.xml', 'name');
        eq(B.utf8Text(back[0].data), '<?xml version="1.0"?><doc>hello</doc>', 'content');
        eq(back[0].crc, B.crc32(payload), 'CRC');
    });

    test('DOCX core properties are blanked and body text is swept', function () {
        var core = '<?xml version="1.0"?><cp:coreProperties xmlns:cp="c" xmlns:dc="d">' +
            '<dc:creator>Jane Doe</dc:creator><cp:lastModifiedBy>Jane Doe</cp:lastModifiedBy>' +
            '<cp:revision>17</cp:revision></cp:coreProperties>';
        var doc = '<?xml version="1.0"?><w:document><w:t>Quarterly' + ZWSP + ' report</w:t></w:document>';
        var zip = WMR.containers.writeZip([
            { name: '[Content_Types].xml', bytes: B.utf8Bytes('<Types/>'), store: true, time: 0x4A21, date: 0x5678 },
            { name: 'docProps/core.xml', bytes: B.utf8Bytes(core), store: true, time: 0x4A21, date: 0x5678 },
            { name: 'word/document.xml', bytes: B.utf8Bytes(doc), store: true, time: 0x4A21, date: 0x5678 }
        ]);

        return WMR.containers.clean(zip, { text: WMR.text.defaults() }).then(function (res) {
            var entries = WMR.containers.readZip(res.bytes);
            eq(entries.length, 3, 'entry count');
            var byName = {};
            entries.forEach(function (e) { byName[e.name] = e; });

            return Promise.all([
                readEntry(byName['docProps/core.xml']),
                readEntry(byName['word/document.xml'])
            ]).then(function (texts) {
                ok(texts[0].indexOf('Jane Doe') === -1, 'creator blanked');
                ok(texts[0].indexOf('<dc:creator></dc:creator>') !== -1, 'element kept, value gone');
                ok(texts[1].indexOf(ZWSP) === -1, 'zero-width space swept from the body');
                ok(texts[1].indexOf('<w:t>Quarterly report</w:t>') !== -1, 'markup intact');
                eq(entries[0].time, 0, 'timestamps normalised');
                ok(res.findings.some(function (f) { return /timestamps/i.test(f.label); }), 'timestamps reported');
            });
        });

        function readEntry(entry) {
            if (entry.method === 0) return Promise.resolve(B.utf8Text(entry.data));
            var stream = new Response(entry.data).body.pipeThrough(new DecompressionStream('deflate-raw'));
            return new Response(stream).arrayBuffer().then(function (ab) { return B.utf8Text(new Uint8Array(ab)); });
        }
    });

    /* ================================================================ SVG */

    test('SVG metadata, comments and editor attributes are removed', function () {
        var svg = '<svg xmlns="http://www.w3.org/2000/svg" inkscape:version="1.1" width="10" height="10">' +
            '<!-- exported by someone --><metadata><rdf:RDF>author</rdf:RDF></metadata>' +
            '<title>Chart' + ZWSP + '</title><rect width="10" height="10"/></svg>';
        var res = WMR.containers.cleanSVG(svg, WMR.text.defaults());
        ok(res.text.indexOf('<metadata') === -1, 'metadata gone');
        ok(res.text.indexOf('exported by someone') === -1, 'comment gone');
        ok(res.text.indexOf('inkscape:version') === -1, 'editor attribute gone');
        ok(res.text.indexOf(ZWSP) === -1, 'zero-width space gone');
        ok(res.text.indexOf('<rect width="10" height="10"/>') !== -1, 'drawing intact');
    });

    /* ============================================================== run */

    function run(onResult) {
        var results = [];
        return T.reduce(function (chain, t) {
            return chain.then(function () {
                var started = Date.now();
                return Promise.resolve()
                    .then(t.fn)
                    .then(function () {
                        var r = { name: t.name, pass: true, ms: Date.now() - started };
                        results.push(r); if (onResult) onResult(r);
                    })
                    .catch(function (err) {
                        var r = { name: t.name, pass: false, error: err.message, ms: Date.now() - started };
                        results.push(r); if (onResult) onResult(r);
                    });
            });
        }, Promise.resolve()).then(function () { return results; });
    }

    WMR.tests = { run: run, count: function () { return T.length; } };
})(typeof window !== 'undefined' ? window : globalThis);
