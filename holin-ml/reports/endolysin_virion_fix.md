# Endolysin: the tail-lysozyme error, traced and fixed

**The error.** In the blind scan of 152 new genomes (`blind/blind_scan.md`), the endolysin model's main confident
mistake was calling virion lytic enzymes -- T4-type "baseplate hub subunit and tail lysozyme" (gp5) and T7-type
internal virion proteins -- as the endolysin (12 of 19 conflicting calls). They cut peptidoglycan at infection, not
at lysis.

**The cause was in the training labels.** Seven of the eight clearest cases were 89-100% identical to proteins in the
endolysin POSITIVES: Pfam family members (mostly the CHAP domain, PF05257, and PF00959) whose own database
descriptions read "baseplate hub subunit and tail lysozyme", "pre-baseplate central spike protein Gp5", "minor tail
protein". 51 of the 1,111 positives (4.6%) were virion proteins. The model had been taught they are endolysins.

**Fix.** Those 51 moved from the positives to the negatives (`endolysin_positives_v2_novirion.json`,
`endolysin_virion_negatives.json`), same recipe otherwise. Decision rule set before the runs: adopt if unseen-family
ranked-first or top 5 improves on CPT without a significant loss, and known-family is not wholly worse.

| | old model | new model | change (95% CI) |
|---|---|---|---|
| CPT, 119 genomes, unseen family, ranked 1st | 0.664 | **0.720** | **+0.056 [+0.016, +0.103]** |
| CPT, unseen family, top 5 | 0.888 | 0.896 | +0.008 |
| CPT, known family, ranked 1st / top 5 | 0.848 / 0.960 | 0.856 / **0.984** | +0.008 / +0.024 |
| experimental set, ranked 1st, unseen / known | 12/22 / 15/22 | 12/22 / **18/22** | |
| confident-call precision at 0.9995, unseen / known (CPT) | 0.811 / 0.887 | **0.833 / 0.900** | same recall |

**Adopted** as `models/endolysin_model.pkl` (old model kept as `endolysin_model_v1_evidence_retired.pkl`).

**Proximity.** Proposed as a fix (use the neighbouring holin/spanin to pick the lysis endolysin over a virion one).
The predictor already does this (score = logit P + 6 x strongest holin/spanin P within 3 genes), but a saturated
P = 1.0000 on a virion protein outweighs it. Capping the logit so proximity can win was tested on CPT with
leave-one-genome-out scores: every cap lowered ranked-first (unseen family 0.815 uncapped -> 0.798 at cap 9 -> 0.706
at cap 3), so it was not adopted. With the labels fixed the virion proteins no longer saturate, and proximity as it
stands does its job: with context, the new model ranks the curated endolysin first in 81.5% (unseen family) and
93.3% (known) of CPT genomes.

## Confirmed on a second, fresh blind set

123 more genomes published from June 2026, none in the first blind set or anywhere else in the project, scanned from
DNA alone with each model and frozen (commit 45a360e) before scoring against their annotations (`reports/blind2/`):

| blind set 2, 114 genomes with an annotated endolysin | old model | new model | change (95% CI) |
|---|---|---|---|
| the call is the annotated endolysin | 0.860 | **0.921** | **+0.061 [+0.018, +0.114]** (8 fixed, 1 broken) |
| annotated endolysin in top 5 | 0.991 | 0.982 | |
| confident calls on virion proteins | 8 | 5 | |

What remains: T7-type internal virion proteins (2) and short "baseplate hub" proteins (2-3). From the first blind
scan, short (~165 aa) lysozymes beside the holin, annotated after gp5's lysozyme domain, look like real endolysins
misnamed by the annotation pipeline rather than model errors.
