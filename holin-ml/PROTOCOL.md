# Protocol: build and honestly evaluate a holin predictor

Paste everything below the line into Claude, ChatGPT, Gemini or any coding assistant with shell access. It gives the
method and the traps, not the answers, so the assistant has to do the work and you can check what it reports against
the reference results at the end. Bracketed fields are yours. The same structure transfers to any "find protein family
X in genomes" problem: swap the sources, the positives and the hard cases.

---

You are helping me build a machine-learning model that finds **holin genes** in phage and bacterial genomes, and — more
importantly — an evaluation that says honestly whether it works. Carry the work out; do not stop at a plan. Use real
downloads and real model output, keep provenance for everything, and never let a plausible number stand in for
something you did not measure. If a result looks too good, find the leak before reporting it.

## My project

- Target class: **holins** — small phage proteins that permeabilise the host inner membrane to schedule lysis
- Output folder: **[ABSOLUTE PATH]**
- Compute: **[CPU ONLY / GPU, CORES, RAM]** (everything below runs on 4 CPU cores and 16 GB in ~2 h, excluding downloads)
- May I submit public sequences to public web services? **[YES / NO / ASK FIRST]**
- Genomes I care about most: **[ACCESSIONS]**
- Python: `biopython pyopal pyrodigal scikit-learn numpy torch (CPU wheel) transformers`

## 0. Why this problem punishes sloppiness

Holins are the worst case for homology search: dozens of unrelated families, 60–150 aa, no conserved motif beyond
"small, hydrophobic, basic C-terminus". Two consequences shape everything below.

- A classifier trained and tested on holins that are near-duplicates looks excellent and is useless. Every split is
  grouped by sequence homology.
- If the model cannot beat a plain alignment search, it has added nothing. Build that baseline first and keep reporting
  it beside the model even when the model wins.

## 1. Sources, with provenance

Record for every download: URL, UTC timestamp, SHA-256, byte count and database release.

- **TCDB** superfamily **1.E** (the holin superfamily): `https://www.tcdb.org/public/tcdb` (all sequences, FASTA headers
  carry the TC id) and `https://www.tcdb.org/cgi-bin/projectv/public/families.py` (family names).
- **UniProtKB/Swiss-Prot** via `https://rest.uniprot.org/uniprotkb/stream`, TSV, fields including `protein_existence`,
  `protein_families`, `cc_function`, `keyword`, `xref_tcdb`, `lineage_ids`, `sequence`. Four queries:
  - positives: `reviewed:true AND (protein_name:holin OR family:holin OR protein_name:antiholin OR protein_name:pinholin)`
  - phage negatives pool: `reviewed:true AND taxonomy_id:10239 AND virus_host_id:2`
  - bacterial negatives pool: `reviewed:true AND taxonomy_id:2 AND length:[30 TO 250] AND ft_transmem:*`
  - (optional, unused for training) `reviewed:false AND family:holin`
- **InterPro/Pfam** holin entries, for cross-reference only.

Expect roughly 740 TCDB 1.E sequences, ~145 Swiss-Prot holin entries, ~2,000 Swiss-Prot phage proteins and ~13,000
bacterial small membrane proteins. If your counts differ by a lot, say so rather than proceeding quietly.

## 2. Labels, and the traps in them

Three classes:

- **holin** (positives) — TCDB 1.E members of *phage* holin families, plus Swiss-Prot phage holins. Tag each with an
  **evidence tier** and never blur the tiers in a reported number:
  - `tested` — UniProt protein-existence 1 (evidence at protein level)
  - `curated` — reviewed entry, or a named phage holin family in TCDB
  - `putative` — TCDB families whose own name says "putative"
- **holin-like** (held out of training, scored separately as hard cases) — dedicated antiholins and CidB/LrgB, bacterial
  CidA/LrgA, Hok/Gef toxins, TcdE, gene-transfer-agent release holins, Bacillus spore germination holin-like, T4
  superinfection immunity, phage Mu releasin, archaeal putative holins. In TCDB these are families 1.E.9, .14, .19,
  .23, .42, .43, .52, .53, .54, .55, .66, .70, .72.
