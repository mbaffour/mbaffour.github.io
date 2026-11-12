# CPT-curated phages: does the model find the curated lysis genes?

**Truth = lysis genes curated by hand at the Center for Phage Technology**, in every CPT genome in NCBI
(`scripts/44_fetch_cpt.py`). CPT annotates lysis genes manually with a controlled vocabulary (holin classes I-III,
pinholin; endolysin, SAR endolysin; i-, o-, u-spanin, Rz-like spanin). That is expert curation, not experiment, and is
reported separately from the experimental benchmark (`reports/validated_benchmark.md`). The models never see these
names: they score each protein from its amino-acid sequence alone, and the names only grade the result.

**Set:** 186 NCBI records, of which 56 duplicate another (a GenBank record and its RefSeq copy, or a resequenced phage),
leaving **130 distinct genomes**: 125 endolysins in 119 genomes, 78 holins in 78, 162 spanins in 90. Antiholins and
virion-associated lysins are excluded, as everywhere else.

**Protocol:** leave-one-genome-out. Before a genome is scored, its curated genes' near-copies (>= 95% identity, *known
family*) or whole family (>= 30%, *novel family*) are removed from training. Shipped recipes. **Metric: rank** of each
curated gene among all proteins of its genome, with 95% CIs by bootstrap over genomes (`scripts/45_rank_report.py`).

## Results

| gene | test | genes / genomes | ranked 1st | in top 5 | median rank |
|---|---|---|---|---|---|
| endolysin | known family | 125 / 119 | 0.808 (0.74-0.87) | **0.952** (0.91-0.98) | 1 |
| endolysin | novel family | 125 / 119 | 0.688 (0.61-0.77) | **0.912** (0.86-0.96) | 1 |
| holin | known family | 78 / 78 | 0.705 (0.60-0.80) | **0.936** (0.87-0.99) | 1 |
| holin | novel family | 78 / 78 | 0.538 (0.42-0.64) | **0.846** (0.76-0.92) | 1 |
| spanin | known family | 162 / 90 | 0.475 | **0.926** (0.88-0.96) | 2 |
| spanin | novel family | 162 / 90 | 0.383 | **0.852** (0.79-0.90) | 2 |

Spanin top-1 per gene is capped because most genomes carry an i/o pair that cannot both rank first. Per genome, the
best-ranked curated spanin is **1st in 86% (known) / 69% (novel)** and in the top 5 in 96% / 88%.

By spanin type (novel family, top 5): o-spanin 99% (79 genes), i-spanin 87% (76), u-spanin 90% (10), **Rz-like 72%
(60)**. By holin type (novel family, top 5): class I 100% (15), class II 90% (21), pinholin 100% (6), unclassified 80%
(83), class III 1 of 3. Endolysin: canonical 92% top 5 / 69% first; SAR endolysins 90% / 48%.

## Agreement with the experimental benchmark

| novel family, in top 5 | CPT-curated | experimental (bare DNA) |
|---|---|---|
| endolysin | 91% of 125 | 20 of 21 |
| holin | 85% of 78 | 7 of 8 |
| spanin (best per genome) | 88% of 90 | 3 of 4 |

The two benchmarks, built from independent evidence, agree. The curated set is large enough for intervals of about
+/-5-9 points, so it can now resolve model changes the old panel could not.

## Where it fails (novel family)

- **Holins in jumbo phages:** Marfa 67th of 279 proteins, EI 39th of 295, pKp20 36th of 272, CcrColossus 20th of
  446. Large genomes with atypical holins.
- **Rz-like spanins** are the weakest spanin type (72% in the top 5); a run of closely related *Pseudomonas*-phage
  PI genomes ranks them 23rd-29th of ~88.
- **Endolysins:** Cerberus 93rd of 97 ("endolysin endopeptidase"), Pagan 21st of 59 (SAR endolysin), Magnus 19th of 212.
- SAR endolysins rank first less often than canonical ones (48% vs 69%): their N-terminal membrane anchor makes them
  look partly like membrane proteins.

## Housekeeping found on the way

- NCBI holds 55 CPT genomes twice (GenBank record + RefSeq copy). `scripts/44` now keeps one record per genome
  (identical DNA, or the same organism), preferring CPT's own record.
- The older 66-genome panel had the same problem twice over (`NC_001825` / `NC_001825.1`; `NC_015274` / `NC_015274.1`).
  Removing the copies lowers the shipped endolysin AP from 0.614 to 0.605 (novel) and 0.809 to 0.805 (known): below
  that panel's ~0.05 resolution, and paired comparisons (both arms on the same genomes) are unaffected.
  `scripts/40` now skips duplicate DNA on load.
- The run itself was made before de-duplication; `scripts/45` reports on the de-duplicated set without refitting,
  since a genome's ranks depend only on its own curated genes.
