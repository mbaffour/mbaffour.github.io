# N4-like phages (Schitoviridae): blind lysis-gene scan

**Design.** Every GenBank complete N4-like genome (Schitoviridae) not already used for evaluation or training:
255 genomes from 29 host genera (Pseudomonas 79, Escherichia 43, Klebsiella 24, Vibrio 15, Erwinia 12, Achromobacter
10, Rhizobium 9, then marine Roseobacter-clade hosts and others). The shipped predictor ran on the DNA only
(`scripts/52b --set n4`); calls frozen in commit dc9418c before any annotation was read; then scored against each
genome's annotation with the fixed rules of `scripts/52c`.

## What the scan found (before looking at annotations)

- All three lysis genes called confidently in **237 of 255** genomes; in **210** they sit within 6 genes of each
  other.
- Cassette order, in the direction of transcription: **holin-endolysin-spanin 115**, endolysin-spanin-holin 72,
  endolysin-holin-spanin 22.
- 164 nested lipoprotein ORFs (embedded o-spanins), 0.64 per genome -- more than in the general blind sets.
- Median lengths: holin 105 aa, endolysin 189 aa, spanin 108 aa.

## Against the annotations

| | genomes annotating one | call is the annotated gene | annotated gene in top 5 |
|---|---|---|---|
| endolysin | 145 | **0.972** [0.945, 0.993] | **1.000** |
| spanin | 102 | 0.559 (pair-level **0.90**, below) | 0.990 |
| holin | 96 | 0.625 [0.531, 0.719] | 0.969 |

**Endolysin.** 58 of the annotated N4-like endolysins are < 30% identical to anything in training (a family the
model has never seen), and the call is right in 55 of them.

**Spanin.** In 34 more genomes the call overlaps the annotated spanin: it is the nested/overlapping partner of the
same pair. Counting either member of the pair, the call agrees in 91 of 101 genomes (0.90).

**Holin: two holin-family genes side by side.** In 33 of the 34 disagreements the called protein is the gene
immediately next to the annotated holin, and the annotated holin is ranked 2nd (in every case but one). The called
proteins are one recurring family (29 of 34 in one homology group, 104-124 aa), not homologous to any holin
annotated in the other N4 genomes, and scored higher than the annotated holin (P 0.975-1.000 vs 0.75-0.999). Both
genes are holin-family proteins by the training data's own labels (30-95% identical to training holins; the called
one nearest Pfam phage-holin-family proteins, the annotated one nearest TCDB 1.E.64 and the lambda holin family).
Annotations of the called family are inconsistent: "hypothetical protein", "tail length tape-measure protein"
(12 times, implausible for a ~110-aa protein), and in a few genomes "antiholin" / "antiholin/holin protein".

So N4-like lysis cassettes carry two adjacent holin-family membrane proteins; the annotation names one, the model
prefers the other. Which is the functional holin (and whether the other is an antiholin or a second holin) is a
biological question the sequences cannot settle; it needs experimental data. The practical reading: **for N4-like
phages, take the top two holin candidates** -- together they contain the annotated holin in 93 of 96 genomes.

Files: `reports/n4/pred/` (frozen calls), `score.json`, `blind_calls_summary.json`.
