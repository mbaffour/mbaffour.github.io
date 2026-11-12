# The integrated caller: one called gene per class, method chosen per class by honest validation

**Goal (from the user):** models that detect holins, endolysins and spanins and call them out.

The caller names one gene per class per genome, marked **confident** or **candidate**. Three ways of choosing that gene
were compared, each fed by the three first-stage models' leave-one-genome-out scores, on the 130 CPT-curated genomes:

- **model only:** the class's own probability;
- **context rule:** logit P plus beta times the strongest other-class score within W genes (`scripts/46`);
- **learned caller:** a second-stage gradient-boosted model per class over all three scores, genome rank, neighbour
  scores at 1/2/3/5 genes, distance to each class's top candidate, and protein shape: length, TM segments, lipobox
  (`scripts/48`).

## The validation had to be done twice

Split by genome, the learned caller looked transformative: holins from unseen families ranked first rose from 62%
(context rule) to 82%. That was a leak. The CPT set has clusters of related phages (three lambda variants, four
near-identical *Burkholderia* phages, the T4-like *Klebsiella* group). With a sibling in the training folds, the learned
caller recognised the family from shape alone ("a 218-aa one-helix protein is the holin") -- exactly the knowledge the
novel-family test is meant to deny.

Redone with **family-grouped folds** (genomes whose curated genes of the class are >= 30% identical never split):

| class | measure | context rule | learned caller | difference (95% CI) |
|---|---|---|---|---|
| holin | ranked 1st, novel | 0.615 | 0.564 | -0.051 [-0.154, +0.038] |
| holin | top 5, novel | 0.859 | 0.782 | **-0.077 [-0.154, -0.013]** |
| endolysin | ranked 1st, novel | 0.752 | 0.672 | **-0.080 [-0.138, -0.024]** |
| spanin | best per genome 1st, novel | 0.733 | 0.800 | +0.067 [0.000, +0.133] |
| spanin | best per genome 1st, known | 0.833 | 0.911 | **+0.078 [+0.022, +0.133]** |

Without the shape features the learned caller was no better for holins or endolysins and lost its spanin advantage.
That fits the biology: a lipobox and an N-terminal anchor define a spanin across spanin families, while holin and
endolysin length and topology vary family by family, so a learned model memorises them.

## What ships

| class | method | top pick correct, known / novel | confident calls: precision / recall, known | confident calls: precision / recall, novel |
|---|---|---|---|---|
| holin | context rule (beta 6, W 2; z >= 6) | 0.81 / 0.62 | 0.93 / 0.64 | 0.90 / 0.33 |
| endolysin | context rule (beta 6, W 3; z >= 0) + domain evidence with `--domains` | 0.92 / 0.79 | 0.95 / 0.87 | 0.85 / 0.64 |
| spanin | learned caller (S >= 0.02) | **0.91 / 0.80** | 0.98 / 0.69 | **0.98 / 0.51** |

All figures are from family-grouped cross-validation, out of fold, against CPT curation (an uncurated real gene counts
against them). For spanins, the context rule's figures on the same folds were 0.83 / 0.73 top pick and 0.89 / 0.46
for confident novel-family calls.

Held out (the experimental set, never seen): the shipped choices match or beat the alternatives there too. The spanin
caller puts a proven spanin first in all 4 genomes (context rule 3 of 4).

Through the real predictor: Serwaa holin 012 / endolysin 011 / spanin 010; DAC15 endolysin gp039 (by its GH73 domain),
holin gp095 as a candidate and no confident spanin; lambda from bare DNA S / R / Rz; T7 holin 17.5, endolysin gp3.5 and
o-spanin 18.7; Mu endolysin Mu_22 and o-spanin Mu_55 -- the proven genes in each case.

## Holins: what is and is not fixable

- The jumbo-phage misses are one family, the T4-type holins (217-218 aa, one TM). Under the novel-family test the family
  is removed and nothing like it remains; in T4-like phages the holin is not next to the endolysin, so context cannot
  help. In practice T4-like phages are a well-known family, which the known-family figures (0.81 top pick) describe.
- Several apparent misses are annotation artefacts: lambda-like S annotated twice (105-aa holin and 107-aa antiholin,
  one gene); *Burkholderia* phages whose top pick is CPT's own "antiholin/holin".
- The learned caller did not help holins once related phages were kept out of its training, so holins keep the rule.
