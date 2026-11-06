# Escherichia phage phiX174 — membrane topology & charge lab reference

Open **`phiX174_Topology_Atlas.html`** in any modern browser. It is a single self-contained file that works offline: data, figure code and server plots are all embedded. Links to papers need internet access.

All topology calls here are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_001422.1**, "Escherichia phage phiX174, complete genome", 5386 nt, circular. The NCBI record was last updated 2023/01/11, taxid 2886930.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC). URLs and SHA-256 checksums are in `inputs/provenance.json`:
  - GenBank record: `inputs/NC_001422.1.gb`
  - NCBI CDS translations: `inputs/NC_001422.1.cds_aa.fasta`
  - Genome FASTA: `inputs/NC_001422.1.fna`
- Annotation preference: the current RefSeq annotation is used exactly as published. **Scope:** all 11 CDS features with a `/translation` (11 CDS features in total; 0 pseudogenes or untranslated CDSs).
- Every translation was cross-checked in two ways:
  - Against NCBI's CDS FASTA.
  - Against an independent translation from the coordinates (strand, joins, `codon_start`, genetic code 11). Both agree for all proteins.
- Flags such as `joined_location_spans_circular_origin` mark CDSs that wrap the circular genome origin. They are informational. No sequence was trimmed, padded or edited. Curator gene letters (`curator_alias`) are added only as search aliases; RefSeq NC_001422.1 has no `/gene` qualifiers.
- Host context: Escherichia coli (host); membrane predictions refer to a generic membrane context, not a specific host membrane.

## Methods run (all 11 proteins)
| Method | Coverage | Submission |
|---|---|---|
| Phobius | 11/11 | batch 1: job `n/a`, complete, submitted 2026-11-06T18:50:04+00:00; batch 1 (nog): job `n/a`, complete, submitted 2026-11-06T18:49:24+00:00; batch 1 (short): job `n/a`, complete, submitted 2026-11-06T18:49:27+00:00 |
| DeepTMHMM | 11/11 | batch 1: job `b959235c-cdf3-47d7-8808-213d675aca27`, complete, submitted 2026-11-06T18:56:03+00:00 |
| TOPCONS2 | 11/11 | batch 1: job `rst_4a1e4x74`, complete, submitted 2026-11-06T18:53:23+00:00 |

- **Phobius**: phobius.sbc.su.se JSON API (`/api/predict`, with `plot: true`). The plain-text long/short formats and the web-form outputs are kept in `raw/Phobius/` as cross-checks. Signal-peptide boundaries were verified against the reported cleavage site, and the `C` cleavage marker is never counted as a signal-peptide residue.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM, version(s): DTU/DeepTMHMM:1.0.57. Raw `predicted_topologies.3line`, `TMRs.gff3` and `deeptmhmm_results.md` are in `raw/DeepTMHMM/batch1/results/`.
- **TOPCONS2**: topcons.net WSDL API, with OCTOPUS, Philius, PolyPhobius, SCAMPI and SPOCTOPUS outputs retained.
  - TOPCONS2 served cached results for identical sequences: cached: 9, newrun: 2. The original computation dates are 2023-12-06, 2023-12-07, 2026-11-06.
  - Per-protein generation dates and cache status are in `data.json`.
  - The original result zip and an extracted copy are in `raw/TOPCONS2/`.
  - The components feed the TOPCONS2 consensus; they are not independent votes in addition to it.

## Per-protein summary (main methods)
| Gene | Locus tag | Accession | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|---|
| gene A | `phiX174p01` | NP_040703.1 | DNA replication initiation | 513 | none | none | none | — |
| gene A* | `phiX174p02` | NP_040704.1 | DNA replication initiation | 341 | none | none | none | — |
| gene B | `phiX174p03` | NP_040705.1 | head morphogenesis | 120 | none | SP 1–59 | none | signal_peptide |
| gene K | `phiX174p04` | NP_040706.1 | K | 56 | none | none | none | — |
| gene C | `phiX174p05` | NP_040707.1 | terminase | 86 | none | none | none | — |
| gene D | `phiX174p07` | NP_040708.1 | head morphogenesis | 152 | none | none | none | — |
| gene E | `phiX174p08` | NP_040709.1 | endolysin | 91 | SP 1–33 | SP 1–26 | SP 1–30 | signal_peptide_boundary |
| gene J | `phiX174p09` | NP_040710.1 | DNA condensation | 38 | none | none | none | — |
| gene F | `phiX174p06` | NP_040711.1 | major head protein | 427 | none | none | none | — |
| gene G | `phiX174p10` | NP_040712.1 | major spike protein | 175 | none | SP 1–30 | none | signal_peptide |
| gene H | `phiX174p11` | NP_040713.1 | pilot protein for DNA ejection | 328 | SP 1–19 | none | SP 1–21 | signal_peptide, signal_peptide_boundary |



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
`verification.json` records 51/51 passing checks (run time recorded in the file). They cover:
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
