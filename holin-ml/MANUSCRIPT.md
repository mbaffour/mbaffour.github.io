# Sequence-only machine-learning identification of phage lysis genes — holins, endolysins and spanins — across bacteriophage diversity

**Draft manuscript (in preparation).** Code, data provenance and all result files in this repository.
Corresponding work: Michael Baffour Awuah, Center for Phage Technology.

---

## Abstract

Bacteriophages end infection by lysing the host cell with a small cassette of genes: a **holin** (triggers inner-membrane permeabilization and sets lysis timing), an **endolysin** (degrades peptidoglycan), and, in Gram-negative hosts, a **spanin** system (disrupts the outer membrane). These genes are short, fast-evolving and frequently mis- or un-annotated, and they do not always sit together in the genome. We built three protein classifiers — one per gene class — from hand-crafted biochemical features and ESM-2 protein-language-model embeddings, trained one-vs-rest so that each class is separated from the other two and from bulk bacterial and phage proteins. Under homology-controlled leave-one-genome-out scanning of 66 genomes carrying 180 annotated lysis genes, genome-scan average precision is **0.75** for a holin from a known family in a new phage and **0.61** for a never-before-seen family; endolysin reaches **0.81/0.61** and spanin **0.80/0.57**. The true gene is among the top five proteins of its genome 87–100 % of the time but ranked first only 50–70 %, so the classifiers are best used as shortlist generators, paired with lysis-domain HMM evidence that recovers genes the model under-scores. Applied to 300+ diverse phage genomes — including actinobacterial hosts — the caller recovers annotated lysis genes at high rates and runs directly on raw nucleotide assemblies via de-novo gene calling. Beyond recovery, a systematic analysis uncovered a reproducible biological signal: because the classifier has **no positional input**, its tendency to call a *second* holin-fold gene immediately next to the annotated holin cannot be an artefact of genomic context — and we show these second genes cluster adjacent to the first far more than chance (median 2 vs 22 genes apart), are membrane proteins with holin signatures, and are frequently either annotated second holins, holin–antiholin pairs, or un-annotated candidates. We release the models, a single-command tool that accepts protein or nucleotide input, and a Galaxy wrapper.

---

## 1. Background

The phage lysis cassette is one of the most intensively studied small genetic modules in molecular biology, yet it remains hard to annotate automatically. Holins in particular are extraordinarily diverse at the sequence level — they have been classed into dozens of unrelated families (TCDB superfamily 1.E) with little or no detectable homology between them — so homology search (BLAST/HMM) misses holins from families not already in the reference set. Endolysins are modular enzymes spanning many catalytic folds; spanins are small, membrane-embedded, and under-annotated. A method that recognises these genes from sequence *character* rather than only from homology would help close the annotation gap, especially for the under-characterised phages that dominate metagenomes.

This work asks a narrow, testable question: **can a protein-language-model classifier identify each lysis gene class across phage diversity, and does it generalise beyond the families it was trained on?** We hold ourselves to homology-controlled evaluation throughout, because the central failure mode of "ML finds known genes" is measuring recovery of training data.

## 2. Methods

### 2.1 Data

Positives were assembled per class from UniProt (reviewed and, where needed for depth, phage-taxonomy TrEMBL), Pfam/InterPro family members restricted to phage taxonomy, TCDB, the mined phage pool (below), and, for spanins, the curated Center for Phage Technology dataset from Kongari *et al.* 2018 (BMC Bioinformatics; Additional file 2). Final deduplicated, homology-clustered positive sets:

| class | positives | clusters | evidence tiers |
|---|---|---|---|
| holin | 558 + 4,497 curated | — | Swiss-Prot/TCDB + Pfam family depth |
| endolysin | 1,529 | 229 | 378 validated (PE=1), 83 reviewed, 418 pool-annotated, 650 Pfam |
| spanin | 2,045 | 185 | 10 validated, 18 reviewed, **910 CPT-curated (Kongari 2018)**, 25 pool, 1,023 phage TrEMBL, 59 Pfam |

