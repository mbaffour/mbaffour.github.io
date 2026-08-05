/* Shared source of truth for the non-research side builds.
   Used by builds.html and by the #builds section on index.html, so the two
   can no longer drift apart. */
const builds = [
    {
        title: "QR Forge", date: "2026",
        blurb: "Free open-source QR generator embedding Ghanaian Adinkra symbols and Kente patterns directly into corner squares. 10 content types, print-ready, fully client-side.",
        tech: ["JavaScript", "PWA", "Cultural"],
        app: "https://mbaffour.github.io/qr-forge/", blog: "https://mbaffour.github.io/qr-forge/blog.html"
    },
    {
        title: "NCLEX Pro Simulator", date: "2026",
        blurb: "Watching someone grind through nursing school made me want to help. Adaptive practice questions plus AI clinical rationales, free, in the browser.",
        tech: ["JavaScript", "Adaptive", "AI"],
        app: "https://mbaffour.github.io/nclex-simulator/", blog: "https://mbaffour.github.io/nclex-simulator/blog_public.html"
    },
    {
        title: "MCAT Prep", date: "2026",
        blurb: "Full-length MCAT simulator with section breakdowns, time tracking, and AI-generated explanations. Free, browser-based, no account needed.",
        tech: ["JavaScript", "Adaptive", "AI"],
        app: "https://mbaffour.github.io/mcat-prep/", blog: "https://mbaffour.github.io/mcat-prep/blog.html"
    },
    {
        title: "Fitness Forge", date: "2025",
        blurb: "Offline-first fitness PWA: AI-generated 12–16 week programs, 60+ exercise database, local storage. No account, no server, no tracking.",
        tech: ["PWA", "Offline-First", "Fitness"],
        app: "https://mbaffour.github.io/fitness-forge/", blog: "https://mbaffour.github.io/fitness-forge/blog.html"
    },
    {
        title: "PennyWise+", date: "2026",
        blurb: "Private browser-based finance tracker: log income, categorize spending, visualize trends. Runs fully client-side. No account, no server, no tracking.",
        tech: ["JavaScript", "Finance", "Offline"],
        app: "https://mbaffour.github.io/pennywise-plus/", blog: "https://mbaffour.github.io/pennywise-plus/blog.html"
    },
    {
        title: "datamask", date: "2026",
        blurb: "Privacy-first local anonymizer that masks, shuffles, or replaces sensitive columns in CSV/Excel. Your data never leaves the browser.",
        tech: ["JavaScript", "Privacy", "CSV"],
        app: "https://mbaffour.github.io/datamask/", blog: "https://mbaffour.github.io/datamask/blog.html"
    },
    {
        title: "batchcrop", date: "2025",
        blurb: "Fast offline-first batch image cropper with 5 crop shapes and live preview. Zero uploads, zero accounts.",
        tech: ["JavaScript", "Image", "Offline"],
        app: "https://mbaffour.github.io/batchcrop/", blog: "https://mbaffour.github.io/batchcrop/blog.html"
    },
    {
        title: "LifeXP", date: "2026",
        blurb: "A gamified life tracker — habits, time tracking, planning, and analytics with XP, levels, and achievements. Local-first PWA in React + TypeScript; all your data stays on your device.",
        tech: ["TypeScript", "React", "PWA"],
        app: "https://mbaffour.github.io/lifexp/", blog: "https://mbaffour.github.io/blog/lifexp.html"
    },
    {
        title: "Number Tug", date: "2026",
        blurb: "A same-device arithmetic tug-of-war — solo, two-player, or versus the computer, with timed rounds, sound, and haptics. A tiny, polished TypeScript game for quick mental-math practice.",
        tech: ["TypeScript", "React", "Game"],
        app: "https://mbaffour.github.io/number-tug/", blog: "https://mbaffour.github.io/blog/number-tug.html"
    }
];
