# Pseudomonas phage phi6 — membrane topology & charge lab reference

Open **`phi6_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_003715.1**: "Pseudomonas phage phi-6 segment L, complete sequence", 6,374 nt, linear; NCBI record updated 2023/01/11; taxid 2928686.
- RefSeq **NC_003716.1**: "Pseudomonas phage phi-6 segment M, complete sequence", 4,063 nt, linear; NCBI record updated 2023/01/11; taxid 2928686.
- RefSeq **NC_003714.1**: "Pseudomonas phage phi-6 segment S, complete sequence", 2,948 nt, linear; NCBI record updated 2018/08/13; taxid 2928686.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **13** CDS features with a `/translation` (13 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Pseudomonas syringae pv. phaseolicola. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions. phi6 is enveloped and its genome has three segments (L, M, S); these predictions do not assign any protein to the virion envelope.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 13 / 13 ({'complete': 13}) | — |
| DeepTMHMM | 13 / 13 ({'complete': 13}) | — |
| TOPCONS2 | 13 / 13 ({'complete': 13}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: cached: 12, newrun: 1. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 3 records.

## Summary
- 4 proteins with ≥1 predicted membrane span (any main method); 1 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 5 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| — | `phi-6L_1` | prohead | 161 | none | none | none | — |
| pol | `phi-6L_2` | RNA polymerase | 665 | none | none | none | — |
| — | `phi-6L_3` | terminase | 332 | TM 170–186, TM 198–220, TM 240–258 | none | none | span_count |
| — | `phi-6L_4` | prohead | 769 | none | none | none | — |
| — | `phi-6M_1` | membrane protein | 42 | TM 20–40 | TM 25–40 | TM 21–41 | n_terminal_side |
| — | `phi-6M_2` | P6 protein | 168 | TM 29–46, TM 52–76, TM 144–161 | TM 29–42, TM 143–152 | TM 28–48, TM 50–70, TM 91–111, TM 144–164 | span_count |
| — | `phi-6M_3` | P3 protein | 648 | none | none | none | — |
| — | `phi-6M_4` | P13 protein | 72 | none | none | none | — |
| — | `phi-6S_1` | hypothetical protein | 149 | none | none | SP 1–21 | signal_peptide |
| — | `phi-6S_2` | hypothetical protein | 195 | none | none | none | — |
| — | `phi-6S_3` | hypothetical protein | 90 | TM 53–72 | none | none | span_count |
| — | `phi-6S_4` | hypothetical protein | 220 | none | none | none | — |
| — | `phi-6S_5` | hypothetical protein | 212 | none | none | none | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org phi6 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `phi6`; or locally `python3 scripts/rerun.py --org phi6`.

## Validation
`verification.json`: 31 pass, 0 fail, 0 pending of 31 checks. 
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org phi6     # skips files already present
python3 scripts/02_inventory.py --org phi6
python3 scripts/03_run_phobius.py --org phi6      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org phi6    # resumable
python3 scripts/04_run_topcons.py --org phi6      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org phi6 && python3 scripts/08_build_atlas.py --org phi6
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org phi6
python3 scripts/rerun.py --org phi6 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
