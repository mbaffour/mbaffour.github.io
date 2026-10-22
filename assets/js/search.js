/* search.js — site-wide search (⌘K / Ctrl+K / "/").
 *
 * One script for every page. It builds its own dialog, loads the shared data
 * files it needs on first open (site-data.js, builds-data.js, posts-data.js),
 * and resolves every link against the site root, so the same results work from
 * /, /blog/ or anywhere else.
 *
 * Opened by: ⌘K / Ctrl+K, "/", any element with [data-search-open] or
 * #cmdkOpen, and, on pages that have neither, a floating Search button.
 *
 * Matching: every word typed must appear somewhere in an item (title, tags,
 * tech, blurb), as a word prefix; a few lab synonyms widen a word
 * (titer → PFU, colony → CFU, cloning → Gibson…). Titles weigh most.
 */
(function () {
    var SCRIPT = document.currentScript;
    var ROOT = new URL('../../', SCRIPT ? SCRIPT.src : location.href);
    function abs(h) { try { return new URL(h, ROOT).href; } catch (e) { return h; } }
    function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
    function plain(s) { var d = document.createElement('div'); d.innerHTML = s || ''; return d.textContent; }
    var mac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);

    /* ---------- data ---------- */
    function load(src) {
        return new Promise(function (ok) {
            var s = document.createElement('script');
            s.src = abs(src); s.onload = s.onerror = function () { ok(); };
            document.head.appendChild(s);
        });
    }
    var ready = null;
    function data() {
        if (ready) return ready;
        var need = [];
        if (typeof tools === 'undefined') need.push('assets/js/site-data.js');
        if (typeof builds === 'undefined') need.push('assets/js/builds-data.js');
        if (typeof posts === 'undefined') need.push('assets/js/posts-data.js');
        ready = Promise.all(need.map(load)).then(build);
        return ready;
    }

    var PAGES = [
        ['Research focus', 'The N4 lysis model, bench methods', '#research'],
        ['Lysis curve playground', 'Tune infection parameters and watch the curve', '#playground'],
        ['Publications', 'Preprint and papers', '#publications'],
        ['Talks and posters', 'Conference talks and posters', '#talks'],
        ['Research software', 'All 19 open tools', '#tools'],
        ['Teaching and mentoring', '700+ enrollments across 9 courses', '#teaching'],
        ['Recognition and service', 'Fellowships, awards, outreach', '#recognition'],
        ['About', 'Who I am', '#about'],
        ['Contact', 'Get in touch', '#contact'],
        ['Journey', 'From Ghana to phage N4, in figures', 'journey.html'],
        ['Side builds', 'Apps built outside the lab, and the TailFiber game', 'builds.html'],
        ['Off the pitch', 'Football, and the Life in the Lab gallery', 'beyond.html'],
        ['Blog', 'Every post, with filters', 'blog/'],
        ['CV (PDF)', 'Download the CV', 'cv-resume/Michael_Baffour_Awuah_CV.pdf']
    ];
    var LINKS = [
        ['GitHub', '@mbaffour', 'https://github.com/mbaffour'],
        ['Google Scholar', 'Citations', 'https://scholar.google.com/citations?user=e5_h_2YAAAAJ&hl=en'],
        ['ORCID', '0009-0007-9036-413X', 'https://orcid.org/0009-0007-9036-413X'],
        ['LinkedIn', 'Profile', 'https://www.linkedin.com/in/mba-101b/'],
        ['Email', 'baffour@tamu.edu', 'mailto:baffour@tamu.edu']
    ];
    var SYN = {
        titer: ['pfu', 'plaque', 'titre'], titre: ['titer', 'pfu'], plaques: ['plaque'],
        colony: ['cfu', 'colonies'], colonies: ['cfu', 'colony'], count: ['cfu', 'pfu', 'counts'],
        cloning: ['gibson', 'assembly', 'plasmid'], plasmid: ['gibson', 'cloning'], pcr: ['gibson', 'cloning'],
        microscopy: ['morphology', 'cellmorphr', 'figurelab', 'image'], shape: ['morphology', 'morphometry'],
        cell: ['cellmorphr', 'morphology'], image: ['microscopy', 'photo', 'figure'],
        structure: ['alphafold', 'protein', 'pdb'], protein: ['alphafold', 'structure', 'ppi'], fold: ['alphafold'],
        homolog: ['homologue', 'hmm'], homologue: ['hmm', 'homolog'], hmm: ['homologue'],
        sequence: ['fasta', 'fastq', 'genomics', 'sequences'], sequencing: ['fastq', 'reads', 'genomics'],
        reads: ['fastq', 'qc'], dedupe: ['seqsieve', 'deduplication'], duplicate: ['seqsieve', 'deduplication'],
        growth: ['lysis', 'od600', 'curve'], od: ['od600'], kill: ['killcurveplot', 'lysis'], curve: ['curves', 'lysis'],
        plate: ['96-well', 'dilution', 'plates'], pipetting: ['dilution', 'gibson', 'volumes'],
        figure: ['figures', 'figurelab', 'plot'], plot: ['plots', 'figure', 'viz'], stats: ['statistics'],
        watermark: ['unicode', 'invisible'], game: ['tug', 'tailfiber', 'number'], privacy: ['watermark']
    };

    var ITEMS = [], GROUPS;
    function item(kind, title, sub, text, href, actions, extra) {
        var o = { kind: kind, title: title, sub: sub, href: abs(href), actions: actions || [],
            hay: { t: title.toLowerCase(), k: (text.k || '').toLowerCase(), b: (text.b || '').toLowerCase() } };
        for (var x in extra) o[x] = extra[x];
        ITEMS.push(o); return o;
    }
    function acts(list) { return list.filter(function (a) { return a[1]; }).map(function (a) { return { label: a[0], href: abs(a[1]) }; }); }
    function build() {
        ITEMS = [];
        var T = typeof tools === 'undefined' ? [] : tools;
        var B = typeof builds === 'undefined' ? [] : builds;
        var P = typeof posts === 'undefined' ? [] : posts;
        var U = typeof publications === 'undefined' ? [] : publications;
        T.forEach(function (t) {
            var primary = t.app || t.blog || t.repo;
            var isRepo = /github\.com/.test(primary);
            item('tool', t.title, t.blurb, { k: (t.tech || []).join(' ') + ' ' + (t.label || ''), b: t.blurb }, primary,
                acts([[isRepo ? 'Source' : 'Open', primary], ['Write-up', t.blog !== primary && t.blog], ['Source', !isRepo && t.repo]]));
        });
        B.forEach(function (b) {
            item('build', b.title, b.blurb, { k: (b.tech || []).join(' '), b: b.blurb }, b.app || b.repo,
                acts([['Open', b.app], ['Write-up', b.blog], ['Source', b.repo]]));
        });
        P.forEach(function (p) {
            item('post', p.title, p.date + ' · ' + p.tags.join(' · '), { k: p.tags.join(' '), b: p.blurb }, p.url, [], { anim: p.animated });
        });
        U.forEach(function (p) {
            var j = plain(p.journal);
            var href = p.doi ? (/^http/.test(p.doi) ? p.doi : 'https://doi.org/' + p.doi) : (p.kind === 'paper' ? '#publications' : '#talks');
            item('pub', plain(p.title), (p.kind || 'paper') + ' · ' + j + ' · ' + p.year, { k: (p.kind || '') + ' ' + j, b: plain(p.authors) }, href, []);
        });
        PAGES.forEach(function (g) { item('page', g[0], g[1], { k: g[1] }, g[2], []); });
        LINKS.forEach(function (g) { item('link', g[0], g[1], { k: g[1] }, g[2], []); });
        GROUPS = [
            ['tool', 'Research tools'], ['build', 'Side builds'], ['post', 'Blog'],
            ['page', 'Pages'], ['pub', 'Papers, talks and posters'], ['link', 'Elsewhere']
        ];
    }

    function words(q) { return q.toLowerCase().replace(/[^a-z0-9µ\-\s]/g, ' ').split(/\s+/).filter(Boolean); }
    function hit(hay, w) {
        // word-prefix match ("plaq" finds "plaque"; "ma" does not find "format")
        var i = hay.indexOf(w);
        while (i !== -1) {
            if (i === 0 || /[^a-z0-9]/.test(hay[i - 1])) return true;
            i = hay.indexOf(w, i + 1);
        }
        return false;
    }
    var KW = { tool: 3, build: 2, post: 1.5, page: 1.5, pub: 1, link: 0.5 };
    function score(it, ws) {
        var total = 0;
        for (var n = 0; n < ws.length; n++) {
            var alts = [ws[n]].concat(SYN[ws[n]] || []), best = 0;
            for (var a = 0; a < alts.length; a++) {
                var w = alts[a], f = a ? 0.7 : 1;
                if (hit(it.hay.t, w)) best = Math.max(best, (it.hay.t.indexOf(w) === 0 ? 12 : 8) * f);
                else if (hit(it.hay.k, w)) best = Math.max(best, 4 * f);
                else if (hit(it.hay.b, w)) best = Math.max(best, 2 * f);
            }
            if (!best) return 0;
            total += best;
        }
        return total + KW[it.kind];
    }

    /* ---------- dialog ---------- */
    var ICON = {
        tool: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.5-.5-.5-2.5z"/>',
        build: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
        post: '<path d="M6 3h9l4 4v14H6z"/><path d="M9 12h7M9 16h7M9 8h3"/>',
        pub: '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>',
        page: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
        link: '<path d="M10 14a4 4 0 0 0 6 0l3-3a4 4 0 0 0-6-6l-1 1"/><path d="M14 10a4 4 0 0 0-6 0l-3 3a4 4 0 0 0 6 6l1-1"/>'
    };
    var FILTERS = [['all', 'All'], ['tools', 'Tools'], ['post', 'Blog'], ['pub', 'Papers'], ['page', 'Pages']];
    var root, input, list, chips, filter = 'all', rows = [], active = 0, lastFocus = null, built = false;

    function ui() {
        if (built) return;
        built = true;
        root = document.createElement('div');
        root.className = 'sx';
        root.hidden = true;
        root.innerHTML =
            '<div class="sx-scrim" data-close></div>' +
            '<div class="sx-panel" role="dialog" aria-modal="true" aria-label="Search the site">' +
            '<div class="sx-top"><svg class="sx-mag" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>' +
            '<input class="sx-input" type="search" placeholder="Search tools, posts, papers…" aria-label="Search tools, posts, papers and pages" autocomplete="off" spellcheck="false" aria-describedby="sx-status">' +
            '<button class="sx-x" type="button" data-close aria-label="esc: close search">esc</button></div>' +
            '<div class="sx-chips" role="group" aria-label="Show"></div>' +
            '<p class="sx-status" id="sx-status" aria-live="polite"></p>' +
            '<div class="sx-list" role="region" aria-label="Results"></div>' +
            '<div class="sx-foot" aria-hidden="true"><span><kbd>↑</kbd><kbd>↓</kbd> move</span><span><kbd>↵</kbd> open</span><span><kbd>esc</kbd> close</span><span class="sx-tip">Try “titer”, “microscopy” or “AlphaFold”</span></div>' +
            '</div>';
        document.body.appendChild(root);
        input = root.querySelector('.sx-input');
        list = root.querySelector('.sx-list');
        chips = root.querySelector('.sx-chips');
        root.addEventListener('click', function (e) {
            if (e.target.closest('[data-close]')) close();
            var a = e.target.closest('a');
            if (a && a.target !== '_blank') close(true);
        });
        input.addEventListener('input', function () { render(); });
        root.addEventListener('keydown', key);
        chips.addEventListener('click', function (e) {
            var b = e.target.closest('button'); if (!b) return;
            filter = b.getAttribute('data-f'); render(); input.focus();
        });
    }

    function pass(it) {
        if (filter === 'all') return true;
        if (filter === 'tools') return it.kind === 'tool' || it.kind === 'build';
        if (filter === 'page') return it.kind === 'page' || it.kind === 'link';
        return it.kind === filter;
    }
    function rowHTML(it, i) {
        var ext = !/^https?:\/\/[^/]*mbaffour\.github\.io|^mailto/.test(it.href) && it.href.indexOf(ROOT.origin) !== 0;
        var tgt = ext ? ' target="_blank" rel="noopener"' : '';
        var acts = it.actions.slice(1).map(function (a) {
            return '<a class="sx-act" href="' + esc(a.href) + '" target="_blank" rel="noopener" tabindex="-1">' + esc(a.label) + '</a>';
        }).join('');
        var lead = it.actions[0] ? it.actions[0].label : ext ? 'Open' : 'Go';
        return '<div class="sx-row" data-i="' + i + '">' +
            '<a class="sx-main" href="' + esc(it.href) + '"' + tgt + ' tabindex="-1">' +
            '<svg class="sx-ic sx-ic-' + it.kind + '" viewBox="0 0 24 24" aria-hidden="true">' + ICON[it.kind] + '</svg>' +
            '<span class="sx-txt"><span class="sx-t">' + esc(it.title) + (it.anim ? '<span class="sx-anim">animated</span>' : '') + '</span>' +
            '<span class="sx-s">' + esc(it.sub) + '</span></span>' +
            '<span class="sx-go">' + esc(lead) + (ext ? ' ↗' : ' →') + '</span></a>' +
            (acts ? '<span class="sx-acts">' + acts + '</span>' : '') + '</div>';
    }
    function render() {
        var q = input.value.trim(), ws = words(q), html = '';
        var counts = { all: 0, tools: 0, post: 0, pub: 0, page: 0 };
        var found = ITEMS.map(function (it) { return { it: it, s: ws.length ? score(it, ws) : 1 }; }).filter(function (x) { return x.s > 0; });
        found.forEach(function (x) {
            counts.all++;
            var k = x.it.kind; counts[k === 'tool' || k === 'build' ? 'tools' : k === 'link' ? 'page' : k]++;
        });
        chips.innerHTML = FILTERS.map(function (f) {
            return '<button type="button" class="sx-chip" data-f="' + f[0] + '" aria-pressed="' + (filter === f[0]) + '">' + f[1] + ' <span>' + counts[f[0]] + '</span></button>';
        }).join('');
        found = found.filter(function (x) { return pass(x.it); });
        rows = [];
        if (!found.length) {
            list.innerHTML = '<div class="sx-empty">Nothing matches “' + esc(q) + '”. Try a technique (plaque, AlphaFold, FASTQ) or a tool name.</div>';
            announce('No results');
            return;
        }
        if (ws.length) {
            found.sort(function (a, b) { return b.s - a.s; });
            html += '<div class="sx-h">' + found.length + ' result' + (found.length > 1 ? 's' : '') + '</div>';
            found.forEach(function (x) { html += rowHTML(x.it, rows.length); rows.push(x.it); });
        } else {
            GROUPS.forEach(function (g) {
                var gs = found.filter(function (x) { return x.it.kind === g[0]; });
                if (!gs.length) return;
                html += '<div class="sx-h">' + g[1] + ' <span>' + gs.length + '</span></div>';
                gs.forEach(function (x) { html += rowHTML(x.it, rows.length); rows.push(x.it); });
            });
        }
        list.innerHTML = html;
        list.scrollTop = 0;
        select(0);
        announce(ws.length ? rows.length + ' results. Down arrow to move through them.' : '');
    }
    var announceT;
    function announce(msg) {
        clearTimeout(announceT);
        announceT = setTimeout(function () { root.querySelector('.sx-status').textContent = msg; }, 450);
    }
    function select(i, focus) {
        var els = list.querySelectorAll('.sx-row');
        if (!els.length) return;
        active = Math.max(0, Math.min(els.length - 1, i));
        els.forEach(function (el, k) { el.classList.toggle('on', k === active); });
        var el = els[active];
        if (focus) el.querySelector('.sx-main').focus({ preventScroll: true });
        var top = el.offsetTop, bot = top + el.offsetHeight;
        if (top < list.scrollTop + 30) list.scrollTop = top - 30;
        else if (bot > list.scrollTop + list.clientHeight) list.scrollTop = bot - list.clientHeight + 8;
    }
    function key(e) {
        if (e.key === 'Escape') { e.preventDefault(); close(); return; }
        var inList = list.contains(document.activeElement);
        // arrows move real focus through the results (the input keeps the first one highlighted)
        if (e.key === 'ArrowDown') { e.preventDefault(); select(inList ? active + 1 : active, true); }
        else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (!inList) return;
            if (active === 0) input.focus(); else select(active - 1, true);
        }
        else if (inList && e.key.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey) { input.focus(); }
        else if (e.key === 'Enter' && document.activeElement === input) {
            var el = list.querySelectorAll('.sx-row .sx-main')[active];
            if (el) { e.preventDefault(); el.click(); }
        } else if (e.key === 'Tab') {
            // keep focus inside: the input, the filters, the highlighted result's links, close
            var f = [].slice.call(root.querySelectorAll('.sx-input, .sx-chip, .sx-row.on a, .sx-x'));
            var i = f.indexOf(document.activeElement);
            e.preventDefault();
            f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
        }
    }
    function open() {
        ui();
        if (!root.hidden) return;
        lastFocus = document.activeElement;
        root.hidden = false;
        document.documentElement.classList.add('sx-open');
        input.value = '';
        filter = 'all';
        list.innerHTML = '<div class="sx-empty">Loading…</div>';
        requestAnimationFrame(function () { root.classList.add('in'); input.focus(); });
        data().then(render);
    }
    function close(navigating) {
        if (!root || root.hidden) return;
        root.classList.remove('in');
        root.hidden = true;
        document.documentElement.classList.remove('sx-open');
        if (!navigating && lastFocus && lastFocus.focus) lastFocus.focus();
    }

    document.addEventListener('keydown', function (e) {
        if (e.defaultPrevented) return;   // the page handled the key itself (the blog index's own "/" search)
        var t = e.target, typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
        if ((e.metaKey || e.ctrlKey) && !e.altKey && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (root && !root.hidden) close(); else open();
        } else if (e.key === '/' && !typing && !(root && !root.hidden)) {
            e.preventDefault(); open();
        }
    });
    document.addEventListener('click', function (e) {
        if (e.target.closest('[data-search-open], #cmdkOpen')) { e.preventDefault(); open(); }
    });

    function fab() {
        if (document.querySelector('[data-search-open], #cmdkOpen')) return;
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'sx-fab';
        b.setAttribute('data-search-open', '');
        b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg><span>Search</span><kbd aria-hidden="true">' + (mac ? '⌘K' : 'Ctrl K') + '</kbd>';
        document.body.appendChild(b);
        // out of the way while reading down the page, back on any scroll up
        var lastY = window.scrollY, tick = false;
        window.addEventListener('scroll', function () {
            if (tick) return; tick = true;
            requestAnimationFrame(function () {
                var y = window.scrollY;
                if (Math.abs(y - lastY) > 6) { b.classList.toggle('sx-away', y > lastY && y > 200); lastY = y; }
                tick = false;
            });
        }, { passive: true });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fab); else fab();
    window.siteSearch = { open: open, close: close };
})();
