# Sequence-only machine-learning identification of phage lysis genes — holins, endolysins and spanins — across bacteriophage diversity

**Draft manuscript (in preparation).** Code, data provenance and all result files in this repository.
Corresponding work: Michael Baffour Awuah, Center for Phage Technology.

---

## Abstract

Bacteriophages end infection by lysing the host cell with a small cassette of genes: a **holin** (triggers inner-membrane permeabilization and sets lysis timing), an **endolysin** (degrades peptidoglycan), and, in Gram-negative hosts, a **spanin** system (disrupts the outer membrane). These genes are short, fast-evolving and frequently mis- or un-annotated, and they do not always sit together in the genome. We built three protein classifiers — one per gene class — from hand-crafted biochemical features and ESM-2 protein-language-model embeddings, trained one-vs-rest so that each class is separated from the other two and from bulk bacterial and phage proteins. Under strict, homology-controlled evaluation (homology-clustered splits, a frozen gold hold-out, and leave-one-genome-out scanning), the holin classifier reaches a genome-scan average precision of **0.965** for a new phage from a known family and **0.785** for a never-before-seen family; endolysin and spanin reach **0.84/0.73** and **0.83/0.73** respectively. Applied to 300+ diverse phage genomes — including actinobacterial hosts — the caller recovers annotated lysis genes at high rates and runs directly on raw nucleotide assemblies via de-novo gene calling. Beyond recovery, a systematic analysis uncovered a reproducible biological signal: because the classifier has **no positional input**, its tendency to call a *second* holin-fold gene immediately next to the annotated holin cannot be an artefact of genomic context — and we show these second genes cluster adjacent to the first far more than chance (median 2 vs 22 genes apart), are membrane proteins with holin signatures, and are frequently either annotated second holins, holin–antiholin pairs, or un-annotated candidates. We release the models, a single-command tool that accepts protein or nucleotide input, and a Galaxy wrapper.

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

Each protein is represented by 36 hand-crafted biochemical features (length, transmembrane-segment count and fraction from a Kyte–Doolittle scan, terminal charges, amino-acid composition, hydrophobic-moment proxies) concatenated with a 480-dimensional mean-pooled embedding from **ESM-2** (`facebook/esm2_t12_35M_UR50D`), for a 516-dimensional vector. The classifier is a histogram gradient-boosted decision tree (scikit-learn `HistGradientBoostingClassifier`). We tested and **rejected** a transmembrane-anchored local-feature representation (it did not help the hard long-holin cases and cost recall; §3.2).

### 2.3 Leakage control and evaluation

The project's discipline is that no performance number is trusted unless homology leakage between train and test is controlled:

- **Homology clustering.** All sequences are clustered by exhaustive Smith–Waterman identity (greedy set-cover; a k-mer prefilter was rejected for ~10 % edge recall, and single-linkage for chaining). Splits never place homologues on both sides.
- **Frozen gold hold-out.** 20 % of clusters per class, chosen once with a fixed seed, never used for model selection.
- **Leave-one-genome-out (LOGO) genome scan.** For each evaluation genome we remove the target gene's homologues from training before scoring that genome, and report two protocols: **realistic** (remove ≥95 % identical near-duplicates — a newly sequenced phage whose gene belongs to a *known* family) and **strict** (remove the whole family at ≥30 % identity — a *never-seen* family). This is the honest deployment estimate.

A recurring, important subtlety we surfaced and report throughout: **a genome being out-of-sample does not make its genes out-of-sample**, because characterised phages' lysis genes are in the public databases regardless of which genome they sit in. We therefore always report the exact-sequence in-sample fraction alongside any recovery rate.

## 3. Results

### 3.1 Classifier performance (homology-controlled)

| gene | gold-hold-out AP | realistic LOGO AP | strict LOGO AP |
|---|---|---|---|
| holin | ~0.88 | **0.965** (95 % CI 0.89–1.0; recall@0.9 = 0.92; top-ranked protein in all genomes) | **0.785** |
| endolysin | 0.801 | 0.843 | 0.729 |
| spanin | 0.916 | 0.834 | 0.729 |

Reading: for a new phage whose lysis gene belongs to a known family, all three genes are called reliably and the holin is the single top-ranked protein in the genome. For a genuinely novel family, the strict numbers (~0.73–0.79) mean the tool provides a ranked shortlist, not a verdict — results should be triangulated with membrane-topology prediction and genomic context. Precision is ~0.75 at P≥0.9, so a 0.95 threshold is advised for high-confidence calls.

### 3.2 What worked and what did not

Four interventions were attempted under the same guards; two were adopted and two rejected, each on its own evidence:

