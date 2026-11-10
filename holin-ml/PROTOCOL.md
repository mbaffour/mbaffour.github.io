# Protocol: build and honestly evaluate a holin predictor

Paste everything below the line into Claude, ChatGPT, Gemini or any coding assistant with shell access. It gives the
method and the traps, not the answers, so the assistant has to do the work and you can check what it reports against
the reference results at the end. Bracketed fields are yours. The same structure transfers to any "find protein family
X in genomes" problem: swap the sources, the positives and the hard cases.

This version reflects the project's final state. Earlier versions led with a gold-holdout AP of 0.904 and a "12 of 13
holins recovered" membrane cross-check; both are **retracted** (section 10) and the protocol below exists largely to
stop you reproducing those mistakes.

---

You are helping me build a machine-learning model that finds **holin genes** in phage and bacterial genomes, and — more
importantly — an evaluation that says honestly whether it works. Carry the work out; do not stop at a plan. Use real
downloads and real model output, keep provenance for everything, and never let a plausible number stand in for
something you did not measure. If a result looks too good, find the leak before reporting it. Report every rejected
experiment as well as the adopted ones.

## My project

- Target class: **holins** — small phage proteins that permeabilise the host inner membrane to schedule lysis
- Output folder: **[ABSOLUTE PATH]**
- Compute: **[CPU ONLY / GPU, CORES, RAM]** (the core pipeline runs on 4 CPU cores and 16 GB in a few hours, excluding
  downloads; the Pfam fetch is several hundred MB)
- May I submit public sequences to public web services? **[YES / NO / ASK FIRST]**
- Genomes I care about most: **[ACCESSIONS]**
- Python: `biopython pyopal pyrodigal scikit-learn numpy torch (CPU wheel) transformers`

## 0. Why this problem punishes sloppiness

Holins are the worst case for homology search: dozens of unrelated families, 60–150 aa (some ~218 aa), no conserved
motif beyond "small, hydrophobic, basic C-terminus". Three consequences shape everything below.

- A classifier trained and tested on near-duplicate holins looks excellent and is useless. Every split is grouped by
  sequence homology.
- If the model cannot beat a plain alignment search, it has added nothing. Build that baseline first and keep reporting
  it beside the model.
- The classic phages (λ, T4, T7, P22, ...) have holins that are themselves training examples. A genome scan that does
  not remove them measures memorisation. And even a clean holdout can be wrong if its negatives do not look like the
  deployment task (a phage genome full of phage proteins and spanins).

## 1. The pipeline, step by step

Every step is a script in `scripts/`; read its top-of-file docstring for the exact purpose and `Usage:` line. Run them
in this order. Scripts 06–11, 15 and 16 are experiments or dead ends kept for the record; the ones that produce the
final model and headline are marked **core**.

| # | Script | Purpose | Status |
|---|---|---|---|
| 01 | `01_fetch_data.py` | Download UniProt, TCDB, InterPro with URL, UTC time, SHA-256 | core |
| 02 | `02_build_dataset.py` | Assemble labelled set: holin / holin_like / negative, evidence tiers | core |
| 03 | `03_cluster.py` | Exhaustive Smith-Waterman, greedy homology clusters, `search()` helper | core |
| 04 | `04_train.py` | Grouped-CV training, feature-set comparison, homology baseline, hard cases | core |
| 05 | `05_scan_genome.py` | Score a genome (`--annotated`/`--denovo`, `--holdout`) | core |
| 06 | `06_benchmark_genomes.py` | First leave-one-genome-out recall benchmark | superseded by 14/22 |
| 07 | `07_family_analysis.py` | Per-family/tier/length recall; leave-one-family-out | core (diagnosis) |
| 08 | `08_mine_pool.py` | Unlabelled phage pool plus genomic neighbourhood, for self-training | used by 09, rejected |
| 09 | `09_iterate.py` | Guarded self-training loop; creates the frozen gold holdout | loop **rejected**; holdout kept |
| 10 | `10_specialists.py` | Specialist models for the measured failures | **rejected** |
| 11 | `11_membrane_cross_check.py` | Hits vs Phobius/DeepTMHMM/TOPCONS2 topologies | **contaminated, retracted** |
| 12 | `12_phage_negatives.py` | Build phage-derived negatives (incl. Rz-like spanins) | core, adopted |
| 13 | `13_retrain_phage_negatives.py` | Retrain with them; judge by genome scan first | core, adopted |
| 14 | `14_genome_loo_eval.py` | Leave-one-genome-out scan with family removal | core |
| 15 | `15_local_features_eval.py` | TM-anchored local features | **rejected** |
| 16 | `16_signature_discovery.py` | Holins vs bacterial / phage negatives / spanins | superseded by 18 |
| 17 | `17_family_dependence.py` | Recognising a holin vs recognising its family | core (finding) |
| 18 | `18_signature_controls.py` | Signature candidates vs membrane-matched controls | core (finding) |
| 19 | `19_fetch_holin_families.py` | Download members of the 38 Pfam holin families | core, adopted |
| 20 | `20_curate_more_holins.py` | Tier and subsample them into training records | core, adopted |
| 21 | `21_merge_curated.py` | Assign cluster ids without disturbing the frozen gold holdout | core |
| 22 | `22_retrain_curated.py` | LOGO under two protocols; the **headline numbers** | core |
| 23 | `23_train_production.py` | Fit and save the deployable model plus model card | core |

