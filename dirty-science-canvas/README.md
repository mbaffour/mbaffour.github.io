# Dirty Science Canvas

Protein membrane-topology and charge atlases for small bacteriophage proteomes. Every annotated protein translation was run through **Phobius**, **DeepTMHMM** and **TOPCONS2** (including its OCTOPUS, Philius, PolyPhobius, SCAMPI and SPOCTOPUS components). The results were normalized with provenance, validated, and rendered into self-contained offline HTML atlases.

All calls are computational predictions, not experimental evidence.

| Phage | RefSeq | Proteins | ≥1 span (any main method) | Signal peptide (any main method) | Main-method disagreement | Coverage | Package |
|---|---|---|---|---|---|---|---|
| [Escherichia phage phiX174](phiX174_Topology_Lab_Reference/phiX174_Topology_Atlas.html) | NC_001422.1 | 11 | 0 | 4 | 4 | Phobius 11/11 · DeepTMHMM 11/11 · TOPCONS2 11/11 | [zip](packages/phiX174_Topology_Lab_Reference.zip) |
| [Enterobacteria phage M13](M13_Topology_Lab_Reference/M13_Topology_Atlas.html) | NC_003287.2 | 10 | 7 | 4 | 5 | Phobius 10/10 · DeepTMHMM 10/10 · TOPCONS2 10/10 | [zip](packages/M13_Topology_Lab_Reference.zip) |
| [Escherichia phage MS2](MS2_Topology_Lab_Reference/MS2_Topology_Atlas.html) | NC_001417.2 | 4 | 1 | 0 | 1 | Phobius 4/4 · DeepTMHMM 4/4 · TOPCONS2 4/4 | [zip](packages/MS2_Topology_Lab_Reference.zip) |

Start at `index.html`, or open a phage's `*_Topology_Atlas.html` directly; each works offline. Each phage folder's `README.md` documents its sources, jobs, coverage, conventions, validation and how to rebuild it.

`scripts/` holds the whole pipeline (fetch → inventory → predictors → normalize → atlas → figures → browser check → validation/package). `scripts/config.py` lists the phages, so adding a phage means adding an entry there and rerunning the pipeline.
