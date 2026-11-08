# Reusable prompt: build and honestly evaluate a holin predictor

Copy everything below the line into Claude, ChatGPT, Gemini or any coding assistant with shell access. It describes the
method, not the answers, so the assistant has to do the work and can be checked against what it reports. Bracketed fields
are yours to fill. The same structure works for any "find protein family X in genomes" problem: swap the sources,
positives and hard cases.

---

You are helping me build a machine-learning model that finds **holin genes** in phage and bacterial genomes, and — more
importantly — an evaluation that tells me honestly whether it works. Carry the work out; do not stop at a plan. Use real
downloads and real predictor output, keep provenance for everything, and never let a number stand in for something you
did not actually measure.

## My project

- Target class: **holins** (small phage proteins that permeabilise the host inner membrane to end infection)
- Output folder: **[ABSOLUTE PATH]**
- Compute available: **[CPU ONLY / GPU / CORES / RAM]**
- Time budget: **[HOURS]**
- May I submit public sequences to public web services? **[YES / NO / ASK FIRST]**
- Genomes I care about most: **[ACCESSIONS, e.g. my own phage]**

## 1. Why this problem needs care

Holins are the worst case for homology search: dozens of unrelated families, 60–150 aa, almost no conserved motif beyond
"small, hydrophobic, charged C-terminus". Two consequences drive the whole design:

- A classifier trained and tested on holins that are near-duplicates of each other will look excellent and be useless.
  Every evaluation below is grouped by sequence homology for this reason.
- If the model cannot beat a plain alignment search, it has added nothing. Build that baseline first and keep reporting
  it next to the model, even when the model wins.

## 2. Build the labelled set, and show your working

Pull positives from at least two independent curated resources, and record for every download the URL, the UTC time, the
SHA-256 and the database release:

- **TCDB** superfamily **1.E** (the holin superfamily), sequences plus family names
- **UniProtKB/Swiss-Prot** entries named or classified as holin, with the `protein_existence` field

Label each positive with an **evidence tier**, and never let the tiers blur together in a reported number:

- `tested` — UniProt protein-existence 1 (evidence at protein level)
- `curated` — reviewed entry, or a named phage-holin family in TCDB
- `putative` — families whose own name says "putative"

Hold out a third class, **holin-like**, from training and score it separately as hard cases: dedicated antiholins,
bacterial CidA/LrgA, Hok/Gef toxins, gene-transfer-agent and spore holin-like families, superinfection-immunity
proteins, releasins. These are what a naive model gets wrong, and watching their scores tells you what it learned.

Negatives: phage proteins and bacterial membrane proteins of similar length from the same curated database, after
removing anything whose name, family, function or keywords mention lysis. State plainly that these are **unlabelled**,
not verified non-holins, so measured precision is a lower bound.

Traps I hit, which you should check for explicitly and report on:

- **Dual-start holin genes.** λ *S*, φ29 *gp14*, P21 *S21* and SPP1 are annotated by UniProt under the name of their
  long product ("antiholin") while TCDB files the same gene in a phage holin family. Treating that as a label conflict
  and dropping it silently deletes λ S — the most-studied holin there is — from training. Label the ORF a holin and flag
  it. Print the eight or so affected entries so I can see them.
- **Prophage holins live in bacterial proteomes** (e.g. B. subtilis SPβ *bhlB*), so "is the organism a virus?" misses
  them. Treat prophage-derived and holin-family entries as phage-associated.
- Merge identical sequences and keep all their sources; let an explicit holin annotation outrank membership of the
  generic negative pool; write any remaining conflicts to a file rather than discarding them quietly.
- Never edit a sequence to make a tool accept it.

Report the final counts by label, tier and family, generated from the data rather than typed by hand.

## 3. Cluster by homology before you split anything

Compute **all-vs-all local alignment** (Smith-Waterman, BLOSUM62, gap open 11 / extend 1). An exhaustive comparison of
~10,000 short proteins takes a few minutes on four cores with a vectorised library, so do not reach for a k-mer
prefilter without measuring it: mine recovered only ~10% of true holin-holin pairs and I threw it away.

Call two sequences related at **≥30% identity over ≥50% of the shorter sequence**. Then cluster **greedily,
longest-first** (CD-HIT / MMseqs style): each unassigned sequence becomes a centroid and absorbs its unassigned
neighbours. Do not use single linkage — I tried, and it chained all 10,000 proteins into one component, which makes
grouped cross-validation meaningless. Print the cluster-size distribution so the chaining failure is visible if it
happens.

