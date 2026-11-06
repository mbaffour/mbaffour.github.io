# Bacillus subtilis 168 — membrane topology & charge lab reference

Open **`Bsubtilis_168_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

> **Partial:** at least one predictor has not yet finished every eligible protein (see coverage). Missing results are shown as pending, never substituted. Resume with the commands below.

## Source
- RefSeq **NC_000964.3**: "Bacillus subtilis subsp. subtilis str. 168 complete genome", 4,215,606 nt, circular; NCBI record updated 2021/02/12; taxid 224308.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json` (GenBank stored gzip-compressed; checksums of both forms recorded).
- Scope: all **4,237** CDS features with a `/translation` (4,237 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Bacterial proteome. Inside/outside are the models' cytoplasmic/non-cytoplasmic sides; the models do not say which membrane a protein is in. Gram-positive: a single cytoplasmic membrane; 'outside' is the non-cytoplasmic side.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 0 / 4,237 ({'pending': 4237}) | — |
| DeepTMHMM | 0 / 4,237 ({'pending': 4237}) | — |
| TOPCONS2 | 0 / 4,237 ({'pending': 4237}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Plots not requested at proteome scale.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (not recorded); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: —. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 0 records.

## Summary
- 0 proteins with ≥1 predicted membrane span (any main method); 0 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 0 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org Bsubtilis_168 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `Bsubtilis_168`; or locally `python3 scripts/rerun.py --org Bsubtilis_168`.

## Validation
`verification.json`: 21 pass, 0 fail, 3 pending of 24 checks. Pending: Phobius coverage of eligible proteins: 0/4237 eligible (4237 in inventory); {'pending': 4237}; DeepTMHMM coverage of eligible proteins: 0/4237 eligible (4237 in inventory); {'pending': 4237}; TOPCONS2 coverage of eligible proteins: 0/4237 eligible (4237 in inventory); {'pending': 4237}.
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org Bsubtilis_168     # skips files already present
python3 scripts/02_inventory.py --org Bsubtilis_168
python3 scripts/03_run_phobius.py --org Bsubtilis_168      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org Bsubtilis_168    # resumable
python3 scripts/04_run_topcons.py --org Bsubtilis_168      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org Bsubtilis_168 && python3 scripts/08_build_atlas.py --org Bsubtilis_168
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org Bsubtilis_168
python3 scripts/rerun.py --org Bsubtilis_168 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record. Large TOPCONS2 result zips (mostly per-sequence images) are not stored; their checksums/URLs are recorded and every text output needed to reproduce the predictions is archived unmodified in `raw/TOPCONS2/*.text.tar.xz`.
