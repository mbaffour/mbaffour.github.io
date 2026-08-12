/* ==============================================================
   TAILFIBER — playable mini-game v2
   Real-phage character select, duration choice, 4 receptors,
   difficulty levels, stats tracking, biology results screen,
   virtual joystick for touch.
=============================================================== */
(function() {
    const wrap = document.getElementById('tfWrap');
    if (!wrap) return;
    const canvas = document.getElementById('tfCanvas');
    const ctx = canvas.getContext('2d');
    const overlay = document.getElementById('tfOverlay');
    const overlayCard = document.getElementById('tfOverlayCard');
    const scoreEl = document.getElementById('tfScore');
    const lysesEl = document.getElementById('tfLyses');
    const timeEl  = document.getElementById('tfTime');
    const timeLabelEl = document.getElementById('tfTimeLabel');
    const hpFill  = document.getElementById('tfHpFill');
    const levelEl = document.getElementById('tfLevel');
    const pauseBtn = document.getElementById('tfPauseBtn');
    const fullBtn = document.getElementById('tfFullBtn');
    const fiberBtns = document.querySelectorAll('.tf-fiber-btn');
    const toast   = document.getElementById('tfToast');
    const joystick = document.getElementById('tfJoystick');
    const joyThumb = document.getElementById('tfJoyThumb');
    const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

    const RECEPTORS = {
        lps:  { name: 'LPS',  color: '#f4c430', glow: 'rgba(244,196,48,0.45)' },
        ompc: { name: 'OmpC', color: '#4cc97d', glow: 'rgba(76,201,125,0.45)' },
        lamb: { name: 'LamB', color: '#ff6b8a', glow: 'rgba(255,107,138,0.45)' },
        pili: { name: 'Pili', color: '#4cb8ff', glow: 'rgba(76,184,255,0.45)' },
        nfra: { name: 'NfrA', color: '#c084fc', glow: 'rgba(192,132,252,0.45)' }
    };
    const FIBER_KEYS = ['lps', 'ompc', 'lamb', 'pili'];

    // Phage characters — each with real-biology flavor
    const PHAGES = {
        generic: {
            name: 'φ-Generic', short: 'Generic',
            preferred: 'lps',
            speed: 1.0, hpMax: 100, burstBonus: 0, immuneRes: 1.0,
            bonus: '', lore: 'A versatile coliphage — no specialty, balanced stats. Good for learning.'
        },
        t4: {
            name: 'T4', short: 'T4',
            preferred: 'lps',
            speed: 0.95, hpMax: 110, burstBonus: 30, immuneRes: 0.9,
            bonus: 'Long tail fibers reversibly bind LPS; short tail fibers lock in at the baseplate.',
            lore: 'T4: large myovirus with contractile tail. Long tail fibers recognize LPS on E. coli; irreversible binding follows at the baseplate. Big, tough, hard to miss.'
        },
        lambda: {
            name: 'λ (Lambda)', short: 'λ',
            preferred: 'lamb',
            speed: 1.15, hpMax: 85, burstBonus: 10, immuneRes: 1.0,
            bonus: 'J-protein tip targets LamB (maltoporin); fast and precise adsorption.',
            lore: 'Lambda: temperate siphovirus. The J-protein at the tail tip binds LamB (maltoporin) on E. coli K-12. Fast, surgical, and sometimes goes lysogenic.'
        },
        n4: {
            name: 'N4', short: 'N4',
            preferred: 'nfra',
            speed: 0.9, hpMax: 100, burstBonus: 80, immuneRes: 1.0,
            bonus: 'Binds NfrA — a rare outer membrane receptor. Lysis-inhibited: bigger burst per lyse.',
            lore: 'N4: podovirus that uses NfrA on the outer membrane of E. coli as its primary receptor. Delays lysis to maximize burst size — each lyse scores bigger.'
        },
        icp1: {
            name: 'ICP1', short: 'ICP1',
            preferred: 'lps',
            speed: 1.10, hpMax: 95, burstBonus: 20, immuneRes: 0.65,
            bonus: 'Targets O-antigen (LPS) on V. cholerae. Anti-CRISPR genes cut immune damage.',
            lore: 'ICP1: myovirus that infects Vibrio cholerae O1 by binding the O-antigen of LPS. Carries anti-CRISPR genes — takes less damage from host defenses.'
        }
    };
    const PHAGE_KEYS = ['generic', 't4', 'lambda', 'n4', 'icp1'];

    const DURATIONS = [
        { key: 30,   label: '30s' },
        { key: 60,   label: '1 min' },
        { key: 120,  label: '2 min' },
        { key: 300,  label: '5 min' },
        { key: 0,    label: '∞' }
    ];

    const TIPS = [
        'Match your tail fiber color to the receptor on the bacterium.',
        'Y-shapes are antibodies — neutralize on contact.',
        'Press 1/2/3/4 (or tap) to swap tail fiber type.',
        'Red blobs are macrophages — they engulf and damage you.',
        'Each correct dock = +100, +HP regen, and burst progeny.',
        'Level up every 30s — more receptor variety, faster antibodies.'
    ];

    let W, H, dpr;
    let state = 'setup'; // setup | playing | paused | over
    let player, bacteria, antibodies, macrophages, particles;
    let score, hp, lyses, missed, neutralized, macHits, dockAttempts, timeLeft, elapsed;
    let level = 1;
    let chosenPhage = 'generic';
    let chosenDuration = 60;
    let spawnT, abSpawnT, macSpawnT, tipT, tipIdx, levelT;
    let lastT = 0, rafId = null;
    const keys = {};
    const pointer = { x: 0, y: 0, active: false };
    const joy = { active: false, dx: 0, dy: 0, cx: 0, cy: 0 };
    let currentFiber = 'lps';
    let shakeT = 0;

    function resize() {
        dpr = devicePixelRatio || 1;
        const r = canvas.getBoundingClientRect();
        W = r.width; H = r.height;
        canvas.width = W * dpr; canvas.height = H * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function rand(min, max) { return min + Math.random() * (max - min); }
    function dist2(a, b) { const dx = a.x - b.x, dy = a.y - b.y; return dx * dx + dy * dy; }

    // ===== Entities =====
    function makePlayer() {
        const p = PHAGES[chosenPhage];
        return {
            x: W / 2, y: H / 2,
            vx: 0, vy: 0,
            size: 11,
            speed: 0.42 * p.speed,
            friction: 0.92,
            rot: 0,
            invuln: 0
        };
    }
    function activeReceptorsForLevel() {
        // Level 1: 3 receptors. Level 2: add Pili. Level 3+: add NfrA.
        if (level === 1) return ['lps', 'ompc', 'lamb'];
        if (level === 2) return ['lps', 'ompc', 'lamb', 'pili'];
        return ['lps', 'ompc', 'lamb', 'pili', 'nfra'];
    }
    function makeBacterium() {
        const margin = 60;
        const x = rand(margin, W - margin);
        const y = rand(margin, H - margin);
        const pool = activeReceptorsForLevel();
        const receptor = pool[Math.floor(Math.random() * pool.length)];
        return {
            x, y,
            vx: rand(-0.06, 0.06),
            vy: rand(-0.06, 0.06),
            len: rand(34, 46),
            rad: 12,
            rot: rand(0, Math.PI * 2),
            rotSpeed: rand(-0.002, 0.002),
            receptor,
            pulse: 0,
            hp: 1
        };
    }
    function makeAntibody() {
        const side = Math.floor(Math.random() * 4);
        let x, y, vx, vy;
        const sp = rand(0.30, 0.55) * (1 + (level - 1) * 0.18);
        if (side === 0)      { x = -20;     y = rand(0, H); vx = sp;  vy = rand(-0.1, 0.1); }
        else if (side === 1) { x = W + 20;  y = rand(0, H); vx = -sp; vy = rand(-0.1, 0.1); }
        else if (side === 2) { x = rand(0, W); y = -20;     vx = rand(-0.1, 0.1); vy = sp; }
        else                 { x = rand(0, W); y = H + 20;  vx = rand(-0.1, 0.1); vy = -sp; }
        return { x, y, vx, vy, size: 10, rot: rand(0, Math.PI * 2), rotSpeed: rand(-0.02, 0.02) };
    }
    function makeMacrophage() {
        const x = Math.random() < 0.5 ? -40 : W + 40;
        const y = rand(40, H - 40);
        return { x, y, vx: 0, vy: 0, size: 28, speed: 0.16 + level * 0.02, wobble: 0 };
    }
    function makeParticle(x, y, color, opts = {}) {
        return {
            x, y,
            vx: opts.vx ?? rand(-1.2, 1.2),
            vy: opts.vy ?? rand(-1.2, 1.2),
            size: opts.size ?? rand(2, 4),
            color,
            life: opts.life ?? rand(0.6, 1.2),
            age: 0,
            kind: opts.kind || 'spark'
        };
    }

    // ===== UI helpers =====
    function showToast(msg, ms = 2500) {
        toast.textContent = msg;
        toast.classList.add('show');
        clearTimeout(showToast._t);
        showToast._t = setTimeout(() => toast.classList.remove('show'), ms);
    }
    function setFiber(key) {
        currentFiber = key;
        fiberBtns.forEach(b => b.classList.toggle('active', b.dataset.fiber === currentFiber));
        showToast(`Tail fiber: ${RECEPTORS[key].name}`, 1200);
    }
    function updateHP() {
        const pct = Math.max(0, (hp / PHAGES[chosenPhage].hpMax) * 100);
        hpFill.style.width = pct + '%';
        hpFill.classList.toggle('low', pct < 50);
        hpFill.classList.toggle('critical', pct < 25);
    }
    function setLevel(n) {
        if (level === n) return;
        level = n;
        levelEl.textContent = `LVL ${n}`;
        levelEl.classList.add('bump');
        setTimeout(() => levelEl.classList.remove('bump'), 600);
        const msgs = {
            2: 'Level 2 — Type IV pili emerge. Faster antibodies.',
            3: 'Level 3 — NfrA receptors appear. Macrophages on patrol.',
            4: 'Level 4 — Maximum immune pressure.'
        };
        if (msgs[n]) showToast(msgs[n], 2800);
    }

    // ===== Screens (overlay content swap) =====
    function renderSetup() {
        const p = PHAGES[chosenPhage];
        overlayCard.innerHTML = `
            <div class="tf-setup">
                <h4 class="tf-setup-title">TailFiber</h4>
                <div class="tf-setup-sub">A scientifically-grounded phage simulator</div>

                <div class="tf-setup-group">
                    <label class="tf-setup-label">Pick your phage</label>
                    <div class="tf-phage-grid">
                        ${PHAGE_KEYS.map(k => `
                            <button class="tf-phage-opt ${k === chosenPhage ? 'active' : ''}" data-phage="${k}">
                                <span class="tf-phage-name">${PHAGES[k].short}</span>
                                <span class="tf-phage-stat">${PHAGES[k].preferred.toUpperCase()}</span>
                            </button>
                        `).join('')}
                    </div>
                    <div class="tf-phage-lore" id="tfPhageLore">${p.lore}</div>
                </div>

                <div class="tf-setup-group">
                    <label class="tf-setup-label">Duration</label>
                    <div class="tf-dur-grid">
                        ${DURATIONS.map(d => `
                            <button class="tf-dur-opt ${d.key === chosenDuration ? 'active' : ''}" data-dur="${d.key}">${d.label}</button>
                        `).join('')}
                    </div>
                </div>

                <div class="tf-overlay-keys">
                    <span><kbd>↑↓←→</kbd> move</span>
                    <span><kbd>1</kbd><kbd>2</kbd><kbd>3</kbd><kbd>4</kbd> fiber</span>
                    <span><kbd>P</kbd> pause</span>
                </div>

                <button class="tf-btn-play" id="tfPlay">▶ Play</button>
            </div>
        `;

        // Wire up
        overlayCard.querySelectorAll('.tf-phage-opt').forEach(btn => {
            btn.addEventListener('click', () => {
                chosenPhage = btn.dataset.phage;
                overlayCard.querySelectorAll('.tf-phage-opt').forEach(b => b.classList.toggle('active', b.dataset.phage === chosenPhage));
                document.getElementById('tfPhageLore').textContent = PHAGES[chosenPhage].lore;
            });
        });
        overlayCard.querySelectorAll('.tf-dur-opt').forEach(btn => {
            btn.addEventListener('click', () => {
                chosenDuration = parseInt(btn.dataset.dur, 10);
                overlayCard.querySelectorAll('.tf-dur-opt').forEach(b => b.classList.toggle('active', parseInt(b.dataset.dur, 10) === chosenDuration));
            });
        });
        document.getElementById('tfPlay').addEventListener('click', startGame);
    }

    function renderPaused() {
        overlayCard.innerHTML = `
            <h4 class="tf-overlay-title">Paused</h4>
            <p class="tf-overlay-text">Take a breath. Press <kbd>P</kbd> or click resume.</p>
            <button class="tf-btn-play" id="tfResume">▶ Resume</button>
            <button class="tf-btn-secondary" id="tfQuit" style="margin-top:0.5rem">↺ Quit run</button>
        `;
        document.getElementById('tfResume').addEventListener('click', resumeGame);
        document.getElementById('tfQuit').addEventListener('click', () => {
            state = 'setup';
            renderSetup();
        });
    }

    function renderResults() {
        const acc = dockAttempts > 0 ? Math.round((lyses / dockAttempts) * 100) : 0;
        const timePlayed = chosenDuration === 0
            ? `${Math.floor(elapsed)}s survived`
            : `${chosenDuration - Math.ceil(timeLeft)}s of ${chosenDuration}s`;
        const p = PHAGES[chosenPhage];

        // Educational explanation tuned to playstyle
        let bio;
        if (lyses === 0) {
            bio = `<strong>Adsorption failed</strong>. In real phage biology, this is what happens when the tail fibers can't recognize a host receptor. <strong>${p.short}</strong> prefers <strong>${RECEPTORS[p.preferred].name}</strong> — try keeping that fiber active and looking for matching bacteria.`;
        } else if (acc >= 80 && lyses >= 5) {
            bio = `<strong>High adsorption efficiency.</strong> ${lyses} successful dockings at ${acc}% accuracy means your tail fibers recognized the right receptors quickly — the kind of specificity that gives real phages narrow but devastating host ranges.`;
        } else if (missed > lyses) {
            bio = `<strong>Receptor mismatch.</strong> You attempted to dock on the wrong receptor more often than not. In nature this would just be a bounce — phage tail fibers are specific to one or two host molecules (LPS, OmpC, LamB, pili).`;
        } else if (neutralized >= 4) {
            bio = `<strong>Heavy neutralization.</strong> ${neutralized} antibody hits — IgG and IgM antibodies coat phages and prevent adsorption. Phage therapy in vivo has to contend with this.`;
        } else {
            bio = `<strong>Solid run.</strong> ${lyses} successful lyses with ${neutralized} antibody hits. ${p.short} ${p.bonus || 'kept docking despite the immune barriers'}.`;
        }

        overlayCard.innerHTML = `
            <h4 class="tf-overlay-title">${lyses >= 15 ? 'Phage Therapy Success' : lyses >= 8 ? 'Productive Infection' : 'Run Complete'}</h4>
            <p class="tf-overlay-text">${p.short} · ${timePlayed}</p>

            <div class="tf-results-grid">
                <div class="tf-result-cell"><span class="tf-result-key">Score</span><span class="tf-result-val">${score}</span></div>
                <div class="tf-result-cell"><span class="tf-result-key">Lyses</span><span class="tf-result-val">${lyses}</span></div>
                <div class="tf-result-cell"><span class="tf-result-key">Accuracy</span><span class="tf-result-val">${acc}%</span></div>
                <div class="tf-result-cell"><span class="tf-result-key">Mismatched docks</span><span class="tf-result-val">${missed}</span></div>
                <div class="tf-result-cell"><span class="tf-result-key">Antibody hits</span><span class="tf-result-val">${neutralized}</span></div>
                <div class="tf-result-cell"><span class="tf-result-key">Macrophage hits</span><span class="tf-result-val">${macHits}</span></div>
            </div>

            <div class="tf-bio-explain">${bio}</div>

            <div class="tf-result-actions">
                <button class="tf-btn-play" id="tfReplay">▶ Play again</button>
                <button class="tf-btn-secondary" id="tfChange">↺ Change phage</button>
            </div>
        `;
        document.getElementById('tfReplay').addEventListener('click', startGame);
        document.getElementById('tfChange').addEventListener('click', () => {
            state = 'setup';
            renderSetup();
        });
    }

    // ===== Game lifecycle =====
    function startGame() {
        player = makePlayer();
        const p = PHAGES[chosenPhage];
        bacteria = []; antibodies = []; macrophages = []; particles = [];
        score = 0; hp = p.hpMax; lyses = 0;
        missed = 0; neutralized = 0; macHits = 0; dockAttempts = 0;
        timeLeft = chosenDuration; elapsed = 0;
        level = 1;
        spawnT = 0; abSpawnT = 2; macSpawnT = 28;
        tipT = 5; tipIdx = 0; levelT = 30;
        currentFiber = p.preferred;
        fiberBtns.forEach(b => b.classList.toggle('active', b.dataset.fiber === currentFiber));
        updateHP();
        levelEl.textContent = 'LVL 1';
        scoreEl.textContent = '0';
        lysesEl.textContent = '0';
        timeLabelEl.textContent = chosenDuration === 0 ? 'TIME' : 'TIME';
        timeEl.textContent = chosenDuration === 0 ? '0' : chosenDuration;
        for (let i = 0; i < 4; i++) bacteria.push(makeBacterium());
        state = 'playing';
        overlay.classList.add('hidden');
        wrap.focus();
        lastT = performance.now();
        if (rafId) cancelAnimationFrame(rafId);
        tick(lastT);
    }
    function endGame() {
        state = 'over';
        renderResults();
        overlay.classList.remove('hidden');
    }
    function pauseGame() {
        if (state !== 'playing') return;
        state = 'paused';
        renderPaused();
        overlay.classList.remove('hidden');
    }
    function resumeGame() {
        state = 'playing';
        overlay.classList.add('hidden');
        lastT = performance.now();
        tick(lastT);
    }

    function hurt(amount, source) {
        if (player.invuln > 0) return;
        const p = PHAGES[chosenPhage];
        const actual = amount * p.immuneRes;
        hp = Math.max(0, hp - actual);
        player.invuln = 0.6;
        wrap.classList.add('hurt');
        shakeT = 0.25;
        setTimeout(() => wrap.classList.remove('hurt'), 320);
        if (source === 'antibody') neutralized++;
        else if (source === 'macrophage') macHits++;
        updateHP();
        if (hp <= 0) endGame();
    }

    // ===== Update loop =====
    function update(dt) {
        elapsed += dt;

        // Time
        if (chosenDuration > 0) {
            timeLeft -= dt;
            if (timeLeft <= 0) { timeLeft = 0; endGame(); return; }
            timeEl.textContent = Math.ceil(timeLeft);
        } else {
            timeEl.textContent = Math.floor(elapsed);
        }

        // Level progression every 30s
        levelT -= dt;
        if (levelT <= 0) {
            setLevel(level + 1);
            levelT = 30;
        }

        // Player input
        let dx = 0, dy = 0;
        if (keys['ArrowLeft']  || keys['a'] || keys['A']) dx -= 1;
        if (keys['ArrowRight'] || keys['d'] || keys['D']) dx += 1;
        if (keys['ArrowUp']    || keys['w'] || keys['W']) dy -= 1;
        if (keys['ArrowDown']  || keys['s'] || keys['S']) dy += 1;
        if (pointer.active) {
            const px = pointer.x - player.x;
            const py = pointer.y - player.y;
            const d = Math.hypot(px, py);
            if (d > 8) { dx += px / d; dy += py / d; }
        }
        if (joy.active) {
            dx += joy.dx;
            dy += joy.dy;
        }
        const mag = Math.hypot(dx, dy);
        if (mag > 0) {
            dx /= mag; dy /= mag;
            player.vx += dx * player.speed;
            player.vy += dy * player.speed;
        }
        player.vx *= player.friction;
        player.vy *= player.friction;
        player.x += player.vx;
        player.y += player.vy;
        const m = player.size;
        if (player.x < m) { player.x = m; player.vx *= -0.4; }
        if (player.x > W - m) { player.x = W - m; player.vx *= -0.4; }
        if (player.y < m) { player.y = m; player.vy *= -0.4; }
        if (player.y > H - m) { player.y = H - m; player.vy *= -0.4; }
        if (Math.abs(player.vx) > 0.05 || Math.abs(player.vy) > 0.05) {
            player.rot = Math.atan2(player.vy, player.vx);
        }
        player.invuln = Math.max(0, player.invuln - dt);

        // Bacteria: drift, gentle attraction toward player when near
        bacteria.forEach(b => {
            b.x += b.vx; b.y += b.vy; b.rot += b.rotSpeed; b.pulse += dt * 2;
            if (b.x < 20 || b.x > W - 20) b.vx *= -1;
            if (b.y < 20 || b.y > H - 20) b.vy *= -1;
            const px = player.x - b.x, py = player.y - b.y;
            const d = Math.hypot(px, py);
            if (d < 70 && d > 0) {
                b.vx += (px / d) * 0.004;
                b.vy += (py / d) * 0.004;
            }
            // Collision
            const r = (player.size + b.rad) * 0.95;
            if (dist2(player, b) < r * r) {
                dockAttempts++;
                if (b.receptor === currentFiber) {
                    const p = PHAGES[chosenPhage];
                    const burstBase = 100;
                    score += burstBase + p.burstBonus;
                    lyses++;
                    scoreEl.textContent = score;
                    lysesEl.textContent = lyses;
                    hp = Math.min(p.hpMax, hp + 6); updateHP();
                    const c = RECEPTORS[b.receptor].color;
                    const burstCount = 18 + Math.min(20, Math.floor(p.burstBonus / 5));
                    for (let i = 0; i < burstCount; i++) {
                        particles.push(makeParticle(b.x, b.y, c, { life: rand(0.5, 1.0), kind: 'phage', size: rand(2, 4) }));
                    }
                    b.hp = 0;
                    if (lyses === 3) showToast('Tip: swap fibers with 1/2/3/4.', 2400);
                    if (lyses === 6) showToast('Tip: avoid the Y-shaped antibodies.', 2400);
                    if (lyses === 10) showToast('Excellent adsorption efficiency!', 2400);
                } else {
                    missed++;
                    const a = Math.atan2(player.y - b.y, player.x - b.x);
                    player.vx += Math.cos(a) * 2.2;
                    player.vy += Math.sin(a) * 2.2;
                    if (player.invuln <= 0) {
                        showToast(`Wrong fiber — need ${RECEPTORS[b.receptor].name}`, 1400);
                        player.invuln = 0.25;
                    }
                }
            }
        });
        bacteria = bacteria.filter(b => b.hp > 0);

        // Spawn bacteria
        spawnT -= dt;
        const maxBact = 5 + Math.min(3, level - 1);
        if (spawnT <= 0 && bacteria.length < maxBact) {
            bacteria.push(makeBacterium());
            spawnT = rand(1.6, 2.8) - (level - 1) * 0.15;
        }

        // Antibodies — home toward player
        antibodies.forEach(a => {
            a.x += a.vx; a.y += a.vy; a.rot += a.rotSpeed;
            const px = player.x - a.x, py = player.y - a.y;
            const d = Math.hypot(px, py);
            if (d < 200) {
                a.vx += (px / d) * 0.005;
                a.vy += (py / d) * 0.005;
            }
            const r = (player.size + a.size) * 0.7;
            if (dist2(player, a) < r * r) {
                hurt(12, 'antibody');
                a.dead = true;
                for (let i = 0; i < 6; i++) particles.push(makeParticle(a.x, a.y, '#c4a8ff', { life: 0.5 }));
            }
        });
        antibodies = antibodies.filter(a => !a.dead && a.x > -60 && a.x < W + 60 && a.y > -60 && a.y < H + 60);
        abSpawnT -= dt;
        if (abSpawnT <= 0) {
            antibodies.push(makeAntibody());
            const intensity = Math.min(1, elapsed / 90);
            abSpawnT = Math.max(0.6, rand(1.4, 3.5) - intensity * 1.2 - (level - 1) * 0.3);
        }

        // Macrophages — from level 3 onwards, or 60s in
        macSpawnT -= dt;
        const macActive = level >= 3 || elapsed > 55;
        if (macSpawnT <= 0 && macrophages.length < 2 && macActive) {
            macrophages.push(makeMacrophage());
            macSpawnT = rand(22, 34) - (level - 1) * 2;
            showToast('⚠ Macrophage incoming!', 2200);
        }
        macrophages.forEach(mac => {
            const px = player.x - mac.x, py = player.y - mac.y;
            const d = Math.hypot(px, py);
            if (d > 0) { mac.vx = (px / d) * mac.speed; mac.vy = (py / d) * mac.speed; }
            mac.x += mac.vx; mac.y += mac.vy;
            mac.wobble += dt * 3;
            const r = (player.size + mac.size) * 0.7;
            if (dist2(player, mac) < r * r) hurt(18, 'macrophage');
        });

        // Particles
        particles.forEach(p => {
            p.age += dt;
            p.x += p.vx; p.y += p.vy;
            p.vx *= 0.96; p.vy *= 0.96;
        });
        particles = particles.filter(p => p.age < p.life);

        // Cycling tips
        tipT -= dt;
        if (tipT <= 0) {
            showToast(TIPS[tipIdx % TIPS.length], 3200);
            tipIdx++;
            tipT = 18;
        }

        shakeT = Math.max(0, shakeT - dt);
    }

    // ===== Render =====
    function drawPlayer() {
        const c = RECEPTORS[currentFiber].color;
        ctx.save();
        ctx.translate(player.x, player.y);
        ctx.rotate(player.rot + Math.PI / 2);
        const s = player.size;
        ctx.beginPath();
        for (let i = 0; i < 6; i++) {
            const a = (Math.PI * 2 / 6) * i - Math.PI / 2;
            const px = Math.cos(a) * s * 0.7;
            const py = Math.sin(a) * s * 0.7;
            i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fillStyle = `${c}cc`; ctx.fill();
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = c;
        ctx.shadowColor = c;
        ctx.shadowBlur = player.invuln > 0 ? 0 : 8;
        ctx.stroke();
        ctx.shadowBlur = 0;
        if (chosenPhage === 'n4') {
            // N4 is a podovirus: short, stubby non-contractile tail, no baseplate
            // or long tail fibers — just a stub with a couple of short fiber tips.
            ctx.beginPath();
            ctx.moveTo(0, s * 0.7); ctx.lineTo(0, s * 0.95);
            ctx.lineWidth = 2.2; ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(-s * 0.12, s * 0.88); ctx.lineTo(-s * 0.32, s * 1.02);
            ctx.moveTo(s * 0.12, s * 0.88); ctx.lineTo(s * 0.32, s * 1.02);
            ctx.lineWidth = 1.3; ctx.stroke();
        } else {
            ctx.beginPath();
            ctx.moveTo(0, s * 0.7); ctx.lineTo(0, s * 1.6);
            ctx.lineWidth = 1.5; ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(-s * 0.4, s * 1.5); ctx.lineTo(s * 0.4, s * 1.5);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, s * 1.6); ctx.lineTo(-s * 0.8, s * 2.2);
            ctx.moveTo(0, s * 1.6); ctx.lineTo(s * 0.8, s * 2.2);
            ctx.lineWidth = 1.4; ctx.stroke();
        }
        if (player.invuln > 0 && Math.floor(player.invuln * 20) % 2 === 0) {
            ctx.globalAlpha = 0.3;
            ctx.fillStyle = '#fff';
            ctx.beginPath();
            ctx.arc(0, 0, s * 0.7, 0, Math.PI * 2);
            ctx.fill();
            ctx.globalAlpha = 1;
        }
        ctx.restore();
    }

    function drawBacterium(b) {
        const rec = RECEPTORS[b.receptor];
        ctx.save();
        ctx.translate(b.x, b.y);
        ctx.rotate(b.rot);
        const len = b.len, rad = b.rad;
        const grd = ctx.createLinearGradient(-len/2, 0, len/2, 0);
        grd.addColorStop(0, 'rgba(26, 128, 64, 0.25)');
        grd.addColorStop(1, 'rgba(26, 128, 64, 0.10)');
        ctx.beginPath();
        ctx.moveTo(-len/2 + rad, -rad);
        ctx.lineTo(len/2 - rad, -rad);
        ctx.arc(len/2 - rad, 0, rad, -Math.PI/2, Math.PI/2);
        ctx.lineTo(-len/2 + rad, rad);
        ctx.arc(-len/2 + rad, 0, rad, Math.PI/2, Math.PI*1.5);
        ctx.closePath();
        ctx.fillStyle = grd; ctx.fill();
        ctx.strokeStyle = '#1a8040'; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.shadowColor = rec.glow;
        ctx.shadowBlur = 12 + Math.sin(b.pulse) * 3;
        ctx.fillStyle = rec.color;
        for (let i = -1; i <= 1; i++) {
            ctx.beginPath();
            ctx.arc(i * (len/3 - 4), 0, 3.2, 0, Math.PI * 2);
            ctx.fill();
        }
        // Pili decoration if this is a pili bacterium
        if (b.receptor === 'pili') {
            ctx.shadowBlur = 0;
            ctx.strokeStyle = rec.color;
            ctx.lineWidth = 1;
            for (let i = -1; i <= 1; i++) {
                ctx.beginPath();
                ctx.moveTo(i * (len/3 - 4), -rad);
                ctx.lineTo(i * (len/3 - 4) + (i || 1) * 4, -rad - 6);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(i * (len/3 - 4), rad);
                ctx.lineTo(i * (len/3 - 4) + (i || 1) * 4, rad + 6);
                ctx.stroke();
            }
        }
        ctx.shadowBlur = 0;
        ctx.restore();
        ctx.save();
        ctx.font = 'bold 9px JetBrains Mono, monospace';
        ctx.fillStyle = rec.color;
        ctx.textAlign = 'center';
        ctx.globalAlpha = 0.85;
        ctx.fillText(rec.name, b.x, b.y - rad - 10);
        ctx.restore();
    }

    function drawAntibody(a) {
        ctx.save();
        ctx.translate(a.x, a.y);
        ctx.rotate(a.rot);
        ctx.strokeStyle = '#c4a8ff'; ctx.lineWidth = 1.5; ctx.lineCap = 'round';
        const s = a.size;
        ctx.beginPath();
        ctx.moveTo(0, s); ctx.lineTo(0, -s * 0.2);
        ctx.moveTo(0, -s * 0.2); ctx.lineTo(-s * 0.7, -s);
        ctx.moveTo(0, -s * 0.2); ctx.lineTo(s * 0.7, -s);
        ctx.stroke();
        ctx.fillStyle = 'rgba(196, 168, 255, 0.4)';
        ctx.beginPath();
        ctx.arc(-s * 0.7, -s, 1.6, 0, Math.PI * 2);
        ctx.arc(s * 0.7, -s, 1.6, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }

    function drawMacrophage(m) {
        ctx.save();
        ctx.translate(m.x, m.y);
        const s = m.size + Math.sin(m.wobble) * 1.5;
        ctx.fillStyle = 'rgba(196, 30, 58, 0.18)';
        ctx.beginPath(); ctx.arc(0, 0, s + 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = 'rgba(196, 30, 58, 0.42)';
        ctx.beginPath(); ctx.arc(0, 0, s, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = 'rgba(196, 30, 58, 0.55)'; ctx.lineWidth = 1;
        for (let i = 0; i < 6; i++) {
            const a = (Math.PI * 2 / 6) * i + m.wobble * 0.2;
            ctx.beginPath();
            ctx.moveTo(Math.cos(a) * s, Math.sin(a) * s);
            ctx.lineTo(Math.cos(a) * (s + 6), Math.sin(a) * (s + 6));
            ctx.stroke();
        }
        ctx.restore();
    }

    function drawParticle(p) {
        const t = 1 - p.age / p.life;
        ctx.fillStyle = p.color;
        ctx.globalAlpha = t;
        if (p.kind === 'phage') {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * t, 0, Math.PI * 2);
            ctx.fill();
        } else {
            ctx.fillRect(p.x - p.size/2, p.y - p.size/2, p.size, p.size);
        }
        ctx.globalAlpha = 1;
    }

    function drawGrid() {
        ctx.strokeStyle = 'rgba(244, 196, 48, 0.04)';
        ctx.lineWidth = 1;
        const step = 30;
        for (let x = 0; x < W; x += step) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
        }
        for (let y = 0; y < H; y += step) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
        }
    }

    function render() {
        const sx = shakeT > 0 ? (Math.random() - 0.5) * shakeT * 14 : 0;
        const sy = shakeT > 0 ? (Math.random() - 0.5) * shakeT * 14 : 0;
        ctx.setTransform(dpr, 0, 0, dpr, sx * dpr, sy * dpr);
        ctx.clearRect(0, 0, W, H);
        drawGrid();
        macrophages.forEach(drawMacrophage);
        bacteria.forEach(drawBacterium);
        antibodies.forEach(drawAntibody);
        particles.forEach(drawParticle);
        drawPlayer();
    }

    function tick(t) {
        if (state !== 'playing') return;
        const dt = Math.min(0.05, (t - lastT) / 1000);
        lastT = t;
        update(dt);
        render();
        rafId = requestAnimationFrame(tick);
    }

    // ===== Input =====
    /* The game lives in the middle of a long page, so its key handlers must not
       act unless it actually has focus. Bound to document (a canvas game needs
       keys wherever the pointer is inside it) they previously swallowed the
       arrow keys for the WHOLE page the moment a game started: scrolling by
       keyboard died, and a/s/d/w could not be typed into the ⌘K search. That is
       a WCAG 2.1.2 keyboard trap. Fullscreen always counts as focused. */
    function gameHasFocus() {
        return wrap.contains(document.activeElement) || wrap.classList.contains('tf-fullscreen');
    }
    function isTypingTarget(t) {
        return !!t && (t.isContentEditable ||
            t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT');
    }
    function gameShouldHandle(e) {
        return gameHasFocus() && !isTypingTarget(e.target);
    }

    function onKeyDown(e) {
        if (!gameShouldHandle(e)) return;
        const k = e.key;
        if (state === 'playing') {
            if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','w','a','s','d','W','A','S','D'].includes(k)) {
                keys[k] = true; e.preventDefault(); return;
            }
            if (k === '1') { setFiber('lps'); return; }
            if (k === '2') { setFiber('ompc'); return; }
            if (k === '3') { setFiber('lamb'); return; }
            if (k === '4') { setFiber('pili'); return; }
            if (k === '5') { setFiber('nfra'); return; }
            if (k === 'p' || k === 'P') { pauseGame(); return; }
        } else if (state === 'paused') {
            if (k === 'p' || k === 'P') { resumeGame(); }
        }
    }
    // Note: keyup is NOT focus-gated. If focus leaves mid-press the keydown was
    // already recorded, and skipping the keyup would leave that key stuck down
    // and the phage gliding on its own when the visitor comes back.
    function onKeyUp(e) { keys[e.key] = false; }
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);

    /* Stop the game running off-screen: it kept a rAF loop and a canvas redraw
       going while the visitor read the rest of the page, which is wasted battery
       on a phone. pauseGame() already no-ops unless state === 'playing'. */
    if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
            entries.forEach(function (en) { if (!en.isIntersecting) pauseGame(); });
        }, { threshold: 0 }).observe(wrap);
    }
    // Same for a backgrounded tab.
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) pauseGame();
    });

    function updatePointer(e) {
        const r = canvas.getBoundingClientRect();
        const t = e.touches ? e.touches[0] : e;
        pointer.x = t.clientX - r.left;
        pointer.y = t.clientY - r.top;
    }
    wrap.addEventListener('mousedown', (e) => {
        if (state !== 'playing') return;
        if (e.target.closest('.tf-pause-btn, .tf-fiber-btn, .tf-joystick')) return;
        pointer.active = true; updatePointer(e); e.preventDefault();
    });
    wrap.addEventListener('mousemove', (e) => { if (pointer.active) updatePointer(e); });
    wrap.addEventListener('mouseup', () => { pointer.active = false; });
    wrap.addEventListener('mouseleave', () => { pointer.active = false; });

    // Joystick (touch)
    function joyStart(e) {
        const t = e.touches ? e.touches[0] : e;
        const r = joystick.getBoundingClientRect();
        joy.cx = r.left + r.width / 2;
        joy.cy = r.top + r.height / 2;
        joy.active = true;
        joystick.classList.add('active');
        joyMove(e);
        e.preventDefault();
    }
    function joyMove(e) {
        if (!joy.active) return;
        const t = e.touches ? e.touches[0] : e;
        let dx = t.clientX - joy.cx;
        let dy = t.clientY - joy.cy;
        const max = 32;
        const d = Math.hypot(dx, dy);
        if (d > max) { dx = (dx / d) * max; dy = (dy / d) * max; }
        joyThumb.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px))`;
        joy.dx = dx / max;
        joy.dy = dy / max;
        e.preventDefault();
    }
    function joyEnd() {
        joy.active = false;
        joy.dx = 0; joy.dy = 0;
        joystick.classList.remove('active');
        joyThumb.style.transform = 'translate(-50%, -50%)';
    }
    joystick.addEventListener('touchstart', joyStart, { passive: false });
    joystick.addEventListener('touchmove',  joyMove,  { passive: false });
    joystick.addEventListener('touchend',   joyEnd);
    joystick.addEventListener('touchcancel',joyEnd);
    joystick.addEventListener('mousedown',  joyStart);
    window.addEventListener('mousemove',    (e) => { if (joy.active) joyMove(e); });
    window.addEventListener('mouseup',      joyEnd);

    // Non-joystick touch on the play field for drag-to-move
    wrap.addEventListener('touchstart', (e) => {
        if (state !== 'playing') return;
        if (e.target.closest('.tf-pause-btn, .tf-fiber-btn, .tf-joystick')) return;
        pointer.active = true; updatePointer(e); e.preventDefault();
    }, { passive: false });
    wrap.addEventListener('touchmove', (e) => {
        if (!pointer.active) return;
        updatePointer(e); e.preventDefault();
    }, { passive: false });
    wrap.addEventListener('touchend', () => { pointer.active = false; });

    // Fiber buttons (works during play)
    fiberBtns.forEach(b => b.addEventListener('click', () => {
        if (state === 'playing') setFiber(b.dataset.fiber);
    }));

    // Pause button
    pauseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (state === 'playing') pauseGame();
        else if (state === 'paused') resumeGame();
    });

    // Fullscreen toggle (CSS-driven, with body lock + resize)
    function toggleFullscreen() {
        const on = wrap.classList.toggle('tf-fullscreen');
        document.body.classList.toggle('tf-locked', on);
        fullBtn.textContent = on ? '⊠' : '⛶';
        fullBtn.title = on ? 'Exit fullscreen [F or Esc]' : 'Fullscreen [F]';
        // Try the real Fullscreen API too (graceful no-op if blocked)
        if (on) {
            try { wrap.requestFullscreen?.({ navigationUI: 'hide' }).catch(()=>{}); } catch {}
        } else {
            try { if (document.fullscreenElement) document.exitFullscreen?.(); } catch {}
        }
        // Schedule a resize after layout settles
        requestAnimationFrame(() => requestAnimationFrame(resize));
    }
    fullBtn.addEventListener('click', (e) => { e.stopPropagation(); toggleFullscreen(); });
    // Sync class if user exits via browser ESC out of native fullscreen
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement && wrap.classList.contains('tf-fullscreen')) {
            wrap.classList.remove('tf-fullscreen');
            document.body.classList.remove('tf-locked');
            fullBtn.textContent = '⛶';
            requestAnimationFrame(resize);
        }
    });
    // Keyboard: F to toggle, ESC to exit.
    // The old gate was `wrap.matches(':hover') || state !== 'setup'`, and state
    // is only reset to 'setup' when a new game starts — so after playing once,
    // pressing "f" ANYWHERE on the page (including in the ⌘K search box) threw
    // the game into fullscreen. Same focus rule as the movement keys.
    document.addEventListener('keydown', (e) => {
        if (e.key === 'f' || e.key === 'F') {
            if (gameShouldHandle(e)) { toggleFullscreen(); e.preventDefault(); }
        } else if (e.key === 'Escape' && wrap.classList.contains('tf-fullscreen')) {
            toggleFullscreen();
        }
    });

    // Resize
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    resize();

    // Init UI
    updateHP();
    scoreEl.textContent = '0';
    lysesEl.textContent = '0';
    timeEl.textContent = chosenDuration === 0 ? '0' : chosenDuration;
    levelEl.textContent = 'LVL 1';
    renderSetup();

    // Decorative idle render so the canvas isn't blank
    function idleFrame() {
        ctx.clearRect(0, 0, W, H);
        drawGrid();
        const decor = [
            { x: W * 0.30, y: H * 0.42, len: 36, rad: 11, rot: 0.2, pulse: 0, receptor: 'lps' },
            { x: W * 0.70, y: H * 0.58, len: 38, rad: 12, rot: -0.4, pulse: 1.0, receptor: 'ompc' },
            { x: W * 0.50, y: H * 0.30, len: 32, rad: 10, rot: 0.6, pulse: 2.0, receptor: 'lamb' },
            { x: W * 0.30, y: H * 0.74, len: 34, rad: 11, rot: 0.3, pulse: 1.5, receptor: 'pili' }
        ];
        decor.forEach(drawBacterium);
    }
    idleFrame();
})();
