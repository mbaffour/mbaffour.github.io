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

/* ==============================================================
   COMMAND PALETTE
=============================================================== */
(function() {
    const overlay = document.getElementById('cmdkOverlay');
    const input = document.getElementById('cmdkInput');
    const results = document.getElementById('cmdkResults');
    const opener = document.getElementById('cmdkOpen');

    // Build the index
    const baseItems = [
        { type: 'section', label: 'Research focus',       hint: 'lysis · N4 · phage biology', href: '#research', icon: '🦠' },
        { type: 'section', label: 'Lysis curve playground', hint: 'tune phage parameters live', href: '#playground', icon: '📈' },
        { type: 'section', label: 'Publications',         hint: 'preprints & papers',  href: '#publications', icon: '📖' },
        { type: 'section', label: 'Research software',     hint: 'open-source tools', href: '#tools', icon: '🧰' },
        { type: 'section', label: 'Other tools',             hint: 'apps built outside the lab', href: '#builds', icon: '⚙️' },
        { type: 'section', label: 'TailFiber game',        hint: 'TailFiber · playable phage game', href: '#next', icon: '🧪' },
        { type: 'section', label: 'Recognition & service',hint: 'awards · outreach',   href: '#recognition', icon: '🏆' },
        { type: 'section', label: 'About',                hint: 'who I am',            href: '#about', icon: '🧬' },
        { type: 'section', label: 'CV',                   hint: 'view or download',    href: '#about', icon: '📄' },
        { type: 'section', label: 'Contact',              hint: 'get in touch',        href: '#contact', icon: '✉' },
        { type: 'link',    label: 'Email — baffour@tamu.edu', hint: 'academic email',  href: 'mailto:baffour@tamu.edu', icon: '✉', external: true },
        { type: 'link',    label: 'Email — mbaffour890@gmail.com', hint: 'personal email', href: 'mailto:mbaffour890@gmail.com', icon: '✉', external: true },
        { type: 'link',    label: 'GitHub @mbaffour',     hint: 'open source repos',   href: 'https://github.com/mbaffour', icon: '⌥', external: true },
        { type: 'link',    label: 'Google Scholar',       hint: 'citations',           href: 'https://scholar.google.com/citations?user=e5_h_2YAAAAJ&hl=en', icon: '🎓', external: true },
        { type: 'link',    label: 'LinkedIn',             hint: 'profile',             href: 'https://www.linkedin.com/in/mba-101b/', icon: 'in', external: true },
        { type: 'link',    label: 'ORCID',                hint: '0009-0007-9036-413X', href: 'https://orcid.org/0009-0007-9036-413X', icon: '🆔', external: true },
        { type: 'link',    label: 'Twitter / X',          hint: '@AwuahMB',            href: 'https://twitter.com/AwuahMB', icon: '𝕏', external: true },
        { type: 'link',    label: 'Download CV (PDF)',    hint: 'résumé',              href: 'cv-resume/Michael_Baffour_Awuah_CV.pdf', icon: '📄', external: false }
    ];
    const toolItems = tools.flatMap(t => {
        const out = [{ type: 'tool', label: t.title, hint: t.tech.join(' · '), href: t.app || t.blog, icon: '🧰', external: true }];
        if (t.blog && t.blog !== t.app) out.push({ type: 'tool', label: t.title + ' — Blog', hint: 'write-up · how it works', href: t.blog, icon: '📝', external: true });
        return out;
    });
    const pubItems  = publications.map(p => ({ type: 'pub', label: p.title, hint: p.journal + ' · ' + p.year, href: p.doi, icon: '📖', external: true }));
    /* The 'Projects' group used to filter on type:'project', which nothing ever
       emitted — the side builds were unsearchable. They come from the shared
       builds array now. */
    const projectItems = (typeof builds === 'undefined' ? [] : builds).map(b => ({
        type: 'project', label: b.title, hint: b.tech.join(' · '), href: b.app, icon: '⚙️', external: true
    }));
    const items = [...baseItems, ...pubItems, ...toolItems, ...projectItems];

    function score(q, item) {
        if (!q) return 0;
        const s = (item.label + ' ' + item.hint).toLowerCase();
        const Q = q.toLowerCase();
        if (s.includes(Q)) return 100 - s.indexOf(Q);
        // fuzzy: char-by-char
        let i = 0;
        for (const ch of s) {
            if (ch === Q[i]) i++;
            if (i === Q.length) return 50 - (s.length - Q.length) * 0.1;
        }
        return -1;
    }

    const groups = {
        'Jump to': it => it.type === 'section',
        'Tools': it => it.type === 'tool',
        'Projects': it => it.type === 'project',
        'Publications': it => it.type === 'pub',
        'Links': it => it.type === 'link'
    };

    let active = 0;
    let visible = [];

    function render(q = '') {
        const scored = items
            .map(it => ({ it, s: q ? score(q, it) : 0 }))
            .filter(x => !q || x.s >= 0)
            .sort((a, b) => b.s - a.s);

        visible = scored.map(x => x.it);
        if (visible.length === 0) {
            results.innerHTML = '<div class="cmdk-empty">No matches. Try "lysis", "FigureLab", "Patterson", or "GitHub".</div>';
            return;
        }

        // Show grouped (when not searching) or flat (when searching)
        let html = '';
        if (q) {
            visible.slice(0, 12).forEach((it, idx) => {
                html += itemHTML(it, idx);
            });
        } else {
            let idx = 0;
            Object.entries(groups).forEach(([name, fn]) => {
                const g = visible.filter(fn);
                if (g.length === 0) return;
                html += `<div class="cmdk-group">${name}</div>`;
                g.forEach(it => {
                    html += itemHTML(it, idx);
                    idx++;
                });
            });
            // Re-flatten to match visible order
            visible = [...visible.filter(it => groups['Jump to'](it)),
                       ...visible.filter(it => groups['Tools'](it)),
                       ...visible.filter(it => groups['Projects'](it)),
                       ...visible.filter(it => groups['Publications'](it)),
                       ...visible.filter(it => groups['Links'](it))];
        }
        results.innerHTML = html;
        active = 0;
        highlight();
    }

    function itemHTML(it, idx) {
        const target = it.external ? ' target="_blank" rel="noopener"' : '';
        return `<a class="cmdk-item" href="${it.href}" data-idx="${idx}"${target}>
            <span class="ic">${it.icon}</span>
            <span><strong>${it.label}</strong><div style="font-size:0.75rem;color:var(--ink-4);margin-top:1px">${it.hint}</div></span>
            <span class="arrow">${it.external ? '↗' : '↵'}</span>
        </a>`;
    }

    function highlight() {
        results.querySelectorAll('.cmdk-item').forEach((el, i) => {
            el.classList.toggle('selected', i === active);
            if (i === active) el.scrollIntoView({ block: 'nearest' });
        });
    }

    let lastFocus = null;
    function open() {
        lastFocus = document.activeElement;
        overlay.classList.add('open');
        input.value = '';
        render('');
        setTimeout(() => input.focus(), 30);
    }
    function close() {
        overlay.classList.remove('open');
        /* Send focus back where it came from, rather than dropping it on <body>. */
        if (lastFocus && lastFocus.focus) lastFocus.focus();
        lastFocus = null;
    }

    opener && opener.addEventListener('click', open);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    input.addEventListener('input', () => render(input.value.trim()));
    input.addEventListener('keydown', (e) => {
        const list = results.querySelectorAll('.cmdk-item');
        if (e.key === 'ArrowDown') { e.preventDefault(); active = Math.min(active + 1, list.length - 1); highlight(); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); active = Math.max(active - 1, 0); highlight(); }
        else if (e.key === 'Enter') {
            const el = list[active];
            if (el) el.click();
        } else if (e.key === 'Escape') {
            close();
        } else if (e.key === 'Tab') {
            /* The palette is a modal dialog; keep Tab inside it. */
            e.preventDefault();
            const el = list[active];
            if (el) el.focus ? el.focus() : input.focus();
        }
    });
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            overlay.classList.contains('open') ? close() : open();
        } else if (e.key === 'Escape' && overlay.classList.contains('open')) {
            close();
        } else if (e.key === '/' && !overlay.classList.contains('open') && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
            e.preventDefault();
            open();
        }
    });
})();

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
    const messages = [
        { icon: '🦠', text: 'Wrapping up the N4 lysis preprint &amp; building new R Shiny tools for the lab.' },
        { icon: '🧫', text: 'Mentoring undergrads through phage isolation, TEM, and genome annotation.' },
        { icon: '🔬', text: 'Hunting for new phages in Texas creeks and characterizing them by TEM.' },
        { icon: '🧬', text: 'Reverse-engineering N4’s lysis decisions for high-titer phage production.' },
        { icon: '💻', text: 'Shipping open scientific software &mdash; browser-first, privacy-first, zero-install.' }
    ];
    let i = 0;
    setInterval(() => {
        i = (i + 1) % messages.length;
        badge.classList.add('fading');
        setTimeout(() => {
            icon.textContent = messages[i].icon;
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
    nav.style.background = y > 80
        ? 'rgba(10, 8, 2, 0.92)'
        : 'rgba(10, 8, 2, 0.78)';
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
