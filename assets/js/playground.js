/* ==============================================================
   LIFECYCLE STAGE INTERACTION
=============================================================== */
const stageData = [
    { title: "Adsorption", info: "The phage tail fibers latch onto specific surface receptors on the bacterium — the molecular handshake that decides which hosts get infected." },
    { title: "DNA Injection", info: "Tail contracts; viral genome is injected through the cell envelope into the cytoplasm. Phage protein arrives essentially empty afterward." },
    { title: "Early Gene Expression", info: "Phage early genes hijack the host's transcription machinery, shut down defenses, and reprogram metabolism for viral replication." },
    { title: "Replication", info: "Massive DNA replication and structural protein synthesis. The cell is now a fully-rerouted viral factory." },
    { title: "Lysis Inhibition (N4)", info: "Phage N4 delays its own lysis decision, letting the factory keep producing — burst size jumps from ~200 to ~3,000 particles per cell." },
    { title: "Lysis & Release", info: "Holins puncture the membrane and endolysins shred the peptidoglycan. The cell bursts and thousands of progeny phages spill out to start over." }
];
const lifeInfo = document.getElementById('lifecycleInfo');
document.querySelectorAll('.lifecycle-stage').forEach((g, i) => {
    const show = () => {
        const d = stageData[i];
        lifeInfo.innerHTML = `<strong>${d.title}</strong> &mdash; ${d.info}`;
    };
    g.addEventListener('mouseenter', show);
    g.addEventListener('click', show);
    g.addEventListener('touchstart', show, { passive: true });
});

