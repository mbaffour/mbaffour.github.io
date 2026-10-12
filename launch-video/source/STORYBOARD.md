---
format: 1080x1920
duration: 30s
message: "I study how phage N4 decides when to kill its host"
arc: Logo → Headline → Feature 1 → Feature 2 → Feature 3 → CTA
audience: PIs, hiring committees and phage researchers scrolling X / Instagram
mode: autonomous
music: none
---

## Video direction

- **Palette (frame.md, dark brand):** ground = cream role `#121009` charcoal; voice = ink `#F5EDD8`;
  secondary text ink-2 `#D8C98C`, labels ink-3 `#AB9059`; cards = tile `#221C0E`; the one voltage
  = coral role, the site gold `#F4C430`. Kente green `#1F9249` / red `#D4324B` only inside the
  Kente stripe rule or inside captured screenshots. Frame 1 is the single exception: a full-bleed
  gold field ("the brand color") with the mark in charcoal.
- **Type:** display = Fraunces 400, sentence case, negative tracking; the gold italic phrase is the
  site's own headline treatment ("when to kill its host"). Body/lead = Inter. Kickers = JetBrains
  Mono uppercase, prefixed by the gold phage glyph (never ✱).
- **Motion grammar:** snappy. Entrances on `power3.out` / `expo.out`, short (≈0.35–0.6s), tight
  staggers. No bounce except one spring-pop on the CTA URL pill. Every frame reveals in cued steps
  across its duration (a kicker, then the title, then the screenshot, then the push to the detail);
  never the whole frame at t=0. Holds are still; at most a slow ≤3% drift on a screenshot.
- **Screens:** captured UI always sits on a tile card with a 1px gold@26% hairline and 24px radius,
  the site's own card look. Never rebuild the UI; screenshots are the source of truth. Push-ins are
  scale on the screenshot inside a clipped card (camera move), landing on a named region.
- **Rhythm:** Frames 1–2 fast (logo sting, word-by-word). Frames 3–5 one reveal per ~1.2s. Frame 6
  is the breather: one build, then a still hold for the last ≈2.5s so the URL can be read.
- **Layout:** 1080x1920. Content lives in the top 83% (y < 1590); side gutters 72px.
- **Negative list:** no stock footage, no bokeh, no purple/blue gradients, no cursor, no browser
  chrome, no nav bars; no slideshow (front-load then freeze) and no screensaver (everything drifting
  independently).

## Frame 1 — Logo reveal

- scene: The gold phage mark draws itself onto a full-bleed gold field, fills in charcoal, and the name locks up beneath it
- duration: 3s
- poster: 2.4s
- transition_in: cut
- status: animated
- src: compositions/frames/01-logo.html
- type: product_intro
- asset_candidates: assets/logo-favicon.svg — the brand mark (gold hexagon-head phage), drawn here in charcoal on gold
- blueprint: logo-assemble-lockup (Adapt)
- focal: assets/logo-favicon.svg
- roles: logo-favicon = cutout

Adapt: keep the "mark comes to exist" signature (outline draws on, then fills); a single mark not parts; the lockup is the name + a Kente stripe.
Scene 1 (0.0–1.1s): full-bleed gold `#F4C430` field. The hexagon head's outline draws on in charcoal stroke, then the tail and baseplate draw down, dead-centre, mark ≈ 34% of frame width, upper-middle (centre ≈ y 820).
Scene 2 (1.1–1.7s): the hexagon fills charcoal with a quick scale punch (1.0→1.06→1.0); a thin Kente stripe wipes on left→right under the mark.
Scene 3 (1.7–3.0s): "Michael Baffour Awuah" rises in under the stripe in Fraunces, charcoal, centred; then a mono kicker "PHAGE BIOLOGIST · TEXAS A&M" fades up beneath. Hold still.

## Frame 2 — Headline, word by word

- scene: The site's headline builds one word at a time on charcoal; "when to kill its host" lands in gold italic
- duration: 5s
- poster: 4.6s
- transition_in: push-slide UP 0.5s
- status: animated
- src: compositions/frames/02-headline.html
- type: hook
- asset_candidates: assets/logo-favicon.svg — small gold mark as the kicker glyph
- blueprint: kinetic-type-beats (Adapt)
- focal: headline text
- roles: logo-favicon = supporting

Adapt: keep the "statement builds across beats" signature; one stacked statement on one screen, each word its own beat.
Scene 1 (0.0–0.4s): charcoal ground; a small gold phage glyph + mono kicker "WHAT I STUDY" fades in top-left of the text block (y ≈ 560).
Scene 2 (0.4–3.9s): headline "I study how phage N4 decides when to kill its host." builds word by word, ≈0.32s apart, each word rising 40px + fading in with a slight blur clear. Left-aligned block, Fraunces display ≈ 112px, line-height 1.02, stacked over 5–6 lines, x = 72. "when to kill its host." are gold italic.
Scene 3 (3.9–5.0s): a thin gold rule draws under the last line; hold still.

## Frame 3 — Feature 1: the lysis model

- scene: The real "Fig 1 · N4 lysis model" figure steps through rapid lysis, ending as the cell bursts and releases its phages
- duration: 5s
- poster: 4.4s
- transition_in: blur-crossfade 0.5s
- status: animated
- src: compositions/frames/03-feature-lysis.html
- type: key_feature
- asset_candidates: assets/f1-0-anchored.png — figure, gp61 tethered, progeny inside; assets/f1-1-pinholes.png — figure, gp63 pinholes open; assets/f1-2-released.png — figure, gp61 released and cutting the wall; assets/f1-burst-00.png — burst flipbook frame 1 of 11 (f1-burst-00…10.png, seeked from the live animation)
- blueprint: device-surface-showcase (Adapt)
- focal: assets/f1-burst-10.png
- roles: f1-0-anchored = supporting · f1-1-pinholes = supporting · f1-2-released = supporting · f1-burst-00…10 = cutout (flipbook)

