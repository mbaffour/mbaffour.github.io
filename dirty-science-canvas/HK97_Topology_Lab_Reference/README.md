# Enterobacteria phage HK97 — membrane topology & charge lab reference

Open **`HK97_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_002167.1**: "Enterobacteria phage HK97, complete genome", 39,732 nt, linear; NCBI record updated 2023/01/11; taxid 2681617.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **61** CDS features with a `/translation` (61 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Escherichia coli. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 61 / 61 ({'complete': 61}) | — |
| DeepTMHMM | 61 / 61 ({'complete': 61}) | — |
| TOPCONS2 | 61 / 61 ({'complete': 61}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: cached: 8, newrun: 53. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 3 records.

## Summary
- 8 proteins with ≥1 predicted membrane span (any main method); 4 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 9 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| — | `HK97p01` | terminase small subunit | 161 | none | none | none | — |
| — | `HK97p02` | terminase large subunit | 504 | none | none | none | — |
| — | `HK97p03` | portal protein | 424 | none | none | none | — |
| — | `HK97p04` | head maturation protease | 225 | none | none | none | — |
| — | `HK97p05` | major head protein | 385 | none | TM 215–224 | none | span_count |
| — | `HK97p06` | head-tail adaptor Ad1 | 108 | none | none | none | — |
| — | `HK97p07` | head closure Hc1 | 112 | none | none | none | — |
| — | `HK97p08` | HK97 gp10 family protein | 149 | none | none | none | — |
| — | `HK97p09` | tail terminator | 115 | none | none | none | — |
| — | `HK97p10` | major tail subunit | 234 | none | none | none | — |
| — | `HK97p11` | tail protein | 224 | none | none | none | — |
| — | `HK97p12` | tail protein | 128 | none | none | none | — |
| — | `HK97p13` | Gp15 | 62 | TM 6–24 | TM 4–24 | TM 5–25 | — |
| H | `HK97p14` | tail length tape measure protein | 1089 | none | TM 71–80, TM 295–305, TM 432–441 | TM 292–312, TM 427–447 | span_count, n_terminal_side |
| M | `HK97p15` | minor tail protein | 112 | none | none | none | — |
| L | `HK97p16` | minor tail protein | 252 | none | none | none | — |
| K | `HK97p17` | minor tail protein | 236 | none | none | none | — |
| I | `HK97p19` | tail protein | 202 | TM 98–121, TM 127–145 | none | TM 93–113, TM 124–144 | span_count |
| — | `HK97p20` | Gp22 | 120 | none | none | none | — |
| — | `HK97p21` | Gp23 | 86 | SP 1–24 | none | none | signal_peptide |
| J | `HK97p22` | tail protein | 1296 | none | none | none | — |
| stf | `HK97p23` | tail fiber protein | 321 | none | none | none | — |
| tfa | `HK97p24` | tail fiber assembly | 202 | none | none | none | — |
| int | `HK97p25` | integrase | 356 | none | none | none | — |
| xis | `HK97p26` | excisionase | 72 | none | none | none | — |
| — | `HK97p27` | Gp37 | 176 | none | none | none | — |
| — | `HK97p28` | DUF2737 family protein | 54 | none | none | none | — |
| — | `HK97p29` | abc2 anti-RecBCD | 97 | none | none | none | — |
| — | `HK97p30` | Gp40 | 129 | none | none | none | — |
| erf | `HK97p31` | Erf-like ssDNA annealing protein | 201 | none | none | none | — |
| — | `HK97p32` | recombinase | 83 | none | none | none | — |
| — | `HK97p33` | recombinase | 58 | none | none | none | — |
| kil | `HK97p34` | Kil protein for bacterial septation inhibition | 50 | none | none | none | — |
| cIII | `HK97p35` | CIII anti-termination | 44 | none | none | none | — |
| — | `HK97p36` | Gp45 | 156 | none | none | none | — |
| N | `HK97p37` | anti-termination protein N-like | 127 | none | none | none | — |
| — | `HK97p38` | Gp48 | 216 | TM 151–175 | TM 151–171 | TM 15–35, TM 151–171 | span_count |
| — | `HK97p39` | Gp49 | 88 | none | none | none | — |
| cI | `HK97p40` | LexA family transcriptional regulator | 237 | none | none | none | — |
| — | `HK97p41` | Cro/CI family transcriptional regulator | 66 | none | none | none | — |
| cII | `HK97p42` | CII-like transcriptional activator | 98 | none | none | none | — |
| — | `HK97p43` | Gp53 | 53 | none | none | none | — |
| O | `HK97p44` | replication initiation O-like | 273 | none | none | none | — |
| P | `HK97p45` | replicative DNA helicase | 458 | SP 1–23 | none | none | signal_peptide |
| — | `HK97p46` | Gp56 | 32 | none | SP 1–23 | TM 2–22 | span_count, signal_peptide |
| — | `HK97p47` | Gp60 | 70 | none | none | none | — |
| — | `HK97p48` | NinB/ Orf homologous recombination mediator | 146 | none | none | none | — |
| — | `HK97p49` | DNA methyltransferase | 175 | none | none | none | — |
| — | `HK97p50` | NinE family protein | 60 | none | none | none | — |
| — | `HK97p51` | protein ninF | 56 | none | none | none | — |
| roi | `HK97p52` | anti-repressor | 241 | none | none | none | — |
| — | `HK97p53` | HNH endonuclease | 96 | none | none | none | — |
| — | `HK97p54` | RusA family crossover junction endodeoxyribonuclease | 120 | none | none | none | — |
| — | `HK97p55` | protein ninH | 62 | none | none | none | — |
| — | `HK97p56` | antitermination protein | 207 | none | none | none | — |
| — | `HK97p57` | holin/anti-holin | 106 | TM 12–31, TM 38–57, TM 63–82 | TM 12–31, TM 43–63, TM 70–90 | TM 41–61, TM 68–88 | span_count, n_terminal_side |
| — | `HK97p58` | endolysin | 158 | none | none | none | — |
| Rz | `HK97p59` | Rz-like spanin | 145 | SP 1–22 | TM 4–23 | SP 1–22 | span_count, signal_peptide |
| — | `HK97p60` | KilA-N domain-containing protein | 242 | none | none | none | — |
| — | `HK97p61` | hypothetical protein | 77 | none | none | none | — |
| — | `HK97p62` | HNH endonuclease | 119 | none | none | none | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org HK97 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `HK97`; or locally `python3 scripts/rerun.py --org HK97`.

## Validation
`verification.json`: 25 pass, 0 fail, 0 pending of 25 checks. 
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org HK97     # skips files already present
python3 scripts/02_inventory.py --org HK97
python3 scripts/03_run_phobius.py --org HK97      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org HK97    # resumable
python3 scripts/04_run_topcons.py --org HK97      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org HK97 && python3 scripts/08_build_atlas.py --org HK97
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org HK97
python3 scripts/rerun.py --org HK97 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
