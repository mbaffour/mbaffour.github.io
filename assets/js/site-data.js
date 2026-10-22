/* site-data.js — publications and research tools, shared by the homepage
   (main.js renders them) and the site-wide search (search.js indexes them).
   Classic script: the two arrays are globals. */
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
        title: "Protein Structure Viewer",
        repo: "https://github.com/mbaffour/protein-structure-viewer",
        featured: true,
        blurb: "Single-file browser viewer for AlphaFold and experimental structures — compares models while showing its chain pairing, puts pLDDT, PAE and interface confidence next to the structure, and exports figures or a self-contained interactive report. Nothing is uploaded.",
        tech: ["JavaScript", "AlphaFold", "3Dmol.js"],
        stack: "js",
        blog: "blog/protein-structure-viewer.html",
        app:  "https://mbaffour.github.io/structure-viewer/",
        label: "Structure Viewer",
        preview: "structure",
        doi: "10.5281/zenodo.22741487",
        citation: {
            plain: "Awuah, M. B. (2026). Protein Structure Viewer: compare, annotate and publish predicted and experimental protein structures in the browser (Version 2.22.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22741488",
            bibtex: "@software{awuah_protein_structure_viewer_2026,\n  author    = {Awuah, Michael Baffour},\n  title     = {{Protein Structure Viewer}: compare, annotate and publish predicted and experimental protein structures in the browser},\n  year      = {2026},\n  version   = {2.22.0},\n  publisher = {Zenodo},\n  doi       = {10.5281/zenodo.22741488},\n  url       = {https://doi.org/10.5281/zenodo.22741488}\n}"
        }
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
        blurb: "R Shiny app for publication-ready CFU figures — absolute counts or survival paired within each culture, log10 statistics with intervals and effect sizes, a data area that stays fixed however the figure is labelled, and one archive holding every export plus the script that rebuilds it.",
        tech: ["R Shiny", "CFU", "Statistics"],
        stack: "r",
        blog: "blog/cfu-plot-studio.html",
        app:  "https://mbaffour.github.io/cfu-plot-studio/",
        label: "CFU Plotter",
        preview: "cfu"
    },
    {
        title: "PFU Calculator",
        repo: "https://github.com/mbaffour/pfu-calculator",
        blurb: "Plaque counts to PFU/mL in one browser page — full plates or spot assays, replicates, detection limits, and a real Excel workbook on the way out. The phage twin of the CFU Calculator.",
        tech: ["JavaScript", "Phage", "Offline"],
        stack: "js",
        blog: "blog/pfu-calculator.html",
        app:  "https://mbaffour.github.io/pfu-calculator/",
        label: "Phage Titer Calc",
        preview: "pfucalc"
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
