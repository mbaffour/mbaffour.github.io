/* ==============================================================
   SHARED HELPERS
=============================================================== */
/* Escape text before interpolating it into innerHTML. Previously this lived
   only in builds.html; the index renderers had no escaping at all. */
const esc = s => String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));

/* ==============================================================
   THEME TOGGLE
=============================================================== */
(function() {
    const html = document.documentElement;
    const btn  = document.getElementById('themeToggle');
    if (!btn) return;

    function applyTheme(t) {
        html.setAttribute('data-theme', t);
        btn.setAttribute('aria-label', t === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
        // Update theme-color meta for mobile browsers. The page ships a pair of
        // media-scoped metas so the browser chrome is right before this runs;
        // once a theme is explicit those would fight it, so drop them and keep
        // one meta under our control.
        var paired = document.querySelectorAll('meta[name="theme-color"][media]');
        for (var i = 0; i < paired.length; i++) paired[i].parentNode.removeChild(paired[i]);
        var meta = document.querySelector('meta[name="theme-color"]:not([media])');
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute('name', 'theme-color');
            document.head.appendChild(meta);
        }
        meta.setAttribute('content', t === 'dark' ? '#121009' : '#f7f4ea');
    }

    // Init from whatever the anti-FOUC script decided. Defaulting to 'dark' when
    // the attribute is missing would override a light-mode visitor's preference
    // in exactly the case where that script failed — ask the OS instead.
    var current = html.getAttribute('data-theme');
    if (current !== 'dark' && current !== 'light') {
        current = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
            ? 'dark' : 'light';
    }
    applyTheme(current);

    btn.addEventListener('click', function() {
        var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        // Blocked storage must not stop the toggle from working for this visit.
        try { localStorage.setItem('theme', next); } catch (e) {}
    });

    // Enable smooth transitions after load (suppressed during initial paint)
    window.addEventListener('load', function() {
        html.classList.add('theme-ready');
    });
})();

/* ==============================================================
   DATA — Publications
=============================================================== */
const publications = [
    /* ── Papers / Preprints ──────────────────────────────── */
    {
        kind: "paper",
        title: "Phage N4 uses a SAR endolysin-holin system for host cell lysis",
        authors: "Awuah MB, Martin C, Chamblee JS, Tomaszewski AJ, Sullivan TE, Emilia Q, Tran S, Snowden JH, Niemiec KA, Zhu J, Ramsey J",
        journal: "bioRxiv [Preprint]",
        ids: "2025.11.12.688109 · PMID 41292803 · PMCID PMC12642591",
        year: 2025,
        doi: "https://doi.org/10.1101/2025.11.12.688109",
        status: "preprint",
        firstAuthor: true,
        code: "https://github.com/mbaffour/N4-Lysis-paper-codes",
        /* Eleven authors: a screener cannot tell what was his without opening the
           DOI, and three of five recruiter reads stalled here. Drawn only from
           work this CV already claims as his own. Replace with the manuscript's
           CRediT statement verbatim if the wording there differs. */
        contribution: "Led the lysis genetics — CRISPR-based deletion and complementation series to define the minimal lysis gene set, SAR endolysin–holin characterisation, lysis-phenotype assays, and the RNA-seq comparison of wild-type and rapid-lysis lineages — and wrote the manuscript.",
        summary: "First-author study of how phage N4 takes its host cell apart, showing it lyses via a SAR endolysin–holin system and mapping genomic regions — inside and outside the lysis cassette — involved in lysis inhibition.",
        citation: {
            plain: "Awuah MB, Martin C, Chamblee JS, Tomaszewski AJ, Sullivan TE, Emilia Q, Tran S, Snowden JH, Niemiec KA, Zhu J, Ramsey J. Phage N4 uses a SAR endolysin-holin system for host cell lysis. bioRxiv. 2025. doi:10.1101/2025.11.12.688109",
            bibtex: "@article{awuah2025n4lysis,\n  title   = {Phage {N4} uses a {SAR} endolysin-holin system for host cell lysis},\n  author  = {Awuah, Michael Baffour and Martin, C. and Chamblee, Joel S. and Tomaszewski, A. J. and Sullivan, T. E. and Emilia, Q. and Tran, S. and Snowden, J. H. and Niemiec, K. A. and Zhu, J. and Ramsey, Jolene},\n  journal = {bioRxiv},\n  year    = {2025},\n  doi     = {10.1101/2025.11.12.688109},\n  note    = {Preprint}\n}"
        },
        thumbSvg: '<svg viewBox="0 0 96 72" width="96" height="72" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><rect width="96" height="72" fill="#1a1408"/><path d="M6 62 C26 60 30 30 41 30 C49 30 50 66 92 67" fill="none" stroke="#f4c430" stroke-width="2.4" stroke-linecap="round"/><path d="M6 62 C30 58 41 24 60 18 C76 13 86 12 92 11" fill="none" stroke="#d4324b" stroke-width="2.4" stroke-linecap="round"/></svg>'
    },
    {
        /* The thesis result the Patterson Fellowship was awarded for. Listing it
           as in-preparation is the honest place for it: it is real work with a
           public award citation and two conference presentations behind it, but
           it is not what the preprint reports, and the two were being conflated. */
        kind: "paper",
        title: "A novel regulator of lysis timing in bacteriophage N4",
        authors: "Awuah MB, Ramsey J",
        journal: "Manuscript in preparation",
        year: 2026,
        status: "inprep",
        firstAuthor: true,
        summary: "Identification and characterisation of a novel regulator of the lysis-timing decision in phage N4: an essential gene whose mutation drives rapid lysis. The work recognised by the Thomas L. Patterson Graduate Student Fellowship (2025) and presented at BIOGSA and the Texas ASM Branch Meeting (2024). The gene is unnamed here until the manuscript is submitted."
    },
    {
        kind: "paper",
        title: "Complete genome sequence of <i>Escherichia</i> Siphophage Serwaa",
        authors: "Debrah MA, Awuah MB, Koh A, Ramsey J",
        journal: "Microbiology Resource Announcements",
        ids: "e01222-25 · PMID 42214348 · PMCID PMC13348217",
        year: 2026,
        doi: "https://doi.org/10.1128/mra.01222-25",
        status: "published",
        // The accessions ARE the deliverable of a genome announcement — the
        // first thing another phage lab checks, and previously nowhere on the site.
        data: [
            { label: "GenBank",    id: "PX021331",     url: "https://www.ncbi.nlm.nih.gov/nuccore/PX021331" },
            { label: "BioProject", id: "PRJNA222858",  url: "https://www.ncbi.nlm.nih.gov/bioproject/PRJNA222858" },
            { label: "SRA",        id: "SRR34773693",  url: "https://www.ncbi.nlm.nih.gov/sra/SRR34773693" },
            { label: "BioSample",  id: "SAMN50231104", url: "https://www.ncbi.nlm.nih.gov/biosample/SAMN50231104" }
        ],
        citation: {
            plain: "Debrah MA, Awuah MB, Koh A, Ramsey J. Complete genome sequence of Escherichia siphophage Serwaa. Microbiol Resour Announc. 2026;15(7):e01222-25. doi:10.1128/mra.01222-25",
            bibtex: "@article{debrah2026serwaa,\n  title   = {Complete genome sequence of {Escherichia} siphophage {Serwaa}},\n  author  = {Debrah, Michael A. and Awuah, Michael Baffour and Koh, Annie and Ramsey, Jolene},\n  journal = {Microbiology Resource Announcements},\n  volume  = {15},\n  number  = {7},\n  pages   = {e01222-25},\n  year    = {2026},\n  doi     = {10.1128/mra.01222-25}\n}"
        },
        thumb: "blog/images/serwaa-tem-thumb.webp",
        thumbAlt: "Transmission electron micrograph of phage Serwaa"
    },
    /* ── Oral talks ──────────────────────────────────────── */
    {
        kind: "talk",
        title: "Bacteriophage N4 Lysis Inhibition: Unraveling Ancient Mechanism with Modern Insights",
        authors: "Awuah MB",
        journal: "Bio &amp; Chem Sciences Symposium · College Station, TX",
        year: 2024,
        status: "talk"
    },
    {
        kind: "talk",
        title: "Bacteriophage N4 Lysis Inhibition — Ancient Conundrum Meets Novel Culprit",
        authors: "Awuah MB",
        journal: "Texas ASM Branch Meeting · Cedar Hill, TX",
        year: 2024,
        status: "talk"
    },
    {
        kind: "talk",
        title: "Delaying the Inevitable — Bacteriophage N4 Lysis Inhibition",
        authors: "Awuah MB",
        journal: "BIOGSA · College Station, TX",
        year: 2024,
        status: "talk"
    },
    /* ── Posters ─────────────────────────────────────────── */
    {
        kind: "poster",
        title: "Phage N4 lysis inhibition — the viral death race",
        journal: "Students' &amp; Postdoc Research Conference · College Station, TX",
        year: 2025,
        status: "poster"
    },
    {
        kind: "poster",
        title: "Breaking Up The Breakdown: How an Open Reading Frame Inhibits Lysis in Bacteriophage N4",
        journal: "Texas ASM Branch Meeting · UTMB, Galveston, TX",
        year: 2024,
        status: "poster"
    },
    {
        kind: "poster",
        title: "Breaking Up The Breakdown: How an Open Reading Frame Inhibits Lysis in Bacteriophage N4",
        journal: "Molecular Genetics of Bacteria &amp; Phages Meeting · UW–Madison",
        year: 2024,
        status: "poster"
    },
    {
        kind: "poster",
        title: "Phage N4 lysis inhibition — the viral death race (Poster + Blitz)",
        journal: "Students' &amp; Postdoc Research Conference · College Station, TX",
        year: 2024,
        status: "poster"
    },
    {
        kind: "poster",
        title: "Delaying the Inevitable — Bacteriophage N4 Lysis Inhibition",
        journal: "Molecular Genetics of Bacteria &amp; Phages Meeting · UW–Madison",
        year: 2023,
        status: "poster"
    },
    {
        kind: "poster",
        title: "Phage Lysis Inhibition is Phruitful Procrastination",
        journal: "Diversity in Science Symposium · Texas A&amp;M University",
        year: 2023,
        status: "poster"
    },
    {
        kind: "poster",
        title: "Phage Lysis Inhibition is Phruitful Procrastination",
        journal: "Texas ASM Branch Meeting · Abilene Christian University",
        year: 2023,
        status: "poster"
    }
];

