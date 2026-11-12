# Holin ML — learning to recognise holin genes

A reproducible pipeline that assembles **annotated and experimentally tested holins**, trains a classifier on them, and
scores every protein in a genome to propose holin candidates.

Holins are small phage membrane proteins that end an infection by permeabilising the inner membrane at a scheduled time.
They are notoriously hard to find by homology: dozens of unrelated families, short sequences, little conservation beyond
"small, hydrophobic, charged C-terminus". That is exactly the situation where a learned model can add something over a
BLAST/HMM search — but only if it is evaluated in a way that homology cannot fake. This project is built around that
evaluation, not around a headline number.

> Everything here is a **prediction**. A high score is a hypothesis to test at the bench, not a demonstrated holin.

## Run it on your computer

The tool now calls all three lysis genes (holins, endolysins, spanins), from protein or nucleotide sequence.
These steps were tested end to end on a clean machine (fresh clone, new environment, install, prediction) and take
about 3 minutes. You need Python 3.11 or newer (3.13 tested), git, about 1.5 GB of free disk (mostly PyTorch), and an
internet connection the first time.

```bash
# 1. Get the code: this branch only, no history (~135 MB)
git clone --depth 1 -b claude/holin-ml --single-branch https://github.com/mbaffour/mbaffour.github.io.git lysis-caller
cd lysis-caller/holin-ml

# 2. Make an isolated environment
python3 -m venv .venv                 # Windows: py -m venv .venv
source .venv/bin/activate             # Windows PowerShell: .venv\Scripts\Activate.ps1

# 3. Install
pip install torch --index-url https://download.pytorch.org/whl/cpu   # LINUX ONLY, see note below
pip install -r requirements.txt       # on Mac and Windows this line alone is enough

# 4. Check it works (should call gp60 spanin, gp61 endolysin, gp62 and gp63 holin)
python scripts/32_predict_lysis.py --proteins galaxy/test-data/sample_proteins.faa
```

Then point it at your own sequences:

```bash
python scripts/32_predict_lysis.py --genome my_phage.fna --show-cassettes         # raw assembly, no annotation
python scripts/32_predict_lysis.py --proteins my_proteins.faa --out hits.tsv      # protein FASTA
python scripts/32_predict_lysis.py --genbank my_phage.gb --domains               # annotated genome
python scripts/32_predict_lysis.py --acc NC_008720.1                              # fetch from NCBI
python scripts/30_scan_many.py --accessions my_list.txt --out reports/my_scan     # many genomes at once
```

Things worth knowing:

- **Linux only:** a plain `pip install torch` downloads multi-gigabyte GPU builds. Install the CPU build first, as in
  step 3. CPU is enough because the protein model is small. Mac (including Apple Silicon) and Windows get a CPU-sized
  build by default.
- **First run** downloads the ESM-2 protein language model (~130 MB) from HuggingFace. After that it runs offline;
  set `HF_HUB_OFFLINE=1` to make sure it never tries the network.
- **Output** is one TSV row per protein: `P_holin`, `P_endolysin`, `P_spanin` are independent probabilities, `rank_*`
  is each protein's rank in the genome, `call` is the strongest class above the threshold, `high_conf` lists classes
  above their own high-confidence cut-off, `lysis_call` names the one gene called per class (confident or candidate,
  using neighbouring genes as context), and `cassette` groups genes that co-locate as a full lysis cassette.
- **Reading the scores:** read the output as a ranked shortlist -- the true gene is in the top five of its genome
  87-100% of the time but ranked first only 50-70%. For high-confidence calls use the `high_conf` column: cut-offs
  are per class (holin and spanin 0.95, endolysin 0.9995), because the endolysin model's probabilities run higher. A
  gene from a family the model has never seen gets a ranked shortlist, not a verdict.
- **If the models fail to load,** check `pip show scikit-learn` reports exactly 1.9.1. The models are saved
  scikit-learn objects and need that version (`pip install scikit-learn==1.9.1`).
- **Windows:** if PowerShell refuses to activate the environment, run
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- **Conda users:** `conda create -n lysis python=3.13 && conda activate lysis`, then step 3.
- **Retraining** the models from scratch needs `pip install -r requirements-pipeline.txt`; see `PROTOCOL.md`.
- If this ever moves to the repository's main branch, drop `-b claude/holin-ml --single-branch` from step 1.

