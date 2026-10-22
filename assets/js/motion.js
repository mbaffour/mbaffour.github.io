/* motion.js — scroll choreography for the homepage.
 *   1. --hs on the hero: 0 at the top, 1 once the hero has scrolled away
 *      (site.css eases the copy up and out, and drifts the microscope).
 *   2. Staggered reveals: cards inside each section rise in one after another
 *      as they enter the viewport, then drop the class so hover effects behave.
 * Nothing here runs under prefers-reduced-motion.
 */
(function () {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var hero = document.getElementById('hero');
    if (hero) {
        var ticking = false;
        var update = function () {
            ticking = false;
            var h = hero.offsetHeight || 1;
            var k = Math.min(1, Math.max(0, window.scrollY / (h * 0.85)));
            hero.style.setProperty('--hs', k.toFixed(3));
        };
        window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
        update();
    }

    if (!('IntersectionObserver' in window)) return;
    var GROUPS = [
        '.research-grid > *', '.bench-cols > *', '.card-grid > *', '.rec-grid > *', '.teach-grid > *',
        '.blog-list > *', '.pub-list > *', '.talk-list > *', '.build-grid > *', '.about-grid > *', '.pa-show'
    ];
    var els = [];
    GROUPS.forEach(function (sel) {
        var seen = new Map();
        document.querySelectorAll(sel).forEach(function (el) {
            if (el.closest('.hero')) return;
            var parent = el.parentElement, i = seen.get(parent) || 0;
            seen.set(parent, i + 1);
            el.style.setProperty('--rv-i', Math.min(i, 7));
            el.classList.add('rv');
            els.push(el);
        });
    });
    if (!els.length) return;
    document.documentElement.classList.add('motion');
    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
            if (!e.isIntersecting) return;
            var el = e.target;
            el.classList.add('rv-in');
            io.unobserve(el);
            // hand transforms back to the cards' own hover rules once revealed
            setTimeout(function () { el.classList.remove('rv', 'rv-in'); el.style.removeProperty('--rv-i'); }, 1700);
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    els.forEach(function (el) { io.observe(el); });
})();
