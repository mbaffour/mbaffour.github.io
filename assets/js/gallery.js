/* Life in the Lab gallery: data, grid, filters and lightbox. Used by beyond.html.
   Self-contained: no-ops on a page without #galleryGrid. */
(function () {
    'use strict';
    if (!document.getElementById('galleryGrid')) return;
    const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    function wireFilter(filtersId, renderFn) {
        const root = document.getElementById(filtersId);
        if (!root) return;
        root.addEventListener('click', (e) => {
            if (!e.target.classList.contains('filter-btn')) return;
            root.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            renderFn(e.target.dataset.filter);
        });
    }
/* ==============================================================
   DATA — Gallery (Life in the Lab)
   Adding a new photo: drop file in /gallery/, add an entry here.
   Layouts: feature (3w × 2h), tall (2w × 2h), wide (3w × 1h), square (2w × 1h)
=============================================================== */
const gallery = [
    {
        src: "gallery/gallery-tem.webp", w: 900, h: 1200,
        tag: "Imaging",
        caption: "TEMs of phages I isolated, at the TAMU Microscopy Core.",
        sub: "Transmission electron microscopy",
        layout: "feature"
    },
    {
        src: "gallery/gallery-talk.webp", w: 900, h: 1200,
        tag: "Talks",
        caption: "Giving a Data Blitz at the TAMU Biology Student &amp; Postdoc Research Conference.",
        sub: "Data Blitz · TAMU",
        layout: "tall"
    },
    {
        src: "gallery/gallery-phage-hunt.webp", w: 844, h: 1125,
        tag: "Discovery",
        caption: "Fishing for phage samples in front of Fort Hood, Texas.",
        sub: "Environmental phage hunting",
        layout: "tall"
    },
    {
        src: "gallery/gallery-prolific-predators.webp", w: 900, h: 507,
        tag: "Talks",
        caption: "Giving a talk at the Bio &amp; Chem Sciences Symposium: TEMs of phages and flasks of lysed <em>E. coli</em>.",
        sub: "College Station, TX",
        layout: "wide"
    },
    {
        src: "gallery/gallery-patterson-ceremony.webp", w: 900, h: 797,
        tag: "Award",
        caption: "Patterson Award Ceremony.",
        sub: "Center for Phage Technology · 2025",
        layout: "square"
    },
    {
        src: "gallery/gallery-patterson-group.webp", w: 900, h: 675,
        tag: "Award",
        caption: "Patterson Award Ceremony, celebrating with the lab.",
        sub: "August 2025",
        layout: "wide"
    },
    {
        src: "gallery/gallery-phage-princess.webp", w: 900, h: 675,
        tag: "Outreach",
        caption: "Darwin Day Outreach with the Ramsey Lab.",
        sub: "Phage Princess &amp; Phage Pirate",
        layout: "tall"
    },
    {
        src: "gallery/gallery-cpt-group.webp", w: 900, h: 675,
        tag: "Lab",
        caption: "Ramsey Lab — Summer 2023.",
        sub: "Lab portrait",
        layout: "wide"
    },
    {
        src: "gallery/gallery-whiteboard.webp", w: 900, h: 675,
        tag: "Brainwork",
        caption: "Brainstorming the N4 infection cycle &amp; how to block superinfection.",
        sub: "Ramsey Lab whiteboard",
        layout: "square"
    },
    {
        src: "gallery/gallery-flasks.webp", w: 900, h: 1200,
        tag: "Bench",
        caption: "Killing bacteria. Dem dead. ☠️",
        sub: "Phage attack in progress",
        layout: "square"
    },
    {
        src: "gallery/gallery-bench.webp", w: 900, h: 1200,
        tag: "Bench",
        caption: "At my bench in the Ramsey Lab.",
        sub: "A regular Tuesday",
        layout: "square"
    },
    {
        src: "gallery/gallery-whiteboard-ny.webp", w: 900, h: 675,
        tag: "Brainwork",
        caption: "Amber suppressor logic: <em>tRNA · gp65am · LE392</em>.",
        sub: "Whiteboard scratchpad",
        layout: "wide"
    },
    {
        src: "gallery/gallery-poster-review.webp", w: 900, h: 1200,
        tag: "Posters",
        caption: "Walking through the N4 lysis model at the poster session.",
        sub: "Poster session",
        layout: "tall"
    },
    {
        src: "gallery/gallery-phage-prep.webp", w: 900, h: 1200,
        tag: "Bench",
        caption: "Watching bands of phage after ultracentrifugation, prepping for dialysis.",
        sub: "How the nice TEMs happen",
        layout: "square"
    }
];

/* Map gallery tags to broad categories */
const TAG_CATEGORY = {
    'Imaging': 'research', 'Discovery': 'research', 'Brainwork': 'research',
    'Equipment': 'research', 'Posters': 'research', 'Molecular biology': 'research',
    'Bench': 'bench',
    'Talks': 'talks',
    'Outreach': 'outreach',
    'Award': 'awards',
    'Conference': 'community', 'Lab': 'community', 'Community': 'community',
    'Lab life': 'community',
    'Aggies': 'aggies', 'Off duty': 'aggies', 'Curiosity': 'aggies',
    'Science': 'community'
};
function catFor(g) { return TAG_CATEGORY[g.tag] || 'other'; }
function plainText(s) { return (s || '').replace(/<[^>]*>/g, ''); }

function renderGallery(filter = 'all') {
    const grid = document.getElementById('galleryGrid');
    if (!grid) return;
    const items = filter === 'all' ? gallery : gallery.filter(g => catFor(g) === filter);
    grid.innerHTML = items.map(g => {
        const idx = gallery.indexOf(g);
        return `
        <div class="gallery-item ${g.layout || 'square'}" data-idx="${idx}"
             role="button" tabindex="0" aria-label="View larger: ${plainText(g.alt || g.caption)}">
            <img src="${g.src}" alt="${plainText(g.alt || g.caption)}"
                 width="${g.w || ''}" height="${g.h || ''}" loading="lazy" decoding="async">
            <div class="gallery-overlay">
                <span class="gallery-tag">${g.tag}</span>
                <div class="gallery-caption">${g.caption}</div>
            </div>
        </div>`;
    }).join('');
}

/* Build gallery filter buttons */
(function() {
    const root = document.getElementById('galleryFilters');
    const counts = gallery.reduce((a, g) => {
        const c = catFor(g); a[c] = (a[c] || 0) + 1; return a;
    }, {});
    const map = [
        ['all',       'All',       gallery.length],
        ['research',  'Research',  counts.research  || 0],
        ['bench',     'Bench',     counts.bench     || 0],
        ['talks',     'Talks',     counts.talks     || 0],
        ['awards',    'Awards',    counts.awards    || 0],
        ['outreach',  'Outreach',  counts.outreach  || 0],
        ['community', 'Community', counts.community || 0],
        ['aggies',    'Off-Duty',  counts.aggies    || 0]
    ];
    root.innerHTML = map.filter(([,,n]) => n > 0).map(([k, label, n], i) => `
        <button class="filter-btn ${i === 0 ? 'active' : ''}" data-filter="${k}">
            ${label} <span class="filter-count">${n}</span>
        </button>
    `).join('');
})();
renderGallery();
wireFilter('galleryFilters', renderGallery);

/* Lightbox */
(function() {
    const box = document.getElementById('lightbox');
    const img = document.getElementById('lightboxImg');
    const cap = document.getElementById('lightboxCap');
    const close = document.getElementById('lightboxClose');
    if (!box) return;
    let lastFocus = null;

    function open(i) {
        const g = gallery[i];
        if (!g) return;
        lastFocus = document.activeElement;
        img.src = g.src;
        img.alt = plainText(g.alt || g.caption);
        cap.innerHTML = `${g.caption}${g.sub ? '<small>' + g.sub + '</small>' : ''}`;
        box.classList.add('open');
        close.focus();
    }
    function shut() {
        box.classList.remove('open');
        img.src = '';
        if (lastFocus && lastFocus.focus) lastFocus.focus();
        lastFocus = null;
    }

    const grid = document.getElementById('galleryGrid');
    grid.addEventListener('click', (e) => {
        const item = e.target.closest('.gallery-item');
        if (item) open(parseInt(item.dataset.idx, 10));
    });
    /* The tiles are divs, so they need their own Enter/Space handling. */
    grid.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        const item = e.target.closest('.gallery-item');
        if (!item) return;
        e.preventDefault();
        open(parseInt(item.dataset.idx, 10));
    });

    close.addEventListener('click', shut);
    box.addEventListener('click', (e) => { if (e.target === box) shut(); });
    document.addEventListener('keydown', (e) => {
        if (!box.classList.contains('open')) return;
        if (e.key === 'Escape') { shut(); return; }
        /* Keep Tab inside the dialog while it is open. */
        if (e.key === 'Tab') {
            const focusable = box.querySelectorAll('a[href], button, [tabindex]:not([tabindex="-1"])');
            if (!focusable.length) return;
            const first = focusable[0], last = focusable[focusable.length - 1];
            if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
            else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
    });
})();
})();
