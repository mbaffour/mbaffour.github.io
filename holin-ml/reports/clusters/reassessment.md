# Do the headline results survive when related genomes are not counted as independent?

**Problem.** Every confidence interval so far resampled genomes as if independent. The benchmarks contain groups of
near-identical or closely related phages (three lambda immunity variants in CPT, ten identical Vibrio phages in the
lambdoid set), which makes intervals too narrow.

**Method** (`scripts/58_genome_clusters.py`). Genomes are grouped by single linkage at two levels:
- **ANI >= 95%** (phage species level), from bottom-2000 MinHash sketches of canonical DNA 21-mers (Mash distance).
  Checked: a genome against a copy with 3% of positions mutated reads 96.9%; against its reverse complement, 100%.
- **Shared gene content**: Jaccard >= 0.10 between MinHash sketches of all amino-acid 5-mers of the genome's proteins
  (genus-like; related phages far below 95% ANI still share many proteins). The strictest level, used for decisions.

| benchmark | genomes | ANI-95% groups | gene-content groups |
|---|---|---|---|
| CPT | 129 | 87 | 60 |
| experimental set | 24 | 23 | 20 |
| blind set 1 | 152 | 88 | 65 |
| blind set 2 | 123 | 62 | 45 |

The effective number of independent observations is roughly half the genome count.

## Headline comparisons, re-tested (`scripts/58b_cluster_reassess.py`, `reassessment.json`)

Paired bootstrap, 4,000 draws, resampling genomes vs clusters.

| comparison | by genome | by gene-content cluster | |
|---|---|---|---|
| **Nested o-spanin finder**, CPT from bare DNA, curated spanins in the top 5 (unseen / known family) | +0.131 [+0.087, +0.178] | **+0.131 [+0.065, +0.216]** | **holds** |
| Endolysin virion fix, CPT, unseen family, ranked 1st | +0.059 [+0.017, +0.109] | +0.059 [0.000, +0.124], p = 0.065 | borderline alone |
| Endolysin virion fix, blind set 2, call = annotated endolysin | +0.061 [+0.018, +0.114] | +0.061 [0.000, +0.155], p = 0.076 | borderline alone |
| **Endolysin virion fix, both sets pooled**, joint clusters across sets (233 genomes, 88 clusters) | | **+0.060 [+0.020, +0.103], p = 0.008** | **holds** |
| Holin ESM-2 150M, unseen family, top 5 | -0.077 [-0.141, -0.026] | -0.077 [-0.225, 0.000], p = 0.73 | rejected; "worse" -> "not better" |
| Holin mined families v1, unseen family, ranked 1st | -0.051 [-0.115, 0.000] | -0.051 [-0.118, +0.014] | rejected (unchanged) |
| Holin mined families v2, known family, ranked 1st | -0.064 [-0.128, -0.013] | -0.064 [-0.155, 0.000], p = 0.09 | rejected; "worse" -> "not better" |

**What changes**
- The nested o-spanin finder holds under every resampling scheme.
- The endolysin virion fix is borderline in each benchmark alone (p ~ 0.07) and holds when both are pooled with
  clusters built jointly across them (a quarter of blind set 2 shares gene content with CPT genomes, so the two sets are
  not independent and simply combining their p-values would be optimistic). This pooled test was not planned in
  advance; it is reported as such. The fix is also justified on its own terms: it removes mislabelled training data.
- The rejected holin variants stay rejected (none improved anything), but the claims that some were significantly
  worse no longer hold and are withdrawn.
- From here on every interval uses cluster resampling (`scripts/45_rank_report.py --clusters FILE:gene`).
