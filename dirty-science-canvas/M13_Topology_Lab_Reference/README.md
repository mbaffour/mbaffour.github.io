# Enterobacteria phage M13 — membrane topology & charge lab reference

Open **`M13_Topology_Atlas.html`** in any modern browser. It is a single self-contained file that works offline: data, figure code and server plots are all embedded. Links to papers need internet access.

All topology calls here are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_003287.2**, "Enterobacteria phage M13, complete genome", 6407 nt, circular. The NCBI record was last updated 2018/08/13, taxid 1977402.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC). URLs and SHA-256 checksums are in `inputs/provenance.json`:
  - GenBank record: `inputs/NC_003287.2.gb`
  - NCBI CDS translations: `inputs/NC_003287.2.cds_aa.fasta`
  - Genome FASTA: `inputs/NC_003287.2.fna`
- Annotation preference: the current RefSeq annotation is used exactly as published. **Scope:** all 10 CDS features with a `/translation` (10 CDS features in total; 0 pseudogenes or untranslated CDSs).
- Every translation was cross-checked in two ways:
  - Against NCBI's CDS FASTA.
  - Against an independent translation from the coordinates (strand, joins, `codon_start`, genetic code 11). Both agree for all proteins.
- Flags such as `joined_location_spans_circular_origin` mark CDSs that wrap the circular genome origin. They are informational. No sequence was trimmed, padded or edited.
- Host context: Escherichia coli F+ strains (host); membrane predictions refer to a generic membrane context, not a specific host membrane.

## Methods run (all 10 proteins)
| Method | Coverage | Submission |
|---|---|---|
| Phobius | 10/10 | batch 1: job `n/a`, complete, submitted 2026-11-06T18:50:13+00:00; batch 1 (nog): job `n/a`, complete, submitted 2026-11-06T18:49:30+00:00; batch 1 (short): job `n/a`, complete, submitted 2026-11-06T18:49:33+00:00 |
| DeepTMHMM | 10/10 | batch 1: job `72bd5cd9-c6c2-4dbe-9cac-cf943f0bda45`, complete, submitted 2026-11-06T18:56:59+00:00 |
| TOPCONS2 | 10/10 | batch 1: job `rst_bl4gz7ok`, complete, submitted 2026-11-06T18:53:24+00:00 |

- **Phobius**: phobius.sbc.su.se JSON API (`/api/predict`, with `plot: true`). The plain-text long/short formats and the web-form outputs are kept in `raw/Phobius/` as cross-checks. Signal-peptide boundaries were verified against the reported cleavage site, and the `C` cleavage marker is never counted as a signal-peptide residue.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM, version(s): DTU/DeepTMHMM:1.0.57. Raw `predicted_topologies.3line`, `TMRs.gff3` and `deeptmhmm_results.md` are in `raw/DeepTMHMM/batch1/results/`.
- **TOPCONS2**: topcons.net WSDL API, with OCTOPUS, Philius, PolyPhobius, SCAMPI and SPOCTOPUS outputs retained.
  - TOPCONS2 served cached results for identical sequences: cached: 8, newrun: 2. The original computation dates are 2023-12-06, 2026-11-06.
  - Per-protein generation dates and cache status are in `data.json`.
  - The original result zip and an extracted copy are in `raw/TOPCONS2/`.
  - The components feed the TOPCONS2 consensus; they are not independent votes in addition to it.

## Per-protein summary (main methods)
| Gene | Locus tag | Accession | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|---|
| II | `M13p01` | NP_510885.1 | replication initiation protein | 410 | none | none | none | — |
| X | `M13p02` | NP_510886.1 | gene X product | 111 | none | none | none | — |
| V | `M13p03` | NP_510887.1 | helix destabilising protein | 87 | none | none | none | — |
| VII | `M13p04` | NP_510888.1 | minor coat protein | 33 | TM 13–31 | TM 10–30 | TM 12–32 | — |
| IX | `M13p05` | NP_510889.1 | minor coat protein | 32 | SP 1–18 | SP 1–23 | TM 2–22 | span_count, signal_peptide, signal_peptide_boundary |
| VIII | `M13p06` | NP_510890.1 | major coat protein | 73 | SP 1–23, TM 47–65 | SP 1–23, TM 45–65 | SP 1–23, TM 45–65 | — |
| III | `M13p07` | NP_510891.1 | attachment protein | 424 | SP 1–18, TM 394–419 | SP 1–18, TM 398–419 | SP 1–21, TM 397–417 | span_boundaries(max_shift=4), signal_peptide_boundary |
| VI | `M13p08` | NP_510892.1 | minor coat protein | 112 | TM 6–29, TM 36–59, TM 79–98 | TM 36–47, TM 81–98 | TM 7–27, TM 36–56, TM 80–100 | span_count, n_terminal_side |
| I | `M13p09` | NP_510893.1 | assembly protein | 348 | TM 251–270 | TM 253–262 | none | span_count |
| IV | `M13p10` | NP_510894.1 | phage assembly protein | 426 | SP 1–21 | SP 1–21, β 201–205, β 358–365, β 374–378, β 414–418 | SP 1–21 | span_count |