- **negative** — the two Swiss-Prot pools, after dropping anything whose name, family, function or keywords match
  `holin|pinholin|lysis|lytic|spanin|endolysin|lysozyme|lysin|murein|peptidoglycan|cell wall hydrolase|amidase|
  transglycosylase|rz|rz1|releasin|immunity`, or that carries a TCDB 1.E cross-reference. Say explicitly that these are
  **unlabelled**, not verified non-holins.

Three traps that each cost me a wrong result:

1. **Dual-start holin genes.** λ *S*, φ29 *gp14*, P21 *S21* and SPP1 are annotated by UniProt under the name of their
   long product ("antiholin") while TCDB files the same gene in a phage holin family. Treating that as a label conflict
   and dropping it silently removed λ S — the most-studied holin in existence — from my training set. Label the ORF a
   **holin**, flag it `dual_start_or_antiholin`, and print the affected entries (there were 8).
2. **Prophage holins live in bacterial proteomes** (e.g. B. subtilis SPβ *bhlB*, UniProt O31984/Q99163), so a
   "is the organism a virus?" test misses them. Count prophage-derived names and holin-family membership as
   phage-associated.
3. Merge identical sequences keeping all sources; let an explicit holin annotation outrank membership of the generic
   negative pool; write any remaining conflicts to a file instead of discarding them. Never edit a sequence to make a
   tool accept it — record the reason it is ineligible instead.

Report final counts by label, tier and family, generated from the data.

## 3. Homology clusters, before any split

All-vs-all **Smith-Waterman** (BLOSUM62, gap open 11 / extend 1). With a vectorised library (`pyopal`) an exhaustive
~10,000 × 10,000 comparison of short proteins takes about 7 minutes on 4 cores, so **do not reach for a k-mer prefilter
without measuring its recall** — mine recovered only ~10% of true holin-holin pairs and I discarded it.

Call two sequences related at **≥30% identity over ≥50% of the shorter sequence**. Cluster **greedily, longest-first**
(CD-HIT / MMseqs style): each unassigned sequence becomes a centroid and absorbs its unassigned neighbours.
**Do not use single linkage** — I tried, and chaining merged all 10,000 proteins into one component, which makes
grouped cross-validation meaningless. Print the cluster-size distribution so that failure is visible if it recurs.
Expect ~1,000 clusters, ~140 of them containing holins.

## 4. Features

Compute both and compare them separately as well as combined, so the language model's contribution is visible:

- **Biophysical (~36 numbers)** — length and log length; hydropathy-based TM segment count, total extent, first-segment
  position and C-terminal tail length (Kyte-Doolittle, window 19, threshold 1.6, minimum 15 residues); net charge of the
  N-terminal 20 and C-terminal 20/30 residues; charged, hydrophobic and G+P fractions; amino-acid composition. State in
  the write-up that these TM segments are a **hydropathy heuristic used as a model input**, not a topology prediction.
- **Protein language model** — ESM-2 `facebook/esm2_t12_35M_UR50D`, mean-pooled last hidden layer (480-d). ~12 minutes
  for 10,000 short proteins on 4 CPU threads. Cache per sequence SHA-256; you will re-embed often. Window sequences
  longer than 1,022 residues and average by length.

## 5. Evaluation — the part that decides whether any of this is real

Report all seven, together:

1. **Homology baseline.** Per fold, score each test protein by its best Smith-Waterman identity to that fold's
   *training* holins. No learning. This is the number to beat.
2. **Homology-grouped cross-validation.** `GroupKFold(5)` over the step-3 clusters. Report AUROC, average precision and
   recall at 90/95/99% precision. With ~5% positives, average precision and recall-at-precision matter; AUROC flatters.
3. **Per-family recall** from out-of-fold scores at a fixed high-precision threshold, and name the families missed
   entirely. One overall number hides that holins are not one thing.
4. **Recall by evidence tier** — `tested`, `curated`, `putative` separately.
5. **Leave-one-family-out.** Delete an entire TCDB family *plus anything sharing a homology cluster with it* from
   training, then score its members. This is the "new family" test and the only number that speaks to unstudied phages.
   Expect it to be far worse than the grouped-CV figure. Report it prominently.
6. **Hard cases.** Score the held-out holin-like set, median per category. Antiholins and toxins scoring low is evidence
   the model learned something specific; functionally holin-like proteins (releasins, GTA release holins) scoring high
   is interesting rather than wrong — say so.
