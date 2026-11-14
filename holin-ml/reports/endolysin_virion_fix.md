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

## The remaining cases (diagnosed after the fix; both blind sets had been opened by then)

With the new model, blind set 1 rescored: the endolysin call is the annotated one in 0.900 of genomes (0.838 with the
old model); the long T7-type internal virion proteins and the 541-aa gp5 spikes no longer appear. Each remaining
confident call on a gene annotated with another function was checked against its genomic neighbourhood:

- **Annotation errors, model right** -- PZ402314.1: 166 aa, 70% identical over its full length to T4 gene e (the T4
  endolysin), annotated "baseplate hub subunit and tail lysozyme", no other endolysin annotated. PZ789121/2.1: the
  called lysozyme sits between the spanin and the holin; the gene annotated "endolysin" is 96 aa, 8 genes away,
  P = 0.0000. PZ585203/30.1 (174 aa) sit beside the holin/spanin in genomes annotated with no endolysin at all.
- **Real errors, pattern 1: proximity ignores distance** -- PZ476258.1 (a 607-aa cell-wall hydrolase three genes
  from the holin beats the amidase immediately after it; both P = 0.9994) and PZ897549.1 (a tail hydrolase three
  genes away collects the same holin bonus as the real endolysin next to it).
- **Real errors, pattern 2: a weakly modelled endolysin family** -- PZ445420/22/25.1 (related phages): the call is a
  140-aa virion protein inside the tail module; the true endolysins sit beside the holin and spanin but score only
  P = 0.12-0.16.

**Distance-weighted proximity, tested, not adopted.** A neighbour d genes away counts decay^(d-1) (predictor option
`--context-decay`, default 1.0 = unchanged). On CPT (leave-one-genome-out, beta 6, W 3) decay 0.5 left unseen-family
ranked-first unchanged (0.815) and moved known-family 0.933 -> 0.941 (one genome); stronger bonuses lowered
unseen-family. Rescanning both blind sets with decay 0.5: endolysin fixed 3 genomes and broke 3 (net zero), holin +1,
spanin unchanged. No net gain, so the default stays.

**Where that leaves it.** On blind set 2 the new model makes 5 confident endolysin calls on genes annotated as
something else; 3 look like annotation errors (above) and 2 are real (the PZ445 tail-module family): about 2 real
virion mistakes per 114 genomes. Fixing that family needs better training data for its real endolysins, not a
calling rule; one family in three related genomes is too narrow to train against without overfitting.
