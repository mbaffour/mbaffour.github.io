# Final test: results of the pre-registered analysis

Plan, model hashes and endpoints: `FROZEN.md` (commit 2376b6e, made before any final genome was selected).
Predictions frozen in commit 63c8145 before any annotation was read. Analysis: `scripts/61_final_report.py`,
`final_results.json`.

**Final test set.** The pre-registered rules (the blind-set query, every genome used anywhere in the project excluded
by accession and DNA, at most 25 per host genus) left 311 eligible genomes in only four host genera, giving **87
genomes** (Escherichia 25, Klebsiella 25, Pseudomonas 25, Salmonella 12) in 34 gene-content clusters. Smaller and
narrower than hoped; reported as defined.

## Confirmatory test

**H1 -- the virion-fixed endolysin model's call matches the annotated endolysin more often than the retired model's:
not confirmed.** 0.838 -> 0.863 (+0.025; 2 genomes fixed, 0 broken; 80 genomes, 31 clusters), one-sided p = 0.37.
The direction agrees with development (CPT and blind set 2 pooled: +0.060 [+0.020, +0.103]), but this set has few of
the phages with virion lysozymes the fix targets, so it cannot confirm the effect. The fix remains justified by
correcting mislabelled training data; its size on new genomes is not established.

## Estimation endpoints -- agreement with annotation (not accuracy)

| | the call is the annotated gene | annotated gene in the top 5 |
|---|---|---|
| holin (59 genomes, 25 clusters) | 0.93 [0.82, 1.00] | 0.98 [0.94, 1.00] |
| endolysin (80, 31) | 0.86 [0.70, 0.97] | 1.00 |
| spanin (69, 27) | 0.74 [0.54, 0.90]; pair level 0.85 [0.67, 0.97] | 0.99 [0.95, 1.00] |

By identity of the annotated gene to the training data: holins 41 near-copies (41 called), 17 known family (14),
1 new family (0); endolysins 45 / 33 / 2 (41, 26, 2 called); spanins 51 / 18 / 0. This set therefore confirms
performance on familiar genes and says almost nothing about new families -- the curated benchmarks below and the
remote-homology test (`../remote_homology.md`) are the evidence for those.

## Secondary: curated Swiss-Prot benchmark (43 endolysins, 19 holins, 18 spanins in 42 genomes)

Leave-one-genome-out, per genome, 95% CI over gene-content clusters (`../baselines/reviewed.json`):

| call / top 5 | known family | unseen family (30%) | remote homology removed | PHROGs (has seen these) | PHROGs, else ours (unseen) |
|---|---|---|---|---|---|
| holin (19) | 0.84 / 1.00 | 0.79 / 0.90 | 0.74 / 0.90 | 0.95 / 1.00 | 0.95 / 1.00 |
| endolysin (39) | 0.90 / 1.00 | 0.61 / 0.92 | 0.46 / 0.85 | 0.87 / 0.87 | 0.90 / 0.95 |
| spanin (10) | 0.80 / 1.00 | 0.80 / 1.00 | 0.60 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |

## Every model variant tried during development (disclosure)

| area | variants | decision | where |
|---|---|---|---|
| model capacity | deeper/longer boosting, early stopping on/off, positive subsampling | early stopping off for endolysin; rest unchanged | capacity_sweep.md |
| endolysin positives | pool-labelled, evidence-only, restored 127 holdout, virion proteins removed | evidence-only, then virion-fixed | evidence_only.md, endolysin_virion_fix.md |
| features | similarity-to-training features; biophysics only; + membrane topology; ESM-2 150M | all rejected | similarity_features.md, holin_generalisation.md |
| holin training | family-balanced and 1/sqrt weights; context-mined new families (2 versions); 3 ensembles; label audit | all rejected (mined + ensemble kept as an opt-in T4-aware mode) | holin_generalisation.md, holin_context_mining.md, label_audit/ |
| spanin training | signal-filtered positives; evidence-only; label audit | signal-filtered, then audited | evidence_only.md, label_audit/ |
| calling | genomic-context rule (weights, windows); learned second-stage caller; capped scores; distance decay | context rule (holin, endolysin), learned caller (spanin); cap and decay rejected | integrated_caller.md, endolysin_virion_fix.md |
| gene finding | nested lipoprotein ORFs (5 parameter settings, chosen on gene-finding counts) | adopted | denovo_gene_calling.md |
| topology | our ESM predictor, SAR rule (calibrated on its own 44 proteins), DeepTMHMM, SignalP 6.0 | DeepTMHMM for holin class; SAR by consensus; SignalP for lipoproteins | tm_experimental.md, external/comparison.md |
Decisions were made on CPT (and its experimental subset) with rules stated before each run; the blind sets and this
final set were used only for testing, except that blind set 1 revealed the virion-lysozyme error.
