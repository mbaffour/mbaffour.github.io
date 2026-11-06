# Bacillus phage phi29 — membrane topology & charge lab reference

Open **`phi29_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

> **Partial:** at least one predictor has not yet finished every eligible protein (see coverage). Missing results are shown as pending, never substituted. Resume with the commands below.

## Source
- RefSeq **NC_011048.1**: "Bacillus phage phi29, complete genome", 19,282 nt, linear; NCBI record updated 2023/01/11; taxid 2884424.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **27** CDS features with a `/translation` (27 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Bacillus subtilis. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 27 / 27 ({'complete': 27}) | — |
| DeepTMHMM | 0 / 27 ({'pending': 27}) | — |
| TOPCONS2 | 0 / 27 ({'pending': 27}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (not recorded); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: —. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 1 records.

## Summary
- 1 proteins with ≥1 predicted membrane span (any main method); 2 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 0 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| 0.2 | `phi29_gp0.2` | hypothetical protein | 31 | none | pending | pending | — |
| 0.4 | `phi29_gp0.4` | hypothetical protein | 47 | none | pending | pending | — |
| 0.6 | `phi29_gp0.6` | hypothetical protein | 58 | none | pending | pending | — |
| 0.8 | `phi29_gp0.8` | hypothetical protein | 56 | none | pending | pending | — |
| 1 | `phi29_gp1` | hypothetical protein | 86 | none | pending | pending | — |
| 2 | `phi29_gp2` | DNA polymerase | 572 | none | pending | pending | — |
| 3 | `phi29_gp3` | DNA terminal protein | 266 | none | pending | pending | — |
| 4 | `phi29_gp4` | late transcriptional activator | 125 | none | pending | pending | — |
| 5 | `phi29_gp5` | single strand DNA binding protein | 124 | none | pending | pending | — |
| 5.5 | `phi29_gp5.5` | hypothetical protein | 66 | SP 1–21 | pending | pending | — |
| 6 | `phi29_gp6` | dsDNA binding protein | 104 | none | pending | pending | — |
| 7 | `phi29_gp7` | head scaffolding protein | 98 | none | pending | pending | — |
| 8 | `phi29_gp8` | major head protein | 448 | none | pending | pending | — |
| 8.5 | `phi29_gp8.5` | head fiber protein | 280 | none | pending | pending | — |
| 9 | `phi29_gp9` | tail protein | 599 | none | pending | pending | — |
| 10 | `phi29_gp10` | upper collar connector | 309 | none | pending | pending | — |
| 11 | `phi29_gp11` | adaptor Ad4 | 293 | none | pending | pending | — |
| 12 | `phi29_gp12` | pre-neck appendage protein | 854 | none | pending | pending | — |
| 13 | `phi29_gp13` | tail-type lysozyme domain-containing protein | 364 | none | pending | pending | — |
| 14 | `phi29_gp14` | holin family protein | 131 | TM 20–40, TM 61–79, TM 85–106 | pending | pending | — |
| 15 | `phi29_gp15` | endolysin | 258 | none | pending | pending | — |
| 16 | `phi29_gp16` | terminase | 332 | none | pending | pending | — |
| 16.6 | `phi29_gp16.6` | YgiT-type zinc finger protein | 54 | none | pending | pending | — |
| 16.7 | `phi29_gp16.7` | GP16.7-like replication protein | 130 | SP 1–20 | pending | pending | — |
| 16.8 | `phi29_gp16.8` | hypothetical early protein | 105 | none | pending | pending | — |
| 16.9 | `phi29_gp16.9` | hypothetical early protein | 108 | none | pending | pending | — |
| 17 | `phi29_gp17` | replication protein | 166 | none | pending | pending | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org phi29 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `phi29`; or locally `python3 scripts/rerun.py --org phi29`.

## Validation
`verification.json`: 23 pass, 0 fail, 2 pending of 25 checks. Pending: DeepTMHMM coverage of eligible proteins: 0/27 eligible (27 in inventory); {'pending': 27}; TOPCONS2 coverage of eligible proteins: 0/27 eligible (27 in inventory); {'pending': 27}.
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org phi29     # skips files already present
python3 scripts/02_inventory.py --org phi29
python3 scripts/03_run_phobius.py --org phi29      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org phi29    # resumable
python3 scripts/04_run_topcons.py --org phi29      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org phi29 && python3 scripts/08_build_atlas.py --org phi29
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org phi29
python3 scripts/rerun.py --org phi29 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
