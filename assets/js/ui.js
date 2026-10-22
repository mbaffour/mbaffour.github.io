/* ==============================================================
   SITEWIDE INTERACTIVITY — research cards + hero count-up
=============================================================== */
(function() {
    // Research focus cards: click / keyboard to expand detail
    document.querySelectorAll('.research-card').forEach(card => {
        const toggle = () => {
            const open = card.classList.toggle('open');
            card.setAttribute('aria-expanded', open ? 'true' : 'false');
        };
        card.addEventListener('click', toggle);
        card.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); }
        });
    });

    // Hero stat count-up on first view
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    function countUp(el) {
        const m = (el.textContent || '').trim().match(/^(\d+)(\+?)$/);
        if (!m) return;
        const target = parseInt(m[1], 10), suffix = m[2];
        if (reduce || target === 0) { el.textContent = target + suffix; return; }
        const dur = 900, t0 = performance.now();
        (function step(now) {
            const k = Math.min(1, (now - t0) / dur);
            el.textContent = Math.round((1 - Math.pow(1 - k, 3)) * target) + suffix;
            if (k < 1) requestAnimationFrame(step);
        })(t0);
    }
    // run after toolCount is populated by the render pass
    setTimeout(() => document.querySelectorAll('.hero-stat-value').forEach(countUp), 80);
})();

/* The command palette moved to assets/js/search.js, which runs on every page. */

/* ==============================================================
   NAVBAR SCROLL CONDENSE
=============================================================== */
/* Contact: copy email buttons + mouse glow */
(function() {
    const card = document.getElementById('contactEmail');
    const fb = document.getElementById('copyFeedback');
    if (!card) return;
    document.querySelectorAll('.contact-email-copy').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const addr = btn.dataset.copy;
            try {
                await navigator.clipboard.writeText(addr);
                fb.textContent = 'Copied!';
            } catch {
                fb.textContent = 'Press ⌘C';
            }
            fb.classList.add('show');
            clearTimeout(window._cpyT);
            window._cpyT = setTimeout(() => fb.classList.remove('show'), 1600);
        });
    });
})();

/* Contact canvas: phages drifting toward the email card */
(function() {
    const canvas = document.getElementById('contactCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let w, h, dpr;
    function resize() {
        dpr = devicePixelRatio || 1;
        w = canvas.offsetWidth;
        h = canvas.offsetHeight;
        canvas.width = w * dpr; canvas.height = h * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    resize();

    const PAL = ['244, 196, 48', '26, 128, 64', '196, 30, 58'];
    const phages = [];
    for (let i = 0; i < 18; i++) {
        phages.push({
            x: Math.random() * w,
            y: Math.random() * h,
            size: 10 + Math.random() * 14,
            vx: (Math.random() - 0.5) * 0.18,
            vy: (Math.random() - 0.5) * 0.18,
            rot: Math.random() * Math.PI * 2,
            rotSpeed: (Math.random() - 0.5) * 0.008,
            opacity: 0.18 + Math.random() * 0.18,
            color: PAL[Math.floor(Math.random() * PAL.length)]
        });
    }
    function draw(p) {
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.strokeStyle = `rgba(${p.color}, ${p.opacity})`;
        ctx.fillStyle = `rgba(${p.color}, ${p.opacity})`;
        ctx.lineWidth = 1.1;
        const s = p.size;
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
        ctx.beginPath();
        ctx.moveTo(0, s * 0.5);
        ctx.lineTo(0, s * 1.3);
        ctx.stroke();
        for (let i = -1; i <= 1; i += 2) {
            ctx.beginPath();
            ctx.moveTo(0, s * 1.3);
            ctx.quadraticCurveTo(i * s * 0.3, s * 1.45, i * s * 0.5, s * 1.7);
            ctx.stroke();
        }
        ctx.restore();
    }
    let cVisible = false, cLooping = false;
    function tick() {
        if (!cVisible || reduceMotion) { cLooping = false; return; }
        ctx.clearRect(0, 0, w, h);
        phages.forEach(p => {
            p.x += p.vx; p.y += p.vy; p.rot += p.rotSpeed;
            if (p.x < -40) p.x = w + 40;
            if (p.x > w + 40) p.x = -40;
            if (p.y < -40) p.y = h + 40;
            if (p.y > h + 40) p.y = -40;
            draw(p);
        });
        requestAnimationFrame(tick);
    }
    function cStart() { if (!cLooping && cVisible && !reduceMotion) { cLooping = true; tick(); } }
    const cIo = new IntersectionObserver(es => {
        es.forEach(e => { cVisible = e.isIntersecting; if (cVisible) cStart(); });
    }, { threshold: 0 });
    cIo.observe(canvas);
    // Static frame so it's not empty when section first paints
    ctx.clearRect(0, 0, w, h);
    phages.forEach(draw);
})();

/* "Currently" badge rotation */
(function() {
    const badge = document.getElementById('nowBadge');
    const icon  = document.getElementById('nowIcon');
    const body  = document.getElementById('nowBody');
    if (!badge) return;
    /* The first message is the strongest verifiable live fact, matching the
       pill's static HTML — the rotation must never lead with something weaker
       than what it replaces. "Wrapping up the preprint" was stale (it is
       posted), and every entry here must stay true without maintenance. */
    const messages = [
        { icon: '🦠', text: 'First-author N4 lysis preprint live on bioRxiv &middot; building open tools for phage biology.' },
        { icon: '🧬', text: 'Reverse-engineering N4&rsquo;s lysis decision &mdash; the timing switch that sets how many particles a cell releases.' },
        { icon: '🧫', text: 'Mentoring undergrads through phage isolation, TEM, and genome annotation.' },
        { icon: '💻', text: 'Shipping open scientific software &mdash; browser-first, privacy-first, zero-install.' }
    ];
    let i = 0;
    setInterval(() => {
        i = (i + 1) % messages.length;
        badge.classList.add('fading');
        setTimeout(() => {
            /* icon is a static pulse dot now — emoji rotation retired */
            body.innerHTML = messages[i].text;
            badge.classList.remove('fading');
        }, 360);
    }, 5600);
})();

const progress = document.getElementById('scrollProgress');
const toTop = document.getElementById('toTop');
const navAvatar = document.getElementById('navAvatar');
let lastY = 0;
const ambientEl = document.getElementById('ambientCanvas');
function updateScrollUI() {
    const nav = document.getElementById('navbar');
    const y = window.scrollY;
    /* Toggle a class; let CSS own the colour. Writing the background inline here
       hard-coded a DARK rgba on every scroll event, which beat the light-theme
       rule on specificity — so in light mode the whole navigation bar stayed
       near-black behind near-black links. */
    nav.classList.toggle('scrolled', y > 80);
    const docH = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docH > 0 ? (y / docH) * 100 : 0;
    progress.style.width = pct + '%';
    toTop.classList.toggle('show', y > 600);
    if (navAvatar) navAvatar.classList.toggle('show', y > window.innerHeight * 0.6);
    const heroH = window.innerHeight;
    // Fade in ambient layer after the hero — keeps hero clean
    if (ambientEl) {
        const fadeStart = heroH * 0.6;
        const fadeEnd   = heroH * 1.0;
        const t = Math.max(0, Math.min(1, (y - fadeStart) / (fadeEnd - fadeStart)));
        ambientEl.style.opacity = (t * 0.55).toFixed(3);
    }
    lastY = y;
}
window.addEventListener('scroll', updateScrollUI, { passive: true });
updateScrollUI();
toTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
updateScrollUI();