/* ==============================================================
   DATA — Tools (research/scientific)
=============================================================== */
const tools = [
    {
        title: "Lysis Curve Plotter",
        repo: "https://github.com/mbaffour/lysis-curve-app",
        featured: true,
        blurb: "Browser-based R Shiny app for plotting phage lysis curves — 19 metrics, 7 variability modes, full export. Replaces hours of ggplot2 boilerplate per experiment.",
        tech: ["R Shiny", "OD600", "Data Viz"],
        stack: "r",
        blog: "https://mbaffour.github.io/lysis-curve-app/blogpost.html",
        app:  "https://mbaffour.github.io/lysis-curve-app/",
        label: "Lysis Curve Plotter",
        preview: "lysis"
    },
    {
        title: "Dilution Designer",
        repo: "https://github.com/mbaffour/dilution-designer",
        blurb: "96-well plate experiment designer — stock volumes, dilution factors, and pipetting maps in seconds. Built because I kept doing the math by hand.",
        tech: ["JavaScript", "Lab Tool", "Offline"],
        stack: "js",
        blog: "https://mbaffour.github.io/dilution-designer/blog.html",
        app:  "https://mbaffour.github.io/dilution-designer/",
        label: "96-Well Designer",
        preview: "plate"
    },
    {
        title: "FigureLab",
        repo: "https://github.com/mbaffour/FigureLab",
        featured: true,
        blurb: "Browser-based microscopy figure assembly — no installs, no exports, just open and build publication-ready panels.",
        tech: ["JavaScript", "Microscopy", "Figures"],
        stack: "js",
        blog: "https://mbaffour.github.io/FigureLab/",
        app:  "https://mbaffour.github.io/FigureLab/figure_lab.html",
        label: "Figure Assembly",
        preview: "figure",
        doi: "10.5281/zenodo.21269456",
        citation: {
            plain: "Awuah, M. B. (2026). FigureLab: a browser-based tool for assembling publication-quality scientific figures (Version 3.5) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.21269456",
            bibtex: "@software{awuah_figurelab_2026,\n  author    = {Awuah, Michael Baffour},\n  title     = {{FigureLab}: a browser-based tool for assembling publication-quality scientific figures},\n  year      = {2026},\n  version   = {3.5},\n  publisher = {Zenodo},\n  doi       = {10.5281/zenodo.21269456},\n  url       = {https://doi.org/10.5281/zenodo.21269456}\n}"
        },
        /* Independent use of the tool in someone else's published paper. This is
           the only evidence on the site that the software is used by people who
           did not build it, which is the thing a hiring committee actually wants
           from "I build open tools". */
        usedIn: [{
            quote: "use of the FigureLab web-based application developed by Michael Baffour Awuah",
            citation: "Hoxha EM, Brown GD, Niemiec KA, Ramsey J. The complete genome sequence of Caulobacter phages Senya and Shash. Microbiol Resour Announc. 2026;15(8):e00457-26.",
            doi: "https://doi.org/10.1128/mra.00457-26"
        }]
    },
    {
        title: "CellMorphR",
        repo: "https://github.com/mbaffour/CellMorphR",
        featured: true,
        blurb: "Python pipeline for quantifying cell morphology from microscopy data — statistics, publication-ready plots, reproducible workflows.",
        tech: ["Python", "Morphology", "Stats"],
        stack: "py",
        blog: "blog/cellmorphr.html",
        app:  "https://github.com/mbaffour/CellMorphR",
        label: "Cell Morphology",
        preview: "cellmorph"
    },
    {
        title: "AlphaFold Stoichiometry Generator",
        repo: "https://github.com/mbaffour/AlphaFold-Stoichiometry-Generator",
        blurb: "R script that auto-generates stoichiometry strings for AlphaFold multi-chain predictions — kill the manual formatting errors.",
        tech: ["R", "AlphaFold", "Automation"],
        stack: "r",
        blog: "https://github.com/mbaffour/AlphaFold-Stoichiometry-Generator",
        app:  "https://github.com/mbaffour/AlphaFold-Stoichiometry-Generator",
        label: "AlphaFold Helper",
        preview: "alphafold"
    },
    {
        title: "PooledPPI",
        repo: "https://github.com/mbaffour/PooledPPI",
        featured: true,
        blurb: "R Shiny app for genome-scale protein-protein interaction screens — designs pooled AlphaFold 3 jobs, imports ipTM results, applies size-bias correction, and builds publication-ready interaction networks.",
        tech: ["R Shiny", "AlphaFold 3", "PPI"],
        stack: "r",
        blog: "https://github.com/mbaffour/PooledPPI",
        app:  "https://github.com/mbaffour/PooledPPI",
        label: "Pooled PPI Screens",
        preview: "alphafold"
    },
    {
        title: "killcurveplot",
        repo: "https://github.com/mbaffour/killcurveplot",
        blurb: "Lightweight R package for generating clean lysis and kill curves from raw OD data. Fast, reproducible, ggplot2-flavored.",
        tech: ["R Package", "OD600", "Viz"],
        stack: "r",
        blog: "https://github.com/mbaffour/killcurveplot",
        app:  "https://github.com/mbaffour/killcurveplot",
        label: "killcurveplot",
        preview: "kill"
    },
    {
        title: "N4 Lysis Paper Codes",
        repo: "https://github.com/mbaffour/N4-Lysis-paper-codes",
        blurb: "Shiny apps released alongside the N4 lysis preprint — lysis curve visualization, FASTA reformatting, and reproducibility scaffolding.",
        tech: ["R Shiny", "N4", "Reproducibility"],
        stack: "r",
        blog: "https://github.com/mbaffour/N4-Lysis-paper-codes",
        app:  "https://github.com/mbaffour/N4-Lysis-paper-codes",
        label: "Paper Code Repo",
        preview: "paper"
    },
    {
        title: "CFU Plot Studio",
        repo: "https://github.com/mbaffour/cfu-plot-studio",
        featured: true,
        blurb: "R Shiny app for publication-ready CFU plots — bar charts, error bars, significance annotations, and reproducible figure exports in one place.",
        tech: ["R Shiny", "CFU", "Statistics"],
        stack: "r",
        blog: "blog/cfu-plot-studio.html",
        app:  "https://mbaffour.github.io/cfu-plot-studio/",
        label: "CFU Plotter",
        preview: "cfu"
    },
    {
        title: "CFU Calculator",
        repo: "https://github.com/mbaffour/cfu-calculator",
        blurb: "Colony counts to CFU/mL in one browser page — replicates, countable-window flags, detection limits, and a real Excel workbook on the way out. No installs, nothing uploaded.",
        tech: ["JavaScript", "CFU", "Offline"],
        stack: "js",
        blog: "blog/cfu-calculator.html",
        app:  "https://mbaffour.github.io/cfu-calculator/",
        label: "CFU Bench Calc",
        preview: "cfucalc"
    },
    {
        title: "Genomics Kitchen",
        repo: "https://github.com/mbaffour/genomics-kitchen",
        blurb: "Browser-based sequence preparation toolkit — trim, filter, dedupe, and format sequences for reproducible genomics workflows. No installs.",
        tech: ["JavaScript", "Genomics", "Offline"],
        stack: "js",
        blog: "blog/genomics-kitchen.html",
        app:  "https://mbaffour.github.io/genomics-kitchen/",
        label: "Sequence Prep",
        preview: "genomicskitchen"
    },
    {
        title: "SeqSieve",
        repo: "https://github.com/mbaffour/SeqSieve",
        blurb: "Browser-based exact sequence deduplication with provenance-preserving exports — upload a FASTA, sieve out duplicates, download clean sequences.",
        tech: ["JavaScript", "FASTA", "Offline"],
        stack: "js",
        blog: "https://mbaffour.github.io/SeqSieve/blog.html",
        app:  "https://mbaffour.github.io/SeqSieve/",
        label: "Seq Deduplication",
        preview: "seqsieve"
    },
    {
        title: "ReadQraft",
        repo: "https://github.com/mbaffour/ReadQraft",
        blurb: "Desktop FASTQ quality control and trimming without terminal fear — drag in reads, inspect Phred scores, set trim thresholds, export clean files.",
        tech: ["Python", "FASTQ", "QC"],
        stack: "py",
        blog: "https://mbaffour.github.io/ReadQraft/blogpost.html",
        app:  "https://github.com/mbaffour/ReadQraft",
        label: "FASTQ QC",
        preview: "readqraft"
    },
    {
        title: "Gibson Assembly Calculator",
        repo: "https://github.com/mbaffour/gibson-assembly-calculator",
        blurb: "Browser-based Gibson Assembly setup — enter fragment lengths and concentrations, get exact pipetting volumes at NEB-recommended molar ratios. Export CSV, save reactions. Runs entirely client-side.",
        tech: ["JavaScript", "Cloning", "Offline"],
        stack: "js",
        blog: "blog/gibson-assembly-calculator.html",
        app:  "https://mbaffour.github.io/gibson-assembly-calculator/",
        label: "Gibson Calculator",
        preview: "gibson"
    },
    {
        title: "Plaque Toolkit",
        repo: "https://github.com/mbaffour/plaque-toolkit",
        featured: true,
        /* Provenance stated exactly as the repo states it: the citable engine is
           Trofimova & Jaschke's, PlaqSeg is a third-party YOLO model, and the
           part that is mine is the fusion pipeline and the trained classifier. */
        blurb: "Measures bacteriophage plaques straight from Petri-dish photos — size, turbidity, count, and titer — as a desktop app and CLI. Four detection engines: the published, citable Trofimova &amp; Jaschke method preserved byte-for-byte, plus a pipeline I built that fuses it with a third-party YOLO segmentation model and a ResNet-18 plaque-vs-texture classifier I trained (15,659 boxes; leave-one-plate-out F1&nbsp;≈&nbsp;0.95). A click-to-correct editor means a human always has the last word on the count.",
        tech: ["Python", "ResNet-18", "Computer Vision", "PySide6"],
        stack: "py",
        blog: "blog/plaque-toolkit.html",
        app:  "https://github.com/mbaffour/plaque-toolkit",
        label: "Plaque Quantification",
        preview: "plaque"
    },
    {
        title: "HMM Homologue Finder",
        repo: "https://github.com/mbaffour/hmm-homologue-finder",
        featured: true,
        blurb: "One-command, reproducible HMM-based homologue discovery for protein families across phage and viral databases — six-frame search, ORF validation, and iterative convergence, with golden-file regression tests baked in.",
        tech: ["Python", "HMMER", "Bioinformatics"],
        stack: "py",
        blog: "blog/hmm-homologue-finder.html",
        app:  "https://github.com/mbaffour/hmm-homologue-finder",
        label: "Homologue Discovery",
        preview: "hmm"
    },
    {
        title: "HMM Discovery App",
        repo: "https://github.com/mbaffour/hmm-discovery-app",
        blurb: "The no-code, in-browser version of the homologue workflow: alignment, HMM building, database search, hit classification, synteny, phylogeny, and reproducible export — the whole pipeline without touching a terminal.",
        tech: ["Python", "Shiny", "Bioinformatics"],
        stack: "py",
        blog: "blog/hmm-discovery-app.html",
        app:  "https://mbaffour.github.io/hmm-discovery-app/",
        label: "Protein Family Discovery",
        preview: "hmm"
    }
];