| intervention | outcome |
|---|---|
| Stacked specialist models (window/actino/short + gated stacker) | **rejected** — lowered gold AP; blending miscalibrated the decision threshold |
| Guarded self-training on the mined pool | **rejected, rolled back** — did not beat baseline; candidate set was contaminated by spanins |
| TM-anchored local features | **rejected** — no gain on the target long-holin cases, cost recall |
| Phage-derived hard negatives (incl. spanins) | **adopted** — eliminated Rz-like spanin false positives the bacterial-negative model had never seen |
| Curated holin/spanin depth (Pfam; CPT/Kongari spanins) | **adopted** — holin realistic AP 0.823 → **0.965**; spanin recall@0.9 at strict removal 0.00 → working model |

The spanin result specifically depended on the CPT/Kongari curated set: the class went from 288 to 2,045 sequences and from unusable (zero strict recall) to the strongest gold-hold-out AP of the three.

### 3.3 Breadth across phage diversity

Scanning 300 pooled Caudoviricetes genomes (plus a fresh out-of-sample panel) the caller recovers annotated holins in **96.9 %** of genomes that have one (186/192), of which a majority (107) are out-of-sample. Endolysin and spanin recovery on the pool is near-total but largely in-sample (their positives were partly drawn from these annotations), so the honest generalisation estimates remain the LOGO figures above. The tool runs identically on annotated GenBank and on **raw nucleotide assemblies** via de-novo gene calling (Pyrodigal): on phage N4, the nucleotide path recovered the same holin/endolysin/spanin cassette as the annotation, from sequence alone.

*[Expanded out-of-sample panel — in progress; results appended on completion: additional diverse genomes with emphasis on actinobacterial hosts, reporting genuinely-unseen recovery and the actino subset specifically.]*

### 3.4 A reproducible biological finding: adjacent holin-fold gene pairs

The classifier sees only protein sequence — it has **no positional input**. It nonetheless repeatedly nominated a *second* holin-scoring gene immediately beside the annotated holin (first observed at phage N4, where an un-annotated gene *gp63* outscores the annotated holin *gp62*). Because the model cannot perceive adjacency, any genomic clustering of its high-scoring holins is real signal, not model bias. Testing this against a random-placement null across 300 genomes:

- 99/300 genomes (33 %) carry ≥2 high-confidence (P≥0.9) holin-fold genes.
- Minimum gene-distance between them: **median 2** observed vs **22** under random placement; **67 %** are within 3 genes vs **0 %** by chance.

Characterising the 138 "second" genes: 92 lie in the lysis region; 78 % have ≥1 predicted transmembrane helix and 60 % a positive C-terminal tail (holin signatures); by homology 116 match a known holin and 41 match a known antiholin (an antiholin *is* a holin homologue, so this is a correct fold call), with 22 matching neither. By annotation, 27 are already a second annotated holin, **71 are un-annotated hypotheticals** with holin character, and ~20 are structural/other (the specificity cost). The conclusion is that phage lysis regions commonly encode **two adjacent holin-fold proteins** — annotated dual holins, holin–antiholin pairs, and under-annotated candidates — and the model recovers both from fold alone. This is a general pattern, of which the N4 *gp63* observation was one instance.

### 3.5 Predictions

The method yields concrete, falsifiable outputs for experimental follow-up, all with scores and evidence in the result files:

- **Under-annotated second holins/antiholins:** 71 hypothetical genes with holin signatures adjacent to annotated holins (`reports/dual_holin_analysis.json`).
- **Phage N4 (the lab's organism):** a complete cassette (*gp60* spanin, *gp61* SAR endolysin, *gp62/gp63* holin pair), with the SAR endolysin called out-of-sample at 0.976 and the un-annotated *gp63* out-scoring the annotated holin — a dual-holin candidate for the N4 lysis system (`reports/n4_cassette_scan.*`).
- **Novel-candidate scan of 24,064 unmined proteins:** homology-filtered putative holins with lysis-cassette context (`reports/novel_holin_candidates.*`); we note honestly that follow-up verification down-ranked most to adjacent-to-known-holin cases, leaving a small set of genuine leads.

## 4. Deployment

A single command, `scripts/32_predict_lysis.py`, accepts protein FASTA, nucleotide FASTA (de-novo gene calling), GenBank, or an NCBI accession, and returns per-protein P(holin/endolysin/spanin) plus cassette flags (`DEPLOY.md`). A Galaxy tool wrapper is provided for institutional deployment (Center for Phage Technology Galaxy instance). Dependencies are pinned (notably scikit-learn 1.9.1, as the models are pickled estimators); the ESM-2 weights (~130 MB) download on first run.

## 5. Limitations

- Strict (never-seen-family) performance of ~0.73–0.79 means the tool is a ranked shortlist for genuinely novel families, not a definitive caller.
- Endolysin generalisation is bounded by catalytic-family diversity, not sequence count; more validated *families*, not more sequences, would help.
- Spanin's high recovery rests partly on in-sample data; its honest generalisation number is the 0.73 strict figure.
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
