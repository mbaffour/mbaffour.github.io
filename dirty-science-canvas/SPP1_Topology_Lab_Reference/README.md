# Bacillus phage SPP1 — membrane topology & charge lab reference

Open **`SPP1_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.

## Source
- RefSeq **NC_004166.2**: "Bacteriophage SPP1 complete nucleotide sequence", 44,010 nt, circular; NCBI record updated 2023/01/07; taxid 10724.
- Downloaded from NCBI E-utilities on 2026-11-06 (UTC); URLs and SHA-256 in `inputs/provenance.json`.
- Scope: all **97** CDS features with a `/translation` (97 CDS features; 0 pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.
- Context: Host: Bacillus subtilis. Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions.

## Coverage
| Method | Complete / eligible | Not eligible (reason) |
|---|---|---|
| Phobius | 97 / 97 ({'complete': 97}) | — |
| DeepTMHMM | 97 / 97 ({'complete': 97}) | — |
| TOPCONS2 | 97 / 97 ({'complete': 97}) | — |

- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM (DTU/DeepTMHMM:1.0.57); ≤500 sequences per job, one job at a time.
- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: cached: 18, newrun: 79. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.
- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; 3 records.

## Summary
- 21 proteins with ≥1 predicted membrane span (any main method); 11 with a predicted signal peptide; 1 with DeepTMHMM β-type states; 24 with main-method disagreement.
- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.

### Per-protein calls (main methods)
| Gene | Locus tag | Product | aa | Phobius | DeepTMHMM | TOPCONS2 | Disagreement |
|---|---|---|---|---|---|---|---|
| — | `SPP1p001` | terminase small subunit | 184 | none | none | none | — |
| — | `SPP1p002` | hypothetical protein | 101 | TM 21–42, TM 62–80 | none | SP 1–21, TM 23–43, TM 62–82 | span_count, signal_peptide, n_terminal_side |
| — | `SPP1p003` | terminase large subunit | 422 | TM 43–61 | none | none | span_count |
| — | `SPP1p004` | hypothetical protein | 98 | none | none | TM 2–22 | span_count |
| — | `SPP1p005` | hypothetical protein | 94 | none | none | none | — |
| — | `SPP1p006` | hypothetical protein | 71 | none | none | none | — |
| — | `SPP1p007` | hypothetical protein | 74 | none | none | none | — |
| — | `SPP1p008` | hypothetical protein | 85 | none | none | none | — |
| — | `SPP1p009` | hypothetical protein | 89 | none | none | none | — |
| — | `SPP1p010` | portal protein | 503 | none | none | none | — |
| — | `SPP1p011` | minor head protein | 308 | none | none | none | — |
| — | `SPP1p012` | hypothetical protein | 77 | none | none | none | — |
| — | `SPP1p013` | hypothetical protein | 96 | SP 1–25, TM 41–61, TM 73–92 | SP 1–25, TM 45–61 | SP 1–25, TM 41–61, TM 73–93 | span_count |
| — | `SPP1p014` | hypothetical protein | 107 | SP 1–27, TM 68–90 | none | SP 1–27, TM 70–90 | span_count, signal_peptide |
| — | `SPP1p015` | hypothetical protein | 382 | none | none | none | — |
| — | `SPP1p016` | hypothetical protein | 107 | TM 6–28, TM 49–74, TM 86–106 | none | TM 8–28, TM 53–73, TM 78–98 | span_count, n_terminal_side |
| — | `SPP1p017` | hypothetical protein | 112 | none | none | none | — |
| — | `SPP1p018` | hypothetical protein | 69 | none | none | none | — |
| — | `SPP1p019` | hypothetical protein | 145 | SP 1–32 | none | SP 1–30 | signal_peptide, signal_peptide_boundary |
| — | `SPP1p020` | head scaffolding protein | 214 | none | none | none | — |
| — | `SPP1p021` | hypothetical protein | 113 | none | none | SP 1–22 | signal_peptide |
| — | `SPP1p022` | hypothetical protein | 64 | none | none | none | — |
| — | `SPP1p023` | major head protein | 324 | none | none | none | — |
| — | `SPP1p024` | hypothetical protein | 58 | none | none | none | — |
| — | `SPP1p025` | head-tail adaptor | 102 | none | none | none | — |
| — | `SPP1p026` | head closure Hc1 | 109 | none | none | none | — |
| — | `SPP1p027` | tail completion or Neck1 protein | 144 | none | none | none | — |
| — | `SPP1p028` | tail terminator | 134 | none | none | none | — |
| — | `SPP1p107` | major tail protein | 264 | none | none | none | — |
| — | `SPP1p029` | major tail protein | 177 | none | none | none | — |
| — | `SPP1p030` | hypothetical protein | 184 | TM 119–142, TM 154–175 | none | TM 153–173 | span_count, n_terminal_side |
| — | `SPP1p108` | tail assembly chaperone | 303 | none | none | none | — |
| — | `SPP1p033` | tail chaperone protein | 179 | none | none | none | — |
| — | `SPP1p035` | tail length tape measure protein | 1032 | TM 599–616, TM 628–647, TM 653–671 | TM 659–668, TM 849–858 | TM 71–91, TM 109–129, TM 396–416, TM 435–455, TM 563–583, TM 649–669 | span_count, n_terminal_side |
| — | `SPP1p038` | hypothetical protein | 151 | TM 20–41, TM 53–70 | none | none | span_count |
| — | `SPP1p039` | distal tail protein Dit | 253 | none | none | none | — |
| — | `SPP1p040` | hypothetical protein | 74 | none | none | none | — |
| — | `SPP1p043` | tail tip protein Tal | 1111 | none | none | none | — |
| — | `SPP1p044` | hypothetical protein | 102 | none | none | none | — |
| — | `SPP1p045` | hypothetical protein | 146 | none | none | none | — |
| — | `SPP1p046` | hypothetical protein | 98 | none | none | none | — |
| — | `SPP1p047` | hypothetical protein | 54 | none | none | none | — |
| — | `SPP1p048` | hypothetical protein | 51 | none | none | none | — |
| — | `SPP1p049` | hypothetical protein | 76 | none | none | none | — |
| — | `SPP1p050` | hypothetical protein | 83 | TM 57–81 | TM 60–78 | TM 57–77 | span_boundaries(max_shift=4) |
| — | `SPP1p051` | endolysin | 271 | none | none | none | — |
| — | `SPP1p052` | hypothetical protein | 117 | TM 12–33, TM 45–66, TM 78–100 | none | TM 10–30 | span_count |
| — | `SPP1p053` | holin | 82 | SP 1–24, TM 40–59 | TM 9–22, TM 41–56 | TM 7–27, TM 43–63 | span_count, signal_peptide, n_terminal_side |
| — | `SPP1p054` | hypothetical protein | 184 | none | none | none | — |
| — | `SPP1p055` | hypothetical protein | 95 | none | none | none | — |
| — | `SPP1p056` | hypothetical protein | 100 | none | none | none | — |
| — | `SPP1p057` | hypothetical protein | 105 | none | none | none | — |
| — | `SPP1p058` | hypothetical protein | 54 | none | none | none | — |
| — | `SPP1p059` | hypothetical protein | 56 | none | none | none | — |
| — | `SPP1p060` | hypothetical protein | 94 | none | none | none | — |
| — | `SPP1p061` | hypothetical protein | 126 | SP 1–58, TM 68–93, TM 100–117 | SP 1–58, TM 75–93, TM 99–119 | TM 38–58, TM 73–93 | signal_peptide, n_terminal_side |
| — | `SPP1p062` | hypothetical protein | 105 | TM 60–79, TM 86–104 | TM 60–78, TM 83–103 | TM 58–78, TM 84–104 | — |
| — | `SPP1p063` | hypothetical protein | 836 | none | none | none | — |
| — | `SPP1p064` | hypothetical protein | 157 | none | none | none | — |
| — | `SPP1p065` | hypothetical protein | 131 | TM 23–43, TM 55–73 | none | TM 24–44, TM 51–71 | span_count |
| — | `SPP1p066` | hypothetical protein | 128 | none | none | none | — |
| — | `SPP1p067` | hypothetical protein | 137 | none | none | none | — |
| — | `SPP1p068` | tail spike protein | 599 | none | SP 1–18 | none | signal_peptide |
| — | `SPP1p069` | hypothetical protein | 72 | none | none | none | — |
| — | `SPP1p070` | hypothetical protein | 52 | none | none | none | — |
| — | `SPP1p071` | RecE-like recombination exonuclease | 311 | none | none | none | — |
| — | `SPP1p072` | hypothetical protein | 57 | none | none | none | — |
| — | `SPP1p073` | hypothetical protein | 97 | TM 12–30, TM 37–58, TM 78–96 | none | TM 37–57, TM 76–96 | span_count, n_terminal_side |
| — | `SPP1p074` | hypothetical protein | 84 | none | none | none | — |
| — | `SPP1p075` | hypothetical protein | 96 | none | none | none | — |
| — | `SPP1p076` | RecT-like ssDNA annealing protein | 287 | none | none | none | — |
| — | `SPP1p077` | hypothetical protein | 156 | none | none | SP 1–21 | signal_peptide |
| — | `SPP1p078` | hypothetical protein | 159 | none | none | none | — |
| — | `SPP1p083` | excisionase and transcriptional regulator | 57 | none | none | none | — |
| — | `SPP1p084` | DnaD-like helicase loader | 256 | none | none | none | — |
| — | `SPP1p085` | helicase loader | 126 | none | none | none | — |
| — | `SPP1p086` | DnaB-like replicative helicase | 442 | none | none | none | — |
| — | `SPP1p087` | DnaB-like replicative helicase | 300 | none | none | none | — |
| — | `SPP1p088` | hypothetical protein | 91 | TM 25–45, TM 65–84 | SP 1–49 | TM 25–45 | span_count, signal_peptide |
| — | `SPP1p089` | hypothetical protein | 108 | TM 22–44 | none | none | span_count |
| — | `SPP1p090` | hypothetical protein | 175 | none | none | none | — |
| — | `SPP1p091` | hypothetical protein | 131 | none | none | none | — |
| — | `SPP1p092` | hypothetical protein | 56 | none | none | none | — |
| — | `SPP1p093` | hypothetical protein | 98 | none | none | none | — |
| — | `SPP1p094` | hypothetical protein | 117 | none | none | none | — |
| — | `SPP1p095` | hypothetical protein | 172 | none | none | none | — |
| — | `SPP1p096` | hypothetical protein | 62 | none | none | none | — |
| — | `SPP1p097` | hypothetical protein | 100 | none | none | none | — |
| — | `SPP1p098` | hypothetical protein | 103 | TM 6–24, TM 33–49, TM 76–94 | TM 6–21, TM 33–49, TM 76–94 | TM 4–24, TM 30–50, TM 74–94 | n_terminal_side |
| — | `SPP1p099` | hypothetical protein | 119 | none | none | none | — |
| — | `SPP1p100` | hypothetical protein | 122 | none | none | none | — |
| — | `SPP1p101` | hypothetical protein | 54 | none | none | none | — |
| — | `SPP1p102` | hypothetical protein | 57 | none | none | none | — |
| — | `SPP1p103` | hypothetical protein | 60 | TM 7–25, TM 31–50 | TM 7–25, TM 33–49 | TM 5–25, TM 34–54 | span_boundaries(max_shift=5) |
| — | `SPP1p104` | hypothetical protein | 51 | SP 1–25 | SP 1–25 | SP 1–25 | — |
| — | `SPP1p105` | hypothetical protein | 80 | none | none | none | — |
| — | `SPP1p106` | hypothetical protein | 68 | TM 6–28 | TM 8–26 | TM 5–25 | n_terminal_side |

## Conventions & cautions
- 1-based inclusive amino-acid positions in the annotated precursor translation; signal peptides keep precursor numbering. comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string.
- Normalized states: **I** inside / cytoplasmic side of the membrane (model-defined); **O** outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior; **M** alpha-helical membrane span; **S** signal peptide (precursor numbering; predicted, cleavage not demonstrated); **B** beta-strand membrane span (DeepTMHMM); **P** periplasm, in DeepTMHMM beta-barrel predictions. Native labels are kept (`nseg`).
- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.
- Disagreements are flagged, never resolved into a consensus.

## Figures
The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org SPP1 [--png]`.

## Re-run
- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).
- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/topology-rerun.yml`, https://github.com/mbaffour/mbaffour.github.io/actions/workflows/topology-rerun.yml) with organism `SPP1`; or locally `python3 scripts/rerun.py --org SPP1`.

## Validation
`verification.json`: 25 pass, 0 fail, 0 pending of 25 checks. 
Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.

## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)
```
python3 scripts/01_fetch_inputs.py --org SPP1     # skips files already present
python3 scripts/02_inventory.py --org SPP1
python3 scripts/03_run_phobius.py --org SPP1      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org SPP1    # resumable
python3 scripts/04_run_topcons.py --org SPP1      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org SPP1 && python3 scripts/08_build_atlas.py --org SPP1
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org SPP1
python3 scripts/rerun.py --org SPP1 [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```
Web-job links expire; the raw outputs and job records here are the durable record.
