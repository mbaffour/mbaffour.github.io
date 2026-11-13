# Experimentally proven lysis genes, found from bare DNA

**Question.** The models score proteins from sequence alone, but until now they were graded against GenBank product
names. How do they do on phages whose lysis genes were proven experimentally, handled the way a newly sequenced phage
would be: no annotation at all?

**Set-up.**
- **Truth = experimental evidence.** UniProt Swiss-Prot phage proteins with evidence at protein level (PE=1) for host
  lysis or bacteriolytic activity, assigned by hand (`scripts/43_fetch_validated.py`; every exclusion and its reason is
  written there). Each was placed in its phage's complete genome by amino-acid sequence. Result: 22 endolysins,
  8 holins and 7 spanins in 24 genomes.
- **No annotation.** With `scripts/40_logo_benchmark.py --de-novo` each genome is reduced to bare DNA, genes are called
  with Pyrodigal, and the proven proteins are found among the called proteins by sequence. No product name or
  annotated coordinate is read.
- **Novel-phage conditions.** Before a genome is scored, the proven gene's whole family (every training protein >= 30%
  identical, whole homology clusters) is removed from training: the **novel family** test. The **known family** test
  removes only near-copies (>= 95%).
- **Metric = rank** of the proven gene among all proteins of its genome. A rank needs no label on any other protein, so
  unproven or unnamed lysins elsewhere in the genome cannot be miscounted. (AP is also in the JSON, but it treats every
  other protein as a non-lysin and is the wrong metric here.)
- Shipped recipes throughout: endolysin v1 positives with early stopping off; holin arm B and spanin v2 with the default.

## Results

### Bare DNA, novel family (the closest stand-in for a new phage from an unseen family)

| gene | proven genes scored | ranked 1st | in top 5 | median rank | P >= 0.5 |
|---|---|---|---|---|---|
| endolysin | 21 | 10 | **20** | 2 | 13 |
| holin | 8 | 7 | **7** | 1 | 7 |
| spanin | 4 | 3 | **3** | 1 | 3 |

### All four conditions (top 5 / scored)

| gene | annotated, known | annotated, novel | bare DNA, known | bare DNA, novel |
|---|---|---|---|---|
| endolysin | 22/22 | 21/22 | 21/21 | 20/21 |
| holin | 8/8 | 7/8 | 8/8 | 7/8 |
| spanin | 7/7 | 6/7 | 4/4 | 3/4 |

Bare DNA matches the annotated genes: the annotation contributes nothing to what the models find. The only cost of
bare DNA is genes the gene finder never produces (below).

### Per-genome ranks, endolysin, bare DNA, novel family

λ 1/62 · T4 1/265 · T7 1/51 · Mu 1/55 · φKZ 1/365 · φ29 1/25 · Cp-1 1/27 · Cp-7 1/29 · Dp-1 1/73 · 2638A 1/54 ·
P1 2/99 · T5 2/187 · PRD1 2/26 · K11 2/48 · KP32 2/49 · C1 (PlyCA) 2/26 · D29 3/76 · φKMV 3/52 · G15 4/213 ·
Twort 4/202 · **P22 9/66**

## What did not work

- **P22 endolysin (gene 19), rank 9 of 66, P = 0.000** under the novel-family test (rank 7 with annotated genes). The
  one endolysin miss. The P22 lysozyme's family is removed under this test, and nothing else in training resembles it
  closely enough.
- **T4 holin (t), rank 13 of 265, P = 0.002.** T4 t is an atypical holin: 218 aa, one transmembrane helix and a large
  periplasmic domain. Its family is removed under the novel-family test and the model has nothing like it left.
- **T1 u-spanin, rank 6 of 73.** A unimolecular spanin, a distinct architecture with almost no relatives in training.
- **Genes the gene finder never produces** (a gene-calling limit, before any model runs):
  - three o-spanins (λ Rz1, T7 18.7, Mu): each lies inside its i-spanin gene in another reading frame, and standard
    gene finders do not call nested genes;
  - phage K's endolysin LysK: its gene contains an intron, so from bare DNA it appears as two fragments (267 and 209 aa).

  **Fixed since** (`denovo_gene_calling.md`): a nested lipoprotein-ORF finder now recovers all three o-spanins (bare
  DNA, novel family: spanins in top 5 3/7 -> 6/7), and LysK is placed on its 267-aa catalytic fragment, ranked 3rd
  (endolysins in top 5 20/22 -> 21/22). On CPT the same finder lifts curated spanins in the top 5 from 61% to 76%.

## How to read a score on a novel phage

Under novel-family conditions many proven genes rank at or near the top **while scoring far below any threshold**: the
Mu endolysin is ranked 1st at P = 0.002, T4's at 0.003, the PlyC catalytic subunit 2nd at 0.001. Only 13 of 21
endolysins reach P >= 0.5. On a new phage, **read the top of the ranked list for each class, not the probability**.
That is what `scripts/32_predict_lysis.py` prints as the per-class shortlist, whatever the threshold.

## Limits

- Small: 21, 8 and 4 scorable genes. Six proven endolysins and one holin could not be used because their phages have
  no complete genome in NCBI.
- These are mostly classic model phages (λ, T4, T7, P22, φ29, staphylococcal and streptococcal phages). Phages from
  poorly sampled clades -- crAss-like phages, for example -- may be harder; DAC15 showed that.
- The proven proteins themselves are in the training data; the protocol removes them (and, under the novel-family
  test, their whole family) before each genome is scored.