/* ==============================================================
   DATA — Blog posts
   Add new posts at the TOP (most recent first).
   tags drive the filter buttons automatically.
=============================================================== */
const posts = [
    {
        title: "CFU Calculator — colony counts without the arithmetic",
        date: "August 24, 2026",
        iso: "2026-08-24",
        tags: ["Research Software", "Bench"],
        blurb: "A single-file browser calculator for bacterial colony counts: name samples, log replicates at any dilution, get mean ± SD with countable-window flags and detection limits, and export a real Excel workbook.",
        url: "blog/cfu-calculator.html"
    },
    {
        title: "Watermark Remover — the characters you cannot see",
        date: "August 17, 2026",
        iso: "2026-08-17",
        tags: ["Side Builds"],
        blurb: "Unicode has a complete invisible alphabet, and a paragraph can carry a hidden message in it without looking any different. A browser tool that finds those characters — plus EXIF, C2PA and document properties — decodes what was in them, and removes them. Nothing is uploaded.",
        url: "blog/watermark-remover.html"
    },
    {
        title: "Plaque Toolkit — plate photo to defensible numbers",
        date: "June 20, 2026",
        iso: "2026-06-20",
        tags: ["Research Software", "Phage Biology"],
        blurb: "Measures bacteriophage plaques straight from a Petri-dish photo — size, turbidity, count and titer — so wild-type and mutant phages compare on the same footing.",
        url: "blog/plaque-toolkit.html"
    },
    {
        title: "Serwaa: My First Scientific Paper",
        date: "May 30, 2026",
        iso: "2026-05-30",
        tags: ["Lab Notes", "Phage Biology"],
        blurb: "The story behind my first peer-reviewed publication — a phage named after my grandmother, the undergraduate who made it happen, and seeing my name in print.",
        image: "blog/images/serwaa-tem-thumb.webp",
        url: "blog/serwaa-first-paper.html"
    },
    {
        title: "LifeXP — Track your life. Level it up.",
        date: "May 14, 2026",
        iso: "2026-05-14",
        tags: ["Side Builds"],
        blurb: "A gamified, local-first life tracker: habits, time, quests and life metrics with XP, levels and streaks. All data stays on your device.",
        url: "blog/lifexp.html"
    },
    {
        title: "Number Tug — arithmetic tug-of-war on one device",
        date: "May 2, 2026",
        iso: "2026-05-02",
        tags: ["Side Builds"],
        blurb: "A same-device arithmetic tug-of-war. Answer fast to pull the rope your way — solo, two-player on one keyboard, or against the computer. Free, in the browser.",
        url: "blog/number-tug.html"
    },
    {
        title: "HMM Discovery App — the pipeline, no terminal needed",
        date: "April 8, 2026",
        iso: "2026-04-08",
        tags: ["Research Software", "Bioinformatics"],
        blurb: "A no-code web app running the whole profile-HMM discovery pipeline — alignment, HMM build, database search, classification and phylogeny — in your browser.",
        url: "blog/hmm-discovery-app.html"
    },
    {
        title: "CellMorphR — single-cell morphometry, done honestly",
        date: "March 18, 2026",
        iso: "2026-03-18",
        tags: ["Research Software", "Statistics"],
        blurb: "Quantifies single-cell morphology over time and keeps the statistics honest: per-replicate summaries first, then models at the level the design supports.",
        url: "blog/cellmorphr.html"
    },
    {
        title: "HMM Homologue Finder — one reproducible command",
        date: "March 2, 2026",
        iso: "2026-03-02",
        tags: ["Research Software", "Bioinformatics"],
        blurb: "A reproducible HMM-based homologue-discovery CLI: six-frame search, ORF validation, iterate-to-convergence, regression tests and a locked environment.",
        url: "blog/hmm-homologue-finder.html"
    },
    {
        title: "CFU Plot Studio — reproducible colony-count figures",
        date: "February 11, 2026",
        iso: "2026-02-11",
        tags: ["Research Software", "Statistics"],
        blurb: "An R/Shiny app turning replicate-level CFU data into publication-ready bar plots with log10 statistics, significance annotations, and a reproducible export.",
        url: "blog/cfu-plot-studio.html"
    },
    {
        title: "Genomics Kitchen — the prep station for sequence work",
        date: "January 22, 2026",
        iso: "2026-01-22",
        tags: ["Research Software", "Bioinformatics"],
        blurb: "Five browser-based sequence-prep tools: dedup, QC, comparison, ORF finding and HMM-ready protein cleanup. No installs, no server, no data leaving your machine.",
        url: "blog/genomics-kitchen.html"
    },
    {
        title: "Gibson Assembly Calculator — exact pipetting volumes",
        date: "November 30, 2025",
        iso: "2025-11-30",
        tags: ["Research Software", "Bench"],
        blurb: "Enter fragment lengths and concentrations, read off exact pipetting volumes at NEB-recommended molar ratios. A single page, no account, no spreadsheet.",
        url: "blog/gibson-assembly-calculator.html"
    }
];

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

