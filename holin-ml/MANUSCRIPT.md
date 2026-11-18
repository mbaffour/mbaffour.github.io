# Finding phage lysis genes — holins, endolysins and spanins — from DNA alone

**Draft manuscript (in preparation).** Code, data provenance and every result file cited below are in this
repository (branch `claude/holin-ml`). Corresponding work: Michael Baffour Awuah, Center for Phage Technology.

---

## Abstract

Tailed phages lyse their host with a small set of genes: a **holin** that permeabilises the inner membrane and times
lysis, an **endolysin** that degrades peptidoglycan, and, in Gram-negative hosts, a **spanin** complex that disrupts
the outer membrane. These genes are short, diverse and often missing or mislabelled in genome annotations. We built
one classifier per gene class from 36 biochemical features and ESM-2 protein-language-model embeddings, combined them
with a gene finder that also recovers o-spanins nested inside another gene, and with a genomic-context rule that names
one gene per class per genome. Every claim was tested with related phages grouped by shared gene content, so that
near-identical genomes are not counted as independent evidence.

On 129 genomes with hand-curated lysis genes, with the target's whole family (≥30% identity) removed from training,
the curated gene was the model's top pick for 54% of holins and 74% of endolysins and was in the top five for 85%
and 90%. Removing remote homologues found by profile search as well (jackhmmer) barely changed holins (50% / 83%) or
spanins (top five 90%) but lowered endolysins to 55% / 82%: the endolysin model depends partly on remote similarity
to ancient enzyme families. Compared with PHROGs, the profile database behind Pharokka, on curated genomes first submitted
after PHROGs was built, our model named the endolysin (0.92 vs 0.82) and the holin (0.76 vs 0.64) about as often,
with no significant difference, while PHROGs named the spanin more often (0.89 vs 0.65). PHROGs assigned no class to
the curated gene in 4–10% of these genomes; using PHROGs where it makes a call and our model where it makes none never
did worse than PHROGs alone and improved endolysin and spanin calls. On 1,423 phage genomes
scanned from DNA alone in four blind designs, with calls committed before annotations were read, the annotated gene
was usually among the top five calls (holin 0.96, endolysin 0.97, spanin 0.96 in the first blind set). A pre-registered final test on
87 new genomes did not confirm the one model change it tested (endolysin training-label fix: 0.838 → 0.863,
one-sided p = 0.37), and confirmed agreement with annotation mainly for genes close to the training data. Membrane
topology from DeepTMHMM and SignalP 6.0, cross-checked with our own predictor, shows family-specific patterns
(class III holins in T4- and T5-like phages, unimolecular spanins in Drexlerviridae, SAR endolysins in Drexlerviridae
and P2-like phages). We release the models and a single command that accepts DNA or protein input, and recommend it
alongside, not instead of, profile-based annotation.

---

## 1. Background

The phage lysis cassette is among the best-studied small genetic modules in biology (Young 2014; Cahill & Young 2019),
yet it is hard to annotate automatically. Holins fall into dozens of families with little detectable homology
between them (TCDB superfamily 1.E; Saier *et al.* 2021), so homology search misses holins from families absent from
the reference set. Endolysins are modular enzymes with many catalytic folds, some exported by a signal-anchor-release
(SAR) domain rather than by the holin (Xu *et al.* 2004). Spanins are small membrane proteins, often encoded as an
outer-membrane lipoprotein (o-spanin) nested within the inner-membrane i-spanin gene, and are under-annotated
(Summer *et al.* 2007; Kongari *et al.* 2018). Profile databases such as PHROGs (Terzian *et al.* 2021), used by
Pharokka (Bouras *et al.* 2023), annotate known families well but by construction cannot recognise a family they have
not seen.

We asked two questions: **can a sequence-based classifier find each lysis gene across phage diversity, including
families it was not trained on, and how does it compare with profile-based annotation?** Because the central risk of
such work is measuring recovery of training data, every estimate below states how much of the target's family was
removed from training, and every interval accounts for related genomes.

## 2. Methods

### 2.1 Training data and labels

Positives for each class came from UniProt (reviewed entries and phage TrEMBL), Pfam/InterPro family members of phage
origin, TCDB, phage genomes mined from RefSeq, and, for spanins, the curated Center for Phage Technology (CPT) set of
Kongari *et al.* (2018). Negatives were 7,884 bacterial transmembrane proteins, 1,619 Swiss-Prot phage proteins and
3,382 phage proteins from 300 RefSeq genomes chosen to include hard confusables (Rz-like spanins and other
lysis-neighbourhood proteins). Each one-vs-rest model also treats the other two lysis classes as negatives. Every
source is recorded with URL, retrieval time and SHA-256 (`data/raw/*/provenance.json`).

**Label audits.** Training labels were audited after errors surfaced in testing:
- *Endolysin positives:* 51 virion-associated lytic proteins (T4-type tail lysozymes, T7-type internal virion
  proteins), found when they caused confident false calls in a blind scan, were moved to the negatives
  (`reports/endolysin_virion_fix.md`). Positives labelled only from genome product names were removed
  (`reports/evidence_only.md`).
