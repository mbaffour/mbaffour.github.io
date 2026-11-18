# Frozen pipeline and pre-registered final test

Committed BEFORE the final test genomes are selected, downloaded, scanned or scored. Nothing below may change after
this commit; any later analysis is labelled exploratory.

## Frozen pipeline (git a5c361b plus this file)

| file | SHA-256 |
|---|---|
| models/holin_model_curated.pkl | 0fcb2e40997ff403653d6ce767fba644cab6c03bb90094b7a5a1f27eca1107b4 |
| models/endolysin_model.pkl (virion-fixed) | 9ef1aecd8657d0d91e2f27a778b60019d04734b3d774072132cf671725e35566 |
| models/spanin_model.pkl (label-audited) | be586e0a4a8f5c9df45a4d9c56b6f5e8b29bcc362c3120ad330b64a8b2af9880 |
| models/spanin_caller.pkl | e46cec6ea13c7b4010b326c5278549b902bb4293c57ec052c8d17ed8ff18a8c1 |
| models/context_params.json | c3a2ccf43b6b3b97627d7375e4c1451b7fe485c3ce604779b335af3d8358ef4e |
| models/endolysin_model_v1_evidence_retired.pkl (comparator for H1 only) | 6c5110c4fa7f7d59f9867da60d63ed8f50488ccae59786618c06fc2131506806 |
| models/tm_predictor.pkl | 9b86d68654d6cd50d9a31a1c28461af5aaf2e7dd664c04bfff7aa0291e0e629d |
| scripts/32_predict_lysis.py | 2ba2fe9cdabf01a33b10a40c0da4d34bda693f80ceb0ed4e547abc2bb5d56e5a |
| scripts/genecall.py | 046d0dd868d1271ee9f705920a36543369902251684ed6f7af72d2615d3d0c62 |
| scripts/features.py | 41d3cbf617a46ee1c0aede61aa7776527f4959dba05209826f9deedad858f7fa |
| scripts/52b_blind_scan.py | 416babaa51c3108506e3986f8735a187352d2f7d0e70455210f45e310587c448 |
| scripts/52c_score_blind.py | 54d6a54f01be92ec6596dc239656b47caa909e2bb3367b7c35d69caf42dc86d1 |

Environment: scikit-learn 1.9.1, torch 2.15.0 (CPU), transformers 5.22.2, pyrodigal 3.7.1, ESM-2 35M
(facebook/esm2_t12_35M_UR50D). Predictor defaults: genes by Pyrodigal + nested lipoprotein ORFs, standard holin mode,
genomic context as in context_params.json, spanin caller on, no distance decay.

## Final test set

- NCBI nuccore: `"Caudoviricetes"[Organism] AND complete genome[Title] AND 2026/06/01:3000/12/31[PDAT] NOT srcdb_refseq[PROP]`
  (the blind-set query), at least 10 annotated CDS, at most 800 kb.
- Excluded by accession and by DNA identity: every genome used anywhere in this project (CPT, experimental and
  reviewed benchmarks, panels, the training pool, the 5,247 mining genomes, blind sets 1 and 2, the N4-like and the
  eight group scans).
- At most 25 genomes per host genus; seeded random sample (seed 7) of up to 300.
- The predictor sees DNA only; calls are committed before any annotation is read (as in scripts/52b/c).

## Endpoints

**Confirmatory (one test, so no multiplicity correction):**
H1. The shipped, virion-fixed endolysin model's call matches the annotated endolysin more often than the retired
model's call (paired, same genomes, both run through the full frozen predictor). One-sided, alpha = 0.05, paired
bootstrap resampling gene-content clusters of the final set (scripts/58). This replicates, on new genomes, the main
model change adopted during development.

**Estimation (primary, with 95% CIs resampling gene-content clusters; no tests):**
For holin, endolysin and spanin: share of genomes whose annotation has the gene in which (a) the call is the annotated
gene (spanin: the annotated gene or its overlapping partner) and (b) the annotated gene is in the top 5; each also split
by the annotated gene's identity to the training positives (>= 95%, 30-95%, < 30%). These are AGREEMENT WITH
ANNOTATION, not accuracy: GenBank annotations of recent phage genomes are largely automated.

**Secondary (descriptive):**
- Curated benchmark of Swiss-Prot reviewed lysis proteins (data/raw/reviewed; 43 endolysins, 19 holins, 18 spanins
  in 42 genomes): leave-one-genome-out ranks under the known-family, unseen-family and remote-homology protocols, and
  the PHROGs baseline on the same genomes (PHROGs has effectively seen them).
- Confident calls on genes the annotation leaves hypothetical or absent, with sequence evidence (scripts/52c).
- Family distribution: holin classes reported from DeepTMHMM (better validated on experimental topologies,
  reports/tm_experimental.md), our predictor as concordance; SAR endolysins as the consensus of our rule and DeepTMHMM;
  lipoproteins from SignalP 6.0.

Anything else run on the final set is exploratory and labelled so.
