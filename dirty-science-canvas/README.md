# Dirty Science Canvas

Membrane-topology and charge atlases for **model bacteriophages and their hosts**. Every annotated protein translation was run through **Phobius**, **DeepTMHMM** and **TOPCONS2** (with OCTOPUS, Philius, PolyPhobius, SCAMPI and SPOCTOPUS) within each service's documented limits; results are normalized with full provenance, validated, and rendered into self-contained offline HTML atlases. All calls are computational predictions, not experimental evidence.

**Start here:** `index.html` → `Dirty_Science_Canvas_Atlas.html` (the combined atlas: every organism in one searchable file). Each organism folder also has its own atlas, README, inputs, untouched raw outputs with job records, normalized `data.json`/CSV and `verification.json`.

| Organism | Kind | RefSeq | Proteins | ≥1 span | Signal peptide | β states | Complete / eligible |
|---|---|---|---|---|---|---|---|
| [Escherichia phage phiX174](phiX174_Topology_Lab_Reference/phiX174_Topology_Atlas.html) | phage | NC_001422.1 | 11 | 0 | 4 | 0 | Phobius 11/11 · DeepTMHMM 11/11 · TOPCONS2 11/11 |
| [Enterobacteria phage M13](M13_Topology_Lab_Reference/M13_Topology_Atlas.html) | phage | NC_003287.2 | 10 | 7 | 4 | 1 | Phobius 10/10 · DeepTMHMM 10/10 · TOPCONS2 10/10 |
| [Escherichia phage MS2](MS2_Topology_Lab_Reference/MS2_Topology_Atlas.html) | phage | NC_001417.2 | 4 | 1 | 0 | 0 | Phobius 4/4 · DeepTMHMM 4/4 · TOPCONS2 4/4 |
| [Enterobacteria phage Qbeta](Qbeta_Topology_Lab_Reference/Qbeta_Topology_Atlas.html) | phage | NC_001890.1 | 4 | 0 | 0 | 0 | Phobius 4/4 · DeepTMHMM 4/4 · TOPCONS2 4/4 |
| [Enterobacteria phage lambda](lambda_Topology_Lab_Reference/lambda_Topology_Atlas.html) | phage | NC_001416.1 | 73 | 9 | 5 | 1 | Phobius 73/73 · DeepTMHMM 73/73 · TOPCONS2 73/73 |
| [Enterobacteria phage T4](T4_Topology_Lab_Reference/T4_Topology_Atlas.html) | phage | NC_000866.4 | 278 | 23 | 21 | 1 | Phobius 278/278 · DeepTMHMM 277/277 · TOPCONS2 277/277 |
| [Enterobacteria phage T7](T7_Topology_Lab_Reference/T7_Topology_Atlas.html) | phage | NC_001604.1 | 60 | 9 | 7 | 0 | Phobius 60/60 · DeepTMHMM 60/60 · TOPCONS2 60/60 |
| [Enterobacteria phage T5](T5_Topology_Lab_Reference/T5_Topology_Atlas.html) | phage | NC_005859.1 | 162 | 20 | 12 | 0 | Phobius 162/162 · DeepTMHMM 162/162 · TOPCONS2 0/162 **(partial)** |
| [Enterobacteria phage P1](P1_Topology_Lab_Reference/P1_Topology_Atlas.html) | phage | NC_005856.1 | 110 | 8 | 9 | 0 | Phobius 110/110 · DeepTMHMM 110/110 · TOPCONS2 0/110 **(partial)** |
| [Enterobacteria phage Mu](Mu_Topology_Lab_Reference/Mu_Topology_Atlas.html) | phage | NC_000929.1 | 55 | 3 | 6 | 0 | Phobius 55/55 · DeepTMHMM 55/55 · TOPCONS2 0/55 **(partial)** |
| [Enterobacteria phage HK97](HK97_Topology_Lab_Reference/HK97_Topology_Atlas.html) | phage | NC_002167.1 | 61 | 7 | 4 | 0 | Phobius 61/61 · DeepTMHMM 61/61 · TOPCONS2 0/61 **(partial)** |
| [Salmonella phage P22](P22_Topology_Lab_Reference/P22_Topology_Atlas.html) | phage | NC_002371.2 | 72 | 10 | 7 | 0 | Phobius 72/72 · DeepTMHMM 72/72 · TOPCONS2 0/72 **(partial)** |
| [Enterobacteria phage PRD1](PRD1_Topology_Lab_Reference/PRD1_Topology_Atlas.html) | phage | NC_001421.2 | 31 | 13 | 10 | 0 | Phobius 31/31 · DeepTMHMM 31/31 · TOPCONS2 0/31 **(partial)** |
| [Pseudomonas phage phi6](phi6_Topology_Lab_Reference/phi6_Topology_Atlas.html) | phage | NC_003715.1, NC_003716.1, NC_003714.1 | 13 | 4 | 0 | 0 | Phobius 13/13 · DeepTMHMM 13/13 · TOPCONS2 0/13 **(partial)** |
| [Bacillus phage phi29](phi29_Topology_Lab_Reference/phi29_Topology_Atlas.html) | phage | NC_011048.1 | 27 | 2 | 4 | 0 | Phobius 27/27 · DeepTMHMM 27/27 · TOPCONS2 0/27 **(partial)** |
| [Bacillus phage SPP1](SPP1_Topology_Lab_Reference/SPP1_Topology_Atlas.html) | phage | NC_004166.2 | 97 | 20 | 8 | 1 | Phobius 97/97 · DeepTMHMM 97/97 · TOPCONS2 0/97 **(partial)** |
| [Escherichia coli K-12 MG1655](Ecoli_K12_Topology_Lab_Reference/Ecoli_K12_Topology_Atlas.html) | host | NC_000913.3 | 4,300 | 1,003 | 834 | 41 | Phobius 4,297/4,297 · DeepTMHMM 2,000/4,297 · TOPCONS2 0/4,293 **(partial)** |
| [Salmonella enterica serovar Typhimurium LT2](Salmonella_LT2_Topology_Lab_Reference/Salmonella_LT2_Topology_Atlas.html) | host | NC_003197.2, NC_003277.2 | 4,554 | 1,018 | 810 | 0 | Phobius 4,551/4,551 · DeepTMHMM 0/4,551 · TOPCONS2 0/4,551 **(partial)** |
| [Bacillus subtilis 168](Bsubtilis_168_Topology_Lab_Reference/Bsubtilis_168_Topology_Atlas.html) | host | NC_000964.3 | 4,237 | 1,043 | 549 | 0 | Phobius 4,237/4,237 · DeepTMHMM 0/4,237 · TOPCONS2 0/4,237 **(partial)** |

**Figures** are publication-ready SVG/PNG produced by a collision-free label engine and audited in a real browser for overlapping or clipped text and crossing lines. **Re-run:** one-click Phobius and DeepTMHMM submissions per protein from the atlas; pipeline re-runs via the GitHub Actions workflow `topology-rerun.yml` or `python3 scripts/rerun.py`. **Pipeline:** `scripts/` (fetch → inventory → predictors → normalize → atlas → browser audit → validation). Add an organism by adding an entry to `scripts/config.py`.
