# A stricter test of generalisation: remove remote homologues found by profile search

**Concern.** The novel-family protocol removes training positives at >= 30% pairwise identity (and their whole
clusters). Remote homologues below that line -- detectable by profile methods, and plausibly by the protein language
model -- stay in training, so "novel family" may overstate generalisation.

**Protocol** (`scripts/40_logo_benchmark.py --remote-homology`, new `remote_removal`): for each test genome, a jackhmmer
search seeded with each curated gene (3 iterations, inclusion and reporting E <= 1e-3) is run against the training
positives; every positive it finds, plus its whole cluster, is removed before training, on top of everything the
30% rule removes. Jackhmmer links 1,574 of 3,250 holin positives, 622 of 937 endolysin positives and 1,255 of 1,306
spanin positives to at least one CPT curated gene.

CPT, per genome, 95% CI by gene-content cluster bootstrap (`remote_homology_summary.json`):

| | known family (>= 95% removed) | novel family (30% rule) | **remote homology removed** |
|---|---|---|---|
| holin, ranked 1st | 0.71 [0.53, 0.86] | 0.54 [0.39, 0.71] | **0.50 [0.35, 0.68]** |
| holin, top 5 | 0.94 [0.88, 0.99] | 0.85 [0.74, 0.95] | **0.83 [0.72, 0.93]** |
| endolysin, ranked 1st | 0.87 [0.79, 0.94] | 0.74 [0.63, 0.84] | **0.55 [0.39, 0.71]** |
| endolysin, top 5 | 0.99 [0.98, 1.00] | 0.90 [0.83, 0.96] | **0.82 [0.66, 0.94]** |
| spanin, top 5 (per gene) | 0.93 [0.83, 1.00] | 0.91 [0.79, 0.99] | **0.90 [0.77, 0.99]** |
| spanin, best per genome in top 5 | 0.97 [0.90, 1.00] | 0.97 [0.90, 1.00] | **0.97 [0.90, 1.00]** |

**Reading.**
- Holins and spanins barely move: their unseen-family estimates were not resting on remote homologues left in
  training. That is the strongest evidence yet that the models recognise holin and spanin character (membrane topology,
  lipoprotein signals, size), not only family membership.
- Endolysins drop most (ranked 1st 0.74 -> 0.55; top 5 0.90 -> 0.82). Their catalytic domains are ancient,
  widespread enzyme families, and the model leans on that remote similarity. The honest statement for an endolysin from
  a genuinely new fold is "in the top five about 80% of the time".
- This is now the reported "never seen" estimate; the 30%-identity figures are reported as "unseen family".
