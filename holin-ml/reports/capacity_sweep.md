# Capacity sweep: does the endolysin model improve with more data, more capacity, or a clean
# early-stopping split?

Three levers, six configurations, a follow-up subsample experiment with three seeds, and sixteen
paired tests. `scripts/40_logo_benchmark.py` for the runs, `scripts/41_paired_delta.py` for the
differences. Endolysin only; 63 genomes, 95 annotated truths.

The question came from a direct challenge: *don't we learn more with more data in an ML model?* The
answer below has two halves. The v2 expansion measurably **hurt** (-0.061 realistic AP at the
configuration where the benchmark can resolve it). And the subsample experiment shows the damage came
from **what was added, not how much**: matched to v1's count and class ratio, v2's mix loses 90% of
the same ground, while 820 extra records of that mix move AP by 0.006.

## The configurations

`v1` is the shipped endolysin training set (1,337 positives after the gold holdout). `v2` is the
family expansion -- 14 added catalytic families, 2,157 positives. Both use the same 20,100
negatives. Protocols are leave-one-genome-out with two homology-removal rules: **strict** drops every
training positive >=30% identical to the held-out gene's family, **realistic** drops only >=95%
near-duplicates.

### Strict protocol

| estimator | v1 AP | v2 AP | delta | v1 top-1 | v2 top-1 | v1 r@5 | v2 r@5 |
|---|---|---|---|---|---|---|---|
| auto ES, 400/31, lr 0.06 | 0.6223 | 0.5684 | -0.054 | 0.505 | 0.526 | 0.821 | **0.863** |
| ES off, 400/31, lr 0.06 | **0.6141** | 0.5753 | -0.039 | 0.589 | 0.537 | 0.874 | **0.926** |
| ES off, 800/63, lr 0.04 | 0.5991 | 0.5561 | -0.043 | 0.547 | 0.547 | 0.874 | **0.916** |

### Realistic protocol

| estimator | v1 AP | v2 AP | delta | v1 top-1 | v2 top-1 | v1 r@5 | v2 r@5 |
|---|---|---|---|---|---|---|---|
| auto ES, 400/31, lr 0.06 | 0.7636 | 0.7517 | -0.012 | 0.589 | 0.558 | 0.926 | 0.905 |
| ES off, 400/31, lr 0.06 | **0.8092** | 0.7479 | -0.061 | 0.579 | 0.558 | 0.926 | 0.905 |
| ES off, 800/63, lr 0.04 | 0.7934 | 0.7396 | -0.054 | 0.568 | 0.568 | **0.947** | 0.937 |

Every marginal CI overlaps every other. That is why the differences are tested pairwise below rather
than read off these tables.

## The paired tests

Both configurations in a contrast are scored on the *same* genomes under the same protocol, so the
comparison is paired and the difference has far less variance than either AP alone. Genomes are
resampled once and both APs recomputed on that resample.

| contrast | protocol | delta | CI95 | p | B worse in |
|---|---|---|---|---|---|
| v1 -> v2 data, auto ES 400/31 | strict | -0.0539 | [-0.1171, +0.0239] | 0.193 | 90% |
| v1 -> v2 data, auto ES 400/31 | realistic | -0.0118 | [-0.0538, +0.0313] | 0.614 | 69% |
| **v1 -> v2 data, ES off 400/31** | strict | -0.0389 | [-0.0903, +0.0122] | 0.155 | 92% |
| **v1 -> v2 data, ES off 400/31** | **realistic** | **-0.0613** | **[-0.1126, -0.0108]** | **0.013** | **99%** |
| **v1 -> v2 data, ES off 800/63** | strict | -0.0429 | [-0.0965, +0.0152] | 0.158 | 92% |
| **v1 -> v2 data, ES off 800/63** | realistic | **-0.0538** | [-0.1043, +0.0009] | 0.055 | 97% |
| ES auto -> off, v2 data | strict | +0.0068 | [-0.0423, +0.0530] | 0.825 | 41% |
| ES auto -> off, v2 data | realistic | -0.0039 | [-0.0355, +0.0247] | 0.764 | 62% |
| 400/31 -> 800/63, v2 data | strict | -0.0191 | [-0.0460, +0.0093] | 0.188 | 91% |
| 400/31 -> 800/63, v2 data | realistic | -0.0083 | [-0.0238, +0.0087] | 0.358 | 82% |
| 400/31 -> 800/63, v1 data | strict | -0.0151 | [-0.0541, +0.0212] | 0.436 | 78% |
| 400/31 -> 800/63, v1 data | realistic | -0.0158 | [-0.0380, +0.0042] | 0.145 | 93% |

