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
    /* ════════════════════════════════════
       MOUNTAIN RANGE — varied peaks, drifting clouds, one erupting volcano
       (lower silhouettes with cloud cover over two atmospheric ridge layers;
        hero peak gets a molten crater, lava flows, and arcing embers)
    ════════════════════════════════════ */
ath.random() * w,
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

    /* ════════════════════════════════════
       CHERRY BLOSSOM PARTICLES
    ════════════════════════════════════ */
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
    }

    /* ════════════════════════════════════
       ATMOSPHERIC WASH
       A single blended field instead of literal scenery: a cool indigo
       bloom (heritage: Japan/Saitama) melts into a warm amber bloom
       (Ghana/Accra), tied together by slow drifting haze. Everything
       sits low and soft against the dark page.
    ════════════════════════════════════ */
    /* ════════════════════════════════════
       RENDER LOOP  (20 fps)
    ════════════════════════════════════ */
    resize();
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) { cancelAnimationFrame(raf); raf = null; }
        else if (!raf) raf = requestAnimationFrame(render);
    });
    raf = requestAnimationFrame(render);
})();
