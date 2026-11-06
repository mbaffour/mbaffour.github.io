# Enterobacteria phage T4 — membrane topology & charge lab reference

Open **`T4_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

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
| TOPCONS2 | 277 / 277 ({'complete': 277, 'unsupported': 1}) | `T4|T4p225`: unsupported residue(s) X not in the TOPCONS2 alphabet (sequence not altered) |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: cached: 256, newrun: 21. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 5 records.

## Summary
- 23 proteins with ≥1 predicted membrane span (any main method); 21 with a predicted signal peptide; 1 with DeepTMHMM β-type states; 31 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| rIIA | `T4p001` | RIIA lysis inhibitor | 725 | none | none | none | — |
| rIIA.1 | `T4p002` | rIIA.1 hypothetical protein | 67 | none | none | none | — |
| 60 | `T4p003` | DNA topoisomerase II | 160 | none | none | none | — |
| 60.1 | `T4p004` | gp60.1 hypothetical protein | 126 | none | none | none | — |
| mobA | `T4p005` | homing endonuclease | 37 | none | none | none | — |
| 39 | `T4p006` | DNA topoisomerase II large subunit | 516 | none | none | none | — |
| 39.1 | `T4p007` | gp39.1 hypothetical protein | 65 | none | SP 1–10 | none | signal_peptide |
| 39.2 | `T4p008` | FmdB-like transcriptional regulator | 45 | none | none | none | — |
| goF | `T4p009` | hypothetical protein | 141 | none | none | none | — |
| cef | `T4p010` | cef modifier of supressor tRNAs | 71 | none | none | none | — |
| motB | `T4p011` | MotB-like transcriptional regulator | 162 | none | none | none | — |
| motB.1 | `T4p012` | hypothetical protein | 119 | TM 38–57 | none | none | span_count |
| motB.2 | `T4p013` | hypothetical protein | 166 | none | none | none | — |
| dexA | `T4p014` | exonuclease | 227 | none | none | none | — |
| dexA.1 | `T4p015` | DexA.1 hypothetical protein | 80 | none | none | none | — |
| dexA.2 | `T4p016` | dextranase | 81 | none | none | none | — |
| dda | `T4p017` | Dda-like helicase | 439 | none | none | none | — |
| dda.1 | `T4p018` | Dda.1 hypothetical protein | 103 | none | none | none | — |
| srd | `T4p019` | Srd anti-sigma factor | 248 | none | none | none | — |
| modA | `T4p020` | RNA polymerase ADP-ribosylase | 200 | none | none | none | — |
| modB | `T4p021` | RNA polymerase ADP-ribosylase | 207 | none | none | none | — |
| modA.2 | `T4p022` | hypothetical protein | 60 | none | none | none | — |
| modA.3 | `T4p023` | Mrh transcription modulator under heat shock | 156 | none | none | none | — |
| modA.4 | `T4p024` | ModA.4 hypothetical protein | 54 | none | none | none | — |
| srh | `T4p025` | decoy of host sigma32 | 67 | none | none | none | — |
| mrh | `T4p026` | Mrh transcription modulator under heat shock | 161 | none | none | none | — |
| mrh.1 | `T4p027` | Mrh.1 hypothetical protein | 113 | none | none | none | — |
| mrh.2 | `T4p028` | Mrh.2 hypothetical protein | 68 | none | none | none | — |
| soc | `T4p029` | virion structural protein | 80 | none | none | none | — |
| segF | `T4p030` | SegF homing endonuclease | 224 | none | none | none | — |
| 56 | `T4p031` | dUTPase | 171 | none | none | none | — |
| dam | `T4p032` | Dam family site-specific DNA-(adenine-N6)-methyltransferase | 259 | none | none | none | — |
| 61 | `T4p033` | DNA primase | 342 | none | none | none | — |
| 61.1 | `T4p034` | gp61.1 hypothetical protein | 54 | none | none | none | — |
| 61.2 | `T4p035` | gp61.2 hypothetical protein | 208 | none | none | none | — |
| sp | `T4p036` | spackle periplasmic | 97 | SP 1–22 | SP 1–22 | SP 1–22 | — |
| 61.4 | `T4p037` | gp61.4 hypothetical protein | 85 | none | none | none | — |
| dmd | `T4p038` | Dmd discriminator of mRNA degradation | 60 | none | none | none | — |
| 41 | `T4p039` | AAA family ATPase | 475 | none | none | none | — |
| 40 | `T4p040` | head vertex assembly chaperone | 114 | none | none | none | — |
| uvsX | `T4p041` | recombinase | 391 | none | none | none | — |
| segA | `T4p042` | homing endonuclease | 221 | none | none | none | — |
| b-gt | `T4p043` | beta-glucosyltransferase | 351 | none | none | none | — |
| 42 | `T4p044` | thymidylate synthase | 246 | none | none | none | — |
| imm | `T4p045` | immunity to superinfection | 83 | TM 6–29, TM 41–64 | TM 9–29, TM 39–48, TM 50–61 | TM 6–26, TM 41–61 | span_count |
| imm.1 | `T4p046` | iduronate sulfatase | 125 | SP 1–17 | SP 1–14 | SP 1–21 | signal_peptide_boundary |
| 43 | `T4p047` | DNA polymerase | 898 | none | none | none | — |
| regA | `T4p048` | translation repressor | 122 | none | none | none | — |
| 62 | `T4p049` | clamp loader of DNA polymerase | 187 | none | none | none | — |
| 44 | `T4p050` | clamp loader of DNA polymerase | 319 | none | none | none | — |
| 45 | `T4p051` | DNA polymerase processivity factor | 228 | none | none | none | — |
| rpbA | `T4p052` | RNA polymerase binding | 129 | none | none | none | — |
| 45.2 | `T4p053` | protein GP45.2 | 62 | none | none | none | — |
| 46 | `T4p054` | SbcC-like subunit of palindrome specific endonuclease | 560 | none | none | none | — |
| 46.1 | `T4p055` | DUF5487 family protein | 68 | none | none | none | — |
| 46.2 | `T4p056` | gp46.2 hypothetical protein | 87 | none | none | none | — |
| 47 | `T4p057` | SbcD-like subunit of palindrome specific endonuclease | 339 | none | none | none | — |
| 47.1 | `T4p058` | gp47.1 hypothetical predicted membrane protein | 46 | SP 1–19 | SP 1–45 | TM 2–22, TM 25–45 | span_count, signal_peptide, signal_peptide_boundary |
| a-gt | `T4p059` | alpha-glucosyltransferase | 400 | none | none | none | — |
| mobB | `T4p060` | homing endonuclease | 264 | none | none | none | — |
| a-gt.2 | `T4p061` | a-gt.2 hypothetical protein | 63 | none | none | none | — |
| a-gt.3 | `T4p062` | a-gt.3 hypothetical protein | 67 | none | none | none | — |
| a-gt.4 | `T4p063` | a-gt.4 family protein | 105 | none | none | none | — |
| a-gt.5 | `T4p064` | a-gt.5 hypothetical protein | 72 | none | none | none | — |
| 55 | `T4p065` | RNA polymerase sigma factor | 185 | none | none | none | — |
| 55.1 | `T4p066` | gp55.1 hypothetical protein | 87 | none | none | none | — |
| 55.2 | `T4p067` | gp55.2 hypothetical protein | 108 | none | none | none | — |
| 55.3 | `T4p068` | gp55.3 hypothetical protein | 79 | none | none | none | — |
| 55.4 | `T4p069` | gp55.4 conserved hypothetical protein | 43 | none | none | none | — |
| 55.5 | `T4p070` | gp55.5 conserved protein of unknown function | 97 | none | none | none | — |
| 55.6 | `T4p071` | gp55.6 conserved hypothetical protein | 60 | none | none | none | — |
| nrdH | `T4p072` | NrdH glutaredoxin | 102 | none | none | none | — |
| 55.8 | `T4p073` | gp55.8 conserved hypothetical predicted membrane protein | 70 | TM 12–41 | TM 15–24, TM 26–38 | TM 15–35 | span_count, n_terminal_side |
| nrdG | `T4p074` | anaerobic ribonucleotide reductase small subunit | 156 | none | none | none | — |
| mobC | `T4p075` | homing endonuclease | 210 | none | none | none | — |
| nrdD | `T4p076` | anaerobic ribonucleoside reductase large subunit | 605 | none | none | none | — |
| I-TevII | `T4p077` | I-TevII homing endonuclease | 258 | none | none | none | — |
| 49 | `T4p078` | endonuclease VII | 157 | none | none | none | — |
| 49 | `T4p079` | endonuclease VII | 105 | none | none | none | — |
| pin | `T4p080` | inhibitor of host Lon protease | 161 | none | none | none | — |
| 49.1 | `T4p081` | gp49.1 conserved protein of unknown function | 51 | none | none | none | — |
| 49.2 | `T4p082` | ribonucleotide reductase | 106 | none | none | none | — |
| 49.3 | `T4p083` | gp49.3 hypothetical protein | 102 | none | none | none | — |
| nrdC | `T4p084` | NrdC thioredoxin | 87 | none | none | none | — |
| nrdC.1 | `T4p085` | hypothetical protein | 80 | none | none | none | — |
| nrdC.2 | `T4p086` | hypothetical protein | 104 | none | none | none | — |
| nrdC.3 | `T4p087` | hypothetical protein | 308 | none | none | none | — |
| nrdC.4 | `T4p088` | hypothetical protein | 333 | none | none | none | — |
| nrdC.5 | `T4p089` | NrdC.5 conserved hypothetical protein | 340 | none | none | none | — |
| nrdC.6 | `T4p090` | hypothetical protein | 275 | none | none | none | — |
| nrdC.7 | `T4p091` | NrdC.7 conserved hypothetical, predicted membrane protein | 133 | TM 9–27, TM 103–129 | TM 9–24, TM 103–126 | TM 9–29, TM 106–126 | span_boundaries(max_shift=5) |
| nrdC.8 | `T4p092` | hypothetical protein | 175 | none | none | none | — |
| nrdC.9 | `T4p093` | NrdC.9 conserved hypothetical protein | 100 | none | none | none | — |
| nrdC.10 | `T4p094` | hypothetical protein | 325 | none | none | none | — |
| nrdC.11 | `T4p095` | nucleotidyltransferase | 336 | none | none | none | — |
| mobD | `T4p096` | homing endonuclease | 259 | none | none | none | — |
| mobD.1 | `T4p097` | MobD.1 conserved hypothetical protein | 181 | none | none | none | — |
| mobD.2 | `T4p098` | MobD.2 conserved hypothetical protein | 34 | none | SP 1–33 | none | signal_peptide |
| mobD.2a | `T4p099` | MobD.2a hypothetical protein | 38 | none | none | none | — |
| mobD.3 | `T4p100` | MobD.3 hypothetical protein | 64 | none | none | none | — |
| mobD.4 | `T4p101` | molybdopterin-guanine dinucleotide biosynthesis protein MobD | 60 | none | none | none | — |
| mobD.5 | `T4p102` | MobD.5 hypothetical protein | 62 | none | none | none | — |
| rI.-1 | `T4p103` | starvation-inducible transcriptional regulator | 128 | none | none | none | — |
| rI | `T4p104` | lysis inhibition | 97 | SP 1–24 | SP 1–24 | SP 1–24 | — |
| rI.1 | `T4p105` | rI.1 conserved hypothetical protein | 70 | none | none | none | — |
| tk | `T4p106` | thymidine kinase | 193 | SP 1–22 | none | none | signal_peptide |
| tk.1 | `T4p107` | Tk.1 conserved hypothetical protein | 62 | none | none | none | — |
| tk.2 | `T4p108` | Tk.2 conserved hypothetical protein | 61 | none | none | none | — |
| tk.3 | `T4p109` | Tk.2 conserved hypothetical protein | 70 | none | none | none | — |
| tk.4 | `T4p110` | phosphatase | 155 | none | none | none | — |
| vs | `T4p111` | valyl tRNA synthetase modifier | 115 | SP 1–20 | SP 1–18 | SP 1–21 | signal_peptide_boundary |
| vs.1 | `T4p112` | hypothetical protein | 181 | SP 1–18 | SP 1–18 | SP 1–21 | signal_peptide_boundary |
| regB | `T4p113` | endoribonuclease | 153 | none | none | none | — |
| vs.3 | `T4p114` | Vs.3 conserved hypothetical protein | 92 | none | none | none | — |
| vs.4 | `T4p115` | Vs.4 conserved hypothetical protein | 88 | none | none | none | — |
| vs.5 | `T4p116` | Vs.5 conserved hypothetical protein | 58 | none | none | none | — |
| vs.6 | `T4p117` | autonomous glycyl radical cofactor GrcA | 120 | none | none | none | — |
| vs.7 | `T4p118` | hypothetical protein | 109 | none | none | none | — |
| vs.8 | `T4p119` | hypothetical protein | 219 | none | none | none | — |
| denV | `T4p120` | endonuclease V N-glycosylase UV repair enzyme | 138 | none | none | none | — |
| ipII | `T4p121` | internal virion protein | 100 | none | none | none | — |
| ipIII | `T4p122` | internal virion protein | 193 | none | none | none | — |
| e | `T4p123` | glycoside hydrolase family protein | 164 | none | none | none | — |
| nudE | `T4p124` | nudix hydrolase | 151 | none | none | none | — |
| e.2 | `T4p125` | hypothetical protein | 102 | TM 78–96 | TM 77–96 | TM 76–96 | n_terminal_side |
| e.3 | `T4p126` | hypothetical protein | 120 | TM 12–37, TM 57–77 | TM 17–37, TM 60–75 | TM 18–38, TM 57–77 | span_boundaries(max_shift=6) |
| e.4 | `T4p127` | hypothetical protein | 130 | TM 21–45, TM 57–82 | TM 28–48, TM 56–78 | TM 24–44, TM 57–77 | span_boundaries(max_shift=7) |
| e.5 | `T4p128` | e.5 conserved hypothetical protein | 202 | none | none | none | — |
| e.6 | `T4p129` | e.6 conserved hypothetical protein | 197 | none | none | none | — |
| e.7 | `T4p130` | e.7 hypothetical protein | 111 | none | none | none | — |
| e.8 | `T4p131` | e.8 conserved hypothetical protein | 87 | none | none | none | — |
| segB | `T4p132` | homing endonuclease | 221 | none | none | none | — |
| trna.2 | `T4p133` | Trna.2 conserved hypothetical protein | 95 | none | none | none | — |
| trna.3 | `T4p134` | Trna.3 conserved hypothetical protein | 136 | none | none | none | — |
| trna.4 | `T4p135` | hypothetical protein | 61 | TM 12–33, TM 39–57 | TM 11–31, TM 38–54 | TM 10–30, TM 36–56 | — |
| ipI | `T4p136` | internal virion protein | 95 | none | none | none | — |
| 57B | `T4p137` | RNA ligase | 152 | none | none | none | — |
| 57A | `T4p138` | tail fiber chaperone | 80 | none | none | none | — |
| 1 | `T4p139` | deoxynucleoside monophosphate kinase | 241 | none | none | none | — |
| 3 | `T4p140` | tail protein | 176 | none | none | none | — |
| 2 | `T4p141` | DNA end protector | 274 | none | none | none | — |
| 4 | `T4p142` | head closure | 150 | none | none | none | — |
| 53 | `T4p143` | baseplate wedge subunit | 196 | none | none | none | — |
| 5 | `T4p144` | baseplate hub subunit and tail lysozyme | 575 | none | none | none | — |
| repEB | `T4p145` | replication initiation protein | 45 | none | none | none | — |
| repEA | `T4p146` | replication initiation protein | 50 | none | SP 1–19 | none | signal_peptide |
| 5.1 | `T4p147` | hypothetical protein | 164 | none | none | none | — |
| segC | `T4p148` | homing endonuclease | 140 | none | none | none | — |
| 5.3 | `T4p149` | gp5.3 conserved hypothetical protein | 56 | none | none | none | — |
| 5.4 | `T4p150` | PAAR motif of membran proteins | 97 | none | none | none | — |
| 6 | `T4p151` | baseplate wedge subunit | 660 | none | none | none | — |
| 7 | `T4p152` | baseplate wedge subunit | 1032 | TM 882–906 | TM 879–888, TM 890–900 | TM 882–902 | span_count, n_terminal_side |
| 8 | `T4p153` | baseplate wedge subunit | 334 | none | none | none | — |
| 9 | `T4p154` | baseplate wedge tail fiber protein connector | 288 | none | none | none | — |
| 10 | `T4p155` | baseplate wedge subunit | 602 | none | none | none | — |
| 11 | `T4p156` | baseplate wedge subunit | 219 | none | SP 1–22 | none | signal_peptide |
| 12 | `T4p157` | tail collar fiber protein | 527 | none | none | none | — |
| wac | `T4p158` | fibritin neck whisker | 487 | none | none | none | — |
| 13 | `T4p159` | head-tail adaptor Ad2 | 309 | none | none | none | — |
| 14 | `T4p160` | head closure Hc2 | 256 | none | none | none | — |
| 15 | `T4p161` | tail sheath stabilizer | 272 | none | none | none | — |
| 16 | `T4p162` | terminase small subunit | 164 | none | none | none | — |
| 17 | `T4p163` | terminase large subunit | 610 | none | none | none | — |
| 17 | `T4p164` | terminase large subunit | 523 | none | none | none | — |
| 17 | `T4p165` | terminase large subunit | 505 | none | none | none | — |
| 17 | `T4p166` | large terminase protein | 416 | none | none | none | — |
| 18 | `T4p167` | tail sheath | 659 | none | none | none | — |
| 19 | `T4p168` | tail protein | 163 | none | none | none | — |
| 20 | `T4p169` | portal protein | 524 | none | none | none | — |
| 67 | `T4p170` | prohead | 80 | none | none | none | — |
| 68 | `T4p171` | head scaffolding protein | 141 | none | none | none | — |
| 21 | `T4p172` | head maturation protease | 212 | none | none | none | — |
| 21 | `T4p173` | head maturation protease | 190 | none | none | none | — |
| 22 | `T4p174` | head scaffolding protein | 269 | none | none | none | — |
| 23 | `T4p175` | major head protein | 521 | none | none | none | — |
| segD | `T4p176` | homing endonuclease | 223 | none | none | none | — |
| 24 | `T4p177` | capsid vertex protein | 427 | none | none | none | — |
| rnlB | `T4p178` | RNA ligase | 334 | none | none | none | — |
| 24.2 | `T4p179` | gp24.2 conserved hypothetical protein | 92 | none | none | none | — |
| 24.3 | `T4p180` | gp24.3 conserved hypothetical protein | 56 | none | none | none | — |
| hoc | `T4p181` | Hoc-like head decoration | 376 | none | none | none | — |
| inh | `T4p182` | minor head protein inhibitor of protease | 226 | none | none | none | — |
| segE | `T4p183` | homing endonuclease | 205 | none | none | none | — |
| uvsW | `T4p184` | DNA helicase | 587 | none | none | none | — |
| uvsY.-2 | `T4p185` | hypothetical protein | 55 | none | none | none | — |
| uvsY.-1 | `T4p186` | UvsY.-1 conserved hypothetical protein | 74 | none | none | none | — |
| uvsY | `T4p187` | UvsY-like recombination mediator | 137 | none | none | none | — |
| 25 | `T4p188` | baseplate wedge subunit | 132 | none | none | none | — |
| 26 | `T4p189` | baseplate hub | 208 | none | none | none | — |
| 26' | `T4p190` | baseplate hub | 95 | none | none | none | — |
| 51 | `T4p191` | baseplate hub assembly protein | 249 | none | none | none | — |
| 27 | `T4p192` | baseplate hub | 391 | none | none | none | — |
| 28 | `T4p193` | baseplate hub distal subunit | 177 | none | none | none | — |
| 29 | `T4p194` | baseplate hub subunit and tail length | 590 | TM 239–258 | TM 237–246 | TM 233–253 | n_terminal_side |
| 48 | `T4p195` | baseplate tail tube cap | 364 | none | none | none | — |
| 54 | `T4p196` | tail tube | 320 | none | none | none | — |
| alt.-3 | `T4p197` | Alt.-3 conserved hypothetical protein | 96 | none | none | none | — |
| alt.-2 | `T4p198` | Alt.-2 hypothetical protein | 67 | none | none | none | — |
| alt.-1 | `T4p199` | Alt.-1 hypothetical protein | 61 | none | none | none | — |
| alt | `T4p200` | Alt-like RNA polymerase ADP-ribosyltransferase | 682 | none | none | none | — |
| alt.1 | `T4p201` | Alt.1 conserved hypothetical protein | 62 | none | none | none | — |
| 30 | `T4p202` | DNA ligase | 487 | none | none | none | — |
| 30.1 | `T4p203` | DUF3045 domain-containing protein | 89 | none | none | none | — |
| 30.2 | `T4p204` | hypothetical protein | 278 | none | none | none | — |
| 30.3 | `T4p205` | hypothetical protein | 152 | none | none | none | — |
| 30.3' | `T4p206` | gp30.3' hypothetical protein | 75 | none | none | none | — |
| 30.4 | `T4p207` | gp30.4 conserved hypothetical protein | 68 | none | none | none | — |
| 30.5 | `T4p208` | gp30.5 hypothetical protein | 65 | none | none | none | — |
| 30.6 | `T4p209` | gp30.6 conserved hypothetical protein | 95 | none | none | none | — |
| 30.7 | `T4p210` | gp30.7 conserved hypothetical protein | 121 | none | none | none | — |
| 30.8 | `T4p211` | gp30.8 conserved hypothetical protein | 110 | none | none | none | — |
| 30.9 | `T4p212` | gp30.9 conserved hypothetical protein | 58 | none | none | none | — |
| rIII | `T4p213` | lysis inhibition; accessory protein | 82 | none | none | none | — |
| 31 | `T4p214` | head morphogenesis | 111 | none | none | none | — |
| 31.1 | `T4p215` | SH3 beta-barrel fold-containing protein | 102 | none | none | none | — |
| 31.2 | `T4p216` | hypothetical protein | 78 | none | none | none | — |
| cd | `T4p217` | dCMP deaminase | 193 | none | none | none | — |
| cd.1 | `T4p218` | Cd.1 hypothetical protein | 112 | none | none | none | — |
| cd.2 | `T4p219` | Cd.2 conserved hypothetical protein | 76 | none | none | none | — |
| cd.3 | `T4p220` | Cd.3 conserved hypothetical protein | 91 | none | none | none | — |
| cd.4 | `T4p221` | Cd.4 conserved hypothetical protein | 66 | none | none | none | — |
| cd.5 | `T4p222` | Cd.5 hypothetical protein | 75 | none | none | none | — |
| pseT | `T4p223` | polynucleotide kinase | 301 | SP 1–19 | none | none | signal_peptide |
| pseT.1 | `T4p224` | PseT.1 conserved hypothetical protein | 75 | none | none | none | — |
| pseT.2 | `T4p225` | Rz-like spanin | 99 | SP 1–19 | unsupported | unsupported | — |
| pseT.3 | `T4p226` | Rz-like spanin | 117 | TM 6–24 | TM 6–24 | TM 4–24 | n_terminal_side |
| alc | `T4p227` | inhibitor of host transcription | 167 | none | none | none | — |
| rnlA | `T4p228` | RNA ligase and tail fiber protein attachment catalyst | 374 | none | none | none | — |
| denA | `T4p229` | endonuclease | 144 | none | none | none | — |
| nrdB | `T4p230` | ribonucleotide reductase class Ia beta subunit | 388 | none | none | none | — |
| I-TevIII | `T4p231` | endonuclease | 97 | none | none | none | — |
| nrdB.1 | `T4p232` | Nrd.1 hypothetical protein | 83 | none | none | none | — |
| mobE | `T4p233` | homing endonuclease | 141 | TM 52–75 | none | none | span_count |
| nrdA | `T4p234` | NrdA-like aerobic NDP reductase large subunit | 754 | none | none | none | — |
| nrdA.1 | `T4p235` | hypothetical protein | 108 | none | none | none | — |
| nrdA.2 | `T4p236` | NrdA.2 conserved hypothetical protein | 87 | none | none | none | — |
| td | `T4p237` | thymidylate synthase | 286 | none | none | none | — |
| I-TevI | `T4p238` | homing endonuclease | 245 | none | none | none | — |
| frd | `T4p239` | dihydrofolate reductase | 193 | none | none | none | — |
| frd.1 | `T4p240` | DUF5417 domain-containing protein | 80 | none | none | none | — |
| frd.2 | `T4p241` | hypothetical protein | 128 | none | none | none | — |
| frd.3 | `T4p242` | hypothetical protein | 75 | none | none | none | — |
| 32 | `T4p243` | single strand DNA binding protein | 301 | none | none | none | — |
| SegG | `T4p244` | homing endonuclease | 210 | none | none | none | — |
| 59 | `T4p245` | DNA helicase loader | 217 | none | none | none | — |
| 33 | `T4p246` | late promoter transcriptional regulator | 112 | none | none | none | — |
| dsbA | `T4p247` | transcriptional regulator | 89 | none | none | none | — |
| rnh | `T4p248` | RnaseH | 305 | none | none | none | — |
| 34 | `T4p249` | tail fiber protein proximal subunit | 1289 | none | none | none | — |
| 35 | `T4p250` | long tail fiber protein proximal connector | 372 | none | none | none | — |
| 36 | `T4p251` | hinge connector of long tail fiber protein distal connector | 221 | none | none | none | — |
| 37 | `T4p252` | long tail fiber protein distal subunit | 1026 | none | none | none | — |
| 38 | `T4p253` | tail fiber assembly | 183 | none | none | none | — |
| t | `T4p254` | holin | 218 | TM 31–49 | TM 30–49 | TM 30–50 | n_terminal_side |
| asiA | `T4p255` | anti-sigma factor | 90 | none | none | none | — |
| asiA.1 | `T4p256` | AsiA.1 hypothetical protein | 50 | none | none | none | — |
| arn | `T4p257` | inhibitor of MrcBC restriction | 92 | none | none | none | — |
| arn.1 | `T4p258` | hypothetical protein | 43 | none | none | none | — |
| arn.2 | `T4p259` | hypothetical protein | 98 | none | none | none | — |
| arn.3 | `T4p260` | Arn.3 conserved hypothetical protein | 152 | none | none | none | — |
| arn.4 | `T4p261` | Arn.4 conserved hypothetical protein | 68 | none | none | none | — |
| motA | `T4p262` | MotA-like activator of middle period transcription | 211 | none | none | none | — |
| motA.1 | `T4p263` | MotA.1 hypothetical predicted periplasmic protein | 49 | TM 12–35 | SP 1–11 | SP 1–25, TM 27–47 | span_count, signal_peptide, signal_peptide_boundary |
| 52 | `T4p264` | DNA topoisomerase II | 442 | none | none | none | — |
| 52.1 | `T4p265` | gp52.1 conserved hypothetical predicted membrane protein | 46 | TM 12–34 | SP 1–18 | TM 10–30 | span_count, signal_peptide |
| ac | `T4p266` | Ac acridine resistance protein | 51 | SP 1–36 | TM 6–23, TM 34–48 | SP 1–30 | span_count, signal_peptide, signal_peptide_boundary |
| stp | `T4p267` | activator of host PrrC lysyl-tRNA endonuclease | 26 | none | none | none | — |
| ndd | `T4p268` | Ndd-like nucleoid disruption protein | 151 | none | none | none | — |
| ndd.1 | `T4p269` | hypothetical protein | 71 | none | none | none | — |
| ndd.2 | `T4p270` | Ndd.2 hypothetical predicted outer membrane protein | 36 | TM 7–26 | SP 1–18 | TM 4–24 | span_count, signal_peptide |
| ndd.2a | `T4p271` | periplasmic protein | 40 | SP 1–17 | TM 2–21 | TM 2–22 | span_count, signal_peptide, n_terminal_side |
| ndd.3 | `T4p272` | Ndd.3 hypothetical predicted inner membrane protein | 26 | TM 6–23 | SP 1–22 | TM 5–25 | span_count, signal_peptide |
| ndd.4 | `T4p273` | Ndd.4 hypothetical predicted inner membrane | 42 | TM 12–39 | TM 16–35 | TM 12–32 | span_boundaries(max_shift=7) |
| ndd.5 | `T4p274` | outer membrane protein | 32 | TM 7–29 | TM 7–25 | SP 1–21 | span_count, signal_peptide |
| ndd.6 | `T4p275` | outer membrane protein | 28 | TM 6–25 | SP 1–27 | TM 6–26 | span_count, signal_peptide |
| denB | `T4p276` | DenB-like DNA endonuclease IV | 185 | none | none | none | — |
| denB.1 | `T4p277` | DenB.1 hypothetical protein | 64 | none | none | none | — |
| rIIB | `T4p278` | RIIB lysis inhibitor | 312 | none | none | none | — |

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
`verification.json`: 24 pass, 1 fail, 0 pending of 25 checks.  Failures: browser layout audit: no text overlaps, no clipped text, no line crossing a label, no crossing leaders/bonds (all figures of every checked protein; 1568 proteins checked atlas-wide, all phage proteins + host sample): [["T4|T4p263", {"C_TOPCONS2": ["conn crosses text \"OUTSIDE \u00b7 non-cytoplasmic\""]}]].
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
