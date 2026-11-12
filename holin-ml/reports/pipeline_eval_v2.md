# Did the ML + HMM pipeline actually get better? 72 genomes, 180 annotated lysis genes

Measured with `scripts/37_eval_hybrid.py`, stratified with `scripts/38_hybrid_summary.py`. The test: for a lysis
gene we know is present, does **evidence-aware ranking** (domain tier first, then model probability) put it nearer
the top than **model-only ranking**?

**Circularity caveat, which applies to every HMM column below.** Ground truth is the GenBank product name, and
phage lysis-gene annotations are usually produced by homology or domain search — so the HMM half shares a lineage
with the labels it is graded against, and its advantage on *annotated* genes is partly circular. The model-only
column has no such problem. The case that matters most (an unannotated "hypothetical protein" in an
out-of-distribution genome) has no ground truth and cannot be scored here at all.

## Answer: barely, on annotated genomes — because there was almost no headroom

### Classic panel phages (166 annotated lysis genes, 50 genomes)

| class | n | median rank | top-1 | recall@5 | better | worse | had domain |
|---|---|---|---|---|---|---|---|
| holin | 46 | 1 → 1 | 0.74 → **0.80** | 0.98 → 0.98 | 3 | **0** | 31 |
| endolysin | 90 | 1 → 1 | 0.60 → 0.62 | 0.93 → 0.94 | 10 | 7 | 61 |
| spanin | 30 | 1 → 1 | 0.60 → **0.57** | 1.00 → 1.00 | 4 | **5** | 17 |
| **all** | 166 | 1 → 1 | 0.64 → 0.66 | 0.96 → 0.96 | 17 | 12 | 109 |

Exit-lysins-only (virion-named truths removed) moves endolysin top-1 to 0.75 → 0.77.

Read honestly:
- **Holin: a real, safe gain.** +6 points of top-1 and, in 46 cases, it never once made a holin rank worse.
- **Endolysin: marginal.** +2 points, with 10 genes improved and 7 made worse — noise-dominated.
- **Spanin: slightly worse.** −3 points top-1, 5 genes worsened against 4 improved. The cause is mechanical: the
  tier is per class, so a *non-annotated* protein carrying a spanin-family hit gets promoted above a true spanin
  that has no hit. A real, small cost of domain-first ranking.
- **The ceiling was already there.** Recall@5 was 0.96–1.00 *before* the HMMs. On genomes like these the model was
  already finding the genes; there was nothing for the HMM to recover.

### crAss-like phages (10 annotated lysis genes, 7 genomes) — the interesting half

| class | n | median rank | top-1 | recall@5 | had domain |
|---|---|---|---|---|---|
| holin | 6 | 2 → 2 | 0.50 → 0.50 | 1.00 → 1.00 | **0 of 6** |
| endolysin | 4 | 1 → 1 | 1.00 → 1.00 | 1.00 → 1.00 | 3 of 4 |
| spanin | **0** | — | — | — | — |

Three findings here matter more than the aggregate table:

1. **No crAss-like holin has a Pfam holin domain — 0 of 6.** The HMMs are blind to them, so the **ML model is the
   only thing that finds them**, and it puts all 6 within the top 5 (3 at rank 1, the rest at ranks 3–5, with
   P ranging 0.025 to 0.9999). This is the clearest evidence in the project that the holin model earns its place:
   on novel genomes it does work no domain method can.
2. **The added endolysin families pay off here.** The crAss-like endolysins hit **PF01832** (the DAC15 family) and
   **PF05838 (GH108)** — both added in this week's expansion. And `M1M53_gp083` scores **P = 0.4861**, *below the
   0.5 threshold*, so the model would not have called it — the domain hit rescues it. That is a second
   independent case of the HMM catching an endolysin the model under-scores.
3. **Not one of the 8 crAss-like genomes has an annotated spanin.** Combined with DAC15's rejected gp004/gp008,
   this is a consistent pattern across the clade, not a one-genome oddity: **crAss-like outer-membrane disruption
   is unidentified**, even though these are Gram-negative-host phages.

## *Escherichia* phage Serwaa (PX021331.1) — a canonical cassette, and one bad miss

62,144 bp, 85 CDS, CPT-annotated, with all four lysis genes adjacent on the + strand. The o-spanin gene sits
entirely inside the i-spanin gene in a different frame — the classic λ Rz/Rz1 arrangement.

| gene | class | size | P | model rank | evidence rank | domain |
|---|---|---|---|---|---|---|
| CPT_Serwaa_012 | holin | 112 aa | **0.9999** | **1** | **1** | PF16083 holin/family (2.2e-12) |
| CPT_Serwaa_010 | o-spanin | 84 aa | **0.9887** | **1** | **1** | **PF28595** spanin/family (2.4e-09) |
| CPT_Serwaa_009 | i-spanin | 179 aa | **0.9821** | 2 | 2 | — |
| CPT_Serwaa_011 | **endolysin** | 145 aa | **0.3641** | **6** | **6** | **none** |

**Three of four, essentially perfect.** The holin is called at 0.9999 with domain support; both spanins score
>0.98 and occupy ranks 1–2. Note the o-spanin hit **PF28595 (RzoQ)** — one of the spanin families added this
week — so the family expansion is validated on a real genome, not just a benchmark.

**The endolysin is a clean, unambiguous failure, and both halves of the pipeline fail on it.** It scores 0.3641
(below threshold), ranks 6th, and matches none of the 74 lysis HMMs. What the model ranked *above* it:

