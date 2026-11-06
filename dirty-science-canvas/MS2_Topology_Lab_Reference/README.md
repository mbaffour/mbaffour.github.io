# Escherichia phage MS2 — membrane topology & charge lab reference

Open **`MS2_Topology_Atlas.html`** in any modern browser. It is a single self-contained file that works offline: data, figure code and server plots are all embedded. Links to papers need internet access.

All topology calls here are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_001417.2**, "phage MS2 genome", 3569 nt, linear. The NCBI record was last updated 2023/01/07, taxid 12022.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC). URLs and SHA-256 checksums are in `inputs/provenance.json`:
  - GenBank record: `inputs/NC_001417.2.gb`
  - NCBI CDS translations: `inputs/NC_001417.2.cds_aa.fasta`
  - Genome FASTA: `inputs/NC_001417.2.fna`
- Annotation preference: the current RefSeq annotation is used exactly as published. **Scope:** all 4 CDS features with a `/translation` (4 CDS features in total; 0 pseudogenes or untranslated CDSs).
- Every translation was cross-checked in two ways:
  - Against NCBI's CDS FASTA.
  - Against an independent translation from the coordinates (strand, joins, `codon_start`, genetic code 11). Both agree for all proteins.
- Flags such as `joined_location_spans_circular_origin` mark CDSs that wrap the circular genome origin. They are informational. No sequence was trimmed, padded or edited.
- Host context: Escherichia coli F+ strains (host); membrane predictions refer to a generic membrane context, not a specific host membrane.

## Methods run (all 4 proteins)
| Method | Coverage | Submission |
|---|---|---|
| Phobius | 4/4 | batch 1: job `n/a`, complete, submitted 2026-11-06T18:50:21+00:00; batch 1 (nog): job `n/a`, complete, submitted 2026-11-06T18:49:36+00:00; batch 1 (short): job `n/a`, complete, submitted 2026-11-06T18:49:38+00:00 |
| DeepTMHMM | 4/4 | batch 1: job `n/a`, complete, submitted 2026-11-06T18:50 (approx., from CLI log; first log line 18:51:39) |
| TOPCONS2 | 4/4 | batch 1: job `rst_mg63wokt`, complete, submitted 2026-11-06T18:53:24+00:00 |

- **Phobius**: phobius.sbc.su.se JSON API (`/api/predict`, with `plot: true`). The plain-text long/short formats and the web-form outputs are kept in `raw/Phobius/` as cross-checks. Signal-peptide boundaries were verified against the reported cleavage site, and the `C` cleavage marker is never counted as a signal-peptide residue.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM, version(s): not recorded. Raw `predicted_topologies.3line`, `TMRs.gff3` and `deeptmhmm_results.md` are in `raw/DeepTMHMM/batch1/results/`.
- **TOPCONS2**: topcons.net WSDL API, with OCTOPUS, Philius, PolyPhobius, SCAMPI and SPOCTOPUS outputs retained.
  - TOPCONS2 served cached results for identical sequences: cached: 4. The original computation dates are 2023-12-06.
  - Per-protein generation dates and cache status are in `data.json`.
  - The original result zip and an extracted copy are in `raw/TOPCONS2/`.
  - The components feed the TOPCONS2 consensus; they are not independent votes in addition to it.

## Per-protein summary (main methods)
| Gene | Locus tag | Accession | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|---|
| mat | `MS2g1` | YP_009640124.1 | head maturation protease | 393 | none | none | none | — |
| cp | `MS2g2` | YP_009640125.1 | head protein | 130 | none | none | none | — |
| lys | `MS2g3` | YP_009640126.1 | hypothetical protein | 75 | TM 38–60 | TM 40–49 | TM 37–57 | span_boundaries(max_shift=11) |
| rep | `MS2g4` | YP_009640127.1 | RNA replicase beta subunit | 545 | none | none | none | — |



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
`verification.json` records 42/42 passing checks (run time recorded in the file). They cover:
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