- *Spanin positives:* name-labelled TrEMBL entries were kept only when corroborated by a lipobox or i-spanin
  topology, and 7 clearly wrong entries (plant RNA-binding proteins, peptidases, a phosphodiesterase, a holin) were
  removed (`reports/label_audit/label_audit.md`).
- *Holin positives:* 50 entries whose own database description names another function (15 PTS transporter subunits,
  ribokinases, restriction enzymes, endolysin-type enzymes) were identified. Removing them did not pass the
  pre-set non-inferiority rule (§2.6), so the shipped holin model still contains them; the list is released.

### 2.2 Features and models

Each protein is represented by 36 handcrafted features (length, Kyte–Doolittle transmembrane segments, terminal
charges, composition, hydrophobic-moment proxies) and the 480-dimensional mean-pooled embedding of ESM-2
(`esm2_t12_35M_UR50D`; Lin *et al.* 2023), 516 dimensions in all. Each class has a histogram gradient-boosted tree
classifier (scikit-learn; Pedregosa *et al.* 2011; 400 rounds, 31 leaves, learning rate 0.06). The endolysin model
trains without early stopping: scikit-learn's automatic early stopping holds out a random 10% of rows, which in
homology-rich data are near-copies of training rows, and stopped training at 104 of 400 rounds
(`reports/capacity_sweep.md`).

### 2.3 Genes from DNA

Genes are called with Pyrodigal (Larralde 2022; Hyatt *et al.* 2010). Standard gene finders do not report a gene
embedded in another gene's reading frame, which is where many o-spanins lie. A narrow finder adds nested ORFs inside
genes of 60–300 codons that begin with a lipoprotein signal: a lipobox ([LVI][ASTVI][GAS]C) with the cysteine at
residue 15–35, preceded by a hydrophobic h-region (mean Kyte–Doolittle ≥ 1.5) (`scripts/genecall.py`). It adds about
0.5 ORFs per genome.

### 2.4 One call per class

Each model scores proteins independently, but lysis genes usually sit together. For holins and endolysins the score
is re-ranked with genomic context, z = logit(P) + β × (the strongest other-class score among the protein's
neighbours), with β and the window fitted on CPT genomes (`scripts/46_context_rerank.py`, `models/context_params.json`).
For spanins, a learned second-stage caller combines the three class scores, neighbour scores, rank within the genome
and protein shape (`models/spanin_caller.pkl`). A learned caller was also tried for holins; its apparent gain vanished
when related phages were kept in the same cross-validation fold, so it was not used (`reports/integrated_caller.md`).
A call is marked confident when its context score clears a measured cut-off or it carries a catalytic lysis domain.

### 2.5 Evaluation protocols

**Leave-one-genome-out with homology removal.** For each test genome, before scoring it, training positives related
to its curated lysis genes are removed at one of three levels (`scripts/40_logo_benchmark.py`):

| protocol | removed from training | answers |
|---|---|---|
| known family | ≥95% identical sequences | a new phage whose gene is from a known family |
| unseen family | ≥30% identity (Smith–Waterman, coverage ≥0.5, score ≥80) and their whole homology clusters | a family absent from training at the sequence level |
| remote homology removed | additionally, every positive found by jackhmmer seeded with the curated gene (3 iterations, E ≤ 10⁻³; Johnson *et al.* 2010; PyHMMER, Larralde & Zeller 2023), and its cluster | a family with no detectable profile homologue in training |

Per genome we report whether the call is the curated gene and whether the curated gene is in the top five proteins.

**Benchmarks with independent ground truth.**
- *CPT curated set:* 129 genomes whose lysis genes were assigned by hand at the CPT (125 endolysins, 78 holins,
  162 spanins).
- *Experimental set:* 24 genomes with UniProt lysis proteins evidenced at protein level, reduced to DNA.
- *Reviewed set:* 42 genomes carrying Swiss-Prot reviewed lysis proteins (43 endolysins, 19 holins, 18 spanins).

**Blind scans.** For the scans of unseen genomes, the predictor received DNA only, its calls were committed to git
before any annotation was opened, and they were then scored against the genome's own annotation under matching rules
fixed in advance (`scripts/52a–c`). These measure **agreement with annotation, not accuracy**: annotations of recent
phage genomes are largely automated and some are wrong (§3.3).

**Related genomes.** Phage benchmarks contain near-identical genomes (three lambda immunity variants in CPT, ten
identical Vibrio phages in the lambdoid set), so resampling genomes as independent gives intervals that are too
narrow. Genomes were grouped by single linkage on shared gene content: Jaccard ≥ 0.10 between MinHash sketches of all
amino-acid 5-mers of their proteins (a genus-like level), with whole-genome ANI ≥ 95% (Mash-style DNA 21-mer sketches;
Ondov *et al.* 2016) as a second, finer level (`scripts/58_genome_clusters.py`). The effective sample size is about
half the genome count (CPT 129 genomes → 60 gene-content clusters; experimental set 24 → 20; blind set 1 152 → 65;
blind set 2 123 → 45). **All 95% intervals and paired tests below resample gene-content clusters** (cluster bootstrap,
4,000 draws; Field & Welsh 2007) unless stated otherwise.

