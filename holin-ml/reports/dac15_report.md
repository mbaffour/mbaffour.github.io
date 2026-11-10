# Lysis genes in Bacteroides phage DAC15 (NC_055832.1)

**Genome:** 99,494 bp, linear. *Crassvirales; Steigviridae; Asinivirinae; Wulfhauvirus* (crAss-like); host *Bacteroides*.
Of its 120 annotated CDS, almost all are "hypothetical protein".

**Out-of-sample status:** no DAC15 protein is in any training set (holin, endolysin, or spanin). No crAss-like phage
contributed lysis genes to training, so DAC15 is **out of distribution at the genome and the family level**. Read
everything below as candidates, not verdicts.

**Reproduce:**
```
python3 scripts/32_predict_lysis.py --acc NC_055832.1 --out reports/dac15_lysis.tsv
python3 scripts/33_verify_calls.py --tsv reports/dac15_lysis.tsv --genbank data/raw/genomes/NC_055832.1.gb --top 3
```
`scripts/33` checks each candidate with Pfam lysis-domain HMMs (pyhmmer, E < 1e-3), Phobius topology, a training-set
lookup and ±3-gene context. It also scans the **whole proteome** for lysis domains, including proteins over the
predictor's 2,000-aa cap, to catch genes the model missed ("domain rescue").

## Result

| role | gene | position | size | model P | independent evidence | confidence |
|---|---|---|---|---|---|---|
| **endolysin** | **gp039** | 86,545 (−) | 157 aa | 0.006 (missed) | **Glucosaminidase PF01832, aa 53–156, E = 8.7e-17**; Phobius signal peptide, cleaved at 27/28 → secreted lysin | **best supported** |
| holin | gp095 | 25,829 (+) | 133 aa | 0.966 | Phobius: 1 TM (out 6–25 in); no holin Pfam; max identity to known holins 0.32 | plausible, unconfirmed |
| holin | gp012 | 97,466 (−) | 31 aa | 0.728 | 1 TM, but 31 aa is too short for a holin | likely false positive |
| endolysin | gp080 | 41,176 (+) | 832 aa | 0.839 | no lysis domain, no TM; sits among virion structural proteins | likely false positive / virion protein |
| spanin | gp004 = gp008 | 1,337 (−) / 98,989 (−) | 50 aa | 0.865 | identical copies in the terminal repeat; Phobius signal peptide (cleaved at 22) but **no lipobox** | weak |

**No lysis cassette.** These genes are scattered across the genome, not clustered. gp039 sits among nucleotide and
NAD-salvage genes (ribose-phosphate pyrophosphokinase gp038, nicotinamide phosphoribosyltransferase gp036). gp095
sits in a block of uncharacterized genes.

## How to read this

- **The strongest call came from verification, not from the model.** gp039 is the only DAC15 protein with any lysis
  domain. The endolysin model scored it 0.006, because the Glucosaminidase family (PF01832) is missing from the
  endolysin training families. This is a known coverage gap, not a random error.
- **Caveat on gp039:** Glucosaminidase domains also occur in non-lytic proteins such as FlgJ and bacterial autolysins.
  On its own, a domain hit can't separate an exit lysin from a virion or entry lysin. Two things argue for lysis here:
  the cleavable signal peptide (a secreted endolysin, a known strategy that works with a pinhole-type holin) and its
  position outside the structural module.
- **Holin:** gp095 has the size and single-TM topology of a class II/III holin, and the model is confident. But there
  is no family or homology support, and it isn't next to gp039.
- **Spanin:** spanins are expected in Gram-negative hosts like *Bacteroides*, but the gp004/gp008 call lacks the
  o-spanin lipobox and an i-spanin partner. Treat it as unresolved. crAss-like phages may use an unrecognized
  spanin-equivalent.

## What would settle it
1. Experimental tests:
   - express gp039 and run a zymogram or turbidity assay on *Bacteroides* or *E. coli* peptidoglycan;
   - co-express gp095 with gp039 in *E. coli* to test holin-dependent lysis.
2. Model fix: retrain the endolysin model with the missing catalytic families (PF01832 Glucosaminidase, and also SLT
   PF01464, M23 PF01551, NlpC PF00877, GH25 PF01183, M15 PF02557/PF08291/PF13539, GH108 PF05838). Then re-score
   DAC15. Until then, run `scripts/33` with the domain rescue on any out-of-distribution genome.