Negatives (shared, 9,503 + 3,382): 7,884 bacterial transmembrane proteins + 1,619 Swiss-Prot phage proteins, plus 3,382 phage proteins mined from 300 RefSeq genomes specifically to include the **hard confusables** the original set lacked — above all 101 Rz-like spanins and proteins drawn from lysis-cassette neighbourhoods. For each one-vs-rest model the negatives also include the *other two* lysis classes, forcing the model to separate holin from endolysin from spanin rather than merely "lysis-like from not."

Every external source is recorded with its URL, retrieval time and SHA-256 (`data/raw/*/provenance.json`); bulk sequence dumps are regenerable and excluded from version control.

### 2.2 Features and models

Each protein is represented by 36 hand-crafted biochemical features (length, transmembrane-segment count and fraction from a Kyte–Doolittle scan, terminal charges, amino-acid composition, hydrophobic-moment proxies) concatenated with a 480-dimensional mean-pooled embedding from **ESM-2** (`facebook/esm2_t12_35M_UR50D`), for a 516-dimensional vector. The classifier is a histogram gradient-boosted decision tree (scikit-learn `HistGradientBoostingClassifier`, 400 rounds, 31 leaves, learning rate 0.06). The shipped endolysin model trains **without early stopping**: scikit-learn's default enables it above 10,000 rows using a random 10 % validation split, which in homology-rich data is full of near-copies of the training rows. That stopped training at 104 of 400 rounds, and removing it raised realistic LOGO AP by 0.046 (paired 95 % CI +0.017 to +0.070) without affecting the strict protocol (`reports/capacity_sweep.md`). Because the resulting probabilities are more extreme, high-confidence thresholds are set per class (§3.1). We tested and **rejected** a transmembrane-anchored local-feature representation (it did not help the hard long-holin cases and cost recall; §3.2).

### 2.3 Leakage control and evaluation

The project's discipline is that no performance number is trusted unless homology leakage between train and test is controlled:

- **Homology clustering.** All sequences are clustered by exhaustive Smith–Waterman identity (greedy set-cover; a k-mer prefilter was rejected for ~10 % edge recall, and single-linkage for chaining). Splits never place homologues on both sides.
- **Frozen gold hold-out.** 20 % of clusters per class, chosen once with a fixed seed, never used for model selection. It is frozen only *within* a dataset version: rebuilding a class's dataset re-clusters it, and the same seed then draws different clusters (an endolysin rebuild moved the held-out share from 13 % to 23 % of positives). Gold-hold-out scores are therefore never compared across dataset versions.
- **Leave-one-genome-out (LOGO) genome scan.** For each evaluation genome we remove the target gene's homologues from training before scoring that genome, and report two protocols: **realistic** (remove ≥95 % identical near-duplicates — a newly sequenced phage whose gene belongs to a *known* family) and **strict** (remove the whole family at ≥30 % identity — a *never-seen* family). This is the honest deployment estimate.

A recurring, important subtlety we surfaced and report throughout: **a genome being out-of-sample does not make its genes out-of-sample**, because characterised phages' lysis genes are in the public databases regardless of which genome they sit in. We therefore always report the exact-sequence in-sample fraction alongside any recovery rate.

## 3. Results

### 3.1 Classifier performance (homology-controlled)

Leave-one-genome-out genome-scan performance over every annotated lysis gene in a 66-genome panel (`scripts/40_logo_benchmark.py`; 95 % CIs by bootstrap over genomes):

| gene | genes / genomes | realistic LOGO AP | strict LOGO AP | top-1 (real./strict) | recall@5 (real./strict) |
|---|---|---|---|---|---|
| holin | 53 / 50 | **0.754** (0.66–0.84) | **0.613** (0.49–0.74) | 0.70 / 0.66 | 0.98 / 0.93 |
| endolysin | 95 / 63 | **0.809** (0.73–0.88) | **0.614** (0.51–0.73) | 0.58 / 0.59 | 0.93 / 0.87 |
| spanin | 32 / 19 | **0.800** (0.67–0.94) | **0.568** (0.43–0.80) | 0.56 / 0.50 | 1.00 / 0.97 |