### 2.6 Decisions and the final test

Development decisions were made on CPT and the experimental set, with the rule for adopting each change written down
before the run. A change justified by correctness alone (a label fix) was adopted if it was non-inferior: the lower
95% bound of the change in unseen-family top-1 and top-5 on CPT had to stay above −0.05. A change justified by
performance needed a paired interval excluding zero.

Before any final-test genome was selected, the pipeline was frozen (model and script SHA-256 hashes) together with a
pre-registered analysis plan (`reports/final/FROZEN.md`, commit 2376b6e): one confirmatory hypothesis (H1, one-sided,
α = 0.05, so no multiplicity correction), estimation endpoints with intervals but no tests, and descriptive secondary
analyses. Anything else run on the final set is labelled exploratory.

### 2.7 Comparison with existing tools

- **PHROGs** v4 (38,880 profiles, 305 in the lysis category; from the Pharokka v1.11.0 database bundle, Zenodo record
  21755221), searched with PyHMMER; as in Pharokka, each protein takes its best PHROG (E ≤ 10⁻⁵), and proteins whose
  best PHROG's name marks it as a holin, endolysin or spanin (the same name rules as for annotations) are ranked by
  bit score.
- **Pfam lysis domains** (Mistry *et al.* 2021), ranked by E-value.
- **Hybrid:** PHROGs where it assigns the class in a genome, our model where it assigns nothing.

PHROGs was built from genomes available around 2019–2020 and has effectively seen most benchmark genes, so the
fairest comparison is on CPT genomes first submitted to GenBank from 2022 on (`scripts/60_baselines.py`). Differences
from PHROGs are tested with a paired cluster bootstrap; these tests were added after the comparison was first made and
are not corrected for multiplicity.

### 2.8 Membrane topology

Holin class (I/II/III = 3/2/1 transmembrane helices) and orientation, spanin type and SAR endolysins were assigned
with DeepTMHMM (Hallgren *et al.* 2022) and SignalP 6.0 (Teufel *et al.* 2022), run on the public lysis-protein
sequences via the BioLib service, and with our own predictor as an independent check. Our predictor is a per-residue
logistic regression on ESM-2 embeddings and local hydropathy, trained on 3,225 Swiss-Prot bacterial and viral
proteins (helical, soluble and signal-peptide) with all phage lysis proteins held out; orientation follows the
positive-inside rule (von Heijne 1989), counting K+R within 15 residues of each helix end (`scripts/55_tm_predictor.py`).
Both predictors were scored against the 449 reviewed proteins whose every transmembrane feature has experimental
evidence (ECO:0000269) and that our predictor did not train on (`scripts/55c_tm_experimental.py`). A SAR endolysin is
called only when our N-terminal SAR rule and DeepTMHMM (signal-like N terminus) agree; lipoproteins (o- and
u-spanins) are taken from SignalP's Sec/SPII call (`scripts/57_consensus_topology.py`).

## 3. Results

### 3.1 How well the models generalise

CPT curated genomes, per genome, 95% cluster-bootstrap intervals (`reports/remote_homology.md`):

| | known family | unseen family (30%) | remote homology removed |
|---|---|---|---|
| holin, call is the curated gene | 0.71 [0.53, 0.86] | 0.54 [0.39, 0.71] | **0.50** [0.35, 0.68] |
| holin, curated gene in top 5 | 0.94 [0.88, 0.99] | 0.85 [0.74, 0.95] | **0.83** [0.72, 0.93] |
| endolysin, call | 0.87 [0.79, 0.94] | 0.74 [0.63, 0.84] | **0.55** [0.39, 0.71] |
| endolysin, top 5 | 0.99 [0.98, 1.00] | 0.90 [0.83, 0.96] | **0.82** [0.66, 0.94] |
| spanin, curated gene in top 5 | 0.93 [0.83, 1.00] | 0.91 [0.79, 0.99] | **0.90** [0.77, 0.99] |

Holins and spanins lose little when remote homologues are removed, so their unseen-family performance does not rest
on profile-detectable homologues left in training; the models appear to recognise membrane topology, lipoprotein
signals and size rather than only family membership. Endolysins lose the most (top pick 0.74 → 0.55): their
catalytic domains belong to ancient enzyme families, and the model draws on that remote similarity. For an endolysin
of a genuinely new fold, the honest statement is "in the top five about 80% of the time".

The pattern holds on the other curated sets (`reports/final/final_results.md`, `reports/validated_benchmark.md`).
Reviewed Swiss-Prot set, call / top 5: holin 0.84/1.00 (known), 0.79/0.90 (unseen), 0.74/0.90 (remote removed);
endolysin 0.90/1.00, 0.61/0.92, 0.46/0.85; spanin 0.80/1.00, 0.80/1.00, 0.60/1.00. The intervals on this set are wide
(19 holins, 10 spanin genomes).

