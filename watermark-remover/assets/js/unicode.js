/* unicode.js — Layer A: deterministic text hygiene.
   ---------------------------------------------------------------------------
   Everything here is verifiable. A codepoint is either present or it is not,
   so every finding this file reports can be checked by hand. Nothing in this
   file guesses at whether text "feels" AI-written, and nothing rewrites your
   sentences — that is Layer B, and it does not run in a browser (see the
   honesty note in index.html).

   The rules below are deliberately context-aware. A zero-width joiner inside
   a family emoji and a zero-width joiner smuggled between two Latin letters
   are the same codepoint but not the same thing, and a tool that strips both
   quietly corrupts real text. Where a character has a legitimate use we keep
   it and say so, classified as likely-false-positive.
   ========================================================================= */
(function (global) {
    'use strict';

    var WMR = global.WMR || (global.WMR = {});

    /* ---------------------------------------------------------------------
       Codepoint names. Only the ones we actually detect — this is a lookup
       for the report, not a copy of UnicodeData.txt.
    --------------------------------------------------------------------- */
    var NAMES = {
        0x0009: 'CHARACTER TABULATION',
        0x00A0: 'NO-BREAK SPACE',
        0x00AD: 'SOFT HYPHEN',
        0x061C: 'ARABIC LETTER MARK',
        0x115F: 'HANGUL CHOSEONG FILLER',
        0x1160: 'HANGUL JUNGSEONG FILLER',
        0x1680: 'OGHAM SPACE MARK',
        0x180E: 'MONGOLIAN VOWEL SEPARATOR',
        0x2000: 'EN QUAD',
        0x2001: 'EM QUAD',
        0x2002: 'EN SPACE',
        0x2003: 'EM SPACE',
        0x2004: 'THREE-PER-EM SPACE',
        0x2005: 'FOUR-PER-EM SPACE',
        0x2006: 'SIX-PER-EM SPACE',
        0x2007: 'FIGURE SPACE',
        0x2008: 'PUNCTUATION SPACE',
        0x2009: 'THIN SPACE',
        0x200A: 'HAIR SPACE',
        0x200B: 'ZERO WIDTH SPACE',
        0x200C: 'ZERO WIDTH NON-JOINER',
        0x200D: 'ZERO WIDTH JOINER',
        0x200E: 'LEFT-TO-RIGHT MARK',
        0x200F: 'RIGHT-TO-LEFT MARK',
        0x2028: 'LINE SEPARATOR',
        0x2029: 'PARAGRAPH SEPARATOR',
        0x202A: 'LEFT-TO-RIGHT EMBEDDING',
        0x202B: 'RIGHT-TO-LEFT EMBEDDING',
        0x202C: 'POP DIRECTIONAL FORMATTING',
        0x202D: 'LEFT-TO-RIGHT OVERRIDE',
        0x202E: 'RIGHT-TO-LEFT OVERRIDE',
        0x202F: 'NARROW NO-BREAK SPACE',
        0x205F: 'MEDIUM MATHEMATICAL SPACE',
        0x2060: 'WORD JOINER',
        0x2061: 'FUNCTION APPLICATION',
        0x2062: 'INVISIBLE TIMES',
        0x2063: 'INVISIBLE SEPARATOR',
        0x2064: 'INVISIBLE PLUS',
        0x2066: 'LEFT-TO-RIGHT ISOLATE',
        0x2067: 'RIGHT-TO-LEFT ISOLATE',
        0x2068: 'FIRST STRONG ISOLATE',
        0x2069: 'POP DIRECTIONAL ISOLATE',
        0x206A: 'INHIBIT SYMMETRIC SWAPPING',
        0x206B: 'ACTIVATE SYMMETRIC SWAPPING',
        0x206C: 'INHIBIT ARABIC FORM SHAPING',
        0x206D: 'ACTIVATE ARABIC FORM SHAPING',
        0x206E: 'NATIONAL DIGIT SHAPES',
        0x206F: 'NOMINAL DIGIT SHAPES',
        0x2800: 'BRAILLE PATTERN BLANK',
        0x3000: 'IDEOGRAPHIC SPACE',
        0x3164: 'HANGUL FILLER',
        0xFEFF: 'ZERO WIDTH NO-BREAK SPACE (BOM)',
        0xFFA0: 'HALFWIDTH HANGUL FILLER',
        0xFFF9: 'INTERLINEAR ANNOTATION ANCHOR',
        0xFFFA: 'INTERLINEAR ANNOTATION SEPARATOR',
        0xFFFB: 'INTERLINEAR ANNOTATION TERMINATOR',
        0x17B4: 'KHMER VOWEL INHERENT AQ',
        0x17B5: 'KHMER VOWEL INHERENT AA'
    };

    /* Names for the confusables we fold, so the report says "CYRILLIC SMALL
       LETTER O → o" rather than leaving a bare codepoint on the row. Built
       from the block plus a letter table, which is enough for the Cyrillic
       and Greek ranges the confusable map covers. */
    var CYRILLIC = {
        0x0410: 'A', 0x0412: 'VE', 0x0415: 'IE', 0x0417: 'ZE', 0x041A: 'KA', 0x041C: 'EM',
        0x041D: 'EN', 0x041E: 'O', 0x0420: 'ER', 0x0421: 'ES', 0x0422: 'TE', 0x0423: 'U',
        0x0425: 'HA', 0x0405: 'DZE', 0x0406: 'BYELORUSSIAN-UKRAINIAN I', 0x0408: 'JE',
        0x0430: 'A', 0x0432: 'VE', 0x0433: 'GHE', 0x0435: 'IE', 0x043A: 'KA', 0x043C: 'EM',
        0x043D: 'EN', 0x043E: 'O', 0x0440: 'ER', 0x0441: 'ES', 0x0442: 'TE', 0x0443: 'U',
        0x0445: 'HA', 0x0455: 'DZE', 0x0456: 'BYELORUSSIAN-UKRAINIAN I', 0x0458: 'JE',
        0x04AE: 'STRAIGHT U', 0x04BB: 'SHHA', 0x04CF: 'PALOCHKA', 0x0491: 'GHE WITH UPTURN',
        0x0492: 'GHE WITH STROKE', 0x0501: 'KOMI DE'
    };
    var GREEK = {
        0x0391: 'ALPHA', 0x0392: 'BETA', 0x0395: 'EPSILON', 0x0396: 'ZETA', 0x0397: 'ETA',
        0x0399: 'IOTA', 0x039A: 'KAPPA', 0x039C: 'MU', 0x039D: 'NU', 0x039F: 'OMICRON',
        0x03A1: 'RHO', 0x03A4: 'TAU', 0x03A5: 'UPSILON', 0x03A7: 'CHI',
        0x03B1: 'ALPHA', 0x03B5: 'EPSILON', 0x03B9: 'IOTA', 0x03BA: 'KAPPA', 0x03BD: 'NU',
        0x03BF: 'OMICRON', 0x03C1: 'RHO', 0x03C3: 'SIGMA', 0x03C5: 'UPSILON', 0x03C7: 'CHI'
    };

    function nameOf(cp) {
        if (NAMES[cp]) return NAMES[cp];
        if (CYRILLIC[cp]) {
            // Basic Cyrillic is capitals up to U+042F; the extended letters in
            // this table (ghe with upturn, shha, palochka, komi de) are the
            // lowercase members of their pairs, apart from straight U.
            var capital = cp <= 0x042F || cp === 0x04AE || cp === 0x0492;
            return 'CYRILLIC ' + (capital ? 'CAPITAL' : 'SMALL') + ' LETTER ' + CYRILLIC[cp];
        }
        if (GREEK[cp]) {
            return 'GREEK ' + (cp <= 0x03A9 ? 'CAPITAL' : 'SMALL') + ' LETTER ' + GREEK[cp];
        }
        if (cp === 0x0585) return 'ARMENIAN SMALL LETTER OH';
        if (cp === 0x0578) return 'ARMENIAN SMALL LETTER VO';
        if (cp === 0x057D) return 'ARMENIAN SMALL LETTER SEH';
        if (cp === 0x13A0) return 'CHEROKEE LETTER A';
        if (cp === 0x13C0) return 'CHEROKEE LETTER NAH';
        if (cp === 0x2C9F) return 'COPTIC SMALL LETTER O';
        if (cp >= 0xFF01 && cp <= 0xFF5E) return 'FULLWIDTH ' + JSON.stringify(String.fromCharCode(cp - 0xFEE0)).slice(1, -1);
        if (cp >= 0x1D400 && cp <= 0x1D7FF) return 'MATHEMATICAL ALPHANUMERIC SYMBOL';
        if (cp >= 0xFE00 && cp <= 0xFE0F) return 'VARIATION SELECTOR-' + (cp - 0xFE00 + 1);
        if (cp >= 0xE0100 && cp <= 0xE01EF) return 'VARIATION SELECTOR-' + (cp - 0xE0100 + 17);
        if (cp === 0xE0001) return 'LANGUAGE TAG';
        if (cp === 0xE007F) return 'CANCEL TAG';
        if (cp >= 0xE0020 && cp <= 0xE007E) return 'TAG ' + JSON.stringify(String.fromCharCode(cp - 0xE0000)).slice(1, -1);
        if (cp >= 0xE0000 && cp <= 0xE007F) return 'RESERVED TAG CHARACTER';
        return 'U+' + hex(cp);
    }

    function hex(cp) {
        var s = cp.toString(16).toUpperCase();
        while (s.length < 4) s = '0' + s;
        return s;
    }

    /* ---------------------------------------------------------------------
       Category metadata. The UI renders its toggles straight off this, so a
       new rule only has to be described in one place.
    --------------------------------------------------------------------- */
    var CATEGORIES = [
        {
            id: 'invisible',
            label: 'Invisible & zero-width characters',
            hint: 'Zero-width space, word joiner, soft hyphen, BOM, Hangul and Khmer fillers. These render as nothing and carry no meaning in running prose.',
            severity: 'confirmed',
            def: true
        },
        {
            id: 'tags',
            label: 'Unicode tag characters',
            hint: 'U+E0000–E007F. A whole ASCII alphabet that renders as nothing — the usual carrier for a message hidden inside visible text. Flag-emoji tag sequences are kept.',
            severity: 'confirmed',
            def: true
        },
        {
            id: 'variation',
            label: 'Variation selectors',
            hint: 'U+FE00–FE0F and U+E0100–E01EF. 256 invisible codepoints, one per byte value, so a run of them is a byte string. Emoji-presentation FE0F after a pictograph is kept.',
            severity: 'confirmed',
            def: true
        },
        {
            id: 'joiners',
            label: 'Zero-width joiners & non-joiners',
            hint: 'U+200D / U+200C. Structural in emoji sequences and in Indic, Arabic and Hebrew script — kept there, removed between Latin letters where they do nothing but mark the text.',
            severity: 'probable',
            def: true
        },
        {
            id: 'bidi',
            label: 'Bidirectional controls',
            hint: 'Overrides, embeddings and isolates (U+202A–202E, U+2066–2069, LRM/RLM/ALM). Legitimate in mixed-direction text; also how source code is made to read differently than it runs.',
            severity: 'probable',
            def: true
        },
        {
            id: 'spaces',
            label: 'Exotic spaces → normal space',
            hint: 'NBSP, en/em/thin/hair spaces, narrow NBSP, Ogham space. Ideographic space (U+3000) is left alone when the text contains CJK, where it is ordinary punctuation.',
            severity: 'informational',
            def: true
        },
        {
            id: 'confusables',
            label: 'Homoglyphs in mixed-script words',
            hint: 'Cyrillic а, Greek ο and friends sitting inside otherwise-Latin words. Whole words in another script are left untouched — only words that mix scripts are folded to Latin.',
            severity: 'confirmed',
            def: true
        },
        {
            id: 'compat',
            label: 'Styled letterforms → plain',
            hint: 'Mathematical alphanumerics (𝐀 𝑨 𝔸), fullwidth (Ａ) and letterlike symbols folded to their plain equivalents via NFKC. Turn off if you are cleaning genuine mathematical notation.',
            severity: 'probable',
            def: true
        },
        {
            id: 'lineSeparators',
            label: 'Line/paragraph separators → newline',
            hint: 'U+2028 and U+2029. Behave as line breaks in some renderers and as nothing in others, which makes them a quiet way to differ two copies of a document.',
            severity: 'informational',
            def: true
        },
        {
            id: 'typography',
            label: 'Typographic normalisation',
            hint: 'Curly quotes → straight, em/en dash → hyphen, … → three dots. This one changes how your writing looks. Off by default, because it is a style edit, not a watermark removal.',
            severity: 'informational',
            def: false
        },
        {
            id: 'tidy',
            label: 'Whitespace tidy',
            hint: 'Trailing spaces at end of line, and runs of three or more blank lines collapsed to one blank line.',
            severity: 'informational',
            def: false
        }
    ];

    function defaults() {
        var o = {};
        CATEGORIES.forEach(function (c) { o[c.id] = c.def; });
        return o;
    }

    /* ---------------------------------------------------------------------
       Character sets
    --------------------------------------------------------------------- */

    // Renders as nothing, means nothing in prose. Safe to delete outright.
    var INVISIBLE = {};
    [0x200B, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF, 0x00AD,
     0x180E, 0x115F, 0x1160, 0x3164, 0xFFA0, 0x17B4, 0x17B5,
     0xFFF9, 0xFFFA, 0xFFFB, 0x206A, 0x206B, 0x206C, 0x206D, 0x206E, 0x206F
    ].forEach(function (cp) { INVISIBLE[cp] = true; });

    // Space-like, but not U+0020. Value is what we replace them with.
    var SPACES = {
        0x00A0: ' ', 0x1680: ' ', 0x2000: ' ', 0x2001: ' ', 0x2002: ' ',
        0x2003: ' ', 0x2004: ' ', 0x2005: ' ', 0x2006: ' ', 0x2007: ' ',
        0x2008: ' ', 0x2009: ' ', 0x200A: ' ', 0x202F: ' ', 0x205F: ' ',
        0x3000: ' ', 0x2800: ' '
    };

    var BIDI = {};
    [0x200E, 0x200F, 0x061C, 0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
     0x2066, 0x2067, 0x2068, 0x2069].forEach(function (cp) { BIDI[cp] = true; });

    var TYPOGRAPHY = {
        0x2018: "'", 0x2019: "'", 0x201A: "'", 0x201B: "'",
        0x201C: '"', 0x201D: '"', 0x201E: '"', 0x201F: '"',
        0x2032: "'", 0x2033: '"',
        0x2010: '-', 0x2011: '-', 0x2012: '-', 0x2013: '-', 0x2014: '-', 0x2015: '-',
        0x2026: '...', 0x00A0: ' ', 0x2044: '/', 0x2212: '-'
    };

    /* Confusables: non-Latin codepoints that read as Latin letters. Applied
       only inside words that mix scripts, so Russian stays Russian. */
    var CONFUSABLE = {
        // Cyrillic
        0x0410: 'A', 0x0412: 'B', 0x0415: 'E', 0x041A: 'K', 0x041C: 'M',
        0x041D: 'H', 0x041E: 'O', 0x0420: 'P', 0x0421: 'C', 0x0422: 'T',
        0x0423: 'Y', 0x0425: 'X', 0x0405: 'S', 0x0406: 'I', 0x0408: 'J',
        0x04AE: 'Y', 0x0492: 'F', 0x0417: '3',
        0x0430: 'a', 0x0432: 'b', 0x0435: 'e', 0x043A: 'k', 0x043C: 'm',
        0x043E: 'o', 0x0440: 'p', 0x0441: 'c', 0x0443: 'y', 0x0445: 'x',
        0x0455: 's', 0x0456: 'i', 0x0458: 'j', 0x04CF: 'l', 0x0501: 'd',
        0x04BB: 'h', 0x0491: 'r', 0x0433: 'r', 0x043D: 'h', 0x0442: 't',
        // Greek
        0x0391: 'A', 0x0392: 'B', 0x0395: 'E', 0x0396: 'Z', 0x0397: 'H',
        0x0399: 'I', 0x039A: 'K', 0x039C: 'M', 0x039D: 'N', 0x039F: 'O',
        0x03A1: 'P', 0x03A4: 'T', 0x03A5: 'Y', 0x03A7: 'X', 0x03BF: 'o',
        0x03B9: 'i', 0x03BD: 'v', 0x03C1: 'p', 0x03C5: 'u', 0x03BA: 'k',
        0x03C7: 'x', 0x03B5: 'e', 0x03B1: 'a', 0x03C3: 'o',
        // Armenian / Cherokee / other one-offs that show up in spoofing sets
        0x0585: 'o', 0x0578: 'n', 0x057D: 's', 0x13A0: 'D', 0x13C0: 'G',
        0x2C9F: 'o', 0xFF10: '0'
    };

    /* Context probes. Built with try/catch because a browser without Unicode
       property escapes should degrade to "no context known", not throw. */
    var RE_PICTO = build('\\p{Extended_Pictographic}');
    var RE_RI = build('[\\u{1F1E6}-\\u{1F1FF}]');
    var RE_JOINING = build('[\\p{Script=Arabic}\\p{Script=Hebrew}\\p{Script=Devanagari}\\p{Script=Bengali}' +
        '\\p{Script=Gurmukhi}\\p{Script=Gujarati}\\p{Script=Oriya}\\p{Script=Tamil}\\p{Script=Telugu}' +
        '\\p{Script=Kannada}\\p{Script=Malayalam}\\p{Script=Sinhala}\\p{Script=Thaana}\\p{Script=Syriac}' +
        '\\p{Script=Myanmar}\\p{Script=Khmer}\\p{Script=Mongolian}\\p{Script=Tibetan}\\p{Script=Nko}]');
    var RE_CJK = build('[\\p{Script=Han}\\p{Script=Hiragana}\\p{Script=Katakana}\\p{Script=Hangul}]');
    var RE_LATIN = build('\\p{Script=Latin}');
    var RE_MARK = build('\\p{M}');
    var RE_LETTER = build('[\\p{L}\\p{N}]');

    function build(src) {
        try { return new RegExp(src, 'u'); } catch (e) { return null; }
    }

    function isPicto(ch) {
        if (!ch) return false;
        if (RE_PICTO && RE_PICTO.test(ch)) return true;
        return RE_RI ? RE_RI.test(ch) : false;
    }
    function isJoiningScript(ch) { return !!ch && !!RE_JOINING && RE_JOINING.test(ch); }
    function isLatin(ch) { return !!ch && !!RE_LATIN && RE_LATIN.test(ch); }
    function isLetter(ch) { return !!ch && !!RE_LETTER && RE_LETTER.test(ch); }

    /* ---------------------------------------------------------------------
       Codepoint walk. Returns [{i, len, ch, cp}] over the whole string so
       surrogate pairs are handled once, here, and nowhere else.
    --------------------------------------------------------------------- */
    function codepoints(str) {
        var out = [], i = 0;
        while (i < str.length) {
            var cp = str.codePointAt(i);
            var len = cp > 0xFFFF ? 2 : 1;
            out.push({ i: i, len: len, cp: cp, ch: str.substr(i, len) });
            i += len;
        }
        return out;
    }

    /* Nearest visible neighbour, skipping the invisible run between. Emoji
       context has to look past a variation selector or a joiner to find the
       pictograph on the other side. */
    function neighbour(cps, from, dir) {
        var j = from + dir;
        while (j >= 0 && j < cps.length) {
            var cp = cps[j].cp;
            var skip = INVISIBLE[cp] || BIDI[cp] ||
                (cp >= 0xFE00 && cp <= 0xFE0F) || (cp >= 0xE0100 && cp <= 0xE01EF) ||
                (cp >= 0xE0000 && cp <= 0xE007F) || cp === 0x200C || cp === 0x200D ||
                (RE_MARK && RE_MARK.test(cps[j].ch));
            if (!skip) return cps[j].ch;
            j += dir;
        }
        return null;
    }

    /* ---------------------------------------------------------------------
       Hidden payload decoding. Finding the carrier characters is the useful
       half; showing what was actually written in them is the half that makes
       people believe the finding.
    --------------------------------------------------------------------- */
    var utf8 = (typeof TextDecoder !== 'undefined') ? new TextDecoder('utf-8', { fatal: false }) : null;

    function bytesToText(bytes) {
        if (utf8) {
            try { return utf8.decode(new Uint8Array(bytes)); } catch (e) { /* fall through */ }
        }
        return bytes.map(function (b) { return String.fromCharCode(b); }).join('');
    }

    function printableRatio(s) {
        if (!s.length) return 0;
        var ok = 0;
        for (var i = 0; i < s.length; i++) {
            var c = s.charCodeAt(i);
            if (c === 9 || c === 10 || c === 13 || (c >= 32 && c !== 127)) ok++;
        }
        return ok / s.length;
    }

    function decodePayloads(cps) {
        var payloads = [];
        var i = 0;

        while (i < cps.length) {
            var cp = cps[i].cp;

            // --- Unicode tag characters: cp - 0xE0000 is the ASCII byte.
            if (cp >= 0xE0000 && cp <= 0xE007F) {
                var start = i, bytes = [];
                while (i < cps.length && cps[i].cp >= 0xE0000 && cps[i].cp <= 0xE007F) {
                    var b = cps[i].cp - 0xE0000;
                    if (b >= 0x20 && b <= 0x7E) bytes.push(b);
                    i++;
                }
                if (bytes.length) {
                    payloads.push({
                        kind: 'Unicode tag characters',
                        at: cps[start].i,
                        chars: i - start,
                        decoded: bytesToText(bytes)
                    });
                }
                continue;
            }

            // --- Variation selectors: 256 codepoints, one per byte value.
            if ((cp >= 0xFE00 && cp <= 0xFE0F) || (cp >= 0xE0100 && cp <= 0xE01EF)) {
                var s2 = i, vbytes = [];
                while (i < cps.length) {
                    var c2 = cps[i].cp;
                    if (c2 >= 0xFE00 && c2 <= 0xFE0F) vbytes.push(c2 - 0xFE00);
                    else if (c2 >= 0xE0100 && c2 <= 0xE01EF) vbytes.push(c2 - 0xE0100 + 16);
                    else break;
                    i++;
                }
                // One selector is emoji presentation, not a message. Two or
                // more in a row is a byte string by any reasonable reading.
                if (vbytes.length >= 3) {
                    var txt = bytesToText(vbytes);
                    if (printableRatio(txt) > 0.8) {
                        payloads.push({
                            kind: 'Variation-selector bytes',
                            at: cps[s2].i,
                            chars: vbytes.length,
                            decoded: txt
                        });
                    }
                }
                continue;
            }

            // --- Zero-width binary. Two mappings cover almost everything in
            //     the wild; we accept a decode only if it lands on printable
            //     ASCII, which keeps false positives near zero.
            if (cp === 0x200B || cp === 0x200C || cp === 0x200D || cp === 0xFEFF) {
                var s3 = i, run = [];
                while (i < cps.length) {
                    var c3 = cps[i].cp;
                    if (c3 === 0x200B || c3 === 0x200C || c3 === 0x200D || c3 === 0xFEFF) { run.push(c3); i++; }
                    else break;
                }
                if (run.length >= 16) {
                    var got = decodeZeroWidthBinary(run);
                    if (got) {
                        payloads.push({
                            kind: 'Zero-width binary (' + got.mapping + ')',
                            at: cps[s3].i,
                            chars: run.length,
                            decoded: got.text
                        });
                    }
                }
                continue;
            }

            i++;
        }
        return payloads;
    }

    function decodeZeroWidthBinary(run) {
        var mappings = [
            { name: '200B=0, 200C=1', zero: 0x200B, one: 0x200C },
            { name: '200C=0, 200D=1', zero: 0x200C, one: 0x200D },
            { name: '200B=0, 200D=1', zero: 0x200B, one: 0x200D }
        ];
        for (var m = 0; m < mappings.length; m++) {
            var map = mappings[m], bits = '';
            var usable = true;
            for (var k = 0; k < run.length; k++) {
                if (run[k] === map.zero) bits += '0';
                else if (run[k] === map.one) bits += '1';
                else { usable = false; break; }
            }
            if (!usable || bits.length < 16 || bits.length % 8 !== 0) continue;
            var bytes = [];
            for (var p = 0; p < bits.length; p += 8) bytes.push(parseInt(bits.substr(p, 8), 2));
            var text = bytesToText(bytes);
            if (printableRatio(text) === 1) return { mapping: map.name, text: text };
        }
        return null;
    }

    /* ---------------------------------------------------------------------
       Mixed-script word detection for the confusables pass.
       A word is "mixed" when it contains Latin letters and also letters from
       a script whose characters we know to be Latin lookalikes. Only those
       words get folded.
    --------------------------------------------------------------------- */
    function confusableTargets(cps) {
        var targets = {};   // index in cps -> replacement
        var word = [], hasLatin = false, hasConfusable = false;

        function flush() {
            if (hasLatin && hasConfusable) {
                word.forEach(function (idx) {
                    var rep = CONFUSABLE[cps[idx].cp];
                    if (rep) targets[idx] = rep;
                });
            }
            word = []; hasLatin = false; hasConfusable = false;
        }

        for (var i = 0; i < cps.length; i++) {
            var ch = cps[i].ch, cp = cps[i].cp;
            var invisible = INVISIBLE[cp] || BIDI[cp] || cp === 0x200C || cp === 0x200D ||
                (cp >= 0xFE00 && cp <= 0xFE0F) || (cp >= 0xE0100 && cp <= 0xE01EF) ||
                (cp >= 0xE0000 && cp <= 0xE007F);
            if (invisible) continue;                 // does not break a word
            if (isLetter(ch) || cp === 0x27 || cp === 0x2019) {
                word.push(i);
                if (isLatin(ch)) hasLatin = true;
                if (CONFUSABLE[cp]) hasConfusable = true;
            } else {
                flush();
            }
        }
        flush();
        return targets;
    }

    /* ---------------------------------------------------------------------
       Compatibility folding (NFKC) for styled letterforms, one codepoint at
       a time so we never touch anything outside the ranges we mean.
    --------------------------------------------------------------------- */
    function compatFold(ch, cp) {
        var styled =
            (cp >= 0x1D400 && cp <= 0x1D7FF) ||   // mathematical alphanumeric
            (cp >= 0xFF01 && cp <= 0xFF5E) ||     // fullwidth ASCII
            (cp >= 0x2100 && cp <= 0x214F) ||     // letterlike symbols
            (cp >= 0x1F130 && cp <= 0x1F149) ||   // squared latin capitals
            (cp >= 0x1FBF0 && cp <= 0x1FBF9);     // segmented digits
        if (!styled) return null;
        if (!String.prototype.normalize) return null;
        var folded = ch.normalize('NFKC');
        if (folded === ch) return null;
        // Only accept a fold that lands on plain ASCII; ℡ → TEL is fine, but
        // we are not in the business of expanding ligatures or CJK squares.
        if (!/^[\x20-\x7E]{1,4}$/.test(folded)) return null;
        return folded;
    }

    /* ---------------------------------------------------------------------
       scan(text, opts) — the one entry point.
    --------------------------------------------------------------------- */
    function scan(text, opts) {
        opts = Object.assign(defaults(), opts || {});
        var cps = codepoints(text);
        var hasCJK = RE_CJK ? RE_CJK.test(text) : false;
        var confusables = opts.confusables ? confusableTargets(cps) : {};
        var payloads = decodePayloads(cps);

        var ops = [];               // {i, len, to, cat, cp, kept, note}
        var tally = {};             // key -> finding

        /* Tag characters and variation selectors arrive by the dozen — one
           row per codepoint turns a 14-character payload into 14 rows of
           noise. They are collapsed to a single row per action; the decoded
           payload above the table is where the detail actually belongs. */
        var GROUPED = {
            tags: { code: 'U+E0000–E007F', name: 'UNICODE TAG CHARACTERS' },
            variation: { code: 'U+FE00–FE0F, U+E0100–E01EF', name: 'VARIATION SELECTORS' }
        };

        function record(cp, cat, action, replacement, note, severity, index) {
            var group = GROUPED[cat];
            var key = cat + ':' + (group ? '*' : cp) + ':' + action;
            var f = tally[key];
            if (!f) {
                f = tally[key] = {
                    category: cat,
                    cp: cp,
                    code: group ? group.code : 'U+' + hex(cp),
                    name: group ? group.name : nameOf(cp),
                    action: action,
                    replacement: replacement,
                    note: note || '',
                    severity: severity,
                    count: 0,
                    at: []
                };
            }
            f.count++;
            if (f.at.length < 12) f.at.push(index);
        }

        for (var i = 0; i < cps.length; i++) {
            var c = cps[i], cp = c.cp, ch = c.ch;
            var prev = null, next = null;

            /* -- invisible ------------------------------------------------ */
            if (INVISIBLE[cp]) {
                if (opts.invisible) {
                    ops.push({ i: c.i, len: c.len, to: '' });
                    record(cp, 'invisible', 'removed', '', cp === 0xFEFF && c.i === 0 ? 'Byte-order mark at start of file.' : '', 'confirmed', c.i);
                } else {
                    record(cp, 'invisible', 'kept', null, 'Rule disabled.', 'confirmed', c.i);
                }
                continue;
            }

            /* -- unicode tag characters ----------------------------------- */
            if (cp >= 0xE0000 && cp <= 0xE007F) {
                // U+1F3F4 + tags + CANCEL TAG is how the England/Scotland/Wales
                // flags are actually spelled. That is a real emoji, not a mark.
                prev = neighbour(cps, i, -1);
                var inFlag = prev === '\u{1F3F4}';
                if (inFlag) {
                    record(cp, 'tags', 'kept', null, 'Part of an emoji tag sequence (regional flag).', 'likely-false-positive', c.i);
                } else if (opts.tags) {
                    ops.push({ i: c.i, len: c.len, to: '' });
                    record(cp, 'tags', 'removed', '', '', 'confirmed', c.i);
                } else {
                    record(cp, 'tags', 'kept', null, 'Rule disabled.', 'confirmed', c.i);
                }
                continue;
            }

            /* -- variation selectors -------------------------------------- */
            if ((cp >= 0xFE00 && cp <= 0xFE0F) || (cp >= 0xE0100 && cp <= 0xE01EF)) {
                prev = neighbour(cps, i, -1);
                var prevIsVS = i > 0 && ((cps[i - 1].cp >= 0xFE00 && cps[i - 1].cp <= 0xFE0F) ||
                    (cps[i - 1].cp >= 0xE0100 && cps[i - 1].cp <= 0xE01EF));
                // FE0F directly after a pictograph or a keycap base is emoji
                // presentation. A *second* selector on the same base is not.
                var emojiPresentation = cp === 0xFE0F && !prevIsVS &&
                    (isPicto(prev) || (prev !== null && /^[0-9#*]$/.test(prev)));
                // FE00–FE0F after a CJK ideograph selects a glyph variant.
                var cjkVariant = !prevIsVS && cp >= 0xFE00 && cp <= 0xFE0F &&
                    prev !== null && RE_CJK && RE_CJK.test(prev);
                if (emojiPresentation || cjkVariant) {
                    record(cp, 'variation', 'kept', null,
                        emojiPresentation ? 'Emoji presentation selector on a pictograph.' : 'Glyph variant on a CJK ideograph.',
                        'likely-false-positive', c.i);
                } else if (opts.variation) {
                    ops.push({ i: c.i, len: c.len, to: '' });
                    record(cp, 'variation', 'removed', '', '', 'confirmed', c.i);
                } else {
                    record(cp, 'variation', 'kept', null, 'Rule disabled.', 'confirmed', c.i);
                }
                continue;
            }

            /* -- joiners / non-joiners ------------------------------------ */
            if (cp === 0x200C || cp === 0x200D) {
                prev = neighbour(cps, i, -1);
                next = neighbour(cps, i, 1);
                var structural =
                    (cp === 0x200D && (isPicto(prev) || isPicto(next))) ||
                    isJoiningScript(prev) || isJoiningScript(next);
                if (structural) {
                    record(cp, 'joiners', 'kept', null,
                        cp === 0x200D && (isPicto(prev) || isPicto(next))
                            ? 'Joins an emoji sequence.'
                            : 'Structural in a joining script.',
                        'likely-false-positive', c.i);
                } else if (opts.joiners) {
                    ops.push({ i: c.i, len: c.len, to: '' });
                    record(cp, 'joiners', 'removed', '', 'Between characters where it has no rendering effect.', 'confirmed', c.i);
                } else {
                    record(cp, 'joiners', 'kept', null, 'Rule disabled.', 'probable', c.i);
                }
                continue;
            }

            /* -- bidi controls -------------------------------------------- */
            if (BIDI[cp]) {
                if (opts.bidi) {
                    ops.push({ i: c.i, len: c.len, to: '' });
                    record(cp, 'bidi', 'removed', '', '', 'probable', c.i);
                } else {
                    record(cp, 'bidi', 'kept', null, 'Rule disabled.', 'probable', c.i);
                }
                continue;
            }

            /* -- line / paragraph separators ------------------------------ */
            if (cp === 0x2028 || cp === 0x2029) {
                if (opts.lineSeparators) {
                    var nl = cp === 0x2029 ? '\n\n' : '\n';
                    ops.push({ i: c.i, len: c.len, to: nl });
                    record(cp, 'lineSeparators', 'replaced', '\\n', '', 'informational', c.i);
                } else {
                    record(cp, 'lineSeparators', 'kept', null, 'Rule disabled.', 'informational', c.i);
                }
                continue;
            }

            /* -- exotic spaces -------------------------------------------- */
            if (SPACES[cp] !== undefined) {
                if (cp === 0x3000 && hasCJK) {
                    record(cp, 'spaces', 'kept', null, 'Ordinary punctuation in CJK text.', 'likely-false-positive', c.i);
                } else if (opts.spaces) {
                    ops.push({ i: c.i, len: c.len, to: SPACES[cp] });
                    record(cp, 'spaces', 'replaced', 'U+0020', '', 'informational', c.i);
                } else {
                    record(cp, 'spaces', 'kept', null, 'Rule disabled.', 'informational', c.i);
                }
                continue;
            }

            /* -- homoglyphs ------------------------------------------------ */
            if (confusables[i] !== undefined) {
                ops.push({ i: c.i, len: c.len, to: confusables[i] });
                record(cp, 'confusables', 'replaced', confusables[i],
                    'Sat inside a word that was otherwise Latin.', 'confirmed', c.i);
                continue;
            }
            if (!opts.confusables && CONFUSABLE[cp] !== undefined) {
                record(cp, 'confusables', 'kept', null, 'Rule disabled.', 'probable', c.i);
                continue;
            }

            /* -- styled letterforms ---------------------------------------- */
            if (opts.compat) {
                var folded = compatFold(ch, cp);
                if (folded) {
                    ops.push({ i: c.i, len: c.len, to: folded });
                    record(cp, 'compat', 'replaced', folded, '', 'probable', c.i);
                    continue;
                }
            }

            /* -- typography ------------------------------------------------ */
            if (opts.typography && TYPOGRAPHY[cp] !== undefined) {
                ops.push({ i: c.i, len: c.len, to: TYPOGRAPHY[cp] });
                record(cp, 'typography', 'replaced', TYPOGRAPHY[cp], '', 'informational', c.i);
                continue;
            }
        }

        ops.sort(function (a, b) { return a.i - b.i; });

        // Apply
        var out = [], pos = 0;
        for (var k = 0; k < ops.length; k++) {
            var op = ops[k];
            if (op.i < pos) continue;                    // never overlap
            out.push(text.slice(pos, op.i));
            out.push(op.to);
            pos = op.i + op.len;
        }
        out.push(text.slice(pos));
        var cleaned = out.join('');

        // Line-level tidy runs last, on the already-cleaned text.
        var tidyCount = 0;
        if (opts.tidy) {
            var before = cleaned;
            cleaned = cleaned.replace(/[ \t]+$/gm, '');
            cleaned = cleaned.replace(/\n{3,}/g, '\n\n');
            if (before !== cleaned) tidyCount = 1;
        }

        var findings = Object.keys(tally).map(function (k2) { return tally[k2]; });
        findings.sort(function (a, b) {
            if (a.action !== b.action) return a.action === 'kept' ? 1 : -1;
            return b.count - a.count;
        });

        var changed = 0;
        findings.forEach(function (f) { if (f.action !== 'kept') changed += f.count; });

        return {
            cleaned: cleaned,
            findings: findings,
            payloads: payloads,
            ops: ops,
            stats: {
                inputChars: text.length,
                outputChars: cleaned.length,
                inputCodepoints: cps.length,
                changed: changed,
                tidied: tidyCount,
                categories: findings.reduce(function (acc, f) {
                    if (f.action !== 'kept') acc[f.category] = (acc[f.category] || 0) + f.count;
                    return acc;
                }, {})
            }
        };
    }

    /* ---------------------------------------------------------------------
       Highlighted rendering of the original, so the invisible characters
       become visible. Returns HTML; caller inserts it.
    --------------------------------------------------------------------- */
    function escapeHtml(s) {
        return s.replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }

    function highlight(text, result, limit) {
        limit = limit || 40000;
        var truncated = text.length > limit;
        var slice = truncated ? text.slice(0, limit) : text;
        var ops = result.ops.filter(function (o) { return o.i < slice.length; });
        var html = [], pos = 0;
        for (var i = 0; i < ops.length; i++) {
            var op = ops[i];
            if (op.i < pos) continue;
            html.push(escapeHtml(slice.slice(pos, op.i)));
            var original = slice.substr(op.i, op.len);
            var cp = original.codePointAt(0);
            var label = op.to === '' ? '∅' : escapeHtml(op.to);
            html.push('<mark class="hl" title="U+' + hex(cp) + ' ' + escapeHtml(nameOf(cp)) +
                (op.to === '' ? ' — removed' : ' — replaced with ' + escapeHtml(JSON.stringify(op.to))) +
                '">' + label + '</mark>');
            pos = op.i + op.len;
        }
        html.push(escapeHtml(slice.slice(pos)));
        if (truncated) html.push('\n\n<span class="hl-more">… preview truncated at ' +
            limit.toLocaleString() + ' characters. The full text is still cleaned.</span>');
        return html.join('');
    }

    WMR.text = {
        scan: scan,
        highlight: highlight,
        CATEGORIES: CATEGORIES,
        defaults: defaults,
        nameOf: nameOf,
        hex: hex,
        escapeHtml: escapeHtml,
        _internal: { codepoints: codepoints, decodePayloads: decodePayloads, confusableTargets: confusableTargets }
    };
})(typeof window !== 'undefined' ? window : globalThis);
