# Enterobacteria phage Mu — membrane topology & charge lab reference

Open **`Mu_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

> **Partial:** at least one predictor has not yet finished every eligible protein (see coverage). Missing results are shown as pending, never substituted. Resume with the commands below.

## Source
- RefSeq **NC_000929.1**: "Enterobacteria phage Mu, complete genome", 36,717 nt, linear; NCBI record updated 2023/01/11; taxid 2681603.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **55** CDS features with a `/translation` (55 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Escherichia coli. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 55 / 55 ({'complete': 55}) | — |
| DeepTMHMM | 55 / 55 ({'complete': 55}) | — |
| TOPCONS2 | 0 / 55 ({'pending': 55}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: —. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 2 records.

## Summary
- 3 proteins with ≥1 predicted membrane span (any main method); 6 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 7 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| — | `Mup01` | transcriptional repressor | 174 | none | none | pending | — |
| — | `Mup02` | transcriptional repressor | 75 | none | none | pending | — |
| — | `Mup03` | Mu transposase C-terminal domain-containing protein | 663 | none | none | pending | — |
| — | `Mup04` | DNA transposition protein | 312 | none | none | pending | — |
| — | `Mup05` | Kil protein for bacterial septation inhibition | 74 | none | none | pending | — |
| — | `Mup06` | hypothetical protein | 76 | none | none | pending | — |
| — | `Mup07` | hypothetical protein | 87 | none | none | pending | — |
| — | `Mup08` | hypothetical protein | 139 | none | none | pending | — |
| — | `Mup09` | transcriptional regulator, D5-like | 99 | none | none | pending | — |
| — | `Mup10` | host nuclease inhibitor | 174 | none | none | pending | — |
| — | `Mup11` | hypothetical protein | 176 | none | none | pending | — |
| — | `Mup12` | hypothetical protein | 176 | none | none | pending | — |
| — | `Mup13` | hypothetical protein | 60 | none | none | pending | — |
| — | `Mup14` | hypothetical protein | 100 | none | none | pending | — |
| — | `Mup15` | hypothetical protein | 88 | none | none | pending | — |
| — | `Mup16` | regulatory protein GemA | 183 | none | none | pending | — |
| — | `Mup17` | late transcriptional activator | 129 | none | none | pending | — |
| — | `Mup18` | hypothetical protein | 72 | none | none | pending | — |
| — | `Mup19` | hypothetical protein | 120 | TM 12–32, TM 38–56, TM 68–91, TM 97–114 | TM 12–27, TM 32–56, TM 68–88, TM 98–114 | pending | span_boundaries(max_shift=6) |
| — | `Mup20` | hypothetical protein | 39 | TM 21–38 | TM 21–34 | pending | span_boundaries(max_shift=4) |
| — | `Mup21` | late transcriptional activator | 140 | none | none | pending | — |
| — | `Mup22` | endolysin | 171 | SP 1–24 | SP 1–24 | pending | — |
| — | `Mup23` | Rz-like spanin | 128 | SP 1–19 | SP 1–21 | pending | signal_peptide_boundary |
| — | `Mup24` | hypothetical protein | 64 | none | none | pending | — |
| — | `Mup25` | DUF2730 family protein | 99 | SP 1–19 | TM 6–25 | pending | span_count, signal_peptide |
| — | `Mup26` | hypothetical protein | 96 | none | none | pending | — |
| — | `Mup27` | terminase small subunit | 191 | none | none | pending | — |
| — | `Mup28` | putative portal protein | 551 | none | none | pending | — |
| — | `Mup29` | portal protein | 512 | none | none | pending | — |
| — | `Mup30` | minor head protein and DNA pilot | 439 | none | none | pending | — |
| — | `Mup31` | tail completion or Neck1 protein | 156 | none | none | pending | — |
| — | `Mup32` | head maturation protease | 361 | SP 1–15 | none | pending | signal_peptide |
| — | `Mup33` | head maturation protease | 183 | none | none | pending | — |
| — | `Mup34` | major head protein | 305 | none | none | pending | — |
| — | `Mup35` | hypothetical protein | 136 | none | none | pending | — |
| — | `Mup36` | head-tail adaptor | 141 | none | none | pending | — |
| — | `Mup37` | portal protein | 182 | none | none | pending | — |
| — | `Mup38` | DUF2635 domain-containing protein | 67 | none | none | pending | — |
| — | `Mup39` | tail sheath | 495 | none | none | pending | — |
| — | `Mup40` | tail tube protein | 118 | none | none | pending | — |
| — | `Mup41` | tail assembly chaperone | 144 | none | none | pending | — |
| — | `Mup42` | tail length tape measure protein | 690 | none | none | pending | — |
| — | `Mup43` | DNA circularization N-terminal domain-containing protein | 495 | none | none | pending | — |
| — | `Mup44` | baseplate hub | 379 | none | none | pending | — |
| — | `Mup45` | baseplate assembly protein V | 197 | none | none | pending | — |
| — | `Mup46` | baseplate wedge subunit | 145 | none | none | pending | — |
| — | `Mup47` | baseplate protein | 360 | none | none | pending | — |
| — | `Mup48` | baseplate wedge subunit | 180 | SP 1–19 | none | pending | signal_peptide |
| — | `Mup49` | tail fiber protein | 504 | none | none | pending | — |
| — | `Mup50` | tail fiber assembly protein | 175 | none | none | pending | — |
| — | `Mup51` | tail fiber assembly protein | 177 | none | none | pending | — |
| — | `Mup52` | tail fiber protein | 328 | none | SP 1–10 | pending | signal_peptide |
| — | `Mup53` | DNA invertase | 193 | none | none | pending | — |
| — | `Mup54` | gpCom control of modification | 62 | none | none | pending | — |
| — | `Mup55` | Mom-like DNA modification protein | 241 | none | none | pending | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org Mu [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `Mu`; or locally `python3 scripts/rerun.py --org Mu`.

## Validation
`verification.json`: 24 pass, 0 fail, 1 pending of 25 checks. Pending: TOPCONS2 coverage of eligible proteins: 0/55 eligible (55 in inventory); {'pending': 55}.
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org Mu     # skips files already present
python3 scripts/02_inventory.py --org Mu
python3 scripts/03_run_phobius.py --org Mu      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org Mu    # resumable
python3 scripts/04_run_topcons.py --org Mu      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org Mu && python3 scripts/08_build_atlas.py --org Mu
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org Mu
python3 scripts/rerun.py --org Mu [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