### β-type predictions
- `M13|M13p10` — DeepTMHMM class **BETA**: periplasm (P), extracellular (O) and β-strand (B) segments, shown as a linear map rather than a helical cartoon.

### Comparison with experimentally known signal-peptide ends (informational)
- `M13|M13p06`: experimentally the signal peptide ends at residue 23 (pVIII precursor (procoat) 73 aa; mature coat begins at residue 24 (AEGDDP...) — e.g. Kuhn & Wickner 1985 J Biol Chem 260:15914). Predicted ends: Phobius 23, DeepTMHMM 23, TOPCONS2 23.
- `M13|M13p07`: experimentally the signal peptide ends at residue 18 (pIII precursor; mature protein begins at residue 19 (AETVES...) — e.g. van Wezenbeek et al. 1980 Gene 11:129). Predicted ends: Phobius 18, DeepTMHMM 18, TOPCONS2 21.

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation. Signal peptides keep precursor numbering.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Each method's native label strings are kept alongside (`native_labels`).
- Inside/outside labels on proteins with no predicted span do not establish localization.
- For phage proteins, no specific host membrane is assigned, and none of this predicts a viral envelope.
- Charge classes (K/R, D/E, variable H, declared hydrophobic/aromatic group) are approximate side-chain categories near neutral pH. They are not measured charges, net charge, pI or electrostatics.
- Disagreements between methods are flagged, never resolved into a consensus.

## Figures
The atlas draws four views for each protein:
- **A**: presentation orientation, with residue-proportional horizontal scale.
- **B**: full-length sequence and charge map. It shows every residue by default; an optional window is available.
- **C**: switchable residue-bead cartoon. Long loops are abbreviated with explicit omitted ranges.
- **D**: method-comparison tracks.

Every figure has buttons for SVG, PNG (2×/4×; PNG is automatically down-scaled when it would exceed browser canvas limits), copy-image (falls back to download) and copy-caption. A pre-rendered SVG library is in `figures/`, with 2× PNGs of view A for proteins with a predicted span or signal peptide.

## Files
`data.json` (normalized, complete) · `protein_inventory.csv` · `topology_summary.csv` · `inventory.json` · `pseudogene_inventory.json` · `inputs/` · `raw/` · `figures/` · `verification.json` + `verification_browser.json` · `SHA256SUMS.txt`. The zip package in `../packages/` also contains `scripts/`.

## Validation
`verification.json` records 53/53 passing checks (run time recorded in the file). They cover:
- input checksums and CDS reconciliation;
- submitted-FASTA identity per batch and raw-output checksums;
- label length, contiguity and alphabet for every prediction;
- Phobius signal-peptide boundaries, and β segments against DeepTMHMM's GFF;
- that the atlas embeds the current data and contains no other organism's names;
- a headless Chromium pass (153.0.8010.12, file://, offline) over every protein. It confirms that each residue's identity, number and band state is correct and that bead cartoons account for every residue exactly once. It also checks bead overlap, search, filters, component toggles, windowing, SVG/PNG export, and the absence of horizontal overflow at phone width.

Clipboard copy was not exercised headlessly.

## Rebuild / resume
From the project root (`dirty-science-canvas/`), with Python 3 + `biopython requests suds pybiolib` and Node + Playwright:
```
python3 scripts/01_fetch_inputs.py        # skips files already present
python3 scripts/02_inventory.py
python3 scripts/03b_run_phobius_api.py    # resumable; skips complete batches
python3 scripts/04_topcons_submit.py      # never resubmits a batch that has a job ID
python3 scripts/05_topcons_collect.py     # poll + download; exit code 2 while pending
python3 scripts/07_run_deeptmhmm.py       # resumable
python3 scripts/06_normalize.py && python3 scripts/08_build_atlas.py
node scripts/10_export_figures.js && node scripts/09_browser_check.js logs/browser_check.json
python3 scripts/11_validate_package.py && python3 scripts/12_write_readmes.py
```
Web-job links (TOPCONS2 result URLs, BioLib job IDs) may expire; the raw outputs here are the durable record.