These replace the figures from an earlier, smaller evaluation — holin 0.965 / 0.785, endolysin 0.843 / 0.729, spanin 0.834 / 0.729 — which rested on 12–16 genomes and 13–19 annotated genes per class and carried confidence intervals too wide to separate any two models. On the larger panel every class is lower, and the apparent lead of the holin model largely disappears.

Reading: the right use is a **ranked shortlist**. For a new phage the true gene is in the top five almost always, but it is the single top-ranked protein only about 60 % of the time. For a genuinely novel family (strict) the shortlist still usually contains it (recall@5 0.87–0.97), at lower precision. With the endolysin class's 95 truths across 63 genomes, paired differences between models are resolvable only above about 0.05 AP; smaller claimed gains on this panel should be read as unmeasured.

**High-confidence calls use per-class cut-offs**, read from each model file and reported in the `high_conf` column: 0.95 for holin and spanin, **0.9995 for endolysin**. The endolysin model's probabilities are more extreme (§2.2); at 0.9995 it gives precision 0.976 / recall 0.421 (realistic) and 0.913 / 0.221 (strict), which beats the previous endolysin model at 0.95 on all four measures. That cut-off was chosen on the same panel it is reported on, so it is mildly optimistic.

**Validation on curated and experimental evidence.** Product names are an imperfect yardstick, so the models were
also tested against two sets graded without them. On **130 CPT genomes** whose lysis genes were curated by hand
(125 endolysins, 78 holins, 162 spanins), the curated gene is in the top five proteins of its genome for 91 % of
endolysins, 85 % of holins and 88 % of genomes' spanins under the novel-family protocol (95 %, 94 % and 96 % for known
families) (`reports/cpt_benchmark.md`). On **24 genomes with experimentally proven lysis genes** (UniProt, evidence at
protein level), reduced to bare DNA and re-called with Pyrodigal so that no annotation is used at all, the proven gene
is in the top five for 20 of 21 endolysins, 7 of 8 holins and 3 of 4 spanins under the same protocol
(`reports/validated_benchmark.md`). The two sets agree.

A blind scan of 152 phage genomes published after the training data (DNA only, calls frozen before the annotations
were read) put the annotated holin, endolysin and spanin in the top five ~96% of the time. Its main confident error,
calling tail lysozymes as endolysins, traced to 51 virion proteins among the endolysin training positives; moving them
to the negatives raised unseen-family ranked-first on CPT from 0.664 to 0.720 (+0.056, 95% CI +0.016 to +0.103) and,
on a second fresh blind set of 123 genomes, the share of genomes where the endolysin call is the annotated one from
0.860 to 0.921 (+0.061, +0.018 to +0.114) (`reports/blind/blind_scan.md`, `reports/endolysin_virion_fix.md`).

Standard gene finders do not call genes embedded in another gene's reading frame, and embedded o-spanins are exactly
that: from bare DNA, Pyrodigal does not produce 48 of CPT's 162 curated spanins. A narrow finder for nested ORFs that
begin with a lipoprotein signal (0.5 extra ORFs per genome) recovers 24 of them, and raises the share of curated
spanins in their genome's top five, from bare DNA under the novel-family protocol, from 61 % to 76 % (+14.8 points,
95 % CI +9.9 to +19.9); on the experimental set it recovers all three missed o-spanins (6 of 7 spanins in the top
five) (`reports/denovo_gene_calling.md`). It is on by default for raw assemblies.

Two genomes in the 66-genome panel were present twice (an accession with and without its version suffix); removing the
copies lowers the endolysin figures by 0.005-0.009 AP, below the panel's resolution.

