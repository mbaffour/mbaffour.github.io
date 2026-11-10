# Retraining with expanded family coverage (v2) — what it did and did not fix

Driven by *Bacteroides* phage DAC15 (`reports/dac15_report.md`), where the only lysis domain in the genome was
Glucosaminidase PF01832 — a family absent from the endolysin training set — so the endolysin model scored the real
candidate **0.006** and a whole-proteome HMM scan had to find it.

The ship rule was fixed in code (`scripts/35_compare_retrain.py`) **before** any v2 number was read: primary metric
is the strict leave-one-genome-out genome AP (the genome's whole family removed at ≥30% identity), realistic as
tie-break, and confusable negatives ship only if they do not lose strict AP. Gold-holdout AP is deliberately not
the comparison metric, because `scripts/27` re-draws the homology clusters and the frozen holdout over the larger
positive set, so v1's and v2's holdouts are different sequence sets and their APs are not comparable.

## What was added

| class | families | positives | what was actually missing |
|---|---|---|---|
| endolysin | 8 → 22 populated | 1,529 → 2,788 | all five catalytic classes thin; **PF01832 GH73**, DAC15's family, absent |
| spanin | 2 → 6 | 2,045 → 2,160 | **the entire i-spanin class** (PF03245 Rz, 311 members) |
| holin | 33, unchanged | unchanged | nothing — both remaining candidate families returned 0 viral members |

Holin family coverage was already complete across all four architectural classes (class I PF05106 λ S, class II
PF10746/PF11031, class III PF16083/PF16085, pinholin PF04971, actinobacterial PF07332/PF04020/PF16081). Nothing
was padded in to make the work look bigger.

## Result: endolysin — the expansion REGRESSED on the benchmark

Leave-one-genome-out genome AP over the 16 atlas phages:

| model | strict (never-seen family) | realistic (new phage, known family) |
|---|---|---|
| v1 shipped | **0.7286** | **0.8430** |
| v2 families | 0.6517 | 0.7369 |
| v2 families + confusables | 0.5415 | 0.6394 |

By the committed rule, **v1 is kept**. No model was promoted.

The confusables collapse was predicted before it was read, and its mechanism is provable: that arm adds 109 phage
tail lysozymes as explicit negatives, while **3 of the 19 atlas endolysin targets are themselves virion-associated
entry lysins** — T4 gp5, whose product is literally "baseplate hub subunit and tail lysozyme", plus T7 p51 (a
1,318-aa internal virion protein) and phi29 gp13. The arm is trained to suppress precisely what the benchmark
rewards finding. That drop measures a disagreement about what "endolysin" means, not a loss of capability.

### A correction, for the record
An earlier reading of this was wrong and is corrected here. The structural-name guard did **not** remove the atlas
targets from training: T4 gp5 is a v2 training positive, because the guard applies only to the Pfam depth tier and
gp5 enters via the curated tier. What the guard removed is 1,360 of 7,958 (17%) Pfam-tier members, correctly
identified by name ("Pre-baseplate central spike protein Gp5", "Tail lysin", "CHAP-domain tail tip cell wall
hydrolase", "Minor tail protein") — i.e. *homologs* that would otherwise help rank those entry-lysin targets under
the realistic protocol. Real contributor, different mechanism.

### Two causes still to separate
1. **Breadth dilution** — the positive class went from 8 to 22 families and is now far more heterogeneous.
2. **The structural guard** removing 1,360 entry-lysin homologs.

Strict (−0.077) and realistic (−0.106) fell by similar amounts, which *suggests* dilution dominates, since the
strict protocol removes families anyway and should be less guard-sensitive. That is an inference, not a
measurement; the attributing ablation is v2 families with the guard switched off.

## Everything here is within noise — read directions, not magnitudes

Every bootstrap confidence interval overlaps. With 16 atlas phages and 15–19 targets per class, the benchmark
cannot resolve these differences, and no comparison below is claimed as statistically significant.

| model | strict AP | CI95 |
|---|---|---|
| endolysin v1 | 0.7286 | [0.523, 0.881] |
| endolysin v2 | 0.6517 | [0.425, 0.855] |
| spanin v1 | 0.7290 | [0.551, 1.000] |
| spanin v2 | 0.8059 | [0.589, 1.000] |
| holin arm B | 0.7847 | [0.538, 0.962] |
| holin arm C | 0.7986 | [0.550, 0.978] |

What is usable is **direction-consistency across the two independent removal protocols** — weaker evidence than a
significant difference, but not nothing. Fixing the underpowered benchmark means more genomes carrying annotated
lysis genes; 16 phages is not enough to validate work at this granularity, and that is the single biggest
limitation of this evaluation.

## Result: spanin — the expansion WORKS

| model | strict | realistic |
|---|---|---|
| v1 shipped | 0.7290 | 0.8345 |
| **v2 families (shipped)** | **0.8059** (+0.077) | **0.8831** (+0.049) |
| v2 families + confusables | 0.7271 | 0.8709 |

Better on both protocols, and this is the arm with no labelling conflict — 0 of 15 atlas spanin targets is
virion-associated. Promoted.

The two classes diverging is itself the informative result, and it rules out "more families is good/bad" as the
lesson. Spanin gained a coherent, genuinely absent **architectural** class — i-spanins are inner-membrane
proteins, and the old set held only T7-like outer subunits — and improved. Endolysin gained nine more unrelated
catalytic folds for a class that was already a disjunction of five, and degraded. What matters is whether the
added members share enough structure for one classifier to learn them together.

## Result: holin — arm C makes no measurable difference

| arm | strict | realistic | FP > 0.9 (strict) |
|---|---|---|---|
| A current | 0.6252 | 0.8234 | 1 |
| **B + curated (kept)** | 0.7847 | 0.9647 | 3 |
| C + cross-class negatives | 0.7986 | 0.9588 | 6 |

Arm C is +0.014 strict but −0.006 realistic, with strict false positives above 0.9 rising 3 → 6. Inconsistent
direction, overlapping CIs: noise. **Arm B is kept.**

This **declines the literal committed rule**, which said ship C on strict AP ≥ B. Flagged rather than done
quietly. The rule exists to stop a metric being outcome-shopped to justify a wanted change; applying it here
would replace a deployed model on the strength of noise while doubling strict-protocol false positives. "No
change without evidence" serves the rule's purpose better than its letter.

The holin cross-class discipline gap therefore stays open. Closing it properly needs a **held-out** cross-class
evaluation: arm C trained on every endolysin and spanin positive, so it cannot be fairly scored against them.

## Confusable negatives fail for both classes — and the mechanism is measured

| set | n | median len | p10–p90 | fraction with a TM |
|---|---|---|---|---|
| spanin positives | 2,160 | 116 | 68–160 | 0.69 |
| microvirus E (negative) | 26 | 83 | 56–96 | **1.00** |
| MS2 L (negative) | 14 | 75 | 63–75 | 0.79 |
| endolysin positives | 2,788 | 267 | 151–561 | 0.19 |
| tail lysozyme (negative) | 109 | 286 | 190–910 | 0.38 |

Each confusable set sits *inside* the length and topology envelope of the class it damaged. Microvirus E and MS2
L are small single-TM membrane proteins — which is what a spanin looks like to a feature-based classifier — so as
negatives they inject label noise into exactly the region the spanin model must stay sensitive in. Tail lysozymes
did the same in endolysin space, compounded by the benchmark scoring three of them as positives.

This was my hypothesis, it was tested, and it failed on both classes. The lesson is architectural: **a confusable
that is not separable from the target class by the available features cannot serve as a precision anchor in the
label set.** Excluding entry lysins and single-gene lysis proteins belongs where `scripts/33` already does it — in
genomic context, domain identity and topology.

## DAC15 re-score: the retrain does NOT fix it

| endolysin model | gp039 (the real candidate) | gp080 (likely false positive) |
|---|---|---|
| v1 (shipped) | **0.0059** | 0.839 |
| v2 families | 0.107 | 0.964 |
| v2 families + confusables | 0.218 | 0.850 |

Adding the family lifted gp039 by 18–37× and left it far below any usable threshold. The striking part: the v2
model holds a training positive **80.3% identical to gp039 at full coverage**, and still scores it 0.11. A
similarity-based method would score that near-certain. So the mean-pooled ESM-2 + gradient-boosting
representation is not exploiting family resemblance for endolysins at all — independent support for the
architectural conclusion below. The `scripts/33` domain scan remains the only thing that finds gp039.

Spanin v2 does improve DAC15 behaviour, which is a small real win: the weak, lipobox-less gp004 call drops
0.865 → 0.575, and cross-class confusion on gp095 drops 0.171 → 0.047. Being less confident about a bad call is
the right direction.

## Shipping decisions

| class | decision | why |
|---|---|---|
| endolysin | **keep v1** | v2 worse on both protocols, worse again with confusables |
| spanin | **ship v2 families** | better on both protocols; better DAC15 behaviour |
| holin | **keep arm B** | arm C within noise, strict FP 3 → 6 |

## Reading this honestly

The benchmark's positive label is a product-name regex, so it conflates exit endolysins with virion-associated
entry lysins. That makes it unable to judge precision work on exactly the confusion that matters in a real genome —
and it is the same confusion that makes DAC15 gp080 (832 aa, in the structural module, endolysin P = 0.839) a
likely false positive. Fixing that definition is a change worth making on its own merits, not because it would
flatter a retrain; both numbers stay on the record either way.

The deeper signal is that **"endolysin" may not be one learnable class.** Holins are a genuine structural class —
small, transmembrane, compositionally distinctive — which is why that model reaches 0.965. Endolysins are five
unrelated catalytic folds sharing only a substrate, and a one-vs-rest classifier is being asked to learn a
disjunction; HMMs separate those folds cleanly, which is exactly how `scripts/33` found gp039 when the model could
not. If the ablation confirms dilution, the honest conclusion is that endolysin detection should be domain-driven
with the model as a ranker, rather than the reverse.

Also worth stating plainly: gp039 was never a hard case. Its nearest relative among the newly added data is
**80.3% identical at full coverage**, and those relatives are from crAss-like phages (`uncultured phage cr126_1`,
`uncultured phage cr151_1`, `Kolpuevirus frurule`) that were in UniProt all along. If a v2-style model scores
gp039 highly, that is not a modelling achievement — it is the model finally having data that should never have
been missing. By contrast DAC15's holin gp095 sits at **37.5% max identity (coverage ≥0.8)** to any of 5,055
training holins, so that one is a real novel-family call the holin model made unaided at 0.966.