Full deployment notes, including the Galaxy wrapper, are in `DEPLOY.md`; the write-up is `MANUSCRIPT.md`.

## Headline result

The honest performance number is the **leave-one-genome-out (LOGO) genome scan**: for each of 16 model phages, remove
what the model could cheat with, train on the rest, and ask it to pick the holin out of that phage's proteins. It is
reported under **two protocols, always together**, because they answer different questions
(`reports/curated_retrain_eval.json`, curated model, arm `B_plus_curated`):

| Protocol | What is removed from training | Question it answers | Genome AP (CI95 over genomes) | Recall @ score 0.9 | Precision @ 0.9 | Holin ranked #1 |
|---|---|---|---|---|---|---|
| **Realistic** | holins ≥95% identical to the target genome's holin | A newly sequenced phage whose holin belongs to a **known** family — the common case | **0.9647** [0.893, 1.0] | 0.923 (12/13) | 0.75 | 1.0 of genomes (all 16) |
| **Strict** | the whole holin **family**: every relative at ≥30% identity | A phage from a family **nobody has seen** | **0.7847** [0.538, 0.962] | 0.692 (9/13) | 0.75 | 0.8 of genomes |

For comparison, the model before the Pfam curation scored 0.823 (realistic) and 0.625 (strict) on the same scan.

How to read it: under the realistic protocol the tool finds the holin in a phage from a known family. Under the strict
protocol it is a **shortlist generator, not an answer** — the holin is usually near the top, but in one genome of five it
is not ranked first, and 4 of the 13 holins fall below the 0.9 call threshold. There are only 13 annotated holins in 16
genomes; the confidence intervals are wide because genomes, not proteins, are the unit of resampling.

**Retracted figures.** Two numbers in earlier versions of this README are withdrawn and must not be quoted:
- *"Gold holdout AP 0.904."* The frozen gold holdout shares the training distribution's blind spot (its negatives are the original
  Swiss-Prot set, with no phage-derived negatives and no spanins, so it cannot see the Rz-like spanin false positives), so it measures the wrong task. It is kept only as a
  secondary check (see below).
- *"12 of 13 holins recovered" in the membrane cross-check.* Those holins were themselves training examples, so the scan
  measured memorisation. The same trap applies to any unheld-out scan of λ, T4, T7, P22 and the other classic phages.

## What is in the box

| Stage | Script |
|---|---|
| Fetch sources with provenance | `scripts/01_fetch_data.py` |
| Build the labelled set | `scripts/02_build_dataset.py` |
| Homology clusters for leakage-free CV | `scripts/03_cluster.py` |
| Train + grouped-CV evaluation vs homology baseline | `scripts/04_train.py` |
| Scan a genome | `scripts/05_scan_genome.py` |
| Early genome benchmark, family analysis, pool mining | `scripts/06`–`08` |
| Intervention experiments (several rejected, see ledger) | `scripts/09`, `10`, `12`, `13`, `15` |
| Membrane cross-check (contaminated, retracted) | `scripts/11_membrane_cross_check.py` |
| **Leave-one-genome-out evaluation** | `scripts/14_genome_loo_eval.py`, `scripts/22_retrain_curated.py` |
| Signature discovery and its controls | `scripts/16`, `scripts/18` |
| Family dependence | `scripts/17_family_dependence.py` |
| Pfam holin curation (fetch, curate, merge) | `scripts/19`, `20`, `21` |
| **Deployable model** | `scripts/23_train_production.py` → `models/holin_model_curated.pkl`, model card `reports/model_card.json` |

Note on the deployable model: `models/holin_model_curated.pkl` and `reports/model_card.json` are written by
`scripts/23_train_production.py`. They were **not present in this checkout** when this document was written; run
script 23 to produce them. That model is trained on every label available, including the gold holdout, so a score it
gives on the gold holdout is memorisation and is not an estimate of anything. Quote the LOGO figures above, not a score
from the production model.

`PROTOCOL.md` documents the whole pipeline step by step so it can be rerun elsewhere.

## The labelled set (final)

`data/processed/dataset_summary.json` and `reports/curation_report.json` are generated, not hand-written.

