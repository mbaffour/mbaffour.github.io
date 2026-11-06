# Enterobacteria phage M13 — membrane topology & charge lab reference

Open **`M13_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_003287.2**: "Enterobacteria phage M13, complete genome", 6,407 nt, circular; NCBI record updated 2018/08/13; taxid 1977402.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **10** CDS features with a `/translation` (10 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Escherichia coli (F+). Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 10 / 10 ({'complete': 10}) | — |
| DeepTMHMM | 10 / 10 ({'complete': 10}) | — |
| TOPCONS2 | 10 / 10 ({'complete': 10}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: cached: 8, newrun: 2. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 5 records.

## Summary
- 7 proteins with ≥1 predicted membrane span (any main method); 4 with a predicted signal peptide; 1 with DeepTMHMM β-type states; 5 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Comparison with experimentally known signal-peptide ends (informational)
- `M13|M13p06`: experimental end 23 (pVIII precursor (procoat); mature coat begins at residue 24 (AEGDDP...), e.g. Kuhn & Wickner 1985 J Biol Chem 260:15914). Predicted: Phobius 23, DeepTMHMM 23, TOPCONS2 23.
- `M13|M13p07`: experimental end 18 (pIII precursor; mature protein begins at residue 19 (AETVES...), e.g. van Wezenbeek et al. 1980 Gene 11:129). Predicted: Phobius 18, DeepTMHMM 18, TOPCONS2 21.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| II | `M13p01` | replication initiation protein | 410 | none | none | none | — |
| X | `M13p02` | gene X product | 111 | none | none | none | — |
| V | `M13p03` | helix destabilising protein | 87 | none | none | none | — |
| VII | `M13p04` | minor coat protein | 33 | TM 13–31 | TM 10–30 | TM 12–32 | — |
| IX | `M13p05` | minor coat protein | 32 | SP 1–18 | SP 1–23 | TM 2–22 | span_count, signal_peptide, signal_peptide_boundary |
| VIII | `M13p06` | major coat protein | 73 | SP 1–23, TM 47–65 | SP 1–23, TM 45–65 | SP 1–23, TM 45–65 | — |
| III | `M13p07` | attachment protein | 424 | SP 1–18, TM 394–419 | SP 1–18, TM 398–419 | SP 1–21, TM 397–417 | span_boundaries(max_shift=4), signal_peptide_boundary |
| VI | `M13p08` | minor coat protein | 112 | TM 6–29, TM 36–59, TM 79–98 | TM 36–47, TM 81–98 | TM 7–27, TM 36–56, TM 80–100 | span_count, n_terminal_side |
| I | `M13p09` | assembly protein | 348 | TM 251–270 | TM 253–262 | none | span_count |
| IV | `M13p10` | phage assembly protein | 426 | SP 1–21 | SP 1–21, β 201–205, β 358–365, β 374–378, β 414–418 | SP 1–21 | span_count |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org M13 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `M13`; or locally `python3 scripts/rerun.py --org M13`.

## Validation
`verification.json`: 25 pass, 0 fail, 0 pending of 25 checks. 
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org M13     # skips files already present
python3 scripts/02_inventory.py --org M13
python3 scripts/03_run_phobius.py --org M13      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org M13    # resumable
python3 scripts/04_run_topcons.py --org M13      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org M13 && python3 scripts/08_build_atlas.py --org M13
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org M13
python3 scripts/rerun.py --org M13 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
