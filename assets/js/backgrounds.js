/* ==============================================================
   HERO CANVAS — Floating microbiology zoo
   Phages, bacteria (rods + cocci), plasmids, DNA helices, ribosomes.
   Density and palette tuned for ambient (low-distraction) presence.
=============================================================== */
(function() {
    const canvas = document.getElementById('heroCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let w, h;

    function resize() {
        w = canvas.width = canvas.offsetWidth;
        h = canvas.height = canvas.offsetHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    const PALETTE = ['244, 196, 48', '26, 128, 64', '196, 30, 58'];
    const pickColor = (op) => `rgba(${PALETTE[Math.floor(Math.random() * PALETTE.length * 0.62)]}, ${op})`;

    class Organism {
        constructor(kind) {
            this.kind = kind;
            this.reset();
        }
        reset() {
            this.x = Math.random() * w;
            this.y = Math.random() * h;
            this.size = 12 + Math.random() * 22;
            this.speed = 0.07 + Math.random() * 0.28;
            this.angle = Math.random() * Math.PI * 2;
            this.rotSpeed = (Math.random() - 0.5) * 0.006;
            this.rotation = Math.random() * Math.PI * 2;
            this.opacity = 0.10 + Math.random() * 0.22;
            this.color = pickColor(this.opacity);
            this.strokeWidth = 1 + Math.random() * 0.5;
            this.drift = Math.random() * Math.PI * 2;
            this.driftSpeed = 0.002 + Math.random() * 0.003;
            this.pulse = Math.random() * Math.PI * 2;
        }
        update() {
            this.drift += this.driftSpeed;
            this.pulse += 0.02;
            this.x += Math.cos(this.angle) * this.speed + Math.sin(this.drift) * 0.18;
            this.y += Math.sin(this.angle) * this.speed + Math.cos(this.drift) * 0.14;
            this.rotation += this.rotSpeed;
            const m = 80;
            if (this.x < -m) this.x = w + m;
            if (this.x > w + m) this.x = -m;
            if (this.y < -m) this.y = h + m;
            if (this.y > m + h) this.y = -m;
        }
        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);
            ctx.strokeStyle = this.color;
            ctx.fillStyle = this.color;
            ctx.lineWidth = this.strokeWidth;
            switch (this.kind) {
                case 'phage':    this.drawPhage();    break;
                case 'rod':      this.drawRod();      break;
                case 'coccus':   this.drawCoccus();   break;
                case 'plasmid':  this.drawPlasmid();  break;
                case 'helix':    this.drawHelix();    break;
                case 'ribosome': this.drawRibosome(); break;
            }
            ctx.restore();
        }
        // Bacteriophage, drawn as a podovirus (icosahedral capsid, short tail, fibres)
        drawPhage() {
            const s = this.size;
            ctx.beginPath();
            for (let i = 0; i < 6; i++) {
                const a = (Math.PI * 2 / 6) * i - Math.PI / 2;
                const px = Math.cos(a) * s * 0.5;
                const py = Math.sin(a) * s * 0.5;
                i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
            }
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            // N4 is a podovirus: a short, stubby, non-contractile tail and no
            // baseplate. The tail is a fraction of the capsid, not its equal.
            const lw = ctx.lineWidth;
            ctx.lineWidth = lw * 2.4;
            ctx.beginPath();
            ctx.moveTo(0, s * 0.5);
            ctx.lineTo(0, s * 0.72);
            ctx.stroke();
            ctx.lineWidth = lw;
            const fy = s * 0.72;
            for (let i = -1; i <= 1; i += 2) {
                ctx.beginPath();
                ctx.moveTo(0, fy);
                ctx.quadraticCurveTo(i * s * 0.16, fy + s * 0.12, i * s * 0.26, fy + s * 0.26);
                ctx.stroke();
            }
        }
        // Rod-shaped bacterium (E. coli-like)
        drawRod() {
            const len = this.size * 1.8;
            const rad = this.size * 0.42;
            ctx.beginPath();
            ctx.moveTo(-len/2 + rad, -rad);
            ctx.lineTo(len/2 - rad, -rad);
            ctx.arc(len/2 - rad, 0, rad, -Math.PI/2, Math.PI/2);
            ctx.lineTo(-len/2 + rad, rad);
            ctx.arc(-len/2 + rad, 0, rad, Math.PI/2, Math.PI*1.5);
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            // membrane highlight
            ctx.beginPath();
            ctx.moveTo(-len/2 + rad, -rad * 0.6);
            ctx.lineTo(len/2 - rad, -rad * 0.6);
            ctx.strokeStyle = `rgba(245, 237, 216, ${this.opacity * 0.5})`;
            ctx.stroke();
        }
        // Coccus (spherical cell, possibly diplo- or tetra-)
        drawCoccus() {
            const r = this.size * 0.55;
            const pulse = 1 + Math.sin(this.pulse) * 0.04;
            ctx.beginPath();
            ctx.arc(-r * 0.7, 0, r * pulse, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(r * 0.7, 0, r * pulse, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
        }
        // Plasmid (closed circular DNA loop)
        drawPlasmid() {
            const r = this.size * 0.6;
            ctx.beginPath();
            // wavy circle to suggest supercoiled DNA
            const segments = 36;
            for (let i = 0; i <= segments; i++) {
                const t = (i / segments) * Math.PI * 2;
                const wob = Math.sin(t * 3 + this.pulse) * 1.4;
                const x = Math.cos(t) * (r + wob);
                const y = Math.sin(t) * (r + wob);
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.stroke();
            // inner loop (supercoiled twist)
            ctx.beginPath();
            ctx.arc(0, 0, r * 0.55, 0, Math.PI * 1.4);
            ctx.stroke();
        }
        // DNA double helix segment
        drawHelix() {
            const len = this.size * 2.6;
            const amp = this.size * 0.3;
            const segments = 26;
            // Strand A
            ctx.beginPath();
            for (let i = 0; i <= segments; i++) {
                const t = i / segments;
                const x = -len/2 + t * len;
                const y = Math.sin(t * Math.PI * 3) * amp;
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            }
            ctx.stroke();
            // Strand B (phase-shifted)
            ctx.beginPath();
            for (let i = 0; i <= segments; i++) {
                const t = i / segments;
                const x = -len/2 + t * len;
                const y = Math.sin(t * Math.PI * 3 + Math.PI) * amp;
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            }
            ctx.stroke();
            // base-pair rungs (every few segments)
            for (let i = 2; i < segments; i += 4) {
                const t = i / segments;
                const x = -len/2 + t * len;
                const y1 = Math.sin(t * Math.PI * 3) * amp;
                const y2 = Math.sin(t * Math.PI * 3 + Math.PI) * amp;
                ctx.beginPath();
                ctx.moveTo(x, y1);
                ctx.lineTo(x, y2);
                ctx.stroke();
            }
        }
        // Ribosome (two-subunit blob)
        drawRibosome() {
            const r1 = this.size * 0.55;
            const r2 = this.size * 0.40;
            ctx.beginPath();
            ctx.arc(0, -r2 * 0.4, r1, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(0, r1 * 0.6, r2, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // Build organism mix — scale by viewport area so big screens
    // don't pay 50-organism redraw cost just because they have pixels.
    const viewportArea = innerWidth * innerHeight;
    const densityMult = viewportArea > 1600 * 1000
        ? 0.7  // 1080p+ desktops: lighter, big canvas already feels full
        : viewportArea > 1100 * 700
            ? 1.0
            : 0.85; // small screens
    const recipe = [
        ['phage', Math.round(14 * densityMult)],
        ['rod', Math.round(7 * densityMult)],
        ['coccus', Math.round(6 * densityMult)],
        ['plasmid', Math.round(5 * densityMult)],
        ['helix', Math.round(4 * densityMult)],
        ['ribosome', Math.round(7 * densityMult)]
    ];
    const organisms = [];
    recipe.forEach(([kind, n]) => {
        for (let i = 0; i < n; i++) organisms.push(new Organism(kind));
    });

    let visible = true, looping = false;
    function tick() {
        if (!visible || reduceMotion) { looping = false; return; }
        ctx.clearRect(0, 0, w, h);
        organisms.forEach(o => { o.update(); o.draw(); });
        requestAnimationFrame(tick);
    }
    function startLoop() { if (!looping && visible && !reduceMotion) { looping = true; tick(); } }
    const io = new IntersectionObserver(es => {
        es.forEach(e => { visible = e.isIntersecting; if (visible) startLoop(); });
    }, { threshold: 0 });
    io.observe(canvas);
    // Draw one static frame so it's not blank before loop starts
    ctx.clearRect(0, 0, w, h);
    organisms.forEach(o => o.draw());
    startLoop();
})();

/* ==============================================================
   AMBIENT MICROBIOLOGY LAYER (background canvas, full page)
   Very low-density drift to make the whole site feel "alive".
=============================================================== */
(function() {
    const canvas = document.getElementById('ambientCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) return;
    let w, h, dpr;
    // Render at a *lower* internal resolution than the screen DPR.
    // Ambient is background fluff — full-res redraws are wasted GPU.
    function resize() {
        const realDpr = devicePixelRatio || 1;
        // 0.6x of physical pixels still looks fine for soft shapes
        dpr = Math.min(realDpr, 1) * 0.65;
        w = canvas.offsetWidth;
        h = canvas.offsetHeight;
        canvas.width = Math.max(1, Math.round(w * dpr));
        canvas.height = Math.max(1, Math.round(h * dpr));
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    window.addEventListener('resize', resize);
    resize();

    const PALETTE = ['244, 196, 48', '26, 128, 64', '196, 30, 58'];
    const drifters = [];
    const KINDS = ['phage', 'rod', 'plasmid', 'helix', 'coccus'];
    const ambientCount = innerWidth * innerHeight > 1600 * 1000 ? 28 : 38;
    for (let i = 0; i < ambientCount; i++) {
        drifters.push({
            kind: KINDS[Math.floor(Math.random() * KINDS.length)],
            x: Math.random() * w,
            y: Math.random() * h,
            vx: (Math.random() - 0.5) * 0.05,
            vy: (Math.random() - 0.5) * 0.05,
            rot: Math.random() * Math.PI * 2,
            rotSpeed: (Math.random() - 0.5) * 0.002,
            size: 10 + Math.random() * 16,
            opacity: 0.035 + Math.random() * 0.06,
            color: PALETTE[Math.floor(Math.random() * PALETTE.length * 0.7)]
        });
    }

    function drawShape(d) {
        ctx.save();
        ctx.translate(d.x, d.y);
        ctx.rotate(d.rot);
        ctx.strokeStyle = `rgba(${d.color}, ${d.opacity})`;
        ctx.fillStyle = `rgba(${d.color}, ${d.opacity * 0.45})`;
        ctx.lineWidth = 1;
        const s = d.size;
        switch (d.kind) {
            case 'phage':
                ctx.beginPath();
                for (let i = 0; i < 6; i++) {
                    const a = (Math.PI * 2 / 6) * i - Math.PI / 2;
                    const px = Math.cos(a) * s * 0.5;
                    const py = Math.sin(a) * s * 0.5;
                    i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
                }
                ctx.closePath();
                ctx.fill(); ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(0, s * 0.5); ctx.lineTo(0, s * 1.25);
                ctx.stroke();
                break;
            case 'rod':
                const len = s * 1.6, rad = s * 0.38;
                ctx.beginPath();
                ctx.moveTo(-len/2 + rad, -rad);
                ctx.lineTo(len/2 - rad, -rad);
                ctx.arc(len/2 - rad, 0, rad, -Math.PI/2, Math.PI/2);
                ctx.lineTo(-len/2 + rad, rad);
                ctx.arc(-len/2 + rad, 0, rad, Math.PI/2, Math.PI*1.5);
                ctx.closePath();
                ctx.fill(); ctx.stroke();
                break;
            case 'plasmid':
                ctx.beginPath();
                ctx.arc(0, 0, s * 0.55, 0, Math.PI * 2);
                ctx.stroke();
                break;
            case 'helix':
                ctx.beginPath();
                for (let i = 0; i <= 20; i++) {
                    const t = i / 20;
                    const x = -s + t * 2 * s;
                    const y = Math.sin(t * Math.PI * 3) * s * 0.25;
                    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
                }
                ctx.stroke();
                ctx.beginPath();
                for (let i = 0; i <= 20; i++) {
                    const t = i / 20;
                    const x = -s + t * 2 * s;
                    const y = Math.sin(t * Math.PI * 3 + Math.PI) * s * 0.25;
                    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
                }
                ctx.stroke();
                break;
            case 'coccus':
                ctx.beginPath();
                ctx.arc(0, 0, s * 0.5, 0, Math.PI * 2);
                ctx.fill(); ctx.stroke();
                break;
        }
        ctx.restore();
    }

    // Cursor-aware: drifters get gentle attraction toward the cursor when nearby
    // Stored in viewport coords (canvas is position:fixed)
    const cursor = { x: -9999, y: -9999, active: false };
    document.addEventListener('mousemove', (e) => {
        if (matchMedia('(hover: none)').matches) return;
        cursor.x = e.clientX;
        cursor.y = e.clientY;
        cursor.active = true;
    }, { passive: true });
    document.addEventListener('mouseleave', () => { cursor.active = false; });

    // Throttle to ~30fps — background ambience doesn't need 60fps
    const FRAME_MS = 1000 / 30;
    let lastFrame = 0;
    function tick(t) {
        if (!running) return;
        if (t - lastFrame >= FRAME_MS) {
            lastFrame = t;
            ctx.clearRect(0, 0, w, h);
            for (let i = 0; i < drifters.length; i++) {
                const d = drifters[i];
                if (cursor.active) {
                    const dx = cursor.x - d.x;
                    const dy = cursor.y - d.y;
                    const dist2 = dx * dx + dy * dy;
                    if (dist2 < 25600 && dist2 > 0) {
                        const dist = Math.sqrt(dist2);
                        d.vx += (dx / dist) * 0.0035;
                        d.vy += (dy / dist) * 0.0035;
                    }
                }
                d.vx *= 0.997;
                d.vy *= 0.997;
                d.x += d.vx;
                d.y += d.vy;
                d.rot += d.rotSpeed;
                if (d.x < -50) d.x = w + 50;
                if (d.x > w + 50) d.x = -50;
                if (d.y < -50) d.y = h + 50;
                if (d.y > h + 50) d.y = -50;
                drawShape(d);
            }
        }
        requestAnimationFrame(tick);
    }

    // Pause when tab hidden or user prefers reduced motion already handled above
    let running = true;
    document.addEventListener('visibilitychange', () => {
        const shouldRun = !document.hidden;
        if (shouldRun && !running) { running = true; requestAnimationFrame(tick); }
        else { running = shouldRun; }
    });
    // Viewport-fixed: just resize on viewport change, no doc-height tracking
    window.addEventListener('resize', resize);
    requestAnimationFrame(tick);
})();


/* ==============================================================
   CULTURAL BACKGROUND CANVAS  v5
   Left  → Japanese/Saitama : Mountain range (erupting volcano + clouds), torii, Hokusai waves, blossoms
   Right → Ghanaian/Accra+Kumasi : Cape Coast Castle, Accra skyline, stadium,
           coastal waves, Adinkra, palm, football silhouette
   Both  → Floating bacteriophage particles (researcher's mark)
=============================================================== */
(function () {
    const canvas = document.getElementById('culturalBgCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const isMobile = matchMedia('(hover: none) and (pointer: coarse)').matches;
    const PM = isMobile ? 0.5 : 1.0;
    const FRAME_MS = 1000 / 20;
    let w, h, jPhase = 0, gPhase = 0;
    let petals = [], phages = [];
    let lastFrame = 0, raf;

    /* ─── Catmull-Rom spline through ridge points ─── */
    function mountainSpline(pts) {
        ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 0; i < pts.length - 1; i++) {
            const p0 = pts[Math.max(0, i - 1)];
            const p1 = pts[i];
            const p2 = pts[i + 1];
            const p3 = pts[Math.min(pts.length - 1, i + 2)];
            const cp1x = p1.x + (p2.x - p0.x) / 6;
            const cp1y = p1.y + (p2.y - p0.y) / 6;
            const cp2x = p2.x - (p3.x - p1.x) / 6;
            const cp2y = p2.y - (p3.y - p1.y) / 6;
            ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
        }
    }

    function mountainLayer(pts, baseY, topRgba, midRgba) {
        const topY = Math.min(...pts.map(p => p.y));
        const grd = ctx.createLinearGradient(0, topY, 0, baseY);
        grd.addColorStop(0,    topRgba);
        grd.addColorStop(0.62, midRgba);
        grd.addColorStop(1,    'rgba(0,0,0,0)');
        ctx.save();
        ctx.fillStyle = grd;
        ctx.beginPath();
        mountainSpline(pts);
        ctx.lineTo(pts[pts.length - 1].x, baseY + 2);
        ctx.lineTo(pts[0].x, baseY + 2);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
    }

    /* ════════════════════════════════════
       MOUNTAIN RANGE — varied peaks, drifting clouds, one erupting volcano
       (lower silhouettes with cloud cover over two atmospheric ridge layers;
        hero peak gets a molten crater, lava flows, and arcing embers)
    ════════════════════════════════════ */
    function fbmRnd(s) { const x = Math.sin(s * 127.1 + 11.3) * 43758.5453; return x - Math.floor(x); }

    function ridgeLayer(seed, crest, amp, segs, col0, col1, baseY) {
        const pts = [], x0 = -0.05, x1 = 0.57;
        for (let i = 0; i <= segs; i++) {
            const t = i / segs;
            const env = Math.pow(Math.sin(t * Math.PI), 0.7);        // taller in the middle
            const jag = 0.40 + 0.60 * fbmRnd(seed + i * 1.7);
            pts.push({ x: w * (x0 + (x1 - x0) * t), y: h * crest - amp * h * env * jag });
        }
        const topY = Math.min(...pts.map(p => p.y));
        const g = ctx.createLinearGradient(0, topY, 0, baseY);
        // flat silhouette tone, fading only near the base for depth
        g.addColorStop(0, col0); g.addColorStop(0.82, col0); g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.save(); ctx.fillStyle = g; ctx.beginPath();
        mountainSpline(pts);
        ctx.lineTo(pts[pts.length - 1].x, baseY + 2);
        ctx.lineTo(pts[0].x, baseY + 2);
        ctx.closePath(); ctx.fill(); ctx.restore();
    }

    function drawMountainRange() {
        const baseY = h * 0.82;
        const t = jPhase;
        const X1 = w * 0.62;                        // the range fills the left / back

        /* night-sky glow behind the range */
        const sgx = w * 0.24, sgy = h * 0.40;
        const sg = ctx.createRadialGradient(sgx, sgy - h * 0.04, 0, sgx, sgy, w * 0.46);
        sg.addColorStop(0,   'rgba(96,104,150,0.12)');
        sg.addColorStop(0.5, 'rgba(54,62,108,0.05)');
        sg.addColorStop(1,   'rgba(22,30,65,0.0)');
        ctx.save(); ctx.fillStyle = sg; ctx.fillRect(0, 0, X1 + w * 0.08, h * 0.74); ctx.restore();

        /* ─── distant, layered mountain range (hazy back → softer front) ─── */
        function rangeLayer(crestF, ampF, segs, seed, fill) {
            const pts = [];
            for (let i = 0; i <= segs; i++) {
                const tt = i / segs;
                const env = 0.45 + 0.55 * Math.pow(Math.sin(tt * Math.PI), 0.6);
                const jag = 0.45 + 0.55 * fbmRnd(seed + i * 1.7);
                pts.push({ x: -w * 0.05 + (X1 + w * 0.10) * tt, y: h * crestF - ampF * h * env * jag });
            }
            const topY = Math.min(...pts.map(p => p.y));
            const g = ctx.createLinearGradient(0, topY, 0, baseY);
            g.addColorStop(0, fill); g.addColorStop(0.85, fill); g.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.save(); ctx.fillStyle = g; ctx.beginPath();
            mountainSpline(pts);
            ctx.lineTo(pts[pts.length - 1].x, baseY + 2);
            ctx.lineTo(pts[0].x, baseY + 2);
            ctx.closePath(); ctx.fill(); ctx.restore();
        }
        rangeLayer(0.58,  0.13, 9,  3.1,  'rgba(60,70,114,0.12)');   // farthest, palest
        rangeLayer(0.62,  0.15, 11, 7.4,  'rgba(50,60,104,0.16)');
        rangeLayer(0.66,  0.17, 13, 12.8, 'rgba(42,52,94,0.22)');    // nearest, darkest

        /* ─── distant drifting clouds ─── */
        function cloudPuff(cx, cy, rw, rh, a) {
            const blobs = [[0,0,1.0],[-0.55,0.10,0.72],[0.55,0.10,0.74],[-0.95,0.26,0.50],[0.95,0.24,0.52],[0.22,-0.16,0.60],[-0.28,-0.13,0.56]];
            for (const [dx, dyb, s] of blobs) {
                const bx = cx + dx * rw, by = cy + dyb * rh, br = rh * s * 1.7;
                const g = ctx.createRadialGradient(bx, by, 0, bx, by, br);
                g.addColorStop(0,   'rgba(208,212,230,' + a.toFixed(3) + ')');
                g.addColorStop(0.6, 'rgba(178,184,208,' + (a * 0.5).toFixed(3) + ')');
                g.addColorStop(1,   'rgba(178,184,208,0)');
                ctx.fillStyle = g; ctx.beginPath(); ctx.arc(bx, by, br, 0, Math.PI * 2); ctx.fill();
            }
        }
        const bands = [
            { x: 0.10, y: 0.34, s: 1.1, a: 0.16, sp: 0.020 },
            { x: 0.40, y: 0.27, s: 1.4, a: 0.17, sp: 0.013 },
            { x: 0.24, y: 0.46, s: 0.9, a: 0.12, sp: 0.026 },
            { x: 0.52, y: 0.40, s: 1.0, a: 0.14, sp: 0.017 }
        ];
        ctx.save();
        for (const b of bands) {
            const span = 1.6;
            const fx = (b.x + t * b.sp * 0.02) % span;       // slow drift, then wrap
            cloudPuff(w * (fx - 0.20), h * b.y, w * 0.12 * b.s, h * 0.030 * b.s, b.a);
        }
        ctx.restore();

        /* ─── Mount Fuji — distinct hero peak, drawn in front of the haze ─── */
        const fujiX = w * 0.22, fujiY = h * 0.34;
        const baseHalf = w * 0.150, sumHalf = w * 0.013, dy = baseY - fujiY;
        const lbx = fujiX - baseHalf, rbx = fujiX + baseHalf, slx = fujiX - sumHalf, srx = fujiX + sumHalf;
        const fg = ctx.createLinearGradient(0, fujiY, 0, baseY);
        fg.addColorStop(0, 'rgba(70,78,118,0.66)');
        fg.addColorStop(0.6, 'rgba(46,54,92,0.36)');
        fg.addColorStop(1, 'rgba(28,34,64,0.0)');
        ctx.save(); ctx.fillStyle = fg; ctx.beginPath();
        ctx.moveTo(lbx, baseY);
        ctx.bezierCurveTo(fujiX - baseHalf * 0.52, baseY - dy * 0.30, slx - w * 0.02, fujiY + dy * 0.12, slx, fujiY);
        ctx.lineTo(srx, fujiY);
        ctx.bezierCurveTo(srx + w * 0.02, fujiY + dy * 0.12, fujiX + baseHalf * 0.52, baseY - dy * 0.30, rbx, baseY);
        ctx.closePath(); ctx.fill();
        ctx.fillStyle = 'rgba(18,24,50,0.16)'; ctx.beginPath();
        ctx.moveTo(fujiX, fujiY); ctx.lineTo(srx, fujiY);
        ctx.bezierCurveTo(srx + w * 0.02, fujiY + dy * 0.12, fujiX + baseHalf * 0.52, baseY - dy * 0.30, rbx, baseY);
        ctx.lineTo(fujiX, baseY); ctx.closePath(); ctx.fill();
        ctx.restore();
        const snowBottom = fujiY + dy * 0.27, capHalf = baseHalf * 0.30;
        const sgr = ctx.createLinearGradient(0, fujiY, 0, snowBottom);
        sgr.addColorStop(0, 'rgba(236,232,226,0.66)');
        sgr.addColorStop(1, 'rgba(210,216,232,0.06)');
        ctx.save(); ctx.fillStyle = sgr; ctx.beginPath();
        ctx.moveTo(slx, fujiY); ctx.lineTo(srx, fujiY); ctx.lineTo(fujiX + capHalf, snowBottom - 4);
        for (let i = 1; i < 7; i++) { const tt = i / 7, gx = fujiX + capHalf - 2 * capHalf * tt; ctx.lineTo(gx, (i % 2 === 0) ? snowBottom - 4 : snowBottom - 13); }
        ctx.lineTo(fujiX - capHalf, snowBottom - 4); ctx.closePath(); ctx.fill(); ctx.restore();
    }

    /* ════════════════════════════════════
       TORII GATE
    ════════════════════════════════════ */
    function drawTorii() {
        const gx = w * 0.045, gy = h * 0.56;
        const gW = Math.max(60, w * 0.088);
        const gH = Math.min(h * 0.26, 195);
        const pW = Math.max(5, gW * 0.10);
        ctx.save();
        ctx.globalAlpha = 0.22;
        ctx.fillStyle = 'rgb(188,44,44)';
        ctx.fillRect(gx - gW*0.5, gy, pW, gH);
        ctx.fillRect(gx + gW*0.5 - pW, gy, pW, gH);
        ctx.fillRect(gx - gW*0.5, gy + gH*0.22, gW, pW*1.3);
        ctx.beginPath();
        ctx.moveTo(gx - gW*0.70, gy + pW*1.6);
        ctx.quadraticCurveTo(gx, gy - pW*0.9, gx + gW*0.70, gy + pW*1.6);
        ctx.lineTo(gx + gW*0.70, gy + pW*3.0);
        ctx.quadraticCurveTo(gx, gy + pW*0.7, gx - gW*0.70, gy + pW*3.0);
        ctx.closePath(); ctx.fill();
        ctx.restore();
    }

    /* ════════════════════════════════════
       WAVE GEOMETRY — shared
    ════════════════════════════════════ */
    function waveLine(x0, x1, baseY, amp, wl, phase) {
        ctx.moveTo(x0, baseY);
        for (let x = x0; x <= x1; x += 4) {
            const t = (x / wl) * Math.PI * 2 + phase;
            ctx.lineTo(x, baseY + amp * Math.sin(t) + amp * 0.28 * Math.sin(t * 2 + 0.6));
        }
    }

    function drawJapaneseWaves() {
        const layers = [
            {ry:0.800,amp: 9,wl:0.22,a:'rgba(16,40,100,0.10)'},
            {ry:0.836,amp:13,wl:0.26,a:'rgba(20,52,128,0.14)'},
            {ry:0.866,amp:17,wl:0.30,a:'rgba(26,64,152,0.17)'},
            {ry:0.896,amp:21,wl:0.34,a:'rgba(32,76,168,0.20)'},
            {ry:0.924,amp:25,wl:0.38,a:'rgba(38,86,180,0.22)'},
        ];
        ctx.save();
        layers.forEach((l, i) => {
            ctx.fillStyle = l.a;
            ctx.beginPath();
            const by = h * l.ry;
            waveLine(0, w * 0.58, by, l.amp, w * l.wl, jPhase + i * 0.55);
            ctx.lineTo(w * 0.58, h + 2); ctx.lineTo(0, h + 2);
            ctx.closePath(); ctx.fill();
        });
        ctx.restore();
    }

    /* ════════════════════════════════════
       ACCRA CITY SKYLINE  (right half backdrop)
    ════════════════════════════════════ */
    function drawAccraSkyline() {
        const baseY = h * 0.80;
        const t = jPhase;
        /* warm haze over right half */
        const haze = ctx.createLinearGradient(w * 0.45, 0, w, 0);
        haze.addColorStop(0,    'rgba(0,0,0,0)');
        haze.addColorStop(0.12, 'rgba(96,62,22,0.06)');
        haze.addColorStop(1,    'rgba(96,62,22,0.06)');
        ctx.save(); ctx.fillStyle = haze;
        ctx.fillRect(w * 0.45, 0, w * 0.55, h);
        ctx.restore();

        /* warm ground glow from the lit city */
        const cityGlow = ctx.createRadialGradient(w * 0.78, baseY, 0, w * 0.78, baseY, w * 0.40);
        cityGlow.addColorStop(0, 'rgba(234,170,72,0.17)');
        cityGlow.addColorStop(1, 'rgba(234,170,72,0)');
        ctx.save(); ctx.fillStyle = cityGlow; ctx.fillRect(w * 0.45, h * 0.30, w * 0.55, h * 0.60); ctx.restore();

        /* varied building silhouettes */
        const bldgs = [
            [0.55,0.025,0.18],[0.576,0.018,0.25],[0.596,0.030,0.20],
            [0.629,0.022,0.30],[0.653,0.040,0.22],[0.696,0.025,0.36],
            [0.723,0.018,0.27],[0.743,0.035,0.19],[0.781,0.020,0.33],
            [0.804,0.015,0.24],[0.821,0.028,0.17],[0.852,0.020,0.29],
            [0.874,0.025,0.21],[0.901,0.018,0.27],[0.921,0.032,0.18],
            [0.956,0.026,0.24],
        ];
        const bGrd = ctx.createLinearGradient(0, h * 0.28, 0, baseY);
        bGrd.addColorStop(0,   'rgba(40,28,14,0.52)');
        bGrd.addColorStop(0.6, 'rgba(30,20,10,0.40)');
        bGrd.addColorStop(1,   'rgba(0,0,0,0)');
        ctx.save();
        bldgs.forEach(([xr, wr, hr], bi) => {
            /* brought forward: taller + a touch wider */
            const bx = w * xr, bw = w * wr * 1.15, bh = h * hr * 1.4;
            const fade = Math.max(0, Math.min(1, (xr - 0.50) / 0.08));
            /* dark silhouette so the lit windows read */
            ctx.globalAlpha = fade * 0.70;
            ctx.fillStyle = bGrd;
            ctx.fillRect(bx, baseY - bh, bw, bh + 2);
            /* lit windows — stable per window (fbm), a few gently twinkle */
            let ry = 0;
            for (let wy = baseY - bh + 7; wy < baseY - 6; wy += 11, ry++) {
                let rx = 0;
                for (let wx = bx + 3; wx < bx + bw - 3; wx += 8, rx++) {
                    const seed = bi * 31.7 + ry * 7.3 + rx * 2.1;
                    const on = fbmRnd(seed);
                    if (on > 0.40) {
                        const tw = on > 0.92 ? (0.55 + 0.45 * Math.sin(t * 1.3 + seed * 9)) : 1;
                        ctx.globalAlpha = fade * 0.72 * tw;
                        ctx.fillStyle = on > 0.78 ? 'rgba(255,228,150,1)' : 'rgba(255,200,116,1)';
                        ctx.fillRect(wx, wy, 2, 2.4);
                    }
                }
            }
        });
        ctx.restore();
    }

    /* ════════════════════════════════════
       ELMINA CASTLE — whitewashed coastal fort, lit up at night
    ════════════════════════════════════ */
    function drawCoastalCastle() {
        const cx   = w * 0.70;
        const by   = h * 0.84;                            // brought forward (lower)
        const CW   = Math.min(w * 0.25, 250);             // larger
        const CH   = Math.min(h * 0.205, 176);
        const mW   = CW * 0.048, mH = CH * 0.11, mGap = CW * 0.038;

        /* warm ambient glow (floodlit walls) */
        const glow = ctx.createRadialGradient(cx, by - CH * 0.55, 0, cx, by - CH * 0.55, CW * 0.95);
        glow.addColorStop(0,   'rgba(232,196,128,0.30)');
        glow.addColorStop(0.6, 'rgba(188,138,76,0.12)');
        glow.addColorStop(1,   'rgba(0,0,0,0)');
        ctx.save(); ctx.globalAlpha = 1; ctx.fillStyle = glow;
        ctx.fillRect(cx - CW * 1.1, by - CH * 1.8, CW * 2.2, CH * 2.0);
        ctx.restore();

        ctx.save();
        ctx.globalAlpha = 0.55;
        const cc = 'rgba(232,224,206,1)';                 // whitewashed Elmina walls

        /* ── main curtain wall ── */
        ctx.fillStyle = cc;
        ctx.fillRect(cx - CW*0.5, by - CH*0.38, CW, CH*0.38);
        /* crenellations */
        for (let mx = cx - CW*0.5 + mGap; mx < cx + CW*0.5 - mGap; mx += mW + mGap) {
            ctx.fillRect(mx, by - CH*0.38 - mH, mW, mH);
        }

        /* ── left bastion ── */
        ctx.fillRect(cx - CW*0.53, by - CH*0.58, CW*0.19, CH*0.58);
        for (let mx = cx - CW*0.53; mx < cx - CW*0.53 + CW*0.19; mx += mW*0.88 + mGap*0.55) {
            ctx.fillRect(mx, by - CH*0.58 - mH*0.88, mW*0.88, mH*0.88);
        }

        /* ── right bastion ── */
        ctx.fillRect(cx + CW*0.34, by - CH*0.58, CW*0.19, CH*0.58);
        for (let mx = cx + CW*0.34; mx < cx + CW*0.53; mx += mW*0.88 + mGap*0.55) {
            ctx.fillRect(mx, by - CH*0.58 - mH*0.88, mW*0.88, mH*0.88);
        }

        /* ── central keep (taller) ── */
        ctx.fillRect(cx - CW*0.12, by - CH*0.90, CW*0.24, CH*0.90);
        for (let mx = cx - CW*0.12; mx < cx + CW*0.12; mx += mW + mGap) {
            ctx.fillRect(mx, by - CH*0.90 - mH, mW, mH);
        }

        /* ── arch entrance ── */
        const aW = CW*0.14, aH = CH*0.22;
        ctx.globalAlpha = 0.24;
        ctx.save();
        ctx.fillStyle = 'rgba(28,16,6,1)';
        ctx.globalAlpha = 1;
        ctx.fillRect(cx - aW*0.5, by - aH*0.72, aW, aH*0.72);
        ctx.beginPath();
        ctx.arc(cx, by - aH*0.72, aW*0.5, Math.PI, 0);
        ctx.fill();
        ctx.restore();

        /* ── cannon ports ── */
        ctx.save();
        ctx.fillStyle = 'rgba(20,10,4,0.85)';
        ctx.globalAlpha = 0.85;
        [-0.34, -0.20, -0.06, 0.09, 0.23].forEach(px => {
            ctx.fillRect(cx + CW*px, by - CH*0.22, CW*0.048, CH*0.09);
        });
        ctx.restore();

        /* ── lit windows (warm, floodlit fort) ── */
        ctx.save();
        ctx.globalAlpha = 0.85;
        ctx.fillStyle = 'rgba(255,214,132,1)';
        /* keep windows (two rows) */
        for (let r = 0; r < 2; r++) {
            for (let i = 0; i < 3; i++) {
                ctx.fillRect(cx - CW*0.075 + i*CW*0.06, by - CH*(0.70 - r*0.22), CW*0.022, CH*0.05);
            }
        }
        /* curtain-wall windows */
        [-0.32, -0.18, 0.18, 0.32].forEach(px => {
            ctx.fillRect(cx + CW*px, by - CH*0.26, CW*0.02, CH*0.05);
        });
        /* bastion windows */
        [-0.46, 0.42].forEach(px => {
            ctx.fillRect(cx + CW*px, by - CH*0.42, CW*0.02, CH*0.05);
        });
        ctx.restore();

        /* ── flagpole + Ghana flag ── */
        ctx.save();
        ctx.strokeStyle = 'rgba(200,180,140,0.55)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx + CW*0.03, by - CH*0.90 - mH);
        ctx.lineTo(cx + CW*0.03, by - CH*0.90 - mH - CH*0.25);
        ctx.stroke();
        const fy = by - CH*0.90 - mH - CH*0.25;
        const fw = CW*0.11, fh = CH*0.092;
        const flagCols = ['rgba(200,38,38,0.50)','rgba(218,178,46,0.50)','rgba(32,108,38,0.50)'];
        flagCols.forEach((fc, ci) => {
            ctx.fillStyle = fc;
            ctx.fillRect(cx + CW*0.03, fy + ci*(fh/3), fw, fh/3 + 0.5);
        });
        ctx.restore();

        ctx.restore();
    }

    /* ════════════════════════════════════
       ACCRA SPORTS STADIUM
    ════════════════════════════════════ */
    function drawStadium() {
        const sx = w * 0.87, by = h * 0.84;
        const SW = Math.min(w * 0.155, 148);
        const SH = Math.min(h * 0.095, 78);
        ctx.save();
        ctx.globalAlpha = 0.19;

        /* lower bowl */
        ctx.fillStyle = 'rgba(78,62,42,1)';
        ctx.fillRect(sx - SW*0.5, by - SH*0.38, SW, SH*0.38);

        /* cantilever roof */
        ctx.fillStyle = 'rgba(92,74,52,1)';
        ctx.beginPath();
        ctx.moveTo(sx - SW*0.52, by - SH*0.34);
        ctx.bezierCurveTo(sx - SW*0.56, by - SH*0.92, sx - SW*0.30, by - SH*1.12, sx, by - SH*1.17);
        ctx.bezierCurveTo(sx + SW*0.30, by - SH*1.12, sx + SW*0.56, by - SH*0.92, sx + SW*0.52, by - SH*0.34);
        ctx.lineTo(sx + SW*0.47, by - SH*0.34);
        ctx.bezierCurveTo(sx + SW*0.50, by - SH*0.84, sx + SW*0.27, by - SH*1.00, sx, by - SH*1.05);
        ctx.bezierCurveTo(sx - SW*0.27, by - SH*1.00, sx - SW*0.50, by - SH*0.84, sx - SW*0.47, by - SH*0.34);
        ctx.closePath(); ctx.fill();

        /* support columns */
        ctx.fillStyle = 'rgba(68,52,32,0.9)';
        [-0.42,-0.28,-0.14,0.0,0.14,0.28,0.42].forEach(cp => {
            ctx.fillRect(sx + SW*cp - 2, by - SH*0.88, 4, SH*0.50);
        });

        /* floodlight pylons */
        ctx.fillStyle = 'rgba(88,72,52,0.7)';
        [-0.50, 0.50].forEach(lp => {
            ctx.fillRect(sx + SW*lp - 1.5, by - SH*1.32, 3, SH*0.36);
            ctx.fillRect(sx + SW*lp - SW*0.055, by - SH*1.38, SW*0.11, SH*0.064);
        });

        ctx.restore();
    }

    /* ════════════════════════════════════
       PALM TREE
    ════════════════════════════════════ */
    function drawPalm() {
        const px = w * 0.965, py = h;
        const TH = Math.min(h * 0.32, 250);
        ctx.save(); ctx.globalAlpha = 0.19;
        ctx.strokeStyle = 'rgb(58,78,28)';
        ctx.lineWidth = Math.max(4, w * 0.006);
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(px, py);
        ctx.bezierCurveTo(px - w*0.015, py - TH*0.4, px + w*0.02, py - TH*0.7, px - w*0.01, py - TH);
        ctx.stroke();
        ctx.lineWidth = Math.max(2, w * 0.0028);
        const bx = px - w*0.01, bY = py - TH;
        [[-0.09,-0.15,-0.22,-0.05,0.06],
         [-0.02,-0.20,-0.10,-0.22,0.04],
         [0.06,-0.16,0.16,-0.12,0.02],
         [0.08,-0.12,0.22,-0.06,-0.02],
         [-0.10,-0.10,-0.24,0.02,-0.04],
        ].forEach(([dx1,dy1,dx2,dy2,ex]) => {
            ctx.beginPath();
            ctx.moveTo(bx, bY);
            ctx.bezierCurveTo(bx+w*dx1, bY+h*dy1, bx+w*dx2, bY+h*dy2, bx+w*(dx2+ex), bY+h*(dy2+0.08));
            ctx.stroke();
        });
        ctx.restore();
    }

    /* ════════════════════════════════════
       COASTAL WAVES — Gulf of Guinea
    ════════════════════════════════════ */
    function drawCoastalWaves() {
        /* full-width foreground sea — gentle, slow swell across the whole scene */
        const layers = [
            {ry:0.800,amp: 7,wl:0.22,a:'rgba(14,82,80,0.12)'},
            {ry:0.834,amp:10,wl:0.26,a:'rgba(18,96,88,0.15)'},
            {ry:0.864,amp:14,wl:0.30,a:'rgba(22,108,94,0.18)'},
            {ry:0.894,amp:18,wl:0.34,a:'rgba(28,118,98,0.21)'},
            {ry:0.922,amp:22,wl:0.38,a:'rgba(34,126,104,0.24)'},
        ];
        ctx.save();
        layers.forEach((l, i) => {
            ctx.fillStyle = l.a;
            ctx.beginPath();
            const by = h * l.ry;
            waveLine(-4, w + 4, by, l.amp, w * l.wl, gPhase + i * 0.50 + Math.PI);
            ctx.lineTo(w + 4, h + 2); ctx.lineTo(-4, h + 2);
            ctx.closePath(); ctx.fill();
        });
        ctx.restore();
    }

    /* ════════════════════════════════════
       ADINKRA SYMBOLS — bold & clean
    ════════════════════════════════════ */
    function adinkra(type, cx, cy, r, alpha) {
        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.strokeStyle = 'rgba(218,172,55,1)';
        ctx.fillStyle   = 'rgba(218,172,55,1)';
        ctx.lineWidth   = Math.max(1.8, r * 0.11);
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';

        if (type === 'adinkrahene') {
            [1, 0.65, 0.35].forEach(s => {
                ctx.beginPath(); ctx.arc(cx, cy, r * s, 0, Math.PI * 2); ctx.stroke();
            });
        } else if (type === 'gye_nyame') {
            ctx.beginPath();
            ctx.moveTo(cx - r, cy);
            ctx.bezierCurveTo(cx - r*0.5, cy - r*0.82, cx + r*0.5, cy - r*0.82, cx + r, cy);
            ctx.bezierCurveTo(cx + r*0.5, cy + r*0.82, cx - r*0.5, cy + r*0.82, cx - r, cy);
            ctx.stroke();
            ctx.beginPath(); ctx.arc(cx, cy, r*0.20, 0, Math.PI*2); ctx.fill();
            ctx.lineWidth *= 0.7;
            ctx.beginPath();
            ctx.moveTo(cx, cy - r*0.52); ctx.lineTo(cx, cy + r*0.52);
            ctx.moveTo(cx - r*0.32, cy); ctx.lineTo(cx + r*0.32, cy);
            ctx.stroke();
        } else if (type === 'sankofa') {
            ctx.beginPath();
            ctx.arc(cx - r*0.34, cy - r*0.18, r*0.40, Math.PI, 0);
            ctx.arc(cx + r*0.34, cy - r*0.18, r*0.40, Math.PI, 0);
            ctx.bezierCurveTo(cx + r*0.74, cy - r*0.18, cx + r*0.40, cy + r*0.42, cx, cy + r*0.76);
            ctx.bezierCurveTo(cx - r*0.40, cy + r*0.42, cx - r*0.74, cy - r*0.18, cx - r*0.74, cy - r*0.18);
            ctx.closePath(); ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(cx, cy + r*0.76);
            ctx.bezierCurveTo(cx - r*0.28, cy + r*0.52, cx - r*0.48, cy, cx - r*0.28, cy - r*0.38);
            ctx.stroke();
        }
        ctx.restore();
    }

    function drawAdinkraSymbols() {
        adinkra('adinkrahene', w*0.67, h*0.32, Math.min(32,w*0.027), 0.19);
        adinkra('gye_nyame',   w*0.84, h*0.21, Math.min(26,w*0.023), 0.18);
        adinkra('sankofa',     w*0.93, h*0.45, Math.min(24,w*0.021), 0.18);
    }

    /* ════════════════════════════════════
       KENTE STRIP  (top right)
    ════════════════════════════════════ */
    function drawKenteStrip() {
        // Woven Kente band: alternating warp/weft thread blocks (basket weave)
        const x0 = w * 0.55, y0 = h * 0.045, bandW = w * 0.45;
        const cell = Math.max(10, Math.min(15, w * 0.011));
        const rows = 3, cols = Math.ceil(bandW / cell);
        const pal = ['rgba(212,170,40,A)', 'rgba(40,112,56,A)', 'rgba(190,40,46,A)', 'rgba(232,224,205,A)'];
        const a = 0.17, th = cell / 3;
        ctx.save();
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                const cx = x0 + c * cell, cy = y0 + r * cell;
                if (cx + cell > w + 1) continue;
                const horiz = ((r + c) % 2 === 0);
                ctx.fillStyle = pal[(c + r * 2) % pal.length].replace('A', a);
                for (let k = 0; k < 3; k++) {
                    if (horiz) ctx.fillRect(cx + 1, cy + k * th + 0.5, cell - 2, th - 1.2);
                    else        ctx.fillRect(cx + k * th + 0.5, cy + 1, th - 1.2, cell - 2);
                }
            }
        }
        ctx.restore();
    }

    /* ════════════════════════════════════
       BLACK STAR — Ghanaian identity anchor
    ════════════════════════════════════ */
    function fivePointStar(cx, cy, rO, rI) {
        ctx.beginPath();
        for (let i = 0; i < 10; i++) {
            const ang = -Math.PI / 2 + i * Math.PI / 5;
            const rr = (i % 2 === 0) ? rO : rI;
            const x = cx + rr * Math.cos(ang), y = cy + rr * Math.sin(ang);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
    }
    function drawBlackStar() {
        const cx = w * 0.885, cy = h * 0.125, rO = Math.min(26, w * 0.022), rI = rO * 0.42;
        ctx.save();
        ctx.globalAlpha = 0.20;
        fivePointStar(cx, cy, rO, rI);
        ctx.fillStyle = 'rgba(244,196,48,1)';
        ctx.fill();
        ctx.restore();
    }

    /* ════════════════════════════════════
       FOOTBALLER SILHOUETTE  (Ghana pride)
    ════════════════════════════════════ */
    function drawFootballer() {
        const fx = w * 0.60, fy = h * 0.84;
        const sc = Math.min(h * 0.095, 78);
        ctx.save();
        ctx.globalAlpha = 0.11;
        ctx.fillStyle = 'rgba(88,58,22,1)';

        /* torso */
        ctx.beginPath();
        ctx.ellipse(fx, fy - sc*0.62, sc*0.14, sc*0.22, -0.15, 0, Math.PI*2);
        ctx.fill();

        /* head */
        ctx.beginPath();
        ctx.arc(fx - sc*0.04, fy - sc*0.92, sc*0.10, 0, Math.PI*2);
        ctx.fill();

        /* kicking leg */
        ctx.lineWidth = sc * 0.09;
        ctx.strokeStyle = 'rgba(88,58,22,1)';
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(fx, fy - sc*0.40);
        ctx.quadraticCurveTo(fx + sc*0.18, fy - sc*0.10, fx + sc*0.38, fy - sc*0.05);
        ctx.stroke();

        /* standing leg */
        ctx.beginPath();
        ctx.moveTo(fx, fy - sc*0.40);
        ctx.quadraticCurveTo(fx - sc*0.05, fy - sc*0.05, fx - sc*0.04, fy);
        ctx.stroke();

        /* arms */
        ctx.lineWidth = sc * 0.065;
        ctx.beginPath();
        ctx.moveTo(fx - sc*0.05, fy - sc*0.72);
        ctx.quadraticCurveTo(fx - sc*0.22, fy - sc*0.52, fx - sc*0.18, fy - sc*0.36);
        ctx.moveTo(fx + sc*0.04, fy - sc*0.68);
        ctx.quadraticCurveTo(fx + sc*0.20, fy - sc*0.55, fx + sc*0.15, fy - sc*0.38);
        ctx.stroke();

        /* ball */
        ctx.beginPath();
        ctx.arc(fx + sc*0.44, fy - sc*0.07, sc*0.09, 0, Math.PI*2);
        ctx.fill();

        ctx.restore();
    }

    /* ════════════════════════════════════
       BACTERIOPHAGE PARTICLES
    ════════════════════════════════════ */
    function drawPhageShape(x, y, sz, rot) {
        const hR = sz * 0.38;
        const tLen = sz * 0.60;
        const tW   = sz * 0.10;
        const bpR  = tW * 1.55;
        const tTop = hR * 0.82;
        const tBot = tTop + tLen;

        ctx.save();
        ctx.translate(x, y); ctx.rotate(rot);
        ctx.strokeStyle = 'rgba(140,220,178,1)';
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.lineWidth = Math.max(0.9, sz * 0.048);

        /* hexagonal head */
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const a = (i * Math.PI / 3) - Math.PI / 6;
            const px = hR * Math.cos(a), py = hR * Math.sin(a);
            i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath(); ctx.stroke();

        /* inner star detail */
        ctx.lineWidth = Math.max(0.5, sz * 0.026);
        for (let i = 0; i < 3; i++) {
            const a = i * Math.PI / 3;
            ctx.beginPath();
            ctx.moveTo(hR*0.55*Math.cos(a), hR*0.55*Math.sin(a));
            ctx.lineTo(hR*0.55*Math.cos(a+Math.PI), hR*0.55*Math.sin(a+Math.PI));
            ctx.stroke();
        }

        ctx.lineWidth = Math.max(0.9, sz * 0.048);
        /* collar */
        ctx.beginPath();
        ctx.moveTo(-tW*0.95, tTop - sz*0.04);
        ctx.lineTo( tW*0.95, tTop - sz*0.04);
        ctx.stroke();

        /* tail sheath (double line) */
        ctx.beginPath(); ctx.moveTo(-tW*0.45, tTop); ctx.lineTo(-tW*0.45, tBot); ctx.stroke();
        ctx.beginPath(); ctx.moveTo( tW*0.45, tTop); ctx.lineTo( tW*0.45, tBot); ctx.stroke();
        /* sheath rings */
        ctx.lineWidth = Math.max(0.5, sz * 0.026);
        for (let ri = 0.2; ri < 0.85; ri += 0.22) {
            const ry = tTop + tLen * ri;
            ctx.beginPath(); ctx.moveTo(-tW*0.5, ry); ctx.lineTo(tW*0.5, ry); ctx.stroke();
        }

        ctx.lineWidth = Math.max(0.9, sz * 0.048);
        /* base plate (flattened hexagon) */
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const a = i * Math.PI / 3;
            const px = bpR * Math.cos(a);
            const py = tBot + bpR * 0.5 * Math.sin(a);
            i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath(); ctx.stroke();

        /* tail fibers */
        ctx.lineWidth = Math.max(0.5, sz * 0.026);
        for (let i = 0; i < 6; i++) {
            const a = (i * Math.PI / 3) - Math.PI / 12;
            const sx2 = bpR * 0.68 * Math.cos(a);
            const ex  = bpR * 1.82 * Math.cos(a);
            const ey  = tBot + sz * 0.30;
            ctx.beginPath();
            ctx.moveTo(sx2, tBot);
            ctx.quadraticCurveTo(bpR * 1.25 * Math.cos(a), tBot + sz * 0.14, ex, ey);
            ctx.stroke();
        }
        ctx.restore();
    }

    function initPhages() {
        phages = [];
        const count = Math.round(13 * PM);
        for (let i = 0; i < count; i++) {
            phages.push({
                x:    Math.random() * w,
                y:    Math.random() * h,
                sz:   18 + Math.random() * 22,
                vx:   (Math.random() - 0.5) * 0.18,
                vy:   -0.04 - Math.random() * 0.13,
                rot:  Math.random() * Math.PI * 2,
                vrot: (Math.random() - 0.5) * 0.008,
                alp:  0.08 + Math.random() * 0.12,
            });
        }
    }

    function updateDrawPhages() {
        phages.forEach(p => {
            p.x  += p.vx;
            p.y  += p.vy;
            p.rot += p.vrot;
            if (p.y < -90)     { p.y = h + 40; p.x = Math.random() * w; }
            if (p.x < -90)       p.x = w + 40;
            if (p.x > w + 90)    p.x = -40;
            ctx.save();
            ctx.globalAlpha = p.alp;
            drawPhageShape(p.x, p.y, p.sz, p.rot);
            ctx.restore();
        });
    }

    /* ════════════════════════════════════
       CHERRY BLOSSOM PARTICLES
    ════════════════════════════════════ */
    function initPetals() {
        petals = [];
        const count = Math.round(16 * PM);
        for (let i = 0; i < count; i++) {
            petals.push({
                x: Math.random() * w * 0.62,
                y: Math.random() * h,
                vx: 0.12 + Math.random() * 0.22,
                vy: 0.06 + Math.random() * 0.20,
                sw: Math.random() * Math.PI * 2,
                swS: 0.015 + Math.random() * 0.02,
                rot: Math.random() * Math.PI * 2,
                vr: (Math.random() - 0.5) * 0.04,
                r:  3 + Math.random() * 3,
            });
        }
    }

    function updateDrawPetals() {
        petals.forEach(p => {
            p.x += p.vx + Math.sin(p.sw) * 0.30;
            p.y += p.vy;
            p.sw += p.swS;
            p.rot += p.vr;
            if (p.x > w * 0.76 || p.y > h + 20) {
                p.x = Math.random() * w * 0.28; p.y = -10;
            }
            const fade = Math.max(0, 1 - (p.x - w*0.35) / (w*0.30));
            ctx.save();
            ctx.globalAlpha = fade * 0.24;
            ctx.fillStyle = 'rgba(232,152,168,1)';
            ctx.translate(p.x, p.y); ctx.rotate(p.rot);
            for (let i = 0; i < 5; i++) {
                const a = (i * Math.PI * 2) / 5;
                ctx.beginPath();
                ctx.ellipse(Math.cos(a)*p.r*0.7, Math.sin(a)*p.r*0.7, p.r*0.55, p.r*0.30, a, 0, Math.PI*2);
                ctx.fill();
            }
            ctx.restore();
        });
    }

    /* ════════════════════════════════════
       RESIZE
    ════════════════════════════════════ */
    function resize() {
        const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
        canvas.width  = Math.round(window.innerWidth  * dpr);
        canvas.height = Math.round(window.innerHeight * dpr);
        canvas.style.width  = window.innerWidth  + 'px';
        canvas.style.height = window.innerHeight + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        w = window.innerWidth;
        h = window.innerHeight;
        initPetals();
        initPhages();
    }

    /* ════════════════════════════════════
       ATMOSPHERIC WASH
       A single blended field instead of literal scenery: a cool indigo
       bloom (heritage: Japan/Saitama) melts into a warm amber bloom
       (Ghana/Accra), tied together by slow drifting haze. Everything
       sits low and soft against the dark page.
    ════════════════════════════════════ */
    function drawAtmosphere() {
        const t = jPhase;
        const breathe = 0.5 + 0.5 * Math.sin(t * 0.05);

        ctx.save();
        ctx.globalCompositeOperation = 'lighter';

        /* cool indigo bloom drifting through the upper-left */
        const cx1 = w * (0.26 + 0.03 * Math.sin(t * 0.04));
        const cy1 = h * (0.36 + 0.03 * Math.cos(t * 0.045));
        const g1 = ctx.createRadialGradient(cx1, cy1, 0, cx1, cy1, w * 0.62);
        g1.addColorStop(0,   'rgba(66,92,154,' + (0.12 + 0.035 * breathe).toFixed(3) + ')');
        g1.addColorStop(0.5, 'rgba(44,62,112,0.052)');
        g1.addColorStop(1,   'rgba(20,30,60,0)');
        ctx.fillStyle = g1; ctx.fillRect(0, 0, w, h);

        /* warm amber bloom drifting through the lower-right */
        const cx2 = w * (0.76 - 0.03 * Math.cos(t * 0.042));
        const cy2 = h * (0.60 + 0.03 * Math.sin(t * 0.05));
        const g2 = ctx.createRadialGradient(cx2, cy2, 0, cx2, cy2, w * 0.62);
        g2.addColorStop(0,   'rgba(156,108,46,' + (0.075 + 0.03 * (1 - breathe)).toFixed(3) + ')');
        g2.addColorStop(0.5, 'rgba(120,76,30,0.030)');
        g2.addColorStop(1,   'rgba(60,40,16,0)');
        ctx.fillStyle = g2; ctx.fillRect(0, 0, w, h);

        /* slow drifting haze that ties the whole field together */
        const haze = [
            { x: 0.12, y: 0.30, r: 0.34, fl: 0.42, c: '128,150,200', a: 0.058, sp: 0.020 },
            { x: 0.40, y: 0.58, r: 0.42, fl: 0.40, c: '150,150,172', a: 0.044, sp: 0.013 },
            { x: 0.68, y: 0.38, r: 0.36, fl: 0.44, c: '190,156,100', a: 0.045, sp: 0.017 },
            { x: 0.30, y: 0.74, r: 0.38, fl: 0.40, c: '128,150,200', a: 0.048, sp: 0.011 },
            { x: 0.86, y: 0.66, r: 0.34, fl: 0.42, c: '190,150,96',  a: 0.040, sp: 0.015 },
            { x: 0.55, y: 0.20, r: 0.30, fl: 0.46, c: '140,150,180', a: 0.032, sp: 0.022 }
        ];
        for (const b of haze) {
            const span = 1.4;                                   // wrap distance (screen widths)
            const fx = (b.x + t * b.sp * 0.02) % span;          // drift right, then wrap
            const cx = w * (fx - 0.2);
            const cy = h * (b.y + 0.02 * Math.sin(t * 0.06 + b.x * 8));
            const r = w * b.r;
            ctx.save();
            ctx.translate(cx, cy);
            ctx.scale(1, b.fl);
            const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
            g.addColorStop(0,    'rgba(' + b.c + ',' + b.a.toFixed(3) + ')');
            g.addColorStop(0.55, 'rgba(' + b.c + ',' + (b.a * 0.45).toFixed(3) + ')');
            g.addColorStop(1,    'rgba(' + b.c + ',0)');
            ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
            ctx.restore();
        }
        ctx.restore();
    }

    /* ════════════════════════════════════
       RENDER LOOP  (20 fps)
    ════════════════════════════════════ */
    function render(t) {
        raf = requestAnimationFrame(render);
        if (t - lastFrame < FRAME_MS) return;
        lastFrame = t;

        ctx.clearRect(0, 0, w, h);
        jPhase += 0.006;

        /* Minimal Kente-tinted wash — soft, slowly drifting glows in the
           Kente palette (gold / green / red). No literal scenery; just
           colour and texture so the content stays clean and readable. */
        const glows = [
            { c: '244,196,48', x: 0.16, y: 0.20, r: 0.60, a: 0.070, sp: 0.55 },  // gold
            { c: '26,128,64',  x: 0.84, y: 0.80, r: 0.60, a: 0.055, sp: -0.45 }, // green
            { c: '196,30,58',  x: 0.72, y: 0.18, r: 0.50, a: 0.045, sp: 0.40 },  // red
            { c: '244,196,48', x: 0.30, y: 0.86, r: 0.50, a: 0.040, sp: -0.30 }  // gold
        ];
        for (const o of glows) {
            const cx = w * (o.x + 0.02 * Math.sin(jPhase * o.sp));
            const cy = h * (o.y + 0.02 * Math.cos(jPhase * o.sp));
            const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, w * o.r);
            g.addColorStop(0, 'rgba(' + o.c + ',' + o.a + ')');
            g.addColorStop(1, 'rgba(' + o.c + ',0)');
            ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
        }
    }

    resize();
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) { cancelAnimationFrame(raf); raf = null; }
        else if (!raf) raf = requestAnimationFrame(render);
    });
    raf = requestAnimationFrame(render);
})();
