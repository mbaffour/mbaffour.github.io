# How certain are the family-level lysis patterns?

`scripts/54c_distribution_uncertainty.py`; full table `uncertainty.csv` (108 family x feature rows); figure
`figures/8_key_features_ci.png`.

**Effective sample sizes are small.** Related phages are not independent. Grouping each family's genomes by shared gene
content (scripts/58): N4-like 255 genomes -> 42 groups (one group of 59 genomes at >= 95% ANI), lambdoid 120 -> 31,
T7-like 120 -> 52, P2-like 111 -> 31, Drexlerviridae 101 -> 9, T5-like 106 -> 14, Herelleviridae 88 -> 25,
T4-like 100 -> 17, jumbo 60 -> 39. Intervals below resample those groups.

**Patterns that are solid** (narrow intervals, and the family's calls for that gene match annotations in >= 80% of
genomes):
- Drexlerviridae: unimolecular spanins 95% [91, 100]; SAR endolysins 94% [90, 99]; class III holins 99%.
- Herelleviridae (Gram-positive hosts): no confident spanin 75% [61, 87]; class II holins 91%; amidase endolysins 60% [30, 82].
- T4-like: lysis genes never co-located (0%); two-component spanins 83% [57, 94]; class III holins 83%.
- Unimolecular spanins essentially absent outside Drexlerviridae (T7-like 9% [2, 19]; all others 0%).
- N4-like: no SAR endolysins by consensus (0%).

**Patterns that are uncertain** (wide intervals; driven by a few large groups of related genomes):
- Holin class mix in N4-like (class I 40% [8, 72]) and lambdoid phages (class I 57% [14, 74]).
- T5-like endolysins as peptidases: 87% but [33, 96] -- 106 genomes are only 14 groups, one of 69.
- Holin copy number (>= 2 strong holin genes) in most families.
Statements about these should be qualitative ("common in", "found in") and carry the interval.

**Weak calls.** Where a family's calls for a gene matched the annotation in < 80% of genomes, the feature rests on
uncertain calls (open dots in the figure): N4-like and jumbo holins, T4-like and jumbo endolysins, jumbo spanins.

**Group definitions.**
- "Lambdoid" is not a taxonomic family. The set is 48 P22-like (Lederbergvirus), 42 records without an assigned genus
  matched because their own description says "lambdoid" or "lambda-like" (including 12 Vibrio phages of doubtful
  lambdoid membership), 5 Lambdavirus and single genera. It should be reported as "lambdoid / P22-like (mixed)".
- "Jumbo" is a size class (> 200 kb), not a family; its genomes span 39 gene-content groups.
- Records over 800 kb were removed (bacterial chromosomes filed under phage taxa); family assignments otherwise follow
  NCBI taxonomy as deposited.