`scripts/features.py` is shared by all of them. Note that the docstring at the top of `03_cluster.py` still says
"connected components (single linkage)"; the code actually runs greedy set-cover (see `greedy()`), and
`data/processed/cluster_summary.json` records `"greedy set-cover, longest-first"`. Trust the code and the summary.

## 2. Sources, with provenance (script 01)

Record for every download: URL, UTC timestamp, SHA-256, byte count and database release (`data/raw/provenance.json`).

- **TCDB** superfamily **1.E** (the holin superfamily): `https://www.tcdb.org/public/tcdb` (all sequences, FASTA headers
  carry the TC id) and `https://www.tcdb.org/cgi-bin/projectv/public/families.py` (family names).
- **UniProtKB/Swiss-Prot** via `https://rest.uniprot.org/uniprotkb/stream`, TSV, fields including `protein_existence`,
  `protein_families`, `cc_function`, `keyword`, `xref_tcdb`, `lineage_ids`, `sequence`. Queries:
  - positives: `reviewed:true AND (protein_name:holin OR family:holin OR protein_name:antiholin OR protein_name:pinholin)`
  - phage negatives pool: `reviewed:true AND taxonomy_id:10239 AND virus_host_id:2`
  - bacterial negatives pool: `reviewed:true AND taxonomy_id:2 AND length:[30 TO 250] AND ft_transmem:*`
  - (optional, unused for training) `reviewed:false AND family:holin`
- **InterPro/Pfam** holin entries: `data/raw/interpro_pfam_holin.json` lists **38 Pfam families** whose name is a holin.
  Script 19 downloads their members (kept in `data/raw/pfam/`, gitignored, with URL/UTC/SHA-256 in `provenance.json`).
  Three of the 38 are **antiholin** families and are recorded separately.

Expect roughly 740 TCDB 1.E sequences, ~145 Swiss-Prot holin entries, ~2,000 Swiss-Prot phage proteins and ~13,000
bacterial small membrane proteins. If your counts differ by a lot, say so rather than proceeding quietly.

## 3. Labels, and the traps in them (scripts 02, 20)

Three classes:

- **holin** (positives) — TCDB 1.E members of *phage* holin families, plus Swiss-Prot phage holins, plus (script 20)
  curated members of the Pfam holin families. Tag each with an **evidence tier** and never blur the tiers in a reported
  number:
  - `tested` — UniProt protein-existence 1 (evidence at protein level)
  - `curated` — reviewed entry, or a named phage holin family in TCDB
  - `putative` — TCDB families whose own name says "putative"
  - `pfam_reviewed` / `pfam_unreviewed` — Pfam holin family members, Swiss-Prot reviewed or not. **This is profile-match
    evidence, weaker than a Swiss-Prot annotation, and for unreviewed entries nobody has checked it.** Only 7 of the
    2,886 usable curated holins are reviewed.
- **holin-like** (held out of training, scored separately as hard cases) — dedicated antiholins and CidB/LrgB, bacterial
  CidA/LrgA, Hok/Gef toxins, TcdE, gene-transfer-agent release holins, Bacillus spore germination holin-like, T4
  superinfection immunity, phage Mu releasin, archaeal putative holins (TCDB 1.E.9, .14, .19, .23, .42, .43, .52, .53,
  .54, .55, .66, .70, .72). **An antiholin is not a holin**: Pfam antiholin families and any entry whose own name says
  antiholin are labelled `holin_like`, whatever family they sit in.
