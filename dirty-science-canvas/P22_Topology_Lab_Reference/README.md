# Salmonella phage P22 — membrane topology & charge lab reference

Open **`P22_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

> **Partial:** at least one predictor has not yet finished every eligible protein (see coverage). Missing results are shown as pending, never substituted. Resume with the commands below.

## Source
- RefSeq **NC_002371.2**: "TPA: Salmonella phage P22, complete genome", 41,724 nt, linear; NCBI record updated 2023/01/11; taxid 2908168.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **72** CDS features with a `/translation` (72 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Salmonella enterica serovar Typhimurium. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 72 / 72 ({'complete': 72}) | — |
| DeepTMHMM | 72 / 72 ({'complete': 72}) | — |
| TOPCONS2 | 0 / 72 ({'pending': 72}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: —. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 2 records.

## Summary
- 10 proteins with ≥1 predicted membrane span (any main method); 7 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 12 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| 3 | `P22gp01` | terminase small subunit | 162 | none | none | pending | — |
| 2 | `P22gp02` | terminase large subunit | 499 | none | none | pending | — |
| 1 | `P22gp03` | portal protein | 725 | none | none | pending | — |
| 8 | `P22gp04` | head scaffolding protein | 303 | none | none | pending | — |
| 5 | `P22gp05` | head protein | 430 | none | none | pending | — |
| orf69 | `P22gp06` | hypothetical protein | 69 | none | none | pending | — |
| 4 | `P22gp07` | head-tail adaptor Ad3 | 166 | none | none | pending | — |
| 10 | `P22gp08` | head closure Hc3 | 472 | none | none | pending | — |
| 26 | `P22gp09` | tail needle protein | 233 | none | none | pending | — |
| 14 | `P22gp10` | head morphogenesis | 151 | none | none | pending | — |
| 7 | `P22gp11` | DNA ejection | 229 | none | none | pending | — |
| 20 | `P22gp12` | released from the phage upon host infection | 471 | none | none | pending | — |
| 16 | `P22gp13` | head morphogenesis | 609 | none | none | pending | — |
| sieA | `P22gp14` | superinfection exclusion SieA-like | 164 | TM 6–28, TM 81–106, TM 118–141 | TM 8–28, TM 81–107, TM 121–141 | pending | — |
| orf59a | `P22gp16` | hypothetical protein | 59 | none | none | pending | — |
| mnt | `P22gp15` | partition protein ATPase | 83 | none | none | pending | — |
| arc | `P22gp18` | Arc-like repressor | 53 | none | none | pending | — |
| ant | `P22gp17` | Ant | 300 | none | none | pending | — |
| 9 | `P22gp19` | tail spike protein | 667 | none | none | pending | — |
| gtrC | `P22gp20` | GtrC-like O-antigen conversion translocase | 486 | TM 12–32, TM 57–87, TM 99–116, TM 122–143, TM 155–180, TM 200–219, TM 231–249, TM 261–281, TM 293–313, TM 319–342, TM 351–368 | TM 10–24, TM 75–90, TM 100–111, TM 126–142, TM 148–163, TM 167–180, TM 197–209, TM 265–280, TM 293–313, TM 323–342, TM 351–362 | pending | span_boundaries(max_shift=40) |
| gtrB | `P22gp21` | GtrB glycosyltransferase for O-antigen conversion | 310 | TM 228–249, TM 261–286 | TM 228–241, TM 265–283 | pending | span_boundaries(max_shift=8) |
| gtrA | `P22gp22` | GtrA-like O-antigen conversion | 120 | TM 12–30, TM 36–53, TM 65–84, TM 90–110 | TM 5–27, TM 36–56, TM 65–85, TM 93–111 | pending | span_boundaries(max_shift=7) |
| int | `P22gp23` | integrase | 387 | none | none | pending | — |
| xis | `P22gp24` | excisionase | 116 | none | none | pending | — |
| eaC | `P22gp25` | EaC | 211 | none | none | pending | — |
| eaG | `P22gp26` | EaG | 59 | none | none | pending | — |
| eaA | `P22gp27` | EaA | 317 | none | none | pending | — |
| eaI | `P22gp28` | EaI | 64 | none | none | pending | — |
| eaD | `P22gp29` | EaD | 197 | none | none | pending | — |
| eaF | `P22gp30` | EaF | 119 | none | none | pending | — |
| orf45 | `P22gp31` | hypothetical protein | 45 | none | none | pending | — |
| eaE | `P22gp32` | EaE | 165 | none | none | pending | — |
| orf56 | `P22gp33` | hypothetical protein | 56 | none | none | pending | — |
| abc2 | `P22gp34` | abc2 anti-RecBCD | 97 | none | none | pending | — |
| abc1 | `P22gp35` | Abc1 | 94 | none | none | pending | — |
| erf | `P22gp36` | Erf-like ssDNA annealing protein | 205 | none | none | pending | — |
| arf | `P22gp37` | Erf recombination cofactor Arf | 47 | none | none | pending | — |
| kil | `P22gp38` | Kil protein for bacterial septation inhibition | 62 | none | none | pending | — |
| c3 | `P22gp39` | CIII anti-termination | 52 | none | none | pending | — |
| 17 | `P22gp40` | superinfection exclusion | 103 | none | none | pending | — |
| orf87 | `P22gp41` | hypothetical protein | 67 | none | none | pending | — |
| orf78 | `P22gp42` | hypothetical protein | 78 | none | none | pending | — |
| ral | `P22gp43` | restriction alleviation ral | 64 | none | none | pending | — |
| sieB | `P22gp44` | superinfection exclusion; inhibits SieB | 192 | TM 12–36, TM 56–77 | TM 19–36, TM 56–73 | pending | span_boundaries(max_shift=7) |
| esc | `P22gp45` | superinfection exclusion; inhibits SieB | 168 | SP 1–16, TM 32–53 | TM 2–12, TM 32–52 | pending | span_count, signal_peptide, n_terminal_side |
| 24 | `P22gp46` | hypothetical protein | 100 | none | none | pending | — |
| c2 | `P22gp47` | C2 | 216 | none | none | pending | — |
| cro | `P22gp48` | transcriptional regulator | 61 | none | none | pending | — |
| c1 | `P22gp49` | CII-like transcriptional activator | 92 | none | none | pending | — |
| orf48 | `P22gp50` | tail protein | 48 | none | none | pending | — |
| 18 | `P22gp51` | replication initiation O-like | 271 | none | none | pending | — |
| 12 | `P22gp52` | hypothetical protein | 458 | SP 1–23 | none | pending | signal_peptide |
| ninA | `P22gp53` | hypothetical protein | 26 | TM 6–22 | SP 1–21 | pending | span_count, signal_peptide |
| ninB | `P22gp54` | NinB/ Orf homologous recombination mediator | 145 | none | none | pending | — |
| ninD | `P22gp55` | NinD | 57 | none | none | pending | — |
| ninE | `P22gp56` | NinE | 58 | none | none | pending | — |
| ninX | `P22gp57` | NinX | 112 | none | none | pending | — |
| ninF | `P22gp58` | NinF | 58 | none | none | pending | — |
| ninG | `P22gp59` | NinG/ Rap DNA junction specific endonuclease | 203 | none | none | pending | — |
| ninY | `P22gp60` | NinY | 74 | none | none | pending | — |
| ninH | `P22gp61` | NinH | 67 | none | none | pending | — |
| ninZ | `P22gp62` | NinZ | 59 | none | none | pending | — |
| 23 | `P22gp63` | transcription antitermination protein | 207 | none | none | pending | — |
| 13 | `P22gp64` | holin/anti-holin | 108 | TM 12–33, TM 45–66, TM 72–92 | TM 20–35, TM 45–65, TM 72–92 | pending | span_boundaries(max_shift=8) |
| 13' | `P22gp65` | holin/anti-holin | 105 | TM 12–30, TM 42–63, TM 69–89 | TM 17–32, TM 42–62, TM 69–89 | pending | span_boundaries(max_shift=5) |
| 19 | `P22gp66` | endolysin | 146 | none | none | pending | — |
| 15 | `P22gp67` | Rz-like spanin | 145 | SP 1–22 | TM 6–23 | pending | span_count, signal_peptide |
| Rz1 | `P22gp68` | Rz-like spanin | 61 | SP 1–19 | SP 1–19 | pending | — |
| rha | `P22gp69` | anti-repressor | 201 | SP 1–17 | none | pending | signal_peptide |
| orf25 | `P22gp70` | hypothetical protein | 25 | none | SP 1–24 | pending | signal_peptide |
| orf80 | `P22gp71` | Orf80 | 80 | none | none | pending | — |
| orf59c | `P22gp72` | Orf59c | 59 | none | none | pending | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org P22 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `P22`; or locally `python3 scripts/rerun.py --org P22`.

## Validation
`verification.json`: 24 pass, 0 fail, 1 pending of 25 checks. Pending: TOPCONS2 coverage of eligible proteins: 0/72 eligible (72 in inventory); {'pending': 72}.
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org P22     # skips files already present
python3 scripts/02_inventory.py --org P22
python3 scripts/03_run_phobius.py --org P22      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org P22    # resumable
python3 scripts/04_run_topcons.py --org P22      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org P22 && python3 scripts/08_build_atlas.py --org P22
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org P22
python3 scripts/rerun.py --org P22 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