**Genomic context and calling.** Lysis genes sit together, but each model scores a protein alone. Re-ranking each
class with the strongest other-class score among a protein's neighbours (z = logit P + beta x neighbouring score;
`scripts/46_context_rerank.py`, parameters tuned on the CPT set) raises the fraction of curated genes ranked first, in
5-fold cross-validation over CPT genomes, by 10 points for holins (54 -> 64 % novel family; 71 -> 81 % known; 95 % CIs
exclude zero), 4-6 points for endolysins and 4 points for spanins (best per genome), with no measure made worse. The
predictor now names one gene per class per genome, **confident** when its context score clears a measured cut-off or
it carries a catalytic lysis domain. A learned second-stage caller over all three scores, neighbour scores, genome
rank and protein shape was also built. Cross-validated by genome it appeared to raise novel-family holins ranked first
from 62 % to 82 %, but with related phages kept in the same fold that gain vanished: it had learned families from shape
in sibling genomes. It is used only for spanins, where lipobox and membrane topology generalise across families (top
pick correct 0.91 known / 0.80 novel, against 0.83 / 0.73 for the context rule). Family-grouped, out of fold, confident
calls are correct 95 % (endolysin), 93 % (holin) and 98 % (spanin) of the time for known families, and 85 %, 90 % and
98 % for novel ones (`reports/integrated_caller.md`).

**Training on evidence only.** The shipped endolysin model is trained only on evidence-backed labels -- UniProt
protein-level evidence, Swiss-Prot review, or a lysis Pfam domain -- with the 368 positives labelled from genome
product names removed. Paired on 119 CPT genomes it is indistinguishable from the model it replaced (ranked first
-0.024 novel, +0.040 known, neither significant) and ranks 15 of 22 experimentally proven endolysins first (was 12).
For spanins, removing all 760 name-labelled TrEMBL entries improved novel-family recall (top five +6.2 points,
p = 0.008) but cost known-family ranking (-4.3 points, p = 0.002). Keeping only those whose label is corroborated by a
sequence signal (an o-spanin lipobox or i-spanin topology) kept the novel-family gain (+5.6, p = 0.049) without the
loss, and is the shipped spanin model (`reports/evidence_only.md`).

### 3.2 What worked and what did not

Four interventions were attempted under the same guards; two were adopted and two rejected, each on its own evidence:

| intervention | outcome |
|---|---|
| Stacked specialist models (window/actino/short + gated stacker) | **rejected** — lowered gold AP; blending miscalibrated the decision threshold |
| Guarded self-training on the mined pool | **rejected, rolled back** — did not beat baseline; candidate set was contaminated by spanins |
| TM-anchored local features | **rejected** — no gain on the target long-holin cases, cost recall |
| Phage-derived hard negatives (incl. spanins) | **adopted** — eliminated Rz-like spanin false positives the bacterial-negative model had never seen |
| Curated holin/spanin depth (Pfam; CPT/Kongari spanins) | **adopted** — holin realistic AP 0.823 → 0.965 on the earlier small evaluation (0.754 on the 66-genome panel, §3.1); spanin recall@0.9 at strict removal 0.00 → working model |
| Endolysin family expansion (+14 catalytic families, 1,529 → 2,788 positives) | **rejected** — realistic AP −0.061 (paired CI −0.113 to −0.011). Cut back to the original count with its new composition it still lost 90 % of that ground, while 820 extra records of the same mix changed AP by 0.006: the loss is composition, not volume (`reports/capacity_sweep.md`) |
| Per-catalytic-fold endolysin models | **rejected** as a replacement — sharper within a fold, but loses cross-fold transfer, which is what the strict protocol measures |
| Larger trees / more rounds (800 rounds, 63 leaves) | **rejected** — lower AP in all four paired contrasts |
| Early stopping removed (endolysin) | **adopted** — realistic AP +0.046 (§2.2); no effect on the expanded data or on strict |

The spanin result specifically depended on the CPT/Kongari curated set: the class went from 288 to 2,045 sequences and from unusable (zero strict recall) to the strongest gold-hold-out AP of the three.