- **Positives:** 558 Swiss-Prot/TCDB holins (evidence tiers `tested` 8, `curated` 482, `putative` 68; 61 families)
  **plus 4,497 curated holins** drawn from the 38 Pfam holin families.
- **Negatives:** 9,503 Swiss-Prot negatives (phage proteins 1,619 and bacterial small membrane proteins 7,884, after
  removing anything lysis-annotated; the "bacterial" label in this project's reports refers to this original pool) **plus 3,382 phage-derived**, including 101 Rz-like spanins as hard negatives.
- **Antiholins are out of training.** An antiholin is not a holin. Antiholin families and entries named antiholin are
  labelled `holin_like` and held out (the 234 original holin-like proteins, plus 204 antiholin records from the Pfam curation).
- **Frozen gold holdout:** 2,978 records, 194 holins, chosen once as whole homology clusters with seed 0, never trained
  on during model selection. After merging the curated set, existing records kept their original cluster ids so the
  holdout could not be re-leaked (`scripts/21`).
- Of the 4,701 curated records, 2,886 holins were usable for training. The training set of the curated model has 3,250
  holins (364 original after removing the gold holdout, plus 2,886) and 13,351 records.

Decisions worth knowing:

- **Dual-start holin genes are positives, and flagged.** λ *S*, φ29 *gp14*, P21 *S21* and SPP1 holins are annotated by
  UniProt under the name of their long product ("antiholin") while TCDB files the gene in a phage holin family. The ORF
  is the holin gene, so it is labelled `holin` with `dual_start_or_antiholin: true`. An earlier version dropped these
  eight as label conflicts — which silently removed λ S, the most-studied holin of all, from the training data.
- **Prophage holins in bacterial proteomes count as phage-associated** (e.g. B. subtilis SPβ *bhlB*).
- Identical sequences are merged with all their sources kept; nothing is dropped silently — conflicts land in
  `data/processed/dropped_conflicts.json`. Sequences are never edited to fit a tool.

## What was found

1. **Curation added depth, not breadth.** 4,700 of 4,701 curated records joined families already present in the
   training set; only 1 formed a new family. Pfam is effectively exhausted as a source of new holin architectures.
   Only 7 of the 2,886 usable curated holins are Swiss-Prot reviewed; the rest are profile-match (Pfam) evidence, not
   verified holins.
2. **The long single-N-terminal-TM holins are recovered only if their family is present.** T4 holin T and T5 C1
   (~218 aa) were scored ~0.000 by the previous model. The curated model recovers them under the realistic protocol,
   but under strict removal they stay ~0.000: you cannot teach a family you then delete.
3. **The model generalises to small multi-TM class I holins and little else** (`reports/family_dependence.json`). Of 13
   annotated holins, 9 hold their score when their family is removed, 3 are family recognition only (T4 t, T5 C1,
   φ29 14), and 1 (P1 lydD) fails either way. This is 13 case-by-case observations, not rates.
4. **Curation has a cost.** Precision at score 0.9 fell from about 0.82 to 0.75 (realistic protocol). Use the **0.95**
   score threshold for high-confidence calls.
5. **No novel compositional signature survives proper controls.** Only C-terminal K+R enrichment is consistent against
   spanins, bacterial membrane proteins and the membrane subset of phage proteins, and that is the long-established
   charged C-terminal tail, not a discovery. A tempting glycine-zipper enrichment is an artifact of comparing against
   glycine-poor spanins: holins carry a GxxxG-spaced motif *less* often than ordinary bacterial membrane proteins
   (59.8% vs 68.9%) (`reports/signature_controls.json`).

Secondary check, with its caveat: on the frozen gold holdout (original negatives, i.e. no mined phage negatives and no spanins) the curated model has AP 0.8824
and recall at 95% precision 0.5309, against 0.8876 and 0.7062 for the pre-curation model. The holdout cannot see the
phage-protein regime the model is used in, and it is not a headline.

## Intervention ledger

| Intervention | Verdict | Why |
|---|---|---|
| Stacked specialist models (`scripts/10`) | **Rejected** | Lowered gold AP, miscalibrated threshold |
| Guarded self-training loop (`scripts/08`, `09`) | **Rejected, rolled back** | Did not beat baseline; spanin contamination in candidates |
| TM-anchored local features (`scripts/15`) | **Rejected** | Did nothing for target proteins, cost recall |
| Phage-derived negatives (`scripts/12`, `13`) | **Adopted** | Eliminated Rz-like spanin false positives, which no bacterial-negative-only model had ever seen |
| Curated Pfam holins (`scripts/19`–`22`) | **Adopted** | The headline gain above (realistic AP 0.823 to 0.9647; strict 0.625 to 0.7847) |

## Why the evaluation is grouped

Reported with a random train/test split, any holin classifier looks excellent, because near-identical holins land on both
sides of the split. Sequences are clustered by **exhaustive all-vs-all Smith-Waterman** (pyopal, BLOSUM62, gap 11/1; edge
at ≥30% identity and ≥50% coverage of the shorter sequence), with **greedy longest-first set-cover** clustering
(CD-HIT/MMseqs-style). Single linkage chained the whole set into one component and was rejected. Cross-validation is
`GroupKFold` over those clusters. The same folds score a **homology baseline** (best Smith-Waterman identity to the fold's
training holins, no learning); a model that cannot beat it is not finding anything new.

Grouped CV is necessary but not sufficient. It uses the original negatives only, so it cannot see the phage-derived regime
(spanins especially), and it has no way to say what happens for a family that is genuinely absent. That is why the LOGO
scan with two removal protocols is the headline.

## Features

- **Biophysical (36)** — length, hydropathy-based TM segment count and extent (Kyte-Doolittle, window 19, threshold 1.6),
  terminal charges, charged/hydrophobic fractions, amino-acid composition. The TM segments are a hydropathy heuristic
  used as a model input; they are not a topology prediction.
- **ESM-2** — `facebook/esm2_t12_35M_UR50D`, mean-pooled last layer (480-d), cached per sequence hash.

## Scanning a genome

```
python3 scripts/05_scan_genome.py --acc NC_001416.1 --annotated --holdout
```

`--annotated` scores the GenBank CDS translations; `--denovo` calls ORFs with Pyrodigal instead (an extra inference, and
the report says so). `--holdout` removes every training holin homologous to the scanned genome and retrains, which is the
only way a recovery claim on λ or T4 means anything. Without it, the report states plainly that the genome's own holin may
have been in training.

## Reproduce

```
pip install biopython pyopal pyrodigal scikit-learn torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers
# see PROTOCOL.md for the full ordered list, scripts 01-23
python3 scripts/01_fetch_data.py && python3 scripts/02_build_dataset.py && python3 scripts/03_cluster.py
python3 scripts/22_retrain_curated.py     # the LOGO headline, both protocols
python3 scripts/23_train_production.py    # saves the deployable model and model card
```

`data/raw/provenance.json` records where every input came from and when.

## Limitations

- **Strict-protocol performance is modest.** From a genuinely unseen family you get a shortlist, not an answer: holin
  strict AP is 0.613 (95% CI 0.49-0.74) over 53 annotated holins in 50 genomes. The 0.7847 reported earlier came from
  13 holins in 16 genomes and did not hold up on the larger panel (see `MANUSCRIPT.md` section 3.1).
- **Most positives are profile matches.** 4,497 of the positives are Pfam members of which only a handful are reviewed;
  "holin" for these means "matches a holin profile", and Pfam membership can be wrong.
- **Positives are biased toward studied families** and "putative" TCDB families are predictions themselves. Only 8
  entries have direct protein-level evidence.
- **Negatives are unlabelled, not verified non-holins:** Swiss-Prot phage proteins may include unrecognised holins, so
  measured precision is a lower bound and some "false positives" may be real.
- **Precision is the weak side:** the true gene is top-ranked in its genome only 50-70% of the time, and curation
  lowered holin precision. Use the per-class `high_conf` cut-offs for calls you will act on.
- **Long single-TM holins** (T4 t, T5 C1) are found only if their family is in training.
- The model scores proteins independently. It does not use genomic context (holins sit next to endolysin and spanin
  genes), which is the strongest signal a human curator uses.
- Nothing here distinguishes holin classes (canonical vs pinholin), predicts lysis timing, or says which membrane is
  involved.
