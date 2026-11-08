# Escherichia phage phiX174 — membrane topology & charge lab reference

Open **`phiX174_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_001422.1**: "Escherichia phage phiX174, complete genome", 5,386 nt, circular; NCBI record updated 2023/01/11; taxid 2886930.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **11** CDS features with a `/translation` (11 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Escherichia coli. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 11 / 11 ({'complete': 11}) | — |
| DeepTMHMM | 11 / 11 ({'complete': 11}) | — |
| TOPCONS2 | 11 / 11 ({'complete': 11}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: cached: 9, newrun: 2. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 5 records.

## Summary
- 0 proteins with ≥1 predicted membrane span (any main method); 4 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 4 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| gene A | `phiX174p01` | DNA replication initiation | 513 | none | none | none | — |
| gene A* | `phiX174p02` | DNA replication initiation | 341 | none | none | none | — |
| gene B | `phiX174p03` | head morphogenesis | 120 | none | SP 1–59 | none | signal_peptide |
| gene K | `phiX174p04` | K | 56 | none | none | none | — |
| gene C | `phiX174p05` | terminase | 86 | none | none | none | — |
| gene D | `phiX174p07` | head morphogenesis | 152 | none | none | none | — |
| gene E | `phiX174p08` | endolysin | 91 | SP 1–33 | SP 1–26 | SP 1–30 | signal_peptide_boundary |
| gene J | `phiX174p09` | DNA condensation | 38 | none | none | none | — |
| gene F | `phiX174p06` | major head protein | 427 | none | none | none | — |
| gene G | `phiX174p10` | major spike protein | 175 | none | SP 1–30 | none | signal_peptide |
| gene H | `phiX174p11` | pilot protein for DNA ejection | 328 | SP 1–19 | none | SP 1–21 | signal_peptide, signal_peptide_boundary |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org phiX174 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `phiX174`; or locally `python3 scripts/rerun.py --org phiX174`.

## Validation
`verification.json`: 25 pass, 0 fail, 0 pending of 25 checks. 
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org phiX174     # skips files already present
python3 scripts/02_inventory.py --org phiX174
python3 scripts/03_run_phobius.py --org phiX174      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org phiX174    # resumable
python3 scripts/04_run_topcons.py --org phiX174      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org phiX174 && python3 scripts/08_build_atlas.py --org phiX174
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org phiX174
python3 scripts/rerun.py --org phiX174 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