### 3.3 Breadth across phage diversity

Scanning 300 pooled Caudoviricetes genomes (plus a fresh out-of-sample panel) the caller recovers annotated holins in **96.9 %** of genomes that have one (186/192), of which a majority (107) are out-of-sample. Endolysin and spanin recovery on the pool is near-total but largely in-sample (their positives were partly drawn from these annotations), so the honest generalisation estimates remain the LOGO figures above. The tool runs identically on annotated GenBank and on **raw nucleotide assemblies** via de-novo gene calling (Pyrodigal): on phage N4, the nucleotide path recovered the same holin/endolysin/spanin cassette as the annotation, from sequence alone.

**Expanded out-of-sample panel (38 genomes, 23 actinobacterial).** To test generalisation on genomes with no overlap with training (verified against the pool, prior panel, atlas and benchmark), and specifically to probe the historical actinobacterial weakness, we scanned a fresh panel weighted toward *Mycobacterium*, *Streptomyces*, *Rhodococcus*, *Gordonia*, *Corynebacterium* and *Propionibacterium* phages. Reporting genuinely-unseen recovery (recovered gene is *not* an exact training sequence):

| class | annotated | recovered | in-sample | genuinely unseen |
|---|---|---|---|---|
| holin | 26 | 25 (96 %) | 11 | **14** |
| endolysin | 37 | 36 (97 %) | 8 | **28** |
| spanin | 6 | 6 | 6 | 0 (no generalisation test here) |

Here "unseen" is the weaker criterion of *not an exact training sequence* — close homologues (e.g. *Mycobacterium* cluster siblings) may still be in training, so this is more permissive than the strict LOGO protocol (§2.3, §3.1), which removes the whole family at ≥30 % identity and remains the true never-seen-family estimate. Within the actinobacterial subset, **7 holins not identical to any training sequence** were recovered — Rosebush, Phlyer, Tweety, *Propionibacterium* PHL194M00, Barnyard, *Rhodococcus* ReqiPepy6, Predator — all at 0.975–1.000, together with 19 such endolysins (0.92–0.995). This is a marked improvement in evidence over the first panel, which contained only one, and gives no sign of the historical actinobacterial holin blind spot at this level of homology control. It is reported with its limits: the subset is *Mycobacterium*-dominated; 9 of 23 genomes have no annotated holin to score; the two misses are in less-represented hosts (*Corynebacterium* P1201 holin, 0.33; *Streptomyces* VWB endolysin, 0.21); and this measures sensitivity, not specificity. Separately, **marine cyanophage endolysins are a documented weakness** (S-PM2 0.60, P-SSM2 0.63). Across the panel there are ~1.6 high-confidence un-annotated calls per genome — i.e. the caller is sensitive but over-calls, and high-confidence use should apply the per-class cut-offs (§3.1) and context filtering. (This panel scan predates the current endolysin model.)

### 3.4 A reproducible biological finding: adjacent holin-fold gene pairs

The classifier sees only protein sequence — it has **no positional input**. It nonetheless repeatedly nominated a *second* holin-scoring gene immediately beside the annotated holin (first observed at phage N4, where an un-annotated gene *gp63* outscores the annotated holin *gp62*). Because the model cannot perceive adjacency, any genomic clustering of its high-scoring holins is real signal, not model bias. Testing this against a random-placement null across 300 genomes:

- 99/300 genomes (33 %) carry ≥2 high-confidence (P≥0.9) holin-fold genes.
- Minimum gene-distance between them: **median 2** observed vs **22** under random placement; **67 %** are within 3 genes vs **0 %** by chance.

Characterising the 138 "second" genes: 92 lie in the lysis region; 78 % have ≥1 predicted transmembrane helix and 60 % a positive C-terminal tail (holin signatures); by homology 116 match a known holin and 41 match a known antiholin (an antiholin *is* a holin homologue, so this is a correct fold call), with 22 matching neither. By annotation, 27 are already a second annotated holin, **71 are un-annotated hypotheticals** with holin character, and ~20 are structural/other (the specificity cost). The conclusion is that phage lysis regions commonly encode **two adjacent holin-fold proteins** — annotated dual holins, holin–antiholin pairs, and under-annotated candidates — and the model recovers both from fold alone. This is a general pattern, of which the N4 *gp63* observation was one instance.