- **negative** — the two Swiss-Prot pools after dropping anything whose name, family, function or keywords match
  `holin|pinholin|lysis|lytic|spanin|endolysin|lysozyme|lysin|murein|peptidoglycan|cell wall hydrolase|amidase|
  transglycosylase|rz|rz1|releasin|immunity`, or that carries a TCDB 1.E cross-reference; **plus phage-derived
  negatives** (script 12, section 6). Say explicitly that negatives are **unlabelled**, not verified non-holins.

Traps that each cost me a wrong result:

1. **Dual-start holin genes.** λ *S*, φ29 *gp14*, P21 *S21* and SPP1 are annotated by UniProt under the name of their
   long product ("antiholin") while TCDB files the same gene in a phage holin family. Treating that as a label conflict
   and dropping it silently removed λ S from my training set. Label the ORF a **holin**, flag it
   `dual_start_or_antiholin`, and print the affected entries (there were 8). Do not extend this to genuine antiholin
   families, which stay out.
2. **Prophage holins live in bacterial proteomes** (e.g. B. subtilis SPβ *bhlB*, UniProt O31984/Q99163), so a "is the
   organism a virus?" test misses them.
3. Merge identical sequences keeping all sources; let an explicit holin annotation outrank membership of the generic
   negative pool; write remaining conflicts to a file instead of discarding them. Never edit a sequence to make a tool
   accept it — record why it is ineligible.
4. **Pfam curation drops a lot.** For the curated set, 1,086 candidates were out of length range, 450 were already in the
   dataset and 13 had non-standard residues; at most 150 members per family were kept, so 41,029 Pfam members became
   4,701 records (4,497 holins, 204 antiholin `holin_like`). Report your own drop counts.

Report final counts by label, tier and family, generated from the data.

## 4. Homology clusters, before any split (scripts 03, 21)

All-vs-all **Smith-Waterman** (BLOSUM62, gap open 11 / extend 1). With a vectorised library (`pyopal`) an exhaustive
~10,000 × 10,000 comparison of short proteins takes about 7 minutes on 4 cores, so **do not reach for a k-mer prefilter
without measuring its recall** — mine recovered only ~10% of true holin-holin pairs and I discarded it.

Call two sequences related at **≥30% identity over ≥50% of the shorter sequence**. Cluster **greedily, longest-first**
(CD-HIT / MMseqs style). **Do not use single linkage** — chaining merged all 10,000 proteins into one component, which
makes grouped cross-validation meaningless. Print the cluster-size distribution. Expect ~1,000 clusters, ~140 containing
holins (I got 1,034 and 143).

**Do not re-cluster after you freeze the gold holdout.** Adding thousands of sequences can bridge two previously separate
clusters and quietly put a training holin in the same family as a holdout holin; the holdout would still list the same
ids and the leak would be invisible. Script 21 instead keeps existing cluster ids, assigns each new holin to the cluster
of its best existing hit (≥30% identity at ≥50% coverage) or to a fresh cluster, and marks any new holin that lands in a
gold-holdout cluster `excluded_gold_cluster` so it is never trained on.

## 5. Features (`scripts/features.py`)

Compute both and compare them separately as well as combined:

- **Biophysical (~36 numbers)** — length and log length; hydropathy-based TM segment count, total extent, first-segment
  position and C-terminal tail length (Kyte-Doolittle, window 19, threshold 1.6, minimum 15 residues); net charge of the
  N-terminal 20 and C-terminal 20/30 residues; charged, hydrophobic and G+P fractions; amino-acid composition. State in
  the write-up that these TM segments are a **hydropathy heuristic used as a model input**, not a topology prediction.
- **Protein language model** — ESM-2 `facebook/esm2_t12_35M_UR50D`, mean-pooled last hidden layer (480-d). ~12 minutes
  for 10,000 short proteins on 4 CPU threads. Cache per sequence SHA-256 (`models/esm_cache`). Window sequences longer
  than 1,022 residues and average by length.