**Use as a shortlist.** In every protocol the curated gene is in the top five far more often than it is the top
pick. The tool reports a ranked shortlist as well as one call per class.

**Development benchmark.** During development a 66-genome panel (180 annotated lysis genes) was scored by
genome-scan average precision: holin 0.75 (known family) / 0.61 (unseen family), endolysin 0.81 / 0.61, spanin
0.80 / 0.57 (`reports/genome_benchmark_*.json`). These intervals resampled genomes, not clusters, and are given only
for continuity with earlier reports.

**Gene finding.** From bare DNA, Pyrodigal does not produce 48 of CPT's 162 curated spanins. The nested lipoprotein
ORF finder recovers 24 of them and raises the share of CPT genomes whose curated spanin is in the top five, from DNA
under the unseen-family protocol, by +0.131 [+0.065, +0.216] (`reports/denovo_gene_calling.md`,
`reports/clusters/reassessment.md`). On the experimental set it recovers all three missed o-spanins.

**Calling one gene.** The context rule raises the share of curated holins ranked first in 5-fold cross-validation
over CPT genomes by about 10 points (54 → 64% unseen family; 71 → 81% known family), endolysins by 4–6 and spanins
by 4, with no measure made worse. Out of fold, with related genomes kept together, confident calls were correct for
85–98% of genes depending on class and protocol (`reports/integrated_caller.md`).

### 3.2 Comparison with PHROGs and Pfam

CPT genomes first submitted from 2022 on, call is the curated gene (`reports/baselines/baselines.md`):

| | PHROGs | ours, known family | ours, unseen family | PHROGs, else ours (unseen) |
|---|---|---|---|---|
| holin (33 genomes) | 0.64 [0.41, 0.87] | 0.76 [0.54, 0.97] | 0.48 [0.28, 0.74] | 0.67 [0.45, 0.90] |
| endolysin (50) | 0.82 [0.62, 0.95] | 0.92 [0.82, 0.98] | 0.76 [0.58, 0.89] | 0.92 [0.79, 1.00] |
| spanin (46) | **0.89** [0.71, 1.00] | 0.65 [0.41, 0.91] | 0.54 [0.32, 0.77] | **0.91** [0.74, 1.00] |

- **Holins and endolysins: no significant difference.** Ours minus PHROGs, paired, on all CPT genomes: holin −0.05
  [−0.27, +0.15], endolysin +0.12 [−0.02, +0.27] (known family); under the unseen-family protocol, −0.22 [−0.44, +0.01]
  and −0.03 [−0.18, +0.13].
- **Spanins: PHROGs names the gene more often** (0.89 vs 0.65 on recent genomes; −0.35 [−0.58, −0.09] against our
  unseen-family protocol), although both put it in the top five equally often.
- **Coverage.** PHROGs assigns no class to the curated gene in 6–8% of CPT genomes per class (endolysin 8%, 10% from
  2022 on); our model always ranks it.
- **Hybrid.** PHROGs where it calls and our model where it does not improves on PHROGs alone for endolysins (+0.08
  [+0.01, +0.16]) and spanins (+0.04 [+0.01, +0.10]), never does worse, and has the curated gene in the top five in
  every recent genome. Over all CPT genomes: holin 0.78, endolysin 0.86, spanin 0.93 (our model alone, known family:
  0.70, 0.90, 0.79). **We therefore recommend running the predictor alongside Pharokka.**

An earlier version of this comparison understated PHROGs on endolysins (0.58 on recent genomes) because a speed-up
skipped 24 endolysin-named PHROGs outside the lysis category; the error was found when the per-gene data release was
rebuilt from scratch and checked against the reported numbers.

Pfam lysis domains alone call 0.54 (holin), 0.74 (endolysin) and 0.31 (spanin) on CPT. PHROGs has no equivalent of
the unseen-family fallback: its misses are coverage gaps.

### 3.3 Blind scans of unseen genomes from DNA

**Blind set 1** (`reports/blind/blind_scan.md`): 152 tailed-phage genomes deposited from June 2026, 26 host genera.

| | genomes with the gene annotated | call is the annotated gene | annotated gene in top 5 |
|---|---|---|---|
| holin | 104 | 0.885 | 0.962 |
| endolysin | 130 | 0.838 | 0.969 |
| spanin | 92 | 0.761 | 0.957 |

(Intervals here resampled genomes; with gene-content clusters they widen but the point estimates stand.) Split by the
annotated gene's identity to training, the known-family column (30–95%) is the fair estimate for a typical new phage:
the gene was in the top five 95–96% of the time and named outright 71–80% of the time. Only 8 genes were from new
families. The main confident error, calling virion tail lysozymes as endolysins, led to the label fix of §2.1.

