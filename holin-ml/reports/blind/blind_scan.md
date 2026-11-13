# Blind scan: lysis genes found from DNA alone, then checked against the annotations

**Design.** 152 tailed-phage genomes published from June 2026, never used anywhere in this project (26 host genera,
at most 15 per genus; `scripts/52a`). The shipped predictor ran on the **DNA only**: genes called from scratch,
nested o-spanin ORFs added, each class scored, one call per class (`scripts/52b`). Those calls were **committed
(6057406) before any annotation was opened**. Only then were they compared with the genomes' own GenBank annotations,
under rules fixed in advance (`scripts/52c`): which product names count as holin / endolysin / spanin, how a de novo
gene is matched to an annotated one, and what counts as agreement.

22,216 proteins called; confident calls: 124 holins, 149 endolysins, 122 spanins; all three confident in 98 genomes.

## Does the scan find the annotated lysis genes?

| | genomes whose annotation has one | the one call IS the annotated gene | annotated gene in the top 5 |
|---|---|---|---|
| holin | 104 | **0.885** [0.817, 0.942] | **0.962** [0.923, 0.990] |
| endolysin | 130 | **0.838** [0.777, 0.900] | **0.969** [0.938, 0.992] |
| spanin | 92 | **0.761** [0.674, 0.848] | **0.957** [0.913, 0.989] |

95% genome-bootstrap intervals. Spanin agreement is lower partly by construction: a spanin is a pair, the scan
names one gene, and the partner is often the one the annotation names, or is a nested ORF the annotation lacks.

**How new were these genes?** Recent genomes still mostly carry familiar lysis genes. Split by each annotated gene's
identity to the training data:

| | near-copy of training (>= 95%) | known family (30-95%) | new family (< 30%) |
|---|---|---|---|
| holin: call correct / in top 5 | 59/61 / 61/61 | **33/41 / 39/41** | 0/2 / 0/2 |
| endolysin | 69/72 / 72/72 | **37/52 / 50/52** | 3/6 / 4/6 |
| spanin | 58/76 / 73/76 | **12/16 / 15/16** | (none) |

The known-family column is the fair read for a typical new phage: the right gene is in the top five 95-96% of the
time and named outright 71-80% of the time. New families are too few here to measure (8 genes).

## Where scan and annotation disagree

**Confident calls on genes annotated with another function:** endolysin 19, holin 2, spanin 5.
- 12 of the 19 endolysin conflicts are virion-associated lytic enzymes: T4-type "baseplate hub subunit and tail
  lysozyme" (8) and T7-type internal virion proteins (4). They do cut peptidoglycan, but at infection, not lysis; this
  is the endolysin model's known blind spot. **Since fixed:** the cause was 51 virion proteins in the endolysin training positives; see `../endolysin_virion_fix.md` (on a second blind set the endolysin call is right in 92% of genomes, up from 86%). A few others (D-Ala-D-Ala carboxypeptidase, Peptidase M37, chitinase) are
  plausible endolysins under another name.

**Confident calls on genes the annotation calls hypothetical, or does not have at all, in genomes whose annotation has
no gene of that class** -- candidate additions, checked against sequence evidence the models do not use directly
(`candidate_additions.tsv`):

| | candidates | strong evidence | what "strong" means |
|---|---|---|---|
| holin | 29 | **22** | 1-3 TM segments and next to another lysis call |
| endolysin | 13 | **11** | next to another lysis call |
| spanin | 28 | **9** | next to another lysis call and a TM segment or lipobox |

The 22 holins are the clearest result: genomes annotated with no holin at all, where the scan finds a small membrane
protein beside the endolysin -- the textbook holin position. The weak spanin calls (19; 9 of them with no membrane
segment and nowhere near a lysis gene) are more likely errors than discoveries.

## Bottom line

From DNA alone, on genomes it had never seen, the predictor puts the annotated holin, endolysin and spanin in its top
five ~96% of the time and names it outright 76-89% of the time. Its main error is calling virion lysozymes as
endolysins. It also proposes ~40 well-supported lysis genes the annotations lack. Those are predictions, not
confirmations; annotation names are themselves imperfect, which is why the project's headline estimates come from
curated (CPT) and experimentally proven genes.
