/* post-anim.js — animated figures for the blog posts.
 *
 * Each <figure class="pa" data-anim="NAME"> gets an SVG (or HTML) stage, a row
 * of step buttons and a replay button, inserted before its <figcaption>.
 * Every animation is a pure function of time t (seconds): draw(t) sets the
 * whole picture for that instant, so playing, pausing offscreen, jumping to a
 * step and reduced motion all come from the same code.
 *
 *   dilution  serial dilution → plate → count → CFU/mL   (data-variant="pfu" for plaques)
 *   plaques   two plates → detect → measure → compare diameters
 *   gibson    three fragments → chew back → anneal → seal → plasmid
 *   hmm       seeds → profile → search, add hits, rebuild → converge
 *   unicode   a sentence → reveal hidden characters → decode → clean
 *   superplot cells from three dishes → measured → replicate medians → tested at N = 3
 *   csvplot   a CFU CSV → mapped → log10 plot with error bars → exported with its R script
 *   kitchen   sequence files → dedup → QC → six-frame ORFs → exports
 *   plddt     a predicted backbone → pLDDT colours → filtered → PAE map
 *
 * Colours come from CSS custom properties (assets/css/post-anim.css), so each
 * post can map them onto its own palette.
 */
(function () {
    var NS = 'http://www.w3.org/2000/svg';
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

    function el(tag, a, p) {
        var e = document.createElementNS(NS, tag);
        for (var k in a) e.setAttribute(k, a[k]);
        if (p) p.appendChild(e);
        return e;
    }
    function txt(p, x, y, s, cls, anchor) {
        var t = el('text', { x: x, y: y, 'class': cls || 'pa-lab' }, p);
        if (anchor) t.setAttribute('text-anchor', anchor);
        t.textContent = s;
        return t;
    }
    function clamp(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
    function seg(t, a, b) { return clamp((t - a) / (b - a)); }
    function inout(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
    function out(x) { return 1 - Math.pow(1 - x, 3); }
    function lerp(a, b, k) { return a + (b - a) * k; }
    function rng(seed) {
        return function () { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
    }
    function gauss(r) { return Math.sqrt(-2 * Math.log(r() + 1e-9)) * Math.cos(2 * Math.PI * r()); }
    function op(e, v) { e.setAttribute('opacity', v.toFixed(3)); }
    function svgStage(stage, h, label) {
        return el('svg', { viewBox: '0 0 720 ' + h, 'class': 'pa-svg', role: 'img', 'aria-label': label }, stage);
    }
    var SUP = '⁰¹²³⁴⁵⁶⁷⁸⁹';
    function sup(n) { return String(n).split('').map(function (d) { return SUP[+d]; }).join(''); }

    var ANIMS = {};

    /* ------------------------------------------------------------------
     * Serial dilution → plate → count → titer. Numbers are the posts' own
     * worked examples: CFU 148 colonies, 10⁻⁶, 100 µL; PFU 22 plaques, 10⁻⁷, 10 µL.
     * ------------------------------------------------------------------ */
    ANIMS.dilution = function (stage, fig) {
        var pfu = fig.getAttribute('data-variant') === 'pfu';
        var N = pfu ? 7 : 6, COUNT = pfu ? 22 : 148;
        var noun = pfu ? 'plaques' : 'colonies', unit = pfu ? 'PFU/mL' : 'CFU/mL';
        var vol = pfu ? '0.01 mL' : '0.1 mL', volUL = pfu ? '10 µL' : '100 µL';
        var result = pfu ? '2.2 × 10¹⁰' : '1.48 × 10⁹';
        var svg = svgStage(stage, 320, 'A ten-fold dilution series is ' + (pfu ? 'spotted on a bacterial lawn' : 'plated') +
            '; ' + COUNT + ' ' + noun + ' at 10⁻' + N + ' give ' + result + ' ' + unit + '.');
        var r = rng(pfu ? 7 : 6);
        var X0 = 40, DX = (468 - X0) / N, TY = 46;
        function tx(i) { return X0 + i * DX; }

        // tubes
        var tubes = [], labs = [];
        for (var i = 0; i <= N; i++) {
            var g = el('g', {}, svg), x = tx(i);
            el('path', { d: 'M' + (x - 11) + ',78 V120 a11 11 0 0 0 22 0 V78 Z', 'class': 'pa-liq' }, g);
            var dots = [], nd = Math.max(1, Math.round(44 * Math.pow(0.46, i)));
            for (var d = 0; d < nd; d++) {
                var dy = 84 + r() * 42, half = dy > 120 ? Math.sqrt(Math.max(0, 121 - Math.pow(dy - 120, 2))) - 2 : 8;
                dots.push(el('circle', { cx: (x + (r() * 2 - 1) * half).toFixed(1), cy: dy.toFixed(1), r: 1.7, 'class': 'pa-cell' }, g));
            }
            el('path', { d: 'M' + (x - 13) + ',' + TY + ' V120 a13 13 0 0 0 26 0 V' + TY, 'class': 'pa-glass' }, g);
            labs.push(txt(svg, x, 156, i ? '10⁻' + sup(i) : 'neat', 'pa-lab', 'middle'));
            tubes.push(dots);
        }
        txt(svg, X0 - 14, 182, 'each tube: 1 part of the last + 9 parts diluent', 'pa-lab pa-lab-dim');

        // plate
        var PX = 614, PY = 206, PR = 84;
        el('circle', { cx: PX, cy: PY, r: PR + 6, 'class': 'pa-dish' }, svg);
        el('circle', { cx: PX, cy: PY, r: PR, 'class': pfu ? 'pa-lawn' : 'pa-agar' }, svg);
        if (pfu) el('circle', { cx: PX, cy: PY, r: PR, fill: 'url(#pa-speck-' + uid + ')' }, svg);
        var spread = el('circle', { cx: PX, cy: PY, r: 0, 'class': pfu ? 'pa-spot' : 'pa-spread' }, svg);
        var cols = [], RR = pfu ? 26 : 74;
        while (cols.length < COUNT) {
            var a = r() * Math.PI * 2, rr = Math.sqrt(r()) * RR, cx = PX + Math.cos(a) * rr, cy = PY + Math.sin(a) * rr, ok = true;
            for (var j = 0; j < cols.length && ok; j++) if (Math.hypot(cols[j].x - cx, cols[j].y - cy) < (pfu ? 6.2 : 6)) ok = false;
            if (!ok) continue;
            cols.push({ x: cx, y: cy, t: r(), e: el('circle', { cx: cx.toFixed(1), cy: cy.toFixed(1), r: 0, 'class': pfu ? 'pa-plaque' : 'pa-colony' }, svg), s: pfu ? 2.2 + r() * 0.8 : 1.6 + r() * 1.2 });
        }
        var volLab = txt(svg, PX, PY - PR - 14, volUL + ' ' + (pfu ? 'spotted' : 'spread'), 'pa-lab', 'middle');
        var counter = txt(svg, PX, 312, '', 'pa-num', 'middle');

        // pipette (tip at local 0,0)
        var pip = el('g', { 'class': 'pa-pipette' }, svg);
        el('path', { d: 'M-1.5,0 L-4,-24 H4 L1.5,0 Z', 'class': 'pa-tip' }, pip);
        el('rect', { x: -5.5, y: -64, width: 11, height: 40, rx: 3, 'class': 'pa-body' }, pip);
        el('rect', { x: -7, y: -72, width: 14, height: 9, rx: 3, 'class': 'pa-body' }, pip);
        var load = el('path', { d: 'M-1.2,-1 L-2.6,-14 H2.6 L1.2,-1 Z', 'class': 'pa-load' }, pip);

        // equation
        txt(svg, 22, 222, noun + ' × 10^step ÷ mL ' + (pfu ? 'spotted' : 'plated'), 'pa-lab pa-lab-dim');
        var eq = el('text', { x: 22, y: 256, 'class': 'pa-eq' }, svg);
        var terms = [String(COUNT), ' × ', '10' + sup(N), ' ÷ ', vol, ' = '].map(function (s) {
            var t = el('tspan', {}, eq); t.textContent = s; return t;
        });
        var res = el('text', { x: 22, y: 288, 'class': 'pa-eq pa-eq-res' }, svg);
        res.textContent = result + ' ' + unit;

        var D = 0.62, T0 = 0.5, TP = T0 + N * D, TI = TP + 1.8, TE = TI + 2.0;
        function pipAt(x, y, k) { pip.setAttribute('transform', 'translate(' + x.toFixed(1) + ',' + y.toFixed(1) + ')'); op(load, k); }
        var HOV = 34, DIP = 98;

        return {
            dur: TE + 3.2,
            steps: [
                [0, 'Ten-fold serial dilution: each tube holds a tenth of the one before'],
                [TP, pfu ? 'Spot 10 µL of the 10⁻⁷ tube on a bacterial lawn' : 'Spread 100 µL of the 10⁻⁶ tube on a plate'],
                [TI, 'Incubate overnight, then count: ' + COUNT + ' ' + noun],
                [TE, unit + ' = ' + noun + ' × 10^step ÷ volume in mL']
            ],
            draw: function (t) {
                // dots appear in tube i+1 when the tip dips into it
                for (var i = 0; i <= N; i++) {
                    var k = i === 0 ? 1 : seg(t, T0 + (i - 1) * D + 0.66 * D, T0 + (i - 1) * D + 0.95 * D);
                    tubes[i].forEach(function (c) { op(c, k); });
                    labs[i].setAttribute('class', 'pa-lab' + (i === N && t > TE + 0.8 ? ' pa-hot' : ''));
                }
                // pipette path
                if (t < TP) {
                    var n = Math.min(N - 1, Math.max(0, Math.floor((t - T0) / D))), u = clamp((t - T0 - n * D) / D);
                    if (t < T0) pipAt(tx(0), lerp(-10, HOV, out(seg(t, 0, T0))), 0);
                    else if (u < 0.28) pipAt(tx(n), HOV + (DIP - HOV) * Math.sin(Math.PI * u / 0.28), u > 0.14 ? 1 : 0);
                    else if (u < 0.62) pipAt(lerp(tx(n), tx(n + 1), inout((u - 0.28) / 0.34)), HOV, 1);
                    else pipAt(tx(n + 1), HOV + (DIP - HOV) * Math.sin(Math.PI * clamp((u - 0.62) / 0.33)), u < 0.8 ? 1 : 0);
                } else {
                    var v = t - TP;
                    if (v < 0.4) pipAt(tx(N), HOV + (DIP - HOV) * Math.sin(Math.PI * v / 0.4), v > 0.2 ? 1 : 0);
                    else if (v < 1.05) { var m = inout((v - 0.4) / 0.65); pipAt(lerp(tx(N), PX, m), lerp(HOV, PY - 40, m) - Math.sin(Math.PI * m) * 16, 1); }
                    else if (v < 1.35) pipAt(PX, lerp(PY - 40, PY - 8, out((v - 1.05) / 0.3)), v < 1.25 ? 1 : 0);
                    else pipAt(PX, lerp(PY - 8, -90, inout(seg(v, 1.35, 1.75))), 0);
                }
                op(pip, t < TP + 1.75 ? 1 : 0);
                // spread / spot
                var s = out(seg(t, TP + 1.25, TP + 1.7));
                spread.setAttribute('r', (s * (pfu ? 30 : 80)).toFixed(1));
                op(spread, pfu ? s * 0.9 : s * (1 - seg(t, TP + 1.7, TI + 0.4)) * 0.8);
                op(volLab, seg(t, TP + 0.5, TP + 0.9) * (1 - seg(t, TI, TI + 0.3)));
                // colonies / plaques appear over the incubation
                var shown = 0;
                cols.forEach(function (c) {
                    var a = TI + 0.2 + c.t * 1.5, k = out(seg(t, a, a + 0.25));
                    if (k > 0.5) shown++;
                    c.e.setAttribute('r', (k * c.s).toFixed(2));
                });
                counter.textContent = t > TI ? shown + ' ' + noun : '';
                counter.setAttribute('class', 'pa-num' + (t > TE && t < TE + 0.6 ? ' pa-hot' : ''));
                // equation, term by term
                terms.forEach(function (tm, i) { op(tm, seg(t, TE + i * 0.32, TE + i * 0.32 + 0.25)); });
                terms[2].setAttribute('class', t > TE + 0.64 && t < TE + 1.4 ? 'pa-hot' : '');
                terms[4].setAttribute('class', t > TE + 1.28 && t < TE + 2 ? 'pa-hot' : '');
                op(res, seg(t, TE + 2.0, TE + 2.5));
            }
        };
    };

    /* ------------------------------------------------------------------
     * Plaque Toolkit: two lawns → detect → measure → compare.
     * Means are the post's own example (WT 1.84 mm, mutant 1.32 mm).
     * ------------------------------------------------------------------ */
    ANIMS.plaques = function (stage) {
        var svg = svgStage(stage, 320, 'Plaques appear on a wild-type and a mutant plate, are detected and measured, and their diameters are compared: 1.84 mm against 1.32 mm.');
        var r = rng(42), PXMM = 6.2;
        var plates = [{ x: 132, y: 150, mean: 1.84, name: 'WT', cls: 'pa-a' }, { x: 368, y: 150, mean: 1.32, name: 'mutant', cls: 'pa-b' }];
        var CH = { x0: 548, y: function (d) { return 262 - (d - 0.8) / 1.6 * 200; } };
        plates.forEach(function (P, pi) {
            el('circle', { cx: P.x, cy: P.y, r: 112, 'class': 'pa-dish' }, svg);
            el('circle', { cx: P.x, cy: P.y, r: 106, 'class': 'pa-lawn' }, svg);
            el('circle', { cx: P.x, cy: P.y, r: 106, fill: 'url(#pa-speck-' + uid + ')' }, svg);
            txt(svg, P.x, 292, P.name, 'pa-lab', 'middle');
            var ds = [], n = 22;
            for (var i = 0; i < n; i++) ds.push(P.mean + gauss(r) * 0.2);
            var shift = P.mean - ds.reduce(function (a, b) { return a + b; }, 0) / n;
            P.pl = [];
            var tries = 0;
            for (i = 0; i < n && tries < 5000; tries++) {
                var d = ds[i] + shift, rad = d / 2 * PXMM, a = r() * 6.283, rr = Math.sqrt(r()) * (96 - rad), x = P.x + Math.cos(a) * rr, y = P.y + Math.sin(a) * rr, ok = true;
                for (var j = 0; j < P.pl.length && ok; j++) if (Math.hypot(P.pl[j].x - x, P.pl[j].y - y) < rad + P.pl[j].rad + 5) ok = false;
                if (!ok) continue;
                P.pl.push({ x: x, y: y, d: d, rad: rad, t0: 0.3 + r() * 1.5,
                    hole: el('circle', { cx: x.toFixed(1), cy: y.toFixed(1), r: 0, 'class': 'pa-plaque' }, svg),
                    ring: el('circle', { cx: x.toFixed(1), cy: y.toFixed(1), r: (rad + 2.6).toFixed(1), 'class': 'pa-ring ' + P.cls }, svg),
                    dot: el('circle', { r: 3.2, 'class': 'pa-dot ' + P.cls }, svg),
                    jx: (r() * 2 - 1) * 14 });
                i++;
            }
            P.scan = el('line', { x1: 0, x2: 0, y1: P.y - 112, y2: P.y + 112, 'class': 'pa-scan' }, svg);
            P.col = 604 + pi * 72;
            P.bar = el('line', { x1: P.col - 22, x2: P.col + 22, y1: CH.y(P.mean), y2: CH.y(P.mean), 'class': 'pa-mean ' + P.cls }, svg);
            P.lab = txt(svg, P.col, 306, P.mean.toFixed(2) + ' mm', 'pa-num ' + P.cls, 'middle');
            P.name2 = txt(svg, P.col, 288, P.name, 'pa-lab', 'middle');
        });
        // axis
        var ax = el('g', {}, svg);
        el('line', { x1: CH.x0, x2: CH.x0, y1: CH.y(0.8), y2: CH.y(2.4), 'class': 'pa-axis' }, ax);
        [1, 1.5, 2].forEach(function (v) {
            el('line', { x1: CH.x0 - 4, x2: CH.x0, y1: CH.y(v), y2: CH.y(v), 'class': 'pa-axis' }, ax);
            txt(ax, CH.x0 - 8, CH.y(v) + 4, v.toFixed(1), 'pa-lab', 'end');
        });
        txt(ax, CH.x0, CH.y(2.4) - 10, 'diameter (mm)', 'pa-lab', 'start');
        var dl = el('line', { x1: 640, x2: 640, y1: CH.y(1.84), y2: CH.y(1.32), 'class': 'pa-delta' }, svg);
        var dt = txt(svg, 716, CH.y(2.4) - 10, 'Δ 0.52 mm', 'pa-num pa-hot', 'end');

        return {
            dur: 8.6,
            steps: [[0, 'Phage on two lawns: each clearing is a plaque'], [2.3, 'Find every plaque on the photo'],
                [3.9, 'Measure each one in millimetres, calibrated to the dish'], [5.6, 'Compare: WT 1.84 mm against mutant 1.32 mm']],
            draw: function (t) {
                op(ax, seg(t, 3.7, 4.2));
                plates.forEach(function (P, pi) {
                    var sx = lerp(P.x - 112, P.x + 112, seg(t, 2.3, 3.6));
                    P.scan.setAttribute('x1', sx.toFixed(1)); P.scan.setAttribute('x2', sx.toFixed(1));
                    op(P.scan, t > 2.3 && t < 3.6 ? 1 : 0);
                    P.pl.forEach(function (p, i) {
                        p.hole.setAttribute('r', (p.rad * out(seg(t, p.t0, p.t0 + 0.8))).toFixed(2));
                        var seen = t > 2.3 && sx > p.x - p.rad;
                        op(p.ring, seen ? 1 - 0.6 * seg(t, 5.6, 6.2) : 0);
                        var a = 3.9 + i * 0.05 + pi * 0.1, k = inout(seg(t, a, a + 0.7));
                        p.dot.setAttribute('cx', lerp(p.x, P.col + p.jx, k).toFixed(1));
                        p.dot.setAttribute('cy', lerp(p.y, CH.y(p.d), k).toFixed(1));
                        op(p.dot, t > a ? 1 : 0);
                    });
                    var m = out(seg(t, 5.6 + pi * 0.2, 6.1 + pi * 0.2));
                    P.bar.setAttribute('x1', (P.col - 24 * m).toFixed(1)); P.bar.setAttribute('x2', (P.col + 24 * m).toFixed(1)); op(P.bar, m > 0 ? 1 : 0);
                    op(P.lab, seg(t, 5.9 + pi * 0.2, 6.3 + pi * 0.2));
                    op(P.name2, seg(t, 3.7, 4.2));
                });
                op(dl, seg(t, 6.5, 6.9)); op(dt, seg(t, 6.6, 7.0));
            }
        };
    };

    /* ------------------------------------------------------------------
     * Gibson assembly: three overlapping fragments, 5′ ends chewed back,
     * overlaps anneal while the line closes into a ring, gaps filled, nicks sealed.
     * ------------------------------------------------------------------ */
    ANIMS.gibson = function (stage) {
        var svg = svgStage(stage, 320, 'Three DNA fragments with overlapping ends are chewed back, anneal at the overlaps, are filled in and sealed, and close into a circular plasmid.');
        var R = 92, C = 2 * Math.PI * R, O = 26, CH = O + 9, G = 40, SC = C / 2, CX = 360;
        var J = [0, 300, 455];
        var F = [
            { a: J[0] - O / 2, b: J[1] + O / 2, sh: -G, cls: 'pa-f0', name: 'vector' },
            { a: J[1] - O / 2, b: J[2] + O / 2, sh: 0, cls: 'pa-f1', name: 'insert A' },
            { a: J[2] - O / 2, b: C + O / 2, sh: G, cls: 'pa-f2', name: 'insert B' }
        ];
        var rungs = el('path', { 'class': 'pa-rung' }, svg);
        F.forEach(function (f) {
            f.p = {};
            ['top', 'bot'].forEach(function (s) {
                f.p[s] = el('path', { 'class': 'pa-strand ' + f.cls }, svg);
                f.p[s + 'L'] = el('path', { 'class': 'pa-strand pa-arm' }, svg);
                f.p[s + 'R'] = el('path', { 'class': 'pa-strand pa-arm' }, svg);
            });
            f.exo = [el('circle', { r: 4.5, 'class': 'pa-exo' }, svg), el('circle', { r: 4.5, 'class': 'pa-exo' }, svg)];
            f.lab = txt(svg, 0, 0, f.name, 'pa-lab', 'middle');
        });
        var nicks = [];
        for (var i = 0; i < 6; i++) nicks.push(el('circle', { r: 0, 'class': 'pa-nick' }, svg));
        var mid = txt(svg, CX, 160, 'one plasmid', 'pa-num', 'middle');
        var mid2 = txt(svg, CX, 180, 'one tube · 50 °C', 'pa-lab', 'middle');

        var kap = 0, top = 150;
        function P(s, rr) {
            var k = Math.max(kap, 1e-6), Rr = 1 / k, th = (s - SC) * k;
            return [CX + (Rr - rr) * Math.sin(th), top + Rr - (Rr - rr) * Math.cos(th)];
        }
        function path(s0, s1, rr) {
            if (s1 - s0 < 0.5) return '';
            var d = '', n = Math.max(2, Math.ceil((s1 - s0) / 4));
            for (var i = 0; i <= n; i++) { var q = P(lerp(s0, s1, i / n), rr); d += (i ? 'L' : 'M') + q[0].toFixed(1) + ',' + q[1].toFixed(1); }
            return d;
        }
        return {
            dur: 8,
            steps: [[0, 'Three fragments whose ends share 20–40 bp of sequence'], [1.0, 'An exonuclease chews back each 5′ end'],
                [2.4, 'The exposed overlaps find each other and anneal'], [4.6, 'Polymerase fills the gaps; ligase seals the nicks'],
                [5.9, 'One seamless circular plasmid, made in one tube']],
            draw: function (t) {
                var ch = CH * inout(seg(t, 1.0, 2.2)) - (CH - O) * inout(seg(t, 4.6, 5.2));
                var e = inout(seg(t, 2.4, 4.4));
                kap = e / R; top = lerp(150, 62, e);
                var appear = out(seg(t, 0, 0.8)), closed = e > 0.999;
                F.forEach(function (f, fi) {
                    var sh = f.sh * (1 - e) + (1 - appear) * (fi - 1) * 40, a = f.a + sh, b = f.b + sh;
                    var ext = { top: [a + ch, b], bot: [a, b - ch] };
                    ['top', 'bot'].forEach(function (s) {
                        var rr = s === 'top' ? -5 : 5, x = ext[s];
                        f.p[s].setAttribute('d', path(x[0], x[1], rr));
                        f.p[s + 'L'].setAttribute('d', path(Math.max(x[0], a), Math.min(x[1], a + O), rr));
                        f.p[s + 'R'].setAttribute('d', path(Math.max(x[0], b - O), Math.min(x[1], b), rr));
                        op(f.p[s], appear); op(f.p[s + 'L'], appear); op(f.p[s + 'R'], appear);
                    });
                    var chewing = t > 1.0 && t < 2.2;
                    var q1 = P(a + ch, -5), q2 = P(b - ch, 5);
                    f.exo[0].setAttribute('cx', q1[0].toFixed(1)); f.exo[0].setAttribute('cy', q1[1].toFixed(1));
                    f.exo[1].setAttribute('cx', q2[0].toFixed(1)); f.exo[1].setAttribute('cy', q2[1].toFixed(1));
                    op(f.exo[0], chewing ? 1 : 0); op(f.exo[1], chewing ? 1 : 0);
                    var lq = P((f.a + f.b) / 2 + sh, 26);
                    f.lab.setAttribute('x', lq[0].toFixed(1)); f.lab.setAttribute('y', (lq[1] + 4).toFixed(1));
                    op(f.lab, appear * (1 - seg(t, 2.4, 2.9)));
                    f.ext = ext;
                });
                // base-pair rungs wherever both strands are present
                var d = '';
                function has(s, w) {
                    for (var k = 0; k < 3; k++) {
                        var x = F[k].ext[w];
                        if ((s >= x[0] && s <= x[1]) || (closed && ((s + C >= x[0] && s + C <= x[1]) || (s - C >= x[0] && s - C <= x[1])))) return true;
                    }
                    return false;
                }
                for (var s = -80; s < C + 80; s += 7) {
                    if (closed && (s < 0 || s >= C)) continue;
                    if (has(s, 'top') && has(s, 'bot')) {
                        var u = P(s, -3), v = P(s, 3);
                        d += 'M' + u[0].toFixed(1) + ',' + u[1].toFixed(1) + 'L' + v[0].toFixed(1) + ',' + v[1].toFixed(1);
                    }
                }
                rungs.setAttribute('d', d); op(rungs, appear);
                // nicks flash once the gaps are filled
                J.forEach(function (j, ji) {
                    [[j + O / 2, -5], [j - O / 2, 5]].forEach(function (n, ni) {
                        var c = nicks[ji * 2 + ni], q = P(n[0], n[1]), k = seg(t, 5.2 + ji * 0.12, 5.75 + ji * 0.12);
                        c.setAttribute('cx', q[0].toFixed(1)); c.setAttribute('cy', q[1].toFixed(1));
                        c.setAttribute('r', (k * 10).toFixed(1)); op(c, k > 0 && k < 1 ? 1 - k : 0);
                    });
                });
                op(mid, seg(t, 5.9, 6.4)); op(mid2, seg(t, 6.1, 6.6));
            }
        };
    };

    /* ------------------------------------------------------------------
     * Iterative profile search: seeds → profile → search → add hits → rebuild,
     * until a round finds nothing new.
     * ------------------------------------------------------------------ */
    ANIMS.hmm = function (stage) {
        var svg = svgStage(stage, 320, 'Seed sequences are aligned into a profile; each search round adds new hits and rebuilds the profile until a round finds nothing new.');
        var r = rng(11), AA = 'ACDEFGHIKLMNPQRSTVWY', L = 18;
        var CONS = { 1: 'G', 3: 'D', 4: 'W', 7: 'P', 9: 'C', 10: 'R', 13: 'H', 15: 'Y' };
        function seq(keep) {
            var s = '';
            for (var i = 0; i < L; i++) s += CONS[i] && r() < keep ? CONS[i] : AA[Math.floor(r() * 20)];
            return s;
        }
        var seeds = [seq(1), seq(0.95), seq(0.9), seq(1)];
        var DB = 13, ROUND1 = { 1: 1, 6: 1, 10: 1 }, ROUND2 = { 3: 1, 8: 1 };
        var hits = [1, 6, 10, 3, 8], hitSeq = {};
        hits.forEach(function (h) { hitSeq[h] = seq(ROUND1[h] ? 0.85 : 0.6); });
        var AX = 26, CW = 13.4, RY = 62, RH = 15.5;
        function colX(i) { return AX + i * CW + CW / 2; }
        txt(svg, AX, 30, 'alignment', 'pa-lab pa-lab-dim');
        txt(svg, 400, 30, 'genomes searched', 'pa-lab pa-lab-dim');
        var consBg = [];
        Object.keys(CONS).forEach(function (c) {
            consBg.push(el('rect', { x: AX + c * CW, y: RY - 11, width: CW - 1.5, height: RH * 9, rx: 2, 'class': 'pa-cons' }, svg));
        });
        function row(s, x, y, cls) {
            var g = el('g', { transform: 'translate(' + x + ',' + y + ')' }, svg);
            for (var i = 0; i < L; i++) {
                var t = el('text', { x: (i * CW + CW / 2).toFixed(1), y: 0, 'class': 'pa-aa' + (CONS[i] && s[i] === CONS[i] ? ' pa-aa-c' : ''), 'text-anchor': 'middle' }, g);
                t.textContent = s[i];
            }
            if (cls) g.setAttribute('class', cls);
            return g;
        }
        var seedRows = seeds.map(function (s, i) { return row(s, AX, RY + i * RH); });
        // database
        var dbRows = [];
        for (var i = 0; i < DB; i++) {
            var y = RY + i * 17 - 4, g = el('g', {}, svg);
            txt(g, 400, y + 4, 'contig ' + String(110 + i * 37), 'pa-lab pa-lab-dim');
            el('line', { x1: 470, x2: 640, y1: y, y2: y, 'class': 'pa-orf' }, g);
            var mx = 490 + r() * 110;
            var motif = el('line', { x1: mx, x2: mx + 34, y1: y, y2: y, 'class': 'pa-motif' + (ROUND2[i] ? ' pa-faint' : '') }, g);
            var score = el('rect', { x: 650, y: y - 4, width: 0, height: 8, rx: 2, 'class': 'pa-score' }, g);
            dbRows.push({ y: y, motif: motif, score: score, mx: mx });
        }
        var band = el('rect', { x: 394, y: 0, width: 312, height: RH, rx: 4, 'class': 'pa-band' }, svg);
        // profile bars, recomputed from the alignment after each round
        function profile(rows) {
            var p = [];
            for (var i = 0; i < L; i++) {
                var c = {}, m = 0;
                rows.forEach(function (s) { c[s[i]] = (c[s[i]] || 0) + 1; m = Math.max(m, c[s[i]]); });
                p.push(rows.length > 1 ? (m - 1) / (rows.length - 1) : 0);
            }
            return p;
        }
        var round1 = [1, 6, 10], round2 = [3, 8];
        var prof = [profile(seeds), profile(seeds.concat(round1.map(function (h) { return hitSeq[h]; }))),
            profile(seeds.concat(hits.map(function (h) { return hitSeq[h]; })))];
        var PY = 248, bars = [];
        for (i = 0; i < L; i++) bars.push(el('rect', { x: AX + i * CW + 1, width: CW - 3.5, y: PY, height: 0, rx: 1.5, 'class': 'pa-pbar' + (CONS[i] ? ' pa-pbar-c' : '') }, svg));
        el('line', { x1: AX, x2: AX + L * CW, y1: PY, y2: PY, 'class': 'pa-axis' }, svg);
        var plab = txt(svg, AX, PY + 18, 'profile HMM', 'pa-lab');
        var newRows = hits.map(function (h, k) { return { h: h, g: row(hitSeq[h], AX, RY + (4 + k) * RH, 'pa-new') }; });
        var status = txt(svg, 400, 300, '', 'pa-num');
        var T = [1.8, 4.6, 7.4], SCAN = 1.5;

        return {
            dur: 10.4,
            steps: [[0, 'Start from a few aligned seed sequences'], [0.8, 'Build a profile: how conserved is each column?'],
                [T[0], 'Round 1: search every genome with the profile'], [T[0] + SCAN + 0.1, 'Add the hits and rebuild the profile'],
                [T[1], 'Round 2: the sharper profile finds more distant homologues'], [T[2], 'Round 3 finds nothing new: converged']],
            draw: function (t) {
                seedRows.forEach(function (g, i) { op(g, seg(t, i * 0.12, i * 0.12 + 0.4)); });
                consBg.forEach(function (b) { op(b, seg(t, 0.8, 1.3) * 0.9); });
                var pk = [seg(t, 0.9, 1.6), seg(t, T[0] + SCAN + 0.9, T[0] + SCAN + 1.5), seg(t, T[1] + SCAN + 0.9, T[1] + SCAN + 1.5)].map(inout);
                bars.forEach(function (b, i) {
                    var v = lerp(lerp(prof[0][i] * pk[0], prof[1][i], pk[1]), prof[2][i], pk[2]), h = 6 + 46 * v;
                    h *= pk[0];
                    b.setAttribute('y', (PY - h).toFixed(1)); b.setAttribute('height', h.toFixed(1));
                });
                op(plab, seg(t, 0.9, 1.3));
                // scanning band
                var ri = t < T[1] ? 0 : t < T[2] ? 1 : 2, u = seg(t, T[ri], T[ri] + SCAN);
                var yb = lerp(dbRows[0].y, dbRows[DB - 1].y, u);
                band.setAttribute('y', (yb - RH / 2).toFixed(1));
                op(band, t > T[ri] && u < 1 ? 1 : 0);
                dbRows.forEach(function (d, i) {
                    var when = ROUND1[i] ? T[0] + SCAN * i / (DB - 1) : ROUND2[i] ? T[1] + SCAN * i / (DB - 1) : 1e9;
                    var k = out(seg(t, when, when + 0.3));
                    d.score.setAttribute('width', (k * (ROUND1[i] ? 44 : 30)).toFixed(1));
                    d.motif.setAttribute('class', 'pa-motif' + (k > 0 ? ' pa-hit' : ROUND2[i] ? ' pa-faint' : ''));
                });
                // hits fly from the database into the alignment
                newRows.forEach(function (n, k) {
                    var rd = k < 3 ? 0 : 1, a = T[rd] + SCAN + 0.15 + (k % 3) * 0.12, m = inout(seg(t, a, a + 0.7));
                    var d = dbRows[n.h], y0 = d.y + 4, y1 = RY + (4 + k) * RH;
                    n.g.setAttribute('transform', 'translate(' + lerp(470, AX, m).toFixed(1) + ',' + lerp(y0, y1, m).toFixed(1) + ') scale(' + lerp(0.7, 1, m).toFixed(3) + ')');
                    op(n.g, t > a ? 1 : 0);
                });
                var msg = '';
                if (t > T[0] + 0.5) msg = 'round 1 · 3 new hits';
                if (t > T[1] + 0.5) msg = 'round 2 · 2 new hits';
                if (t > T[2] + 0.5) msg = 'round 3 · 0 new hits';
                if (t > T[2] + SCAN + 0.2) msg = 'converged · 5 homologues found';
                status.textContent = msg;
                status.setAttribute('class', 'pa-num' + (t > T[2] + SCAN + 0.2 ? ' pa-hot' : ''));
            }
        };
    };

    /* ------------------------------------------------------------------
     * Invisible Unicode: the post's own example sentence, revealed, decoded, cleaned.
     * HTML rather than SVG so the sentence wraps like text.
     * ------------------------------------------------------------------ */
    ANIMS.unicode = function (stage) {
        stage.classList.add('pa-uni');
        stage.setAttribute('role', 'img');
        stage.setAttribute('aria-label', 'A sentence that looks ordinary is scanned; 18 hidden characters and a look-alike Cyrillic letter appear, two hidden messages are decoded, and the text is cleaned.');
        var line = document.createElement('div');
        line.className = 'pa-uni-line';
        stage.appendChild(line);
        function span(cls, s) { var e = document.createElement('span'); e.className = cls; e.textContent = s; line.appendChild(e); return e; }
        span('', 'The quarterly rep');
        var homo = span('pa-homo', 'о');
        span('', 'rt');
        var g1 = span('pa-ghost', '∅ ×14');
        span('', ' is attached.');
        var g2 = span('pa-ghost', '∅ ×2');
        span('', ' Please review before Friday');
        var g3 = span('pa-ghost', '∅ ×2');
        span('', '.');
        var scan = document.createElement('div'); scan.className = 'pa-uni-scan'; stage.appendChild(scan);
        var dec = document.createElement('div'); dec.className = 'pa-uni-dec'; stage.appendChild(dec);
        function card(k, v) {
            var c = document.createElement('div'); c.className = 'pa-uni-card';
            c.innerHTML = '<span class="pa-uni-k"></span><span class="pa-uni-v"></span>';
            c.firstChild.textContent = k; c.lastChild.textContent = v; dec.appendChild(c); return c;
        }
        var c1 = card('Unicode tag characters', 'doc-id:7741-BX');
        var c2 = card('variation-selector bytes', 'MB');
        var c3 = card('Cyrillic о in "report"', 'look-alike letter');
        var foot = document.createElement('div'); foot.className = 'pa-uni-foot'; stage.appendChild(foot);
        var ghosts = [g1, g2, g3];
        function typeIn(v, s, k) { v.textContent = s.slice(0, Math.round(s.length * k)); }
        return {
            dur: 8.4,
            steps: [[0, 'An ordinary-looking sentence'], [1.2, 'Scan it: make the invisible characters visible'],
                [3.2, 'Decode what they spell'], [5.6, 'Strip them, and say what was removed']],
            draw: function (t) {
                var sk = seg(t, 1.2, 2.6);
                scan.style.left = (sk * 100).toFixed(1) + '%';
                scan.style.opacity = t > 1.2 && sk < 1 ? 1 : 0;
                var clean = inout(seg(t, 5.6, 6.3));
                ghosts.forEach(function (g, i) {
                    var k = out(seg(t, 1.5 + i * 0.4, 1.9 + i * 0.4)) * (1 - clean);
                    g.style.maxWidth = (k * 4.6).toFixed(2) + 'em';
                    g.style.opacity = k.toFixed(3);
                    g.style.marginLeft = g.style.marginRight = (k * 0.18).toFixed(3) + 'em';
                    g.style.paddingLeft = g.style.paddingRight = (k * 0.3).toFixed(3) + 'em';
                });
                var hk = seg(t, 1.6, 1.9);
                homo.classList.toggle('on', hk > 0 && t < 6.3);
                if (t > 6.0) homo.textContent = 'o'; else homo.textContent = 'о';
                [c1, c2, c3].forEach(function (c, i) {
                    var k = out(seg(t, 3.2 + i * 0.6, 3.6 + i * 0.6));
                    c.style.opacity = k.toFixed(3);
                    c.style.transform = 'translateY(' + ((1 - k) * 10).toFixed(1) + 'px)';
                    typeIn(c.lastChild, i === 0 ? 'doc-id:7741-BX' : i === 1 ? 'MB' : 'look-alike letter', seg(t, 3.4 + i * 0.6, 4.1 + i * 0.6));
                });
                foot.style.opacity = seg(t, 6.3, 6.8).toFixed(3);
                foot.textContent = '18 hidden characters removed · 1 look-alike letter replaced';
            }
        };
    };

    /* Okabe–Ito: the colourblind-safe palette CellMorphR and CFU Plot Studio use */
    var OI = { orange: '#E69F00', sky: '#56B4E9', green: '#009E73', blue: '#0072B2', red: '#D55E00' };

    /* ------------------------------------------------------------------
     * CellMorphR: cells from three dishes → measured → plotted → collapsed to
     * replicate medians → tested at N = 3 (a SuperPlot, Lord et al. 2020).
     * ------------------------------------------------------------------ */
    ANIMS.superplot = function (stage) {
        var svg = svgStage(stage, 320, 'Cells from three replicate dishes in two conditions are segmented and measured; plotted together they look like 36 data points, but each dish is summarised to its median and the test runs on 3 paired replicates.');
        var r = rng(33), REP = [OI.orange, OI.sky, OI.green];
        var BASE = [2.0, 2.9], DISH = [-0.3, 0.05, 0.32], FX = [106, 224], FY = [70, 160, 250], FR = 40;
        var CX = [534, 650];
        function Y(a) { return 268 - (a - 1) / 3 * 218; }
        txt(svg, FX[0], 18, 'Control', 'pa-lab', 'middle');
        txt(svg, FX[1], 18, 'Infected', 'pa-lab', 'middle');
        var fields = [], cells = [];
        for (var k = 0; k < 3; k++) {
            var lab = txt(svg, 20, FY[k] + 4, 'dish ' + (k + 1), 'pa-lab', 'start');
            el('circle', { cx: 11, cy: FY[k], r: 4, fill: REP[k] }, svg);
            fields.push(lab);
            for (var c = 0; c < 2; c++) {
                var g = el('g', {}, svg);
                el('circle', { cx: FX[c], cy: FY[k], r: FR, 'class': 'pa-field' }, g);
                fields.push(g);
                var placed = [];
                for (var n = 0, tries = 0; n < 6 && tries < 400; tries++) {
                    var area = Math.max(1.15, BASE[c] + DISH[k] + gauss(r) * 0.28);
                    var len = 8 + area * 6, a = r() * Math.PI, rr = r() * (FR - len / 2 - 5), q = r() * 6.283;
                    var x = FX[c] + Math.cos(q) * rr, y = FY[k] + Math.sin(q) * rr, ok = true;
                    for (var j = 0; j < placed.length && ok; j++) if (Math.hypot(placed[j][0] - x, placed[j][1] - y) < 15) ok = false;
                    if (!ok) continue;
                    placed.push([x, y]);
                    var rod = el('rect', { x: (-len / 2).toFixed(1), y: -3.6, width: len.toFixed(1), height: 7.2, rx: 3.6, 'class': 'pa-rod',
                        transform: 'translate(' + x.toFixed(1) + ',' + y.toFixed(1) + ') rotate(' + (a * 57.3).toFixed(0) + ')' }, g);
                    cells.push({ k: k, c: c, x: x, y: y, area: area, rod: rod,
                        dot: el('circle', { r: 3.2, fill: REP[k], 'class': 'pa-sdot' }, svg), jx: (k - 1) * 17 + (r() * 2 - 1) * 6 });
                    n++;
                }
            }
        }
        cells.forEach(function (cl, i) { cl.ts = 1.2 + i / cells.length * 1.7; cl.tf = 3.2 + i / cells.length * 1.5; });
        // axis
        var ax = el('g', {}, svg);
        el('line', { x1: 468, x2: 468, y1: Y(1), y2: Y(4), 'class': 'pa-axis' }, ax);
        [1.5, 2.5, 3.5].forEach(function (v) {
            el('line', { x1: 464, x2: 468, y1: Y(v), y2: Y(v), 'class': 'pa-axis' }, ax);
            txt(ax, 460, Y(v) + 4, v.toFixed(1), 'pa-lab', 'end');
        });
        txt(ax, 468, Y(4) - 12, 'cell area (µm²)', 'pa-lab', 'start');
        txt(ax, CX[0], 292, 'Control', 'pa-lab', 'middle');
        txt(ax, CX[1], 292, 'Infected', 'pa-lab', 'middle');
        // replicate medians, paired by dish
        var meds = [], pairs = [];
        for (k = 0; k < 3; k++) {
            var m = [0, 1].map(function (c) {
                var v = cells.filter(function (cl) { return cl.k === k && cl.c === c; }).map(function (cl) { return cl.area; }).sort(function (a, b) { return a - b; });
                return (v[2] + v[3]) / 2;
            });
            pairs.push(el('line', { x1: CX[0] + (k - 1) * 17, x2: CX[1] + (k - 1) * 17, y1: Y(m[0]), y2: Y(m[1]), stroke: REP[k], 'class': 'pa-pair' }, svg));
            meds.push([0, 1].map(function (c) { return el('circle', { cx: CX[c] + (k - 1) * 17, cy: Y(m[c]), r: 0, fill: REP[k], 'class': 'pa-med' }, svg); }));
            meds[k].v = m;
        }
        var mc = meds.reduce(function (s, d) { return s + d.v[0]; }, 0) / 3, mi = meds.reduce(function (s, d) { return s + d.v[1]; }, 0) / 3;
        var nlab = txt(svg, 592, 314, '', 'pa-num', 'middle');
        var br = el('path', { d: 'M' + CX[0] + ',78 v-8 H' + CX[1] + ' v8', 'class': 'pa-bracket' }, svg);
        var brt = txt(svg, (CX[0] + CX[1]) / 2, 62, 'paired test, N = 3 · +' + Math.round((mi / mc - 1) * 100) + '% area', 'pa-num pa-hot', 'middle');
        return {
            dur: 10.4,
            steps: [[0, 'Three replicate dishes, each imaged in two conditions'], [1.2, 'Segment every cell and measure its area'],
                [3.2, 'Plotted together, 36 cells look like 36 data points'], [5.4, 'They are not: summarise each dish to its median first'],
                [7.4, 'Then test the 3 replicate medians, paired by dish']],
            draw: function (t) {
                fields.forEach(function (f, i) { op(f, seg(t, i * 0.06, i * 0.06 + 0.5)); });
                cells.forEach(function (cl) {
                    var s = t > cl.ts;
                    cl.rod.style.stroke = s ? REP[cl.k] : '';
                    cl.rod.style.fill = s ? REP[cl.k] : '';
                    cl.rod.setAttribute('class', 'pa-rod' + (s ? ' on' : ''));
                    var f = inout(seg(t, cl.tf, cl.tf + 0.7));
                    cl.dot.setAttribute('cx', lerp(cl.x, CX[cl.c] + cl.jx, f).toFixed(1));
                    cl.dot.setAttribute('cy', lerp(cl.y, Y(cl.area), f).toFixed(1));
                    op(cl.dot, t > cl.tf ? 0.75 - 0.5 * seg(t, 5.4, 6.0) : 0);
                });
                op(ax, seg(t, 3.0, 3.4));
                meds.forEach(function (d, k) { d.forEach(function (e) { e.setAttribute('r', (8 * out(seg(t, 5.5 + k * 0.15, 6.0 + k * 0.15))).toFixed(1)); }); });
                pairs.forEach(function (p, k) { op(p, seg(t, 6.5 + k * 0.12, 6.9 + k * 0.12)); });
                op(br, seg(t, 7.4, 7.8)); op(brt, seg(t, 7.6, 8.0));
                if (t < 3.6) nlab.textContent = '';
                else if (t < 5.4) { nlab.textContent = 'n = 36 cells?'; nlab.setAttribute('class', 'pa-num pa-bad'); }
                else { nlab.textContent = 'N = 3 dishes'; nlab.setAttribute('class', 'pa-num pa-good'); }
            }
        };
    };

    /* ------------------------------------------------------------------
     * CFU Plot Studio: a replicate-level CSV → mapped → log10 plot with bars,
     * SD error bars and an adjusted p → exported with its R script.
     * ------------------------------------------------------------------ */
    ANIMS.csvplot = function (stage) {
        var svg = svgStage(stage, 320, 'A replicate-level CSV of colony counts is column-mapped, every replicate is plotted on a log10 axis with bars, SD error bars and an adjusted p-value, and the figure is exported with the R script that produced it.');
        var r = rng(8), COL = { EV: OI.orange, strain: OI.blue };
        var MEAN = { EV: [8.7, 8.9], strain: [8.6, 6.3] }, rows = [];
        ['EV', 'strain'].forEach(function (s) {
            [0, 1].forEach(function (ti) {
                for (var rep = 1; rep <= 3; rep++) {
                    var v = MEAN[s][ti] + gauss(r) * 0.12;
                    rows.push({ s: s, ti: ti, rep: rep, v: v });
                }
            });
        });
        var TX = [22, 86, 150, 192], RY0 = 66, RH = 16.5;
        var bands = ['sample', 'timepoint', 'replicate', 'CFU'].map(function (n, i) {
            var g = el('g', {}, svg);
            el('rect', { x: TX[i] - 5, y: 38, width: i === 3 ? 66 : 50, height: RY0 + RH * 12 - 46, rx: 4, 'class': 'pa-cons' }, g);
            txt(g, TX[i] - 2, i % 2 ? 32 : 20, '→ ' + n, 'pa-lab pa-hot');
            return g;
        });
        var head = txt(svg, TX[0], 52, '', 'pa-csv pa-csv-h');
        ['sample', 'time', 'rep', 'cfu'].forEach(function (h, i) { var s = el('tspan', { x: TX[i] }, head); s.textContent = h; });
        rows.forEach(function (rw, i) {
            var t = txt(svg, TX[0], RY0 + i * RH, '', 'pa-csv');
            [rw.s, rw.ti ? '24' : '0', String(rw.rep), (Math.pow(10, rw.v) / Math.pow(10, Math.floor(rw.v))).toFixed(1) + 'e' + Math.floor(rw.v)]
                .forEach(function (v, j) { var s = el('tspan', { x: TX[j] }, t); s.textContent = v; });
            rw.text = t;
        });
        // plot
        function Y(v) { return 262 - (v - 5) / 4.6 * 212; }
        var GX = [436, 616], OFF = { EV: -30, strain: 30 }, ax = el('g', {}, svg);
        el('line', { x1: 330, x2: 330, y1: Y(5), y2: Y(9.6), 'class': 'pa-axis' }, ax);
        el('line', { x1: 330, x2: 704, y1: Y(5), y2: Y(5), 'class': 'pa-axis' }, ax);
        [5, 6, 7, 8, 9].forEach(function (v) {
            el('line', { x1: 326, x2: 330, y1: Y(v), y2: Y(v), 'class': 'pa-axis' }, ax);
            txt(ax, 322, Y(v) + 4, '10' + sup(v), 'pa-lab', 'end');
        });
        txt(ax, 330, Y(9.6) - 10, 'CFU/mL (log₁₀ axis)', 'pa-lab', 'start');
        txt(ax, GX[0], 282, '0 h', 'pa-lab', 'middle'); txt(ax, GX[1], 282, '24 h', 'pa-lab', 'middle');
        [['EV', 'empty vector'], ['strain', 'strain']].forEach(function (s, i) {
            el('rect', { x: 548 + i * 104, y: 24, width: 10, height: 10, rx: 2, fill: COL[s[0]] }, ax);
            txt(ax, 562 + i * 104, 33, s[1], 'pa-lab', 'start');
        });
        var bars = [];
        ['EV', 'strain'].forEach(function (s) {
            [0, 1].forEach(function (ti) {
                var vs = rows.filter(function (rw) { return rw.s === s && rw.ti === ti; }).map(function (rw) { return rw.v; });
                var m = vs.reduce(function (a, b) { return a + b; }, 0) / 3;
                var sd = Math.sqrt(vs.reduce(function (a, b) { return a + (b - m) * (b - m); }, 0) / 2);
                var x = GX[ti] + OFF[s];
                bars.push({ m: m, sd: sd, x: x,
                    bar: el('rect', { x: x - 22, width: 44, y: Y(5), height: 0, fill: COL[s], 'class': 'pa-cbar' }, svg),
                    err: el('path', { d: 'M' + (x - 7) + ',' + Y(m + sd) + ' h14 M' + x + ',' + Y(m + sd) + ' V' + Y(m - sd) + ' M' + (x - 7) + ',' + Y(m - sd) + ' h14', 'class': 'pa-err' }, svg) });
            });
        });
        rows.forEach(function (rw, i) {
            rw.dot = el('circle', { r: 3.6, fill: COL[rw.s], 'class': 'pa-cdot' }, svg);
            rw.tx = GX[rw.ti] + OFF[rw.s] + (rw.rep - 2) * 9; rw.t0 = 2.9 + i * 0.13;
        });
        var py = Y(9.25), pb = el('path', { d: 'M' + (GX[1] + OFF.EV) + ',' + (py + 8) + ' V' + py + ' H' + (GX[1] + OFF.strain) + ' V' + (py + 8), 'class': 'pa-bracket' }, svg);
        var pt = txt(svg, GX[1], py - 6, 'adj. p < 0.01', 'pa-num pa-hot', 'middle');
        // the exported script
        var code = el('g', {}, svg);
        el('rect', { x: 10, y: 40, width: 280, height: 222, rx: 8, 'class': 'pa-code' }, code);
        var LINES = ['# cfu_figure.R · written by CFU Plot Studio', 'd <- read.csv("counts.csv")', 'd$log_cfu <- log10(d$cfu)',
            'ggplot(d, aes(time, log_cfu,', '           fill = sample)) +', '  stat_summary(geom = "col") +', '  geom_point() +',
            '  stat_summary(fun.data = mean_sdl,', '               geom = "errorbar") +', '  scale_fill_manual(', '    values = okabe_ito)'];
        var codeT = LINES.map(function (l, i) { return txt(code, 22, 64 + i * 17.5, '', i ? 'pa-csv' : 'pa-csv pa-lab-dim'); });
        return {
            dur: 10.6,
            steps: [[0, 'A replicate-level CSV, in the layout your lab already uses'], [1.2, 'Map the columns: sample, timepoint, replicate, CFU'],
                [2.8, 'Every replicate lands on a log₁₀ axis'], [5.0, 'Bars, SD error bars and the adjusted p-value'],
                [7.0, 'Export the figure with the R script that made it']],
            draw: function (t) {
                op(head, seg(t, 0, 0.4));
                rows.forEach(function (rw, i) {
                    op(rw.text, seg(t, i * 0.05, i * 0.05 + 0.3) * (1 - 0.65 * seg(t, rw.t0, rw.t0 + 0.3)) * (1 - seg(t, 6.9, 7.2)));
                    var f = inout(seg(t, rw.t0, rw.t0 + 0.6));
                    rw.dot.setAttribute('cx', lerp(TX[3] + 20, rw.tx, f).toFixed(1));
                    rw.dot.setAttribute('cy', lerp(RY0 + i * RH - 4, Y(rw.v), f).toFixed(1));
                    op(rw.dot, t > rw.t0 ? 1 : 0);
                });
                bands.forEach(function (b, i) { op(b, seg(t, 1.2 + i * 0.25, 1.5 + i * 0.25) * (1 - seg(t, 2.8, 3.2))); });
                op(ax, seg(t, 2.6, 3.0));
                bars.forEach(function (b, i) {
                    var k = out(seg(t, 5.0 + i * 0.12, 5.6 + i * 0.12));
                    b.bar.setAttribute('y', lerp(Y(5), Y(b.m), k).toFixed(1));
                    b.bar.setAttribute('height', (k * (Y(5) - Y(b.m))).toFixed(1));
                    op(b.err, seg(t, 5.8, 6.1));
                });
                op(pb, seg(t, 6.2, 6.5)); op(pt, seg(t, 6.3, 6.6));
                op(code, seg(t, 7.0, 7.3));
                codeT.forEach(function (c, i) { var k = seg(t, 7.2 + i * 0.22, 7.45 + i * 0.22); c.textContent = LINES[i].slice(0, Math.round(LINES[i].length * k)); });
            }
        };
    };

    /* ------------------------------------------------------------------
     * Genomics Kitchen: files in → SeqSieve collapses exact duplicates →
     * ReadLens profiles and flags → ORFScout scans six frames → exports.
     * ------------------------------------------------------------------ */
    ANIMS.kitchen = function (stage) {
        var svg = svgStage(stage, 320, 'Nine sequence records are collapsed to five unique ones with their duplicate counts kept, profiled for length and GC with an invalid character flagged, scanned in all six reading frames, and exported as tables and FASTA, all in the browser.');
        var NT = { A: '#56B4E9', C: '#E69F00', G: '#009E73', T: '#CC79A7', N: '#D55E00' };
        var PAT = ['ACGTTGCAAGCT', 'GGCATTACGGAT', 'TTAGCCGANTCA', 'CAGGTACCTTGA', 'ATGCGCGTATAC'];
        var REC = [0, 1, 0, 2, 3, 1, 0, 4, 4];
        var CW = 5.5, recs = [];
        function strip(p, x, y) {
            var g = el('g', { transform: 'translate(' + x + ',' + y + ')' }, svg);
            for (var i = 0; i < 12; i++) el('rect', { x: i * CW, y: 0, width: CW - 0.8, height: 9, rx: 1, fill: NT[PAT[p][i]], 'class': PAT[p][i] === 'N' ? 'pa-nt-n' : '' }, g);
            return g;
        }
        var H = [[24, 'your files'], [160, 'SeqSieve'], [312, 'ReadLens'], [478, 'ORFScout']].map(function (h) {
            return txt(svg, h[0], 26, h[1], h[0] === 24 ? 'pa-lab pa-lab-dim' : 'pa-num', 'start');
        });
        var sub = [txt(svg, 160, 42, 'duplicates collapsed', 'pa-lab', 'start'), txt(svg, 312, 42, 'length · GC · warnings', 'pa-lab', 'start'), txt(svg, 478, 42, 'six reading frames', 'pa-lab', 'start')];
        var seen = {}, row = 0;
        REC.forEach(function (p, i) {
            var u = seen[p] == null ? (seen[p] = row++) : seen[p];
            recs.push({ p: p, i: i, u: u, g: strip(p, 24, 58 + i * 21), y0: 58 + i * 21, y1: 62 + u * 30 });
        });
        var counts = {}; REC.forEach(function (p) { counts[p] = (counts[p] || 0) + 1; });
        var badges = Object.keys(seen).map(function (p) {
            return txt(svg, 238, 62 + seen[p] * 30 + 9, counts[p] > 1 ? '×' + counts[p] : '×1', counts[p] > 1 ? 'pa-num pa-hot' : 'pa-lab', 'start');
        });
        var tally = txt(svg, 160, 228, '9 records → 5 unique', 'pa-num', 'start');
        var maptxt = txt(svg, 160, 246, 'mapping table kept', 'pa-lab', 'start');
        // ReadLens: a length histogram and a GC readout, then a warning
        var hist = [], HB = [3, 6, 9, 7, 4, 2];
        HB.forEach(function (h, i) { hist.push(el('rect', { x: 314 + i * 20, width: 15, y: 170, height: 0, rx: 2, 'class': 'pa-hbar' }, svg)); });
        var haxis = el('line', { x1: 310, x2: 440, y1: 170, y2: 170, 'class': 'pa-axis' }, svg);
        var hl = txt(svg, 312, 188, 'read length', 'pa-lab', 'start');
        var uniq = Object.keys(seen).map(function (p) { return PAT[p]; }).join(''), gcn = uniq.replace(/[^GC]/g, '').length;
        var gc = txt(svg, 312, 214, 'GC ' + (gcn / uniq.replace(/N/g, '').length * 100).toFixed(1) + ' %', 'pa-num', 'start');
        var warn = el('g', {}, svg);
        el('rect', { x: 306, y: 228, width: 160, height: 24, rx: 12, 'class': 'pa-warn' }, warn);
        txt(warn, 386, 244, '1 invalid base flagged', 'pa-lab pa-bad', 'middle');
        // ORFScout: a sequence with three frames above (forward) and three below (reverse)
        var SX0 = 478, SX1 = 704, SY = 150;
        var seqline = el('line', { x1: SX0, x2: SX1, y1: SY, y2: SY, 'class': 'pa-seq' }, svg);
        var frames = [];
        [[-1, 0, 0.05, 0.42], [-1, 1, 0.38, 0.88], [-1, 2, 0.12, 0.3], [1, 0, 0.55, 0.95], [1, 1, 0.08, 0.5], [1, 2, 0.6, 0.78]].forEach(function (f, i) {
            var y = SY + f[0] * (16 + f[1] * 14), x0 = SX0 + f[2] * (SX1 - SX0), x1 = SX0 + f[3] * (SX1 - SX0);
            var lab = txt(svg, SX0 - 4, y + 4, (f[0] < 0 ? '+' : '−') + (f[1] + 1), 'pa-lab pa-lab-dim', 'end');
            frames.push({ a: el('path', { 'class': 'pa-orf-arrow' + (f[0] > 0 ? ' rev' : '') }, svg), y: y, x0: x0, x1: x1, rev: f[0] > 0, lab: lab, t0: 5.6 + i * 0.22 });
        });
        var cx = 478, chips = ['TSV', 'JSON', 'CSV', 'FASTA'].map(function (n) {
            var g = el('g', {}, svg), w = n.length * 7.4 + 16, x = cx;
            cx += w + 6;
            el('rect', { x: x, y: 238, width: w, height: 24, rx: 12, 'class': 'pa-chip' }, g);
            txt(g, x + w / 2, 254, n, 'pa-lab', 'middle');
            return g;
        });
        var zero = txt(svg, 478, 290, '0 bytes uploaded', 'pa-num pa-good', 'start');
        return {
            dur: 10.4,
            steps: [[0, 'Drop in sequence files; nothing leaves the browser'], [1.2, 'SeqSieve: collapse exact duplicates, keep the mapping'],
                [3.4, 'ReadLens: length, GC and quality, with problems surfaced'], [5.4, 'ORFScout: scan all six reading frames'],
                [7.6, 'Export TSV, JSON, CSV and FASTA, with methods text']],
            draw: function (t) {
                recs.forEach(function (rc) {
                    var a = seg(t, rc.i * 0.07, rc.i * 0.07 + 0.35), m = inout(seg(t, 1.3 + rc.i * 0.1, 2.1 + rc.i * 0.1));
                    rc.g.setAttribute('transform', 'translate(' + lerp(24, 160, m).toFixed(1) + ',' + lerp(rc.y0, rc.y1, m).toFixed(1) + ')');
                    op(rc.g, a);
                });
                badges.forEach(function (b) { op(b, seg(t, 2.6, 3.0)); });
                op(tally, seg(t, 2.8, 3.2)); op(maptxt, seg(t, 3.0, 3.4));
                op(H[1], seg(t, 1.0, 1.3)); op(sub[0], seg(t, 1.1, 1.4));
                op(H[2], seg(t, 3.3, 3.6)); op(sub[1], seg(t, 3.4, 3.7));
                op(H[3], seg(t, 5.3, 5.6)); op(sub[2], seg(t, 5.4, 5.7));
                hist.forEach(function (b, i) { var h = HB[i] * 11 * out(seg(t, 3.6 + i * 0.12, 4.1 + i * 0.12)); b.setAttribute('y', (170 - h).toFixed(1)); b.setAttribute('height', h.toFixed(1)); });
                op(haxis, seg(t, 3.5, 3.8)); op(hl, seg(t, 3.6, 3.9)); op(gc, seg(t, 4.4, 4.7)); op(warn, seg(t, 4.8, 5.1));
                var nOn = t > 4.8 && t < 7.6;
                svg.querySelectorAll('.pa-nt-n').forEach(function (n) { n.setAttribute('class', 'pa-nt-n' + (nOn ? ' on' : '')); });
                op(seqline, seg(t, 5.4, 5.7));
                frames.forEach(function (f) {
                    var k = out(seg(t, f.t0, f.t0 + 0.5)), len = (f.x1 - f.x0) * k, d;
                    if (len < 1) d = '';
                    else if (!f.rev) { var e = f.x0 + len; d = 'M' + f.x0 + ',' + (f.y - 4) + ' H' + Math.max(f.x0, e - 6) + ' L' + e + ',' + f.y + ' L' + Math.max(f.x0, e - 6) + ',' + (f.y + 4) + ' H' + f.x0 + ' Z'; }
                    else { var s = f.x1 - len; d = 'M' + f.x1 + ',' + (f.y - 4) + ' H' + Math.min(f.x1, s + 6) + ' L' + s + ',' + f.y + ' L' + Math.min(f.x1, s + 6) + ',' + (f.y + 4) + ' H' + f.x1 + ' Z'; }
                    f.a.setAttribute('d', d);
                    op(f.lab, seg(t, f.t0 - 0.2, f.t0 + 0.1));
                });
                chips.forEach(function (c, i) { op(c, seg(t, 7.6 + i * 0.18, 7.9 + i * 0.18)); });
                op(zero, seg(t, 8.6, 9.0));
            }
        };
    };

    /* ------------------------------------------------------------------
     * Protein Structure Viewer: a predicted backbone, coloured by pLDDT,
     * filtered at 70, then its PAE map: two confident domains whose relative
     * placement the model does not know.
     * ------------------------------------------------------------------ */
    ANIMS.plddt = function (stage) {
        var svg = svgStage(stage, 320, 'A predicted protein backbone is coloured by pLDDT: two domains are confident, the linker and termini are not. Hiding residues below 70 leaves the domains. The PAE map shows each domain is well predicted internally, but the error between them is high, so their relative placement is unknown.');
        var r = rng(17), N = 80, P = [], L = [];
        var PL = ['#ff7d45', '#ffdb13', '#65cbf3', '#0053d6'];
        function band(v) { return v < 50 ? 0 : v < 70 ? 1 : v < 90 ? 2 : 3; }
        var x = 34, y = 262;
        for (var i = 0; i < N; i++) {
            var dom = i >= 10 && i <= 35 ? 0 : i >= 46 && i <= 71 ? 1 : -1, v;
            if (dom >= 0) {
                var c0 = dom ? [292, 150] : [128, 128], j = i - (dom ? 46 : 10);
                var th = j * 1.95 + dom, rad = 20 + 22 * Math.abs(Math.sin(j * 0.55 + dom));
                x = c0[0] + Math.cos(th) * rad; y = c0[1] + Math.sin(th) * rad * 0.85;
                var edge = Math.min(j, 25 - j);
                v = edge < 3 ? 76 + edge * 4 + r() * 4 : 90 + r() * 7;
            } else if (i < 10) { x += 8 + r() * 4; y -= 9 + r() * 6; v = 30 + i * 1.5 + r() * 6; }
            else if (i < 46) { var k = (i - 36) / 10; x = lerp(150, 268, k) + (r() - 0.5) * 10; y = lerp(156, 178, k) + Math.sin(k * 6) * 14; v = 52 + r() * 14; }
            else { x += 9 + r() * 4; y += 8 + r() * 5; v = 34 + r() * 10; }
            P.push([x, y]); L.push(v);
        }
        function pt(i) { return P[Math.max(0, Math.min(N - 1, i))]; }
        var segs = [];
        for (i = 0; i < N - 1; i++) {
            var p0 = pt(i - 1), p1 = pt(i), p2 = pt(i + 1), p3 = pt(i + 2);
            var c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6], c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
            segs.push(el('path', { d: 'M' + p1[0].toFixed(1) + ',' + p1[1].toFixed(1) + ' C' + c1.map(function (n) { return n.toFixed(1); }) + ' ' + c2.map(function (n) { return n.toFixed(1); }) + ' ' + p2[0].toFixed(1) + ',' + p2[1].toFixed(1), 'class': 'pa-bb' }, svg));
        }
        // pLDDT legend
        var leg = el('g', {}, svg);
        ['< 50', '50–70', '70–90', '> 90'].forEach(function (s, i) {
            el('rect', { x: 30 + i * 62, y: 290, width: 58, height: 18, rx: 3, fill: PL[i] }, leg);
            txt(leg, 59 + i * 62, 303, s, 'pa-lab pa-on-band' + (i === 3 ? ' light' : ''), 'middle');
        });
        txt(leg, 30, 284, 'pLDDT', 'pa-lab', 'start');
        // PAE map
        var B = 30, X0 = 452, Y0 = 46, CS = 8, groups = [];
        function domOf(b) { var res = (b + 0.5) * N / B; return res >= 10 && res <= 35 ? 0 : res >= 46 && res <= 71 ? 1 : -1; }
        function pae(a, b) {
            var da = domOf(a), db = domOf(b);
            if (a === b) return 0.5;
            if (da >= 0 && da === db) return 2 + Math.abs(a - b) * 0.25 + r() * 1.5;
            if (da >= 0 && db >= 0) return 19 + r() * 6;
            return 24 + r() * 6;
        }
        function col(v) {
            var k = clamp(v / 30), c0 = [12, 84, 40], c1 = [232, 243, 232];
            return 'rgb(' + c0.map(function (c, i) { return Math.round(c + (c1[i] - c) * k); }).join(',') + ')';
        }
        for (var d = 0; d < B; d++) groups.push(el('g', {}, svg));
        for (var a = 0; a < B; a++) for (var b = 0; b < B; b++) {
            el('rect', { x: X0 + b * CS, y: Y0 + a * CS, width: CS, height: CS, fill: col(pae(a, b)) }, groups[Math.abs(a - b)]);
        }
        var paeAx = el('g', {}, svg);
        txt(paeAx, X0, Y0 - 10, 'PAE (Å): predicted aligned error', 'pa-lab', 'start');
        txt(paeAx, X0 + B * CS / 2, Y0 + B * CS + 16, 'residue', 'pa-lab', 'middle');
        var scale = el('g', {}, svg);
        for (i = 0; i < 6; i++) el('rect', { x: X0 + i * 20, y: Y0 + B * CS + 24, width: 20, height: 8, fill: col(i * 6) }, scale);
        txt(scale, X0 + 128, Y0 + B * CS + 32, '0 → 30 Å', 'pa-lab', 'start');
        // domain blocks and the uncertain off-diagonal block
        function blockRect(r0, r1, c0b, c1b, cls) {
            var bs = function (res) { return Math.round(res / N * B); };
            return el('rect', { x: X0 + bs(c0b) * CS, y: Y0 + bs(r0) * CS, width: (bs(c1b) - bs(c0b)) * CS, height: (bs(r1) - bs(r0)) * CS, 'class': cls }, svg);
        }
        var dA = blockRect(10, 36, 10, 36, 'pa-dom'), dB = blockRect(46, 72, 46, 72, 'pa-dom');
        var off = blockRect(10, 36, 46, 72, 'pa-unk');
        var arrow = el('path', { d: 'M150,168 Q212,222 272,190', 'class': 'pa-unk-arrow' }, svg);
        var q = txt(svg, 212, 236, 'relative placement?', 'pa-num pa-bad', 'middle');
        var dl = [txt(svg, 128, 60, 'domain A', 'pa-lab', 'middle'), txt(svg, 300, 92, 'domain B', 'pa-lab', 'middle')];
        return {
            dur: 11,
            steps: [[0, 'A predicted structure: two domains, a linker and loose ends'], [1.8, 'Colour by pLDDT: how sure the model is of each residue'],
                [3.6, 'Hide pLDDT below 70: what remains is worth reading'], [5.4, 'PAE: low-error blocks are domains predicted well internally'],
                [7.6, 'High error between the blocks: where they sit relative to each other is not known']],
            draw: function (t) {
                segs.forEach(function (s, i) {
                    var shown = t > i * 0.018, colored = t > 1.8 + i * 0.012;
                    s.style.stroke = colored ? PL[band(L[i])] : '';
                    var low = L[i] < 70, hide = seg(t, 3.6, 4.1) * (1 - 0.6 * seg(t, 7.6, 8.0));
                    op(s, shown ? (low ? 1 - 0.85 * hide : 1) : 0);
                });
                op(leg, seg(t, 1.8, 2.2));
                dl.forEach(function (d) { op(d, seg(t, 4.0, 4.4)); });
                groups.forEach(function (g, i) { op(g, seg(t, 5.4 + i * 0.05, 5.7 + i * 0.05)); });
                op(paeAx, seg(t, 5.3, 5.6)); op(scale, seg(t, 5.5, 5.8));
                op(dA, seg(t, 6.6, 7.0)); op(dB, seg(t, 6.8, 7.2));
                op(off, seg(t, 7.6, 8.0)); op(arrow, seg(t, 7.8, 8.2)); op(q, seg(t, 8.0, 8.4));
            }
        };
    };

    /* ------------------------------------------------------------------ */
    var uid = 0;
    function defs(svg) {
        // a fine speckle for bacterial lawns, one per figure
        var d = el('defs', {}, svg), p = el('pattern', { id: 'pa-speck-' + uid, width: 18, height: 18, patternUnits: 'userSpaceOnUse' }, d), r = rng(5);
        for (var i = 0; i < 16; i++) el('circle', { cx: (r() * 18).toFixed(1), cy: (r() * 18).toFixed(1), r: (0.5 + r() * 0.7).toFixed(2), 'class': 'pa-speck' }, p);
        svg.insertBefore(d, svg.firstChild);
    }

    function wire(fig) {
        var make = ANIMS[fig.getAttribute('data-anim')];
        if (!make || fig.__pa) return;
        fig.__pa = true;
        uid++;
        var stage = document.createElement('div');
        stage.className = 'pa-stage';
        var cap = fig.querySelector('figcaption');
        fig.insertBefore(stage, cap);
        var A = make(stage, fig);
        var svg = stage.querySelector('svg');
        if (svg) defs(svg);

        var bar = document.createElement('div');
        bar.className = 'pa-bar';
        var btn = document.createElement('button');
        btn.type = 'button'; btn.className = 'pa-play';
        var dots = document.createElement('div');
        dots.className = 'pa-steps';
        var label = document.createElement('span');
        label.className = 'pa-label';
        var stepBtns = A.steps.map(function (s, i) {
            var b = document.createElement('button');
            b.type = 'button'; b.className = 'pa-dot-btn';
            b.setAttribute('aria-label', 'Step ' + (i + 1) + ': ' + s[1]);
            b.textContent = i + 1;
            b.addEventListener('click', function () { seek(s[0], true); });
            dots.appendChild(b);
            return b;
        });
        bar.appendChild(dots); bar.appendChild(label); bar.appendChild(btn);
        fig.insertBefore(bar, cap);

        var t = 0, playing = false, visible = false, last = 0, started = false;
        function render() {
            A.draw(t);
            var cur = 0;
            A.steps.forEach(function (s, i) { if (t >= s[0] - 1e-6) cur = i; });
            stepBtns.forEach(function (b, i) { b.classList.toggle('on', i === cur); b.classList.toggle('done', i < cur); });
            label.textContent = A.steps[cur][1];
            btn.textContent = playing ? 'Pause' : t >= A.dur ? 'Replay' : started ? 'Play' : 'Play';
        }
        function frame(now) {
            if (!playing) return;
            if (!visible) { playing = 'waiting'; return; }
            t = Math.min(A.dur, t + Math.min(0.05, (now - last) / 1000));
            last = now;
            if (t >= A.dur) { playing = false; fig.dispatchEvent(new CustomEvent('pa:end')); }
            render();
            if (playing) requestAnimationFrame(frame);
        }
        function play() {
            if (t >= A.dur) t = 0;
            playing = true; started = true; last = performance.now();
            requestAnimationFrame(frame);
            render();
        }
        function seek(at, go) {
            t = at; playing = false; render();
            if (go && !reduce) play();
        }
        btn.addEventListener('click', function () {
            if (playing === true) { playing = false; render(); } else play();
        });

        fig.__paSeek = function (at) { seek(at, false); };
        fig.__paRestart = function () { if (reduce) return; t = 0; play(); };
        if (reduce) { t = A.dur; render(); return; }
        render();
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (es) {
                visible = es[0].isIntersecting;
                if (visible && !started) play();
                else if (visible && playing === 'waiting') { playing = true; last = performance.now(); requestAnimationFrame(frame); }
            }, { threshold: 0.35 }).observe(fig);
        } else { visible = true; play(); }
    }

    /* A tabbed showcase: <div class="pa-show"> holding a [role=tablist] of tabs and
     * one [role=tabpanel] per tab, each with a figure.pa inside. Plays the panels in
     * turn while it is on screen, until the reader picks a tab themselves. */
    function show(box) {
        var tabs = [].slice.call(box.querySelectorAll('[role=tab]'));
        var panels = tabs.map(function (b) { return document.getElementById(b.getAttribute('aria-controls')); });
        var cur = 0, auto = !reduce, timer = null, onScreen = false;
        function select(i, restart) {
            cur = (i + tabs.length) % tabs.length;
            tabs.forEach(function (b, k) {
                b.setAttribute('aria-selected', k === cur ? 'true' : 'false');
                b.tabIndex = k === cur ? 0 : -1;
                panels[k].hidden = k !== cur;
            });
            var f = panels[cur].querySelector('figure.pa');
            if (restart && f && f.__paRestart) f.__paRestart();
        }
        tabs.forEach(function (b, i) {
            b.addEventListener('click', function () { auto = false; clearTimeout(timer); select(i, true); });
            b.addEventListener('keydown', function (e) {
                var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
                if (!d) return;
                e.preventDefault(); auto = false; clearTimeout(timer);
                select(cur + d, true); tabs[cur].focus();
            });
        });
        panels.forEach(function (p, i) {
            var f = p.querySelector('figure.pa');
            if (f) f.addEventListener('pa:end', function () {
                if (!auto || i !== cur) return;
                clearTimeout(timer);
                timer = setTimeout(function () { if (auto && onScreen) select(cur + 1, true); }, 2600);
            });
            // the figure's own buttons count as taking control too
            if (f) f.addEventListener('click', function (e) { if (e.target.closest('button')) { auto = false; clearTimeout(timer); } });
        });
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (es) { onScreen = es[0].isIntersecting; }, { threshold: 0.2 }).observe(box);
        }
        select(0, false);
    }

    function init() {
        document.querySelectorAll('figure.pa[data-anim]').forEach(wire);
        document.querySelectorAll('.pa-show').forEach(show);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
