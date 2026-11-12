# Capacity sweep: does the endolysin model improve with more data, more capacity, or a clean
# early-stopping split?

Three levers, six configurations, two follow-up experiments (subsample, three seeds; restore-127, four
arms), and twenty-six paired tests. `scripts/40_logo_benchmark.py` for the runs, `scripts/41_paired_delta.py` for the
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

**Q2 -- does the homology-contaminated early-stopping split matter?** For v1, yes; for v2, no. This
answer has been wrong twice and is now settled by a paired test. I first reported it as worth "+0.046
realistic AP and +0.084 strict top-1" from the v1 pair alone; then, when the v2 pair showed nothing, I
said the effect "is not there". Both were premature. Paired on the same genomes:

| data | protocol | delta (ES auto -> off) | CI95 | p |
|---|---|---|---|---|
| v1 | strict | -0.0082 | [-0.0509, +0.0332] | 0.802 |
| **v1** | **realistic** | **+0.0456** | **[+0.0170, +0.0698]** | **0.001** |
| v2 | strict | +0.0068 | [-0.0423, +0.0530] | 0.825 |
| v2 | realistic | -0.0039 | [-0.0355, +0.0247] | 0.764 |

The v1 realistic gain is the strongest single result in this report: never worse in any of 4,000
resamples, and p = 0.001 survives a Bonferroni correction over every contrast run here. It is an
interaction, not a general effect -- early stopping off helps the v1 training set and does nothing for
v2, and helps neither on the strict protocol. A plausible reading, not tested: with cleaner labels the
extra boosting rounds keep learning signal, with v2's noisier mined labels they fit noise. Practically,
**the shipped endolysin model is v1 data trained with early stopping on**, so the measured-best variant
is not the one shipped.

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
| **left training** (v1 -> v2) | 304 | 177 (58%) | 60 (20%) | 51 (17%) | 16 (5%) |
| **added** in v2 | 1,124 | 1,059 (94%) | 23 (2%) | 34 (3%) | 8 (1%) |

So the expansion changed the training set in three ways at once: 127 curated positives (pool,
validated, reviewed) that v1 trained on left training, 177 Pfam-tier records from core families left
it too, and 1,059 domain-mined records joined it. This experiment shows the composition change is what
hurt; it cannot say which part. (The 127 curated records were moved into v2's gold holdout, not
discarded -- see the restore test below, which also shows they were not the cause.)

## Restoring the 127 curated positives: they were not the cause

The subsample test located the loss in composition. The obvious suspect was 127 curated positives (60
pool, 51 UniProt-validated, 16 reviewed) that v1 trained on and v2 did not. They turned out never to
have been discarded: scripts/27 draws the gold holdout as 20% of homology *clusters* with a fixed seed,
v2's re-clustering changed the cluster ids, the same seed drew different clusters, and v2's draw
landed on larger ones -- 631 positives held out (23%) against 192 (13%) for v1. That draw swept the 127
into v2's holdout.

`scripts/42_restore_holdout.py` returned exactly those 127 to v2's training set (every record keeps v2's
cluster id), plus three count-matched controls returning 127 random held-out **Pfam-mined** records
instead. All at early stopping off, 400/31. Records are flipped by position, because ids are not unique
in v2 -- a first build that flipped by id dragged in 9 extra records and was caught by a count check
before anything ran.

| arm | train positives | strict AP | realistic AP |
|---|---|---|---|
| v1 | 1,337 | 0.6141 | 0.8092 |
| **v2 + 127 curated restored** | 2,284 | **0.5727** | **0.7546** |
| v2 + 127 Pfam-mined (3 seeds) | 2,284 | 0.5573 (0.5629, 0.5535, 0.5555) | 0.7415 (0.7450, 0.7479, 0.7317) |
| v2 | 2,157 | 0.5753 | 0.7479 |