/* ==============================================================
   SVG PREVIEW LIBRARY
   Tiny inline SVGs that hint at what each tool does.
=============================================================== */
const SVG_PREVIEWS = {
    lysis: `<svg viewBox="0 0 320 160" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
        <defs><linearGradient id="lg1" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#1f9249" stop-opacity="0.25"/><stop offset="100%" stop-color="#1f9249" stop-opacity="0"/>
        </linearGradient></defs>
        <rect width="320" height="160" fill="#0d130a"/>
        <g stroke="#1f9249" stroke-opacity="0.15" stroke-width="1">
            <line x1="40" y1="30" x2="300" y2="30"/><line x1="40" y1="70" x2="300" y2="70"/>
            <line x1="40" y1="110" x2="300" y2="110"/>
        </g>
        <path d="M40,120 C90,118 130,90 165,55 C190,30 215,22 240,30 C260,38 280,90 300,135" fill="none" stroke="#f4c430" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M40,120 C90,118 130,95 175,68 C210,48 245,45 290,135" fill="none" stroke="#d4324b" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="4 3"/>
        <path d="M40,120 C90,118 130,90 165,55 C190,30 215,22 240,30 C260,38 280,90 300,135 L300,160 L40,160 Z" fill="url(#lg1)"/>
    </svg>`,
    plate: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0a1018"/>
        <g>${(()=>{let s='';for(let r=0;r<6;r++){for(let c=0;c<12;c++){const cx=30+c*22, cy=18+r*22;const fill=(r+c)%5===0?'#f4c430':(r+c)%3===0?'#1f9249':'#152035';s+=`<circle cx="${cx}" cy="${cy}" r="7" fill="${fill}" opacity="0.85" stroke="#0a1018" stroke-width="1"/>`;}}return s;})()}</g>
    </svg>`,
    figure: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#15101a"/>
        <rect x="14" y="14" width="92" height="62" fill="#2a1f3a" stroke="#f4c430" stroke-width="1.5"/>
        <rect x="116" y="14" width="92" height="62" fill="#1f2a35" stroke="#1f9249" stroke-width="1.5"/>
        <rect x="218" y="14" width="88" height="62" fill="#352323" stroke="#d4324b" stroke-width="1.5"/>
        <rect x="14" y="86" width="142" height="62" fill="#1f2a35" stroke="#1f9249" stroke-width="1.5"/>
        <rect x="166" y="86" width="140" height="62" fill="#2a1f3a" stroke="#f4c430" stroke-width="1.5"/>
        <text x="20" y="32" font-family="JetBrains Mono" font-size="8" fill="#f4c430">A</text>
        <text x="122" y="32" font-family="JetBrains Mono" font-size="8" fill="#1f9249">B</text>
        <text x="224" y="32" font-family="JetBrains Mono" font-size="8" fill="#d4324b">C</text>
        <text x="20" y="104" font-family="JetBrains Mono" font-size="8" fill="#1f9249">D</text>
        <text x="172" y="104" font-family="JetBrains Mono" font-size="8" fill="#f4c430">E</text>
    </svg>`,
    mask: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0a1408"/>
        <g font-family="JetBrains Mono" font-size="10">
            <rect x="14" y="14" width="290" height="18" fill="rgba(244,196,48,0.08)"/>
            <text x="22" y="27" fill="#f4c430">name,email,ssn,dob</text>
            <text x="22" y="50" fill="#7a8868">Alice ✱✱✱,  ✱✱✱@✱✱✱,  ✱✱✱-✱✱-✱✱✱✱,  ✱✱/✱✱/✱✱</text>
            <text x="22" y="68" fill="#7a8868">Bob ✱✱✱,    ✱✱✱@✱✱✱,  ✱✱✱-✱✱-✱✱✱✱,  ✱✱/✱✱/✱✱</text>
            <text x="22" y="86" fill="#7a8868">Carol ✱✱✱,  ✱✱✱@✱✱✱,  ✱✱✱-✱✱-✱✱✱✱,  ✱✱/✱✱/✱✱</text>
            <text x="22" y="104" fill="#7a8868">Dan ✱✱✱,    ✱✱✱@✱✱✱,  ✱✱✱-✱✱-✱✱✱✱,  ✱✱/✱✱/✱✱</text>
            <text x="22" y="138" fill="#1f9249" font-size="14">🔒 anonymized · 0 uploads</text>
        </g>
    </svg>`,
    crop: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#1a0e08"/>
        <g>
            <rect x="20" y="20" width="80" height="60" fill="#3a2418" stroke="#f4c430" stroke-width="1.5"/>
            <rect x="110" y="20" width="80" height="60" fill="#3a2418" stroke="#f4c430" stroke-width="1.5" stroke-dasharray="3 3"/>
            <rect x="200" y="20" width="80" height="60" fill="#3a2418" stroke="#f4c430" stroke-width="1.5"/>
            <circle cx="60" cy="120" r="22" fill="#3a2418" stroke="#1f9249" stroke-width="1.5"/>
            <polygon points="150,98 192,98 192,140 150,140" fill="#3a2418" stroke="#d4324b" stroke-width="1.5"/>
            <polygon points="240,98 282,98 282,140 240,140" fill="#3a2418" stroke="#f4c430" stroke-width="1.5"/>
        </g>
    </svg>`,
    plaque: `<svg viewBox="0 0 320 160" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0d1409"/>
        <circle cx="158" cy="78" r="82" fill="rgba(26,128,64,0.16)" stroke="#1f9249" stroke-width="2"/>
        <g fill="#0d1409" stroke="#f4c430" stroke-width="1.3" stroke-opacity="0.85">
            <circle cx="126" cy="52" r="12"/><circle cx="188" cy="60" r="8"/>
            <circle cx="150" cy="96" r="15"/><circle cx="204" cy="98" r="9"/>
            <circle cx="112" cy="90" r="7"/><circle cx="176" cy="122" r="6"/>
            <circle cx="210" cy="70" r="6"/><circle cx="138" cy="122" r="5"/>
        </g>
        <rect x="14" y="132" width="176" height="16" rx="3" fill="rgba(244,196,48,0.10)"/>
        <text x="22" y="144" font-family="JetBrains Mono" font-size="9" fill="#f4c430">8 plaques · titer 4.2e8 pfu/mL</text>
    </svg>`,
    hmm: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0a1210"/>
        <g font-family="JetBrains Mono" font-size="13" font-weight="600">${(()=>{const rows=['MKVLTAEG','MKILSAEG','MRVLTADG','MKVLTPEG'];const cons=[1,1,0,1,1,0,1,1];const cw=34,x0=22,y0=28;let s='';for(let r=0;r<rows.length;r++){for(let c=0;c<rows[r].length;c++){const col=cons[c]?'#f4c430':'#5f7d6a';s+=`<text x="${x0+c*cw}" y="${y0+r*19}" fill="${col}">${rows[r][c]}</text>`;}}for(let c=0;c<cons.length;c++){const h=cons[c]?24:9;s+=`<rect x="${x0+c*cw-2}" y="${138-h}" width="18" height="${h}" fill="${cons[c]?'#1f9249':'#254036'}"/>`;}return s;})()}</g>
    </svg>`,
    tug: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0e0b14"/>
        <line x1="24" y1="82" x2="296" y2="82" stroke="#5a4a2a" stroke-width="4" stroke-linecap="round"/>
        <circle cx="132" cy="82" r="9" fill="#f4c430"/>
        <rect x="34" y="56" width="66" height="52" rx="9" fill="rgba(26,128,64,0.22)" stroke="#1f9249" stroke-width="2"/>
        <rect x="220" y="56" width="66" height="52" rx="9" fill="rgba(212,50,75,0.20)" stroke="#d4324b" stroke-width="2"/>
        <text x="46" y="89" font-family="JetBrains Mono" font-size="19" fill="#3ec17a">7+5</text>
        <text x="232" y="89" font-family="JetBrains Mono" font-size="19" fill="#e0637a">9×3</text>
        <text x="150" y="42" font-family="Fraunces, serif" font-size="17" fill="#f4c430">= 12</text>
    </svg>`,
    xp: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0b1016"/>
        <circle cx="62" cy="74" r="34" fill="none" stroke="#1e2a22" stroke-width="9"/>
        <circle cx="62" cy="74" r="34" fill="none" stroke="#f4c430" stroke-width="9" stroke-linecap="round" stroke-dasharray="150 214" transform="rotate(-90 62 74)"/>
        <text x="62" y="72" text-anchor="middle" font-family="Fraunces, serif" font-size="22" fill="#f5edd8">7</text>
        <text x="62" y="88" text-anchor="middle" font-family="JetBrains Mono" font-size="7" fill="#a08652">LEVEL</text>
        <g>${(()=>{let s='';for(let r=0;r<3;r++){for(let c=0;c<10;c++){const on=(r*10+c)%3!==0;s+=`<rect x="${120+c*18}" y="${34+r*18}" width="13" height="13" rx="3" fill="${on?'#1f9249':'#1a2620'}"/>`;}}return s;})()}</g>
        <rect x="120" y="120" width="182" height="10" rx="5" fill="#1a2620"/>
        <rect x="120" y="120" width="128" height="10" rx="5" fill="#f4c430"/>
    </svg>`,
    cellmorph: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#071428"/>
        <g>
            <ellipse cx="80" cy="60" rx="35" ry="22" fill="rgba(244,196,48,0.18)" stroke="#f4c430" stroke-width="1.5"/>
            <ellipse cx="180" cy="55" rx="25" ry="20" fill="rgba(244,196,48,0.18)" stroke="#f4c430" stroke-width="1.5"/>
            <ellipse cx="245" cy="80" rx="30" ry="18" fill="rgba(244,196,48,0.18)" stroke="#f4c430" stroke-width="1.5"/>
            <ellipse cx="100" cy="120" rx="28" ry="20" fill="rgba(244,196,48,0.18)" stroke="#f4c430" stroke-width="1.5"/>
            <ellipse cx="200" cy="125" rx="32" ry="15" fill="rgba(244,196,48,0.18)" stroke="#f4c430" stroke-width="1.5"/>
            <line x1="115" y1="60" x2="155" y2="55" stroke="#1f9249" stroke-width="1" stroke-dasharray="2 2"/>
            <text x="120" y="50" font-family="JetBrains Mono" font-size="7" fill="#1f9249">42μm</text>
        </g>
    </svg>`,
    alphafold: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0e1608"/>
        <path d="M30,80 Q60,30 90,80 T150,80 T210,80 T270,80 T300,80" fill="none" stroke="#f4c430" stroke-width="3" stroke-linecap="round"/>
        <path d="M40,100 Q70,50 100,100 T160,100 T220,100 T280,100" fill="none" stroke="#1f9249" stroke-width="3" stroke-linecap="round" opacity="0.8"/>
        <path d="M30,120 Q60,70 90,120 T150,120 T210,120 T270,120 T300,120" fill="none" stroke="#d4324b" stroke-width="3" stroke-linecap="round" opacity="0.7"/>
        <g font-family="JetBrains Mono" font-size="9" fill="#7a8862">
            <text x="20" y="20">chain A:</text><text x="80" y="20" fill="#f4c430">2:1:3</text>
            <text x="160" y="20" fill="#7a8862">→ stoichiometry</text>
        </g>
    </svg>`,
    kill: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#160b07"/>
        <g stroke="rgba(244,196,48,0.1)" stroke-width="1"><line x1="40" y1="40" x2="300" y2="40"/><line x1="40" y1="80" x2="300" y2="80"/><line x1="40" y1="120" x2="300" y2="120"/></g>
        <path d="M40,40 C80,42 120,50 160,90 C200,130 240,140 300,142" fill="none" stroke="#d4324b" stroke-width="2.5"/>
        <path d="M40,50 C80,52 120,65 160,105 C200,135 240,142 300,144" fill="none" stroke="#f4c430" stroke-width="2.5"/>
        <text x="270" y="35" font-family="JetBrains Mono" font-size="9" fill="#7a8868">OD₆₀₀</text>
    </svg>`,
    fasta: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#081508"/>
        <g font-family="JetBrains Mono" font-size="10">
            <text x="16" y="22" fill="#f4c430">&gt;phage_001</text>
            <text x="16" y="36" fill="#a8c490">ATCGATCGTAGCTAGCTAGCT</text>
            <text x="16" y="56" fill="#f4c430">&gt;phage_002</text>
            <text x="16" y="70" fill="#a8c490">GCTAGCTAGCTAGCTACGTAC</text>
            <text x="16" y="90" fill="#7a6238" text-decoration="line-through">&gt;phage_001_dup</text>
            <text x="16" y="104" fill="#7a6238" text-decoration="line-through">ATCGATCGTAGCTAGCTAGCT</text>
            <text x="16" y="130" fill="#1f9249" font-size="12">✓ Deduplicated</text>
            <text x="160" y="130" fill="#7a8868">3 → 2</text>
        </g>
    </svg>`,
    paper: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#081212"/>
        <g>
            <rect x="40" y="20" width="120" height="120" fill="#0d1e1e" stroke="#f4c430" stroke-width="1.5"/>
            <line x1="50" y1="40" x2="150" y2="40" stroke="#f4c430" stroke-width="2"/>
            <line x1="50" y1="55" x2="140" y2="55" stroke="rgba(245,237,216,0.4)"/>
            <line x1="50" y1="65" x2="135" y2="65" stroke="rgba(245,237,216,0.3)"/>
            <line x1="50" y1="75" x2="148" y2="75" stroke="rgba(245,237,216,0.3)"/>
            <rect x="50" y="90" width="100" height="40" fill="rgba(26,128,64,0.15)" stroke="#1f9249"/>
            <text x="58" y="110" font-family="JetBrains Mono" font-size="8" fill="#1f9249">Fig 1.</text>
            <rect x="180" y="40" width="120" height="100" fill="#0d1e1e" stroke="#1f9249" stroke-width="1.5"/>
            <text x="195" y="60" font-family="JetBrains Mono" font-size="9" fill="#1f9249">code/</text>
            <text x="195" y="78" font-family="JetBrains Mono" font-size="9" fill="#a8c4a0">  lysis.R</text>
            <text x="195" y="94" font-family="JetBrains Mono" font-size="9" fill="#a8c4a0">  fasta.R</text>
            <text x="195" y="110" font-family="JetBrains Mono" font-size="9" fill="#a8c4a0">  shiny.R</text>
            <text x="195" y="128" font-family="JetBrains Mono" font-size="9" fill="#f4c430">  README</text>
        </g>
    </svg>`,
    qr: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#1a1200"/>
        <g transform="translate(110,15)">
            <rect x="0" y="0" width="100" height="100" fill="#f4c430"/>
            <g fill="#0a0802">${(()=>{let s='';const m=[[1,1,1,1,1,1,1,0,1,0,1,0,1,1,1,1,1,1,1],[1,0,0,0,0,0,1,0,1,1,0,0,1,0,0,0,0,0,1],[1,0,1,1,1,0,1,0,0,1,1,0,1,0,1,1,1,0,1],[1,0,1,1,1,0,1,1,0,1,0,1,1,0,1,1,1,0,1],[1,0,1,1,1,0,1,0,1,0,1,1,1,0,1,1,1,0,1],[1,0,0,0,0,0,1,1,1,0,0,1,1,0,0,0,0,0,1],[1,1,1,1,1,1,1,0,1,0,1,0,1,1,1,1,1,1,1],[0,0,0,0,0,0,0,0,1,1,0,1,0,0,0,0,0,0,0],[1,1,0,1,1,1,1,1,0,0,1,1,0,1,1,0,1,0,1],[0,0,1,0,1,0,0,1,1,1,1,0,1,0,1,1,0,1,0],[1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,0,1,1,1],[0,1,1,0,1,0,0,1,1,1,0,0,1,0,1,1,0,0,0],[1,0,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1],[0,0,0,0,0,0,0,1,1,0,1,0,1,0,0,0,0,0,1],[1,1,1,1,1,1,1,0,0,1,0,1,1,0,1,0,1,0,1],[1,0,0,0,0,0,1,1,0,0,1,0,0,1,1,1,1,0,1],[1,0,1,1,1,0,1,0,1,1,1,0,1,1,0,0,1,1,1],[1,0,1,1,1,0,1,1,0,0,0,1,1,0,1,0,1,1,0],[1,0,0,0,0,0,1,0,1,1,0,0,1,1,1,1,1,1,1]];for(let r=0;r<m.length;r++)for(let c=0;c<m[r].length;c++)if(m[r][c])s+=`<rect x="${c*5}" y="${r*5}" width="5" height="5"/>`;return s;})()}</g>
            <!-- Adinkra inside corner -->
            <g transform="translate(0,0)"><rect width="35" height="35" fill="#1f9249"/><circle cx="17.5" cy="17.5" r="10" fill="none" stroke="#f4c430" stroke-width="2"/><circle cx="17.5" cy="17.5" r="3" fill="#f4c430"/></g>
        </g>
    </svg>`,
    nclex: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0a1525"/>
        <rect x="20" y="20" width="280" height="120" fill="#162236" stroke="#1f9249" stroke-width="1.5" rx="6"/>
        <text x="32" y="40" font-family="JetBrains Mono" font-size="9" fill="#f4c430">Q. 47 / 75 · pharmacology</text>
        <text x="32" y="58" font-family="Inter" font-size="9" fill="#d8dceb">A patient on warfarin presents</text>
        <text x="32" y="70" font-family="Inter" font-size="9" fill="#d8dceb">with INR 4.8. Best action?</text>
        <g font-family="JetBrains Mono" font-size="9">
            <rect x="32" y="84" width="256" height="14" fill="rgba(26,128,64,0.15)" stroke="#1f9249"/><text x="38" y="94" fill="#1f9249">✓ Hold warfarin · vit K · monitor</text>
            <rect x="32" y="102" width="256" height="12" fill="rgba(196,30,58,0.08)"/><text x="38" y="111" fill="#7a6238">  Increase warfarin dose</text>
            <rect x="32" y="118" width="256" height="12" fill="rgba(196,30,58,0.08)"/><text x="38" y="127" fill="#7a6238">  Discontinue all meds</text>
        </g>
    </svg>`,
    fitness: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#1a0e06"/>
        <g font-family="JetBrains Mono" font-size="10" fill="#a86f3a">
            <text x="20" y="32" fill="#f4c430">WEEK 6 · push</text>
            <text x="20" y="50">bench press   3×5  @ 185 lb  ✓</text>
            <text x="20" y="66">ohp           3×8  @ 95  lb  ✓</text>
            <text x="20" y="82">incline db    3×10 @ 50  lb  ✓</text>
            <text x="20" y="98">tricep dip    3×12         ✓</text>
            <text x="20" y="125" fill="#1f9249" font-size="11">📈 +5lb bench (vs wk 5)</text>
        </g>
        <path d="M20,140 L60,135 L100,128 L140,122 L180,115 L220,108 L260,98 L300,90" fill="none" stroke="#f4c430" stroke-width="2"/>
    </svg>`,
    cfu: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0e0808"/>
        <g stroke="rgba(244,196,48,0.1)" stroke-width="1">
            <line x1="46" y1="18" x2="304" y2="18"/><line x1="46" y1="55" x2="304" y2="55"/>
            <line x1="46" y1="92" x2="304" y2="92"/><line x1="46" y1="129" x2="304" y2="129"/>
        </g>
        <line x1="46" y1="14" x2="46" y2="133" stroke="#f4c430" stroke-width="1.5"/>
        <line x1="46" y1="133" x2="304" y2="133" stroke="#f4c430" stroke-width="1.5"/>
        <rect x="60"  y="58"  width="28" height="75" fill="#f4c430" opacity="0.75"/>
        <rect x="104" y="36"  width="28" height="97" fill="#1f9249" opacity="0.8"/>
        <rect x="148" y="72"  width="28" height="61" fill="#f4c430" opacity="0.6"/>
        <rect x="192" y="44"  width="28" height="89" fill="#d4324b" opacity="0.7"/>
        <rect x="236" y="26"  width="28" height="107" fill="#1f9249" opacity="0.8"/>
        <rect x="268" y="52"  width="28" height="81" fill="#f4c430" opacity="0.65"/>
        <g stroke="white" stroke-width="1.5">
            <line x1="74" y1="48" x2="74" y2="68"/><line x1="69" y1="48" x2="79" y2="48"/><line x1="69" y1="68" x2="79" y2="68"/>
            <line x1="118" y1="26" x2="118" y2="46"/><line x1="113" y1="26" x2="123" y2="26"/><line x1="113" y1="46" x2="123" y2="46"/>
        </g>
        <text x="50" y="152" font-family="JetBrains Mono" font-size="8" fill="#7a8868">CFU/mL · log₁₀ · p&lt;0.05 ✓</text>
    </svg>`,
    cfucalc: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0a0f0b"/>
        <g font-family="JetBrains Mono" font-size="9">
            <text x="16" y="24" fill="#7a8868">SAMPLE</text>
            <text x="122" y="24" fill="#7a8868">COL</text>
            <text x="168" y="24" fill="#7a8868">DIL</text>
            <text x="228" y="24" fill="#7a8868">CFU/mL</text>
            <line x1="14" y1="30" x2="306" y2="30" stroke="#1f9249" stroke-opacity="0.45"/>
            <text x="16" y="48" fill="#c8cfc6">Untreated</text>
            <text x="122" y="48" fill="#e8e4d8">148</text>
            <text x="168" y="48" fill="#7a8868">10&#8315;&#8310;</text>
            <text x="228" y="48" fill="#f4c430">1.5e9</text>
            <text x="16" y="70" fill="#c8cfc6">+ EDTA</text>
            <text x="122" y="70" fill="#e8e4d8">96</text>
            <text x="168" y="70" fill="#7a8868">10&#8315;&#8310;</text>
            <text x="228" y="70" fill="#f4c430">9.6e8</text>
            <text x="16" y="92" fill="#c8cfc6">Phage T4</text>
            <text x="122" y="92" fill="#e8e4d8">42</text>
            <text x="168" y="92" fill="#7a8868">10&#8315;&#8308;</text>
            <text x="228" y="92" fill="#f4c430">4.2e6</text>
            <text x="16" y="114" fill="#c8cfc6">T4 + EDTA</text>
            <text x="122" y="114" fill="#e8e4d8">7</text>
            <text x="168" y="114" fill="#7a8868">10&#8315;&#179;</text>
            <text x="228" y="114" fill="#d4324b">&lt; 30</text>
            <text x="16" y="136" fill="#c8cfc6">Media ctrl</text>
            <text x="122" y="136" fill="#e8e4d8">0</text>
            <text x="168" y="136" fill="#7a8868">10&#8315;&#178;</text>
            <text x="228" y="136" fill="#7a8868">&lt; 1000</text>
            <line x1="14" y1="146" x2="306" y2="146" stroke="#1f9249" stroke-opacity="0.25"/>
            <text x="16" y="157" fill="#1f9249" font-size="8">&#10003; .xlsx ready</text>
        </g>
    </svg>`,
    genomicskitchen: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#080e18"/>
        <g font-family="JetBrains Mono" font-size="9">
            <rect x="14" y="18" width="72" height="34" fill="#102030" stroke="#1f9249" stroke-width="1" rx="2"/>
            <text x="20" y="30" fill="#1f9249">INPUT</text>
            <text x="20" y="44" fill="#6a9490">ATCGATCG…</text>
            <text x="96" y="38" fill="#f4c430" font-size="13">→</text>
            <rect x="114" y="18" width="72" height="34" fill="#1a1208" stroke="#f4c430" stroke-width="1" rx="2"/>
            <text x="120" y="30" fill="#f4c430">TRIM</text>
            <text x="120" y="44" fill="#a8903a">ATCGAT…</text>
            <text x="196" y="38" fill="#f4c430" font-size="13">→</text>
            <rect x="214" y="18" width="92" height="34" fill="#081408" stroke="#1f9249" stroke-width="1" rx="2"/>
            <text x="220" y="30" fill="#1f9249">CLEAN</text>
            <text x="220" y="44" fill="#a8c490">ATCGAT</text>
            <rect x="14"  y="72" width="58" height="20" fill="#182028" stroke="#1f9249" rx="3"/><text x="22" y="85" fill="#1f9249">FILTER</text>
            <rect x="80"  y="72" width="60" height="20" fill="#182028" stroke="#f4c430" rx="3"/><text x="88" y="85" fill="#f4c430">FORMAT</text>
            <rect x="148" y="72" width="60" height="20" fill="#182028" stroke="#d4324b" rx="3"/><text x="156" y="85" fill="#d4324b">DEDUPE</text>
            <rect x="216" y="72" width="88" height="20" fill="#182028" stroke="#1f9249" rx="3"/><text x="224" y="85" fill="#1f9249">ANNOTATE</text>
        </g>
        <text x="16" y="140" font-family="JetBrains Mono" font-size="8" fill="#7a8868">browser-based · no install · reproducible</text>
    </svg>`,
    seqsieve: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#08100e"/>
        <g font-family="JetBrains Mono" font-size="9">
            <text x="16" y="22" fill="#f4c430">&gt;seq_001</text>
            <text x="16" y="34" fill="#a8c490">ATCGATCGTAGCT</text>
            <text x="16" y="52" fill="#f4c430">&gt;seq_002</text>
            <text x="16" y="64" fill="#a8c490">GCTAGCTAGCTAGC</text>
            <text x="16" y="82" fill="#7a6238" text-decoration="line-through">&gt;seq_001_dup</text>
            <text x="16" y="94" fill="#7a6238" text-decoration="line-through">ATCGATCGTAGCT</text>
            <text x="16" y="112" fill="#7a6238" text-decoration="line-through">&gt;seq_003_dup</text>
            <text x="16" y="124" fill="#7a6238" text-decoration="line-through">GCTAGCTAGCTAGC</text>
            <path d="M156,54 L172,54 L172,98 L156,98 Z" fill="none" stroke="#f4c430" stroke-width="1.5" stroke-dasharray="3 2"/>
            <g stroke="#f4c430" stroke-width="1" opacity="0.6">
                <line x1="159" y1="64" x2="169" y2="64"/><line x1="159" y1="72" x2="169" y2="72"/>
                <line x1="159" y1="80" x2="169" y2="80"/><line x1="159" y1="88" x2="169" y2="88"/>
            </g>
            <text x="183" y="34" fill="#f4c430">&gt;seq_001</text>
            <text x="183" y="46" fill="#a8c490">ATCGATCGTAGCT</text>
            <text x="183" y="64" fill="#f4c430">&gt;seq_002</text>
            <text x="183" y="76" fill="#a8c490">GCTAGCTAGCTAGC</text>
            <text x="183" y="120" fill="#1f9249" font-size="10">✓ 4 → 2 unique</text>
        </g>
    </svg>`,
    readqraft: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#060810"/>
        <g font-family="JetBrains Mono" font-size="8.5">
            <text x="14" y="18" fill="#f4c430">@read_001</text>
            <text x="14" y="30" fill="#a8c490">ATCGATCGTAGCTAGCTTACGATCG</text>
            <text x="14" y="42" fill="#6a7868">+</text>
            <text x="14" y="54" fill="#d4324b">IIIIIHHHGGGFFEEDDCCBBAA@@</text>
        </g>
        <line x1="14"  y1="135" x2="305" y2="135" stroke="#f4c430" stroke-width="1"/>
        <line x1="14"  y1="66"  x2="14"  y2="135" stroke="#f4c430" stroke-width="1"/>
        <g fill="#1f9249">
            <rect x="18" y="82" width="10" height="53"/><rect x="31" y="78" width="10" height="57"/>
            <rect x="44" y="80" width="10" height="55"/><rect x="57" y="77" width="10" height="58"/>
            <rect x="70" y="83" width="10" height="52"/><rect x="83" y="86" width="10" height="49"/>
        </g>
        <g fill="#f4c430">
            <rect x="96"  y="93" width="10" height="42"/><rect x="109" y="97" width="10" height="38"/>
            <rect x="122" y="101" width="10" height="34"/><rect x="135" y="104" width="10" height="31"/>
        </g>
        <g fill="#d4324b">
            <rect x="148" y="110" width="10" height="25"/><rect x="161" y="114" width="10" height="21"/>
            <rect x="174" y="118" width="10" height="17"/><rect x="187" y="122" width="10" height="13"/>
        </g>
        <g font-family="JetBrains Mono" font-size="8.5">
            <text x="210" y="90"  fill="#7a8868">Phred Q</text>
            <text x="210" y="106" fill="#1f9249">≥Q30: ✓</text>
            <text x="210" y="122" fill="#d4324b">tail: trim</text>
        </g>
    </svg>`,
    gibson: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#0a1208"/>
        <g fill="none" stroke-width="9" stroke-linecap="round">
            <path d="M70,60 A45,45 0 0 1 160,55" stroke="#f4c430"/>
            <path d="M160,55 A45,45 0 0 1 200,118" stroke="#1f9249"/>
            <path d="M200,118 A45,45 0 0 1 90,118 Q70,95 70,62" stroke="#d4324b"/>
        </g>
        <g fill="#a8c490" font-family="JetBrains Mono" font-size="7">
            <circle cx="160" cy="55" r="3.5" fill="#f5edd8"/>
            <circle cx="200" cy="118" r="3.5" fill="#f5edd8"/>
            <circle cx="74" cy="90" r="3.5" fill="#f5edd8"/>
        </g>
        <g font-family="JetBrains Mono" font-size="8.5">
            <text x="232" y="36" fill="#7a8868">frag</text><text x="285" y="36" fill="#f4c430">µL</text>
            <text x="232" y="56" fill="#f4c430">F1</text><text x="278" y="56" fill="#a8c490">2.4</text>
            <text x="232" y="76" fill="#1f9249">F2</text><text x="278" y="76" fill="#a8c490">1.1</text>
            <text x="232" y="96" fill="#d4324b">F3</text><text x="278" y="96" fill="#a8c490">3.0</text>
            <text x="232" y="120" fill="#7a8868">H₂O</text><text x="278" y="120" fill="#a8c490">8.5</text>
        </g>
    </svg>`,
    mcat: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#080a18"/>
        <rect x="14" y="10" width="292" height="140" fill="#101628" stroke="#1f9249" stroke-width="1.5" rx="5"/>
        <text x="26" y="28" font-family="JetBrains Mono" font-size="8.5" fill="#f4c430">Q.12 / 59 · biochemistry · 04:32</text>
        <text x="26" y="44" font-family="Inter" font-size="9" fill="#d8dceb">A catalytic triad in serine proteases</text>
        <text x="26" y="56" font-family="Inter" font-size="9" fill="#d8dceb">includes His, Asp, and which residue?</text>
        <g font-family="JetBrains Mono" font-size="9">
            <rect x="26" y="65" width="264" height="14" fill="rgba(26,128,64,0.15)" stroke="#1f9249"/>
            <text x="32" y="75" fill="#1f9249">✓  Serine</text>
            <rect x="26" y="82" width="264" height="13" fill="rgba(196,30,58,0.08)"/>
            <text x="32" y="92" fill="#7a6238">   Threonine</text>
            <rect x="26" y="98" width="264" height="13" fill="rgba(196,30,58,0.08)"/>
            <text x="32" y="108" fill="#7a6238">   Tyrosine</text>
            <rect x="26" y="114" width="264" height="13" fill="rgba(196,30,58,0.08)"/>
            <text x="32" y="124" fill="#7a6238">   Cysteine</text>
        </g>
        <text x="26" y="143" font-family="JetBrains Mono" font-size="8" fill="#7a8868">MCAT · Chem/Phys · AI rationale ↗</text>
    </svg>`,
    pennywise: `<svg viewBox="0 0 320 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="320" height="160" fill="#080a12"/>
        <g font-family="JetBrains Mono">
            <text x="16" y="20" font-size="11" fill="#f4c430">PennyWise+</text>
            <text x="200" y="20" font-size="9" fill="#1f9249">May 2026</text>
            <text x="16" y="42" font-size="9" fill="#d8dceb">Rent        </text><text x="120" y="42" font-size="9" fill="#d4324b">-$1,200</text>
            <rect x="198" y="34" width="104" height="10" fill="#2a1015"/><rect x="198" y="34" width="80" height="10" fill="#d4324b" opacity="0.7"/>
            <text x="16" y="58" font-size="9" fill="#d8dceb">Groceries   </text><text x="120" y="58" font-size="9" fill="#d4324b">-$340</text>
            <rect x="198" y="50" width="104" height="10" fill="#2a1015"/><rect x="198" y="50" width="30" height="10" fill="#f4c430" opacity="0.7"/>
            <text x="16" y="74" font-size="9" fill="#d8dceb">Savings     </text><text x="120" y="74" font-size="9" fill="#1f9249">+$500</text>
            <rect x="198" y="66" width="104" height="10" fill="#0a1508"/><rect x="198" y="66" width="42" height="10" fill="#1f9249" opacity="0.7"/>
            <text x="16" y="90" font-size="9" fill="#d8dceb">Transport   </text><text x="120" y="90" font-size="9" fill="#d4324b">-$95</text>
            <rect x="198" y="82" width="104" height="10" fill="#2a1015"/><rect x="198" y="82" width="8" height="10" fill="#f4c430" opacity="0.7"/>
            <line x1="16" y1="106" x2="302" y2="106" stroke="rgba(244,196,48,0.2)" stroke-width="1"/>
            <text x="16" y="122" font-size="9" fill="#7a8868">Balance</text>
            <text x="100" y="122" font-size="12" fill="#1f9249">$2,847.50</text>
            <text x="16" y="148" font-size="8" fill="#7a8868">client-side · 0 uploads · no account</text>
        </g>
    </svg>`
};