**The endolysin label fix.** Moving the 51 virion proteins to the negatives raised the endolysin top pick on CPT
(unseen family) and the endolysin call on a second blind set of 123 genomes by about 6 points in each, borderline in
each set alone (p ≈ 0.07 with cluster resampling) and significant when the two sets are pooled with clusters built
jointly across them: +0.060 [+0.020, +0.103], p = 0.008. This pooled test was not planned in advance
(`reports/clusters/reassessment.md`).

**Nine phage groups** (`reports/groups/groups_scan.md`, `reports/n4/n4_scan.md`): 1,061 GenBank genomes not used
elsewhere, at most 15 per host genus, scanned from DNA with calls frozen before scoring.

| group | genomes | holin call / top 5 | endolysin call / top 5 | spanin pair / top 5 |
|---|---|---|---|---|
| N4-like (Schitoviridae) | 255 | 0.64 / 0.99 | 0.97 / 1.00 | 0.90 / 1.00 |
| Lambdoid / P22-like (mixed) | 120 | 0.80 / 0.85 | 0.92 / 0.95 | 0.98 / 0.98 |
| T7-like (Autographiviridae) | 120 | 0.92 / 1.00 | 0.92 / 0.97 | 0.95 / 0.98 |
| P2-like (Peduoviridae) | 111 | 0.92 / 1.00 | 0.95 / 0.99 | 1.00 / 1.00 |
| Drexlerviridae | 101 | 0.97 / 1.00 | 0.97 / 0.98 | 0.98 / 0.98 |
| T5-like (Demerecviridae) | 106 | 0.96 / 0.99 | 0.96 / 0.99 | 0.89 / 0.92 |
| Herelleviridae (Gram-positive hosts) | 88 | 0.90 / 0.98 | 0.83 / 0.99 | none annotated |
| T4-like (Straboviridae) | 100 | 0.89 / 0.99 | 0.61 / 0.97 | 0.94 / 1.00 |
| Jumbo (> 200 kb) | 60 | 0.17 / 0.50 (6 annotated) | 0.61 / 0.84 | 0.46 / 0.91 |

Disagreements were examined case by case:
- **Gram-positive control.** Herelleviridae hosts have no outer membrane and no spanins are annotated; the predictor
  made a confident spanin call in 22 of 88 genomes (25%), against 87–99% in every Gram-negative group. It mostly
  recognises the absence; the 22 are false positives.
- **Lambdoid holins.** 10 of 16 disagreements are one protein, identical in 10 Vibrio phages, annotated "holin" but
  119 aa with no transmembrane segment and no similarity to any known holin; the model ranks it ~78th. Excluding
  these genomes, the call agrees in 63 of 69 (0.91).
- **N4-like holins.** In 33 of 34 disagreements the called protein is the gene immediately next to the annotated
  holin, and the annotated one is ranked second (§3.7).
- **T4-like endolysins.** In 23 of 26 disagreements the annotated endolysin is ranked second; the call is a
  180–215 aa protein annotated as hypothetical or as an RNA endonuclease with no real similarity to training
  endolysins. T4's lysis genes are scattered, so context cannot help. These proteins are a candidate set of hard
  negatives for a future model (not used in the frozen model).
- **Jumbo phages** are the weakest group: few annotated lysis genes, and 300–600 genes per genome to choose among.

Earlier, smaller panels gave consistent results: an out-of-sample panel of 38 genomes (23 actinobacterial) recovered
25 of 26 annotated holins and 36 of 37 endolysins, including 7 actinobacterial holins not identical to any training
sequence; marine cyanophage endolysins scored lowest (S-PM2 0.60, P-SSM2 0.63).

### 3.4 The pre-registered final test

The frozen rules (the blind-set query, every genome used anywhere in the project excluded by accession and by DNA
identity, at most 25 per host genus) left 311 eligible genomes in only four host genera, giving **87 genomes**
(Escherichia 25, Klebsiella 25, Pseudomonas 25, Salmonella 12) in 34 gene-content clusters — smaller and narrower than
intended, and reported as defined (`reports/final/final_results.md`).

**H1 (confirmatory): not confirmed.** The virion-fixed endolysin model's call matched the annotated endolysin in
0.863 of genomes against 0.838 for the retired model (+0.025; 2 genomes fixed, 0 broken; 80 genomes, 31 clusters;
one-sided p = 0.37). The direction agrees with development, but this set contains few phages with the virion
lysozymes the fix targets. The fix stands because it corrects mislabelled training data; its effect on new genomes is
not established.

**Estimation endpoints (agreement with annotation):**

| | call is the annotated gene | annotated gene in top 5 |
|---|---|---|
| holin (59 genomes, 25 clusters) | 0.93 [0.82, 1.00] | 0.98 [0.94, 1.00] |
| endolysin (80, 31) | 0.86 [0.70, 0.97] | 1.00 |
| spanin (69, 27) | 0.74 [0.54, 0.90]; either pair member 0.85 [0.67, 0.97] | 0.99 [0.95, 1.00] |