7. **Leave-one-genome-out recall.** For each genome with a known holin: remove from training every holin homologous to
   *any* protein of that genome, refit, score every protein, report the rank of the true holin among all proteins.

**The trap in step 7 that cost me a false conclusion.** If "homologous" means identity and coverage alone, short
spurious local alignments fire constantly. Scanning T4 that way removed **556 of 558** training holins, leaving two
positives, and the model then "failed" on T4's holin at rank 92 — an artifact of my filter. Require a real alignment
score too: at **SW ≥ 80** the same genome removed 14. Report how many holins each genome's holdout removed, so the
problem is visible rather than buried.

## 6. Scanning a genome

Support both and label which was used: the GenBank record's own CDS translations, and *de novo* calls (Pyrodigal, meta
mode — an extra inference). For each candidate report score, length, hydropathy TM count, coordinates, strand and
neighbouring gene products: holins sit beside endolysin and spanin genes, so a lone high scorer inside a structural
module deserves more doubt than one next to a spanin.

Where the model disagrees with the deposited annotation, say so plainly and do not resolve it by assuming either side
is right.

## 7. Reporting rules

Every count, score and date generated from data, nothing hard-coded. Model, features, thresholds and database releases
stated beside the numbers. A limitations section covering at least: negatives are unlabelled so precision is a lower
bound; curated positives inherit the field's bias toward studied families; `putative` entries are themselves
predictions; the model scores proteins in isolation and ignores genomic context, the strongest clue a curator uses;
nothing distinguishes canonical holins from pinholins, predicts lysis timing, or identifies which membrane is involved.
Every high score is a hypothesis for the bench, not a demonstrated holin.

## 8. Reference results to compare against

From one run of this protocol (10,295 sequences: 558 holins in 61 families, 234 holin-like, 9,503 negatives; 1,034
clusters). Your numbers will differ with database releases — large divergence means something is wrong.

| Model (grouped CV) | AUROC | Avg precision | Recall @P90 |
|---|---|---|---|
| Homology baseline (SW identity, no ML) | 0.736 | 0.306 | 0.147 |
| Biophysical + logistic regression | 0.837 | 0.274 | 0.002 |
| Biophysical + gradient boosting | 0.955 | 0.759 | 0.428 |
| ESM-2 + logistic regression | 0.980 | 0.872 | 0.704 |
| ESM-2 + gradient boosting | 0.989 | 0.909 | 0.767 |
| **Both + gradient boosting** | **0.990** | **0.915** | **0.792** |

Recall at 95% precision by tier: tested 0.63, curated 0.69, putative 0.44.

Leave-one-genome-out (SW ≥80 holdout), rank of the known holin among all proteins: λ 1 & 2/73, T7 1/60, P2 1/43,
φ29 1/27, SPP1 1 & 2/97, P22 1 & 2/72, φKMV 1/49, D29 1/79, Dp-1 1/72, Cp-1 1/25 — **10 of 14 at rank 1, 13 of 14 in
the top 3**. The exception is real: **T4 holin T ranks 116/278 at score 0.023** with 544 holins still in training. At
218 aa with a large C-terminal cytoplasmic domain it sits outside the length and architecture the model learned, and
T4's Rz-like spanin outranks it. A protocol that does not surface a failure like this is hiding one.

Leave-one-family-out, recall at 95% precision, is **much lower** and is the honest generalisation number: PRD1 P35 0.77,
SPP1 0.75, M2 mycobacterial 0.61, λ S 0.58, T7 0.50, φ11 0.28, LydD 0.27, Holin LLH 0.21, and **0.00** for both
Actinobacterial Holin-X and the mycobacterial 4-TMS family. Treat a single headline figure from grouped CV as an upper
bound on what you will see in a genuinely new family.

## 9. What to add next

- Genomic context as a feature: distance to the nearest endolysin/spanin, position in the lysis cassette.
- Calibrated probabilities (isotonic or Platt on held-out folds) so a score is comparable across genomes.
- A larger ESM-2 on GPU, measured against the 35M model rather than assumed better.
- Explicit handling of long, multi-domain holins (the T4 failure mode) and of dual-start motifs.