/* ==============================================================
   LYSIS PLAYGROUND — interactive sim
=============================================================== */
(function() {
    const canvas = document.getElementById('lysisCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const wrap = canvas.parentElement;
    let W, H, dpr;
    const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

    const state = {
        latent:   parseFloat(document.getElementById('ctrlLatent').value),
        inhibit:  parseFloat(document.getElementById('ctrlInhibit').value),
        burst:    parseFloat(document.getElementById('ctrlBurst').value),
        moi:      parseFloat(document.getElementById('ctrlMOI').value),
        mode:     'inhibited'
    };

    /* ---- Mechanistic infection model (Erlang-staged; superinfection drives LIN) ----
       Time axis is real hours (0..HMAX). LAT_SCALE compresses the latent period so a
       normal phage lyses within ~1 h. Lysis inhibition holds the culture cloudy, then
       collapses after a few hours (INH_CENTER), so N4 lysis is delayed but completes:
       with the default preset the drop begins ~3 h and clears by ~6 h. */
    const T = 110, dt = 0.5, NSTAGE = 24, r = 0.025, rInf = 0.020,
          K = 1.0, ads = 6.0, decay = 0.002, S0 = 0.04, SAMPLES = 200,
          HMAX = 7, LAT_SCALE = 0.30, INH_CENTER = 0.27, INH_STEEP = 11;

    function simulate(latent, burst, moi, cap) {
        let S = S0;
        const E = new Array(NSTAGE).fill(0);
        let p = moi * S0;
        const steps = Math.round(T / dt);
        const baseRate = NSTAGE / (latent * LAT_SCALE);
        const raw = [];
        for (let i = 0; i <= steps; i++) {
            let Etot = 0; for (let k = 0; k < NSTAGE; k++) Etot += E[k];
            raw.push(S + Etot);
            const intact = S + Etot;
            const frac = i / steps;
            // inhibition holds early, then collapses -> delayed but complete lysis
            const capEff = cap > 0 ? cap / (1 + Math.exp((frac - INH_CENTER) * INH_STEEP)) : 0;
            const sigma = ads * p;                       // superinfection signal
            const lysisRate = baseRate / (1 + capEff * sigma);
            let infect = ads * p * S * dt; if (infect > S) infect = S;
            const phageOnE = Math.min(p, ads * p * Etot * dt);
            let lyse = lysisRate * E[NSTAGE - 1] * dt; if (lyse > E[NSTAGE - 1]) lyse = E[NSTAGE - 1];
            const growthS = r * S * (1 - intact / K) * dt;
            for (let k = NSTAGE - 1; k > 0; k--) {
                const a = Math.min(E[k - 1], lysisRate * E[k - 1] * dt);
                E[k] += a; E[k - 1] -= a;
            }
            E[NSTAGE - 1] -= lyse;
            E[0] += infect;
            const gf = 1 + rInf * (1 - intact / K) * dt;  // infected cells keep adding turbidity
            for (let k = 0; k < NSTAGE; k++) { E[k] *= gf; if (E[k] < 0) E[k] = 0; }
            S += growthS - infect; if (S < 0) S = 0;
            p += burst * lyse - infect - phageOnE - decay * p * dt; if (p < 0) p = 0;
        }
        const od = new Array(SAMPLES + 1);
        for (let j = 0; j <= SAMPLES; j++) od[j] = raw[Math.round(j / SAMPLES * (raw.length - 1))];
        let peak = 0, peakIdx = 0;
        for (let j = 0; j <= SAMPLES; j++) if (od[j] > peak) { peak = od[j]; peakIdx = j; }
        // first point after the peak where turbidity has collapsed (culture clears)
        let clearX = null;
        for (let j = peakIdx; j <= SAMPLES; j++) { if (od[j] < peak * 0.05) { clearX = j / SAMPLES; break; } }
        return { od, peak, final: od[SAMPLES], lysisX: peakIdx / SAMPLES, clearX };
    }

    let simControl, simNormal, simInhib, ODMAX;
    function recompute() {
        simControl = simulate(state.latent, 0, 0, 0);
        simNormal  = simulate(state.latent, state.burst, state.moi, 0);
        simInhib   = simulate(state.latent, state.burst, state.moi, state.inhibit * 0.12);
        ODMAX = Math.max(simControl.peak, simNormal.peak, simInhib.peak, 0.2) * 1.08;
    }
    const activeSim = () => state.mode === 'inhibited' ? simInhib : simNormal;
    const sampleAt = (sim, x) => {
        const f = Math.max(0, Math.min(1, x)) * SAMPLES, i = Math.floor(f), frac = f - i;
        const a = sim.od[i], b = sim.od[Math.min(SAMPLES, i + 1)];
        return a + (b - a) * frac;
    };

    /* ---- Stage storyboard (no clock times) ---- */
    const STAGES = [
        { name: 'Adsorption & injection', text: 'The phage docks onto a surface receptor and injects its genome. The host is now infected.' },
        { name: 'Eclipse', text: 'No virions yet. The phage hijacks the host machinery to copy its genome and build viral proteins.' },
        { name: 'Assembly', text: 'New capsids fill with DNA. Virions pile up inside the still-intact cell, so the culture stays cloudy.' },
        { name: 'The lysis decision', text: 'Holins puncture the membrane and endolysin digests the wall. A normal phage commits to bursting right here.' }
    ];
    function outcomeStage() {
        return state.mode === 'inhibited'
            ? { name: 'Lysis inhibition (N4)', text: 'Extra phage <em>superinfect</em> the already-infected cell, and N4 delays lysis. The cell becomes a long-lived virus factory and the culture stays cloudy for hours — then inhibition finally breaks and the culture clears in a delayed, late crash (here around 3–6 h, versus under an hour for a normal phage).' }
            : { name: 'Lysis & burst', text: 'The cell ruptures and releases a burst of new phage. Across the flask, turbidity crashes as the population pops.' };
    }
    const stageInfo = i => i < 4 ? STAGES[i] : outcomeStage();
    function stageBounds() {
        const lx = Math.min(0.92, activeSim().lysisX);
        return [0, 0.15 * lx, 0.55 * lx, 0.9 * lx, lx, 1];
    }
    function stageAt(x) {
        const b = stageBounds();
        for (let s = 4; s >= 0; s--) if (x >= b[s]) return s;
        return 0;
    }

    /* ---- Stepper UI ---- */
    const stepper = document.getElementById('pgStepper');
    const shortLabels = ['Adsorption', 'Eclipse', 'Assembly', 'Decision', 'Outcome'];
    function buildStepper() {
        stepper.innerHTML = shortLabels.map((l, i) =>
            `<button type="button" class="pg-step" data-step="${i}"><span class="pg-step-num">${i + 1}</span><span class="pg-step-label">${i === 4 ? (state.mode === 'inhibited' ? 'Inhibition' : 'Burst') : l}</span></button>`
        ).join('');
        stepper.querySelectorAll('.pg-step').forEach(el => {
            el.addEventListener('click', () => {
                stop();
                const s = +el.dataset.step;
                const b = stageBounds();
                scrub((b[s] + b[s + 1]) / 2);
            });
        });
    }
    function setStage(i) {
        currentStage = i;
        document.getElementById('pgStageNum').textContent = i + 1;
        document.getElementById('pgStageName').textContent = stageInfo(i).name;
        document.getElementById('pgStageText').innerHTML = stageInfo(i).text;
        stepper.querySelectorAll('.pg-step').forEach(el => {
            const s = +el.dataset.step;
            el.classList.toggle('active', s === i);
            el.classList.toggle('done', s < i);
            if (s === i) el.setAttribute('aria-current', 'step');
            else el.removeAttribute('aria-current');
        });
    }

    /* ---- Readouts (MOI-driven pressure; model-driven outcome) ---- */
    function updateReadouts() {
        const moi = state.moi;
        let lvl, cls;
        if (moi < 1)      { lvl = 'Low';    cls = 'pressure-low'; }
        else if (moi < 6) { lvl = 'Medium'; cls = 'pressure-med'; }
        else              { lvl = 'High';   cls = 'pressure-high'; }
        const pEl = document.getElementById('metaPressure');
        pEl.textContent = lvl + ' (MOI ' + moi.toFixed(1) + ')';
        pEl.className = cls;
        const sim = activeSim();
        const mo = document.getElementById('metaOutcome');
        if (sim.clearX != null) {
            const hrs = sim.clearX * HMAX;
            mo.textContent = 'Clears in ~' + (hrs < 1.5 ? hrs.toFixed(1) : Math.round(hrs)) + ' h (cells lyse)';
        } else {
            mo.textContent = 'Stays cloudy (lysis held)';
        }
    }

    function resize() {
        dpr = devicePixelRatio || 1;
        W = wrap.offsetWidth - 32;
        H = Math.max(320, Math.min(460, Math.round(window.innerHeight * 0.42)));
        canvas.width = W * dpr;
        canvas.height = H * dpr;
        canvas.style.width = W + 'px';
        canvas.style.height = H + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        draw(playhead);
    }
    window.addEventListener('resize', resize);

    const pad = { top: 28, right: 18, bottom: 46, left: 50 };
    function curvePoint(sim, x, gw, gh) {
        return {
            x: pad.left + x * gw,
            y: pad.top + gh - Math.max(0, Math.min(1, sampleAt(sim, x) / ODMAX)) * gh
        };
    }
    function strokeCurve(sim, color, width, glow, x0, x1) {
        const gw = W - pad.left - pad.right, gh = H - pad.top - pad.bottom;
        if (glow) { ctx.save(); ctx.shadowColor = color; ctx.shadowBlur = 12; }
        ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = width;
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        const N = 200;
        let started = false;
        for (let i = 0; i <= N; i++) {
            const x = i / N;
            if (x < x0 || x > x1) continue;
            const pt = curvePoint(sim, x, gw, gh);
            started ? ctx.lineTo(pt.x, pt.y) : (ctx.moveTo(pt.x, pt.y), started = true);
        }
        ctx.stroke();
        if (glow) ctx.restore();
    }

    // small hexagon (virion)
    function hex(cx, cy, rr) {
        ctx.beginPath();
        for (let a = 0; a < 6; a++) {
            const ang = Math.PI / 6 + a * Math.PI / 3;
            const px = cx + rr * Math.cos(ang), py = cy + rr * Math.sin(ang);
            a === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath();
    }
    // Rod-shaped (capsule) E. coli body. Holin puncturing the membrane doesn't
    // change the cell's shape — only endolysin digesting the wall does, right
    // before spanins complete lysis. So only the true burst frame is rounded.
    function cellBodyPath(cx, cy, R, rounded) {
        ctx.beginPath();
        if (rounded) {
            ctx.arc(cx, cy, R, 0, Math.PI * 2);
        } else {
            const w = R * 2.3, h = R * 1.15, rr = h / 2;
            const x = cx - w / 2, y = cy - h / 2;
            ctx.moveTo(x + rr, y);
            ctx.lineTo(x + w - rr, y);
            ctx.arc(x + w - rr, y + rr, rr, -Math.PI / 2, Math.PI / 2);
            ctx.lineTo(x + rr, y + h);
            ctx.arc(x + rr, y + rr, rr, Math.PI / 2, Math.PI * 1.5);
            ctx.closePath();
        }
    }
    // Comic "pow" starburst, drawn behind the cell at the moment of rupture
    function drawBurstStar(cx, cy, r) {
        const spikes = 8;
        ctx.beginPath();
        for (let i = 0; i < spikes * 2; i++) {
            const ang = (Math.PI / spikes) * i - Math.PI / 2;
            const rr = i % 2 === 0 ? r : r * 0.5;
            const px = cx + Math.cos(ang) * rr, py = cy + Math.sin(ang) * rr;
            i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fillStyle = 'rgba(244,196,48,0.22)';
        ctx.fill();
    }
    // One jagged half of the cracked cell, offset outward from center
    function drawCellHalf(cx, cy, R, side, offX, offY, fillColor) {
        const s = R / 26;
        const zig = [[4, 18], [-4, 10], [4, 2], [-4, -6], [4, -14], [-4, -22]];
        ctx.save();
        ctx.translate(cx + offX, cy + offY);
        ctx.beginPath();
        ctx.moveTo(0, -26 * s);
        ctx.arc(0, 0, 26 * s, -Math.PI / 2, Math.PI / 2, side === 'left');
        for (const [zx, zy] of zig) ctx.lineTo((side === 'left' ? zx : -zx) * s, zy * s);
        ctx.closePath();
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.lineWidth = 1.8;
        ctx.strokeStyle = '#0a1f0f';
        ctx.stroke();
        ctx.restore();
    }
    // The round, wall-less cell splitting in two — this is what endolysin + spanins
    // actually do at rupture (the shape holins alone never touch).
    function drawCrackedCell(cx, cy, R) {
        const s = R / 26;
        drawCellHalf(cx, cy, R, 'left', -5 * s, -3 * s, '#166b34');
        drawCellHalf(cx, cy, R, 'right', 5 * s, 3 * s, '#2bb35f');
    }
    function drawBurstDroplets(cx, cy, R) {
        const s = R / 26;
        ctx.fillStyle = 'rgba(26,128,64,0.85)';
        [[0, 32, 3.4], [10, 36, 2.2], [-12, 34, 1.9]].forEach(([dx, dy, r]) => {
            ctx.beginPath(); ctx.arc(cx + dx * s, cy + dy * s, r * s, 0, Math.PI * 2); ctx.fill();
        });
    }
    // micro cell-state scene in the top-left of the plot
    function drawCellScene(stage) {
        const bx = pad.left + 14, by = pad.top + 12, R = 22, cx = bx + R, cy = by + R;
        ctx.save();
        const isBurst = stage === 4 && state.mode === 'normal';
        if (isBurst) drawBurstStar(cx, cy, R * 1.9);
        // cell body — round only once endolysin has actually acted (the burst frame),
        // drawn as two cracked halves rather than a plain circle
        if (isBurst) {
            drawCrackedCell(cx, cy, R);
        } else {
            cellBodyPath(cx, cy, R, false);
            ctx.fillStyle = 'rgba(26,128,64,0.12)';
            ctx.fill();
            ctx.lineWidth = 1.6;
            ctx.strokeStyle = 'rgba(245,237,216,0.55)';
            if (stage === 3) ctx.setLineDash([3, 3]);
            ctx.stroke(); ctx.setLineDash([]);
        }
        const gold = '#f4c430';
        if (stage === 0) {                       // phage docking — N4 is a podovirus: short stubby tail, no baseplate
            ctx.strokeStyle = gold; ctx.lineWidth = 1.8;
            ctx.beginPath(); ctx.moveTo(cx, cy - R - 11); ctx.lineTo(cx, cy - R - 3); ctx.stroke();
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(cx - 1.5, cy - R - 6); ctx.lineTo(cx - 4, cy - R - 2);
            ctx.moveTo(cx + 1.5, cy - R - 6); ctx.lineTo(cx + 4, cy - R - 2);
            ctx.stroke();
            hex(cx, cy - R - 16, 5); ctx.fillStyle = gold; ctx.fill();
        } else if (stage === 1) {                // DNA squiggle
            ctx.strokeStyle = gold; ctx.lineWidth = 1.6; ctx.beginPath();
            for (let i = 0; i <= 20; i++) { const t = i / 20; const px = cx - 11 + t * 22; const py = cy + Math.sin(t * Math.PI * 4) * 6; i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
            ctx.stroke();
        } else if (stage === 2 || stage === 3) {  // virions filling
            ctx.fillStyle = gold;
            const n = stage === 2 ? 4 : 8;
            for (let i = 0; i < n; i++) { const ang = i / n * Math.PI * 2; const rr = stage === 2 ? 7 : 11; hex(cx + Math.cos(ang) * rr, cy + Math.sin(ang) * rr, 3.2); ctx.fill(); }
        } else if (isBurst) {  // burst: phages spraying out on speed lines, membrane droplets
            const n = 9;
            ctx.strokeStyle = gold; ctx.lineWidth = 1.4; ctx.lineCap = 'round';
            for (let i = 0; i < n; i++) { const ang = i / n * Math.PI * 2; const rr = R + 10; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(ang) * rr, cy + Math.sin(ang) * rr); ctx.stroke(); }
            ctx.fillStyle = gold;
            for (let i = 0; i < n; i++) { const ang = i / n * Math.PI * 2; const rr = R + 10; hex(cx + Math.cos(ang) * rr, cy + Math.sin(ang) * rr, 3); ctx.fill(); }
            drawBurstDroplets(cx, cy, R);
        } else if (stage === 4) {                 // N4 held: stuffed + superinfecting phages
            ctx.fillStyle = gold;
            for (let i = 0; i < 9; i++) { const ang = i / 9 * Math.PI * 2; hex(cx + Math.cos(ang) * 11, cy + Math.sin(ang) * 11, 3.2); ctx.fill(); }
            ctx.strokeStyle = '#d4324b'; ctx.lineWidth = 1.6;
            [[-1, -1], [1, -1]].forEach(([sx, sy]) => { ctx.beginPath(); ctx.moveTo(cx + sx * (R + 14), cy + sy * (R + 10)); ctx.lineTo(cx + sx * (R + 2), cy + sy * (R - 2)); ctx.stroke(); });
        }
        ctx.restore();
    }

    let playhead = 1, headVisible = false, currentStage = 0;   // narration stage is independent of curve reveal
    function draw(progress, showHead) {
        playhead = progress;
        if (showHead !== undefined) headVisible = showHead;
        ctx.clearRect(0, 0, W, H);
        const gw = W - pad.left - pad.right, gh = H - pad.top - pad.bottom;

        // grid (no numeric labels)
        ctx.strokeStyle = 'rgba(244, 196, 48, 0.06)'; ctx.lineWidth = 1;
        for (let i = 1; i < 5; i++) { const y = pad.top + (gh / 5) * i; ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke(); }
        for (let hh = 1; hh < HMAX; hh++) { const x = pad.left + (gw / HMAX) * hh; ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, H - pad.bottom); ctx.stroke(); }
        // axes
        ctx.strokeStyle = 'rgba(245, 237, 216, 0.25)';
        ctx.beginPath(); ctx.moveTo(pad.left, pad.top); ctx.lineTo(pad.left, H - pad.bottom); ctx.lineTo(W - pad.right, H - pad.bottom); ctx.stroke();
        // x-axis hour ticks + labels
        ctx.fillStyle = 'rgba(245, 237, 216, 0.42)'; ctx.font = '9px JetBrains Mono, monospace'; ctx.textAlign = 'center';
        for (let hh = 0; hh <= HMAX; hh++) ctx.fillText(hh + 'h', pad.left + (gw / HMAX) * hh, H - pad.bottom + 14);
        // axis labels (arrow for time)
        ctx.fillStyle = 'rgba(245, 237, 216, 0.5)'; ctx.font = '11px JetBrains Mono, monospace'; ctx.textAlign = 'center';
        ctx.fillText('time post-infection →', pad.left + gw / 2, H - 10);
        ctx.save(); ctx.translate(15, pad.top + gh / 2); ctx.rotate(-Math.PI / 2);
        ctx.fillText('culture turbidity (OD₆₀₀) →', 0, 0); ctx.restore();

        const inhActive = state.mode === 'inhibited';
        // inactive curves faint; control always faint
        strokeCurve(simControl, 'rgba(26,128,64,0.40)', 2, false, 0, 1);
        strokeCurve(simNormal, inhActive ? 'rgba(244,196,48,0.28)' : 'rgba(244,196,48,0.30)', 2, false, 0, 1);
        strokeCurve(simInhib, inhActive ? 'rgba(196,30,58,0.30)' : 'rgba(196,30,58,0.28)', 2, false, 0, 1);
        // active curve, revealed up to playhead, glowing
        const sim = activeSim();
        const activeColor = inhActive ? '#d4324b' : '#f4c430';
        strokeCurve(sim, activeColor, 3, true, 0, progress);

        // decision marker (vertical) at lysis timing
        const lx = Math.min(0.95, activeSim().lysisX);
        const mx = pad.left + lx * gw;
        ctx.strokeStyle = 'rgba(245,237,216,0.28)'; ctx.setLineDash([3, 4]); ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(mx, pad.top + 4); ctx.lineTo(mx, H - pad.bottom); ctx.stroke(); ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(245,237,216,0.45)'; ctx.font = '9px JetBrains Mono, monospace';
        ctx.textAlign = lx > 0.8 ? 'right' : 'left';
        ctx.fillText('lysis decision', mx + (lx > 0.8 ? -5 : 5), pad.top + 12);

        // playhead dot on active curve (only while playing / after scrubbing)
        if (headVisible) {
            const pt = curvePoint(sim, progress, gw, gh);
            ctx.save(); ctx.shadowColor = activeColor; ctx.shadowBlur = 16;
            ctx.beginPath(); ctx.arc(pt.x, pt.y, 5.5, 0, Math.PI * 2); ctx.fillStyle = activeColor; ctx.fill();
            ctx.restore();
            ctx.beginPath(); ctx.arc(pt.x, pt.y, 2.2, 0, Math.PI * 2); ctx.fillStyle = '#fff8e0'; ctx.fill();
        }

        drawCellScene(currentStage);
    }

    /* ---- Animation ---- */
    let raf = null;
    const playBtn = document.getElementById('pgPlay');
    function stop() {
        if (raf) cancelAnimationFrame(raf), raf = null;
        playBtn.classList.remove('playing');
        playBtn.textContent = '▶ Play infection';
    }
    function play() {
        stop();
        playBtn.classList.add('playing');
        playBtn.textContent = '⏸ Replay';
        const dur = 6500; const t0 = performance.now();
        let lastStage = -1;
        (function frame(now) {
            const x = Math.min(1, (now - t0) / dur);
            draw(x, true);
            const s = stageAt(x);
            if (s !== lastStage) { setStage(s); lastStage = s; }
            if (x < 1) raf = requestAnimationFrame(frame);
            else stop();
        })(t0);
    }
    function scrub(x) { draw(x, true); setStage(stageAt(x)); }
    playBtn.addEventListener('click', () => { raf ? (stop(), scrub(1)) : play(); });

    /* ---- Controls ---- */
    function latentLabel(v) { return v < 28 ? 'Early' : v < 45 ? 'Mid' : v < 62 ? 'Late' : 'Very late'; }
    function refresh() {
        recompute();
        updateReadouts();
        if (!raf) { draw(1, false); }
    }
    function bind(id, key) {
        const el = document.getElementById(id);
        const val = document.getElementById('val' + id.replace('ctrl', ''));
        const upd = () => {
            stop();
            state[key] = parseFloat(el.value);
            const pct = ((parseFloat(el.value) - parseFloat(el.min)) / (parseFloat(el.max) - parseFloat(el.min))) * 100;
            el.style.setProperty('--p', pct + '%');
            if (val) {
                if (id === 'ctrlLatent') val.textContent = latentLabel(state.latent);
                else if (id === 'ctrlInhibit') val.textContent = state.inhibit + '%';
                else if (id === 'ctrlBurst') val.textContent = Math.round(state.burst);
                else if (id === 'ctrlMOI') val.textContent = state.moi.toFixed(1);
            }
            refresh();
        };
        el.addEventListener('input', upd);
        upd();
    }

    const presetN4 = document.getElementById('presetN4');
    const presetNormal = document.getElementById('presetNormal');
    function setMode(mode) {
        stop();
        state.mode = mode;
        presetN4.classList.toggle('active', mode === 'inhibited');
        presetNormal.classList.toggle('active', mode === 'normal');
        if (mode === 'inhibited') {
            document.getElementById('ctrlInhibit').value = 70; state.inhibit = 70;
            document.getElementById('ctrlBurst').value = 1500; state.burst = 1500;
            document.getElementById('ctrlLatent').value = 35; state.latent = 35;
        } else {
            document.getElementById('ctrlInhibit').value = 0; state.inhibit = 0;
            document.getElementById('ctrlBurst').value = 200; state.burst = 200;
            document.getElementById('ctrlLatent').value = 28; state.latent = 28;
        }
        buildStepper();
        ['ctrlLatent', 'ctrlInhibit', 'ctrlBurst', 'ctrlMOI'].forEach(id =>
            document.getElementById(id).dispatchEvent(new Event('input')));
        setStage(0);
    }
    presetN4.addEventListener('click', () => setMode('inhibited'));
    presetNormal.addEventListener('click', () => setMode('normal'));

    buildStepper();
    setStage(0);
    bind('ctrlLatent', 'latent');
    bind('ctrlInhibit', 'inhibit');
    bind('ctrlBurst', 'burst');
    bind('ctrlMOI', 'moi');
    resize();
})();
