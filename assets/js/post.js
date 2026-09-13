/* Shared enhancements for every blog post. Loaded after assets/js/posts-data.js.
   Adds, without touching the post's own markup or styles:
     - a byline bar: link to the blog index, reading time, published and updated dates,
       and a copy-link button;
     - an "On this page" table of contents when the post has three or more h2 headings
       (ids are generated from the heading text if missing), with the current section
       highlighted while scrolling;
     - previous / next links to the neighbouring posts, from the shared posts array.
   Everything degrades to nothing if the script or the data fails to load. */
(function () {
    'use strict';
    const main = document.querySelector('main');
    if (!main) return;
    /* Anchor to the text column: the parent of the first h2 inside main. Some posts lay
       .wrap out as a grid or flex row, and a block appended there lands in a new column. */
    const contentHeadings = [...main.querySelectorAll('h2')].filter(h => !h.closest('.finale, footer, nav'));
    const fallback = main.querySelector('article') || main.querySelector('.wrap') || main;
    const columnOf = heading => {
        let node = (heading && heading.parentElement) || fallback;
        while (node !== main && /^(grid|flex|inline-grid|inline-flex)$/.test(getComputedStyle(node).display) && node.parentElement) node = node.parentElement;
        return node;
    };
    const host = columnOf(contentHeadings[0]);                                   /* byline and contents go above the first section */
    const tail = columnOf(contentHeadings[contentHeadings.length - 1]);          /* previous/next go after the last one */
    const list = (typeof posts === 'undefined' ? [] : posts).slice().sort((a, b) => b.iso.localeCompare(a.iso));
    /* Static hosts serve posts with and without the .html extension, so match on the slug. */
    const slug = path => decodeURIComponent((path || '').split('/').pop()).replace(/\.html?$/i, '');
    const here = slug(location.pathname);
    const index = list.findIndex(p => slug(p.url) === here);
    const post = index >= 0 ? list[index] : null;

    const css = `
.post-meta-bar,.post-toc,.post-nav,.post-nav-all{text-align:left;box-sizing:border-box;width:auto;max-width:100%;margin-left:0;margin-right:0;padding-left:0;padding-right:0;text-indent:0;float:none;columns:auto}
.post-meta-bar{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem 1.1rem;margin:0 0 1.6rem;padding:.7rem 0;border-top:1px solid var(--border,rgba(128,128,128,.25));border-bottom:1px solid var(--border,rgba(128,128,128,.25));font-family:var(--font-mono,ui-monospace,Menlo,monospace);font-size:.78rem;color:var(--ink-3,inherit);letter-spacing:.01em}
.post-meta-bar a{color:inherit;text-decoration:none}
.post-meta-bar a:hover,.post-meta-bar button:hover{color:var(--gold,#b8860b)}
.post-meta-bar .sep{opacity:.45}
.post-meta-bar button{font:inherit;color:inherit;background:none;border:1px solid var(--border-strong,rgba(128,128,128,.4));border-radius:999px;padding:.2rem .7rem;cursor:pointer;margin-left:auto}
.post-toc{margin:0 0 2rem;border:1px solid var(--border,rgba(128,128,128,.25));border-radius:12px;background:var(--bg-card,transparent)}
.post-toc summary{cursor:pointer;padding:.8rem 1rem;font-family:var(--font-mono,ui-monospace,Menlo,monospace);font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;color:var(--gold,#b8860b);list-style:none;display:flex;justify-content:space-between;align-items:center}
.post-toc summary::-webkit-details-marker{display:none}
.post-toc summary::after{content:'+';font-size:1rem;opacity:.7}
.post-toc[open] summary::after{content:'–'}
.post-toc ol{margin:0;padding:0 1rem 1rem 1rem;list-style:none;columns:1}
@media (min-width:760px){.post-toc ol{columns:2;column-gap:2rem}}
.post-toc li{break-inside:avoid;margin:0;padding:.22rem 0;font-size:.92rem;line-height:1.45}
.post-toc a{color:var(--ink-2,inherit);text-decoration:none;border-left:2px solid transparent;padding-left:.6rem;display:inline-block;transition:color .15s,border-color .15s}
.post-toc a:hover{color:var(--gold,#b8860b)}
.post-toc li.current a{color:var(--gold,#b8860b);border-left-color:var(--gold,#b8860b)}
.post-nav{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:3rem 0 1rem}
@media (max-width:640px){.post-nav{grid-template-columns:1fr}}
.post-nav a{display:block;padding:1rem 1.1rem;border:1px solid var(--border,rgba(128,128,128,.25));border-radius:12px;text-decoration:none;color:inherit;background:var(--bg-card,transparent);transition:border-color .15s,transform .15s}
.post-nav a:hover{border-color:var(--gold,#b8860b);transform:translateY(-2px)}
.post-nav a.next{text-align:right}
.post-nav .kicker{display:block;background:none;padding:0;border:0;font-family:var(--font-mono,ui-monospace,Menlo,monospace);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--gold,#b8860b);margin-bottom:.35rem}
.post-nav .title{display:block;font-family:var(--font-display,Georgia,serif);font-size:1.05rem;line-height:1.35;color:var(--ink,inherit)}
.post-nav-all{text-align:center;margin:0 0 2rem;font-family:var(--font-mono,ui-monospace,Menlo,monospace);font-size:.8rem}
.post-nav-all a{color:var(--ink-3,inherit);text-decoration:none}
.post-nav-all a:hover{color:var(--gold,#b8860b)}
main svg[width]{max-width:100%;height:auto}
@media print{.post-meta-bar button,.post-toc,.post-nav,.post-nav-all{display:none}}`;
    const style = document.createElement('style'); style.textContent = css; document.head.append(style);

    const el = (tag, className, text) => { const node = document.createElement(tag); if (className) node.className = className; if (text !== undefined) node.textContent = text; return node; };
    const fmt = iso => { const d = new Date(iso + 'T12:00:00Z'); return isNaN(d) ? iso : d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' }); };
    const sep = () => el('span', 'sep', '·');

    /* ---- byline bar ---- */
    const words = (main.innerText || main.textContent || '').trim().split(/\s+/).filter(Boolean).length;
    const minutes = Math.max(1, Math.round(words / 220));
    const bar = el('div', 'post-meta-bar');
    const all = el('a', null, '← All posts'); all.href = 'index.html'; bar.append(all, sep());
    bar.append(el('span', null, minutes + ' min read'));
    if (post) {
        bar.append(sep(), el('span', null, 'Published ' + fmt(post.iso)));
        if (post.updated && post.updated !== post.iso) bar.append(sep(), el('span', null, 'Updated ' + fmt(post.updated)));
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
        const copy = el('button', null, 'Copy link'); copy.type = 'button';
        copy.addEventListener('click', async () => {
            try { await navigator.clipboard.writeText(location.href.split('#')[0]); copy.textContent = 'Copied'; }
            catch (error) { copy.textContent = 'Copy failed'; }
            setTimeout(() => { copy.textContent = 'Copy link'; }, 1800);
        });
        bar.append(copy);
    }
    host.prepend(bar);

    /* ---- table of contents ---- */
    const headings = [...main.querySelectorAll('h2')].filter(h => !h.closest('.finale, footer, nav, .post-nav') && h.textContent.trim());
    if (headings.length >= 3) {
        const used = new Set([...document.querySelectorAll('[id]')].map(node => node.id));
        headings.forEach(h => {
            if (!h.id) {
                let base = h.textContent.trim().toLowerCase().replace(/['’]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'section';
                let id = base; let n = 2; while (used.has(id)) id = base + '-' + n++;
                h.id = id; used.add(id);
            }
        });
        const toc = el('details', 'post-toc'); toc.open = window.innerWidth >= 760;
        const summary = el('summary', null, 'On this page'); toc.append(summary);
        const nav = el('nav'); nav.setAttribute('aria-label', 'On this page');
        const ol = el('ol'); const items = new Map();
        headings.forEach(h => { const li = el('li'); const a = el('a', null, h.textContent.trim()); a.href = '#' + h.id; li.append(a); ol.append(li); items.set(h.id, li); });
        nav.append(ol); toc.append(nav); bar.insertAdjacentElement('afterend', toc);
        if ('IntersectionObserver' in window) {
            let current = null;
            const observer = new IntersectionObserver(entries => {
                entries.forEach(entry => { if (entry.isIntersecting) { if (current) current.classList.remove('current'); current = items.get(entry.target.id); if (current) current.classList.add('current'); } });
            }, { rootMargin: '-10% 0px -75% 0px' });
            headings.forEach(h => observer.observe(h));
        }
    }

    /* ---- previous / next ---- */
    if (post) {
        const newer = list[index - 1]; const older = list[index + 1];
        const nav = el('nav', 'post-nav'); nav.setAttribute('aria-label', 'More posts');
        const card = (target, kicker, className) => { const a = el('a', className); a.href = (target.url || '').split('/').pop(); a.append(el('span', 'kicker', kicker), el('span', 'title', target.title)); return a; };
        if (older) nav.append(card(older, '← Older', 'prev')); else nav.append(el('span'));
        if (newer) nav.append(card(newer, 'Newer →', 'next'));
        const allLine = el('p', 'post-nav-all'); const link = el('a', null, 'All ' + list.length + ' posts'); link.href = 'index.html'; allLine.append(link);
        /* After the last section rather than inside it, so a closing call-to-action card keeps
           its own shape; inside only when the parent is a grid or flex row. */
        const parentIsRow = tail.parentElement && /^(grid|flex|inline-grid|inline-flex)$/.test(getComputedStyle(tail.parentElement).display);
        if (tail !== main && tail.matches('section, article') && !parentIsRow) tail.after(nav, allLine); else tail.append(nav, allLine);
    }
})();
