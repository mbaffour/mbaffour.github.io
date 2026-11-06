# Enterobacteria phage lambda — membrane topology & charge lab reference

Open **`lambda_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

> **Partial:** at least one predictor has not yet finished every eligible protein (see coverage). Missing results are shown as pending, never substituted. Resume with the commands below.

## Source
- RefSeq **NC_001416.1**: "Enterobacteria phage lambda, complete genome", 48,502 nt, linear; NCBI record updated 2023/01/11; taxid 2681611.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **73** CDS features with a `/translation` (73 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Escherichia coli. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 73 / 73 ({'complete': 73}) | — |
| DeepTMHMM | 73 / 73 ({'complete': 73}) | — |
| TOPCONS2 | 0 / 73 ({'pending': 73}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: —. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 3 records.

## Summary
- 9 proteins with ≥1 predicted membrane span (any main method); 5 with a predicted signal peptide; 1 with DeepTMHMM β-type states; 12 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| nu1 | `lambdap01` | terminase small subunit | 181 | none | none | pending | — |
| A | `lambdap02` | terminase large subunit | 641 | none | none | pending | — |
| W | `lambdap03` | head-tail adaptor Ad1 | 68 | none | none | pending | — |
| B | `lambdap04` | portal protein | 533 | none | none | pending | — |
| C | `lambdap05` | S49 family peptidase | 439 | none | none | pending | — |
| nu3 | `lambdap06` | capsid assembly protein | 201 | none | none | pending | — |
| D | `lambdap07` | head decoration | 110 | none | none | pending | — |
| E | `lambdap08` | major capsid protein | 341 | none | none | pending | — |
| Fi | `lambdap09` | DNA packaging chaperone FI | 132 | none | none | pending | — |
| Fii | `lambdap10` | head closure Hc1 | 117 | none | none | pending | — |
| Z | `lambdap11` | tail protein | 192 | none | none | pending | — |
| U | `lambdap12` | tail terminator | 131 | none | none | pending | — |
| V | `lambdap13` | major tail protein | 246 | none | none | pending | — |
| G | `lambdap14` | minor tail protein G | 140 | none | none | pending | — |
| T | `lambdap15` | minor tail protein | 144 | none | none | pending | — |
| H | `lambdap16` | tail length tape measure protein | 853 | TM 114–140 | TM 117–136 | pending | span_boundaries(max_shift=4) |
| M | `lambdap17` | minor tail protein | 109 | none | none | pending | — |
| L | `lambdap18` | minor tail protein | 232 | none | none | pending | — |
| K | `lambdap19` | C40 family peptidase | 199 | none | none | pending | — |
| I | `lambdap20` | tail assembly protein | 223 | TM 102–126, TM 138–156 | TM 100–109 | pending | span_count |
| J | `lambdap21` | central tail fiber J | 1132 | none | none | pending | — |
| lom | `lambdap26` | Lom outer membrane protein | 206 | SP 1–23 | SP 1–23, β 29–39, β 56–64, β 72–80, β 103–111, β 119–127, β 163–173, β 179–190, β 196–204 | pending | span_count |
| orf-401 | `lambdap27` | tail fiber protein | 401 | none | none | pending | — |
| orf206b | `lambdap90` | hypothetical protein | 206 | SP 1–24 | none | pending | signal_peptide |
| orf-314 | `lambdap28` | tail fiber protein | 314 | none | none | pending | — |
| orf-194 | `lambdap29` | tail fiber assembly | 194 | none | none | pending | — |
| ea47 | `lambdap80` | ea47 | 410 | none | none | pending | — |
| ea31 | `lambdap81` | HNH endonuclease | 296 | none | none | pending | — |
| ea59 | `lambdap82` | AAA family ATPase | 525 | none | none | pending | — |
| int | `lambdap33` | integrase | 356 | none | none | pending | — |
| xis | `lambdap34` | excisionase | 72 | none | none | pending | — |
| — | `lambdap35` | hypothetical protein | 55 | none | none | pending | — |
| ea8.5 | `lambdap36` | ea8.5 | 93 | none | none | pending | — |
| ea22 | `lambdap83` | ead/Ea22-like family protein | 182 | none | none | pending | — |
| orf61 | `lambdap37` | hypothetical protein | 61 | none | none | pending | — |
| orf63 | `lambdap38` | DUF1382 family protein | 63 | none | none | pending | — |
| orf60a | `lambdap39` | DUF1317 domain-containing protein | 60 | none | none | pending | — |
| exo | `lambdap41` | exonuclease | 226 | none | none | pending | — |
| bet | `lambdap84` | RecT-like ssDNA annealing protein | 261 | none | none | pending | — |
| gam | `lambdap42` | gam-like host nuclease inhibitor | 138 | none | none | pending | — |
| kil | `lambdap85` | Kil protein for bacterial septation inhibition | 47 | none | none | pending | — |
| cIII | `lambdap86` | CIII anti-termination | 54 | none | none | pending | — |
| ea10 | `lambdap45` | hypothetical protein | 122 | none | none | pending | — |
| ral | `lambdap46` | restriction alleviation ral | 66 | none | none | pending | — |
| orf28 | `lambdap47` | hypothetical protein | 28 | none | none | pending | — |
| — | `lambdap48` | SieB superinfection exclusion | 184 | TM 21–38, TM 58–80 | TM 24–39, TM 55–72 | pending | span_boundaries(max_shift=8) |
| N | `lambdap49` | anti-termination protein N-like | 133 | none | none | pending | — |
| rexb | `lambdap53` | RexB-like exclusion protein | 144 | TM 7–26, TM 46–66, TM 78–106, TM 112–137 | TM 9–25, TM 50–65, TM 86–106, TM 117–134 | pending | span_boundaries(max_shift=8) |
| rexa | `lambdap87` | RexA-like exclusion protein | 279 | none | none | pending | — |
| cI | `lambdap88` | LexA family transcriptional regulator | 237 | none | none | pending | — |
| cro | `lambdap57` | Cro/CI family transcriptional regulator | 66 | none | none | pending | — |
| cII | `lambdap59` | CII-like transcriptional activator | 97 | none | none | pending | — |
| O | `lambdap89` | replication initiation O-like | 299 | none | none | pending | — |
| P | `lambdap61` | DNA replication protein | 233 | none | none | pending | — |
| ren | `lambdap62` | Ren-like exclusion protein | 96 | none | none | pending | — |
| NinB | `lambdap63` | NinB/ Orf homologous recombination mediator | 146 | none | none | pending | — |
| NinC | `lambdap64` | phosphoadenosine phosphosulfate reductase | 290 | none | none | pending | — |
| NinD | `lambdap65` | NinD protein | 57 | none | none | pending | — |
| NinE | `lambdap66` | NinE family protein | 60 | none | none | pending | — |
| NinF | `lambdap67` | protein ninF | 56 | none | none | pending | — |
| NinG | `lambdap68` | NinG/ Rap DNA junction specific endonuclease | 204 | none | none | pending | — |
| NinH | `lambdap69` | NinH family protein | 68 | none | none | pending | — |
| NinI | `lambdap70` | serine/threonine protein phosphatase | 221 | none | none | pending | — |
| Q | `lambdap71` | antitermination protein | 207 | none | none | pending | — |
| orf-64 | `lambdap73` | hypothetical protein | 64 | TM 41–59 | none | pending | span_count |
| S | `lambdap74` | holin/anti-holin | 107 | TM 12–32, TM 39–58, TM 64–83 | TM 19–34, TM 44–64, TM 71–91 | pending | span_boundaries(max_shift=8) |
| S' | `lambdap92` | holin/anti-holin | 105 | TM 6–26, TM 38–56, TM 62–81 | TM 17–32, TM 42–62, TM 69–89 | pending | span_boundaries(max_shift=11) |
| R | `lambdap75` | endolysin | 158 | none | none | pending | — |
| Rz | `lambdap76` | Rz-like spanin | 153 | SP 1–22 | TM 6–23 | pending | span_count, signal_peptide |
| Rz1 | `lambdap91` | Rz-like spanin | 60 | SP 1–22 | SP 1–19 | pending | signal_peptide_boundary |
| bor | `lambdap77` | Bor-like outer membrane protein | 97 | SP 1–18 | SP 1–16 | pending | signal_peptide_boundary |
| — | `lambdap78` | head protein | 177 | none | none | pending | — |
| — | `lambdap79` | hypothetical protein | 68 | none | none | pending | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org lambda [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `lambda`; or locally `python3 scripts/rerun.py --org lambda`.

## Validation
`verification.json`: 24 pass, 0 fail, 2 pending of 26 checks. Pending: all batches complete: TOPCONS2/b001.job.json:submitted; TOPCONS2 coverage of eligible proteins: 0/73 eligible (73 in inventory); {'pending': 73}.
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org lambda     # skips files already present
python3 scripts/02_inventory.py --org lambda
python3 scripts/03_run_phobius.py --org lambda      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org lambda    # resumable
python3 scripts/04_run_topcons.py --org lambda      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org lambda && python3 scripts/08_build_atlas.py --org lambda
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org lambda
python3 scripts/rerun.py --org lambda [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