Adapt: keep the cursorless stepwise-flow signature (the screen cycles through a real flow); the "device" is the site's own figure card, now the full model's rapid pathway.
Scene 1 (0.0–0.7s): kicker "01 · INTERACTIVE FIGURE" then title "Watch N4 open the cell." top third.
Scene 2 (0.7–1.2s): the figure card rises in below (width 1000, y ≈ 620) on state 1, step 1 lights.
Scene 3 (1.2–3.0s): in place, state 1 → 2 → 3 by quick crossfades ≈0.6s apart, then the burst plays as an 11-frame flipbook of the live animation (≈1s), a four-step list under the card lighting in sync: "gp61 tethered · inactive" → "gp63 pinholes open" → "gp61 released · cutting the wall" → "Cell bursts · phages released".
Scene 4 (3.0–5.0s): push in on the top of the figure where the released phages land outside the torn envelope; hold.

## Frame 4 — Feature 2: the lysis-curve playground

- scene: The real Lysis Curve Playground; the camera travels from the controls to the red N4 curve as it holds, then crashes
- duration: 5s
- poster: 4.4s
- transition_in: push-slide LEFT 0.5s
- status: animated
- src: compositions/frames/04-feature-playground.html
- type: key_feature
- asset_candidates: assets/f2-playground.png — Lysis Curve Playground mid-run, red N4 curve, stage stepper on Inhibition
- blueprint: camera-journey (Adapt)
- focal: assets/f2-playground.png
- roles: f2-playground = cutout

Adapt: keep the multi-leg camera journey (B: cursorless) across one surface; one screenshot, three legs, no cursor.
Scene 1 (0.0–0.7s): kicker "02 · PLAYGROUND" then title "Run the infection yourself." (Fraunces ≈ 88px), top third.
Scene 2 (0.7–1.5s): screenshot card (width 936, y ≈ 680, card height ≈ 820, clipped) enters showing the whole widget scaled to fit.
Scene 3 (1.5–3.3s): camera leg 1: push to the plot (scale ≈1.0→1.7), centring the red N4 curve as it holds up then crashes; a gold mono callout "N4 holds lysis for hours" fades in over the card's lower edge.
Scene 4 (3.3–5.0s): camera leg 2: glide down to the "5 · Lysis inhibition (N4)" stage text card; hold.

## Frame 5 — Feature 3: open tools, used in published research

- scene: Three real tool cards cascade in; the FigureLab card comes forward and the camera lands on its "Used in published research" citation
- duration: 5s
- poster: 4.4s
- transition_in: push-slide LEFT 0.5s
- status: animated
- src: compositions/frames/05-feature-tools.html
- type: key_feature
- asset_candidates: assets/f3a-card-figurelab.png — FigureLab card with the green published-research citation; assets/f3b-card-structure-viewer.png — Protein Structure Viewer card; assets/f3c-card-lysis-plotter.png — Lysis Curve Plotter card
- blueprint: grid-card-assemble (Adapt)
- focal: assets/f3a-card-figurelab.png
- roles: f3a-card-figurelab = cutout · f3b-card-structure-viewer = supporting · f3c-card-lysis-plotter = supporting

Adapt: keep the staggered self-assembling cascade; three cards fanned in depth instead of a grid, then one comes forward.
Scene 1 (0.0–0.7s): kicker "03 · OPEN SOURCE" then title "Open tools, used in published research." (Fraunces ≈ 80px, 3 lines), top third.
Scene 2 (0.7–2.0s): the three cards cascade in from below with a tight stagger, fanned: Structure Viewer back-left (rotate −6°, dimmed), Lysis Plotter back-right (rotate +6°, dimmed), FigureLab centre-front, below the title (y ≈ 760).
Scene 3 (2.0–3.4s): the side cards slide out to the edges and dim further; FigureLab scales up to front-and-centre.
Scene 4 (3.4–5.0s): push in on the FigureLab card's green "Used in published research" quote box (lower third of the card); hold.

## Frame 6 — Call to action

- scene: Logo mark and a two-line ask, then the URL springs up in a gold pill and holds
- duration: 7s
- poster: 6.0s
- transition_in: crossfade 0.5s
- status: animated
- src: compositions/frames/06-cta.html
- type: cta
- asset_candidates: assets/logo-favicon.svg — the brand mark, gold on charcoal
- blueprint: titlecard-reveal (Adapt)
- focal: URL pill
- roles: logo-favicon = supporting

Adapt: keep "one clean reveal then a still hold"; a short chain of three reveals because the CTA has three parts.
Scene 1 (0.0–1.0s): charcoal ground; the gold phage mark (≈ 200px) scales in at upper-middle (y ≈ 560) and a Kente stripe wipes on under it.
Scene 2 (1.0–2.6s): "Defending in 2027." then "Open to postdoc roles." rise in, line by line, Fraunces ≈ 96px, centred; the second line in gold italic.
Scene 3 (2.6–3.6s): the URL "mbaffour.github.io" springs up in a gold pill (charcoal JetBrains Mono ≈ 52px), centred at y ≈ 1220; mono sub-line "Michael Baffour Awuah · Texas A&M" fades in beneath.
Scene 4 (3.6–7.0s): still hold; the only life is a single slow sheen across the pill at ≈5s.
