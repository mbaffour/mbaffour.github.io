/* lysis-fig.js — the N4 lysis-model figure, shared by the homepage
   (Research Focus) and journey.html (Fig 6). Wires every
   <figure data-fig="sar"> on the page; the markup and styles live with each
   page (the markup is generated identically into both).

   Two pathways, after Fig. 7 of the first-author preprint
   (doi:10.1101/2025.11.12.688109):
   - Rapid lysis: the gp63 pinholin makes pinholes that depolarize the inner
     membrane; the gp61 SAR endolysin is released, takes its active form and
     cuts the wall; the gp60/gp60a spanins disrupt the outer membrane, and the
     cell bursts, releasing its progeny (the last step of both pathways).
   - Lysis inhibition (LIN): under superinfection the gp63 pinholin appears to
     be held off; gp61, released spontaneously or by the late gp62 holin, then
     gives asynchronous lysis. The paper marks this half as a proposed model,
     and the status text says so.

   The control row ships `hidden` and is un-hidden here, so without JS the
   static drawing (the end of rapid lysis) shows and there is no dead button. */
(function () {
    'use strict';
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Each step: what is on screen. pins: 'none' | 'open' | 'held'.
    var PATHS = {
        rapid: [
            { pins: 'none', status: 'Lysis proteins made · gp61 tethered in the membrane, inactive', tag: 'INFECTED · LYSIS PROTEINS MADE' },
            { pins: 'open', status: 'gp63 pinholin opens pinholes · inner membrane depolarized', tag: 'gp63 PINHOLES · MEMBRANE DEPOLARIZED' },
            { pins: 'open', rel: true, status: 'gp61 SAR endolysin released, now active · cutting the wall', tag: 'gp61 RELEASED · CELL WALL CUT' },
            { pins: 'open', rel: true, span: true, burst: true, status: 'gp60/gp60a spanins disrupt the outer membrane · the cell bursts, releasing new phages (rapid, synchronous lysis)', tag: 'CELL BURSTS · PROGENY RELEASED' }
        ],
        lin: [
            { pins: 'none', status: 'Lysis proteins made · gp61 tethered in the membrane, inactive', tag: 'INFECTED · LYSIS PROTEINS MADE' },
            { pins: 'held', sin: true, status: 'Superinfection → lysis inhibition · gp63 pinholin held off', tag: 'SUPERINFECTION · gp63 HELD OFF' },
            { pins: 'held', sin: true, gp62: true, status: 'Proposed: the late gp62 holin opens the membrane', tag: 'PROPOSED · LATE gp62 HOLIN' },
            { pins: 'held', sin: true, gp62: true, rel: true, status: 'Proposed: gp61 released (by gp62, or spontaneously) · cutting the wall', tag: 'PROPOSED · gp61 RELEASED' },
            { pins: 'held', sin: true, gp62: true, rel: true, span: true, burst: true, status: 'Spanins disrupt the outer membrane · the cell bursts, releasing new phages (exit from LIN, asynchronous lysis)', tag: 'CELL BURSTS · EXIT FROM LIN' }
        ]
    };

    function all(root, sel) { return Array.prototype.slice.call(root.querySelectorAll(sel)); }

    function wire(f) {
        var svg = f.querySelector('svg'),
            btn = f.querySelector('.fig-act'), status = f.querySelector('.fig-status'),
            modes = all(f, '.fig-mode'), tag = svg.querySelector('.sar-stage'),
            sin = svg.querySelector('.sar-sin'), phages = all(svg, '.sar-sin > g > g'),
            pins = all(svg, '.sar-pins > g'), held = svg.querySelector('.sar-pins-held'),
            gp62 = svg.querySelector('.sar-gp62'),
            imIntact = svg.querySelector('.sar-intact'), imPins = svg.querySelector('.sar-broken'),
            imG = svg.querySelector('.sar-broken-g'),
            omIntact = svg.querySelector('.sar-om-intact'), omBroken = svg.querySelector('.sar-om-broken'),
            ispans = all(svg, '.sar-ispan'),
            env = svg.querySelector('.sar-env'), virions = all(svg, '.sar-virions > g > g'),
            cuts = all(svg, '.sar-cuts rect'), lys = all(svg, '.sar-lys g g');
        var mode = 'rapid', step = 0;

        function op(el, on, max) { el.style.opacity = on ? (max || '1') : '0'; }
        function delay(el, s) { el.style.transitionDelay = (reduce ? 0 : s) + 's'; }

        function render() {
            var path = PATHS[mode], st = path[step];
            // superinfecting phages drop onto the outer membrane
            op(sin, st.sin);
            phages.forEach(function (g, i) {
                delay(g, st.sin ? i * 0.12 : 0);
                g.style.transform = st.sin ? 'none' : 'translate(0,-24px)';
            });
            // inner membrane: intact, broken at the pinholes, or broken at the gp62 hole
            op(imIntact, st.pins !== 'open' && !st.gp62, '.7');   // .7 = .stroke-ink's own opacity
            op(imPins, st.pins === 'open', '.7');
            op(imG, st.gp62 && st.pins !== 'open', '.7');
            pins.forEach(function (g, i) { delay(g, st.pins === 'open' ? i * 0.1 : 0); op(g, st.pins === 'open'); });
            op(held, st.pins === 'held');
            op(gp62, st.gp62);
            // gp61: tethered without a mouth, or released, mouth open and chomping
            lys.forEach(function (g, i) {
                var d = st.rel ? i * 0.12 : 0;
                delay(g, d);
                g.style.transform = st.rel ? 'translate(0,-20px)' : 'none';
                var tm = g.querySelector('path');
                delay(tm, d); op(tm, !st.rel);
                var pac = g.querySelector('.sar-pac');
                pac.setAttribute('d', pac.getAttribute(st.rel ? 'data-open' : 'data-shut'));
                pac.classList.toggle('chomp', !!st.rel);
                delay(cuts[i], st.rel ? d + 0.6 : 0); op(cuts[i], st.rel);
            });
            // spanins: i-spanin a stub until it reaches the outer membrane, which then breaks
            ispans.forEach(function (p, i) {
                delay(p, st.span ? i * 0.1 : 0);
                p.style.strokeDashoffset = st.span ? '0' : '0.62';
            });
            delay(omBroken, st.span ? 0.6 : 0); delay(omIntact, st.span ? 0.6 : 0);
            op(omIntact, !st.span, '.7'); op(omBroken, st.span, '.7');
            // the burst: once the outer membrane is breached, the envelope gives way and the
            // progeny assembled in the cytoplasm stream out through it
            delay(env, st.burst ? 1.2 : 0);
            env.style.opacity = st.burst ? '.35' : '1';
            virions.forEach(function (v, i) {
                delay(v, st.burst ? 1.2 + i * 0.07 : 0);
                v.style.transform = st.burst
                    ? 'translate(' + v.getAttribute('data-dx') + 'px,' + v.getAttribute('data-dy') + 'px)'
                    : 'none';
            });

            if (tag) tag.textContent = st.tag;
            status.textContent = (step + 1) + '/' + path.length + ' · ' + st.status;
            btn.textContent = step === path.length - 1 ? 'Replay' : 'Next step';
            modes.forEach(function (m) { m.setAttribute('aria-pressed', String(m.getAttribute('data-mode') === mode)); });
        }

        function next() { step = (step + 1) % PATHS[mode].length; render(); }

        modes.forEach(function (m) {
            m.addEventListener('click', function () { mode = m.getAttribute('data-mode'); step = 0; render(); });
        });
        btn.addEventListener('click', next);
        svg.addEventListener('click', next);
        render();
        f.querySelector('.fig-ctl').hidden = false;
    }

    function init() {
        Array.prototype.forEach.call(document.querySelectorAll('figure[data-fig="sar"]'), wire);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
