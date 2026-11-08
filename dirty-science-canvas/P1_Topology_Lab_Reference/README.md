# Enterobacteria phage P1 — membrane topology & charge lab reference

Open **`P1_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_005856.1**: "Enterobacteria phage P1, complete genome", 94,800 nt, linear; NCBI record updated 2023/01/11; taxid 2886926.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **110** CDS features with a `/translation` (110 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Escherichia coli. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 110 / 110 ({'complete': 110}) | — |
| DeepTMHMM | 110 / 110 ({'complete': 110}) | — |
| TOPCONS2 | 110 / 110 ({'complete': 110}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: cached: 20, newrun: 90. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 4 records.

## Summary
- 8 proteins with ≥1 predicted membrane span (any main method); 9 with a predicted signal peptide; 0 with DeepTMHMM β-type states; 11 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| cra | `P1_gp002` | Cra | 73 | none | none | none | — |
| cre | `P1_gp003` | site-specific integrase | 343 | none | none | none | — |
| c8 | `P1_gp004` | C8 | 103 | none | none | none | — |
| ref | `P1_gp005` | Ref-like RecA filament endonuclease | 186 | none | none | none | — |
| mat | `P1_gp006` | Mat | 250 | none | none | none | — |
| res | `P1_gp007` | type III restriction-modification system endonuclease | 970 | none | none | none | — |
| lxc | `P1_gp009` | Lxc | 82 | none | none | none | — |
| ulx | `P1_gp010` | Ulx-like anti-restriction | 146 | none | none | none | — |
| darB | `P1_gp011` | N-6 DNA methylase | 2255 | none | none | none | — |
| prt | `P1_gp012` | portal protein | 569 | none | none | none | — |
| pro | `P1_gp013` | tail fiber protein | 339 | none | none | none | — |
| lydE | `P1_gp115` | LydE | 71 | none | none | none | — |
| lydD | `P1_gp014` | holin | 84 | TM 12–32, TM 38–57 | TM 15–32, TM 41–57 | TM 12–32, TM 41–61 | span_boundaries(max_shift=4) |
| lyz | `P1_gp015` | endolysin | 185 | SP 1–24 | SP 1–24 | SP 1–24 | — |
| ssb | `P1_gp016` | single strand DNA binding protein | 162 | none | none | none | — |
| isaA | `P1_gp017` | IsaA | 320 | none | none | none | — |
| insB | `P1_gp018` | transposase | 167 | none | none | none | — |
| insA | `P1_gp019` | transposase | 91 | none | none | none | — |
| isaB | `P1_gp020` | IsaB | 201 | none | none | none | — |
| hxr | `P1_gp021` | Hxr | 102 | none | none | none | — |
| ddrB | `P1_gp022` | DdrB | 995 | none | none | none | — |
| iddB | `P1_gp116` | IddB | 132 | SP 1–26 | none | SP 1–21 | signal_peptide, signal_peptide_boundary |
| ddrA | `P1_gp023` | DdrA-like anti-restriction protein | 121 | none | none | none | — |
| darA | `P1_gp024` | released from the phage upon host infection | 639 | none | none | none | — |
| hdf | `P1_gp025` | Hdf-like antirestriction | 203 | none | none | none | — |
| lydB | `P1_gp026` | lysis determining protein | 147 | SP 1–14 | none | none | signal_peptide |
| lydA | `P1_gp027` | holin | 109 | TM 6–26, TM 38–58 | TM 10–29, TM 38–58, TM 68–84 | TM 7–27, TM 38–58 | span_count |
| lydC | `P1_gp028` | LydC | 93 | TM 6–22, TM 34–52 | TM 6–21, TM 34–52, TM 65–77 | TM 2–22, TM 33–53 | span_count |
| cin | `P1_gp029` | DNA invertase | 186 | none | none | none | — |
| U prime | `P1_gp030` | tail fiber chaperone | 177 | none | none | none | — |
| U | `P1_gp031` | tail fiber assembly protein | 175 | none | none | none | — |
| S | `P1_gp032` | tail fiber protein | 987 | none | none | none | — |
| R | `P1_gp033` | tail fiber assembly protein | 144 | none | none | none | — |
| 16 | `P1_gp034` | tail tube protein | 278 | none | none | none | — |
| bplA | `P1_gp035` | baseplate protein | 477 | none | none | none | — |
| pmgA | `P1_gp036` | PmgA | 118 | none | none | none | — |
| sit | `P1_gp037` | transglycosylase SLT domain-containing protein | 1140 | none | TM 402–411 | none | span_count |
| pmgB | `P1_gp038` | PmgB-like head morphogenesis | 293 | none | none | none | — |
| tub | `P1_gp039` | tail tube protein | 203 | none | none | none | — |
| pmgC | `P1_gp040` | PmgC-like head morphogenesis | 188 | none | none | none | — |
| simC | `P1_gp041` | SimC | 264 | SP 1–25 | SP 1–25 | SP 1–25 | — |
| simB | `P1_gp042` | SimB | 111 | SP 1–24 | SP 1–24 | SP 1–24 | — |
| simA | `P1_gp043` | SimA | 52 | SP 1–26 | SP 1–26 | SP 1–26 | — |
| icd | `P1_gp045` | host cell division inhibitor Icd-like protein | 73 | none | none | none | — |
| ant1 | `P1_gp046` | anti-repressor | 347 | none | none | none | — |
| ant2 | `P1_gp047` | anti-repressor | 264 | none | none | none | — |
| kilA | `P1_gp049` | anti-repressor | 266 | none | none | none | — |
| repL | `P1_gp050` | RepL | 281 | none | none | none | — |
| rlfA | `P1_gp051` | DUF3800 domain-containing protein | 234 | none | none | none | — |
| rlfB | `P1_gp052` | replication protein | 154 | none | none | none | — |
| pmgF | `P1_gp053` | PmgF | 98 | none | none | none | — |
| bplB | `P1_gp054` | tail tube protein | 169 | none | none | none | — |
| pmgG | `P1_gp055` | PmgG-like head morphogenesis | 193 | none | none | none | — |
| 21 | `P1_gp056` | gp21 | 271 | none | none | none | — |
| 22 | `P1_gp057` | tail sheath | 529 | none | none | none | — |
| 23 | `P1_gp058` | gp23 | 568 | none | none | none | — |
| parB | `P1_gp059` | ParB-like partition protein | 333 | none | none | none | — |
| parA | `P1_gp060` | ParA-like partition protein | 398 | none | none | none | — |
| repA | `P1_gp061` | replication helicase | 286 | none | none | none | — |
| upfA | `P1_gp062` | UpfA | 130 | none | none | none | — |
| mlp | `P1_gp063` | Rz-like spanin | 110 | SP 1–45 | SP 1–39 | SP 1–30 | signal_peptide_boundary |
| ppfA | `P1_gp064` | PpfA | 140 | SP 1–35 | TM 17–36 | TM 17–37 | span_count, signal_peptide |
| upfB | `P1_gp065` | UpfB | 281 | none | none | none | — |
| upfC | `P1_gp066` | PAAR motif of membran proteins | 94 | none | none | none | — |
| uhr | `P1_gp067` | nucleoside triphosphate pyrophosphohydrolase | 94 | none | none | none | — |
| hrdC | `P1_gp068` | exonuclease recombination-associated | 301 | none | none | none | — |
| dmt | `P1_gp069` | DNA methyltransferase | 754 | none | none | none | — |
| plp | `P1_gp072` | Plp | 125 | none | none | none | — |
| upl | `P1_gp073` | Upl | 63 | none | none | none | — |
| tciA | `P1_gp074` | tellurite resistance | 141 | none | none | none | — |
| tciB | `P1_gp075` | TciB-like inhibition of cell division or resistance to colicin | 54 | SP 1–19, TM 29–47 | TM 7–20, TM 29–44 | SP 1–23, TM 29–49 | span_count, signal_peptide, n_terminal_side, signal_peptide_boundary |
| tciC | `P1_gp076` | TciC | 35 | TM 12–32 | TM 13–22 | TM 12–32 | span_boundaries(max_shift=10) |
| ban | `P1_gp077` | DnaB-like replicative helicase | 454 | none | none | none | — |
| dbn | `P1_gp078` | Dbn | 332 | none | none | none | — |
| 5 | `P1_gp079` | baseplate protein | 210 | none | none | none | — |
| 6 | `P1_gp080` | tail protein | 338 | none | none | none | — |
| 24 | `P1_gp081` | baseplate protein | 261 | none | none | none | — |
| 7 | `P1_gp082` | tail protein | 242 | none | none | none | — |
| 25 | `P1_gp083` | tail protein | 405 | none | none | none | — |
| 26 | `P1_gp084` | baseplate wedge subunit | 125 | none | none | none | — |
| pmgL | `P1_gp085` | PmgL | 81 | none | none | none | — |
| pmgM | `P1_gp086` | VRR-NUC domain-containing protein | 192 | none | none | none | — |
| pmgN | `P1_gp087` | PmgN | 51 | none | none | none | — |
| pmgO | `P1_gp088` | alpha-2;3-sialyltransferase | 220 | none | none | none | — |
| pmgP | `P1_gp089` | norphogenetic protein | 208 | none | none | none | — |
| ppp | `P1_gp090` | metallophosphoesterase | 230 | none | none | none | — |
| pmgQ | `P1_gp091` | glycosyltransferase | 233 | none | none | none | — |
| pmgR | `P1_gp092` | PmgR | 72 | none | none | none | — |
| pmgS | `P1_gp093` | PmgS-like head morphogenesis | 420 | none | none | none | — |
| pap | `P1_gp094` | Pap | 168 | none | none | none | — |
| pmgT | `P1_gp095` | PmgT | 309 | none | none | none | — |
| pmgU | `P1_gp096` | PmgU | 111 | none | none | none | — |
| pmgV | `P1_gp097` | PmgV | 120 | none | none | none | — |
| upfM | `P1_gp098` | UpfM | 37 | none | none | none | — |
| upfN | `P1_gp099` | UpfN | 65 | none | none | none | — |
| upfO | `P1_gp100` | UpfO | 46 | none | none | none | — |
| hot | `P1_gp101` | DNA polymerase III theta subunit | 87 | none | none | none | — |
| lxr | `P1_gp102` | Lxr | 190 | none | none | none | — |
| humD | `P1_gp103` | UmuD-like protein | 129 | none | none | none | — |
| phd | `P1_gp104` | Phd-like antitoxin | 73 | none | none | none | — |
| doc | `P1_gp105` | Doc-like toxin | 126 | none | none | none | — |
| pdcA | `P1_gp106` | PdcA | 66 | none | none | none | — |
| pdcB | `P1_gp107` | HNH endonuclease | 347 | none | none | none | — |
| lpa | `P1_gp108` | Lpa-like transcriptional activator | 150 | none | none | none | — |
| pacA | `P1_gp109` | terminase | 397 | none | none | none | — |
| pacB | `P1_gp110` | terminase | 494 | TM 65–84 | none | none | span_count |
| c1.100 | `P1_gp111` | C1.100 | 283 | none | none | none | — |
| coi | `P1_gp112` | Coi | 69 | none | none | none | — |
| imcB | `P1_gp113` | ImcB | 31 | none | none | none | — |
| imcA | `P1_gp114` | ImcA | 37 | none | none | none | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org P1 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `P1`; or locally `python3 scripts/rerun.py --org P1`.

## Validation
`verification.json`: 25 pass, 0 fail, 0 pending of 25 checks. 
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org P1     # skips files already present
python3 scripts/02_inventory.py --org P1
python3 scripts/03_run_phobius.py --org P1      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org P1    # resumable
python3 scripts/04_run_topcons.py --org P1      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org P1 && python3 scripts/08_build_atlas.py --org P1
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org P1
python3 scripts/rerun.py --org P1 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
