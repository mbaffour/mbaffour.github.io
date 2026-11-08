# Holin ML — learning to recognise holin genes

A reproducible pipeline that assembles **annotated and experimentally tested holins**, trains a classifier on them, and
scores every protein in a genome to propose holin candidates.

Holins are small phage membrane proteins that end an infection by permeabilising the inner membrane at a scheduled time.
They are notoriously hard to find by homology: dozens of unrelated families, short sequences, little conservation beyond
"small, hydrophobic, charged C-terminus". That is exactly the situation where a learned model can add something over a
BLAST/HMM search — but only if it is evaluated in a way that homology cannot fake. This project is built around that
evaluation, not around a headline number.

> Everything here is a **prediction**. A high score is a hypothesis to test at the bench, not a demonstrated holin.

## Status

Working end to end on the data below; the model is a first baseline and the numbers in `reports/` are the only claims made.

| Stage | Script | State |
|---|---|---|
| Fetch sources with provenance | `scripts/01_fetch_data.py` | done |
| Build labelled set | `scripts/02_build_dataset.py` | done |
| Homology clusters for leakage-free CV | `scripts/03_cluster.py` | done |
| Features (biophysical + ESM-2) | `scripts/features.py` | done |
| Train + evaluate vs homology baseline | `scripts/04_train.py` | running / see `reports/training_report.json` |
| Scan a genome | `scripts/05_scan_genome.py` | written, pending the trained model |

## The labelled set

`data/processed/dataset_summary.json` is generated, not hand-written. At the last build:

- **558 holins** — TCDB superfamily 1.E phage-holin families + Swiss-Prot phage holins, in three evidence tiers:
  `tested` (UniProt protein-existence 1, 8 entries), `curated` (482), `putative` (68, from TCDB families named "putative").
  61 distinct families are represented.
- **234 holin-like** — held out of training and scored separately as hard cases: dedicated antiholins, bacterial
  CidA/LrgA, Hok/Gef toxins, gene-transfer-agent and spore holin-like families, T4 superinfection immunity, Mu releasin.
- **9,503 negatives** — Swiss-Prot phage proteins (1,619) and Swiss-Prot bacterial membrane proteins of 30–250 aa (7,884),
  after removing anything whose name, family, function or keywords mention lysis (2,514 rows excluded).

Decisions worth knowing:

- **Dual-start holin genes are positives, and flagged.** λ *S*, φ29 *gp14*, P21 *S21* and SPP1 holins are annotated by
  UniProt under the name of their long product ("antiholin") while TCDB files the gene in a phage holin family. The ORF
  is the holin gene, so it is labelled `holin` with `dual_start_or_antiholin: true`. An earlier version dropped these
  eight as label conflicts — which silently removed λ S, the most-studied holin of all, from the training data.
- **Prophage holins in bacterial proteomes count as phage-associated** (e.g. B. subtilis SPβ *bhlB*), which a plain
  "is the organism a virus?" test misses.
- Identical sequences are merged with all their sources kept; an explicit holin annotation outranks membership of the
  generic negative pool. Nothing is dropped silently — conflicts land in `data/processed/dropped_conflicts.json`.
- Sequences are never edited to fit a tool.

## Why the evaluation is grouped

Reported with a random train/test split, any holin classifier looks excellent, because near-identical holins land on both
sides of the split. Here, sequences are clustered by **exhaustive all-vs-all Smith-Waterman** (pyopal, BLOSUM62, gap
11/1; edge at ≥30% identity and ≥50% coverage of the shorter sequence), with **greedy longest-first set-cover**
clustering (CD-HIT/MMseqs-style). Single linkage was tried first and rejected: it chained the whole set into one
component. Cross-validation is `GroupKFold` over those clusters, so no test sequence has a detectable local alignment to
anything the model trained on.

The control that matters: the same folds also score a **homology baseline** — the best Smith-Waterman identity to that
fold's training holins, no learning at all. A model that cannot beat it is not finding anything new.

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
python3 scripts/01_fetch_data.py      # UniProt, TCDB, InterPro; records URL, UTC time, SHA-256
python3 scripts/02_build_dataset.py
python3 scripts/03_cluster.py         # ~7 min on 4 cores
python3 scripts/04_train.py           # ESM embedding dominates the runtime; cached afterwards
python3 scripts/05_scan_genome.py --acc <accession> --annotated --holdout
```

`data/raw/provenance.json` records where every input came from and when.

## Limitations

- Positives come from two curated resources; both inherit the field's bias toward well-studied families, and "putative"
  TCDB families are predictions themselves. Only 8 entries have direct protein-level evidence.
- Negatives are *unlabelled*, not verified non-holins: Swiss-Prot phage proteins include unrecognised holins, so measured
  precision is a lower bound and some "false positives" may be real.
- The model scores proteins independently. It does not use genomic context (holins sit next to endolysin and spanin
  genes), which is the strongest signal a human curator uses.
- Nothing here distinguishes holin classes (canonical vs pinholin), predicts lysis timing, or says which membrane is
  involved.