The deployed recipe is handcrafted + mean-pooled ESM with gradient boosting. The local-feature variant (script 15) was
tried and rejected.

## 6. Evaluation — the part that decides whether any of this is real

There are three tiers of evidence. Report them together, and rank them in this order.

**Tier 1 — HEADLINE: leave-one-genome-out (LOGO) genome scan (scripts 14, 22).** For each of the 16 model phages of the
topology atlas (13 annotated holins, 1,067 proteins), remove training holins as specified below, refit, score every
protein of the genome, and compute genome-scan average precision, precision/recall at score thresholds and the rank of
the true holin. Confidence intervals **resample genomes**, not proteins, because proteins within a genome are not
independent. **Report two removal protocols side by side, always:**

- **Realistic (`sequence`)** — remove only training holins ≥95% identical to the target genome's holin, so the family
  stays. Asks: *would we find the holin in a newly sequenced phage whose holin belongs to a known family?* The common
  case, and where depth should pay.
- **Strict (`family`)** — remove the whole holin family: every training holin within ≥30% identity of that genome's
  holin, whole clusters. Asks: *would we find a holin from a family nobody has seen?* This protocol is blind to
  curation depth by construction.

Reporting only the strict number understates what the tool is useful for; reporting only the realistic one overstates
novelty. The genomes used for LOGO must contribute **no training negatives** (script 12 excludes them by accession).

**Tier 2 — diagnosis.** Grouped CV, per-family and per-tier recall, leave-one-family-out, hard cases, family dependence.
These explain *why* the headline is what it is; none replaces it.

