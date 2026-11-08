# Enterobacteria phage PRD1 — membrane topology & charge lab reference

Open **`PRD1_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

> **Partial:** at least one predictor has not yet finished every eligible protein (see coverage). Missing results are shown as pending, never substituted. Resume with the commands below.

## Source
- RefSeq **NC_001421.2**: "Enterobacteria phage PRD1, complete genome", 14,927 nt, linear; NCBI record updated 2023/01/07; taxid 10658.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **31** CDS features with a `/translation` (31 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Gram-negative bacteria carrying IncP/N/W plasmids (e.g. E. coli, Salmonella). Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions. PRD1 has an internal virion lipid membrane; these predictions do not assign any protein to it.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 31 / 31 ({'complete': 31}) | — |
| DeepTMHMM | 31 / 31 ({'complete': 31}) | — |
| TOPCONS2 | 0 / 31 ({'pending': 31}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: —. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 3 records.

## Summary
- 13 proteins with ≥1 predicted membrane span (any main method); 10 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 15 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| XIII | `PRD1_01` | terminal protein | 259 | none | none | pending | — |
| I | `PRD1_02` | DNA polymerase | 553 | none | none | pending | — |
| XV | `PRD1_03` | endolysin | 149 | none | none | pending | — |
| II | `PRD1_04` | receptor binding | 591 | none | none | pending | — |
| XXXI | `PRD1_05` | major spike protein | 126 | none | none | pending | — |
| V | `PRD1_06` | major spike protein | 340 | none | none | pending | — |
| XVII | `PRD1_07` | assembly | 86 | none | none | pending | — |
| XXXIII | `PRD1_23` | assembly | 68 | none | none | pending | — |
| VI | `PRD1_08` | minor head protein | 166 | none | none | pending | — |
| X | `PRD1_24` | assembly | 203 | TM 136–156 | none | pending | span_count |
| IX | `PRD1_09` | terminase large subunit | 227 | none | none | pending | — |
| ORFi | `PRD1_10` | hypothetical protein | 42 | TM 12–34 | TM 13–33 | pending | — |
| XX | `PRD1_11` | DNA packaging | 42 | TM 12–31 | SP 1–11, TM 13–31 | pending | signal_peptide |
| III | `PRD1_12` | minor head protein | 395 | none | none | pending | — |
| XXII | `PRD1_14` | DNA packaging | 47 | TM 20–38 | TM 21–42 | pending | n_terminal_side |
| ORFx | `PRD1_25` | hypothetical protein | 27 | SP 1–17 | SP 1–20 | pending | signal_peptide_boundary |
| ORFl | `PRD1_26` | hypothetical protein | 40 | SP 1–21 | SP 1–21 | pending | — |
| XVIII | `PRD1_15` | DNA delivery | 90 | SP 1–18, TM 38–54, TM 61–80 | TM 5–16, TM 35–52, TM 63–74 | pending | span_count, signal_peptide |
| XXXII | `PRD1_27` | membrane DNA delivery | 54 | TM 6–25 | TM 8–25 | pending | n_terminal_side |
| XXXIV | `PRD1_16` | membrane DNA delivery | 68 | TM 6–26 | SP 1–26 | pending | span_count, signal_peptide |
| XXX | `PRD1_17` | minor head protein | 84 | none | none | pending | — |
| ORFq | `PRD1_28` | hypothetical protein | 36 | SP 1–26 | SP 1–17 | pending | signal_peptide_boundary |
| XI | `PRD1_18` | DNA delivery | 207 | TM 12–28 | SP 1–26 | pending | span_count, signal_peptide |
| XVI | `PRD1_19` | hypothetical protein | 117 | TM 6–23 | SP 1–24 | pending | span_count, signal_peptide |
| VII | `PRD1_20` | transglycosylase | 265 | TM 217–239 | none | pending | span_count |
| XIV | `PRD1_30` | transglycosylase | 150 | TM 102–124 | TM 102–111 | pending | n_terminal_side |
| XXXV | `PRD1_31` | holin | 117 | TM 7–26, TM 38–61, TM 67–87 | TM 11–26, TM 40–60, TM 67–87 | pending | span_boundaries(max_shift=4) |
| ORFu | `PRD1_32` | Rz-like spanin | 120 | SP 1–31 | TM 12–30 | pending | span_count, signal_peptide |
| ORFv | `PRD1_33` | Rz-like spanin | 90 | SP 1–21 | SP 1–17 | pending | signal_peptide_boundary |
| XIX | `PRD1_21` | single strand DNA binding protein | 94 | none | none | pending | — |
| XII | `PRD1_22` | single strand DNA binding protein | 160 | none | none | pending | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org PRD1 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `PRD1`; or locally `python3 scripts/rerun.py --org PRD1`.

## Validation
`verification.json`: 24 pass, 0 fail, 2 pending of 26 checks. Pending: all batches complete: TOPCONS2/b001.job.json:submitted; TOPCONS2 coverage of eligible proteins: 0/31 eligible (31 in inventory); {'pending': 31}.
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org PRD1     # skips files already present
python3 scripts/02_inventory.py --org PRD1
python3 scripts/03_run_phobius.py --org PRD1      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org PRD1    # resumable
python3 scripts/04_run_topcons.py --org PRD1      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org PRD1 && python3 scripts/08_build_atlas.py --org PRD1
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org PRD1
python3 scripts/rerun.py --org PRD1 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
