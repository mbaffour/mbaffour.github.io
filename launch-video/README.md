# Launch video

A 30-second vertical launch video for the site, built with
[HyperFrames](https://hyperframes.heygen.com) from real screenshots of the live site.

| | |
|---|---|
| File | `mbaffour-launch-1080x1920.mp4` |
| Format | 1080×1920 (9:16), 30 fps, H.264, 30.0 s, silent |
| For | X and Instagram Reels |

## Scenes

| Time | Frame | On screen |
|---|---|---|
| 0–3s | `01-logo` | The favicon phage mark draws itself on gold; name and Kente stripe lock up |
| 3–8s | `02-headline` | "I study how phage N4 decides *when to kill its host.*", one word at a time |
| 8–13s | `03-feature-lysis` | The homepage lysis-model figure steps through rapid lysis; the cell bursts and its phages stream out (11 frames seeked from the live animation), then a push-in on them |
| 13–18s | `04-feature-playground` | Camera journey across the Lysis Curve Playground to the red N4 curve |
| 18–23s | `05-feature-tools` | Three tool cards cascade in; lands on FigureLab's published-research citation |
| 23–30s | `06-cta` | "Defending in 2027. Open to postdoc roles." and the site URL |

`stills/` holds the three frames approved before rendering and a contact sheet.

## Editing and re-rendering

`source/` is the HyperFrames project: `BRIEF.md` (intent), `STORYBOARD.md` (the shot plan),
`frame.md` (design tokens, the site's dark palette and fonts), `compositions/frames/*.html`
(one file per scene) and `assets/` (the screenshots, logo and fonts). Asset paths resolve from
`source/`, not from each frame file, which is why `scripts/check-links.mjs` skips this folder.

```bash
cd launch-video/source
npx hyperframes@0.8.149 lint && npx hyperframes@0.8.149 check
npx hyperframes@0.8.149 render --quality high --output renders/video.mp4
```

The screenshots in `source/assets/` were taken from mbaffour.github.io in October 2026. If the
site changes, re-capture them before re-rendering, or the video will show the old pages.
