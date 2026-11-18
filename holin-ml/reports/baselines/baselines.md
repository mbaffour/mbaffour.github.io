# Comparison with established methods

`scripts/60_baselines.py`. Per genome: is the top-ranked protein the curated gene ("call"), is a curated gene in the
top 5, and does the method assign the class to the curated gene at all ("coverage"). 95% CI by gene-content cluster
bootstrap. Per-gene and per-genome rows: `release/benchmark_genes.csv`, `release/benchmark_genomes.csv`.

> **Correction (2026-11-18).** The first version of this report understated PHROGs on endolysins. To save time the
> script searched all PHROGs only for proteins that hit a PHROG in the *lysis category*, but 24 PHROGs whose names
> make them endolysins under our rules sit in other categories (18 "transglycosylase" and 2 "glycoside hydrolase" under
> "other", 3 "endolysin" under "head and packaging", 1 "pseudomurein endoisopeptidase"). Proteins whose best hit was one
> of these were never assigned to a class. The script now pre-filters on lysis-named PHROGs as well, which is exact for
> class assignment. The release build, which recomputes these baselines from the per-gene hits, caught the problem
> (`release/build_checks.json`). Changes: PHROGs endolysin call on CPT 0.69 → **0.78**, coverage 0.76 → 0.92; on 2022+
> genomes 0.58 → **0.82**, coverage 0.62 → 0.90; experimental set coverage 18 → 19 of 22; reviewed set top 5
> 0.87 → 0.90. Holin and spanin figures are unchanged. The conclusion "our model is clearly better on endolysins" is
> **withdrawn**: the difference is not significant (below). Earlier numbers are in git history (commit aea9518).

- **PHROGs** -- the profile database behind Pharokka (v4 HMMs from the Pharokka v1.11.0 database bundle, Zenodo record
  21755221; 38,880 profiles). As in Pharokka, a protein takes its best PHROG (E <= 1e-5); proteins whose best PHROG
  names a holin / endolysin / spanin (the benchmark's own name rules, scripts/52c) are ranked by bit score.
- **Pfam lysis domains** -- proteins with a catalytic or family-defining lysis domain, ranked by E-value.
- **Ours** -- leave-one-genome-out under three protocols (known family: near-copies removed; unseen family: 30%-identity
  families removed; remote homology removed: jackhmmer, `../remote_homology.md`).
- **PHROGs, else ours** -- PHROGs where it assigns the class in a genome, our model where it assigns nothing.

PHROGs v4 was built from the phage genomes available around 2019-2020 and has effectively seen most benchmark genes,
so the fairest comparison is on genomes first submitted to GenBank from 2022 on (year from the record's "Submitted"
reference; `cpt_2022plus.json`).

## CPT genomes first submitted from 2022 on

| the call is the curated gene | PHROGs | ours, known family | ours, unseen family | PHROGs, else ours (unseen) |
|---|---|---|---|---|
| holin (33 genomes) | 0.64 [0.41, 0.87] | 0.76 [0.54, 0.97] | 0.48 [0.28, 0.74] | 0.67 [0.45, 0.90] |
| endolysin (50) | 0.82 [0.62, 0.95] | 0.92 [0.82, 0.98] | 0.76 [0.58, 0.89] | 0.92 [0.79, 1.00] |
| spanin (46) | **0.89** [0.71, 1.00] | 0.65 [0.41, 0.91] | 0.54 [0.32, 0.77] | **0.91** [0.74, 1.00] |
| curated gene in the top 5 / covered | | | | |
| holin | 0.91 / 0.91 | 0.97 / 1 | 0.85 / 1 | 1.00 / 1 |
| endolysin | 0.90 / 0.90 | 1.00 / 1 | 0.96 / 1 | 1.00 / 1 |
| spanin | 0.96 / 0.96 | 0.94 / 1 | 0.94 / 1 | 1.00 / 1 |

## All CPT genomes (129) and the other benchmarks

| CPT, call | PHROGs | Pfam | ours, known | ours, unseen | ours, remote removed | PHROGs, else ours (unseen) |
|---|---|---|---|---|---|---|
| holin (78) | 0.76 | 0.54 | 0.70 | 0.54 | 0.50 | 0.78 |
| endolysin (119) | 0.78 (coverage 0.92) | 0.74 | 0.90 | 0.76 | 0.56 | 0.86 |
| spanin (90) | 0.89 | 0.31 | 0.79 | 0.72 | 0.63 | 0.93 |

Experimental set (`validated.json`): PHROGs calls 8/8 holins, 18/22 endolysins (19 covered), 4/4 spanin genomes; ours
(known family) 7/8, 18/22 (all 22 in the top 5), 3/4; PHROGs-else-ours (unseen) 8/8, 19/22, 4/4.
Reviewed Swiss-Prot set (`reviewed.json`), call / top 5: PHROGs holin 0.95/1.00, endolysin 0.87/0.90, spanin
1.00/1.00; ours (known family) 0.84/1.00, 0.90/1.00, 0.80/1.00.

## Paired differences from PHROGs (CPT, call; `paired_vs_phrogs.json`)

Paired cluster bootstrap, 4,000 draws. Added with the correction and not planned in advance; with 18 comparisons,
single p-values near 0.05 should not be read as findings.

| method minus PHROGs | all CPT | 2022+ |
|---|---|---|
| holin, ours known family | -0.05 [-0.27, +0.15] | +0.12 [-0.12, +0.36] |
| holin, ours unseen family | -0.22 [-0.44, +0.01] | -0.15 [-0.40, +0.09] |
| holin, PHROGs else ours | +0.03 [0.00, +0.07] | +0.03 [0.00, +0.10] |
| endolysin, ours known family | +0.12 [-0.02, +0.27] | +0.10 [-0.06, +0.30] |
| endolysin, ours unseen family | -0.03 [-0.18, +0.13] | -0.06 [-0.29, +0.17] |
| endolysin, PHROGs else ours | **+0.08 [+0.01, +0.16]** | +0.10 [0.00, +0.26] |
| spanin, ours known family | -0.10 [-0.29, +0.07] | -0.24 [-0.49, +0.03] |
| spanin, ours unseen family | -0.17 [-0.35, +0.01] | **-0.35 [-0.58, -0.09]** |
| spanin, PHROGs else ours | **+0.04 [+0.01, +0.10]** | +0.02 [0.00, +0.08] |

## Reading

- **Naming the gene: no significant difference between our model and PHROGs for holins or endolysins.** Ours is
  ahead on endolysins by about 0.10-0.12 and the intervals include zero; for genuinely unseen families (our unseen
  protocol) the two are level.
- **Spanins: PHROGs names the gene more often**, significantly so against our unseen-family protocol on recent genomes.
  Both put it in the top 5 equally often.
- **Coverage is where they differ.** PHROGs assigns no class to the curated gene in 6-10% of genomes (endolysin 8% of
  CPT, 10% of 2022+); our model always ranks it, and has it in the top 5 in 91-100% under the unseen-family protocol.
- **The hybrid is the recommendation.** PHROGs where it calls, our model where it is silent, improves on PHROGs alone
  for endolysins (+0.08) and spanins (+0.04) on CPT, never does worse, and puts the curated gene in the top 5 in every
  recent genome. On endolysin calls our model alone (0.90) is level with the hybrid (0.86).
- For a gene from a genuinely new family, our model's unseen-family figures apply; PHROGs, a homology method, has no
  equivalent fallback -- its misses are the coverage gaps.