Of the annotated genes, 137 were near-copies of training sequences (≥95%), 68 from known families and only 3 from
new families. **The final test therefore confirms performance on familiar genes and says almost nothing about new
families**; the evidence for those is §3.1.

### 3.5 What was tried and what survived

Every model variant tried during development is listed with its decision and report (`reports/final/final_results.md`,
disclosure table). Summary:

| change | decision | evidence |
|---|---|---|
| Phage-derived hard negatives (incl. Rz-like spanins) | adopted | removed Rz-like spanin false positives the bacterial negatives never showed the models |
| CPT/Kongari curated spanins | adopted | spanin class went from unusable (zero strict recall) to working |
| Endolysin early stopping off | adopted | development AP +0.046 [+0.017, +0.070] (genome resampling, before clustering was introduced) |
| Endolysin: evidence-only labels, then virion proteins removed | adopted | §3.3; H1 not confirmed on the final set |
| Spanin: signal-corroborated labels, then label audit | adopted | unseen-family top 5 +5.6 points (p = 0.049, genome resampling); audit non-inferior (+0.006 [0, +0.023]) |
| Nested lipoprotein ORF finder | adopted | +0.131 [+0.065, +0.216] |
| Genomic-context rule; learned caller for spanins only | adopted | §3.1 |
| Holin label audit (50 mislabelled entries removed) | not adopted | top-1 −0.026 [−0.093, +0.043]: non-inferiority not shown |
| Holin variants: family weighting, context-mined new families (2 versions), 3 ensembles, ESM-2 150M, topology features | rejected | none improved; earlier claims that some were *significantly worse* did not survive cluster resampling and are withdrawn |
| Endolysin family expansion (+14 catalytic families) | rejected | AP −0.061 [−0.113, −0.011] (genome resampling); a composition effect, not volume |
| Stacked specialists, self-training, similarity-to-training features, larger trees | rejected | `reports/capacity_sweep.md`, `reports/similarity_features.md` |

A mined-family holin ensemble is kept as an opt-in "T4-aware" mode; it is not the default and was not part of the
frozen pipeline.

### 3.6 Membrane topology

**Validation against experimental topologies** (`reports/tm_experimental.md`):

| | our predictor | DeepTMHMM | hydropathy heuristic |
|---|---|---|---|
| bacteria + viruses (22 proteins): exact helix count | 0.86 | **0.95** | 0.59 |
| all organisms (449): exact helix count | 0.51 | **0.86** | 0.29 |
| all organisms: N-terminus side correct | 0.77 | **0.94** | – |

Within its training domain our predictor is close to DeepTMHMM; outside it (mostly eukaryotic multi-pass proteins) it
misses helices. DeepTMHMM is therefore the primary source for holin class; ours is a concordance check.

**Agreement on lysis proteins** (2,693 distinct proteins; `reports/external/comparison.md`):
- Holin class agreed in 76–100% of genomes in eight of nine families. Both give the literature topology for the
  reference holins: lambda S and P22 gp13 three helices with the N terminus out (UniProt lists two; Gründling *et al.*
  2001); T4 t one helix, N in (Ramanculov & Young 2001); phage 21 pinholin two helices (Pang *et al.* 2009).
- **T7-like holins are unresolved** (48% agreement): for T7 gp17.5, UniProt and ours give one helix and DeepTMHMM two.
- SAR endolysins: DeepTMHMM labels all 13 Swiss-Prot SAR endolysins as signal-like; SignalP only 6, as expected for an
  uncleaved anchor. Our SAR rule and DeepTMHMM agree within a few points in six of nine families; our rule over-calls
  N4-like endolysins (39% vs 1%), so only consensus calls are reported. Our rule was calibrated on the same 44
  Swiss-Prot endolysins it separates, so it is not independently validated.
- Lipoproteins: SignalP 6.0 confirms 577 of the 579 spanin members our lipobox motif calls, and finds 103 more.

### 3.7 Lysis genes across phage families

From the blind calls for 1,061 genomes in nine groups, with sequence properties and Pfam domains but no annotation
names (`reports/distribution/lysis_distribution.md`). Every value is a model call and carries that group's error rate;
95% intervals resample gene-content groups, and the effective sample sizes are small (Drexlerviridae 101 genomes → 9
groups; T5-like 106 → 14; N4-like 255 → 42) (`reports/distribution/uncertainty.md`).

**Patterns that are well supported** (narrow intervals, calls matching annotations in ≥80% of genomes), and that agree
with known biology:
- Drexlerviridae: unimolecular spanins 95% [91, 100] (as in phage T1, a member of this family); SAR endolysins 94%
  [90, 99]; class III holins 99%.
- Herelleviridae (Gram-positive hosts): no confident spanin in 75% [61, 87]; class II holins 91%; the longest,
  most modular endolysins, amidase domains in 60% [30, 82].
- T4-like: lysis genes never co-located (0%), consistent with T4's scattered lysis genes; two-component spanins 83%
  [57, 94]; class III holins.