/* ==============================================================
   RENDER — Publications
=============================================================== */

function renderPublications(filter = 'all') {
    const container = document.getElementById('pubList');
    const labelFor = s => ({
        'preprint':  'Preprint',
        'published': 'Published',
        'inprep':    'In preparation',
        'talk':      'Talk',
        'poster':    'Poster'
    })[s] || (s[0].toUpperCase() + s.slice(1));

    const renderEntry = pub => {
        const auth = pub.authors ? pub.authors.replace(/Awuah MB/, '<em>Awuah MB</em>') : '';
        const doi = pub.doi ? pub.doi.replace(/^https?:\/\/doi\.org\//, '') : '';
        const altmetric = pub.kind === 'paper' && doi
            ? `<div class="altmetric-wrap" title="Click for full attention details"><div class="altmetric-embed" data-badge-type="donut" data-badge-popover="right" data-doi="${doi}" data-hide-no-mentions="false"></div><span class="altmetric-label">attention</span></div>`
            : '';
        // Clear, obvious link buttons (replaces the tiny "DOI ↗" text)
        const readLabel = pub.status === 'preprint' ? 'Read preprint' : 'Read paper';
        const links = [];
        if (pub.doi)  links.push(`<a class="pub-link primary" href="${pub.doi}" target="_blank" rel="noopener">${readLabel} ↗</a>`);
        if (pub.code) links.push(`<a class="pub-link" href="${pub.code}" target="_blank" rel="noopener">Code ↗</a>`);
        if (pub.pdf)  links.push(`<a class="pub-link" href="${pub.pdf}" target="_blank" rel="noopener">PDF ↗</a>`);
        // Papers get the same Cite affordance the software already had — it was
        // odd that a tool could be cited in one click and the actual papers
        // had to be retyped by hand.
        const citeId = 'pubcite-' + (doi || String(pub.year)).replace(/[^A-Za-z0-9]+/g, '-').toLowerCase();
        if (pub.citation) {
            links.push(`<button class="pub-link pub-cite-btn" type="button"
                aria-expanded="false" aria-controls="${citeId}">Cite</button>`);
        }
        const linkRow = links.length ? `<div class="pub-links">${links.join('')}</div>` : '';

        // Sequence accessions are the deliverable of a genome announcement.
        const dataRow = (pub.data && pub.data.length)
            ? `<div class="pub-data"><span class="pub-data-label">Data</span>${pub.data.map(d =>
                `<a class="pub-acc" href="${d.url}" target="_blank" rel="noopener"
                    title="${esc(d.label)} accession">${esc(d.label)} <code>${esc(d.id)}</code></a>`
              ).join('')}</div>`
            : '';

        const citeBlock = pub.citation
            ? `<div class="pub-citation-block" id="${citeId}" hidden>
                 <div class="cite-tabs">
                   <button class="cite-tab active" type="button" data-tab="plain">Plain text</button>
                   <button class="cite-tab" type="button" data-tab="bibtex">BibTeX</button>
                 </div>
                 <div class="cite-panel" data-panel="plain">
                   <pre class="cite-text">${esc(pub.citation.plain)}</pre>
                   <button class="cite-copy" type="button" data-copy="${encodeURIComponent(pub.citation.plain)}">Copy</button>
                 </div>
                 <div class="cite-panel" data-panel="bibtex" hidden>
                   <pre class="cite-text">${esc(pub.citation.bibtex)}</pre>
                   <button class="cite-copy" type="button" data-copy="${encodeURIComponent(pub.citation.bibtex)}">Copy</button>
                 </div>
               </div>`
            : '';
        const titleHref = pub.doi || pub.code || pub.pdf || '';
        const titleHtml = titleHref
            ? `<a href="${titleHref}" target="_blank" rel="noopener">${pub.title}</a>`
            : pub.title;
        const thumb = pub.thumb
            ? `<img class="pub-thumb" src="${pub.thumb}" alt="${esc(pub.thumbAlt || pub.title)}" width="96" height="72" loading="lazy" decoding="async">`
            : pub.thumbSvg
                ? `<div class="pub-thumb pub-thumb-svg" aria-hidden="true">${pub.thumbSvg}</div>`
                : '';
        return `
        <div class="pub-entry ${pub.latest ? 'latest' : ''} ${pub.firstAuthor ? 'featured' : ''} ${pub.kind === 'paper' ? 'has-altmetric' : ''}">
            <div class="pub-year">${pub.year}</div>
            <div class="pub-body">
                ${thumb}
                <div class="pub-title">${titleHtml}</div>
                ${pub.authors ? `<div class="pub-authors">${auth}</div>` : ''}
                ${pub.contribution ? `<div class="pub-contribution"><span class="pub-contribution-kicker">My contribution</span> ${pub.contribution}</div>` : ''}
                <div class="pub-journal">${pub.journal}</div>
                ${pub.ids ? `<div class="pub-ids">${esc(pub.ids)}</div>` : ''}
                ${dataRow}
                ${pub.summary ? `<div class="pub-summary" style="color:var(--ink-2); font-size:0.9rem; margin-top:6px; line-height:1.55;">${pub.summary}</div>` : ''}
                <div class="pub-meta">
                    <span class="pub-status ${pub.status}">${labelFor(pub.status)}</span>
                    ${pub.firstAuthor ? '<span class="pub-status first-author">★ First author</span>' : ''}
                    ${pub.latest ? '<span class="pub-status preprint">★ Latest</span>' : ''}
                </div>
                ${linkRow}
                ${citeBlock}
            </div>
            ${altmetric}
        </div>`;
    };

    window.__renderPubEntry = renderEntry;

    const renderGroup = (label, items) => {
        if (items.length === 0) return '';
        return `<div class="pub-group">
            <div class="pub-group-header">
                <span class="pub-group-label">${label}</span>
                <span class="pub-group-line"></span>
            </div>
            ${items.map(renderEntry).join('')}
        </div>`;
    };

    /* Papers only. Talks and posters live in their own section, the way every
       comparable academic site separates them. */
    const papers = publications.filter(p => p.kind === 'paper');
    container.innerHTML = renderGroup('Papers & Preprints', papers);

    if (window._altmetric_embed_init) window._altmetric_embed_init();
}

/* Citation UI for papers. Delegated from document rather than bound per render:
   renderPublications() replaces innerHTML whenever a filter changes, which would
   throw away directly-bound listeners. */
(function wirePublicationCitations() {
    document.addEventListener('click', function (e) {
        const toggle = e.target.closest('.pub-cite-btn');
        if (toggle) {
            e.preventDefault();
            const block = document.getElementById(toggle.getAttribute('aria-controls'));
            if (!block) return;
            const open = block.hidden;
            block.hidden = !open;
            toggle.setAttribute('aria-expanded', String(open));
            toggle.textContent = open ? 'Hide citation' : 'Cite';
            return;
        }

        const tab = e.target.closest('.pub-citation-block .cite-tab');
        if (tab) {
            e.preventDefault();
            const block = tab.closest('.pub-citation-block');
            block.querySelectorAll('.cite-tab').forEach(t => {
                t.classList.toggle('active', t === tab);
            });
            block.querySelectorAll('.cite-panel').forEach(p => {
                p.hidden = p.dataset.panel !== tab.dataset.tab;
            });
            return;
        }

        const copy = e.target.closest('.pub-citation-block .cite-copy');
        if (copy) {
            e.preventDefault();
            const text = decodeURIComponent(copy.dataset.copy);
            const done = () => {
                const orig = copy.textContent;
                copy.textContent = 'Copied!';
                setTimeout(() => { copy.textContent = orig; }, 1800);
            };
            // clipboard API needs a secure context; fall back so the button is
            // never simply dead on http:// or an older browser.
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(done).catch(() => legacyCopy(text, done));
            } else {
                legacyCopy(text, done);
            }
        }
    });

    function legacyCopy(text, done) {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:-1000px;opacity:0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); done(); } catch (err) { /* nothing to offer */ }
        ta.remove();
    }
})();