| rank | gene | P | annotated as |
|---|---|---|---|
| 1 | CPT_Serwaa_021 | 0.9692 | **head-tail joining protein** |
| 2 | CPT_Serwaa_031 | 0.8725 | peptidase |
| 3 | CPT_Serwaa_034 | 0.6548 | minor tail protein (1,687 aa) |
| 4 | CPT_Serwaa_059 | 0.5969 | RNAse H-like protein |
| 5 | CPT_Serwaa_006 | 0.4139 | protease |
| **6** | **CPT_Serwaa_011** | **0.3641** | **endolysin** |

On a textbook cassette the endolysin model's top pick is a head-tail joining protein.

**And this is not a coverage gap.** Its nearest training endolysin is **50.4% identical at coverage ≥0.8** — the
family *is* represented. Contrast DAC15 gp039, whose 80.3%-identical relative was absent from training. So the two
failures have different causes and both land on the same component:

| | DAC15 gp039 | Serwaa CPT_Serwaa_011 |
|---|---|---|
| nearest training relative | 80.3% (absent before this week) | **50.4% (present all along)** |
| model score | 0.0059, rank 25 | 0.3641, rank 6 |
| lysis domain | PF01832, E = 9.4e-17 | **none of 74 HMMs** |
| diagnosis | coverage gap | **pure model failure** |
| rescued by HMM? | **yes** (rank 25 → 1) | **no** |

**InterProScan settles the open question: no domain anywhere.** A full InterProScan 5.78 run
(`reports/serwaa011_interproscan.json`) on CPT_Serwaa_011 found **zero matches across all 23 member
analyses** -- Pfam 38.2, CDD, SMART, PANTHER, NCBIfam, HAMAP, PIRSF, PRINTS, PROSITE, SFLD, the structural
classifiers Gene3D/FunFam and SUPERFAMILY, and also SignalP, Phobius and TMHMM (no signal peptide, no
transmembrane segment). EBI's pre-computed lookup failed for this sequence, so every analysis was run on it
from scratch; the null is not a missing cache entry.

So this endolysin belongs to a family that **no domain database recognises**, even at the fold level --
yet it is 50.4% identical, at coverage >=0.8, to an endolysin in our own training set. That pins down what
each part of the pipeline can do with it:

- **The HMM layer can never catch it.** There is no signature to match, in our 74 HMMs or in InterPro.
- **Homology can.** A training relative at 50% identity is a strong signal, which the earlier model scored
  only 0.3641. (Follow-up: the current endolysin model scores it 0.894 without any similarity input, and an
  explicit similarity input was tested and rejected -- `reports/similarity_features.md`.)
- **Genomic context can.** It sits inside a complete holin / endolysin / i-spanin / o-spanin cassette, the
  position an endolysin occupies; the annotation most likely rests on exactly that synteny.

## Discovery mode: genomes with no annotated lysis gene

| genome | CDS | what the pipeline found |
|---|---|---|
| NC_001900.1 (D29) | 79 | holin D29p08 **P=0.9998** PF16081; endolysin D29p07 **P=0.9902** PF31067 |
| NC_009993.1 (Giles) | 79 | holin gp33 **P=0.9999** PF23809; endolysin gp31 **P=0.9777** PF01510+PF01471+PF01551; endolysin gp20 P=0.678 PF06737 |
| NC_055832.1 (DAC15) | 120 | endolysin gp039 P=0.0059 **PF01832** (model miss, domain rescue) |
| NC_091965.1 (Rudgehvirus, crAss-like) | 84 | nothing |
| NC_001609 (P4) | 14 | nothing — correct: P4 is a satellite and uses P2's lysis genes |
| NC_001978.1 (phi-C31) | 55 | nothing |

D29 and Giles are the pipeline working as intended: unannotated genomes where model and domain evidence agree at
>0.97 on both a holin and an endolysin. P4 finding nothing is a correct negative.

## Verdict

**Has the pipeline improved?** Component by component:

- **Holin — yes, and it is the strong part.** +6 points top-1 from the HMMs with zero regressions on the panel, and
  on crAss-like genomes the model finds holins that no domain method can see (0 of 6 had a domain hit). Serwaa's
  holin at 0.9999, rank 1. This component is publishable as-is.
- **Spanin — improved by the family expansion, not by the HMMs.** The i-spanin class addition is validated on
  Serwaa (both subunits in the top 2, o-spanin via the newly added PF28595), but domain-first ranking costs 3
  points of top-1 on the panel. Worth considering `--rank-by model` for spanins specifically.
- **Endolysin — still the weak component, and now failing two ways.** DAC15 showed a coverage gap the HMM could
  rescue; Serwaa shows a model failure at 50% family identity that the HMM cannot rescue. Together they are the
  strongest case yet for the per-fold redesign: separate models per catalytic class (GH24/GH25/GH73/GH108, SLT,
  amidase, endopeptidase, CWH), with the HMM scan as the gate rather than a tiebreak.

**Is the HMM integration worth keeping?** Yes, but for a narrower reason than "it raises the numbers". It raises
them only slightly, and slightly lowers spanin. Its real value is as a **safety net on out-of-distribution
genomes**: two documented saves (DAC15 gp039 from rank 25 to 1; crAss-like `M1M53_gp083` from below threshold to a
confirmed call) in cases the aggregate statistics cannot see, because such genes are exactly the ones with no
annotation to grade against.
