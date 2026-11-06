# Enterobacteria phage T4 — membrane topology & charge lab reference

Open **`T4_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

> **Partial:** at least one predictor has not yet finished every eligible protein (see coverage). Missing results are shown as pending, never substituted. Resume with the commands below.

## Source
- RefSeq **NC_000866.4**: "Enterobacteria phage T4, complete genome", 168,903 nt, linear; NCBI record updated 2023/01/11; taxid 2681598.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **278** CDS features with a `/translation` (278 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Escherichia coli. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 278 / 278 ({'complete': 278}) | — |
| DeepTMHMM | 277 / 277 ({'complete': 277, 'unsupported': 1}) | `T4|T4p225`: unsupported residue(s) X not in the DeepTMHMM alphabet (sequence not altered) |
| TOPCONS2 | 0 / 277 ({'pending': 277, 'unsupported': 1}) | `T4|T4p225`: unsupported residue(s) X not in the TOPCONS2 alphabet (sequence not altered) |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: —. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 5 records.

## Summary
- 22 proteins with ≥1 predicted membrane span (any main method); 20 with a predicted signal peptide; 1 with DeepTMHMM β-type states; 29 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| rIIA | `T4p001` | RIIA lysis inhibitor | 725 | none | none | pending | — |
| rIIA.1 | `T4p002` | rIIA.1 hypothetical protein | 67 | none | none | pending | — |
| 60 | `T4p003` | DNA topoisomerase II | 160 | none | none | pending | — |
| 60.1 | `T4p004` | gp60.1 hypothetical protein | 126 | none | none | pending | — |
| mobA | `T4p005` | homing endonuclease | 37 | none | none | pending | — |
| 39 | `T4p006` | DNA topoisomerase II large subunit | 516 | none | none | pending | — |
| 39.1 | `T4p007` | gp39.1 hypothetical protein | 65 | none | SP 1–10 | pending | signal_peptide |
| 39.2 | `T4p008` | FmdB-like transcriptional regulator | 45 | none | none | pending | — |
| goF | `T4p009` | hypothetical protein | 141 | none | none | pending | — |
| cef | `T4p010` | cef modifier of supressor tRNAs | 71 | none | none | pending | — |
| motB | `T4p011` | MotB-like transcriptional regulator | 162 | none | none | pending | — |
| motB.1 | `T4p012` | hypothetical protein | 119 | TM 38–57 | none | pending | span_count |
| motB.2 | `T4p013` | hypothetical protein | 166 | none | none | pending | — |
| dexA | `T4p014` | exonuclease | 227 | none | none | pending | — |
| dexA.1 | `T4p015` | DexA.1 hypothetical protein | 80 | none | none | pending | — |
| dexA.2 | `T4p016` | dextranase | 81 | none | none | pending | — |
| dda | `T4p017` | Dda-like helicase | 439 | none | none | pending | — |
| dda.1 | `T4p018` | Dda.1 hypothetical protein | 103 | none | none | pending | — |
| srd | `T4p019` | Srd anti-sigma factor | 248 | none | none | pending | — |
| modA | `T4p020` | RNA polymerase ADP-ribosylase | 200 | none | none | pending | — |
| modB | `T4p021` | RNA polymerase ADP-ribosylase | 207 | none | none | pending | — |
| modA.2 | `T4p022` | hypothetical protein | 60 | none | none | pending | — |
| modA.3 | `T4p023` | Mrh transcription modulator under heat shock | 156 | none | none | pending | — |
| modA.4 | `T4p024` | ModA.4 hypothetical protein | 54 | none | none | pending | — |
| srh | `T4p025` | decoy of host sigma32 | 67 | none | none | pending | — |
| mrh | `T4p026` | Mrh transcription modulator under heat shock | 161 | none | none | pending | — |
| mrh.1 | `T4p027` | Mrh.1 hypothetical protein | 113 | none | none | pending | — |
| mrh.2 | `T4p028` | Mrh.2 hypothetical protein | 68 | none | none | pending | — |
| soc | `T4p029` | virion structural protein | 80 | none | none | pending | — |
| segF | `T4p030` | SegF homing endonuclease | 224 | none | none | pending | — |
| 56 | `T4p031` | dUTPase | 171 | none | none | pending | — |
| dam | `T4p032` | Dam family site-specific DNA-(adenine-N6)-methyltransferase | 259 | none | none | pending | — |
| 61 | `T4p033` | DNA primase | 342 | none | none | pending | — |
| 61.1 | `T4p034` | gp61.1 hypothetical protein | 54 | none | none | pending | — |
| 61.2 | `T4p035` | gp61.2 hypothetical protein | 208 | none | none | pending | — |
| sp | `T4p036` | spackle periplasmic | 97 | SP 1–22 | SP 1–22 | pending | — |
| 61.4 | `T4p037` | gp61.4 hypothetical protein | 85 | none | none | pending | — |
| dmd | `T4p038` | Dmd discriminator of mRNA degradation | 60 | none | none | pending | — |
| 41 | `T4p039` | AAA family ATPase | 475 | none | none | pending | — |
| 40 | `T4p040` | head vertex assembly chaperone | 114 | none | none | pending | — |
| uvsX | `T4p041` | recombinase | 391 | none | none | pending | — |
| segA | `T4p042` | homing endonuclease | 221 | none | none | pending | — |
| b-gt | `T4p043` | beta-glucosyltransferase | 351 | none | none | pending | — |
| 42 | `T4p044` | thymidylate synthase | 246 | none | none | pending | — |
| imm | `T4p045` | immunity to superinfection | 83 | TM 6–29, TM 41–64 | TM 9–29, TM 39–48, TM 50–61 | pending | span_count |
| imm.1 | `T4p046` | iduronate sulfatase | 125 | SP 1–17 | SP 1–14 | pending | signal_peptide_boundary |
| 43 | `T4p047` | DNA polymerase | 898 | none | none | pending | — |
| regA | `T4p048` | translation repressor | 122 | none | none | pending | — |
| 62 | `T4p049` | clamp loader of DNA polymerase | 187 | none | none | pending | — |
| 44 | `T4p050` | clamp loader of DNA polymerase | 319 | none | none | pending | — |
| 45 | `T4p051` | DNA polymerase processivity factor | 228 | none | none | pending | — |
| rpbA | `T4p052` | RNA polymerase binding | 129 | none | none | pending | — |
| 45.2 | `T4p053` | protein GP45.2 | 62 | none | none | pending | — |
| 46 | `T4p054` | SbcC-like subunit of palindrome specific endonuclease | 560 | none | none | pending | — |
| 46.1 | `T4p055` | DUF5487 family protein | 68 | none | none | pending | — |
| 46.2 | `T4p056` | gp46.2 hypothetical protein | 87 | none | none | pending | — |
| 47 | `T4p057` | SbcD-like subunit of palindrome specific endonuclease | 339 | none | none | pending | — |
| 47.1 | `T4p058` | gp47.1 hypothetical predicted membrane protein | 46 | SP 1–19 | SP 1–45 | pending | signal_peptide_boundary |
| a-gt | `T4p059` | alpha-glucosyltransferase | 400 | none | none | pending | — |
| mobB | `T4p060` | homing endonuclease | 264 | none | none | pending | — |
| a-gt.2 | `T4p061` | a-gt.2 hypothetical protein | 63 | none | none | pending | — |
| a-gt.3 | `T4p062` | a-gt.3 hypothetical protein | 67 | none | none | pending | — |
| a-gt.4 | `T4p063` | a-gt.4 family protein | 105 | none | none | pending | — |
| a-gt.5 | `T4p064` | a-gt.5 hypothetical protein | 72 | none | none | pending | — |
| 55 | `T4p065` | RNA polymerase sigma factor | 185 | none | none | pending | — |
| 55.1 | `T4p066` | gp55.1 hypothetical protein | 87 | none | none | pending | — |
| 55.2 | `T4p067` | gp55.2 hypothetical protein | 108 | none | none | pending | — |
| 55.3 | `T4p068` | gp55.3 hypothetical protein | 79 | none | none | pending | — |
| 55.4 | `T4p069` | gp55.4 conserved hypothetical protein | 43 | none | none | pending | — |
| 55.5 | `T4p070` | gp55.5 conserved protein of unknown function | 97 | none | none | pending | — |
| 55.6 | `T4p071` | gp55.6 conserved hypothetical protein | 60 | none | none | pending | — |
| nrdH | `T4p072` | NrdH glutaredoxin | 102 | none | none | pending | — |
| 55.8 | `T4p073` | gp55.8 conserved hypothetical predicted membrane protein | 70 | TM 12–41 | TM 15–24, TM 26–38 | pending | span_count |
| nrdG | `T4p074` | anaerobic ribonucleotide reductase small subunit | 156 | none | none | pending | — |
| mobC | `T4p075` | homing endonuclease | 210 | none | none | pending | — |
| nrdD | `T4p076` | anaerobic ribonucleoside reductase large subunit | 605 | none | none | pending | — |
| I-TevII | `T4p077` | I-TevII homing endonuclease | 258 | none | none | pending | — |
| 49 | `T4p078` | endonuclease VII | 157 | none | none | pending | — |
| 49 | `T4p079` | endonuclease VII | 105 | none | none | pending | — |
| pin | `T4p080` | inhibitor of host Lon protease | 161 | none | none | pending | — |
| 49.1 | `T4p081` | gp49.1 conserved protein of unknown function | 51 | none | none | pending | — |
| 49.2 | `T4p082` | ribonucleotide reductase | 106 | none | none | pending | — |
| 49.3 | `T4p083` | gp49.3 hypothetical protein | 102 | none | none | pending | — |
| nrdC | `T4p084` | NrdC thioredoxin | 87 | none | none | pending | — |
| nrdC.1 | `T4p085` | hypothetical protein | 80 | none | none | pending | — |
| nrdC.2 | `T4p086` | hypothetical protein | 104 | none | none | pending | — |
| nrdC.3 | `T4p087` | hypothetical protein | 308 | none | none | pending | — |
| nrdC.4 | `T4p088` | hypothetical protein | 333 | none | none | pending | — |
| nrdC.5 | `T4p089` | NrdC.5 conserved hypothetical protein | 340 | none | none | pending | — |
| nrdC.6 | `T4p090` | hypothetical protein | 275 | none | none | pending | — |
| nrdC.7 | `T4p091` | NrdC.7 conserved hypothetical, predicted membrane protein | 133 | TM 9–27, TM 103–129 | TM 9–24, TM 103–126 | pending | — |
| nrdC.8 | `T4p092` | hypothetical protein | 175 | none | none | pending | — |
| nrdC.9 | `T4p093` | NrdC.9 conserved hypothetical protein | 100 | none | none | pending | — |
| nrdC.10 | `T4p094` | hypothetical protein | 325 | none | none | pending | — |
| nrdC.11 | `T4p095` | nucleotidyltransferase | 336 | none | none | pending | — |
| mobD | `T4p096` | homing endonuclease | 259 | none | none | pending | — |
| mobD.1 | `T4p097` | MobD.1 conserved hypothetical protein | 181 | none | none | pending | — |
| mobD.2 | `T4p098` | MobD.2 conserved hypothetical protein | 34 | none | SP 1–33 | pending | signal_peptide |
| mobD.2a | `T4p099` | MobD.2a hypothetical protein | 38 | none | none | pending | — |
| mobD.3 | `T4p100` | MobD.3 hypothetical protein | 64 | none | none | pending | — |
| mobD.4 | `T4p101` | molybdopterin-guanine dinucleotide biosynthesis protein MobD | 60 | none | none | pending | — |
| mobD.5 | `T4p102` | MobD.5 hypothetical protein | 62 | none | none | pending | — |
| rI.-1 | `T4p103` | starvation-inducible transcriptional regulator | 128 | none | none | pending | — |
| rI | `T4p104` | lysis inhibition | 97 | SP 1–24 | SP 1–24 | pending | — |
| rI.1 | `T4p105` | rI.1 conserved hypothetical protein | 70 | none | none | pending | — |
| tk | `T4p106` | thymidine kinase | 193 | SP 1–22 | none | pending | signal_peptide |
| tk.1 | `T4p107` | Tk.1 conserved hypothetical protein | 62 | none | none | pending | — |
| tk.2 | `T4p108` | Tk.2 conserved hypothetical protein | 61 | none | none | pending | — |
| tk.3 | `T4p109` | Tk.2 conserved hypothetical protein | 70 | none | none | pending | — |
| tk.4 | `T4p110` | phosphatase | 155 | none | none | pending | — |
| vs | `T4p111` | valyl tRNA synthetase modifier | 115 | SP 1–20 | SP 1–18 | pending | signal_peptide_boundary |
| vs.1 | `T4p112` | hypothetical protein | 181 | SP 1–18 | SP 1–18 | pending | — |
| regB | `T4p113` | endoribonuclease | 153 | none | none | pending | — |
| vs.3 | `T4p114` | Vs.3 conserved hypothetical protein | 92 | none | none | pending | — |
| vs.4 | `T4p115` | Vs.4 conserved hypothetical protein | 88 | none | none | pending | — |
| vs.5 | `T4p116` | Vs.5 conserved hypothetical protein | 58 | none | none | pending | — |
| vs.6 | `T4p117` | autonomous glycyl radical cofactor GrcA | 120 | none | none | pending | — |
| vs.7 | `T4p118` | hypothetical protein | 109 | none | none | pending | — |
| vs.8 | `T4p119` | hypothetical protein | 219 | none | none | pending | — |
| denV | `T4p120` | endonuclease V N-glycosylase UV repair enzyme | 138 | none | none | pending | — |
| ipII | `T4p121` | internal virion protein | 100 | none | none | pending | — |
| ipIII | `T4p122` | internal virion protein | 193 | none | none | pending | — |
| e | `T4p123` | glycoside hydrolase family protein | 164 | none | none | pending | — |
| nudE | `T4p124` | nudix hydrolase | 151 | none | none | pending | — |
| e.2 | `T4p125` | hypothetical protein | 102 | TM 78–96 | TM 77–96 | pending | n_terminal_side |
| e.3 | `T4p126` | hypothetical protein | 120 | TM 12–37, TM 57–77 | TM 17–37, TM 60–75 | pending | span_boundaries(max_shift=5) |
| e.4 | `T4p127` | hypothetical protein | 130 | TM 21–45, TM 57–82 | TM 28–48, TM 56–78 | pending | span_boundaries(max_shift=7) |
| e.5 | `T4p128` | e.5 conserved hypothetical protein | 202 | none | none | pending | — |
| e.6 | `T4p129` | e.6 conserved hypothetical protein | 197 | none | none | pending | — |
| e.7 | `T4p130` | e.7 hypothetical protein | 111 | none | none | pending | — |
| e.8 | `T4p131` | e.8 conserved hypothetical protein | 87 | none | none | pending | — |
| segB | `T4p132` | homing endonuclease | 221 | none | none | pending | — |
| trna.2 | `T4p133` | Trna.2 conserved hypothetical protein | 95 | none | none | pending | — |
| trna.3 | `T4p134` | Trna.3 conserved hypothetical protein | 136 | none | none | pending | — |
| trna.4 | `T4p135` | hypothetical protein | 61 | TM 12–33, TM 39–57 | TM 11–31, TM 38–54 | pending | — |
| ipI | `T4p136` | internal virion protein | 95 | none | none | pending | — |
| 57B | `T4p137` | RNA ligase | 152 | none | none | pending | — |
| 57A | `T4p138` | tail fiber chaperone | 80 | none | none | pending | — |
| 1 | `T4p139` | deoxynucleoside monophosphate kinase | 241 | none | none | pending | — |
| 3 | `T4p140` | tail protein | 176 | none | none | pending | — |
| 2 | `T4p141` | DNA end protector | 274 | none | none | pending | — |
| 4 | `T4p142` | head closure | 150 | none | none | pending | — |
| 53 | `T4p143` | baseplate wedge subunit | 196 | none | none | pending | — |
| 5 | `T4p144` | baseplate hub subunit and tail lysozyme | 575 | none | none | pending | — |
| repEB | `T4p145` | replication initiation protein | 45 | none | none | pending | — |
| repEA | `T4p146` | replication initiation protein | 50 | none | SP 1–19 | pending | signal_peptide |
| 5.1 | `T4p147` | hypothetical protein | 164 | none | none | pending | — |
| segC | `T4p148` | homing endonuclease | 140 | none | none | pending | — |
| 5.3 | `T4p149` | gp5.3 conserved hypothetical protein | 56 | none | none | pending | — |
| 5.4 | `T4p150` | PAAR motif of membran proteins | 97 | none | none | pending | — |
| 6 | `T4p151` | baseplate wedge subunit | 660 | none | none | pending | — |
| 7 | `T4p152` | baseplate wedge subunit | 1032 | TM 882–906 | TM 879–888, TM 890–900 | pending | span_count |
| 8 | `T4p153` | baseplate wedge subunit | 334 | none | none | pending | — |
| 9 | `T4p154` | baseplate wedge tail fiber protein connector | 288 | none | none | pending | — |
| 10 | `T4p155` | baseplate wedge subunit | 602 | none | none | pending | — |
| 11 | `T4p156` | baseplate wedge subunit | 219 | none | SP 1–22 | pending | signal_peptide |
| 12 | `T4p157` | tail collar fiber protein | 527 | none | none | pending | — |
| wac | `T4p158` | fibritin neck whisker | 487 | none | none | pending | — |
| 13 | `T4p159` | head-tail adaptor Ad2 | 309 | none | none | pending | — |
| 14 | `T4p160` | head closure Hc2 | 256 | none | none | pending | — |
| 15 | `T4p161` | tail sheath stabilizer | 272 | none | none | pending | — |
| 16 | `T4p162` | terminase small subunit | 164 | none | none | pending | — |
| 17 | `T4p163` | terminase large subunit | 610 | none | none | pending | — |
| 17 | `T4p164` | terminase large subunit | 523 | none | none | pending | — |
| 17 | `T4p165` | terminase large subunit | 505 | none | none | pending | — |
| 17 | `T4p166` | large terminase protein | 416 | none | none | pending | — |
| 18 | `T4p167` | tail sheath | 659 | none | none | pending | — |
| 19 | `T4p168` | tail protein | 163 | none | none | pending | — |
| 20 | `T4p169` | portal protein | 524 | none | none | pending | — |
| 67 | `T4p170` | prohead | 80 | none | none | pending | — |
| 68 | `T4p171` | head scaffolding protein | 141 | none | none | pending | — |
| 21 | `T4p172` | head maturation protease | 212 | none | none | pending | — |
| 21 | `T4p173` | head maturation protease | 190 | none | none | pending | — |
| 22 | `T4p174` | head scaffolding protein | 269 | none | none | pending | — |
| 23 | `T4p175` | major head protein | 521 | none | none | pending | — |
| segD | `T4p176` | homing endonuclease | 223 | none | none | pending | — |
| 24 | `T4p177` | capsid vertex protein | 427 | none | none | pending | — |
| rnlB | `T4p178` | RNA ligase | 334 | none | none | pending | — |
| 24.2 | `T4p179` | gp24.2 conserved hypothetical protein | 92 | none | none | pending | — |
| 24.3 | `T4p180` | gp24.3 conserved hypothetical protein | 56 | none | none | pending | — |
| hoc | `T4p181` | Hoc-like head decoration | 376 | none | none | pending | — |
| inh | `T4p182` | minor head protein inhibitor of protease | 226 | none | none | pending | — |
| segE | `T4p183` | homing endonuclease | 205 | none | none | pending | — |
| uvsW | `T4p184` | DNA helicase | 587 | none | none | pending | — |
| uvsY.-2 | `T4p185` | hypothetical protein | 55 | none | none | pending | — |
| uvsY.-1 | `T4p186` | UvsY.-1 conserved hypothetical protein | 74 | none | none | pending | — |
| uvsY | `T4p187` | UvsY-like recombination mediator | 137 | none | none | pending | — |
| 25 | `T4p188` | baseplate wedge subunit | 132 | none | none | pending | — |
| 26 | `T4p189` | baseplate hub | 208 | none | none | pending | — |
| 26' | `T4p190` | baseplate hub | 95 | none | none | pending | — |
| 51 | `T4p191` | baseplate hub assembly protein | 249 | none | none | pending | — |
| 27 | `T4p192` | baseplate hub | 391 | none | none | pending | — |
| 28 | `T4p193` | baseplate hub distal subunit | 177 | none | none | pending | — |
| 29 | `T4p194` | baseplate hub subunit and tail length | 590 | TM 239–258 | TM 237–246 | pending | span_boundaries(max_shift=12) |
| 48 | `T4p195` | baseplate tail tube cap | 364 | none | none | pending | — |
| 54 | `T4p196` | tail tube | 320 | none | none | pending | — |
| alt.-3 | `T4p197` | Alt.-3 conserved hypothetical protein | 96 | none | none | pending | — |
| alt.-2 | `T4p198` | Alt.-2 hypothetical protein | 67 | none | none | pending | — |
| alt.-1 | `T4p199` | Alt.-1 hypothetical protein | 61 | none | none | pending | — |
| alt | `T4p200` | Alt-like RNA polymerase ADP-ribosyltransferase | 682 | none | none | pending | — |
| alt.1 | `T4p201` | Alt.1 conserved hypothetical protein | 62 | none | none | pending | — |
| 30 | `T4p202` | DNA ligase | 487 | none | none | pending | — |
| 30.1 | `T4p203` | DUF3045 domain-containing protein | 89 | none | none | pending | — |
| 30.2 | `T4p204` | hypothetical protein | 278 | none | none | pending | — |
| 30.3 | `T4p205` | hypothetical protein | 152 | none | none | pending | — |
| 30.3' | `T4p206` | gp30.3' hypothetical protein | 75 | none | none | pending | — |
| 30.4 | `T4p207` | gp30.4 conserved hypothetical protein | 68 | none | none | pending | — |
| 30.5 | `T4p208` | gp30.5 hypothetical protein | 65 | none | none | pending | — |
| 30.6 | `T4p209` | gp30.6 conserved hypothetical protein | 95 | none | none | pending | — |
| 30.7 | `T4p210` | gp30.7 conserved hypothetical protein | 121 | none | none | pending | — |
| 30.8 | `T4p211` | gp30.8 conserved hypothetical protein | 110 | none | none | pending | — |
| 30.9 | `T4p212` | gp30.9 conserved hypothetical protein | 58 | none | none | pending | — |
| rIII | `T4p213` | lysis inhibition; accessory protein | 82 | none | none | pending | — |
| 31 | `T4p214` | head morphogenesis | 111 | none | none | pending | — |
| 31.1 | `T4p215` | SH3 beta-barrel fold-containing protein | 102 | none | none | pending | — |
| 31.2 | `T4p216` | hypothetical protein | 78 | none | none | pending | — |
| cd | `T4p217` | dCMP deaminase | 193 | none | none | pending | — |
| cd.1 | `T4p218` | Cd.1 hypothetical protein | 112 | none | none | pending | — |
| cd.2 | `T4p219` | Cd.2 conserved hypothetical protein | 76 | none | none | pending | — |
| cd.3 | `T4p220` | Cd.3 conserved hypothetical protein | 91 | none | none | pending | — |
| cd.4 | `T4p221` | Cd.4 conserved hypothetical protein | 66 | none | none | pending | — |
| cd.5 | `T4p222` | Cd.5 hypothetical protein | 75 | none | none | pending | — |
| pseT | `T4p223` | polynucleotide kinase | 301 | SP 1–19 | none | pending | signal_peptide |
| pseT.1 | `T4p224` | PseT.1 conserved hypothetical protein | 75 | none | none | pending | — |
| pseT.2 | `T4p225` | Rz-like spanin | 99 | SP 1–19 | unsupported | unsupported | — |
| pseT.3 | `T4p226` | Rz-like spanin | 117 | TM 6–24 | TM 6–24 | pending | n_terminal_side |
| alc | `T4p227` | inhibitor of host transcription | 167 | none | none | pending | — |
| rnlA | `T4p228` | RNA ligase and tail fiber protein attachment catalyst | 374 | none | none | pending | — |
| denA | `T4p229` | endonuclease | 144 | none | none | pending | — |
| nrdB | `T4p230` | ribonucleotide reductase class Ia beta subunit | 388 | none | none | pending | — |
| I-TevIII | `T4p231` | endonuclease | 97 | none | none | pending | — |
| nrdB.1 | `T4p232` | Nrd.1 hypothetical protein | 83 | none | none | pending | — |
| mobE | `T4p233` | homing endonuclease | 141 | TM 52–75 | none | pending | span_count |
| nrdA | `T4p234` | NrdA-like aerobic NDP reductase large subunit | 754 | none | none | pending | — |
| nrdA.1 | `T4p235` | hypothetical protein | 108 | none | none | pending | — |
| nrdA.2 | `T4p236` | NrdA.2 conserved hypothetical protein | 87 | none | none | pending | — |
| td | `T4p237` | thymidylate synthase | 286 | none | none | pending | — |
| I-TevI | `T4p238` | homing endonuclease | 245 | none | none | pending | — |
| frd | `T4p239` | dihydrofolate reductase | 193 | none | none | pending | — |
| frd.1 | `T4p240` | DUF5417 domain-containing protein | 80 | none | none | pending | — |
| frd.2 | `T4p241` | hypothetical protein | 128 | none | none | pending | — |
| frd.3 | `T4p242` | hypothetical protein | 75 | none | none | pending | — |
| 32 | `T4p243` | single strand DNA binding protein | 301 | none | none | pending | — |
| SegG | `T4p244` | homing endonuclease | 210 | none | none | pending | — |
| 59 | `T4p245` | DNA helicase loader | 217 | none | none | pending | — |
| 33 | `T4p246` | late promoter transcriptional regulator | 112 | none | none | pending | — |
| dsbA | `T4p247` | transcriptional regulator | 89 | none | none | pending | — |
| rnh | `T4p248` | RnaseH | 305 | none | none | pending | — |
| 34 | `T4p249` | tail fiber protein proximal subunit | 1289 | none | none | pending | — |
| 35 | `T4p250` | long tail fiber protein proximal connector | 372 | none | none | pending | — |
| 36 | `T4p251` | hinge connector of long tail fiber protein distal connector | 221 | none | none | pending | — |
| 37 | `T4p252` | long tail fiber protein distal subunit | 1026 | none | none | pending | — |
| 38 | `T4p253` | tail fiber assembly | 183 | none | none | pending | — |
| t | `T4p254` | holin | 218 | TM 31–49 | TM 30–49 | pending | n_terminal_side |
| asiA | `T4p255` | anti-sigma factor | 90 | none | none | pending | — |
| asiA.1 | `T4p256` | AsiA.1 hypothetical protein | 50 | none | none | pending | — |
| arn | `T4p257` | inhibitor of MrcBC restriction | 92 | none | none | pending | — |
| arn.1 | `T4p258` | hypothetical protein | 43 | none | none | pending | — |
| arn.2 | `T4p259` | hypothetical protein | 98 | none | none | pending | — |
| arn.3 | `T4p260` | Arn.3 conserved hypothetical protein | 152 | none | none | pending | — |
| arn.4 | `T4p261` | Arn.4 conserved hypothetical protein | 68 | none | none | pending | — |
| motA | `T4p262` | MotA-like activator of middle period transcription | 211 | none | none | pending | — |
| motA.1 | `T4p263` | MotA.1 hypothetical predicted periplasmic protein | 49 | TM 12–35 | SP 1–11 | pending | span_count, signal_peptide |
| 52 | `T4p264` | DNA topoisomerase II | 442 | none | none | pending | — |
| 52.1 | `T4p265` | gp52.1 conserved hypothetical predicted membrane protein | 46 | TM 12–34 | SP 1–18 | pending | span_count, signal_peptide |
| ac | `T4p266` | Ac acridine resistance protein | 51 | SP 1–36 | TM 6–23, TM 34–48 | pending | span_count, signal_peptide |
| stp | `T4p267` | activator of host PrrC lysyl-tRNA endonuclease | 26 | none | none | pending | — |
| ndd | `T4p268` | Ndd-like nucleoid disruption protein | 151 | none | none | pending | — |
| ndd.1 | `T4p269` | hypothetical protein | 71 | none | none | pending | — |
| ndd.2 | `T4p270` | Ndd.2 hypothetical predicted outer membrane protein | 36 | TM 7–26 | SP 1–18 | pending | span_count, signal_peptide |
| ndd.2a | `T4p271` | periplasmic protein | 40 | SP 1–17 | TM 2–21 | pending | span_count, signal_peptide |
| ndd.3 | `T4p272` | Ndd.3 hypothetical predicted inner membrane protein | 26 | TM 6–23 | SP 1–22 | pending | span_count, signal_peptide |
| ndd.4 | `T4p273` | Ndd.4 hypothetical predicted inner membrane | 42 | TM 12–39 | TM 16–35 | pending | span_boundaries(max_shift=4) |
| ndd.5 | `T4p274` | outer membrane protein | 32 | TM 7–29 | TM 7–25 | pending | span_boundaries(max_shift=4) |
| ndd.6 | `T4p275` | outer membrane protein | 28 | TM 6–25 | SP 1–27 | pending | span_count, signal_peptide |
| denB | `T4p276` | DenB-like DNA endonuclease IV | 185 | none | none | pending | — |
| denB.1 | `T4p277` | DenB.1 hypothetical protein | 64 | none | none | pending | — |
| rIIB | `T4p278` | RIIB lysis inhibitor | 312 | none | none | pending | — |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org T4 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `T4`; or locally `python3 scripts/rerun.py --org T4`.

## Validation
`verification.json`: 24 pass, 0 fail, 2 pending of 26 checks. Pending: all batches complete: TOPCONS2/b001.job.json:submitted; TOPCONS2 coverage of eligible proteins: 0/277 eligible (278 in inventory); {'pending': 277, 'unsupported': 1}.
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org T4     # skips files already present
python3 scripts/02_inventory.py --org T4
python3 scripts/03_run_phobius.py --org T4      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org T4    # resumable
python3 scripts/04_run_topcons.py --org T4      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org T4 && python3 scripts/08_build_atlas.py --org T4
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org T4
python3 scripts/rerun.py --org T4 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
