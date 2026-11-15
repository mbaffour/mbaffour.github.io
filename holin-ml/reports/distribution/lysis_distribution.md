# How lysis genes are built and arranged across phage families

Data: the blind DNA-only calls for 1,061 genomes in nine groups (`../groups/groups_scan.md`, `../n4/n4_scan.md`),
re-derived protein sequences, and Pfam domains -- no annotation names (`scripts/54_lysis_distribution.py`; per-genome
table `lysis_by_genome.csv`; figures `scripts/54b`, all checked for overlapping text). Every value is a model call or
a sequence property, so it carries the predictor's error rates for that group (lowest agreement: T4-like endolysins
0.61, jumbo phages); read it as a map of what the predictor sees.

![toolkit](figures/1_toolkit_heatmap.png)

## Patterns that match known biology (a check that the calls are meaningful)

- **Endolysin chemistry is family-specific.** T5-like 87% peptidase (T5's endolysin is an L-alanoyl-D-glutamate
  peptidase); T7-like 33% amidase (T7 gp3.5 is an N-acetylmuramoyl-L-alanine amidase); Drexlerviridae 96%
  glycosidase; Herelleviridae (Gram-positive hosts) 60% amidase, the longest endolysins (median 341 aa) and the most
  cell-wall-binding domains (23%) -- the modular Gram-positive endolysin.
- **Spanins follow the host envelope and the phage family.** Herelleviridae: no confident spanin in 75% (Gram-positive
  hosts have no outer membrane). Drexlerviridae: 99% a single spanin gene, 97% with a lipobox -- the unimolecular
  spanin of phage T1, which belongs to this family. Lambdoid phages: 56% embedded (lambda Rz1 inside Rz). T4-like 89%
  and T5-like 63% overlapping pairs.
- **Cassettes are compact in small phages, scattered in T4.** Co-located in 82-85% of N4-like, lambdoid, P2-like and
  Drexlerviridae genomes; never in T4-like (0%; 74% dispersed), whose lysis genes are known to be spread around the
  genome. Order is strongly conserved: holin-endolysin-spanin in 97-99% of co-located lambdoid, P2-like and
  Drexlerviridae cassettes; spanin-holin-endolysin in 100% of T5-like ones.
- **Holin size.** T4-like and T5-like holins cluster at ~218 aa (the T4 t size: one membrane helix plus a large
  periplasmic domain); Drexlerviridae ~72 aa and T7-like ~69 aa (small holins); lambdoid ~108 aa.

## Patterns worth following up

- **N4-like phages:** two or more strong holin-like genes in 51% of genomes (the two-holin pattern), only 8% of their
  holins match any known Pfam holin family, and 32% of their endolysins carry no recognised catalytic domain -- the
  most novel lysis machinery of the groups scanned, while still detected confidently.
- **Jumbo phages:** only 7% of holins in a known Pfam family, 27% of endolysins without a recognised domain, cassettes
  rarely co-located (10%).
- **Herelleviridae:** 74% carry two or more strong holin-like genes.

## Caveats

- Membrane-segment counts are not used to classify holins: the hydropathy heuristic reads lambda S (3 TM) as 1 TM.
  The "SAR-like N terminus" column uses the same heuristic and is a lower bound.
- Spanin architecture uses confident spanin calls and the nearest strong partner; a missed partner shows as "single".
- Groups are samples (at most 15 genomes per host genus); counts are in the figures.

Figures: `figures/1_toolkit_heatmap.png`, `2_endolysin_classes.png`, `3_spanin_architecture.png`, `4_holins.png`,
`5_cassettes.png`.
