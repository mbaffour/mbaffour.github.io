/* pdf.js — document metadata removal for PDF, without a PDF library.
   ---------------------------------------------------------------------------
   A PDF is a byte-offset format: the cross-reference table at the end records
   the exact position of every object. Delete four bytes near the front and
   every offset after it is wrong, and the file is broken — which is why the
   naive "regex the /Author out" approach produces PDFs that Acrobat refuses.

   So we never change the file's length. Every edit here overwrites bytes in
   place with the same number of bytes: string contents become spaces, hex
   digits become zeroes, XMP packet bodies become whitespace. The xref stays
   valid, incremental-update chains stay valid, and the document still opens.

   The honest limits, stated in the report as well as here:
     • Metadata inside a compressed object stream is invisible to a byte scan.
       We say so when we detect object streams rather than claiming a clean file.
     • Encrypted PDFs have their strings encrypted; we detect /Encrypt and stop
       rather than corrupting the document.
     • This does not touch page content. Text drawn on the page stays drawn.
   ========================================================================= */
(function (global) {
    'use strict';

    var WMR = global.WMR || (global.WMR = {});
    var B = WMR.bytes;
    var f = WMR.images.finding;

    var SPACE = 0x20;

    /* Info-dictionary keys worth blanking. /Title here is the *document* title
       from the Info dictionary only — we resolve the Info object first, so the
       /Title entries inside bookmarks and form fields are never touched. */
    var INFO_KEYS = ['Title', 'Author', 'Subject', 'Keywords', 'Creator',
                     'Producer', 'CreationDate', 'ModDate', 'Company', 'SourceModified',
                     'Trapped', 'GTS_PDFXVersion'];

    function latin1(buf) {
        // PDF syntax is byte-oriented; decode as latin-1 so index N in the
        // string is byte N in the file. UTF-8 decoding would break that.
        var out = '', step = 0x8000;
        for (var i = 0; i < buf.length; i += step) {
            out += String.fromCharCode.apply(null, buf.subarray(i, Math.min(i + step, buf.length)));
        }
        return out;
    }

    /* Walk a literal ( ... ) string from its opening paren, honouring escapes
       and nested parens. Returns the index of the closing paren, or -1. */
    function endOfLiteral(s, open) {
        var depth = 0;
        for (var i = open; i < s.length; i++) {
            var c = s[i];
            if (c === '\\') { i++; continue; }
            if (c === '(') depth++;
            else if (c === ')') { depth--; if (depth === 0) return i; }
        }
        return -1;
    }

    /* Decode a PDF text string enough to show the user what was in there. */
    function decodeString(raw) {
        var s = raw.replace(/\\([nrtbf()\\])/g, function (m, c) {
            return { n: '\n', r: '\r', t: '\t', b: '\b', f: '\f' }[c] || c;
        }).replace(/\\([0-7]{1,3})/g, function (m, o) { return String.fromCharCode(parseInt(o, 8)); });
        if (s.charCodeAt(0) === 0xFE && s.charCodeAt(1) === 0xFF) {   // UTF-16BE
            var out = '';
            for (var i = 2; i + 1 < s.length; i += 2) out += String.fromCharCode((s.charCodeAt(i) << 8) | s.charCodeAt(i + 1));
            return out;
        }
        return s;
    }

    function decodeHexString(raw) {
        var s = '';
        for (var i = 0; i + 1 < raw.length; i += 2) s += String.fromCharCode(parseInt(raw.substr(i, 2), 16));
        if (s.charCodeAt(0) === 0xFE && s.charCodeAt(1) === 0xFF) {
            var out = '';
            for (var j = 2; j + 1 < s.length; j += 2) out += String.fromCharCode((s.charCodeAt(j) << 8) | s.charCodeAt(j + 1));
            return out;
        }
        return s;
    }

    function clean(buf, opts) {
        opts = opts || {};
        var bytes = buf.slice();                 // we mutate a copy
        var s = latin1(buf);
        var findings = [];
        var edits = 0;

        if (!/^%PDF-/.test(s.slice(0, 8))) {
            return { format: 'PDF', bytes: buf, findings: [f('Not a PDF', 'noted', 'informational',
                'The file does not start with %PDF-.')] };
        }

        var encrypted = /\/Encrypt\s+\d+\s+\d+\s+R/.test(s);
        if (encrypted) {
            findings.push(f('Encrypted PDF', 'noted', 'informational',
                'This document uses PDF encryption, so its strings are ciphertext and blanking them in place ' +
                'would corrupt the file. Remove the encryption first (qpdf --decrypt) and run it through again.'));
            return { format: 'PDF', bytes: buf, findings: findings };
        }

        function blankRange(from, to, fill) {
            for (var i = from; i < to; i++) bytes[i] = fill;
            edits += Math.max(0, to - from);
        }

        /* ---------------- Info dictionary ------------------------------- */
        // Every trailer in the file, including those added by incremental
        // updates, may point at a different Info object. Collect them all.
        var infoObjs = {};
        var reInfo = /\/Info\s+(\d+)\s+(\d+)\s+R/g, m;
        while ((m = reInfo.exec(s)) !== null) infoObjs[m[1] + ' ' + m[2]] = true;

        var infoFound = 0;
        Object.keys(infoObjs).forEach(function (ref) {
            var parts = ref.split(' ');
            var reObj = new RegExp('(^|[^0-9])' + parts[0] + '\\s+' + parts[1] + '\\s+obj', 'g');
            var mo;
            while ((mo = reObj.exec(s)) !== null) {
                var start = mo.index + mo[1].length;
                var stop = s.indexOf('endobj', start);
                if (stop === -1) stop = Math.min(s.length, start + 8192);
                infoFound++;
                blankInfoObject(s, start, stop);
            }
        });

        function blankInfoObject(str, start, stop) {
            INFO_KEYS.forEach(function (key) {
                var re = new RegExp('/' + key + '\\s*', 'g');
                re.lastIndex = start;
                var mk;
                while ((mk = re.exec(str)) !== null && mk.index < stop) {
                    var vAt = mk.index + mk[0].length;
                    var ch = str[vAt];
                    if (ch === '(') {
                        var close = endOfLiteral(str, vAt);
                        if (close === -1 || close > stop) continue;
                        var raw = str.slice(vAt + 1, close);
                        if (raw.length) {
                            findings.push(f('Document ' + key.toLowerCase(), 'removed', 'confirmed',
                                B.preview(decodeString(raw)), raw.length));
                            blankRange(vAt + 1, close, SPACE);
                        }
                    } else if (ch === '<' && str[vAt + 1] !== '<') {
                        var closeH = str.indexOf('>', vAt);
                        if (closeH === -1 || closeH > stop) continue;
                        var rawH = str.slice(vAt + 1, closeH);
                        if (rawH.length) {
                            findings.push(f('Document ' + key.toLowerCase(), 'removed', 'confirmed',
                                B.preview(decodeHexString(rawH.replace(/[^0-9a-fA-F]/g, ''))), rawH.length));
                            blankRange(vAt + 1, closeH, 0x30);        // '0'
                        }
                    } else if (ch === '/') {
                        // A name value such as /Trapped /False. Leave it: names
                        // are structural and carry no identifying content.
                    }
                }
            });
        }

        /* ---------------- XMP packets ----------------------------------- */
        // Uncompressed XMP sits in the file as a plain <?xpacket …?> block.
        var xAt = 0, xmpCount = 0;
        while (true) {
            var begin = s.indexOf('<?xpacket begin', xAt);
            if (begin === -1) break;
            var bodyStart = s.indexOf('?>', begin);
            if (bodyStart === -1) break;
            bodyStart += 2;
            var endPacket = s.indexOf('<?xpacket end', bodyStart);
            if (endPacket === -1) { xAt = bodyStart; continue; }
            var body = s.slice(bodyStart, endPacket);
            var tool = (body.match(/<xmp:CreatorTool>([^<]*)</) || [])[1] ||
                       (body.match(/xmp:CreatorTool="([^"]*)"/) || [])[1] || '';
            var creator = (body.match(/<dc:creator>[\s\S]*?<rdf:li[^>]*>([^<]*)</) || [])[1] || '';
            blankRange(bodyStart, endPacket, SPACE);
            xmpCount++;
            findings.push(f('XMP metadata packet', 'removed', 'confirmed',
                B.formatBytes(body.length) + ' of RDF/XML' +
                (tool ? ' · creator tool: ' + B.preview(tool, 80) : '') +
                (creator ? ' · author: ' + B.preview(creator, 80) : '') +
                '. Blanked in place so the file length and every xref offset stay valid.',
                body.length));
            xAt = endPacket + 10;
        }

        /* ---------------- Document ID ----------------------------------- */
        if (opts.pdfClearId !== false) {
            var reId = /\/ID\s*\[\s*<([0-9a-fA-F\s]*)>\s*<([0-9a-fA-F\s]*)>\s*\]/g, mi, idCount = 0;
            while ((mi = reId.exec(s)) !== null) {
                // Two hex strings; blank both, keeping every byte position.
                var g1 = mi.index + mi[0].indexOf('<') + 1;
                blankRange(g1, g1 + mi[1].length, 0x30);
                var secondRel = mi[0].indexOf('<', mi[0].indexOf('>') );
                var g2 = mi.index + secondRel + 1;
                blankRange(g2, g2 + mi[2].length, 0x30);
                idCount++;
            }
            if (idCount) {
                findings.push(f('Document identifier (/ID)', 'removed', 'probable',
                    idCount + ' trailer ID pair' + (idCount === 1 ? '' : 's') + ' zeroed. The /ID survives ' +
                    '"save as" and links copies of a document to each other.', 0));
            }
        }

        /* ---------------- Things we can see but not safely remove -------- */
        if (/\/Type\s*\/ObjStm/.test(s)) {
            findings.push(f('Compressed object streams present', 'noted', 'informational',
                'Some objects in this PDF are deflate-compressed inside object streams. A byte-level pass cannot ' +
                'read them, so metadata hidden there is not covered by this report. Run qpdf --object-streams=disable ' +
                'first if you need certainty.'));
        }
        if (/c2pa|jumbf|contentauth/i.test(s.slice(0, 4096)) || B.indexOfBytes(buf, B.asciiBytes('c2pa'), 0) !== -1) {
            findings.push(f('C2PA / content-credential markers', 'noted', 'probable',
                'Byte patterns associated with content credentials appear in this file. If they live in a compressed ' +
                'stream this pass will not have removed them — verify with c2patool.'));
        }
        if (/\/EmbeddedFile/.test(s)) {
            findings.push(f('Embedded file attachments', 'noted', 'probable',
                'This PDF carries attached files. Their own metadata is untouched by this pass.'));
        }
        if (infoFound === 0 && xmpCount === 0) {
            findings.push(f('No plain-text metadata found', 'noted', 'likely-false-positive',
                'No readable Info dictionary or XMP packet in the byte stream. Either the document is already clean, ' +
                'or its metadata is compressed.'));
        }

        return {
            format: 'PDF',
            bytes: edits ? bytes : buf,
            findings: findings,
            lengthPreserved: true
        };
    }

    WMR.pdf = { clean: clean, _internal: { endOfLiteral: endOfLiteral, decodeString: decodeString } };
})(typeof window !== 'undefined' ? window : globalThis);