| contrast | protocol | delta | CI95 | p | worse in |
|---|---|---|---|---|---|
| v2 -> restore curated | strict | -0.0026 | [-0.0318, +0.0280] | 0.853 | 57% |
| v2 -> restore curated | realistic | +0.0067 | [-0.0116, +0.0266] | 0.524 | 26% |
| v1 -> restore curated (gap left) | strict | -0.0415 | [-0.0878, +0.0034] | 0.070 | 96% |
| v1 -> restore curated (gap left) | realistic | **-0.0546** | **[-0.1030, -0.0083]** | **0.017** | **99%** |
| curated -> Pfam-mined, equal count | strict | -0.0154 | [-0.0440, +0.0128] | 0.313 | 84% |
| curated -> Pfam-mined, equal count | realistic | -0.0131 | [-0.0336, +0.0055] | 0.191 | 90% |
| v2 -> add 127 Pfam-mined | strict | -0.0180 | [-0.0404, +0.0018] | 0.079 | 96% |
| v2 -> add 127 Pfam-mined | realistic | -0.0064 | [-0.0216, +0.0084] | 0.429 | 79% |

**Restoring the curated records recovers almost nothing.** It moves v2 by -0.003 strict and +0.007
realistic, and the gap to v1 stays essentially whole: -0.0546 realistic (it was -0.0613), still
excluding zero, and -0.0415 strict (it was -0.0389). The reading fixed before the run was "restore
~ v2 means the curated records were not the cause", and that is what happened.

**The equal-count comparison leans one way and does not resolve.** At an identical 2,284 positives the
curated set beats the Pfam-mined one by 0.015 strict and 0.013 realistic (the controls are worse in
84% and 90% of resamples). Adding 127 more Pfam-mined records to v2 *lowers* strict AP by 0.018 (worse
in 96%, p = 0.079). Nothing here crosses significance, but every contrast in this block points the same
way: curated positives are roughly neutral at the margin, mined ones slightly harmful.

**What the pre-specified reading over-simplified.** It said that if restoring failed, the loss "was the
added Pfam-mined records". That skipped a second difference between v2 and v1. v1 trained on 177
Pfam-tier records that v2 does not -- 90 swept into v2's holdout by the same redraw, 87 cut outright by
the rebuild's cap or guard -- and they come from the core families (PF00959 phage lysozyme 68, PF05257
32, PF01510 31, PF01520 24, PF31067 19). So the gap now sits on two candidates this experiment cannot
separate: **the ~1,100 records v2 added**, or **the 177 core-family records it lost**. The Pfam-mined
controls favour the first, without settling it. Restoring the 90 held-out ones is the cheap test.

### Correction to the composition write-up above

An earlier version of this report said v2 "discarded 127 curated positives". They were not discarded;
they were moved into v2's gold holdout by the cluster redraw described here. The broader lesson stands
and is worth stating on its own: **the "frozen" gold holdout is frozen only within a dataset version.**
Rebuilding the dataset re-draws it, so it changes which records train *and* which records evaluate.
Gold-holdout scores are not comparable across versions -- which `scripts/35` already enforces -- and
training sets across versions differ by more than whatever the rebuild was meant to change.

### Answer to the original question

*Don't we learn more with more data?* Measured directly: **more data of the same kind did nothing**
(+/-0.006 AP), and **the expansion hurt because of what it contained, not how much of it there was**. The
general principle is not wrong; it is conditional on the added data being as good as what it joins.
Domain-mined labels are not, at least not here, and in this build they came at the expense of curated
ones.

## What this says about where the ceiling is

Of three levers, only one moved anything: fixing the contaminated early-stopping split, and only for
the v1 training set (+0.046 realistic, nothing on strict). More data did not help -- the expansion hurt
through its composition -- and more capacity did not help. A model that responds to neither data nor
capacity on the strict protocol, where it must generalise to unseen families, is limited by its inputs.
The features are 36 handcrafted descriptors plus a 480-dimensional mean-pooled ESM-2 35M embedding, and
mean-pooling is the obvious suspect: it discards the positional structure that distinguishes a catalytic
domain in context from the same residues elsewhere. That fits the two documented failures. DAC15 gp039
scored 0.0059; its 80%-identical relative only entered training with v2. Serwaa's endolysin scored
0.3641 with a 50%-identical relative in training all along, and InterProScan finds no domain in it in
any of 23 member databases, so nothing but homology or genomic context can find it.

Similarity features -- maximum identity to the class's training set -- were the obvious next test, and
were tested (`reports/similarity_features.md`). As a model input they cut strict AP from 0.614 to 0.306
(shortcut learning: real endolysins in training nearly always have close relatives, so the model learns to
distrust genes without one). As a promotion rule they add nothing for known families. The model already
uses homology implicitly. Genomic context is the remaining untested signal.

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
