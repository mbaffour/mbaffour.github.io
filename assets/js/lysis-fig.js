/* lysis-fig.js — the N4 lysis-machinery figure, shared by the homepage
   (Research Focus) and journey.html (Fig 6). Wires every
   <figure data-fig="sar"> on the page; the markup and styles live with each
   page.

   Three stages, as N4 does it: SAR endolysin tethered in the inner membrane
   and inactive (no mouth); pinholes form and depolarize the membrane; the
   endolysins are released into the periplasm, open their mouths and cut the
   wall (cuts land after each enzyme arrives). Starts at the first stage.

   The control row ships `hidden` and is un-hidden here, so without JS the
   static drawing shows and there is no dead button. The button is the
   keyboard route; the drawing is also clickable, as a pointer convenience. */
(function () {
    'use strict';
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var STAGES = [['Form pinholes', 'SAR endolysin anchored · inactive'],
                  ['Release endolysin', 'pinholes · membrane depolarized'],
                  ['Reset', 'SAR endolysin released · cutting the wall']];

    function wire(f) {
        var svg = f.querySelector('svg'),
            btn = f.querySelector('.fig-act'), status = f.querySelector('.fig-status'),
            pins = Array.prototype.slice.call(svg.querySelectorAll('.sar-pins > g')),
            cuts = Array.prototype.slice.call(svg.querySelectorAll('.sar-cuts rect')),
            intact = svg.querySelector('.sar-intact'), broken = svg.querySelector('.sar-broken'),
            lys = Array.prototype.slice.call(svg.querySelectorAll('.sar-lys g g'));
        var stage = 0;

        function render() {
            intact.style.opacity = stage === 0 ? '.7' : '0';   // .7 = .stroke-ink's own opacity
            broken.style.opacity = stage === 0 ? '0' : '.7';
            pins.forEach(function (g, i) {
                g.style.transitionDelay = stage === 1 && !reduce ? i * 0.1 + 's' : '0s';
                g.style.opacity = stage === 0 ? '0' : '1';
            });
            lys.forEach(function (g, i) {
                var d = stage === 2 && !reduce ? i * 0.12 : 0;
                g.style.transitionDelay = d + 's';
                g.style.transform = stage === 2 ? 'translate(0,-17px)' : 'none';
                var tm = g.querySelector('path');
                tm.style.transitionDelay = d + 's';
                tm.style.opacity = stage === 2 ? '0' : '1';
                // inactive in the membrane: no mouth until released
                var pac = g.querySelector('.sar-pac');
                pac.setAttribute('d', pac.getAttribute(stage === 2 ? 'data-open' : 'data-shut'));
                pac.classList.toggle('chomp', stage === 2);
                cuts[i].style.transitionDelay = stage === 2 && !reduce ? d + 0.6 + 's' : '0s';
                cuts[i].style.opacity = stage === 2 ? '1' : '0';
            });
            btn.textContent = STAGES[stage][0];
            status.textContent = STAGES[stage][1];
        }
        function step() { stage = (stage + 1) % 3; render(); }

        render();
        btn.addEventListener('click', step);
        svg.addEventListener('click', step);
        f.querySelector('.fig-ctl').hidden = false;
    }

    function init() {
        Array.prototype.forEach.call(document.querySelectorAll('figure[data-fig="sar"]'), wire);
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();
})();