/* ==============================================================
   RENDER — Talks & posters
=============================================================== */
function renderTalks() {
    const container = document.getElementById('talkList');
    if (!container) return;
    const items = publications.filter(p => p.kind === 'talk' || p.kind === 'poster');

    /* A ledger, not a card wall: ten near-identical cards gave conference
       posters the same visual weight as the papers above them. Repeat
       presentations merge into one entry — same work, several venues — with a
       per-instance year and TALK/POSTER label, which is how a CV lists them. */
    const norm = t => t.replace(/\s*\((Poster.*?|Blitz.*?)\)\s*$/i, '').trim();
    const groups = new Map();
    for (const p of items) {
        const key = norm(p.title);
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(p);
    }

    const talkN = items.filter(p => p.kind === 'talk').length;
    const posterN = items.filter(p => p.kind === 'poster').length;
    const count = document.getElementById('talkCounts');
    if (count) count.textContent = `${talkN} talks · ${posterN} posters`;

    container.innerHTML = [...groups.entries()].map(([title, list]) => {
        list.sort((a, b) => b.year - a.year);
        const rows = list.map(p => `
            <div class="ledger-venue">
                <span class="ledger-year">${p.year}</span>
                <span class="ledger-where">${p.journal}</span>
                <span class="ledger-kind ${p.kind}">${p.kind === 'talk' ? 'Talk' : 'Poster'}</span>
            </div>`).join('');
        return `
        <div class="ledger-entry">
            <h3 class="ledger-title">${title}</h3>
            ${rows}
        </div>`;
    }).join('');
}