- Unimolecular spanins are essentially absent outside Drexlerviridae.
- Endolysin chemistry follows the family: T5-like mostly peptidases (T5's endolysin is a peptidase), T7-like often
  amidases (T7 gp3.5), Drexlerviridae glycosidases.
- Cassette order is conserved: holin–endolysin–spanin in 97–99% of co-located lambdoid, P2-like and Drexlerviridae
  cassettes.

**Patterns that are uncertain** and should be stated qualitatively: the holin class mix in N4-like (class I 40%
[8, 72]) and lambdoid phages; T5-like endolysins as peptidases (87% [33, 96], 106 genomes in 14 groups, one of 69);
holin copy number in most families. Group labels: "lambdoid" is a mixed set (48 P22-like, 42 records described as
lambda-like, 12 Vibrio phages of doubtful membership); "jumbo" is a size class.

### 3.8 Hypotheses for experimental follow-up

These are predictions, not findings, and are listed with the evidence for each.

- **Adjacent holin-family genes in N4-like phages.** In 33 of the 34 N4-like genomes where the holin call disagrees
  with the annotation, the called gene is immediately next to the annotated holin; 29 of these belong to one family
  (104–124 aa) whose annotations are inconsistent ("hypothetical", "antiholin", and implausibly "tape-measure
  protein"). Both genes are holin-family proteins by sequence. Which one is the functional holin, and whether the pair
  is a holin–antiholin system, is testable in N4. More generally, across 300 RefSeq genomes, genomes with two strong
  holin-fold genes place them a median of 2 genes apart against 22 under random placement; the model has no positional
  input, so this clustering is not a model artefact (`reports/dual_holin_analysis.json`).
- **Unannotated o-spanins.** The nested-ORF finder applied to 5,113 RefSeq phage genomes found 303 high-confidence
  (tier A) lipoprotein ORFs embedded in 301 genomes. In 238 of these RefSeq annotates the host gene as an i-spanin or
  Rz-like spanin, and only 2 genomes annotate an o-spanin anywhere. On CPT, tier-A calls were correct for 22 of 24
  (`reports/unannotated_ospanins.md`).
- **Holins in genomes annotated without one.** In the first blind set, 22 confident holin calls with 1–3
  transmembrane segments beside another lysis call, in genomes whose annotation lists no holin
  (`reports/blind/candidate_additions.tsv`).
- **Topology.** Drexlerviridae combine SAR endolysins with single-helix holins whose N terminus faces out — the
  arrangement expected of a pinholin whose first helix is not detected.

## 4. Software

`scripts/32_predict_lysis.py` accepts protein FASTA, nucleotide FASTA, GenBank or an NCBI accession and reports, per
protein, P(holin), P(endolysin), P(spanin), the context-ranked shortlist and one call per class with a confidence
flag (`DEPLOY.md`). Raw DNA is gene-called with Pyrodigal plus the nested lipoprotein ORF finder (on by default;
`--no-nested` to disable). A Galaxy wrapper is provided. Dependencies are pinned (scikit-learn 1.9.1, as the models
are pickled estimators); the ESM-2 weights (~130 MB) download on first run. The frozen versions used for the final
test are listed by SHA-256 in `reports/final/FROZEN.md`.

## 5. Limitations

- **Ground truth.** Blind scans and the final test measure agreement with GenBank annotation, which is largely
  automated and sometimes wrong (§3.3). The curated CPT, experimental and reviewed sets are the independent ground
  truth, and they are small: 60, 20 and fewer than 42 independent genome groups.
- **New families.** The final test held only 3 annotated genes from new families. Generalisation rests on the
  leave-one-genome-out protocols, where endolysins from genuinely new folds are ranked first only about half the time.
- **H1 not confirmed.** The one confirmatory test failed to reach significance; the endolysin fix is supported by
  pooled development data in a test that was not planned in advance.
- **Final set breadth.** The final set covers four enterobacterial and Pseudomonas host genera only.
- **Spanins.** PHROGs names the spanin more often than our model; the hybrid is recommended.
- **Weak groups.** Jumbo phages, T4-like endolysins and N4-like holins have the lowest agreement; Gram-positive phages
  receive false spanin calls in a quarter of genomes; marine cyanophage endolysins score low.
- **Holin labels.** The shipped holin model still contains 50 positives we know to be mislabelled.
- **Topology.** The T7-like holin class is unresolved; our SAR rule is calibrated rather than independently tested;
  family-level topology patterns are model calls with the intervals given.
- **Development reuse.** Model choices were made on CPT, so CPT figures for the chosen models are mildly optimistic;
  the blind sets and the final set were not used for choices, except that blind set 1 revealed the virion-lysozyme
  error.

## 6. Data and code availability

All code, models, reports and data provenance are in this repository (branch `claude/holin-ml`); the pipeline from
sources to deployment is documented in `PROTOCOL.md`. Every individual result is in `release/` as flat tables with a
data dictionary (`release/README.md`) and one Excel workbook: each genome and its relatedness clusters, each call in
every scan with its annotation match and the frozen prediction version (with model SHA-256), every protein's scores,
membrane topology from all three tools for every called protein, each curated benchmark gene's rank under every
protocol with its PHROGs and Pfam hits, the family-level features, the candidate lists, and every development
decision. The tables are rebuilt by `scripts/62_build_release.py`, which checks that they reproduce the reported
numbers (`release/build_checks.json`). Bulk sequence downloads are regenerable from the recorded
queries and accessions and are not version-controlled. Blind-scan predictions are in the commits named in each
report, made before annotations were read. Public lysis-protein sequences were sent to the BioLib service to run
DeepTMHMM and SignalP 6.0.

## References

References should be checked against the published records before submission.

- Bouras G, Nepal R, Houtak G, Psaltis AJ, Wormald PJ, Vreugde S. Pharokka: a fast scalable bacteriophage annotation
  tool. *Bioinformatics* 2023;39:btac776.
- Cahill J, Young R. Phage lysis: multiple genes for multiple barriers. *Adv Virus Res* 2019;103:33–70.
- Field CA, Welsh AH. Bootstrapping clustered data. *J R Stat Soc B* 2007;69:369–390.
- Gründling A, Manson MD, Young R. Holins kill without warning. *Proc Natl Acad Sci USA* 2001;98:9348–9352.
- Hallgren J, Tsirigos KD, Pedersen MD, *et al.* DeepTMHMM predicts alpha and beta transmembrane proteins using deep
  neural networks. *bioRxiv* 2022. doi:10.1101/2022.04.08.487609.
- Hyatt D, Chen GL, LoCascio PF, *et al.* Prodigal: prokaryotic gene recognition and translation initiation site
  identification. *BMC Bioinformatics* 2010;11:119.
- Johnson LS, Eddy SR, Portugaly E. Hidden Markov model speed heuristic and iterative HMM search procedure.
  *BMC Bioinformatics* 2010;11:431.
- Kongari R, Rajaure M, Cahill J, *et al.* Phage spanins: diversity, topological dynamics and gene convergence.
  *BMC Bioinformatics* 2018;19:326.
- Kyte J, Doolittle RF. A simple method for displaying the hydropathic character of a protein. *J Mol Biol*
  1982;157:105–132.
- Larralde M. Pyrodigal: Python bindings and interface to Prodigal, an efficient method for gene prediction in
  prokaryotes. *J Open Source Softw* 2022;7:4296.
- Larralde M, Zeller G. PyHMMER: a Python library binding to HMMER for efficient sequence analysis. *Bioinformatics*
  2023;39:btad214.
- Lin Z, Akin H, Rao R, *et al.* Evolutionary-scale prediction of atomic-level protein structure with a language
  model. *Science* 2023;379:1123–1130.
- Mistry J, Chuguransky S, Williams L, *et al.* Pfam: the protein families database in 2021. *Nucleic Acids Res*
  2021;49:D412–D419.
- Ondov BD, Treangen TJ, Melsted P, *et al.* Mash: fast genome and metagenome distance estimation using MinHash.
  *Genome Biol* 2016;17:132.
- Pang T, Savva CG, Fleming KG, Struck DK, Young R. Structure of the lethal phage pinhole. *Proc Natl Acad Sci USA*
  2009;106:18966–18971.
- Pedregosa F, Varoquaux G, Gramfort A, *et al.* Scikit-learn: machine learning in Python. *J Mach Learn Res*
  2011;12:2825–2830.
- Ramanculov E, Young R. An ancient player unmasked: T4 *rI* encodes a t-specific antiholin. *Mol Microbiol*
  2001;41:575–583.
- Saier MH Jr, Reddy VS, Moreno-Hagelsieb G, *et al.* The Transporter Classification Database (TCDB): 2021 update.
  *Nucleic Acids Res* 2021;49:D461–D467.
- Summer EJ, Berry J, Tran TAT, Niu L, Struck DK, Young R. Rz/Rz1 lysis gene equivalents in phages of Gram-negative
  hosts. *J Mol Biol* 2007;373:1098–1112.
- Terzian P, Olo Ndela E, Galiez C, *et al.* PHROG: families of prokaryotic virus proteins clustered using remote
  homology. *NAR Genom Bioinform* 2021;3:lqab067.
- Teufel F, Almagro Armenteros JJ, Johansen AR, *et al.* SignalP 6.0 predicts all five types of signal peptides using
  protein language models. *Nat Biotechnol* 2022;40:1023–1025.
- von Heijne G. Control of topology and mode of assembly of a polytopic membrane protein by positively charged
  residues. *Nature* 1989;341:456–458.
- Xu M, Struck DK, Deaton J, Wang IN, Young R. A signal-arrest-release sequence mediates export and control of the
  phage P1 endolysin. *Proc Natl Acad Sci USA* 2004;101:6415–6420.
- Young R. Phage lysis: three steps, three choices, one outcome. *J Microbiol* 2014;52:243–258.
