/* dive.js — "Inside one infection": a pinned, scroll-driven scene under the hero.
 *
 * The section is tall; its stage sticks to the viewport while you scroll through
 * it, and scroll progress p (0 → 1) is the timeline:
 *   0.00  the eyepiece opens to fill the screen
 *   0.08  an N4 particle lands             0.18  it injects its genome
 *   0.30  progeny assemble, the rod grows  0.44  more phages arrive: lysis inhibition
 *   0.60  pinholes, the rod contracts from the poles into a sphere
 *   0.74  the burst                        0.86  the question, and a way on
 * The focal cell is a pure function of p, so scrolling back plays it backwards.
 * The culture around it drifts with time, so the field stays alive when you stop.
 * Reduced motion: no pinning; every caption is shown with one still frame.
 */
(function () {
    var sec = document.getElementById('dive');
    if (!sec) return;
    var canvas = sec.querySelector('.dive-canvas'), ctx = canvas.getContext('2d');
    var beats = [].slice.call(sec.querySelectorAll('.dive-beat'));
    var clock = sec.querySelector('.dive-clock'), bar = sec.querySelector('.dive-progress span');
    var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    var AT = beats.map(function (b) { return +b.getAttribute('data-at'); });

    function clamp(x, a, b) { return x < (a || 0) ? (a || 0) : x > (b == null ? 1 : b) ? (b == null ? 1 : b) : x; }
    function seg(p, a, b) { return clamp((p - a) / (b - a)); }
    function ease(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
    function out(x) { return 1 - Math.pow(1 - x, 3); }
    function lerp(a, b, k) { return a + (b - a) * k; }
    function rng(s) { return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
    var CREAM = [245, 237, 216], GOLD = [244, 196, 48], CORAL = [244, 105, 127], GREEN = [63, 191, 110];
    function rgba(c, o) { return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + clamp(o).toFixed(3) + ')'; }
    function mix(a, b, t) { return [0, 1, 2].map(function (i) { return Math.round(a[i] + (b[i] - a[i]) * t); }); }

    /* ---------- fixed cast, generated once ---------- */
    var r = rng(4);
    var amb = [], free = [], prog = [], shards = [], pins = [];
    for (var i = 0; i < 16; i++) amb.push({ x: r() * 2 - 1, y: r() * 2 - 1, a: r() * 3.14, L: 90 + r() * 70, d: 0.35 + r() * 0.5, ph: r() * 6.28 });
    for (i = 0; i < 46; i++) free.push({ x: r() * 2 - 1, y: r() * 2 - 1, ph: r() * 6.28, sp: 0.5 + r(), d: 0.4 + r() * 0.6 });
    for (i = 0; i < 52; i++) prog.push({ fx: r() * 2 - 1, fy: (r() * 2 - 1) * 0.72, dir: r() * 6.283, dist: 0.55 + r() * 0.75, spin: r() * 6 });
    for (i = 0; i < 14; i++) shards.push({ a: i / 14 * 6.283 + (r() - 0.5) * 0.3, s: 0.7 + r() * 0.6, len: 0.25 + r() * 0.3 });
    for (i = 0; i < 14; i++) pins.push({ f: r() * 1.8 - 0.9, side: r() < 0.5 ? -1 : 1, at: 0.60 + i * 0.0028 });
    // the focal cell's phages: where on the surface (axis fraction, outward angle) and when they land
    var LANDERS = [
        { f: 0.32, th: -Math.PI / 2, t0: 0.08, t1: 0.17, inj: 0.20, main: true },
        { f: -0.62, th: -Math.PI / 2 - 0.25, t0: 0.44, t1: 0.49, inj: 0.50 },
        { f: 0.85, th: Math.PI / 2 + 0.2, t0: 0.48, t1: 0.53, inj: 0.54 },
        { f: -0.1, th: Math.PI / 2, t0: 0.52, t1: 0.57, inj: 0.58 }
    ];

    /* ---------- geometry ---------- */
    var W = 0, H = 0, U = 1, DPR = 1;
    function size() {
        var b = canvas.getBoundingClientRect();
        DPR = Math.min(2, window.devicePixelRatio || 1);
        W = b.width; H = b.height;
        canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
        U = Math.min(W, H) / 700;
    }
    function capsule(h, rr) {
        ctx.beginPath();
        ctx.arc(h, 0, rr, -Math.PI / 2, Math.PI / 2);
        ctx.arc(-h, 0, rr, Math.PI / 2, Math.PI * 1.5);
        ctx.closePath();
    }
    function hexagon(x, y, s, a) {
        ctx.beginPath();
        for (var k = 0; k < 6; k++) { var t = a + k * Math.PI / 3; ctx[k ? 'lineTo' : 'moveTo'](x + Math.cos(t) * s, y + Math.sin(t) * s); }
        ctx.closePath();
    }
    // a phage with its tail tip at (x, y), pointing along (nx, ny) away from the tail
    function phage(x, y, nx, ny, s, tone, hollow, glow) {
        ctx.lineWidth = 2.6 * s / 9;
        ctx.strokeStyle = rgba(tone, 0.95);
        ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + nx * s, y + ny * s); ctx.stroke();
        hexagon(x + nx * s * 1.9, y + ny * s * 1.9, s, Math.atan2(ny, nx));
        if (hollow) { ctx.stroke(); return; }
        if (glow) { ctx.shadowColor = rgba(tone, 0.8); ctx.shadowBlur = 12 * DPR; }
        ctx.fillStyle = rgba(tone, 0.98); ctx.fill();
        ctx.shadowBlur = 0;
    }

    /* ---------- one frame ---------- */
    function draw(p, t) {
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
        ctx.fillStyle = '#050402'; ctx.fillRect(0, 0, W, H);
        var cx = W / 2, cy = H / 2;
        // the eyepiece opens from the hero's circle to the whole screen
        var R = lerp(Math.min(W, H) * 0.38, Math.hypot(W, H) / 2 + 30, ease(seg(p, 0, 0.08)));
        ctx.save();
        ctx.beginPath(); ctx.arc(cx, cy, R, 0, 6.283); ctx.clip();
        var bg = ctx.createRadialGradient(cx * 0.9, cy * 0.85, 0, cx, cy, Math.max(W, H) * 0.75);
        bg.addColorStop(0, '#1a150b'); bg.addColorStop(0.65, '#0d0b06'); bg.addColorStop(1, '#060503');
        ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

        var Z = 1 + 0.75 * ease(seg(p, 0.06, 0.32)) - 0.45 * ease(seg(p, 0.72, 0.88));
        var spread = Math.max(W, H) * 0.62;

        // the culture around the focal cell: out of the focal plane, drifting with time
        amb.forEach(function (c) {
            var z = 1 + (Z - 1) * c.d;
            var x = cx + (c.x * spread + Math.sin(t * 0.05 + c.ph) * 26 * U) * z, y = cy + (c.y * spread * 0.7 + Math.cos(t * 0.04 + c.ph) * 20 * U) * z;
            if (Math.hypot(x - cx, y - cy) < 190 * U * Z) return;   // keep the focal cell clear
            ctx.save(); ctx.translate(x, y); ctx.rotate(c.a + Math.sin(t * 0.03 + c.ph) * 0.2);
            capsule(c.L / 2 * U * z * 0.8, 30 * U * z * 0.8);
            ctx.lineWidth = 3 * U; ctx.strokeStyle = rgba(CREAM, 0.12 + 0.18 * c.d); ctx.stroke();
            ctx.fillStyle = rgba(CREAM, 0.025); ctx.fill();
            ctx.restore();
        });
        free.forEach(function (f) {
            var z = 1 + (Z - 1) * f.d;
            var x = cx + (f.x * spread + Math.sin(t * 0.21 * f.sp + f.ph) * 40 * U) * z, y = cy + (f.y * spread * 0.7 + Math.cos(t * 0.17 * f.sp + f.ph * 1.3) * 34 * U) * z;
            var a = t * 0.3 * f.sp + f.ph;
            ctx.globalAlpha = 0.25 + 0.45 * f.d;
            phage(x, y, Math.cos(a), Math.sin(a), 6 * U * Math.sqrt(z), CREAM, false, false);
            ctx.globalAlpha = 1;
        });

        // the focal cell
        var elong = ease(seg(p, 0.30, 0.60)), round = ease(seg(p, 0.64, 0.74)), bu = seg(p, 0.74, 0.86);
        var A = -0.32 + Math.sin(t * 0.25) * 0.025, s = U * Z;
        var h = (160 * (1 + 0.32 * elong) / 2) * (1 - round) * s, rr = 36 * (1 + 0.32 * round) * s;
        var ox = cx + Math.sin(t * 0.2) * 6 * U, oy = cy + Math.cos(t * 0.17) * 5 * U;
        var ca = Math.cos(A), sa = Math.sin(A);
        function W2(lx, ly) { return [ox + lx * ca - ly * sa, oy + lx * sa + ly * ca]; }
        function surf(f, th, off) {
            var q = W2(f * h + Math.cos(th) * (rr + off), Math.sin(th) * (rr + off));
            return { x: q[0], y: q[1], nx: Math.cos(th + A), ny: Math.sin(th + A) };
        }
        var infected = seg(p, 0.20, 0.60), tone = mix(CREAM, CORAL, 0.15 + 0.6 * infected + 0.25 * round);
        var nProg = Math.round(prog.length * clamp(0.35 * seg(p, 0.28, 0.44) + 0.65 * seg(p, 0.44, 0.66)));
        var cellAlpha = 1 - seg(bu, 0.02, 0.2);
        if (cellAlpha > 0) {
            ctx.save(); ctx.translate(ox, oy); ctx.rotate(A); ctx.globalAlpha = cellAlpha;
            capsule(h, rr);
            ctx.fillStyle = rgba(tone, 0.07 + 0.06 * infected); ctx.fill();
            ctx.shadowColor = rgba(p > 0.2 ? tone : GOLD, 0.6); ctx.shadowBlur = 22 * DPR;
            ctx.lineWidth = 4.5 * s; ctx.strokeStyle = rgba(tone, 0.92); ctx.stroke();
            ctx.shadowBlur = 0;
            ctx.beginPath(); ctx.ellipse(0, 0, Math.max(8 * s, h * 0.72 + rr * 0.2), rr * 0.42, 0, 0, 6.283);
            ctx.fillStyle = rgba(GOLD, 0.1 * (1 - infected) + 0.03); ctx.fill();
            // the injected genome, threading in from the first phage
            var dna = seg(p, 0.19, 0.29) * (1 - seg(p, 0.31, 0.37));
            if (dna > 0) {
                var L0 = LANDERS[0], sx = L0.f * h, sy = -rr, n = Math.floor(40 * seg(p, 0.19, 0.29));
                ctx.beginPath(); ctx.moveTo(sx, sy);
                for (var k = 1; k <= n; k++) { var u = k / 40; ctx.lineTo(sx - u * h * 0.9 + Math.sin(u * 22) * 7 * s, sy + u * rr * 1.3 + Math.cos(u * 17) * 6 * s); }
                ctx.lineWidth = 2.2 * s; ctx.strokeStyle = rgba(GOLD, 0.9 * dna); ctx.stroke();
            }
            // progeny assembling
            for (var j = 0; j < nProg; j++) {
                var g = prog[j];
                hexagon(g.fx * (h + rr * 0.45), g.fy * rr * 0.86, 4.6 * s, g.spin);
                ctx.fillStyle = rgba(GOLD, 0.92); ctx.fill();
            }
            // pinholes opening in the membrane
            pins.forEach(function (q) {
                var k2 = seg(p, q.at, q.at + 0.012) * (1 - seg(bu, 0, 0.1));
                if (k2 <= 0) return;
                ctx.beginPath(); ctx.arc(q.f * h, q.side * rr, 3.2 * s * k2, 0, 6.283);
                ctx.fillStyle = '#0d0b06'; ctx.fill();
                ctx.lineWidth = 1.4 * s; ctx.strokeStyle = rgba(GOLD, 0.9); ctx.stroke();
            });
            ctx.restore();
        }
        // lysis inhibition: each superinfecting phage that lands sends out a green ring
        LANDERS.forEach(function (L, idx) {
            if (!idx) return;
            var k3 = seg(p, L.t1, L.t1 + 0.045);
            if (k3 <= 0 || k3 >= 1) return;
            ctx.save(); ctx.translate(ox, oy); ctx.rotate(A);
            capsule(h, rr + (10 + k3 * 40) * s);
            ctx.lineWidth = 3 * s * (1 - k3); ctx.strokeStyle = rgba(GREEN, 0.9 * (1 - k3)); ctx.stroke();
            ctx.restore();
            var q2 = surf(L.f, L.th, 60 * s);
            ctx.font = '600 ' + Math.round(20 * s) + 'px "JetBrains Mono", monospace'; ctx.textAlign = 'center';
            ctx.fillStyle = rgba(GREEN, 1 - k3); ctx.fillText('LIN', q2.x, q2.y);
        });
        // the landing phages
        LANDERS.forEach(function (L) {
            if (p < L.t0) return;
            var k4 = ease(seg(p, L.t0, L.t1));
            var dest = surf(L.f, L.th, 0);
            var x, y, nx, ny, al = 1;
            if (bu > 0) {
                // after the burst the empty capsids drift off
                var d = out(bu) * 160 * s;
                x = dest.x + dest.nx * d; y = dest.y + dest.ny * d; nx = dest.nx; ny = dest.ny; al = 1 - seg(bu, 0.3, 1);
            } else {
                var far = 520 * U, side = (L.main ? 1 : -1) * 120 * U;
                var sx2 = dest.x + dest.nx * far - dest.ny * side, sy2 = dest.y + dest.ny * far + dest.nx * side;
                x = lerp(sx2, dest.x, k4) + Math.sin(k4 * 9) * (1 - k4) * 30 * U; y = lerp(sy2, dest.y, k4) + Math.cos(k4 * 7) * (1 - k4) * 24 * U;
                var wob = (1 - k4) * Math.sin(t * 2 + L.f * 5) * 0.8;
                nx = Math.cos(Math.atan2(dest.ny, dest.nx) + wob); ny = Math.sin(Math.atan2(dest.ny, dest.nx) + wob);
            }
            ctx.globalAlpha = al;
            phage(x, y, nx, ny, 10 * s, L.main ? GOLD : CREAM, p > L.inj, true);
            ctx.globalAlpha = 1;
        });
        // the burst: a flash, the envelope in pieces, the progeny released
        if (bu > 0) {
            var fl = 1 - seg(bu, 0, 0.35);
            if (fl > 0) {
                var gr = ctx.createRadialGradient(ox, oy, 0, ox, oy, rr + bu * 420 * s);
                gr.addColorStop(0, rgba(GOLD, 0.45 * fl)); gr.addColorStop(1, rgba(GOLD, 0));
                ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(ox, oy, rr + bu * 420 * s, 0, 6.283); ctx.fill();
            }
            shards.forEach(function (q) {
                var d = out(bu) * 260 * s * q.s;
                ctx.beginPath();
                ctx.arc(ox + Math.cos(q.a) * (rr + d) - Math.cos(q.a) * 40 * s, oy + Math.sin(q.a) * (rr + d) - Math.sin(q.a) * 40 * s, 40 * s, q.a - q.len, q.a + q.len);
                ctx.lineWidth = 4 * s; ctx.strokeStyle = rgba(CORAL, 0.85 * (1 - seg(bu, 0.2, 1))); ctx.stroke();
            });
            prog.forEach(function (g) {
                var start = [g.fx * rr * 0.6, g.fy * rr * 0.6], dd = out(bu) * g.dist * 290 * s;
                var px = ox + start[0] + Math.cos(g.dir) * dd + Math.sin(t * 0.6 + g.spin) * 10 * U * bu;
                var py = oy + start[1] + Math.sin(g.dir) * dd + Math.cos(t * 0.5 + g.spin) * 10 * U * bu;
                var a2 = g.spin + bu * 4 + t * 0.2;
                phage(px, py, Math.cos(a2), Math.sin(a2), 7.5 * s, mix(GOLD, CREAM, seg(bu, 0.5, 1)), false, bu < 0.7);
            });
        }
        ctx.restore();
        // the eyepiece rim, until it has opened past the screen
        var rimA = 1 - seg(p, 0.05, 0.08);
        if (rimA > 0) {
            ctx.lineWidth = 2; ctx.strokeStyle = rgba(GOLD, 0.5 * rimA);
            ctx.beginPath(); ctx.arc(cx, cy, R + 6, 0, 6.283); ctx.stroke();
            ctx.lineWidth = 1; ctx.strokeStyle = rgba(GOLD, 0.35 * rimA);
            for (var tk = 0; tk < 72; tk++) {
                var an = tk / 72 * 6.283, l1 = tk % 6 ? 6 : 12;
                ctx.beginPath(); ctx.moveTo(cx + Math.cos(an) * (R - l1), cy + Math.sin(an) * (R - l1)); ctx.lineTo(cx + Math.cos(an) * R, cy + Math.sin(an) * R); ctx.stroke();
            }
        }
    }

    /* ---------- captions, clock, progress ---------- */
    var CLOCK = [[0.08, 0], [0.18, 2], [0.30, 20], [0.44, 60], [0.60, 150], [0.74, 176], [0.86, 182], [1, 185]];
    function minutes(p) {
        if (p <= CLOCK[0][0]) return 0;
        for (var k = 1; k < CLOCK.length; k++) if (p <= CLOCK[k][0]) return lerp(CLOCK[k - 1][1], CLOCK[k][1], (p - CLOCK[k - 1][0]) / (CLOCK[k][0] - CLOCK[k - 1][0]));
        return 185;
    }
    var lastBeat = -1;
    function chrome(p) {
        var cur = 0;
        AT.forEach(function (a, k) { if (p >= a) cur = k; });
        if (cur !== lastBeat) {
            beats.forEach(function (b, k) { b.classList.toggle('on', k === cur); b.classList.toggle('past', k < cur); });
            lastBeat = cur;
        }
        var m = Math.round(minutes(p));
        if (clock) clock.textContent = Math.floor(m / 60) + ':' + ('0' + (m % 60)).slice(-2) + ' after infection';
        if (bar) bar.style.transform = 'scaleX(' + p.toFixed(4) + ')';
    }

    /* ---------- run ---------- */
    size();
    if (reduce) {
        sec.classList.add('dive-static');
        size(); draw(0.66, 0); beats.forEach(function (b) { b.classList.add('on'); });
        window.addEventListener('resize', function () { size(); draw(0.66, 0); });
        return;
    }
    var pS = 0, running = false, t0 = performance.now();
    function progress() {
        var b = sec.getBoundingClientRect(), span = b.height - window.innerHeight;
        return span > 0 ? clamp(-b.top / span) : 0;
    }
    function frame(now) {
        if (!running) return;
        var p = progress();
        pS += (p - pS) * 0.14;
        if (Math.abs(p - pS) < 0.0005) pS = p;
        draw(pS, (now - t0) / 1000);
        chrome(pS);
        requestAnimationFrame(frame);
    }
    new IntersectionObserver(function (es) {
        var on = es[0].isIntersecting && !document.hidden;
        if (on && !running) { running = true; pS = progress(); requestAnimationFrame(frame); }
        else if (!on) running = false;
    }).observe(sec);
    document.addEventListener('visibilitychange', function () { if (document.hidden) running = false; });
    window.addEventListener('resize', function () { size(); });
    draw(0, 0); chrome(0);
    // a caption's link scrolls into view when focused from the keyboard
    beats.forEach(function (b) {
        b.addEventListener('focusin', function () {
            var at = +b.getAttribute('data-at'), top = sec.offsetTop + at * (sec.offsetHeight - window.innerHeight) + 4;
            window.scrollTo(0, top);
        });
    });
})();