/* ==============================================================
   RENDER — Tools
=============================================================== */
/* Sixteen equal cards buried the ones that carry the section's argument.
   Default = this explicit six; every other view is one click away.
   The list is ordered, not derived from `featured`: the old flagship filter
   showed four browser apps and hid the two heaviest pieces of engineering
   (a pooled AlphaFold 3 screen designer and a tested CLI), which inverted
   what a technical reader saw first. */
const FLAGSHIPS = ['Plaque Toolkit', 'PooledPPI', 'HMM Homologue Finder',
                   'FigureLab', 'Lysis Curve Plotter', 'HMM Discovery App'];
function renderTools(filter = 'flagship') {
    const container = document.getElementById('toolsGrid');
    const filtered = filter === 'flagship'
        ? FLAGSHIPS.map(f => tools.find(t => t.title === f)).filter(Boolean)
        : filter === 'all' ? tools : tools.filter(t => t.stack === filter);
    container.innerHTML = filtered.map(t => `
        <div class="proj-card ${t.app ? 'proj-card--link' : ''} ${t.featured ? 'featured' : ''}" data-stack="${t.stack}">
            ${t.app ? `<a class="proj-card-stretch" href="${t.app}" target="_blank" rel="noopener" aria-label="Open ${t.title}"></a>` : ''}
            <div class="proj-thumb">
                ${SVG_PREVIEWS[t.preview] || ''}
                <span class="proj-category-pill science">${t.stack.toUpperCase()}</span>
                <span class="proj-thumb-label">${t.label}</span>
            </div>
            <div class="proj-body">
                <h3>${t.featured ? '<span class="proj-featured-star" title="Featured">★</span> ' : ''}${t.title}${t.doi ? ' <span class="proj-doi-badge" title="Archived on Zenodo — citable with a persistent DOI">DOI</span>' : ''}</h3>
                <p>${t.blurb}${t.doi ? ' <span class="proj-citable-note">Archived on Zenodo — citable with a persistent DOI.</span>' : ''}</p>
                <div class="proj-tags">
                    ${t.tech.map(x => `<span class="research-tag">${x}</span>`).join('')}
                </div>
                <div class="proj-actions">
                    ${t.app && t.app !== t.repo ? `<a href="${t.app}"  class="proj-link" target="_blank" rel="noopener">Open ↗</a>` : ''}
                    ${t.repo ? `<a href="${t.repo}" class="proj-link ${t.app && t.app !== t.repo ? 'alt' : ''}" target="_blank" rel="noopener">Source ↗</a>` : ''}
                    ${t.blog && t.blog !== t.app ? `<a href="${t.blog}" class="proj-link alt" target="_blank" rel="noopener">Blog</a>` : ''}
                    ${t.doi ? `<a href="https://doi.org/${t.doi}" class="proj-link alt" target="_blank" rel="noopener">Zenodo ↗</a>` : ''}
                    ${t.doi ? `<button class="proj-link proj-cite-btn" data-tool="${t.title}" type="button">Cite</button>` : ''}
                </div>
                ${t.usedIn && t.usedIn.length ? `
                <div class="proj-usedin">
                    <span class="usedin-badge">Used in published research</span>
                    ${t.usedIn.map(u => `
                    <blockquote class="usedin-quote">&ldquo;${u.quote}&rdquo;</blockquote>
                    <cite class="usedin-cite">${u.citation}
                        <a href="${u.doi}" target="_blank" rel="noopener">doi&nbsp;↗</a>
                    </cite>`).join('')}
                </div>` : ''}
                ${t.citation ? `
                <div class="proj-citation-block" id="cite-${t.title.replace(/\s+/g,'-').toLowerCase()}" aria-hidden="true">
                    <div class="proj-citation-tabs">
                        <button class="cite-tab active" data-tab="plain">Plain text</button>
                        <button class="cite-tab" data-tab="bibtex">BibTeX</button>
                    </div>
                    <div class="cite-panel" data-panel="plain">
                        <pre class="cite-text">${t.citation.plain}</pre>
                        <button class="cite-copy" data-copy="${encodeURIComponent(t.citation.plain)}">Copy</button>
                    </div>
                    <div class="cite-panel" data-panel="bibtex" hidden>
                        <pre class="cite-text">${t.citation.bibtex}</pre>
                        <button class="cite-copy" data-copy="${encodeURIComponent(t.citation.bibtex)}">Copy</button>
                    </div>
                </div>` : ''}
            </div>
        </div>
    `).join('') + (filter === 'flagship'
        ? `<button class="blog-more tools-more" type="button" onclick="renderTools('all')">All ${tools.length} tools ↓</button>`
        : '');

    // Wire cite-block toggle + tabs + copy
    container.querySelectorAll('.proj-cite-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault(); e.stopPropagation();
            const id = 'cite-' + btn.dataset.tool.replace(/\s+/g,'-').toLowerCase();
            const block = document.getElementById(id);
            if (!block) return;
            const open = block.classList.toggle('open');
            block.setAttribute('aria-hidden', String(!open));
            btn.textContent = open ? 'Hide citation' : 'Cite';
        });
    });
    container.querySelectorAll('.cite-tab').forEach(tab => {
        tab.addEventListener('click', e => {
            e.preventDefault(); e.stopPropagation();
            const block = tab.closest('.proj-citation-block');
            block.querySelectorAll('.cite-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const which = tab.dataset.tab;
            block.querySelectorAll('.cite-panel').forEach(p => { p.hidden = p.dataset.panel !== which; });
        });
    });
    container.querySelectorAll('.cite-copy').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault(); e.stopPropagation();
            const text = decodeURIComponent(btn.dataset.copy);
            navigator.clipboard.writeText(text).then(() => {
                const orig = btn.textContent;
                btn.textContent = 'Copied!';
                setTimeout(() => { btn.textContent = orig; }, 1800);
            });
        });
    });
}

