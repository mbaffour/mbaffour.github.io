/* bytes.js — small byte helpers shared by the image, PDF and container
   cleaners. Nothing clever, just the handful of primitives you end up
   rewriting three times otherwise.
   ========================================================================= */
(function (global) {
    'use strict';

    var WMR = global.WMR || (global.WMR = {});

    var CRC_TABLE = (function () {
        var t = new Uint32Array(256);
        for (var n = 0; n < 256; n++) {
            var c = n;
            for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
            t[n] = c >>> 0;
        }
        return t;
    })();

    function crc32(buf, seed) {
        var c = (seed === undefined ? 0xFFFFFFFF : (seed ^ 0xFFFFFFFF)) >>> 0;
        for (var i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
        return (c ^ 0xFFFFFFFF) >>> 0;
    }

    function ascii(buf, off, len) {
        var s = '';
        for (var i = 0; i < len; i++) {
            var b = buf[off + i];
            if (b === undefined) break;
            s += String.fromCharCode(b);
        }
        return s;
    }

    function asciiBytes(str) {
        var out = new Uint8Array(str.length);
        for (var i = 0; i < str.length; i++) out[i] = str.charCodeAt(i) & 0xFF;
        return out;
    }

    function utf8Bytes(str) {
        if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(str);
        return asciiBytes(unescape(encodeURIComponent(str)));
    }

    function utf8Text(buf) {
        if (typeof TextDecoder !== 'undefined') {
            try { return new TextDecoder('utf-8', { fatal: false }).decode(buf); } catch (e) { /* fall through */ }
        }
        return ascii(buf, 0, buf.length);
    }

    function concat(chunks) {
        var total = 0, i;
        for (i = 0; i < chunks.length; i++) total += chunks[i].length;
        var out = new Uint8Array(total), at = 0;
        for (i = 0; i < chunks.length; i++) { out.set(chunks[i], at); at += chunks[i].length; }
        return out;
    }

    function startsWith(buf, sig, off) {
        off = off || 0;
        for (var i = 0; i < sig.length; i++) if (buf[off + i] !== sig[i]) return false;
        return true;
    }

    /* Byte-level substring search. Used to find XMP packets and JUMBF boxes
       without parsing every container format properly. */
    function indexOfBytes(haystack, needle, from) {
        from = from || 0;
        var first = needle[0];
        var limit = haystack.length - needle.length;
        outer:
        for (var i = from; i <= limit; i++) {
            if (haystack[i] !== first) continue;
            for (var j = 1; j < needle.length; j++) if (haystack[i + j] !== needle[j]) continue outer;
            return i;
        }
        return -1;
    }

    function formatBytes(n) {
        if (n < 1024) return n + ' B';
        if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
        return (n / (1024 * 1024)).toFixed(2) + ' MB';
    }

    /* A short, safe preview of whatever was hiding in a metadata field. */
    function preview(str, max) {
        max = max || 220;
        var s = String(str).replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '\u00b7').replace(/\s+/g, ' ').trim();
        return s.length > max ? s.slice(0, max) + '…' : s;
    }

    WMR.bytes = {
        crc32: crc32,
        ascii: ascii,
        asciiBytes: asciiBytes,
        utf8Bytes: utf8Bytes,
        utf8Text: utf8Text,
        concat: concat,
        startsWith: startsWith,
        indexOfBytes: indexOfBytes,
        formatBytes: formatBytes,
        preview: preview
    };
})(typeof window !== 'undefined' ? window : globalThis);