### 3.5 Predictions

The method yields concrete, falsifiable outputs for experimental follow-up, all with scores and evidence in the result files:

- **Under-annotated second holins/antiholins:** 71 hypothetical genes with holin signatures adjacent to annotated holins (`reports/dual_holin_analysis.json`).
- **Phage N4 (the lab's organism):** a complete cassette (*gp60* spanin, *gp61* SAR endolysin, *gp62/gp63* holin pair), with the SAR endolysin called out-of-sample at 0.976 (0.9993 by the current endolysin model) and the un-annotated *gp63* out-scoring the annotated holin — a dual-holin candidate for the N4 lysis system (`reports/n4_cassette_scan.*`).
- **Novel-candidate scan of 24,064 unmined proteins:** homology-filtered putative holins with lysis-cassette context (`reports/novel_holin_candidates.*`); we note honestly that follow-up verification down-ranked most to adjacent-to-known-holin cases, leaving a small set of genuine leads.

## 4. Deployment

A single command, `scripts/32_predict_lysis.py`, accepts protein FASTA, nucleotide FASTA (de-novo gene calling), GenBank, or an NCBI accession, and returns per-protein P(holin/endolysin/spanin) plus cassette flags (`DEPLOY.md`). A Galaxy tool wrapper is provided for institutional deployment (Center for Phage Technology Galaxy instance). Dependencies are pinned (notably scikit-learn 1.9.1, as the models are pickled estimators); the ESM-2 weights (~130 MB) download on first run.

## 5. Limitations

- Strict (never-seen-family) AP of 0.57–0.61 means the tool is a ranked shortlist for genuinely novel families, not a definitive caller.
- More data of the same kind did not help the endolysin model, more capacity did not help, and adding domain-mined positives from new families made it worse. The remaining limit appears to be the representation (a mean-pooled embedding). Explicit similarity to the training set does not help: as an input it halves novel-family AP through shortcut learning, and as a promotion rule it adds nothing for known families (`reports/similarity_features.md`). Genomic context, which the models never see, is the main untested signal.
- Some genuine lysis genes have no recognisable domain at all: the *Escherichia* phage Serwaa endolysin matches nothing in any of 23 InterPro member databases, so domain search cannot rescue it and only homology or genomic context can.
- Spanin's honest generalisation number is the 0.57 strict figure, on only 32 annotated genes in 19 genomes.
- The 66-genome panel resolves paired differences only above ~0.05 AP.
- Pfam is effectively exhausted as a source of new holin architectures (4,700 of 4,701 curated records joined existing families), so further gains need newly characterised families.
- Annotation is an imperfect ground truth; "recovery" and "false positive" are measured against it.

## 6. Data and code availability

All code, model files, evaluation reports, and data provenance are in this repository (branch `claude/holin-ml`). The full pipeline (sources → dataset → clustering → training → evaluation → scanning → deployment) is documented in `PROTOCOL.md`; deployment in `DEPLOY.md`.

## References (to be completed)

- Kongari R, Rajaure M, Cahill J, Rasche E, Mijalis E, Berry J, Young R. *Phage spanins: diversity, topological dynamics and gene convergence.* BMC Bioinformatics 2018;19:326.
- Lin Z *et al.* / Rives A *et al.* ESM-2 protein language model (ESM-2, `esm2_t12_35M_UR50D`).
- Larralde M. *Pyrodigal.* (de-novo prokaryotic/phage gene prediction.)
- TCDB (Saier) superfamily 1.E holins; Pfam/InterPro lysis families.
- *(Holin/endolysin/spanin biology reviews; N4 lysis system — to be added.)*
