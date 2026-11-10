# Panel 2: expanded out-of-sample scan (38 phage genomes, 23 actinobacterial)

Source data: `reports/panel2_scan.json` (threshold 0.5, cassette window 6, scripts unmodified, no retraining). Per-genome in-sample/unseen status and per-gene scores were derived by a scratch re-scoring of the same cached embeddings (exact-sequence match against the training sets, same rule as the script's `of_recovered_how_many_in_sample`). Accession list: scratchpad `panel2.txt` (38 lines, `name<TAB>accession`).

## 1. Frame and honesty points

- All 38 accessions were checked against `data/raw/pool/accessions.json` (3,993), the prior panel (L5, TM4, Giles, phiC31, BFK20, TP901-1, phiKZ, LKA1, phiCbK, T3, N15, Felix O1) and the benchmark/atlas list (incl. N4, lambda, D29). None overlap: **genome-level out-of-sample.**
- **Genome-out-of-sample is not gene-out-of-sample.** Many of these phages' lysis genes are in UniProt/Pfam/Kongari-derived training data. Below, "unseen" = a recovered annotated gene whose sequence is NOT an exact training sequence. Exact match only: close homologues (e.g. Mycobacterium cluster siblings) are still "unseen" here, so "unseen" means "not an identical sequence", not "no homologue in training". True novelty is lower than the unseen counts suggest.
- Annotation is imperfect ground truth. "Recovered" means an annotated gene whose product name matches the class scored >= 0.5. Genomes with no annotated holin (often because the holin is annotated as "gp##"/"hypothetical") cannot be scored for holin recovery.

Candidates dropped (not scanned):
- **In pool (in-sample):** Che9c, Che12, Che8, Corndog, Omega, Cjw1, Fruitloop, Pacc40, Halo, Gmala1, Arthrobacter Brent, Bacillus Nf, B103, Lactobacillus phiPYB5, Vibrio K139, Mycobacterium Bxb1.
- **Search returned only excluded genomes (pool/prior panel/benchmark), so nothing new:** Bxz2, Wildcat, SPBc2 (SPbeta), GA-1, phiCD27, Syn5, Felix O1, Bethlehem, Ardmore, Pukovnik, Kostya, ScottMcG, Brujita, Jasper, Llij, 244, Rey (extra Mycobacterium names tried).
- **No RefSeq "complete genome" title match:** HK022, phage 186, Lc-Nu, "Propionibacterium phage PHL" (substituted PHL194M00), Adjutor, Chah. HK97 skipped (atlas).
- **Not chosen:** Erwinia, Caulobacter beyond one, other jumbo Yersinia/Prochlorococcus/Burkholderia (redundant or time). Additions beyond the named list (Predator, Cooper, Konstantine, PG1, Charlie, Tweety, Nigel, Phlyer, P1201, REQ1, ReqiPine5, Dp-1, Cp-1, Ldl1, Yep-phi, KS14, AH2, P-SSM2, CcrSwift, S-PM2) were added to reach actino depth and diversity.
- Note: phiBT1/VWB/R4/mu1/6 and several Mycobacterium phages are well-studied, so exact-sequence matches in training are plausible (see below).

## 2. Overall

38 genomes, 8 with a detected cassette (21.1%); 61 high-confidence (P >= 0.9) un-annotated calls. Cassette detection is low: the three-gene cassette is rare because most of these phages lack annotated spanins and many have holin/endolysin separated by > 6 genes.

| Class | Genomes with annotated gene | Recovered >= 0.5 | In-sample among recovered (script) | Recovered, derived unseen* | Top-scoring protein is annotated |
|---|---|---|---|---|---|
| holin | 26 | 25 (96%) | 11 | 14 (15 with at least one unseen gene) | 20 |
| endolysin | 37 | 36 (97%) | 8 | 28 (30 with at least one unseen gene) | 33 |
| spanin | 6 | 6 (100%) | 6 | **0** | 6 |

*Recovered minus genomes where the recovered gene is an exact training sequence (script definition). The looser "at least one unseen recovered gene" count is in parentheses.

- Spanin: 100% recovery is entirely in-sample (6/6 exact training sequences); this panel says nothing about spanin generalisation.
- Endolysin recovery is the most robust (30/37 genomes with at least one unseen recovered gene).
- Holin: 25/26 recovered, of which about half are exact training sequences.

## 3. Actinobacterial subset (main goal)

23 actino genomes (12 Mycobacterium, 4 Streptomyces [phiBT1, VWB, R4, mu1/6], 3 Rhodococcus, 1 Gordonia, 1 Corynebacterium, 1 Propionibacterium, plus one additional flagged by the script's regex), 2 with a detected cassette.

| Class | Annotated | Recovered | Unseen (>=1 gene) | Top-scorer annotated |
|---|---|---|---|---|
| holin | 14 | 13 | 7 | 10 |
| endolysin | 23 | 22 | 19 | 21 |

**Genuinely-unseen actino holins recovered: 7** (the previous panel had 1). Scores: Rosebush 1.000, Phlyer 1.000, Tweety 1.000, PHL194M00 0.999, Barnyard 0.995, ReqiPepy6 0.988, Predator 0.975. The other 6 recovered actino holins (Bxz1, mu1/6, Cooper, Konstantine, Charlie, Nigel; all >= 0.99) are exact training sequences and are not evidence of generalisation.

**Genuinely-unseen actino endolysins recovered: 19** of 23 annotated, scores 0.92-0.995 (lowest: mu1/6 0.923, Charlie 0.928, ReqiPepy6 0.932, PHL194M00 0.93; highest PG1 0.995, phiBT1 0.994, Phlyer 0.991, U2 0.991). In-sample: Bxz1, Barnyard, R4.

**Misses (named):**
- Holin: **Corynebacterium phage P1201** (annotated holin best score 0.329; a different protein, gp50, scored 0.921 as holin and may be the real one, or an over-call).
- Endolysin: **Streptomyces phage VWB** (annotated endolysin 0.211; top-scoring protein is an unannotated hypothetical at 0.852).
- Ranking weak spots: in 4 actino genomes the top holin scorer is not the annotated holin (ReqiPepy6, Cooper, Nigel, P1201); Cooper/Nigel top scorers are "gp16"/"gp14" at 1.0 vs annotated holin 0.999 (likely ties between neighbouring genes, not a clear error).

**Read:** actino performance looks solid on this panel at the recovery level (holin 13/14, endolysin 22/23; 7 unseen holins, 19 unseen endolysins), but with real caveats: (a) 9 of 23 actino genomes have no annotated holin and could not be scored, (b) sample is dominated by Mycobacterium cluster siblings, which are closely related to each other and to training sequences, so "unseen" overstates independence; (c) cassette detection is poor (2/23), meaning the full three-gene pattern is almost never completed in actino phages (they generally lack spanins); (d) the model scores many neighbouring/un-annotated proteins highly, so discrimination (precision) is not established by recovery alone. Non-Mycobacterium actino hosts are thinner (VWB and P1201 are the two misses, both outside the Mycobacterium/mycobacteriophage space), so the weakness, if any, is in the less-represented hosts.

## 4. Top un-annotated high-confidence calls (predictions, not validated)

Many are holin calls; holin calls here are numerous (about 1.6 un-annotated calls/genome at P >= 0.9), so treat them as candidates with low expected precision. "TM" = rough count of 19-aa Kyte-Doolittle windows >= 1.6 (crude, not a TM predictor).

| # | Genome | Product / length | Class P | Plausibility |
|---|---|---|---|---|
| 1 | R4 (NC_019414) | hypothetical, 70 aa | holin 1.000 | Small, 1 TM-like segment; plausible holin; R4's annotated lysis genes may be elsewhere. |
| 2 | Cooper | gp16, 107 aa | holin 1.000 | 1 TM; likely a true holin or tied neighbour of the annotated one. |
| 3 | PG1 | hypothetical (gene 16), 99 aa | holin 1.000 | 1 TM; PG1 has no annotated holin, so plausible missing annotation. |
| 4 | Nigel | gp14, 106 aa | holin 1.000 | 1 TM; same as Cooper. |
| 5 | Phlyer | gp19, 159 aa | holin 1.000 | 2 TM; plausible. |
| 6 | Bxz1 | gp80, 98 aa | holin 0.999 | 0 TM-like; weaker; near the lysis region (gp80-82), possibly lysis-adjacent. |
| 7 | PHL194M00 | hypothetical, 67 aa | holin 0.998 | Small, 1 TM; plausible. |
| 8 | ReqiPine5 | gp17, 129 aa | holin 0.998 | 1 TM; plausible (no annotated holin). |
| 9 | REQ1 | hypothetical, 69 aa | holin 0.998 | Small; plausible. |
| 10 | RSL1 | hypothetical, 130 aa | holin 0.997 | 0 TM-like and one of several calls in a 343-protein genome; likely over-call. |
| 11 | CcrSwift | hypothetical, 120 aa | holin 0.997 | Large genome, multiple calls; low confidence. |
| 12 | phiEF24C | membrane protein, 89 aa | holin 0.996 | 1 TM and annotated as membrane protein; plausible. |
| 13 | Rosebush | gp20, 110 aa | holin 0.995 | 1 TM; plausible. |
| 14 | GTE2 | hypothetical, 102 aa | holin 0.995 | 1 TM; no annotated holin; plausible. |
| 15 | Tweety | "minor tail protein", 124 aa | holin 0.994 | Annotated as a tail protein: likely a false positive or mis-annotation. |

Also noted: Bxz1 gp238 (endolysin 0.991) and gp82 (spanin 0.989) sit near the lysis region and merit a manual look.

## 5. Clear failures

- VWB endolysin (0.211), P1201 holin (0.329): the only actino misses.
- Cyanophages **S-PM2 (0.595)** and **P-SSM2 (0.627)**: endolysin barely above threshold, and unannotated hypotheticals outscore the annotated gene (0.975, 0.959). Weak on marine cyanophage lysozyme-type genes.
- **Phage P4**: only 14 proteins, no annotated lysis genes (satellite phage, nothing to score).
- Holin ranking: top-scoring protein is not the annotated holin in 6/26 genomes (ReqiPepy6, RSL1, P1201, Cooper, Nigel, CcrSwift).
- Cassette detection: only 8/38 (21%), 2/23 in actino phages; the cassette caller is not a reliable genome-level indicator on this panel.

## 6. Bottom line

Recovery of annotated holin/endolysin is high (about 96-97%) including on actino phages, with 7 genuinely-unseen actino holins and 19 unseen actino endolysins recovered at >= 0.92, up from 1 before. This is encouraging but is a recovery (sensitivity) test only: annotation is the ground truth, "unseen" is exact-sequence only, Mycobacterium siblings dominate, and spanin results are fully in-sample. Specificity of un-annotated calls remains untested.
