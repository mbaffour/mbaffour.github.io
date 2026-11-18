# Transmembrane topology against EXPERIMENTAL data

Swiss-Prot transmembrane features for bacterial proteins are mostly predictions (ECO:0000255), so the earlier
validation partly measured agreement with older predictors. Here only reviewed proteins whose every TRANSMEM feature
carries experimental evidence (ECO:0000269) are used, excluding anything the predictor trained on
(`scripts/55c_tm_experimental.py`; `tm_experimental.json`; DeepTMHMM run on BioLib).

| | our predictor | DeepTMHMM | hydropathy heuristic |
|---|---|---|---|
| **bacteria + viruses (22 proteins)**: exact helix count | 0.86 | **0.95** | 0.59 |
| helices recovered / precision | 0.96 / 0.99 | 0.98 / 0.99 | 0.74 / 0.96 |
| N-terminus side (experimental topology) | 8 / 10 | 9 / 10 | -- |
| **all organisms (449)**: exact helix count | 0.51 | **0.86** | 0.29 |
| helices recovered / precision | 0.83 / 0.99 | 0.97 / 0.97 | 0.68 / 0.96 |
| N-terminus side | 142 / 185 (0.77) | **176 / 188 (0.94)** | -- |

**Reading.** Within its training domain (bacterial and viral proteins) our predictor is close to DeepTMHMM; outside
it (mostly eukaryotic multi-pass proteins) it misses helices. DeepTMHMM is the better-validated tool, and the two agree
on holin class in 76-100% of genomes per phage family (`external/comparison.md`).

**Decision.** In the final, frozen analysis holin classes are reported from DeepTMHMM, with our predictor as an
independent concordance check; SAR endolysins stay as the consensus of both; lipoproteins from SignalP 6.0.
