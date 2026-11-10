# Putative novel holins from the mined pool

Model `holin_model_curated.pkl` scored 24,064 proteins from 300 phage genomes (none in the benchmark). Recovery check: 202/226 of the pool's own annotated holins score ≥ 0.9.

**Putative novel** = score ≥ 0.9, un-annotated, not a spanin, and < 0.3 identity to any of 5,055 known holins. **Strong** adds a lysis-cassette neighbour (evidence the model never sees).

- Strong (score + context + no homology): **10**
- Putative novel, no genomic context: **21**
- Known family, just unannotated here (not novel): **150**

## Strongest candidates — high score, lysis-cassette context, no homology to a known holin

| score | id→known | len | lysis context | accession | gene | product |
|---|---|---|---|---|---|---|
| 0.997 | 0.30 | 113 | endolysin | NC_014459.2 | 33 | hypothetical protein |
| 0.992 | 0.26 | 87 | endolysin | NC_027627.1 | — | minor tail protein |
| 0.989 | 0.00 | 63 | endolysin, endolysin | NC_023594.2 | — | hypothetical protein |
| 0.984 | 0.29 | 89 | endolysin | NC_027628.1 | — | minor tail protein |
| 0.981 | 0.28 | 87 | endolysin | NC_027629.1 | — | minor tail protein |
| 0.976 | 0.26 | 140 | endolysin | NC_015584.1 | 31 | hypothetical protein |
| 0.973 | 0.29 | 87 | endolysin | NC_003390.2 | — | hypothetical protein |
| 0.962 | 0.00 | 62 | endolysin, Rz-like spanin | NC_005178.1 | orf23 | hypothetical protein |
| 0.934 | 0.00 | 76 | endolysin | NC_011398.1 | — | hemolysin |
| 0.930 | 0.00 | 45 | endolysin | NC_013694.1 | 7 | hypothetical protein |

## Putative novel without genomic context (treat with more caution)

| score | id→known | len | lysis context | accession | gene | product |
|---|---|---|---|---|---|---|
| 0.999 | 0.00 | 53 | — | NC_011269.2 | 77 | hypothetical protein |
| 0.997 | 0.00 | 68 | — | NC_027629.1 | — | hypothetical protein |
| 0.995 | 0.25 | 86 | — | NC_006938.1 | — | gp04 |
| 0.993 | 0.00 | 56 | — | NC_009531.1 | 48 | gp48 |
| 0.992 | 0.00 | 65 | — | NC_019516.2 | — | hypothetical protein |
| 0.992 | 0.23 | 103 | — | NC_006882.2 | — | hypothetical protein |
| 0.992 | 0.00 | 81 | — | NC_005135.1 | — | hypothetical protein |
| 0.990 | 0.29 | 132 | — | NC_004683.1 | — | gp29 |
| 0.988 | 0.26 | 79 | — | NC_014461.1 | 91 | hypothetical protein |
| 0.984 | 0.00 | 47 | — | NC_011398.1 | — | hypothetical protein |
| 0.965 | 0.22 | 118 | — | NC_012530.1 | — | hypothetical protein |
| 0.953 | 0.28 | 99 | — | NC_003907.2 | — | hypothetical protein |
| 0.948 | 0.29 | 113 | — | NC_007610.1 | — | hemolysin |
| 0.944 | 0.00 | 110 | — | NC_005880.2 | — | hypothetical protein |
| 0.937 | 0.00 | 53 | — | NC_015269.1 | — | hypothetical protein |
| 0.924 | 0.00 | 48 | — | NC_011421.1 | 27.7 | gp27.7 |
| 0.923 | 0.00 | 35 | — | NC_027356.1 | — | hypothetical protein |
| 0.913 | 0.00 | 47 | — | NC_017969.1 | orf014 | hypothetical protein |
| 0.910 | 0.00 | 110 | — | NC_007066.1 | — | hypothetical protein |
| 0.904 | 0.00 | 59 | — | NC_008367.1 | — | PfWMP4_21 |
| 0.902 | 0.24 | 94 | — | NC_021335.1 | 9 | hypothetical protein |

## Known families, newly found members (validation, not discovery)

| score | id→known | len | lysis context | accession | gene | product |
|---|---|---|---|---|---|---|
| 1.000 | 1.00 | 93 | — | NC_016562.1 | — | hypothetical protein |
| 1.000 | 0.31 | 182 | endolysin | NC_009016.1 | — | putative phage-related protein |
| 1.000 | 0.43 | 84 | endolysin, endolysin | NC_014461.1 | 28 | hypothetical protein |
| 1.000 | 0.37 | 114 | — | NC_023701.1 | 17 | hypothetical protein |
| 1.000 | 0.97 | 93 | — | NC_015464.1 | — | hypothetical protein |
| 1.000 | 1.00 | 134 | endolysin, Rz-like spanin | NC_004775.2 | — | membrane protein |
| 1.000 | 0.40 | 123 | — | NC_022331.2 | — | hypothetical protein |
| 1.000 | 0.34 | 73 | — | NC_021780.1 | — | hypothetical protein |
| 1.000 | 0.35 | 88 | endolysin | NC_006938.1 | — | gp89 |
| 1.000 | 0.33 | 196 | — | NC_015296.1 | — | putative uncharacterised protein |
| 1.000 | 0.32 | 73 | — | NC_019417.1 | — | hypothetical protein |
| 1.000 | 0.33 | 73 | — | NC_021779.1 | — | hypothetical protein |
| 1.000 | 0.32 | 73 | — | NC_021315.1 | — | hypothetical protein |
| 0.999 | 0.42 | 84 | endolysin, endolysin | NC_015584.1 | 30 | hypothetical protein |
| 0.999 | 1.00 | 70 | endolysin | NC_001884.1 | yomB | involved in bacteriocin production or  |