# A general holin signal: what moves it, what does not

**Goal (from the user):** a signal that detects holins of families the model has never seen. The measure is the
novel-family protocol: before a genome is scored, every training holin >= 30% identical to its curated holin (whole
homology clusters) is removed, and we ask where the curated holin ranks among all proteins of its genome. 78 CPT
genomes; the 8 experimentally proven holins as a held-out check. All comparisons are paired against the shipped holin
model (`scripts/45_rank_report.py --compare`).

Shipped holin model, novel family: ranked 1st **0.538**, top 5 **0.846**. Known family: 0.705 / 0.936.

## Seven variants, none better

| variant | ranked 1st, novel | top 5, novel | ranked 1st, known | top 5, known |
|---|---|---|---|---|
| family-balanced weights (each family equal) | +0.026 | -0.051 | -0.064 | 0.000 |
| milder weighting (1/sqrt family size) | 0.000 | -0.013 | -0.026 | +0.013 |
| biophysical features only (36) | -0.038 | **-0.090** (p=0.016) | -0.090 | -0.064 |
| biophysics + family weights | -0.077 | -0.077 (p=0.07) | 0.000 | **-0.077** (p=0.03) |
| biophysics + 27 membrane-topology descriptors | -0.090 | **-0.141** (p<0.001) | +0.051 | -0.064 |
| full model + topology | 0.000 | **-0.051** (p=0.03) | -0.038 | +0.013 |
| full model + topology + family weights | -0.013 | -0.038 | -0.013 | 0.000 |

Bold: 95% paired CI excluding zero. The experimental set (8 proven holins) agrees: no variant ranks more of them first
than the shipped model (7/8 novel).

T4-type holins (Marfa, pKp20, EI, Nesoi, Persephone, Hypnos), novel family, rank in genome: shipped 10-67; family
weighting made them WORSE (34-106), biophysics-only worse still (64-219).

## What this says about the signal

- **The general holin signal the model has lives in the protein-language-model embedding.** Every variant that drops
  or dilutes it does worse on unseen families; hand-built biophysics and topology, the features one might expect to
  capture "holin-ness" across families, generalise worse than the embedding, not better.
- **Reweighting the same families does not create diversity.** The 3,250 training holins sit in 99 families, the five
  largest holding 50%; equalising them did not help.
- **New data will not come from CPT.** 94% of CPT's curated holins share a family with the training holins (median
  best identity 0.82); only 5 are new families.
- **The honest current answer to "does it project to unseen holins?"** is: for a holin from a family it has never
  seen, the model ranks it first in its genome 54% of the time and in the top five 85% of the time (and context lifts
  the first figure to 62%). It projects, but imperfectly, and T4-type holins are the clearest gap.

## A stronger representation: ESM-2 150M (tested, rejected)

Since the embedding carries the transferable signal, the obvious lever was a bigger one: ESM-2 150M (640-d) in place of
35M (480-d), same recipe, same protocol (`scripts/40 --esm-model facebook/esm2_t30_150M_UR50D`,
`reports/cpt_holin_esm150.json`). Decision rule set before the run: adopt only if the novel-family figures improve
and the known-family CI is not wholly below zero.

| 78 CPT genomes | shipped (35M) | 150M | paired change, 95% CI |
|---|---|---|---|
| novel family, ranked 1st | 0.538 | 0.551 | +0.013 [-0.064, +0.090] |
| novel family, top 5 | 0.846 | 0.769 | **-0.077 [-0.141, -0.026]** (p=0.004) |
| known family, ranked 1st | 0.705 | 0.692 | -0.013 [-0.103, +0.064] |
| known family, top 5 | 0.936 | 0.885 | -0.051 [-0.115, 0.000] |

T4-type holins, novel family, rank in genome: shipped 10-67, 150M **103-184** (Marfa 67->103, EI 39->184, pKp20
36->169, Hypnos 10->151, Nesoi 17->146, Persephone 15->164).

**Rejected.** The larger embedding is significantly worse at placing unseen-family holins in the top five, and it loses
the T4-type holins almost entirely. A bigger general-purpose language model is not, by itself, a more general holin
signal; with ~3,000 training holins in 99 families the extra 160 dimensions mostly give the classifier more room to
fit the families it has. (The 8-holin experimental check was not completed: with 8 genomes it cannot overturn a
significant 78-genome result.)

## Where that leaves the holin signal

Eight variants tried; the shipped 35M model remains best. What is left that could plausibly move unseen-family
performance is new training diversity, not new features: holins from families absent from the training set
(e.g. experimentally characterised holins from the literature outside CPT, or class II/III/T4-type holins mined by
topology and then confirmed), added and re-tested under the same protocol.
