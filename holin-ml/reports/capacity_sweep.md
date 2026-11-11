# Capacity sweep: does the endolysin model improve with more data, more capacity, or a clean
# early-stopping split?

Three levers, six configurations, eight paired tests. `scripts/40_logo_benchmark.py` for the runs,
`scripts/41_paired_delta.py` for the differences. Endolysin only; 63 genomes, 95 annotated truths.

The question came from a direct challenge: *don't we learn more with more data in an ML model?* The
honest answer below is no, not here, and at the one configuration where the benchmark can resolve
the difference the extra data measurably **hurt**.

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
| v1 -> v2 data, auto ES | strict | -0.0539 | [-0.1171, +0.0239] | 0.193 | 90% |
| v1 -> v2 data, auto ES | realistic | -0.0118 | [-0.0538, +0.0313] | 0.614 | 69% |
| **v1 -> v2 data, ES off** | strict | -0.0389 | [-0.0903, +0.0122] | 0.155 | 92% |
| **v1 -> v2 data, ES off** | **realistic** | **-0.0613** | **[-0.1126, -0.0108]** | **0.013** | **99%** |
| ES auto -> off, v2 data | strict | +0.0068 | [-0.0423, +0.0530] | 0.825 | 41% |
| ES auto -> off, v2 data | realistic | -0.0039 | [-0.0355, +0.0247] | 0.764 | 62% |
| 400/31 -> 800/63, v2 data | strict | -0.0191 | [-0.0460, +0.0093] | 0.188 | 91% |
| 400/31 -> 800/63, v2 data | realistic | -0.0083 | [-0.0238, +0.0087] | 0.358 | 82% |

**Exactly one interval excludes zero**: the family expansion costs 0.061 AP on the realistic protocol
at the configuration where it had its best chance -- early stopping off, so no contaminated
validation split truncating training, and the capacity setting that performed best overall.

Multiplicity, stated rather than buried: this is one nominally significant result out of eight
contrasts. The Bonferroni threshold for eight tests is 0.00625 and p = 0.013 does not survive it.
What survives correction is nothing; what survives inspection is that the sign is the same in all
six AP comparisons and that the single resolvable contrast is the one where the data lever was
given its fairest test.

## Answers

**Q1 -- does more data help?** No. Six AP comparisons, six pointing the same way, and the one the
benchmark can resolve says the expansion costs 0.061 AP. The one consistent benefit is strict
recall@5: v2 is better by 0.04 to 0.05 in all three configurations, which fits broader family
coverage buying reach at the cost of precision. If the model is used as a shortlist generator, that
trade is arguably worth having; if it is used as a ranker, it is not.

**Q2 -- does the homology-contaminated early-stopping split matter?** No. This replaces an earlier
claim of mine that it was worth "+0.046 realistic AP and +0.084 strict top-1". That came from one
cell, the v1 realistic protocol. The v2 pair gives -0.0039 (p = 0.76) and the top-1 gain falls from
+0.084 to +0.011. One of four dataset-by-protocol cells showed the effect; it is not there.

**Q3 -- is the model capacity-limited?** No. Going from 400/31 to 800/63 is worse in 91% of strict
resamples and 82% of realistic ones, never better, never significantly so.

## The confound in Q1, which blocks the strong version of the claim

v1 and v2 do not differ only in family coverage. They differ in count, and because both use the same
20,100 negatives, they differ in class ratio: **1:15.0 for v1, 1:9.3 for v2**. "More data hurt" is
therefore not separable here from "a different positive-to-negative ratio hurt", and the second is a
calibration effect, not a statement about data volume.

The experiment that separates them: subsample v2 to 1,337 positives while keeping its broader family
diversity, and rerun. Matching v1 would place the harm on count and ratio; staying low would place it
on the added families' label quality. Until that is run, the defensible claim is narrow -- *this
expansion, as built, did not help and probably cost a little* -- not the general one.

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

## Not run

The two 1500/127 configurations. About 4.5 hours of fitting in a container that restarted four times
during this work, to add a third point to a capacity curve already sloping down in 4 of 4
comparisons. Left to the user to call rather than spent unilaterally.
