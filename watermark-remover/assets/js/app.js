/* app.js — UI wiring. All the work happens in the four modules loaded before
   this one; this file only moves data between them and the DOM.
   ========================================================================= */
(function () {
    'use strict';

    var WMR = window.WMR;
    var B = WMR.bytes;
    var $ = function (id) { return document.getElementById(id); };
    var esc = WMR.text.escapeHtml;

    /* ------------------------------------------------------------ chrome */
    (function theme() {
        var btn = $('themeToggle');
        btn.addEventListener('click', function () {
            var current = document.documentElement.getAttribute('data-theme');
            if (!current) {
                current = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
            }
            var next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            try { localStorage.setItem('theme', next); } catch (e) { /* private mode */ }
        });
    })();

    (function tabs() {
        var list = [['tab-text', 'panel-text'], ['tab-files', 'panel-files'], ['tab-about', 'panel-about']];
        list.forEach(function (pair) {
            $(pair[0]).addEventListener('click', function () {
                list.forEach(function (p) {
                    var selected = p[0] === pair[0];
                    $(p[0]).setAttribute('aria-selected', String(selected));
                    $(p[1]).hidden = !selected;
                });
            });
        });
    })();

    var toastTimer;
    function toast(msg) {
        var el = $('toast');
        el.textContent = msg;
        el.classList.add('show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { el.classList.remove('show'); }, 2200);
    }

    function download(bytesOrText, filename, mime) {
        var blob = bytesOrText instanceof Blob ? bytesOrText
            : new Blob([bytesOrText], { type: mime || 'application/octet-stream' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    }

    function severityChip(sev) {
        var label = sev === 'likely-false-positive' ? 'kept, understood' : sev;
        return '<span class="sev sev-' + sev + '">' + esc(label) + '</span>';
    }

    $('capDeflate').textContent = WMR.containers.hasDeflate
        ? 'DOCX / EPUB supported'
        : 'DOCX / EPUB: browser lacks deflate';
    if (WMR.containers.hasDeflate) $('capDeflate').classList.add('on');

    /* ==================================================================
       TEXT TAB
    ================================================================== */
    var rules = WMR.text.defaults();

    (function renderRules() {
        var host = $('ruleList');
        host.innerHTML = WMR.text.CATEGORIES.map(function (c) {
            return '<div class="opt">' +
                '<input type="checkbox" id="rule-' + c.id + '"' + (c.def ? ' checked' : '') + '>' +
                '<label for="rule-' + c.id + '">' + esc(c.label) + severityChip(c.severity) +
                '<span class="hint">' + esc(c.hint) + '</span></label></div>';
        }).join('');

        WMR.text.CATEGORIES.forEach(function (c) {
            $('rule-' + c.id).addEventListener('change', function () {
                rules[c.id] = this.checked;
                runText();
            });
        });

        $('rulesAll').addEventListener('click', function () {
            WMR.text.CATEGORIES.forEach(function (c) { rules[c.id] = true; $('rule-' + c.id).checked = true; });
            runText();
        });
        $('rulesDefault').addEventListener('click', function () {
            rules = WMR.text.defaults();
            WMR.text.CATEGORIES.forEach(function (c) { $('rule-' + c.id).checked = rules[c.id]; });
            runText();
        });
    })();

    var textTimer;
    function scheduleText() { clearTimeout(textTimer); textTimer = setTimeout(runText, 90); }

    var lastText = null;

    function runText() {
        var input = $('inputText').value;
        $('textCount').textContent = input.length ? input.length.toLocaleString() + ' characters' : '';

        if (!input) {
            $('textResults').hidden = true;
            lastText = null;
            return;
        }

        var res = WMR.text.scan(input, rules);
        lastText = res;
        $('textResults').hidden = false;
        $('outputText').textContent = res.cleaned;

        // --- stats
        var kept = res.findings.filter(function (f) { return f.action === 'kept'; })
            .reduce(function (a, f) { return a + f.count; }, 0);
        var stats = [
            { n: res.stats.inputChars.toLocaleString(), l: 'chars in', cls: '' },
            { n: res.stats.outputChars.toLocaleString(), l: 'chars out', cls: '' },
            { n: res.stats.changed.toLocaleString(), l: 'removed or replaced', cls: res.stats.changed ? 'hit' : 'clean' },
            { n: res.payloads.length.toLocaleString(), l: 'hidden payloads', cls: res.payloads.length ? 'hit' : 'clean' },
            { n: kept.toLocaleString(), l: 'found but kept', cls: '' }
        ];
        $('textStats').innerHTML = stats.map(function (s) {
            return '<div class="stat ' + s.cls + '"><div class="n">' + s.n + '</div><div class="l">' + s.l + '</div></div>';
        }).join('');

        // --- decoded payloads
        $('textPayloads').innerHTML = res.payloads.map(function (p) {
            return '<div class="payload">' +
                '<div class="k">Hidden message · ' + esc(p.kind) + '</div>' +
                '<div class="v">' + esc(p.decoded) + '</div>' +
                '<div class="where">' + p.chars + ' invisible characters starting at offset ' + p.at + '. Removed from the cleaned text.</div>' +
                '</div>';
        }).join('');

        // --- highlight + findings
        $('highlight').innerHTML = res.findings.length
            ? WMR.text.highlight(input, res)
            : '<span class="hl-more">Nothing to mark — the text is already clean under the selected rules.</span>';

        var tbody = $('findingsTable').querySelector('tbody');
        if (!res.findings.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="detail">No findings. Every character in this text is one that renders.</td></tr>';
        } else {
            tbody.innerHTML = res.findings.map(function (f) {
                return '<tr>' +
                    '<td><code>' + esc(f.code) + '</code></td>' +
                    '<td class="name">' + esc(f.name) + '</td>' +
                    '<td>' + f.count + '</td>' +
                    '<td class="act act-' + f.action + '">' + f.action +
                        (f.replacement ? ' → ' + esc(JSON.stringify(f.replacement)) : '') + '</td>' +
                    '<td>' + severityChip(f.severity) + '</td>' +
                    '<td class="detail">' + esc(f.note) + '</td>' +
                    '</tr>';
            }).join('');
        }
    }

    $('inputText').addEventListener('input', scheduleText);
    $('clearText').addEventListener('click', function () {
        $('inputText').value = '';
        runText();
        $('inputText').focus();
    });

    $('copyText').addEventListener('click', function () {
        if (!lastText) return;
        var write = navigator.clipboard && navigator.clipboard.writeText
            ? navigator.clipboard.writeText(lastText.cleaned)
            : Promise.reject();
        write.then(function () { toast('Cleaned text copied.'); })
            .catch(function () {
                // Clipboard API needs a secure context; fall back to selection.
                var ta = document.createElement('textarea');
                ta.value = lastText.cleaned;
                document.body.appendChild(ta);
                ta.select();
                try { document.execCommand('copy'); toast('Cleaned text copied.'); }
                catch (e) { toast('Copy failed — select the text and copy manually.'); }
                ta.remove();
            });
    });

    $('downloadText').addEventListener('click', function () {
        if (!lastText) return;
        download(lastText.cleaned, 'cleaned.txt', 'text/plain;charset=utf-8');
    });

    /* A sample built from escapes rather than pasted as a literal, so the
       source stays readable and every hidden character is unambiguous. */
    $('loadSample').addEventListener('click', function () {
        var ZWSP = '\u200B', ZWNJ = '\u200C', ZWJ = '\u200D',
            RLO = '\u202E', POP = '\u202C', NBSP = '\u00A0', EMDASH = '\u2014';
        var CYR_o = '\u043E', CYR_O = '\u041E';   // look like Latin o and O

        // Unicode tag characters: one per ASCII byte, all invisible.
        function tag(s) {
            return s.split('').map(function (ch) {
                return String.fromCodePoint(0xE0000 + ch.charCodeAt(0));
            }).join('');
        }
        // Variation selectors: 256 codepoints, one per byte value.
        function vs(s) {
            return Array.from(B.utf8Bytes(s)).map(function (b) {
                return b < 16 ? String.fromCodePoint(0xFE00 + b) : String.fromCodePoint(0xE0100 + b - 16);
            }).join('');
        }
        // Zero-width binary, the ZWSP=0 / ZWNJ=1 mapping.
        function zwBinary(s) {
            var bits = '';
            for (var i = 0; i < s.length; i++) {
                var b = s.charCodeAt(i).toString(2);
                while (b.length < 8) b = '0' + b;
                bits += b;
            }
            return bits.split('').map(function (bit) { return bit === '0' ? ZWSP : ZWNJ; }).join('');
        }

        var sample =
            'The quarterly rep' + CYR_o + 'rt' + tag('doc-id:7741-BX') + ' is attached.' + ZWSP + ZWSP + '\n\n' +
            'Please review the figures before Friday' + vs('MBA') + ', and let me know if the\n' +
            'margin' + ZWJ + ' calculation still looks off. ' + RLO + 'This clause is bidi-overridden.' + POP + '\n\n' +
            'A non-breaking' + NBSP + 'space and an em' + EMDASH + 'dash are both in this line.\n\n' +
            'Regards,' + zwBinary('traced') + '\n' + CYR_O + 'perations';

        $('inputText').value = sample;
        runText();
        toast('Sample loaded — six different marks are hiding in it.');
    });

    /* ==================================================================
       FILES TAB
    ================================================================== */
    var cleaned = [];   // {name, bytes, format}

    function fileOpts() {
        return {
            stripICC: $('optICC').checked,
            normalizeTimestamps: $('optTimestamps').checked,
            pdfClearId: $('optPdfId').checked,
            cleanBodyText: $('optBodyText').checked,
            text: rules
        };
    }

    var drop = $('drop'), fileInput = $('fileInput');

    drop.addEventListener('click', function () { fileInput.click(); });
    drop.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); }
    });
    fileInput.addEventListener('change', function () {
        handleFiles(Array.from(this.files));
        this.value = '';
    });
    ['dragenter', 'dragover'].forEach(function (ev) {
        drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('over'); });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
        drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('over'); });
    });
    drop.addEventListener('drop', function (e) {
        if (e.dataTransfer && e.dataTransfer.files) handleFiles(Array.from(e.dataTransfer.files));
    });

    $('clearFiles').addEventListener('click', function () {
        cleaned = [];
        $('fileResults').innerHTML = '';
        $('fileActions').hidden = true;
    });

    $('downloadAll').addEventListener('click', function () {
        if (!cleaned.length) return;
        var zip = WMR.containers.bundle(cleaned.map(function (c) { return { name: c.name, bytes: c.bytes }; }));
        download(new Blob([zip], { type: 'application/zip' }), 'cleaned-files.zip');
    });

    function readFile(file) {
        return new Promise(function (resolve, reject) {
            var fr = new FileReader();
            fr.onload = function () { resolve(new Uint8Array(fr.result)); };
            fr.onerror = function () { reject(new Error('Could not read this file.')); };
            fr.readAsArrayBuffer(file);
        });
    }

    var TEXT_EXT = /\.(txt|md|markdown|html?|xml|csv|tsv|json|ya?ml|js|ts|css|srt|vtt|rtf|tex|bib|log|ini|toml)$/i;

    function handleFiles(files) {
        files.forEach(function (file) {
            var card = document.createElement('div');
            card.className = 'file';
            card.innerHTML = '<div class="file-head"><span class="file-name">' + esc(file.name) + '</span>' +
                '<span class="file-meta">reading…</span></div>';
            $('fileResults').appendChild(card);

            readFile(file)
                .then(function (buf) { return processFile(file, buf); })
                .then(function (result) { renderFile(card, file, result); })
                .catch(function (err) {
                    card.innerHTML = '<div class="file-head"><span class="file-name">' + esc(file.name) + '</span>' +
                        '<span class="file-tag">failed</span></div>' +
                        '<p class="sub" style="margin:10px 0 0">' + esc(err.message) + '</p>';
                });
        });
    }

    function processFile(file, buf) {
        var opts = fileOpts();
        var name = file.name;

        // ZIP-backed documents
        if (buf[0] === 0x50 && buf[1] === 0x4B && (buf[2] === 3 || buf[2] === 5 || buf[2] === 7)) {
            return WMR.containers.clean(buf, opts);
        }

        // PDF
        if (B.ascii(buf, 0, 5) === '%PDF-') {
            return Promise.resolve(WMR.pdf.clean(buf, opts));
        }

        // Images we can operate on losslessly
        var img = WMR.images.clean(buf, opts);
        if (img) return Promise.resolve(img);

        // SVG and other text formats
        var text = B.utf8Text(buf);
        if (/\.svg$/i.test(name) || /^\s*(<\?xml[^>]*\?>\s*)?(<!--[\s\S]*?-->\s*)*<svg[\s>]/i.test(text.slice(0, 600))) {
            var svg = WMR.containers.cleanSVG(text, rules);
            return Promise.resolve({ format: svg.format, findings: svg.findings, bytes: B.utf8Bytes(svg.text), payloads: svg.payloads });
        }
        if (TEXT_EXT.test(name) || looksLikeText(buf)) {
            var res = WMR.text.scan(text, rules);
            var findings = res.findings.filter(function (f) { return f.action !== 'kept'; }).map(function (f) {
                return WMR.images.finding(f.code + '  ' + f.name, f.action, f.severity,
                    f.count + '×' + (f.replacement ? ' → ' + JSON.stringify(f.replacement) : ''), f.count);
            });
            res.payloads.forEach(function (p) {
                findings.unshift(WMR.images.finding('Hidden payload · ' + p.kind, 'removed', 'confirmed',
                    '“' + B.preview(p.decoded, 200) + '”', p.chars));
            });
            if (!findings.length) {
                findings.push(WMR.images.finding('No hidden characters', 'noted', 'likely-false-positive',
                    'Every character in this file renders.'));
            }
            return Promise.resolve({ format: 'Text', findings: findings, bytes: B.utf8Bytes(res.cleaned) });
        }

        return Promise.resolve({
            format: 'Unsupported',
            findings: [WMR.images.finding('Format not supported', 'noted', 'informational',
                'This tool understands PNG, JPEG, WebP, GIF, SVG, PDF, ZIP-based documents and text files. ' +
                'Nothing was changed.')],
            bytes: buf,
            unsupported: true
        });
    }

    function looksLikeText(buf) {
        var n = Math.min(buf.length, 1024), printable = 0;
        for (var i = 0; i < n; i++) {
            var b = buf[i];
            if (b === 9 || b === 10 || b === 13 || (b >= 32 && b !== 127) || b >= 0xC2) printable++;
        }
        return n > 0 && printable / n > 0.9;
    }

    function renderFile(card, file, result) {
        var removed = result.findings.filter(function (f) { return f.action === 'removed' || f.action === 'replaced'; }).length;
        var saved = file.size - (result.bytes ? result.bytes.length : file.size);

        if (!result.findings.length) {
            result.findings = [WMR.images.finding('Nothing found', 'noted', 'likely-false-positive',
                'No metadata, comments or appended data in this file. It was already clean.')];
        }
        var rows = result.findings.map(function (f) {
            return '<tr>' +
                '<td class="name">' + esc(f.label) + '</td>' +
                '<td class="act act-' + f.action + '">' + esc(f.action) + '</td>' +
                '<td>' + severityChip(f.severity) + '</td>' +
                '<td class="detail">' + esc(f.detail) + '</td>' +
                '</tr>';
        }).join('');

        var outName = file.name.replace(/(\.[^.]+)?$/, function (ext) { return '-cleaned' + (ext || ''); });

        card.innerHTML =
            '<div class="file-head">' +
                '<span class="file-name">' + esc(file.name) + '</span>' +
                '<span class="file-meta">' +
                    '<span class="file-tag">' + esc(result.format) + '</span> ' +
                    B.formatBytes(file.size) +
                    (result.bytes && result.bytes.length !== file.size
                        ? ' → ' + B.formatBytes(result.bytes.length) +
                          (saved > 0 ? ' (−' + B.formatBytes(saved) + ')' : '')
                        : '') +
                '</span>' +
            '</div>' +
            '<p class="sub" style="margin:8px 0 12px">' +
                (removed ? removed + ' item' + (removed === 1 ? '' : 's') + ' removed.'
                         : 'Nothing removable found.') +
                (result.lengthPreserved ? ' File length preserved so the PDF cross-reference table stays valid.' : '') +
            '</p>' +
            '<div class="table-scroll"><table class="findings">' +
                '<thead><tr><th>What</th><th>Action</th><th>Classification</th><th>Detail</th></tr></thead>' +
                '<tbody>' + rows + '</tbody></table></div>' +
            '<div class="btn-row">' +
                (result.unsupported ? '' : '<button class="btn btn-primary" data-dl>Download cleaned file</button>') +
                (/^image\//.test(file.type) ? '<button class="btn" data-reencode>Re-encode as PNG (destructive)</button>' : '') +
            '</div>';

        if (!result.unsupported) {
            card.querySelector('[data-dl]').addEventListener('click', function () {
                download(new Blob([result.bytes]), outName, file.type || 'application/octet-stream');
            });
            cleaned.push({ name: outName, bytes: result.bytes });
            $('fileActions').hidden = false;
        }

        var re = card.querySelector('[data-reencode]');
        if (re) {
            re.addEventListener('click', function () {
                re.disabled = true;
                WMR.images.reencode(new Blob([result.bytes || new Uint8Array()], { type: file.type }), 'image/png')
                    .then(function (blob) {
                        download(blob, file.name.replace(/\.[^.]+$/, '') + '-reencoded.png', 'image/png');
                        toast('Re-encoded. Pixels were recompressed — this is the lossy option.');
                    })
                    .catch(function (err) { toast(err.message); })
                    .finally(function () { re.disabled = false; });
            });
        }
    }

    /* ------------------------------------------------------------ offline */
    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('sw.js').catch(function () { /* offline is a bonus, not a requirement */ });
        });
    }
})();
