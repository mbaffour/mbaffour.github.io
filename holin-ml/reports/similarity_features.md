# Similarity to known lysis proteins: tested, not adopted

**Question.** Two documented failures were rescued by homology rather than by the model: DAC15 gp039 by its domain and
Serwaa's endolysin, which has no domain anywhere but a 50%-identical relative in training. Does giving the endolysin
model explicit similarity to its training set help?

**Answer: no.** As a model input it halves novel-family performance. As a separate promotion rule it adds nothing for
known families. The model already uses homology implicitly. Run with `scripts/40_logo_benchmark.py --sim-features`
on the shipped configuration (v1 positives, current spanin negatives, early stopping off, 400/31); paired tests with
`scripts/41_paired_delta.py`.

## The feature and its leakage controls

One number per protein: its maximum identity to the class's training positives. Identity uses the same rule the
protocols use to remove homologues (Smith-Waterman; coverage of the shorter sequence >= 0.5; score >= 80); anything
below the rule counts as 0. Training proteins never see themselves (self and exact duplicates masked). Each held-out
genome is measured only against positives that survive its homology removal.

Checked on the output, not assumed: under the strict protocol every true gene's feature is at most **0.299** (< 0.3,
as the protocol requires); under the realistic protocol at most **0.947** (< 0.95).

## Results (endolysin, 95 genes in 63 genomes)

| version | strict AP | realistic AP |
|---|---|---|
| shipped model | 0.614 | 0.809 |
| shipped + similarity as a model input | **0.306** | 0.828 |
| similarity alone (nearest neighbour) | 0.019 | 0.604 |

Paired against the shipped model:

| change | protocol | delta | 95% CI | p |
|---|---|---|---|---|
| similarity as input | strict | **-0.308** | [-0.378, -0.221] | <0.001 |
| similarity as input | realistic | +0.019 | [-0.039, +0.085] | 0.54 |
| promote if identity >= 0.4 | strict / realistic | -0.241 / +0.016 | | <0.001 / 0.62 |
| promote if identity >= 0.5 | strict / realistic | -0.104 / -0.002 | | <0.001 / 0.90 |
| promote if identity >= 0.6 | strict / realistic | -0.079 / -0.000 | | 0.009 / 0.98 |
| promote if identity >= 0.7 | strict / realistic | -0.054 / +0.006 | | 0.09 / 0.79 |

## Why the input version fails: shortcut learning

About 20% of ordinary, non-lysis phage proteins reach >= 0.3 identity to some training endolysin: alignment noise.
Training endolysins almost all have a close relative in the training set, far above that. The model learns that a
real endolysin always has a close relative, and a gene from a new family breaks that rule, so it is pushed down.
Similarity alone is near-useless for novel families (AP 0.019) by construction, and the model leans on it anyway.

## Why the promotion rule does not help

On known families the model already ranks true genes with close relatives at or near the top, so promotion has
nothing to add. That fits the nearest-neighbour baseline: plain identity reaches 0.604 against the model's 0.809.

On novel families the apparent harm is mostly a labelling artefact. At identity >= 0.5 the rule promotes seven proteins
not named as endolysins. Six are mycobacteriophage genes named only "gpNN" and 54-100% identical to training
endolysins; the model already scores them 0.93-1.00:

| genome | protein | identity | model P |
|---|---|---|---|
| NC_004687 (Bxz1) | gp238 | **1.00** | 1.000 |
| NC_011044 (Nigel) | gp43 | 0.94 | 0.966 |
| NC_008195 (Cooper) | gp45 | 0.92 | 0.980 |
| NC_008198 (PBI1) | gp39 | 0.68 | 0.999 |
| NC_011292 (KONSTANTINE) | gp43 | 0.65 | 0.981 |
| NC_011039 (Predator) | gp40 | 0.54 | 0.929 |
| NC_000924 (933W) | hypothetical protein | 0.55 | 0.000 |

Bxz1 gp238 is an exact match to a sequence already labelled endolysin in training. These are almost certainly real
lysis enzymes whose GenBank records do not name them. (Mycobacteriophages carry both LysA, the endolysin, and LysB, an
esterase; which these are is not settled here.) The benchmark grades by product name and counts them wrong.

## Consequences

- **Not adopted.** The shipped endolysin model is unchanged.
- **The benchmark understates precision for every model**, because unnamed lysins count as false positives. This
  affects all comparisons equally, so no paired result changes, but absolute precision figures are conservative.
- **The two motivating cases are not similarity problems.** DAC15 gp039's 80%-identical relative was never in the
  shipped training set, so no similarity feature could see it; the domain scan already finds it. Serwaa's endolysin is
  already called by the shipped model (0.894).
- What remains for genes like Serwaa's is genomic context: their position in the lysis cassette.
