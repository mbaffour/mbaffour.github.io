# Enterobacteria phage T7 — membrane topology & charge lab reference

Open **`T7_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_001604.1**: "Enterobacteria phage T7, complete genome", 39,937 nt, linear; NCBI record updated 2023/01/07; taxid 10760.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **60** CDS features with a `/translation` (60 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Escherichia coli. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 60 / 60 ({'complete': 60}) | — |
| DeepTMHMM | 60 / 60 ({'complete': 60}) | — |
| TOPCONS2 | 60 / 60 ({'complete': 60}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: cached: 56, newrun: 4. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 3 records.

## Summary
- 9 proteins with ≥1 predicted membrane span (any main method); 7 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 10 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| — | `T7p01` | ocr-like anti-restriction | 117 | none | none | none | — |
| — | `T7p02` | hypothetical protein | 51 | none | none | none | — |
| — | `T7p04` | hypothetical protein | 47 | SP 1–17, TM 27–45 | SP 1–12 | SP 1–21, TM 24–44 | span_count, signal_peptide_boundary |
| — | `T7p05` | hypothetical protein | 111 | none | none | none | — |
| — | `T7p06` | hypothetical protein | 53 | none | none | none | — |
| — | `T7p03` | serine-threonine kinase | 359 | none | none | none | — |
| — | `T7p07` | RNA polymerase | 883 | none | none | none | — |
| — | `T7p09` | hypothetical protein | 42 | none | none | none | — |
| — | `T7p08` | dGTPase inhibitor; target for F exclusion | 85 | none | none | none | — |
| — | `T7p10` | DNA ligase | 359 | none | none | none | — |
| — | `T7p11` | hypothetical protein | 51 | SP 1–19, TM 29–49 | TM 5–23, TM 28–48 | SP 1–24, TM 29–49 | span_count, signal_peptide, n_terminal_side, signal_peptide_boundary |
| — | `T7p12` | hypothetical protein | 29 | SP 1–19 | SP 1–16 | SP 1–21 | signal_peptide_boundary |
| — | `T7p13` | hypothetical protein | 86 | none | none | none | — |
| — | `T7p14` | nucleotide kinase | 196 | none | none | none | — |
| — | `T7p15` | hypothetical protein | 48 | none | none | none | — |
| — | `T7p16` | RNA polymerase inhibitor | 64 | none | none | none | — |
| — | `T7p17` | Gp2.5-like ssDNA binding protein and ssDNA annealing protein | 232 | none | none | none | — |
| — | `T7p18` | endonuclease | 139 | none | none | none | — |
| — | `T7p19` | endonuclease | 149 | none | none | none | — |
| — | `T7p20` | amidase | 151 | none | none | none | — |
| — | `T7p21` | HNH endonuclease | 121 | none | none | none | — |
| — | `T7p22` | DNA primase/helicase | 566 | none | none | none | — |
| — | `T7p23` | hypothetical protein | 40 | none | none | none | — |
| — | `T7p24` | DNA primase/helicase | 503 | none | none | none | — |
| — | `T7p25` | hypothetical protein | 112 | TM 7–31, TM 37–59 | SP 1–37, TM 39–54 | SP 1–26, TM 35–55 | span_count, signal_peptide, n_terminal_side, signal_peptide_boundary |
| — | `T7p26` | hypothetical protein | 70 | none | none | none | — |
| — | `T7p27` | hypothetical protein | 89 | none | none | none | — |
| — | `T7p28` | hypothetical protein | 135 | none | none | none | — |
| — | `T7p29` | DNA polymerase I | 704 | none | none | none | — |
| — | `T7p30` | hypothetical protein | 118 | none | none | none | — |
| — | `T7p31` | hypothetical protein | 169 | none | none | none | — |
| — | `T7p32` | DUF2675 domain-containing protein | 99 | none | none | none | — |
| — | `T7p33` | hypothetical protein | 69 | none | none | none | — |
| — | `T7p34` | Gp5.9-like inihibitor of recBCD nuclease | 52 | none | none | none | — |
| — | `T7p35` | exonuclease | 300 | none | none | none | — |
| — | `T7p36` | DUF5516 domain-containing protein | 37 | TM 6–27 | TM 7–27 | TM 5–25 | — |
| — | `T7p37` | DUF2717 domain-containing protein | 84 | none | none | none | — |
| — | `T7p38` | DUF5476 family protein | 88 | none | none | none | — |
| — | `T7p39` | host range and adsorption protein | 133 | none | none | none | — |
| — | `T7p40` | host range and adsorption protein | 99 | none | none | none | — |
| — | `T7p41` | HNH endonuclease | 130 | none | none | none | — |
| — | `T7p42` | head-tail adaptor | 536 | none | none | none | — |
| — | `T7p43` | head assembly | 307 | none | none | none | — |
| — | `T7p44` | major head protein | 398 | none | none | none | — |
| — | `T7p45` | major head protein | 345 | none | none | none | — |
| — | `T7p46` | tail protein | 196 | none | none | none | — |
| — | `T7p47` | tail protein | 794 | none | none | none | — |
| — | `T7p48` | internal virion protein | 138 | none | none | none | — |
| — | `T7p49` | internal virion protein | 196 | SP 1–16 | none | SP 1–22 | signal_peptide, signal_peptide_boundary |
| — | `T7p50` | internal virion protein | 747 | none | none | none | — |
| — | `T7p51` | internal virion protein with endolysin domain | 1318 | TM 1136–1157 | none | none | span_count |
| — | `T7p52` | tail fiber protein | 553 | none | none | none | — |
| — | `T7p53` | holin | 67 | TM 37–55 | TM 13–26, TM 37–55 | TM 35–55 | span_count, n_terminal_side |
| — | `T7p54` | terminase small subunit | 89 | none | none | none | — |
| — | `T7p55` | Rz-like spanin | 143 | TM 6–25 | TM 8–21 | TM 6–26 | n_terminal_side |
| — | `T7p56` | Rz-like spanin | 83 | SP 1–49 | SP 1–48 | TM 31–51 | span_count, signal_peptide, signal_peptide_boundary |
| — | `T7p57` | terminase large subunit | 586 | none | none | none | — |
| — | `T7p58` | hypothetical protein | 85 | none | none | none | — |
| — | `T7p59` | hypothetical protein | 57 | none | none | none | — |
| — | `T7p60` | hypothetical protein | 49 | SP 1–30 | TM 17–26 | SP 1–30 | span_count, signal_peptide |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org T7 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `T7`; or locally `python3 scripts/rerun.py --org T7`.

## Validation
`verification.json`: 25 pass, 0 fail, 0 pending of 25 checks. 
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org T7     # skips files already present
python3 scripts/02_inventory.py --org T7
python3 scripts/03_run_phobius.py --org T7      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org T7    # resumable
python3 scripts/04_run_topcons.py --org T7      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org T7 && python3 scripts/08_build_atlas.py --org T7
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org T7
python3 scripts/rerun.py --org T7 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