**One interval excludes zero**, and the contrast next to it comes within 0.001 of doing so. Both are
the data lever on the realistic protocol with early stopping off: -0.0613 (p = 0.013, 99% of
resamples worse) at 400/31 and -0.0538 (p = 0.055, CI upper bound +0.0009, 97% worse) at 800/63.
The effect is therefore not an artifact of one estimator setting -- it appears at both capacities
tested. Those two measurements are correlated rather than independent, being the same datasets and
the same genomes under a different estimator, so this is one effect seen twice, not two
replications.

Multiplicity, stated rather than buried: twelve contrasts, one nominal hit. The Bonferroni threshold
for twelve tests is 0.0042 and p = 0.013 does not survive it. Nothing here survives correction. What
survives inspection is that all six data contrasts share a sign, all four capacity contrasts share a
sign, and the two contrasts that come closest to resolving are the same effect at two capacities.

## Answers

**Q1 -- does more data help?** No, and the subsample experiment below says why. Six AP comparisons
point the same way, and the two that come closest to resolving put the cost at 0.061 and 0.054 AP on
the realistic protocol. Cutting v2 back to v1's exact count and class ratio recovers almost none of
that: 90% of the realistic loss and 98% of the strict loss are composition. The extra count itself is
worth +/-0.006. The one consistent benefit is strict recall@5, better by 0.04 to 0.05 in all three
configurations -- broader family coverage buying reach at the cost of precision.

**Q2 -- does the homology-contaminated early-stopping split matter?** No. This replaces an earlier
claim of mine that it was worth "+0.046 realistic AP and +0.084 strict top-1". That came from one
cell, the v1 realistic protocol. The v2 pair gives -0.0039 (p = 0.76) and the top-1 gain falls from
+0.084 to +0.011. One of four dataset-by-protocol cells showed the effect; it is not there.

**Q3 -- is the model capacity-limited?** No. Going from 400/31 to 800/63 is worse in all four
contrasts -- on both datasets and both protocols, in 78% to 93% of resamples -- never better, never
significantly so.

## Resolving the confound: it is composition, not count

The capacity sweep could not say *why* v2 lost, because v1 and v2 differ in count and composition at
once, and with the 20,100 negatives fixed a count change is also a class-ratio change (1:15.0 vs
1:9.3). So v2's training positives were cut to exactly v1's count -- 1,337, stratified by source so
v2's mix is preserved -- and evaluated at the configuration where the gap resolved (early stopping
off, 400/31). Three seeds. The reading was fixed before any number came back: *recovers v1* means
count/ratio did the damage; *stays at v2* means composition did.

| arm | positives | ratio | curated share | strict AP | realistic AP |
|---|---|---|---|---|---|
| v1 | 1,337 | 1:15.0 | 57% | 0.6141 | 0.8092 |
| **v2 subsample** (3 seeds) | **1,337** | **1:15.0** | **33%** | **0.5759** (0.5612, 0.5713, 0.5953) | **0.7541** (0.7630, 0.7312, 0.7682) |
| v2 | 2,157 | 1:9.3 | 33% | 0.5753 | 0.7479 |

Paired, with each resample averaging over the three seeds so the interval covers seed variance as well
as genome variance:

| contrast | protocol | delta | CI95 | p | worse in |
|---|---|---|---|---|---|
| v1 -> subsample (**composition**, count held) | strict | -0.0382 | [-0.0877, +0.0079] | 0.116 | 94% |
| v1 -> subsample (**composition**, count held) | realistic | **-0.0551** | **[-0.1019, -0.0073]** | **0.021** | **99%** |
| subsample -> v2 (**count/ratio**, mix held) | strict | -0.0006 | [-0.0293, +0.0275] | 0.991 | 50% |
| subsample -> v2 (**count/ratio**, mix held) | realistic | -0.0063 | [-0.0266, +0.0111] | 0.515 | 74% |

(The second pair is printed by `scripts/41` as v2 -> subsample; the signs here are flipped to read in
the v1 -> v2 direction so the two rows add up.)