/* ==============================================================
   RENDER — Blog posts
=============================================================== */
function renderPosts(filter = 'all') {
    const container = document.getElementById('blogList');
    /* Side builds have their own page; on the homepage they diluted the
       science writing. The default band is three posts with the Serwaa story
       pinned first — it is the post a hiring reader should meet. */
    const science = posts.filter(p => !p.tags.includes('Side Builds'));
    let filtered, capped = false;
    if (filter === 'all') {
        const serwaa = science.find(p => (p.url || '').includes('serwaa-first-paper'));
        const rest = science.filter(p => p !== serwaa);
        filtered = (serwaa ? [serwaa] : []).concat(rest).slice(0, 3);
        capped = science.length > 3;
    } else if (filter === 'everything') {
        filtered = science;
    } else {
        filtered = science.filter(p => p.tags.includes(filter));
    }
    if (filtered.length === 0) {
        container.innerHTML = `<div class="blog-empty">No posts under that tag yet.</div>`;
        return;
    }
    /* Posts live on this site, so they open in the same tab. */
    container.innerHTML = filtered.map((p, i) => `
        <a class="blog-card ${i === 0 && filter === 'all' ? 'latest' : ''}" href="${p.url}">
            <div class="blog-date-col">
                <time class="blog-date" datetime="${p.iso}">${p.date}</time>
                ${i === 0 && filter === 'all' ? '<span class="blog-new-badge">Featured</span>' : ''}
            </div>
            <div class="blog-body">
                ${p.image ? `<img class="blog-thumb" src="${p.image}" alt="${esc(p.imageAlt || p.title)}" width="108" height="78" loading="lazy" decoding="async">` : ''}
                <div class="blog-tags">${p.tags.map(t => `<span class="blog-tag">${esc(t)}</span>`).join('')}</div>
                <h3 class="blog-title">${esc(p.title)}</h3>
                <p class="blog-blurb">${esc(p.blurb)}</p>
                <span class="blog-read">Read post →</span>
            </div>
        </a>
    `).join('') + (capped && filter === 'all'
        ? `<button class="blog-more" type="button" onclick="renderPosts('everything')">All ${science.length} posts ↓</button>`
        : '');
}

/* ==============================================================
   RENDER — Side builds
   Reads the same `builds` array that builds.html uses (assets/js/builds-data.js)
   so the two pages can't drift apart the way the hand-copied cards did.
=============================================================== */
function renderBuilds() {
    /* builds.html renders its own cards inline; this serves the homepage
       strip, which shows only the newest few. */
    const container = document.getElementById('buildsGrid') || document.getElementById('homeBuildsGrid');
    if (!container || typeof builds === 'undefined') return;
    const list = container.id === 'homeBuildsGrid' ? builds.slice(0, 3) : builds;
    container.innerHTML = list.map(b => `
        <div class="build-card">
            <div class="build-card-top"><h3>${esc(b.title)}</h3><span class="build-year">${esc(b.date)}</span></div>
            <p>${esc(b.blurb)}</p>
            <div class="build-tags">${b.tech.map(t => `<span class="build-tag">${esc(t)}</span>`).join('')}</div>
            <div class="build-actions">
                <a href="${b.app}" class="proj-link" target="_blank" rel="noopener">Open app ↗</a>
                ${b.repo ? `<a href="${b.repo}" class="proj-link alt" target="_blank" rel="noopener">Source ↗</a>` : ''}
                ${b.blog ? `<a href="${b.blog}" class="proj-link alt" target="_blank" rel="noopener">Read blog ↗</a>` : ''}
            </div>
        </div>
    `).join('');
}

/* ==============================================================
   INITIAL RENDER + FILTERS
=============================================================== */
/* (The talk/poster filter buttons are gone with the ledger redesign — six
   merged entries don't need filtering, and the counts line says the totals.) */

renderPublications();
renderTalks();
renderTools();
/* One source of truth for the tool count. (The glance-tile and About copies
   of this stat were removed with their sections in the redesign.) */
(() => {
    const el = document.getElementById('toolCount');
    if (el) el.textContent = tools.length + '+';
})();

/* Build tool filter buttons with counts */
(function() {
    const root = document.getElementById('toolFilters');
    const counts = tools.reduce((a, t) => { a[t.stack] = (a[t.stack] || 0) + 1; return a; }, {});
    /* The grid opens on the flagships, but the row marked "All Tools" as
       active — the control contradicted what was on screen. */
    const map = [
        ['flagship', 'Flagships', FLAGSHIPS.length],
        ['all',  'All Tools', tools.length],
        ['r',    'R / Shiny', counts.r || 0],
        ['js',   'Web / JS',  counts.js || 0],
        ['py',   'Python',    counts.py || 0]
    ];
    root.innerHTML = map.map(([k, label, n], i) => `
        <button class="filter-btn ${i === 0 ? 'active' : ''}" data-filter="${k}">
            ${label} <span class="filter-count">${n}</span>
        </button>
    `).join('');
})();

/* Build blog filter buttons (tags auto-populate from posts data).
   Side Builds are excluded — they have their own page, and on the homepage
   they diluted the science writing the band exists to show. */
(function() {
    const root = document.getElementById('blogFilters');
    if (!root) return;
    const science = posts.filter(p => !p.tags.includes('Side Builds'));
    const allTags = [...new Set(science.flatMap(p => p.tags))];
    const map = [
        ['all', 'Featured', 3],
        ...allTags.map(t => [t, t, science.filter(p => p.tags.includes(t)).length])
    ];
    root.innerHTML = map.map(([k, label, n], i) => `
        <button class="filter-btn ${i === 0 ? 'active' : ''}" data-filter="${k}">
            ${label} <span class="filter-count">${n}</span>
        </button>
    `).join('');
})();
renderPosts();
wireFilter('blogFilters', renderPosts);
renderBuilds();

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
wireFilter('toolFilters', renderTools);

/* ==============================================================
   FADE-IN ON SCROLL
=============================================================== */
const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            fadeObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.08 });
document.querySelectorAll('.fade-in').forEach(el => fadeObserver.observe(el));

/* ==============================================================
   CURSOR GLOW (desktop)
=============================================================== */
(function() {
    const glow = document.getElementById('cursorGlow');
    if (!glow || matchMedia('(hover: none)').matches) return;
    document.addEventListener('mousemove', (e) => {
        glow.style.setProperty('--cx', e.clientX + 'px');
        glow.style.setProperty('--cy', e.clientY + 'px');
    });
})();

/* ==============================================================
   MOBILE NAV
=============================================================== */
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');
function setNav(open) {
    navLinks.classList.toggle('open', open);
    navToggle.setAttribute('aria-expanded', String(open));
}
navToggle.addEventListener('click', () => setNav(!navLinks.classList.contains('open')));
document.querySelectorAll('.nav-links a').forEach(a => {
    a.addEventListener('click', () => setNav(false));
});
/* Escape and clicking away should close the mobile menu, not just tapping a link. */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && navLinks.classList.contains('open')) {
        setNav(false);
        navToggle.focus();
    }
});
document.addEventListener('click', (e) => {
    if (!navLinks.classList.contains('open')) return;
    if (!navLinks.contains(e.target) && !navToggle.contains(e.target)) setNav(false);
});

/* ==============================================================
   NAV: ACTIVE SECTION HIGHLIGHT
=============================================================== */
/* Derived from the nav itself rather than hand-listed. The literal had drifted
   both ways: five spied sections had no nav anchor, so the highlight went blank
   while the reader scrolled them, and nav links that were never spied kept a
   stale highlight. Reading the DOM means adding a section to the nav is enough. */
const navIds = Array.from(document.querySelectorAll('.nav-links a[href^="#"]'))
    .map(a => a.getAttribute('href').slice(1))
    .filter(id => id && document.getElementById(id));
const sectionEls = navIds.map(id => document.getElementById(id)).filter(Boolean);
const navAnchors = Array.from(document.querySelectorAll('.nav-links a')).filter(a => a.getAttribute('href') && a.getAttribute('href').startsWith('#'));

const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && entry.intersectionRatio > 0.4) {
            navAnchors.forEach(a => a.classList.remove('active'));
            const link = navAnchors.find(a => a.getAttribute('href') === '#' + entry.target.id);
            if (link) link.classList.add('active');
        }
    });
}, { threshold: [0.4, 0.6] });
sectionEls.forEach(el => sectionObserver.observe(el));

/* ==============================================================
   RESEARCH CARDS — MOUSE POSITION GLOW
=============================================================== */
if (!matchMedia('(hover: none)').matches) {
    document.querySelectorAll('.research-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const r = card.getBoundingClientRect();
            const x = ((e.clientX - r.left) / r.width) * 100;
            const y = ((e.clientY - r.top) / r.height) * 100;
            card.style.setProperty('--mx', x + '%');
            card.style.setProperty('--my', y + '%');
        });
    });

    /* 3D tilt on project + research cards */
    document.querySelectorAll('.proj-card, .research-card').forEach(card => {
        let raf;
        card.addEventListener('mousemove', (e) => {
            cancelAnimationFrame(raf);
            raf = requestAnimationFrame(() => {
                const r = card.getBoundingClientRect();
                const x = (e.clientX - r.left) / r.width  - 0.5;
                const y = (e.clientY - r.top)  / r.height - 0.5;
                card.style.transform = `translateY(-4px) perspective(900px) rotateX(${-y * 4}deg) rotateY(${x * 4}deg)`;
            });
        });
        card.addEventListener('mouseleave', () => {
            cancelAnimationFrame(raf);
            card.style.transform = '';
        });
    });

    /* Button radial glow follow */
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const r = btn.getBoundingClientRect();
            btn.style.setProperty('--bx', ((e.clientX - r.left)) + 'px');
            btn.style.setProperty('--by', ((e.clientY - r.top)) + 'px');
        });
    });
}
