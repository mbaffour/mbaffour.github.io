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

## Result: spanin

(pending)

## Result: holin — arm C, cross-class negatives

(pending)

## DAC15 blind re-score

(pending)

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
