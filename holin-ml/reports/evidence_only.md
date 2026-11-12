# Training only on evidence: endolysin adopted, spanin not

**Principle (from the user):** the models should learn lysis genes from evidence in the sequence, not from names
someone typed into a genome record. Holin training already met it (Swiss-Prot/TCDB and curated Pfam families). Two
training sets did not:

| class | removed | kept |
|---|---|---|
| endolysin | 368 "pool" positives labelled from RefSeq product names | 969: 332 UniProt PE=1, 67 Swiss-Prot reviewed, 570 carrying a lysis Pfam domain |
| spanin | 760 TrEMBL positives labelled by name, 21 pool | 863: 707 CPT-curated (Kongari 2018), 135 Pfam, 21 reviewed/validated |

Domain-defined labels were kept: they rest on a sequence signal.

**Decision rule, fixed before any result (commit aec44d5):** adopt unless measurably worse, meaning a paired 95% CI on
the CPT-curated set lying entirely below zero for top-1 or top-5 on either protocol. Equal means adopt, on principle.

## Endolysin: adopted

Paired against the model it replaces, 119 CPT genomes:

| | replaced model | evidence-only | difference (95% CI) |
|---|---|---|---|
| ranked 1st, novel family | 0.688 | 0.664 | -0.024 [-0.079, +0.032] |
| ranked 1st, known family | 0.808 | 0.848 | +0.040 [-0.008, +0.088] |
| top 5, novel / known | 0.912 / 0.952 | 0.888 / 0.960 | n.s. both |

Experimental set (22 proven endolysins): ranked 1st 12/22 (novel, was 10) and 15/22 (known, was 12); top 5 21/22 and
22/22. With genomic context re-tuned on its own scores (beta 6, W 3), cross-validated on CPT: ranked 1st **0.720
(novel) / 0.864 (known)**, top 5 0.912 / **0.984**. Confident calls (z >= 0), out of fold: **0.95 precision / 0.88
recall** (known family), 0.83 / 0.61 (novel). At the high-confidence cut-off (0.9995) its protein-level precision on
CPT is higher than the replaced model's (0.887 vs 0.868 known; 0.811 vs 0.733 novel).

Installed as `models/endolysin_model.pkl`; the replaced model is kept as `endolysin_model_v1_pool_retired.pkl`.

## Spanin: not adopted

Paired, 90 CPT genomes:

| | shipped | evidence-only | difference (95% CI) | p |
|---|---|---|---|---|
| top 5, novel family | 0.852 | **0.914** | +0.062 [+0.019, +0.109] | 0.008 |
| ranked 1st, known family | 0.475 | 0.432 | **-0.043 [-0.075, -0.017]** | 0.002 |
| best per genome 1st, known | 0.856 | 0.778 | **-0.078 [-0.133, -0.033]** | 0.002 |

The name-labelled TrEMBL spanins supply close relatives of known spanins. Without them the model generalises better
to unseen spanin families (experimental set: 7/7 in the top 5 under both protocols, against 6/7) but ranks known
families first less often. The known-family CI lies wholly below zero, so the rule keeps the shipped spanin model.

This is a genuine trade-off, not a failure. If the priority is discovering spanins in unusual phages, the evidence-only
spanin model is the better one; for routine annotation of familiar phages the shipped one is. A middle path worth
testing: keep the TrEMBL spanins only where an independent sequence signal agrees (an o-spanin lipobox, i-spanin
transmembrane topology).