**The decomposition adds up.** On the realistic protocol, v1 -> v2 is -0.0613; composition accounts for
-0.0551 of it (90%) and count/ratio for -0.0063 (10%). On the strict protocol it is -0.0382 of -0.0388
(98%) against -0.0006. Matching v1's count and class ratio recovers essentially none of the loss.

**The null is the stronger half of this result.** The count/ratio contrast is not merely
non-significant; its interval is narrow -- about +/-0.02 to +/-0.03 -- and centred on zero. Adding 820
more positives of the same mix moved AP by 0.0006 and 0.0063. That is about as close as this benchmark
gets to showing that something does nothing.

**Seed variance mattered.** The three draws span 0.034 strict and 0.037 realistic, the same order as
the effects being measured. One seed alone could have read anywhere from "most of the gap" to "barely
any", which is why the averaged-over-seeds interval is the one reported.

Multiplicity: this was the single pre-specified test of a new experiment, but across the whole sweep it
is one more contrast. p = 0.021 would not survive a Bonferroni correction over every test run here. The
count/ratio null does not depend on any threshold.

### What "composition" means concretely

v2 is not v1 plus extra families. Against v1's training positives:

| | n | Pfam-mined | pool | UniProt-validated | UniProt-reviewed |
|---|---|---|---|---|---|
| **dropped** from v1 | 304 | 177 (58%) | 60 (20%) | 51 (17%) | 16 (5%) |
| **added** in v2 | 1,124 | 1,059 (94%) | 23 (2%) | 34 (3%) | 8 (1%) |

So the expansion did two things at once: it **discarded 127 curated positives** (pool, validated,
reviewed) that v1 trained on, and it **added 1,059 domain-mined ones**. This experiment shows the
composition change is what hurt; it cannot say which of those two halves did it.

The discarded curated records deserve a look on their own. Nothing in the stated purpose of the v2
rebuild -- adding families -- called for removing validated endolysins from training, so their loss
may be a side effect of the rebuild (deduplication, re-clustering or the stratified per-family cap)
rather than a decision anyone made.

### Answer to the original question

*Don't we learn more with more data?* Measured directly: **more data of the same kind did nothing**
(+/-0.006 AP), and **the expansion hurt because of what it contained, not how much of it there was**. The
general principle is not wrong; it is conditional on the added data being as good as what it joins.
Domain-mined labels are not, at least not here, and in this build they came at the expense of curated
ones.

## What this says about where the ceiling is

Three levers -- data volume, model capacity, and a known defect in the training procedure -- and
three nulls. A model that is neither data-limited nor capacity-limited, and that is unaffected by
fixing a contaminated validation split, is limited by its inputs. The features are 36 handcrafted
descriptors plus a 480-dimensional mean-pooled ESM-2 35M embedding, and mean-pooling is the obvious
suspect: it discards the positional structure that distinguishes a catalytic domain in context from
the same residues elsewhere. That is consistent with the two documented failures, DAC15 gp039
(scored 0.0059 with an 80%-identical relative in training) and Serwaa's endolysin (0.3641 with a
50%-identical relative present all along).

Untested and cheapest to test: similarity features -- maximum Smith-Waterman identity to each class's
training set, as explicit model inputs. The information that rescued both failures was homology, and
the model currently has no direct access to it.

## Benchmark power

With 95 truths across 63 genomes the paired CIs are roughly +/-0.05 AP wide on the strict protocol.
The benchmark cannot resolve effects below about 0.05, so a 0.02 improvement from any future change
is not measurable here. Resolving +/-0.03 would need on the order of three times the genomes. Any
claim of a small gain on this benchmark should be read as unmeasurable rather than real.

## Reproducibility

Three configurations were re-run from scratch during this work and had to match reports committed
hours earlier, on AP, both bootstrap CI bounds, top-1 and recall@5, on both protocols. All three
matched exactly: v1_base_es (twice, once fresh and once fully resumed from checkpoints),
v1_noes_400_31 and v1_noes_800_63. The one deviation found anywhere was a 4e-4 shift in a single CI
bound traced to 6-decimal rounding in the checkpoint writer, which is now full precision.

## Not run

The two 1500/127 configurations. About 4.5 hours of fitting in a container that restarted four times
during this work, to add a third point to a capacity curve already sloping down in 4 of 4
comparisons. Left to the user to call rather than spent unilaterally.
