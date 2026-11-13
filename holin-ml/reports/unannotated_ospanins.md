# Unannotated o-spanins in RefSeq phage genomes

**Question.** Standard gene finders do not call genes embedded in another gene's reading frame, and embedded
o-spanins are exactly that. How many RefSeq phage genomes carry an o-spanin their annotation leaves out?

**Method** (`scripts/51_survey_unannotated_ospanins.py`). All 5,247 RefSeq complete tailed-phage genomes
(`scripts/49a`), minus evaluation genomes and duplicates: 5,113 scanned. RefSeq's own annotated genes are the hosts
for the nested lipoprotein-ORF finder (`scripts/genecall.py`), so every ORF found is, by construction, absent from the
annotation. Each candidate is scored by the shipped spanin model and checked for lysis-cassette context (a catalytic
endolysin domain within 5 genes). Tier A = spanin model >= 0.5 and in a cassette.

## Result

- **728** unannotated nested lipoprotein ORFs in **670** genomes; **303 tier A in 301 genomes** (B 137, C 288).
- In **238 of the 303** tier-A cases RefSeq itself annotates the HOST gene as an i-spanin / Rz / "Rz-like spanin";
  it is the embedded partner that is missing. Only **2 of the 303** genomes annotate an o-spanin anywhere.
- Mostly enterobacterial phages (Salmonella 74, Escherichia 46, Klebsiella 43, Enterobacteria 17), then Pseudomonas
  17, Ralstonia 13, Yersinia 12, Pectobacterium 8.

Examples (all tier A, host annotated by RefSeq as "Rz-like spanin"):

| genome | phage | ORF | similar to |
|---|---|---|---|
| NC_047895.1 | Escherichia phage EG1 | 37074..37274 +, 66 aa, P = 0.994 | T7 gp18.7 (MKYRLSIRKTLPRWKGALIGLFLICVATISGCA...) |
| NC_009514.1 | Enterobacteria phage cdtI | 46123..46308 +, 61 aa, P = 0.993 | lambda Rz1 (MRKLKMKLCALMLPLVVSACGSMP...) |
| NC_048703.1 | Xanthomonas phage RiverRider | 64448..64723 -, 91 aa, P = 0.993 | lipobox o-spanin |

## How much to trust a tier-A call

The same tiers applied to CPT genomes from bare DNA, with leave-one-genome-out spanin scores (the model never saw
the genome's spanin family, or never saw anything >= 95% identical to it), against CPT's curated spanins:

| CPT nested ORFs | n | curated spanin | precision |
|---|---|---|---|
| tier A, unseen family | 8 | 7 | 0.88 |
| tier A, known family | 16 | 15 | 0.94 |
| tier B, unseen / known | 6 / 7 | 3 / 4 | 0.50 / 0.57 |
| tier C, unseen / known | 31 / 22 | 14 / 5 | 0.45 / 0.23 |

The RefSeq candidates are mostly in well-studied enterobacterial families, so the known-family figure is the
closer guide: on the order of **270-285 of the 303 tier-A candidates should be real o-spanins** missing from RefSeq.
The calibration sets are small (8 and 16), so treat that as a rough range.

## What this is and is not

- It is an **annotation gap, quantified**: that embedded Rz1-type genes are often left unannotated has been noted
  before in the spanin literature; this measures it across current RefSeq and gives the list.
- It is **not a new mechanism**. The genes are recognisable o-spanins; what is new is where they are and that the
  records lack them.
- Every call is a prediction. The list (`unannotated_ospanins_tierA.tsv`: genome, coordinates, strand, host locus,
  scores, sequence) is ready for curation or submission as annotation updates.