1. **Homology baseline** (best Smith-Waterman identity to the fold's training holins; no learning). The number to beat.
2. **Homology-grouped cross-validation** `GroupKFold(5)` over the section 4 clusters: AUROC, average precision and recall
   at 90/95/99% precision. With ~5% positives AUROC flatters.
3. **Per-family recall** from out-of-fold scores at a fixed high-precision threshold; name the families missed entirely
   (script 07).
4. **Recall by evidence tier** (`tested`, `curated`, `putative`).
5. **Leave-one-family-out** (script 07): delete a whole TCDB family plus anything in its clusters and score its members.
   Expect it to be far worse than grouped CV.
6. **Hard cases:** score the holin-like set, median per category. Antiholins and toxins scoring low is evidence the
   model learned something specific; functionally holin-like proteins (releasins, GTA release holins, TcdE) scoring high
   is interesting rather than wrong.
7. **Family dependence** (script 17): score each atlas holin with its family in training and with it removed; the
   difference is the "collapse". Verdicts: generalises / family recognition only / fails either way. With 13 holins
   these are case-by-case observations, not rates.

**Tier 3 — SECONDARY ONLY: the frozen gold holdout.** 2,978 records, 194 holins, chosen once as whole homology clusters
with seed 0, written to disk (`data/processed/gold_holdout.json`), never trained on during model selection and never
used to accept a candidate. **Its negatives are the original set, with no phage-derived negatives and no spanins, so it
shares the training distribution's blind spot** and cannot see the Rz-like spanin false positives that appear on real
genomes. Report it, label it secondary, and never quote it as the model's validated performance. The production model
(script 23) is trained on the holdout, so its gold score is memorisation.

**The trap in genome-level holdouts that cost me a false conclusion.** If "homologous" means identity and coverage
alone, short spurious local alignments fire constantly. Scanning T4 that way removed 556 of 558 training holins, leaving
two positives. Require a real alignment score too (SW ≥ 80 fixed it in the early benchmark). Report how many holins/
clusters each genome's holdout removed (the per-genome removal tables in `reports/curated_retrain_eval.json`).

## 7. Interventions tried, with verdicts

Keep this ledger in your write-up; the rejections are part of the result. Each was judged by the Tier 1 scan, not by
gold AP alone.

| Intervention | Script(s) | Verdict | Reason |
|---|---|---|---|
| Stacked specialist models | 10 | **Rejected** | Lowered gold AP, miscalibrated threshold |
| Guarded self-training loop (frozen holdout, independent genomic-context evidence, five guards) | 08, 09 | **Rejected, rolled back** | Did not beat baseline; spanin contamination in candidates |
| TM-anchored local features | 15 | **Rejected** | Did nothing for the target proteins, cost recall |
| Phage-derived negatives (3,382, incl. 101 Rz-like spanins) | 12, 13 | **Adopted** | Eliminated Rz-like spanin false positives, which no bacterial-negative-only model had seen |
| Curated Pfam holins (4,497; 2,886 usable) | 19–22 | **Adopted** | Realistic AP 0.823 to 0.9647; strict 0.625 to 0.7847 |

Constraints for any self-training you attempt: a candidate is accepted only if an independent signal agrees (here, the
ORF sits next to an annotated endolysin or spanin, which the classifier never sees as a feature), and the pool must
exclude every genome used in evaluation.

## 8. Scanning a genome (script 05)

Support both and label which was used: the GenBank record's own CDS translations (`--annotated`), and *de novo* calls
(`--denovo`, Pyrodigal meta mode — an extra inference). For each candidate report score, length, hydropathy TM count,
coordinates, strand and neighbouring gene products: holins sit beside endolysin and spanin genes, so a lone high scorer
inside a structural module deserves more doubt than one next to a spanin. Use `--holdout` for any recovery claim on a
genome whose holin may be in training; without it, say plainly that it may have been.

Where the model disagrees with the deposited annotation, say so and do not resolve it by assuming either side is right.
Use a **0.95** score threshold for high-confidence calls; precision at 0.9 is only 0.75 under both protocols.

## 9. Signature discovery and its controls (scripts 16, 18)

A "signature" separating holins from other proteins only means something if it points the **same way** against spanins,
bacterial membrane proteins **and the membrane subset** of the phage negatives. The phage negatives are overwhelmingly
soluble (median n_tm 0), so holins-vs-phage-negatives mostly reports membrane-ness; script 16's contrast was flawed for
that reason and script 18 repairs it. Spanins are also peculiar in their own right (o-spanin lipoprotein cysteine,
N-terminal anchors).

Result: **no novel compositional signature survives.** Only C-terminal K+R enrichment is consistent across all three
controls, and that is the long-established charged C-terminal tail. Glycine-zipper enrichment, which looks real against
spanins, is an artifact of spanins being glycine-poor: holins are no more glycine-zippered inside TM helices than
ordinary bacterial membrane proteins, and fewer carry a GxxxG-spaced motif (59.8% vs 68.9%). Do not report a compositional
"discovery" without all three controls.

## 10. Failure modes and retracted figures

- **Retracted: gold-holdout AP 0.904.** Measured on a holdout that shares the training blind spot. It coexisted with poor
  precision on real genomes and Rz-like spanins among the top hits. Do not present it as performance.
- **Retracted: "12 of 13 holins recovered" (membrane cross-check, script 11).** Those holins were training examples; it
  measured memorisation. Script 11 is kept only as an example of a contaminated check.
- **Curation adds depth, not breadth.** 4,700 of the 4,701 curated records joined families already in training; one
  formed a new family. Pfam is effectively exhausted as a source of new holin architectures. An arm training only on
  "new-family" curated holins was planned and dropped because it would have had n=1.
- **You cannot teach a family you then delete.** T4 holin T and T5 C1 (~218 aa, single N-terminal TM, large C-terminal
  domain) score ~0.000 under the previous model; the curated model recovers them only in the realistic protocol, and
  under strict removal they stay ~0.000. Only 52 of 558 Swiss-Prot/TCDB training holins exceed 150 aa. Length is not a
  veto (T4 t scores 0.989 at full length with its family present), and the signal is not concentrated in the TM anchor
  (the anchor window alone scores far lower).
- **Cost of curation:** precision at score 0.9 fell from about 0.82 to 0.75 (realistic). Use 0.95 for high-confidence
  calls.
- **Mislabelled holin-like proteins** (antiholins counted as holins) would repeat the dual-start conflict in reverse.
- **Leakage through re-clustering** (section 4) and **memorising classic phages** (section 6).

## 11. Reporting rules

Every count, score and date generated from data, nothing hard-coded. Model, features, thresholds and database releases
stated beside the numbers. Quote both LOGO protocols together. A limitations section covering at least: strict-protocol
performance is modest and rests on 13 annotated holins in 16 genomes; most positives are profile-match (Pfam) evidence
with few reviewed; negatives are unlabelled so precision is a lower bound; positives inherit the field's bias toward
studied families and `putative` entries are themselves predictions; the model scores proteins in isolation and ignores
genomic context, the strongest clue a curator uses; nothing distinguishes canonical holins from pinholins, predicts
lysis timing, or identifies which membrane is involved. Every high score is a hypothesis for the bench, not a
demonstrated holin.

## 12. Deliverables

- `models/holin_model_curated.pkl` — the deployable model, written by script 23 along with a model card at
  `reports/model_card.json`. Trained on every label available (including the gold holdout), so it is **not** the model
  to quote a number from; the honest estimate is the LOGO figure from script 22 (`reports/curated_retrain_eval.json`).
  Check that both files exist after running script 23; in the checkout this protocol was written from they had not yet
  been generated.
- `reports/*.json` — every number in this document traces to one: `curated_retrain_eval.json` (headline),
  `curation_report.json`, `family_dependence.json`, `signature_controls.json`, `training_report.json` (grouped CV),
  `family_analysis.json`.

## 13. Reference results to compare against

Your numbers will differ with database releases — large divergence means something is wrong.

**Headline: LOGO genome scan, curated model (13,351 training records, 3,250 holins), 16 phages, 13 annotated holins.**

| Protocol | Genome AP | CI95 (genomes) | Recall @0.9 | Precision @0.9 | Top-1 rate |
|---|---|---|---|---|---|
| Realistic (≥95% id removed) | 0.9647 | [0.893, 1.0] | 0.923 (12/13) | 0.75 | 1.0 |
| Strict (whole family removed) | 0.7847 | [0.538, 0.962] | 0.692 (9/13) | 0.75 | 0.8 |

Pre-curation model (10,465 records, 364 holins) on the same scan: realistic AP 0.823, strict 0.625. Precision at 0.9
was 0.818 (realistic) and 0.9 (strict, with fewer calls) before curation. Realistic = "find the holin in a new phage
from a known family"; strict = "find a holin from a genuinely novel family — you get a shortlist, not an answer".

**Family dependence** (13 annotated holins): generalises 9, family recognition only 3 (T4 t, T5 C1, φ29 14), fails
either way 1 (P1 lydD). The model generalises to the small multi-TM class I holins and recognises the rest largely by
family similarity.

**Secondary: gold holdout** (2,978 records, 194 holins): pre-curation AP 0.8876, recall at 95% precision 0.7062;
curated AP 0.8824, recall at 95% precision 0.5309. Shares the blind spot of its negatives; not a headline.

**Diagnostic: homology-grouped CV, 5 folds, original 10,061 training records, no phage-derived negatives** (this is the
number that was mistaken for the headline):

| Model | AUROC | Avg precision | Recall @P90 |
|---|---|---|---|
| Homology baseline (SW identity, no ML) | 0.736 | 0.306 | 0.147 |
| Biophysical + logistic regression | 0.837 | 0.274 | 0.002 |
| Biophysical + gradient boosting | 0.955 | 0.759 | 0.428 |
| ESM-2 + logistic regression | 0.980 | 0.872 | 0.704 |
| ESM-2 + gradient boosting | 0.988 | 0.909 | 0.767 |
| Both + logistic regression | 0.980 | 0.866 | 0.688 |
| **Both + gradient boosting** | **0.990** | **0.915** | **0.792** |

Recall at 95% precision by tier for the best model: tested 0.625, curated 0.687, putative 0.441.

Dataset: 10,295 sequences originally (558 holins in 61 families, 234 holin-like, 9,503 negatives; 1,034 clusters),
plus 3,382 phage-derived negatives and 4,701 curated Pfam records (4,497 holins, 204 antiholin holin-like); 4,700 of
those 4,701 join existing families.

Signature controls: only C-terminal K+R (cterm20) is consistent against all three controls (median 3 K+R in holins vs
2 in both bacterial and phage membrane proteins). Everything else is intermediate between spanins and bacterial
membrane proteins.

## 14. What to add next

- Genomic context as a feature: distance to the nearest endolysin/spanin, position in the lysis cassette.
- Calibrated probabilities (isotonic or Platt on held-out folds) so a score is comparable across genomes, and to recover
  the precision lost to curation.
- More experimentally tested holins from genuinely novel families; Pfam cannot supply them.
- A larger ESM-2 on GPU, measured against the 35M model rather than assumed better.
- Explicit handling of long single-TM holins in families not yet in training.
