/* lysis-fig.js — the N4 lysis-model figure, drawn as a whole cell. Shared by
   the homepage (Research Focus) and journey.html (Fig 6): wires every
   <figure data-fig="sar">, drawing into its .sar-cell container.

   The model is Fig. 7 of the first-author preprint
   (doi:10.1101/2025.11.12.688109), shown on one E. coli cell so each lysis
   protein's effect on the cell is visible:
   - Rapid lysis: gp63 pinholes depolarize the inner membrane; the gp61 SAR
     endolysin is released and degrades the wall evenly, so the rod contracts
     from the poles and rounds; with enough wall gone the gp60/gp60a spanins
     act and the cell lyses explosively, releasing its progeny.
   - Lysis inhibition (LIN): under superinfection gp63 appears to be held off;
     the cell keeps elongating; the late gp62 holin, or spontaneous release,
     frees gp61; the cell rounds and lyses (asynchronous lysis). The paper marks this half as a proposed
     model, and the status text says so.

   Everything is computed from a handful of numbers (cell half-length and
   radius, how released the endolysin is, how burst the cell is, ...) that
   ease between steps, so the cell morphs continuously and every protein rides
   on the membrane as it changes shape. Without JS the page shows a static
   picture of the rod (the <noscript> image). */
(function () {
    'use strict';
    var NS = 'http://www.w3.org/2000/svg';
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var W = 800, H = 360, CX = 345, CY = 186;
    // Half-length of the straight sides, and radius. The round cell is only a little wider than the rod:
    // the preprint sees the rod contract from the poles as gp61 degrades the wall evenly, not balloon.
    var ROD = { L: 150, R: 62 }, ROUND = { L: 0, R: 84 }, GROW = 38;   // GROW: extra half-length as an inhibited cell keeps elongating
    var PERI = 7, OM = 14;                                    // cell wall and outer membrane offsets from the inner membrane

    // Where things sit on the inner membrane, as fractions of its perimeter
    var T_LYS = [0.03, 0.15, 0.27, 0.39, 0.53, 0.65, 0.77, 0.89];
    var T_PIN = [0.09, 0.21, 0.33, 0.47, 0.59, 0.71, 0.83, 0.95];
    var T_G62 = [0.12, 0.45, 0.74];
    var T_SPAN = [0.06, 0.36, 0.56, 0.86];
    var T_SIN = [0.07, 0.16, 0.25, 0.62];                     // superinfecting phages, docked on the outer membrane
    var PROGENY = [[-.78, -.35], [-.55, .4], [-.32, -.5], [-.12, .15], [.08, -.38], [.28, .45],
                   [.46, -.12], [.66, .32], [.82, -.4], [-.92, .05], [.2, -.02], [-.4, -.05], [.6, -.52], [-.05, .58]];

    var PATHS = {
        rapid: [
            { pins: 0, status: 'A rod-shaped cell full of new phages · gp61 tethered in the inner membrane, inactive', tag: 'INFECTED · LYSIS PROTEINS MADE' },
            { pins: 1, status: 'gp63 pinholin opens pinholes · the inner membrane depolarizes', tag: 'gp63 PINHOLES · MEMBRANE DEPOLARIZED' },
            { pins: 1, rel: 1, status: 'gp61 released and active · it degrades the wall evenly, and the rod contracts from the poles and rounds', tag: 'gp61 DEGRADES THE WALL · ROD → ROUND' },
            { pins: 1, rel: 1, span: 1, burst: 1, status: 'With enough wall gone, the gp60/gp60a spanins act · explosive lysis releases the phages (rapid, synchronous lysis)', tag: 'SPANINS · EXPLOSIVE LYSIS' }
        ],
        lin: [
            { status: 'A rod-shaped cell full of new phages · gp61 tethered in the inner membrane, inactive', tag: 'INFECTED · LYSIS PROTEINS MADE' },
            { sin: 1, held: 1, grow: 1, status: 'Superinfection → lysis inhibition · gp63 held off; the cell stays a rod and keeps elongating', tag: 'SUPERINFECTION · gp63 HELD OFF' },
            { sin: 1, held: 1, grow: 1, g62: 1, status: 'Proposed: the late gp62 holin opens the inner membrane (holins alone leave the rod shape unchanged)', tag: 'PROPOSED · LATE gp62 HOLIN' },
            { sin: 1, held: 1, grow: 1, g62: 1, rel: 1, status: 'Proposed: gp61 released (by gp62, or spontaneously) · the wall is degraded and the rod contracts to round', tag: 'PROPOSED · gp61 DEGRADES THE WALL' },
            { sin: 1, held: 1, grow: 1, g62: 1, rel: 1, span: 1, burst: 1, status: 'Spanins act · explosive lysis releases the phages (exit from LIN, asynchronous lysis)', tag: 'SPANINS · EXPLOSIVE LYSIS' }
        ]
    };
    // How each quantity moves when it changes: [duration, delay] in seconds
    var TIMING = { pins: [0.5, 0], held: [0.4, 0], sin: [0.6, 0], grow: [1.4, 0.3], g62: [0.5, 0],
                   rel: [0.8, 0], round: [1.3, 0.55], span: [0.6, 0], burst: [1.3, 0.7] };

    function el(tag, attrs, parent) {
        var e = document.createElementNS(NS, tag);
        for (var k in attrs) e.setAttribute(k, attrs[k]);
        if (parent) parent.appendChild(e);
        return e;
    }
    function lerp(a, b, t) { return a + (b - a) * t; }
    function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }

    // Capsule (stadium) outline: straight sides of half-length L, round ends of radius R
    function capsule(L, R) {
        return 'M' + (CX - L) + ' ' + (CY - R) + ' H' + (CX + L) +
            ' A' + R + ' ' + R + ' 0 0 1 ' + (CX + L) + ' ' + (CY + R) + ' H' + (CX - L) +
            ' A' + R + ' ' + R + ' 0 0 1 ' + (CX - L) + ' ' + (CY - R) + ' Z';
    }
    // Point at fraction t of the perimeter (clockwise from top-left), pushed `off` along the outward normal
    function onCell(t, L, R, off) {
        var P = 4 * L + 2 * Math.PI * R, s = ((t % 1) + 1) % 1 * P, x, y, nx, ny, a;
        if (s < 2 * L) { x = CX - L + s; y = CY - R; nx = 0; ny = -1; }
        else if ((s -= 2 * L) < Math.PI * R) { a = -Math.PI / 2 + s / R; nx = Math.cos(a); ny = Math.sin(a); x = CX + L + R * nx; y = CY + R * ny; }
        else if ((s -= Math.PI * R) < 2 * L) { x = CX + L - s; y = CY + R; nx = 0; ny = 1; }
        else { s -= 2 * L; a = Math.PI / 2 + s / R; nx = Math.cos(a); ny = Math.sin(a); x = CX - L + R * nx; y = CY + R * ny; }
        return { x: x + nx * off, y: y + ny * off, nx: nx, ny: ny, deg: Math.atan2(ny, nx) * 180 / Math.PI };
    }
    function place(g, p, rotDeg) { g.setAttribute('transform', 'translate(' + p.x.toFixed(1) + ',' + p.y.toFixed(1) + ') rotate(' + rotDeg.toFixed(1) + ')'); }

    function build(host) {
        var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-hidden': 'true', focusable: 'false' });
        var g = {};
        g.peri = el('path', { class: 'sar-peri' }, svg);           // periplasm band (outer membrane → inner membrane)
        g.cyto = el('path', { class: 'sar-cyto' }, svg);
        g.om = el('path', { class: 'sar-om' }, svg);
        g.pg = el('path', { class: 'sar-pg' }, svg);
        g.im = el('path', { class: 'sar-im' }, svg);
        g.labels = el('g', { class: 'sar-labels' }, svg);
        g.lab = ['OUTER MEMBRANE', 'CELL WALL', 'INNER MEMBRANE'].map(function (txt) {
            return { line: el('path', { class: 'sar-leader' }, g.labels),
                     text: el('text', { class: 'sym sar-lab', 'text-anchor': 'start' }, g.labels) };
        });
        g.lab.forEach(function (l, i) { l.text.textContent = ['OUTER MEMBRANE', 'CELL WALL', 'INNER MEMBRANE'][i]; });
        function marks(ts, make) { return ts.map(function (t) { var m = el('g', {}, svg); make(m); return { t: t, g: m }; }); }
        g.pins = marks(T_PIN, function (m) {
            el('rect', { x: -3, y: -9, width: 2.5, height: 18, rx: 1, class: 'sar-pin' }, m);
            el('rect', { x: 0.5, y: -9, width: 2.5, height: 18, rx: 1, class: 'sar-pin' }, m);
        });
        g.held = marks(T_PIN, function (m) { el('rect', { x: -2.5, y: -9, width: 5, height: 18, rx: 1.5, class: 'sar-pin-held' }, m); });
        g.g62 = marks(T_G62, function (m) {
            el('rect', { x: -7, y: -10, width: 3, height: 20, rx: 1, class: 'sar-g62' }, m);
            el('rect', { x: 4, y: -10, width: 3, height: 20, rx: 1, class: 'sar-g62' }, m);
        });
        g.span = marks(T_SPAN, function (m) { el('path', { d: 'M0 -1 V-' + OM, class: 'sar-span' }, m); });
        g.lys = marks(T_LYS, function (m) {
            el('path', { d: 'M-5 0 H-14', class: 'sar-tether' }, m);   // the SAR anchor, into the inner membrane
            var body = el('g', { class: 'sar-lys-body' }, m);
            el('path', { class: 'sar-pac', d: PAC_SHUT }, body);
            el('circle', { cx: -2.2, cy: -3, r: 1.1, class: 'sar-eye' }, body);
        });
        g.progeny = PROGENY.map(function () {
            var m = el('g', {}, svg);
            el('path', { d: 'M-5 -5 l5 -3 5 3 v6 l-5 3 -5 -3 Z M0 4 v3 M0 6 l-3 2 M0 6 l3 2', class: 'sar-phage' }, m);
            return m;
        });
        g.sin = marks(T_SIN, function (m) {
            el('path', { d: 'M-7 -19 l7 -4 7 4 v8 l-7 4 -7 -4 Z M0 -7 v5 M0 -3 l-4 3 M0 -3 l4 3', class: 'sar-sinphage' }, m);
        });
        g.tag = el('text', { class: 'sym sar-stage', x: W / 2, y: H - 10, 'text-anchor': 'middle' }, svg);
        host.appendChild(svg);
        return g;
    }

    // Pac-Man mouths, drawn at the origin facing +x (rotated onto the membrane normal)
    function pac(half) {
        var r = 6, a = half * Math.PI / 180;
        return 'M0 0 L' + (r * Math.cos(a)).toFixed(2) + ' ' + (-r * Math.sin(a)).toFixed(2) +
            ' A' + r + ' ' + r + ' 0 1 0 ' + (r * Math.cos(a)).toFixed(2) + ' ' + (r * Math.sin(a)).toFixed(2) + ' Z';
    }
    var PAC_SHUT = pac(0.5), PAC_OPEN = pac(38);

    function draw(g, v, now) {
        var L = lerp(ROD.L + GROW * v.grow, ROUND.L, v.round), R = lerp(ROD.R, ROUND.R, v.round);
        var b = v.burst, swell = 1 + 0.12 * b;
        g.im.setAttribute('d', capsule(L, R));
        g.pg.setAttribute('d', capsule(L, R + PERI));
        g.om.setAttribute('d', capsule(L, (R + OM) * swell));
        g.peri.setAttribute('d', capsule(L, R + OM));
        g.cyto.setAttribute('d', capsule(L, R));
        // the wall fades as gp61 cuts it; at the burst the whole envelope tears and fades
        g.pg.style.opacity = (1 - 0.8 * v.rel) * (1 - b);
        g.im.style.opacity = 1 - 0.75 * b;
        g.om.style.opacity = 1 - 0.85 * b;
        g.om.style.strokeDasharray = b > 0 ? (40 - 30 * b) + ' ' + (60 * b) : 'none';
        g.peri.style.opacity = 1 - b; g.cyto.style.opacity = 1 - b;

        // layer labels on the right-hand end of the cell
        [[-0.62, OM], [-0.15, PERI], [0.4, 0]].forEach(function (spec, i) {
            var a = spec[0], r = R + spec[1], px = CX + L + r * Math.cos(a), py = CY + r * Math.sin(a);
            var ty = CY - 46 + i * 46, tx = 640;
            g.lab[i].line.setAttribute('d', 'M' + px.toFixed(1) + ' ' + py.toFixed(1) + ' L' + (tx - 8) + ' ' + ty);
            g.lab[i].text.setAttribute('x', tx); g.lab[i].text.setAttribute('y', ty + 3.5);
        });
        g.labels.style.opacity = 1 - b;

        g.pins.forEach(function (m) { var p = onCell(m.t, L, R, 0); place(m.g, p, p.deg + 90); m.g.style.opacity = v.pins * (1 - b); });
        g.held.forEach(function (m) { var p = onCell(m.t, L, R, 0); place(m.g, p, p.deg + 90); m.g.style.opacity = 0.8 * v.held * (1 - b); });
        g.g62.forEach(function (m) { var p = onCell(m.t, L, R, 0); place(m.g, p, p.deg + 90); m.g.style.opacity = v.g62 * (1 - b); });
        g.span.forEach(function (m) { var p = onCell(m.t, L, R, 0); place(m.g, p, p.deg + 90); m.g.style.opacity = (0.35 + 0.65 * v.span) * (1 - b); });

        // gp61: tethered just outside the inner membrane; released, it lifts into the periplasm and chomps
        var chompOpen = Math.abs(Math.sin(now / 160));
        g.lys.forEach(function (m, i) {
            var p = onCell(m.t, L, R, 6 + 2 * v.rel);
            place(m.g, p, p.deg);
            m.g.firstChild.style.opacity = 1 - v.rel;
            var mouth = v.rel > 0.5 ? (reduce ? 38 : 6 + 32 * chompOpen) : 0.5;
            m.g.querySelector('.sar-pac').setAttribute('d', pac(mouth));
            m.g.style.opacity = 1 - b;
        });

        // progeny: packed inside the cell until the burst throws them out
        g.progeny.forEach(function (m, i) {
            var u = PROGENY[i][0], w = PROGENY[i][1];
            var ix = CX + u * (L + 0.62 * R), iy = CY + w * 0.62 * R;
            var a = Math.atan2(w, u * 1.4), k = 1 + (i % 3) * 0.08;
            var ox = CX + Math.cos(a) * 255 * k, oy = CY + Math.sin(a) * 118 * k;
            var t = ease(Math.min(1, Math.max(0, b * 1.25 - (i % 5) * 0.05)));
            m.setAttribute('transform', 'translate(' + lerp(ix, ox, t).toFixed(1) + ',' + lerp(iy, oy, t).toFixed(1) + ') rotate(' + (t * (i % 2 ? 40 : -40)).toFixed(1) + ')');
        });

        // superinfecting phages dock on the outer membrane, tails toward the cell
        g.sin.forEach(function (m) { var p = onCell(m.t, L, R, OM); place(m.g, p, p.deg + 90); m.g.style.opacity = v.sin * (1 - b); });
    }

    function wire(f) {
        var host = f.querySelector('.sar-cell');
        if (!host) return;
        var g = build(host);
        var btn = f.querySelector('.fig-act'), status = f.querySelector('.fig-status'), modes = Array.prototype.slice.call(f.querySelectorAll('.fig-mode'));
        var keys = ['pins', 'held', 'sin', 'grow', 'g62', 'rel', 'round', 'span', 'burst'];
        var v = {}, anim = {};
        keys.forEach(function (k) { v[k] = 0; });
        var mode = 'rapid', step = 0, raf = null, visible = true;

        function target(st) {
            return { pins: st.pins || 0, held: st.held || 0, sin: st.sin || 0, grow: st.grow || 0, g62: st.g62 || 0,
                     rel: st.rel || 0, round: st.rel || 0, span: st.span || 0, burst: st.burst || 0 };
        }
        function go(st, instant) {
            var t = target(st), now = performance.now();
            keys.forEach(function (k) {
                if (instant || reduce) { v[k] = t[k]; delete anim[k]; return; }
                if (t[k] === v[k] && !anim[k]) return;
                // moving backwards (replay/reset) is quick and undelayed
                var back = t[k] < v[k], tm = TIMING[k];
                anim[k] = { from: v[k], to: t[k], t0: now + (back ? 0 : tm[1] * 1000), dur: (back ? 0.35 : tm[0]) * 1000 };
            });
            g.tag.textContent = st.tag;
            status.textContent = (step + 1) + '/' + PATHS[mode].length + ' · ' + st.status;
            btn.textContent = step === PATHS[mode].length - 1 ? 'Replay' : 'Next step';
            modes.forEach(function (m) { m.setAttribute('aria-pressed', String(m.getAttribute('data-mode') === mode)); });
            kick();
        }
        function frame(now) {
            raf = null;
            var busy = false;
            keys.forEach(function (k) {
                var a = anim[k];
                if (!a) return;
                var p = (now - a.t0) / a.dur;
                if (p >= 1) { v[k] = a.to; delete anim[k]; }
                else { busy = true; if (p > 0) v[k] = lerp(a.from, a.to, ease(p)); }
            });
            draw(g, v, now);
            // keep ticking while anything moves, or while released endolysins chomp on screen
            if (busy || (v.rel > 0.5 && v.burst < 1 && !reduce && visible)) kick();
        }
        function kick() { if (!raf) raf = requestAnimationFrame(frame); }

        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (es) { visible = es[0].isIntersecting; if (visible) kick(); }).observe(f);
        }
        function next() { step = (step + 1) % PATHS[mode].length; go(PATHS[mode][step], step === 0); }
        modes.forEach(function (m) {
            m.addEventListener('click', function () { mode = m.getAttribute('data-mode'); step = 0; go(PATHS[mode][0], true); });
        });
        btn.addEventListener('click', next);
        host.addEventListener('click', next);
        go(PATHS[mode][0], true);
        draw(g, v, performance.now());
        f.querySelector('.fig-ctl').hidden = false;
    }

    function init() {
        Array.prototype.forEach.call(document.querySelectorAll('figure[data-fig="sar"]'), wire);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