## 4. Features

Compute both, and compare them separately as well as combined, so I can see what the language model is contributing:

- **Biophysical, interpretable (~36 numbers)** — length, hydropathy-based transmembrane segment count and extent
  (Kyte-Doolittle, window 19, threshold 1.6), N- and C-terminal net charge over 20–30 residues, charged and hydrophobic
  fractions, amino-acid composition. Say in the write-up that these TM segments are a hydropathy heuristic used as a
  model input, not a topology prediction.
- **Protein language model embeddings** — ESM-2 (`facebook/esm2_t12_35M_UR50D` is enough on CPU and runs ~10,000 short
  proteins in ~12 minutes on four cores), mean-pooled over residues. Cache per sequence hash; you will re-embed often.

## 5. Evaluation — the part that decides whether any of this is real

Run all of these and report them together:

1. **Homology baseline.** For each cross-validation fold, score every test protein by its best Smith-Waterman identity
   to that fold's *training* holins. No learning. This is the number to beat.
2. **Homology-grouped cross-validation.** `GroupKFold` over the clusters from step 3. Report AUROC, average precision,
   and recall at 90/95/99% precision — average precision and recall-at-precision matter here, because the class is ~5%
   of the data and AUROC flatters it.
3. **Per-family recall**, from the out-of-fold scores, at a fixed high-precision threshold. Name the families the model
   misses entirely. An overall number hides that holins are not one thing.
4. **Recall by evidence tier.** Report `tested`, `curated` and `putative` separately.
5. **Leave-one-family-out.** Delete an entire TCDB family — plus anything sharing a homology cluster with it — from
   training, then score its members. This is the "new family" test and the only one that speaks to unstudied phages.
   Expect it to be clearly worse than the grouped-CV number; report it anyway, prominently.
6. **Hard cases.** Score the held-out holin-like set and report median score per category. Antiholins and toxins scoring
   low is evidence the model learned something specific; functionally holin-like proteins (releasins, GTA release
   holins) scoring high is interesting rather than wrong, and is worth saying so.
7. **Leave-one-genome-out recall.** For each genome with a known holin: remove from training every holin homologous to
   *any* protein of that genome, refit, score every protein, and report the rank of the true holin.

A trap in step 7 that cost me a false conclusion: if "homologous" means identity and coverage alone, short spurious
local alignments match constantly. Scanning T4 that way removed **556 of 558** training holins, leaving two positives,
and the model then "failed" to find T4's holin at rank 92 — an artifact of my filter, not a result. Require a real
alignment score as well (SW ≥ 80 with BLOSUM62 removed 14 instead of 556). Report how many holins each genome's holdout
removed, so this is visible rather than buried.

## 6. Scanning a genome

Support both, and say in the output which was used:

- the GenBank record's own CDS translations, and
- *de novo* gene calls (Pyrodigal, meta mode) — an extra inference, and label it as one.

For every candidate report: score, length, hydropathy TM count, coordinates, strand, neighbouring gene products. Holins
sit beside endolysin and spanin genes, so show me the neighbourhood; a lone high-scoring protein in the middle of a
structural module deserves more doubt than one sitting next to a spanin.

Where the model disagrees with the deposited annotation, say so plainly and do not resolve it by assuming either side is
right. On my phage the top-scoring protein was not the one GenBank labels "holin" — that disagreement is a result, not
an error to be smoothed over.

## 7. Report

- Every count, score and date generated from the data; nothing hard-coded.
- Model, feature set, thresholds and database releases stated with the numbers.
- Limitations in their own section, specifically: negatives are unlabelled, so precision is a lower bound; curated
  positives inherit the field's bias toward studied families; `putative` entries are themselves predictions; the model
  scores proteins in isolation and ignores genomic context, which is the strongest clue a curator uses; nothing here
  distinguishes canonical holins from pinholins, predicts lysis timing, or identifies which membrane is involved.
- Every high score is a hypothesis for the bench, never a demonstrated holin.

## 8. What I would add next, if you have time

- Genomic context as a feature: distance to the nearest endolysin/spanin, position within the lysis cassette.
- Calibrated probabilities (isotonic or Platt on held-out folds) so a score means something across genomes.
- A larger ESM-2 if a GPU is available, measured against the 35M model rather than assumed to be better.
- Dual-start motif detection, since the holin/antiholin pair is a real functional distinction this model ignores.
