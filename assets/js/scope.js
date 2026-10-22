/* scope.js — the hero's live "microscope": phage N4 infecting E. coli in darkfield.
 *
 * A small agent simulation drawn on a canvas in a 1000 × 1000 world:
 *   cells   grow and divide; an adsorbed phage injects (its capsid goes hollow),
 *           progeny build up inside, the infected rod elongates; every further
 *           phage that injects during infection delays lysis and adds progeny
 *           (lysis inhibition, flashed "LIN"); at lysis the rod contracts from
 *           the poles into a sphere and bursts, releasing its progeny.
 *   phages  drift by Brownian motion and adsorb where they touch a cell.
 * Click or tap the field (or press "Add phages") to release more. Paused when
 * off screen; prefers-reduced-motion gets one still frame, advanced on click.
 * Not to scale: the particles are drawn far larger than real N4 virions.
 */
(function () {
    var host = document.getElementById('heroScope');
    if (!host) return;
    var canvas = host.querySelector('.scope-canvas');
    var ctx = canvas.getContext('2d');
    var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    var W = 1000, C = 500, EDGE = 470;
    var R0 = 32, MAXCELLS = 9, MAXPHAGE = 75;
    var cells = [], phages = [], fx = [], dust = [];
    var stats = { inf: 0, lys: 0, rel: 0 }, now = 0, nextSpawn = 0;
    var mouse = null;
    function rnd(a, b) { return a + Math.random() * (b - a); }
    function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
    function ease(x) { return x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2; }

    /* ---------- cells ---------- */
    function cell(x, y, L, a) {
        var c = { x: x, y: y, a: a == null ? rnd(0, Math.PI) : a, L: L || rnd(70, 120), r: R0,
            vx: rnd(-0.1, 0.1), vy: rnd(-0.1, 0.1), va: rnd(-0.002, 0.002), born: now, inf: null,
            bound: 0, dots: [] };
        for (var i = 0; i < 40; i++) c.dots.push([rnd(-1, 1), rnd(-0.6, 0.6)]);
        cells.push(c);
        return c;
    }
    function half(c) {
        // straight half-length, shrinking to 0 as an infected cell rounds up
        var L = c.L;
        if (c.inf) L *= 1 + 0.28 * c.inf.prog;
        return Math.max(0, L / 2 * (1 - (c.round || 0)));
    }
    function rad(c) { return c.r * (1 + 0.32 * (c.round || 0)); }
    function local(c, px, py) {
        var dx = px - c.x, dy = py - c.y, ca = Math.cos(c.a), sa = Math.sin(c.a);
        return [dx * ca + dy * sa, -dx * sa + dy * ca];
    }
    function world(c, lx, ly) {
        var ca = Math.cos(c.a), sa = Math.sin(c.a);
        return [c.x + lx * ca - ly * sa, c.y + lx * sa + ly * ca];
    }
    function segDist(c, px, py) {
        var l = local(c, px, py), h = half(c), qx = clamp(l[0], -h, h);
        return Math.hypot(l[0] - qx, l[1]);
    }
    // a point on the surface: fraction along the axis (-1..1) and an outward angle (local frame)
    function surface(c, f, th, off) {
        var h = half(c), r = rad(c) + (off || 0);
        var p = world(c, f * h + Math.cos(th) * r, Math.sin(th) * r);
        var n = [Math.cos(th + c.a), Math.sin(th + c.a)];
        return { x: p[0], y: p[1], nx: n[0], ny: n[1] };
    }

    /* ---------- phages ---------- */
    function phage(x, y, vx, vy, gold) {
        if (phages.length >= MAXPHAGE) {
            // retire the oldest free particle to keep the field readable
            for (var i = 0; i < phages.length; i++) if (phages[i].st === 'free' && !phages[i].die) { phages[i].die = now; break; }
        }
        var p = { x: x, y: y, vx: vx || 0, vy: vy || 0, a: rnd(0, 6.28), st: 'free', born: now, gold: gold ? now : 0, life: rnd(16, 30) };
        phages.push(p);
        return p;
    }
    function adsorb(p, c) {
        var l = local(c, p.x, p.y), h = half(c), qx = clamp(l[0], -h, h);
        p.st = 'bound'; p.c = c; p.f = h ? qx / h : 0; p.th = Math.atan2(l[1], l[0] - qx); p.inj = now + 0.9;
        c.bound++;
    }
    function inject(p) {
        var c = p.c; p.st = 'empty';
        if (!c.inf) {
            c.inf = { t0: now, end: now + rnd(6.5, 9), burst: 22, prog: 0, lin: 0, flash: 0 };
            stats.inf++;
        } else if (!c.round && now - c.inf.t0 > 0.8 && c.inf.end < c.inf.t0 + 16) {
            // superinfection during infection: lysis inhibition (capped, so cells still burst)
            c.inf.end = Math.min(c.inf.t0 + 16, c.inf.end + 2.4);
            c.inf.burst = Math.min(40, c.inf.burst + 5);
            c.inf.lin++; c.inf.flash = now;
        }
    }

    function burst(c) {
        var h = half(c), r = rad(c), n = c.inf.burst;
        for (var i = 0; i < n; i++) {
            var a = rnd(0, 6.283), s = rnd(1.6, 4.2), d = rnd(0, r * 0.7);
            phage(c.x + Math.cos(a) * d, c.y + Math.sin(a) * d, Math.cos(a) * s, Math.sin(a) * s, true);
        }
        stats.rel += n; stats.lys++;
        fx.push({ k: 'flash', x: c.x, y: c.y, t: now, r: r });
        for (i = 0; i < 12; i++) {
            var a0 = i / 12 * 6.283 + rnd(-0.2, 0.2);
            fx.push({ k: 'shard', x: c.x + Math.cos(a0) * r, y: c.y + Math.sin(a0) * r, a: a0, s: rnd(1.2, 2.6), t: now, len: rnd(0.25, 0.5) });
        }
        phages.forEach(function (p) {
            if (p.c === c) { p.st = 'ghost'; p.ghost = now; var s = surface(c, p.f, p.th, 18); p.x = s.x; p.y = s.y; p.vx = s.nx * 1.6; p.vy = s.ny * 1.6; p.c = null; }
        });
        cells.splice(cells.indexOf(c), 1);
    }

    /* ---------- step ---------- */
    function step(dt) {
        now += dt;
        var k = dt * 60, i, j, c, p;
        // cells: drift, keep apart, stay in the field, grow, divide, infect, lyse
        for (i = cells.length - 1; i >= 0; i--) {
            c = cells[i];
            c.vx += rnd(-0.01, 0.01) * k; c.vy += rnd(-0.01, 0.01) * k;
            c.vx *= Math.pow(0.985, k); c.vy *= Math.pow(0.985, k);
            var dc = Math.hypot(c.x - C, c.y - C), lim = EDGE - 70 - half(c);
            if (dc > lim) { c.vx -= (c.x - C) / dc * 0.04 * k; c.vy -= (c.y - C) / dc * 0.04 * k; }
            c.x += c.vx * k; c.y += c.vy * k; c.a += c.va * k;
            if (!c.inf) {
                c.L += 2.6 * dt;
                if (c.L > 150 && cells.length < MAXCELLS && !c.bound) {
                    var ca = Math.cos(c.a), sa = Math.sin(c.a), Ld = c.L / 2 - c.r, o = Ld / 2 + c.r + 2;
                    cells.splice(i, 1);
                    var d1 = cell(c.x - ca * o, c.y - sa * o, Ld, c.a), d2 = cell(c.x + ca * o, c.y + sa * o, Ld, c.a);
                    d1.vx = -ca * 0.25; d1.vy = -sa * 0.25; d2.vx = ca * 0.25; d2.vy = sa * 0.25;
                    d1.born = d2.born = now - 1;
                    continue;
                }
                c.L = Math.min(c.L, 160);
            } else {
                var I = c.inf;
                I.prog = clamp((now - I.t0) / (I.end - I.t0), 0, 1);
                if (now >= I.end) {
                    c.round = clamp((now - I.end) / 1.3, 0, 1);
                    if (c.round >= 1) { burst(c); continue; }
                }
            }
        }
        for (i = 0; i < cells.length; i++) for (j = i + 1; j < cells.length; j++) {
            var a = cells[i], b = cells[j];
            var d = Math.min(segDist(a, b.x, b.y) - rad(a), segDist(b, a.x, a.y) - rad(b));
            var want = Math.max(rad(a), rad(b)) + 8;
            if (d < want) {
                var dx = b.x - a.x, dy = b.y - a.y, m = Math.hypot(dx, dy) || 1, push = (want - d) * 0.012 * k;
                a.vx -= dx / m * push; a.vy -= dy / m * push; b.vx += dx / m * push; b.vy += dy / m * push;
            }
        }
        // phages
        for (i = phages.length - 1; i >= 0; i--) {
            p = phages[i];
            if (p.die && now - p.die > 0.6) { phages.splice(i, 1); continue; }
            if (p.st === 'ghost' && now - p.ghost > 3) { phages.splice(i, 1); continue; }
            // free particles decay, the way titers drop, so the field never silts up
            if (p.st === 'free' && !p.die && now - p.born > p.life) p.die = now;
            if (p.st === 'bound' || p.st === 'empty') {
                if (p.st === 'bound' && now >= p.inj) inject(p);
                continue;
            }
            p.vx += rnd(-0.22, 0.22) * k; p.vy += rnd(-0.22, 0.22) * k;
            if (mouse && p.st === 'free') {
                var mx = mouse.x - p.x, my = mouse.y - p.y, md = Math.hypot(mx, my);
                if (md < 160 && md > 1) { p.vx += mx / md * 0.05 * k; p.vy += my / md * 0.05 * k; }
            }
            var damp = Math.pow(0.93, k); p.vx *= damp; p.vy *= damp;
            p.x += p.vx * k; p.y += p.vy * k; p.a += (p.vx - p.vy) * 0.01 * k;
            var dp = Math.hypot(p.x - C, p.y - C);
            if (dp > EDGE - 10) { var nx = (p.x - C) / dp, ny = (p.y - C) / dp, dot = p.vx * nx + p.vy * ny; if (dot > 0) { p.vx -= 2 * dot * nx; p.vy -= 2 * dot * ny; } p.x = C + nx * (EDGE - 10); p.y = C + ny * (EDGE - 10); }
            if (p.st !== 'free' || p.die || now - p.born < 0.5) continue;
            for (j = 0; j < cells.length; j++) {
                c = cells[j];
                if (c.round || c.bound >= 5) continue;
                if (segDist(c, p.x, p.y) < rad(c) + 10 && Math.random() < (c.inf ? 0.012 : 0.03) * k) { adsorb(p, c); break; }
            }
        }
        for (i = fx.length - 1; i >= 0; i--) if (now - fx[i].t > 1.6) fx.splice(i, 1);
        // keep the culture going
        if (now > nextSpawn) {
            nextSpawn = now + 3;
            var healthy = cells.filter(function (c) { return !c.inf; }).length;
            if (cells.length < 5 || healthy < 3) {
                // a new cell swims in where there is room
                var best = null, bd = -1;
                for (var t = 0; t < 12; t++) {
                    var a2 = rnd(0, 6.283), r2 = rnd(60, 300), x2 = C + Math.cos(a2) * r2, y2 = C + Math.sin(a2) * r2;
                    var dmin = cells.reduce(function (m, c) { return Math.min(m, Math.hypot(c.x - x2, c.y - y2)); }, 1e9);
                    if (dmin > bd) { bd = dmin; best = [x2, y2]; }
                }
                cell(best[0], best[1], rnd(80, 110)).born = now;
            }
            var free = phages.filter(function (p) { return p.st === 'free' && !p.die; }).length;
            if (free < 10) seed(8, null);
        }
    }
    function seed(n, at) {
        for (var i = 0; i < n; i++) {
            if (at) { var a = rnd(0, 6.283), s = rnd(0.6, 2.4); phage(at.x, at.y, Math.cos(a) * s, Math.sin(a) * s, true); }
            else { var b = rnd(0, 6.283), r = rnd(EDGE - 60, EDGE - 20); phage(C + Math.cos(b) * r, C + Math.sin(b) * r, -Math.cos(b) * 1.5, -Math.sin(b) * 1.5); }
        }
    }

    /* ---------- draw ---------- */
    var S = 1, bg = null;
    function size() {
        var css = canvas.clientWidth || 400, dpr = Math.min(2, window.devicePixelRatio || 1);
        canvas.width = Math.round(css * dpr); canvas.height = Math.round(css * dpr);
        S = canvas.width / W;
        bg = null;
    }
    function capsule(h, r) {
        ctx.beginPath();
        ctx.arc(h, 0, r, -Math.PI / 2, Math.PI / 2);
        ctx.arc(-h, 0, r, Math.PI / 2, Math.PI * 1.5);
        ctx.closePath();
    }
    function hexagon(x, y, s, a) {
        ctx.beginPath();
        for (var i = 0; i < 6; i++) { var t = a + i * Math.PI / 3; ctx[i ? 'lineTo' : 'moveTo'](x + Math.cos(t) * s, y + Math.sin(t) * s); }
        ctx.closePath();
    }
    function mix(a, b, t) { return [0, 1, 2].map(function (i) { return Math.round(a[i] + (b[i] - a[i]) * t); }); }
    var CREAM = [245, 237, 216], GOLD = [244, 196, 48], CORAL = [244, 105, 127], GREEN = [63, 191, 110];
    function rgba(c, o) { return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + o.toFixed(3) + ')'; }

    function draw() {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        if (!bg) {
            bg = ctx.createRadialGradient(canvas.width * 0.45, canvas.height * 0.42, 0, canvas.width / 2, canvas.height / 2, canvas.width * 0.6);
            bg.addColorStop(0, '#1a150b'); bg.addColorStop(0.7, '#0d0b06'); bg.addColorStop(1, '#050402');
        }
        ctx.fillStyle = bg; ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.setTransform(S, 0, 0, S, 0, 0);
        // dust in the medium
        ctx.fillStyle = 'rgba(245,237,216,0.10)';
        dust.forEach(function (d) { ctx.fillRect(d[0], d[1], d[2], d[2]); });

        var i, c, p;
        // cells
        for (i = 0; i < cells.length; i++) {
            c = cells[i];
            var h = half(c), r = rad(c), I = c.inf, fade = clamp((now - c.born) / 1.2, 0, 1);
            var tone = I ? mix(CREAM, CORAL, ease(I.prog) * 0.85 + (c.round || 0) * 0.15) : CREAM;
            ctx.save();
            ctx.translate(c.x, c.y); ctx.rotate(c.a);
            ctx.globalAlpha = fade;
            capsule(h, r);
            ctx.fillStyle = rgba(tone, 0.06 + (I ? 0.05 * I.prog : 0));
            ctx.fill();
            ctx.shadowColor = rgba(I ? tone : GOLD, 0.55);
            ctx.shadowBlur = 16 * S * 2;
            ctx.lineWidth = 4.2;
            ctx.strokeStyle = rgba(tone, 0.88);
            ctx.stroke();
            ctx.shadowBlur = 0;
            // nucleoid, then progeny accumulating inside an infected cell
            ctx.beginPath();
            ctx.ellipse(0, 0, Math.max(6, h * 0.75 + r * 0.25), r * 0.42, 0, 0, 6.283);
            ctx.fillStyle = rgba(GOLD, I ? 0.05 : 0.09);
            ctx.fill();
            if (I) {
                var n = Math.floor(I.burst * clamp((I.prog - 0.15) / 0.85, 0, 1));
                ctx.fillStyle = rgba(GOLD, 0.9);
                for (var k = 0; k < n && k < c.dots.length; k++) {
                    var dd = c.dots[k];
                    hexagon(dd[0] * (h + r * 0.45), dd[1] * r * 0.9, 3.4, 0.3);
                    ctx.fill();
                }
                if (I.flash && now - I.flash < 1.4) {
                    var u = (now - I.flash) / 1.4;
                    capsule(h, r + 8 + u * 26);
                    ctx.lineWidth = 3 * (1 - u);
                    ctx.strokeStyle = rgba(GREEN, 0.9 * (1 - u));
                    ctx.stroke();
                }
            }
            ctx.restore();
            if (I && I.flash && now - I.flash < 1.4) {
                ctx.font = '600 26px "JetBrains Mono", monospace';
                ctx.textAlign = 'center';
                ctx.fillStyle = rgba(GREEN, 1 - (now - I.flash) / 1.4);
                ctx.fillText('LIN', c.x, c.y - r - 30 - (now - I.flash) * 14);
            }
        }
        // effects
        fx.forEach(function (f) {
            var u = (now - f.t) / 1.6;
            if (f.k === 'flash') {
                var rr = f.r + u * 220, g = ctx.createRadialGradient(f.x, f.y, 0, f.x, f.y, rr);
                g.addColorStop(0, rgba(GOLD, 0.35 * (1 - u))); g.addColorStop(1, rgba(GOLD, 0));
                ctx.fillStyle = g; ctx.beginPath(); ctx.arc(f.x, f.y, rr, 0, 6.283); ctx.fill();
            } else {
                var d = u * 90 * f.s;
                ctx.beginPath();
                ctx.arc(f.x + Math.cos(f.a) * d - Math.cos(f.a) * 30, f.y + Math.sin(f.a) * d - Math.sin(f.a) * 30, 30, f.a - f.len, f.a + f.len);
                ctx.lineWidth = 3.5; ctx.strokeStyle = rgba(CORAL, 0.8 * (1 - u)); ctx.stroke();
            }
        });
        // phages: a hexagonal head on a short tail (N4 is a podovirus)
        for (i = 0; i < phages.length; i++) {
            p = phages[i];
            var x, y, nx, ny, o = 1;
            if (p.st === 'bound' || p.st === 'empty') {
                var s = surface(p.c, p.f, p.th, 0); x = s.x; y = s.y; nx = s.nx; ny = s.ny;
            } else {
                x = p.x; y = p.y; nx = Math.cos(p.a); ny = Math.sin(p.a);
                x -= nx * 14; y -= ny * 14;
            }
            if (p.die) o = 1 - clamp((now - p.die) / 0.6, 0, 1);
            if (p.st === 'ghost') o = 0.55 * (1 - clamp((now - p.ghost) / 3, 0, 1));
            if (p.st === 'free') o *= clamp((now - p.born) / 0.4, 0.2, 1);
            var hx = x + nx * 17, hy = y + ny * 17, tone2 = p.gold ? mix(GOLD, CREAM, clamp((now - p.gold) / 2.5, 0, 1)) : CREAM;
            ctx.globalAlpha = o;
            ctx.lineWidth = 3;
            ctx.strokeStyle = rgba(tone2, 0.95);
            ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + nx * 9, y + ny * 9); ctx.stroke();
            hexagon(hx, hy, 9, Math.atan2(ny, nx));
            if (p.st === 'empty' || p.st === 'ghost') {
                ctx.lineWidth = 2.2; ctx.stroke();
            } else {
                ctx.shadowColor = rgba(tone2, 0.8); ctx.shadowBlur = 10 * S * 2;
                ctx.fillStyle = rgba(tone2, 0.98); ctx.fill();
                ctx.shadowBlur = 0;
            }
            ctx.globalAlpha = 1;
        }
        // the pointer's reticle
        if (mouse) {
            ctx.strokeStyle = rgba(GOLD, 0.7); ctx.lineWidth = 2;
            ctx.beginPath(); ctx.arc(mouse.x, mouse.y, 34, 0, 6.283); ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(mouse.x - 50, mouse.y); ctx.lineTo(mouse.x - 20, mouse.y);
            ctx.moveTo(mouse.x + 20, mouse.y); ctx.lineTo(mouse.x + 50, mouse.y);
            ctx.moveTo(mouse.x, mouse.y - 50); ctx.lineTo(mouse.x, mouse.y - 20);
            ctx.moveTo(mouse.x, mouse.y + 20); ctx.lineTo(mouse.x, mouse.y + 50);
            ctx.stroke();
        }
    }

    /* ---------- HUD ---------- */
    var hud = {};
    host.querySelectorAll('[data-k]').forEach(function (el) { hud[el.getAttribute('data-k')] = el; });
    var lastHud = 0;
    function updateHud() {
        if (hud.inf) hud.inf.textContent = cells.filter(function (c) { return c.inf; }).length;
        if (hud.lys) hud.lys.textContent = stats.lys;
        if (hud.rel) hud.rel.textContent = stats.rel;
        if (hud.lin) hud.lin.textContent = cells.reduce(function (s, c) { return s + (c.inf ? c.inf.lin : 0); }, 0);
    }

    /* ---------- setup ---------- */
    for (var d = 0; d < 70; d++) { var a = rnd(0, 6.283), r = Math.sqrt(Math.random()) * EDGE; dust.push([C + Math.cos(a) * r, C + Math.sin(a) * r, rnd(1.5, 3.5)]); }
    [[-170, -120, 120, 0.4], [130, -190, 95, 2.2], [190, 90, 135, 1.2], [-120, 170, 100, 2.8], [-260, 40, 80, 1.7], [30, 40, 110, 0.1]]
        .forEach(function (s) { var c = cell(C + s[0], C + s[1], s[2], s[3]); c.born = -2; });
    // one cell already well into infection, so the first burst comes within seconds
    (function () {
        var c = cells[5]; c.inf = { t0: -14, end: 2.6, burst: 30, prog: 0, lin: 1, flash: 0 };
        for (var i = 0; i < 2; i++) { var p = phage(c.x, c.y); adsorb(p, c); p.st = 'empty'; p.th = i ? -1.4 : 1.6; p.f = i ? 0.3 : -0.5; }
        stats.inf = 1;
    })();
    seed(26, null);
    phages.forEach(function (p) { if (p.st === 'free') { var a = rnd(0, 6.283), r = rnd(0, EDGE - 40); p.x = C + Math.cos(a) * r; p.y = C + Math.sin(a) * r; p.born = -1; } });

    // reticle ticks around the rim
    var ticks = host.querySelector('.scope-ticks');
    if (ticks) for (var t = 0; t < 72; t++) {
        var ang = t / 72 * 6.283, long = t % 6 === 0, r1 = long ? 90 : 94;
        var ln = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        ln.setAttribute('x1', (100 + Math.cos(ang) * r1).toFixed(2)); ln.setAttribute('y1', (100 + Math.sin(ang) * r1).toFixed(2));
        ln.setAttribute('x2', (100 + Math.cos(ang) * 98).toFixed(2)); ln.setAttribute('y2', (100 + Math.sin(ang) * 98).toFixed(2));
        ticks.appendChild(ln);
    }
    size();
    window.addEventListener('resize', function () { size(); draw(); });

    var running = false, visible = true, last = 0;
    function frame(t) {
        if (!running) return;
        var dt = Math.min(0.05, (t - last) / 1000 || 0.016);
        last = t;
        step(dt);
        draw();
        if (t - lastHud > 250) { updateHud(); lastHud = t; }
        requestAnimationFrame(frame);
    }
    function setRun() {
        var go = visible && !document.hidden && !reduce;
        if (go && !running) { running = true; last = performance.now(); requestAnimationFrame(frame); }
        else if (!go) running = false;
    }
    if (reduce) {
        for (var s = 0; s < 360; s++) step(1 / 60);
        draw(); updateHud();
    } else {
        draw();
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (es) { visible = es[0].isIntersecting; setRun(); }).observe(host);
        }
        document.addEventListener('visibilitychange', setRun);
        setRun();
    }

    /* ---------- interaction ---------- */
    var field = host.querySelector('.scope-field');
    function toWorld(e) {
        var b = canvas.getBoundingClientRect();
        return { x: (e.clientX - b.left) / b.width * W, y: (e.clientY - b.top) / b.height * W };
    }
    field.addEventListener('pointermove', function (e) { if (e.pointerType === 'mouse') { mouse = toWorld(e); if (reduce) draw(); } });
    field.addEventListener('pointerleave', function () { mouse = null; if (reduce) draw(); });
    field.addEventListener('click', function (e) {
        var w = toWorld(e);
        if (Math.hypot(w.x - C, w.y - C) > EDGE) return;
        seed(7, w);
        if (reduce) { for (var s = 0; s < 120; s++) step(1 / 60); draw(); updateHud(); }
    });
    var add = host.querySelector('.scope-add');
    if (add) add.addEventListener('click', function () {
        seed(8, { x: C + rnd(-150, 150), y: C + rnd(-150, 150) });
        if (reduce) { for (var s = 0; s < 120; s++) step(1 / 60); draw(); updateHud(); }
    });

    // the instrument tilts a little toward the pointer
    var hero = document.getElementById('hero');
    if (hero && !reduce && matchMedia('(hover: hover)').matches) {
        hero.addEventListener('pointermove', function (e) {
            var b = hero.getBoundingClientRect();
            host.style.setProperty('--tx', ((e.clientX - b.left) / b.width - 0.5).toFixed(3));
            host.style.setProperty('--ty', ((e.clientY - b.top) / b.height - 0.5).toFixed(3));
        });
        hero.addEventListener('pointerleave', function () { host.style.setProperty('--tx', 0); host.style.setProperty('--ty', 0); });
    }
})();
