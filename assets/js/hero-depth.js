/* hero-depth.js — the out-of-focus culture behind the hero.
 *
 * Replaces the generic floating-microbe canvas on the homepage hero with the
 * same darkfield world the eyepiece shows, but out of the focal plane: cells and
 * phages at three depths, blurred by the canvas's CSS filter, drifting, growing
 * and now and then bursting. Depth shows as parallax: nearer layers move more
 * with the pointer and with scroll. Drawn at half resolution (it is blurred
 * anyway), paused off screen; one still frame under reduced motion.
 */
(function () {
    var canvas = document.getElementById('heroDepth');
    if (!canvas) return;
    var hero = document.getElementById('hero');
    var ctx = canvas.getContext('2d');
    var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    function rng(s) { return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
    var r = rng(9), cells = [], phages = [];
    for (var i = 0; i < 26; i++) cells.push({ x: r(), y: r(), a: r() * 3.14, L: 0.6 + r() * 0.6, d: [0.25, 0.55, 0.95][i % 3], ph: r() * 40, per: 18 + r() * 16, va: (r() - 0.5) * 0.04 });
    for (i = 0; i < 70; i++) phages.push({ x: r(), y: r(), d: 0.2 + r() * 0.8, ph: r() * 6.28, sp: 0.4 + r() });
    var W, H, S, px = 0, py = 0, tx = 0, ty = 0;
    function size() {
        var b = canvas.getBoundingClientRect();
        W = b.width; H = b.height; S = 0.5;
        canvas.width = Math.max(1, Math.round(W * S)); canvas.height = Math.max(1, Math.round(H * S));
    }
    function capsule(h, rr) {
        ctx.beginPath(); ctx.arc(h, 0, rr, -Math.PI / 2, Math.PI / 2); ctx.arc(-h, 0, rr, Math.PI / 2, Math.PI * 1.5); ctx.closePath();
    }
    function draw(t) {
        ctx.setTransform(S, 0, 0, S, 0, 0);
        ctx.clearRect(0, 0, W, H);
        var U = Math.min(W, H) / 900, sc = window.scrollY || 0;
        cells.forEach(function (c) {
            var z = 0.55 + c.d, age = ((t + c.ph) % c.per) / c.per;
            var ox = px * 60 * c.d, oy = py * 40 * c.d - sc * 0.25 * c.d;
            var x = c.x * W + Math.sin(t * 0.04 + c.ph) * 30 + ox, y = c.y * H + Math.cos(t * 0.035 + c.ph) * 24 + oy;
            var grow = 1 + 0.35 * age, burst = age > 0.94 ? (age - 0.94) / 0.06 : 0;
            var h = 70 * c.L * U * z * grow * (1 - burst), rr = 30 * U * z * (1 + 0.3 * burst);
            ctx.save(); ctx.translate(x, y); ctx.rotate(c.a + t * c.va);
            ctx.globalAlpha = (0.08 + 0.17 * c.d) * (1 - burst) * Math.min(1, age * 12);
            capsule(h, rr);
            ctx.lineWidth = 3.5 * U * z; ctx.strokeStyle = age > 0.6 ? '#d98a8a' : '#f5edd8'; ctx.stroke();
            ctx.fillStyle = 'rgba(244,196,48,0.05)'; ctx.fill();
            ctx.restore();
            if (burst > 0) {
                ctx.globalAlpha = (1 - burst) * 0.5 * c.d;
                ctx.beginPath(); ctx.arc(x, y, rr + burst * 160 * U * z, 0, 6.283);
                ctx.lineWidth = 3 * U; ctx.strokeStyle = '#f4c430'; ctx.stroke();
            }
            ctx.globalAlpha = 1;
        });
        ctx.fillStyle = '#f5edd8';
        phages.forEach(function (f) {
            var ox = px * 80 * f.d, oy = py * 50 * f.d - sc * 0.3 * f.d;
            var x = ((f.x * W + Math.sin(t * 0.13 * f.sp + f.ph) * 60 + t * 4 * f.sp) % (W + 40)) - 20 + ox;
            var y = f.y * H + Math.cos(t * 0.11 * f.sp + f.ph) * 40 + oy;
            ctx.globalAlpha = 0.18 + 0.4 * f.d;
            ctx.beginPath(); ctx.arc(x, y, (2.2 + 3 * f.d) * U * 1.4, 0, 6.283); ctx.fill();
        });
        ctx.globalAlpha = 1;
    }
    size();
    window.addEventListener('resize', function () { size(); if (reduce) draw(0); });
    if (reduce) { draw(0); return; }
    var running = false, t0 = performance.now();
    function frame(now) {
        if (!running) return;
        px += (tx - px) * 0.05; py += (ty - py) * 0.05;
        draw((now - t0) / 1000);
        requestAnimationFrame(frame);
    }
    function setRun(on) {
        if (on && !running) { running = true; requestAnimationFrame(frame); }
        else if (!on) running = false;
    }
    new IntersectionObserver(function (es) { setRun(es[0].isIntersecting && !document.hidden); }).observe(hero);
    document.addEventListener('visibilitychange', function () { setRun(!document.hidden && hero.getBoundingClientRect().bottom > 0); });
    if (matchMedia('(hover: hover)').matches) {
        hero.addEventListener('pointermove', function (e) { tx = e.clientX / window.innerWidth - 0.5; ty = e.clientY / window.innerHeight - 0.5; });
    }
    draw(0);
})();
