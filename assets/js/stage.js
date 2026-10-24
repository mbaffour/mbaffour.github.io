/* stage.js — the homepage's choreography (body.stage, styles in stage.css).
 *
 *   preloader       the wordmark rises, a counter runs to 100, the paper lifts
 *   smooth scroll   Lenis (assets/vendor/lenis.min.js), paused under overlays
 *   the stage       --cov 0→1 as the prologue slides over the hero; the capsid hears it
 *   peeks           underlined phrases show their picture beside the pointer
 *   Act II          tool cards scatter → stack → ring → orbit → fly out, by scroll
 *   Act III         each bench step lights as it crosses the middle of the screen
 *   cursor, clock   a trailing ring on pointer devices; College Station time
 *   menu            focus and scroll handling for the full-screen menu
 * Reduced motion: no preloader, no smooth scroll, no ring choreography (the cards
 * sit in a grid), steps all lit. Every piece checks for its own markup.
 */
(function () {
    var html = document.documentElement;
    var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    var fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
    function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
    function seg(p, a, b) { return clamp((p - a) / (b - a), 0, 1); }
    function ease(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
    function lerp(a, b, k) { return a + (b - a) * k; }

    /* ---------- preloader ---------- */
    var pre = document.querySelector('.pre');
    function ready() { html.classList.add('ready'); setTimeout(function () { if (pre) pre.style.display = 'none'; }, 1100); }
    if (!pre || reduce) { if (pre) pre.style.display = 'none'; html.classList.add('ready'); }
    else {
        var seen = false;
        try { seen = sessionStorage.getItem('mba-pre') === '1'; sessionStorage.setItem('mba-pre', '1'); } catch (e) {}
        var dur = seen ? 450 : 1500, count = pre.querySelector('.pre-count'), bar = pre.querySelector('.pre-bar i'), t0 = performance.now();
        requestAnimationFrame(function () { html.classList.add('pre-in'); });
        (function tick(now) {
            var k = clamp((now - t0) / dur, 0, 1), e = 1 - Math.pow(1 - k, 2.2);
            if (count) count.textContent = ('00' + Math.round(e * 100)).slice(-3);
            if (bar) bar.style.transform = 'scaleX(' + e.toFixed(3) + ')';
            if (k < 1) requestAnimationFrame(tick); else setTimeout(ready, seen ? 80 : 260);
        })(t0);
    }

    /* ---------- smooth scroll ---------- */
    var lenis = null;
    if (!reduce && typeof Lenis !== 'undefined') {
        lenis = new Lenis({ lerp: 0.09, smoothWheel: true, wheelMultiplier: 0.95 });
        (function raf(t) { lenis.raf(t); requestAnimationFrame(raf); })(performance.now());
        window.lenis = lenis;
        // in-page links glide instead of jumping
        document.addEventListener('click', function (e) {
            var a = e.target.closest('a[href^="#"]');
            if (!a || e.defaultPrevented || e.metaKey || e.ctrlKey) return;
            var id = a.getAttribute('href');
            if (id.length < 2) return;
            var el = document.getElementById(id.slice(1));
            if (!el) return;
            e.preventDefault();
            lenis.start();
            lenis.scrollTo(el, { offset: id === '#hero' ? 0 : -24, duration: 1.4 });
            history.replaceState(null, '', id);
        });
        // overlays (search, the menu, the lightbox) hold the page still
        var lb = document.getElementById('lightbox'), menu = document.getElementById('navLinks');
        function hold() {
            var open = html.classList.contains('sx-open') || (menu && menu.classList.contains('open')) || (lb && (lb.classList.contains('open') || lb.classList.contains('active')));
            if (open) lenis.stop(); else lenis.start();
        }
        var mo = new MutationObserver(hold);
        mo.observe(html, { attributes: true, attributeFilter: ['class'] });
        if (menu) mo.observe(menu, { attributes: true, attributeFilter: ['class'] });
        if (lb) mo.observe(lb, { attributes: true, attributeFilter: ['class'] });
    }
    function onScroll(fn) {
        if (lenis) lenis.on('scroll', fn);
        window.addEventListener('scroll', fn, { passive: true });
        window.addEventListener('resize', fn);
        fn();
    }

    /* ---------- the stage: covered as the prologue slides over ---------- */
    var hero = document.getElementById('hero');
    if (hero) onScroll(function () {
        var k = clamp(window.scrollY / (window.innerHeight || 1), 0, 1);
        hero.style.setProperty('--cov', k.toFixed(3));
        if (window.capsid) window.capsid.scroll(k);
    });

    /* ---------- clock ---------- */
    var clock = document.getElementById('localClock');
    if (clock) {
        var fmt;
        try { fmt = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Chicago' }); } catch (e) {}
        var tickClock = function () { if (fmt) clock.textContent = fmt.format(new Date()); };
        tickClock(); setInterval(tickClock, 20000);
    }

    /* ---------- peeks: a phrase's picture, beside the pointer ---------- */
    var chips = document.querySelectorAll('.chip[data-img]');
    if (chips.length && fine) {
        var peek = document.createElement('div');
        peek.className = 'peek'; peek.setAttribute('aria-hidden', 'true');
        peek.innerHTML = '<img alt="">';
        document.body.appendChild(peek);
        var pimg = peek.firstChild, px = 0, py = 0, tx = 0, ty = 0, showing = false;
        (function follow() {
            px += (tx - px) * 0.18; py += (ty - py) * 0.18;
            peek.style.left = px.toFixed(1) + 'px'; peek.style.top = py.toFixed(1) + 'px';
            requestAnimationFrame(follow);
        })();
        var show = function (chip, x, y) { pimg.src = chip.getAttribute('data-img'); tx = x; ty = y; if (!showing) { px = x; py = y; } showing = true; peek.classList.add('on'); };
        var hide = function () { showing = false; peek.classList.remove('on'); };
        chips.forEach(function (c) {
            c.addEventListener('pointerenter', function (e) { show(c, e.clientX + 24, e.clientY - 200); });
            c.addEventListener('pointermove', function (e) { tx = e.clientX + 24; ty = e.clientY - 200; });
            c.addEventListener('pointerleave', hide);
            c.addEventListener('focus', function () { var r = c.getBoundingClientRect(); show(c, r.left, r.top - 210); });
            c.addEventListener('blur', hide);
        });
    }

    /* ---------- Act II: the ring ---------- */
    var act = document.getElementById('act-tools');
    // Dress the cards in the same little illustrations the software grid uses
    // (tools from site-data.js, SVG_PREVIEWS from main.js); the markup's photos
    // are the fallback when either is missing.
    var RING = ['Plaque Toolkit', 'Protein Structure Viewer', 'Lysis Curve Plotter', 'FigureLab', 'CellMorphR', 'HMM Homologue Finder',
        'PFU Calculator', 'CFU Plot Studio', 'Genomics Kitchen', 'Gibson Assembly Calculator', 'PooledPPI', 'Dilution Designer'];
    if (act && typeof tools !== 'undefined' && typeof SVG_PREVIEWS !== 'undefined') {
        var list = act.querySelector('.ring');
        var made = RING.map(function (name) { return tools.filter(function (t) { return t.title === name; })[0]; })
            .filter(function (t) { return t && SVG_PREVIEWS[t.preview]; })
            .map(function (t, i) {
                var href = t.blog || t.app || t.repo, ext = !/^blog\//.test(href);
                return '<li class="ring-card"><a href="' + href + '"' + (ext ? ' target="_blank" rel="noopener"' : '') + '>' +
                    '<span class="rc-img" aria-hidden="true">' + SVG_PREVIEWS[t.preview] + '</span>' +
                    '<span class="rc-no">No.&nbsp;' + ('0' + (i + 1)).slice(-2) + '</span><span class="rc-name">' + t.title + '</span></a></li>';
            });
        if (made.length >= 8) list.innerHTML = made.join('');
    }
    if (act && !reduce) {
        html.classList.add('ring-live');
        var cards = [].slice.call(act.querySelectorAll('.ring-card')), center = act.querySelector('.ring-center'), N = cards.length;
        var seed = 7; function rnd() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
        var scatter = cards.map(function (c, i) {
            var a = i / N * 6.283 + rnd() * 0.6;
            return { x: Math.cos(a) * (0.55 + rnd() * 0.25), y: Math.sin(a) * (0.6 + rnd() * 0.3), r: (rnd() - 0.5) * 50, sr: (rnd() - 0.5) * 12 };
        });
        var placeRing = function () {
            var b = act.getBoundingClientRect(), vh = window.innerHeight, vw = window.innerWidth;
            if (b.bottom < -50 || b.top > vh + 50) return;
            var p = clamp(-b.top / Math.max(1, b.height - vh), 0, 1);
            // an ellipse: wide screens get a wider ring, so the cards clear the centre text
            var ph = vw < 760, ry = Math.min(vw * (ph ? 0.4 : 0.34), vh * (ph ? 0.3 : 0.31)), rx = Math.min(vw * (ph ? 0.4 : 0.36), vh * (ph ? 0.3 : 0.5));
            var gather = ease(seg(p, 0.0, 0.22)), fan = ease(seg(p, 0.26, 0.52)), orbit = seg(p, 0.5, 0.88), out = ease(seg(p, 0.86, 1));
            cards.forEach(function (c, i) {
                var s = scatter[i];
                var x = lerp(s.x * vw * 0.6, i * 1.5 - N * 0.75, gather), y = lerp(s.y * vh * 0.62, i * -1.5 + N * 0.75, gather), rot = lerp(s.r, s.sr, gather);
                var th = -Math.PI / 2 + i / N * 6.283 + orbit * 0.9, grow = 1 + out * 0.6;
                x = lerp(x, Math.cos(th) * rx * grow, fan); y = lerp(y, Math.sin(th) * ry * 0.94 * grow, fan);
                rot = lerp(rot, (th * 57.3 + 90) * 0.05, fan);
                var sc = 1 + out * 0.15, op = clamp(seg(p, 0, 0.06) - out, 0, 1);
                c.style.transform = 'translate(-50%, -50%) translate(' + x.toFixed(1) + 'px, ' + y.toFixed(1) + 'px) rotate(' + rot.toFixed(2) + 'deg) scale(' + sc.toFixed(3) + ')';
                c.style.opacity = op.toFixed(3);
                c.style.zIndex = fan > 0.5 ? 1 : N - i;
                c.style.pointerEvents = op > 0.5 ? 'auto' : 'none';
                c.firstChild.tabIndex = op > 0.5 ? 0 : -1;
                // a dimmed card is scenery (the grid below lists every tool), so screen readers skip it
                if (op > 0.5) c.removeAttribute('aria-hidden'); else c.setAttribute('aria-hidden', 'true');
            });
            var co = seg(p, 0.4, 0.52);
            center.style.opacity = co.toFixed(3);
            center.style.transform = 'translate(-50%, -50%) translateY(' + ((1 - seg(p, 0.4, 0.52)) * 24).toFixed(1) + 'px)';
            center.style.visibility = co > 0.02 ? 'visible' : 'hidden';
        };
        onScroll(placeRing);
        // keyboard users: tabbing to a card scrolls the section to where the ring is open
        cards.forEach(function (c) {
            c.firstChild.addEventListener('focus', function () {
                var b = act.getBoundingClientRect(), top = window.scrollY + b.top + (b.height - window.innerHeight) * 0.66;
                if (Math.abs(window.scrollY - top) > 40) (lenis ? lenis.scrollTo(top, { immediate: true }) : window.scrollTo(0, top));
            });
        });
    }

    /* ---------- Act III: steps ---------- */
    var steps = document.querySelectorAll('.step');
    if (steps.length && 'IntersectionObserver' in window && !reduce) {
        var io = new IntersectionObserver(function (es) {
            es.forEach(function (e) {
                e.target.classList.toggle('on', e.isIntersecting);
                if (e.isIntersecting) e.target.classList.add('seen');
            });
        }, { rootMargin: '-42% 0px -42% 0px' });
        steps.forEach(function (s) { io.observe(s); });
    }

    /* ---------- cursor ---------- */
    if (fine && !reduce) {
        var cur = document.createElement('div');
        cur.className = 'cur'; cur.setAttribute('aria-hidden', 'true');
        cur.innerHTML = '<span></span>';
        document.body.appendChild(cur);
        var lab = cur.firstChild, cx = -100, cy = -100, kx = -100, ky = -100;
        window.addEventListener('pointermove', function (e) { kx = e.clientX; ky = e.clientY; cur.classList.add('on'); }, { passive: true });
        document.addEventListener('pointerleave', function () { cur.classList.remove('on'); });
        (function move() {
            cx += (kx - cx) * 0.2; cy += (ky - cy) * 0.2;
            cur.style.transform = 'translate(' + cx.toFixed(1) + 'px,' + cy.toFixed(1) + 'px)';
            requestAnimationFrame(move);
        })();
        document.addEventListener('pointerover', function (e) {
            var big = e.target.closest('.ring-card a, .tool-card, .proj-card, .blog-card, .gallery-item');
            cur.classList.toggle('big', !!big);
            lab.textContent = big ? (big.closest('.gallery-item') ? 'View' : 'Open') : '';
        });
    }

    /* ---------- menu: words on the button, focus in and out ---------- */
    var toggle = document.getElementById('navToggle'), menuEl = document.getElementById('navLinks');
    if (toggle && menuEl) {
        var word = toggle.querySelector('.pill-word');
        new MutationObserver(function () {
            var open = menuEl.classList.contains('open');
            html.classList.toggle('menu-open', open);
            if (word) word.textContent = open ? 'Close' : 'Menu';
            toggle.setAttribute('aria-label', open ? 'Close menu' : 'Menu');
            if (open) { var first = menuEl.querySelector('a'); if (first) setTimeout(function () { first.focus({ preventScroll: true }); }, 350); }
        }).observe(menuEl, { attributes: true, attributeFilter: ['class'] });
        // keep Tab inside the open menu (and its toggle)
        document.addEventListener('keydown', function (e) {
            if (e.key !== 'Tab' || !menuEl.classList.contains('open')) return;
            var f = [toggle].concat([].slice.call(menuEl.querySelectorAll('a, button')));
            var i = f.indexOf(document.activeElement);
            e.preventDefault();
            f[(i + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
        });
    }
})();
