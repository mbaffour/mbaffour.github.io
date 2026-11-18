# Comparison with established methods

`scripts/60_baselines.py`. Per genome: is the top-ranked protein the curated gene ("call"), is a curated gene in the
top 5, and does the method assign the class to the curated gene at all ("coverage"). 95% CI by gene-content cluster
bootstrap.

- **PHROGs** -- the profile database behind Pharokka (v4 HMMs from the Pharokka v1.11.0 database bundle, Zenodo record
  21755221; 38,880 profiles, 305 in the lysis category). As in Pharokka, a protein takes its best PHROG (E <= 1e-5);
  proteins whose best PHROG is a holin / endolysin / spanin profile are ranked by bit score.
- **Pfam lysis domains** -- proteins with a catalytic or family-defining lysis domain, ranked by E-value.
- **Ours** -- leave-one-genome-out under three protocols (known family: near-copies removed; unseen family: 30%-identity
  families removed; remote homology removed: jackhmmer, `../remote_homology.md`).
- **PHROGs, else ours** -- PHROGs where it assigns the class in a genome, our model where it assigns nothing.

PHROGs v4 was built from the phage genomes available around 2019-2020 and has effectively seen most benchmark genes,
so the fairest comparison is on genomes deposited later.

## CPT genomes deposited from 2022 on (not available when PHROGs was built)

| the call is the curated gene | PHROGs | ours, known family | ours, unseen family | PHROGs, else ours (unseen) |
|---|---|---|---|---|
| holin (33 genomes) | 0.64 [0.41, 0.87] | **0.76** [0.54, 0.97] | 0.48 [0.28, 0.74] | 0.67 [0.45, 0.90] |
| endolysin (50) | 0.58 [0.33, 0.84] | **0.92** [0.82, 0.98] | 0.76 [0.58, 0.89] | 0.90 [0.80, 0.97] |
| spanin (46) | **0.89** [0.71, 1.00] | 0.65 [0.41, 0.91] | 0.54 [0.32, 0.77] | **0.91** [0.74, 1.00] |
| curated gene in the top 5 / covered | PHROGs | ours, known | ours, unseen | hybrid |
| holin | 0.91 / 0.91 | 0.97 / 1 | 0.85 / 1 | 1.00 / 1 |
| endolysin | 0.62 / 0.62 | 1.00 / 1 | 0.96 / 1 | 1.00 / 1 |
| spanin | 0.96 / 0.96 | 0.94 / 1 | 0.94 / 1 | 1.00 / 1 |

## All CPT genomes (129) and the experimental set (24)

| CPT, call | PHROGs | Pfam | ours, known | ours, unseen | ours, remote removed | PHROGs, else ours (unseen) |
|---|---|---|---|---|---|---|
| holin | 0.76 | 0.54 | 0.70 | 0.54 | 0.50 | 0.78 |
| endolysin | 0.69 (coverage 0.76) | 0.74 | 0.90 | 0.76 | 0.56 | 0.90 |
| spanin | 0.89 | 0.31 | 0.79 | 0.72 | 0.63 | 0.93 |

Experimental set: PHROGs calls 8/8 holins, 18/22 endolysins (4 not assigned), 4/4 spanin genomes; ours (known family)
7/8, 18/22 (all 22 in the top 5), 3/4; PHROGs-else-ours 8/8, 20/22, 4/4.

## Reading

- **Endolysins: our model is clearly better.** PHROGs assigns no endolysin to 24% of CPT curated endolysins (38% in
  genomes from 2022 on); ours ranks the curated gene first in 0.90-0.92 (known family) and has it in the top 5 in all.
- **Holins: comparable; ours ahead on new genomes** (0.76 vs 0.64, intervals overlapping); PHROGs ahead on older ones.
- **Spanins: PHROGs is better at naming the gene** (0.89 vs 0.65 on new genomes); ours puts it in the top 5 as often.
- **The two are complementary.** PHROGs where it calls, our model where it is silent, is at least as good as the
  better of the two for every class, and puts the curated gene in the top 5 in every genome. That is the practical
  recommendation: run the predictor alongside Pharokka, not instead of it.
- For a gene from a genuinely new family, our model's unseen-family figures apply; PHROGs, a homology method, has no
  equivalent fallback -- its misses are the "coverage" gaps above.
