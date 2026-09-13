/* Single source of truth for the blog. Used by index.html (the Blog & Notes band and
   the command palette), blog/index.html (the full listing), every post page
   (assets/js/post.js reads it for the byline and previous/next links) and
   scripts/build-site.mjs, which writes feed.xml and sitemap.xml from it.

   Adding a post: write blog/<slug>.html, add an entry here (newest first), run
   `node scripts/build-site.mjs`, commit. Fields: title, date (as shown), iso
   (YYYY-MM-DD), optional updated (YYYY-MM-DD, shown on the post and used as the
   sitemap lastmod), tags, blurb, url (relative to the site root), optional image
   and imageAlt. */
const posts = [
    {
        title: "Protein Structure Viewer — what the confidence numbers actually say",
        date: "September 11, 2026",
        iso: "2026-09-11",
        updated: "2026-09-13",
        tags: ["Research Software", "Structure Prediction"],
        blurb: "AlphaFold hands you a folder of predictions and a pile of JSON, and most viewers show you the structure while leaving the confidence data in a file you never open. A browser viewer that puts pLDDT, PAE and interface confidence next to the model, compares predictions while showing its pairing, and exports a self-contained interactive report. Nothing is uploaded.",
        url: "blog/protein-structure-viewer.html"
    },
    {
        title: "PFU Calculator — the same arithmetic, for plaques",
        date: "August 24, 2026",
        iso: "2026-08-24",
        tags: ["Research Software", "Phage Biology"],
        blurb: "A single-file browser calculator for phage titers: plaque counts to PFU/mL, full plates or spot assays, with replicates, detection limits and a real Excel export.",
        url: "blog/pfu-calculator.html"
    },
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
        blurb: "An R/Shiny app turning replicate-level CFU data into publication-ready figures: paired survival as well as absolute counts, log10 statistics with intervals and effect sizes, a data area that stays fixed however the figure is labelled, and one archive holding every export plus the script that rebuilds it.",
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
