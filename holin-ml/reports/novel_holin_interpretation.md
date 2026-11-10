# Interpretation of 10 ML-flagged "novel holin" candidates

**Preamble.** These ten proteins are machine-learning predictions, not discoveries. Each scored 0.93-0.997 as holin-like, has no measurable homology to the 5,055 known holins (max identity <0.30), and sits within 3 genes of an annotated endolysin or spanin. The checks below (hydropathy, C-terminal charge, local gene order from the local GenBank records in `data/raw/pool/`) are supporting evidence only. None of this confirms holin function. The aim is a prioritized shortlist for experimental testing (e.g. lysis-timing or membrane-permeabilization assays), not a claim that any protein is a holin.

**Method notes.** Kyte-Doolittle hydropathy, window 19. The strict criterion (smoothed hydropathy >1.6 for at least 15 consecutive residues) gave **0 TM helices for all ten**. That is too harsh for proteins of 45-140 aa, so the table also reports the best single 19-residue window at or above 1.6 as "1 borderline hydrophobic segment". This is a crude predictor, and a dedicated tool (TMHMM, DeepTMHMM) should be run before any decision. C-term charge is K/R minus D/E over the last 20 residues. Context comes from the full GenBank records for all ten accessions, matched to the candidate by exact translation. The numbers in the context column are gene offsets (0 is the candidate).

| Accession | Current annotation | Len | Score | Predicted TM (strict / borderline) | C-term charge (last 20) | Lysis-cassette context (from .gb) | Verdict |
|---|---|---|---|---|---|---|---|
| NC_023594.2 | hypothetical protein | 63 | 0.989 | 0 / 1 (res ~4-22, N-term) | -2 | Same (minus) strand. Candidate sits directly upstream in transcription of an endolysin (gene +1 in coding order) and a second endolysin entry is 3 genes away. **No holin annotated in the genome.** Order is candidate then endolysin, as in a canonical cassette. | plausible novel holin (weak-moderate) |
| NC_005178.1 | hypothetical protein (orf23) | 62 | 0.962 | 0 / 1 (res ~40-62, C-terminal) | +2 | Plus strand: endolysin (-2), Rz-like spanin (-1), candidate (0). **No holin annotated.** The candidate comes after the spanin, not before the endolysin, which is atypical. A 148-aa hypothetical at -3 could also be the holin. | uncertain (best-supported by context, atypical order) |
| NC_003390.2 | hypothetical protein | 87 | 0.973 | 0 / 0 at window 19 (max 1.42); weak N-term peak at window 17 | 0 | Plus strand, endolysin immediately upstream (-1). No holin annotated. Followed by terminase small subunit at +2. | uncertain (weak hydrophobicity, neutral tail) |
| NC_015584.1 | hypothetical protein (gene 31) | 140 | 0.976 | 0 / 1 (res ~18-36, strongest peak, 2.27) | -1 | Two endolysin entries (-4, -3), then an **annotated holin at -2**, then a 84-aa hypothetical, then the candidate. Same strand. | uncertain (membrane-like, but a holin is already annotated nearby) |
| NC_011398.1 | hemolysin | 76 | 0.935 | 0 / 1 (res ~54-76, C-terminal) | +1 | Plus strand. **Annotated holin directly downstream (+1)**, endolysin at +2. The candidate is the gene immediately before the holin. | uncertain (could be a holin-associated accessory protein; "hemolysin" label unsupported) |
| NC_014459.2 | hypothetical protein (gene 33) | 113 | 0.997 | 0 / 1 (res ~11-29, N-term) | -4 | Endolysin at -3, helicase -2, **annotated holin at -1**, candidate directly after it. Same strand. | uncertain, leans no (negative tail, a holin already annotated) |
| NC_013694.1 | hypothetical protein (gene 7) | 45 | 0.930 | 0 / 0 (max window-19 1.37, only weak) | -2 | Candidate precedes the endolysin (+1), and an **annotated holin follows at +2**. Neighbouring genes are tail genes and terminase. | likely not a holin (no TM by criterion, negative tail, holin annotated) |
| NC_027627.1 | minor tail protein | 87 | 0.992 | 0 / 1 (res ~8-26) | -3 | Inside the tail module: tape measure, minor tail x2, lectin, **candidate**, collagen-like minor tail, then endolysin (+2) and **annotated holin (+3)**. | likely not a holin (collapsed, see below) |
| NC_027628.1 | minor tail protein | 89 | 0.984 | 0 / 1 (res ~8-26) | -4 | Identical layout to NC_027627.1 (holin at +3). | likely not a holin (collapsed) |
| NC_027629.1 | minor tail protein | 87 | 0.981 | 0 / 1 (res ~8-26) | -4 | Identical layout to NC_027627.1 (holin at +3). | likely not a holin (collapsed) |

Lysis-neighbour presence was confirmed from the genome records in all ten cases. Whether a cassette is intact is a separate question, and for seven of the ten an annotated holin already exists nearby, which cuts against the candidate being the holin.

## Most promising leads
1. **NC_023594.2 (63 aa, 0.989).** It is the only candidate with a clear N-terminal hydrophobic segment, the correct orientation upstream of an endolysin on the same strand, and no competing holin annotation. The tail is mildly acidic (-2), which weakens the call, and it has one hydrophobic segment, so topology would have to be class III-like (one TM) or the assignment is wrong.
2. **NC_005178.1 orf23 (62 aa, 0.962).** It is small, ends in a hydrophobic segment, has a net positive tail (+2), and the genome has an endolysin and Rz-like spanin but no annotated holin. The gene order (after the spanin) is unusual, so check the 148-aa neighbour at -3 as an alternative holin.
3. **NC_003390.2 (87 aa, 0.973)** is a weaker third. It sits directly after an endolysin with no annotated holin, but its hydrophobicity is marginal and its tail is neutral.

NC_015584.1 (140 aa, strongest hydrophobic peak) and NC_011398.1 are worth a look only as possible holin-associated proteins (e.g. antiholin or accessory), since each has a separate annotated holin beside it.

## Probably not holins
- **NC_013694.1:** 45 aa, no TM by the strict test and only a weak window peak, negative tail, and an annotated holin two genes after the endolysin.
- **NC_027627.1 / NC_027628.1 / NC_027629.1:** annotated tail proteins in a tail-gene block, with a negative tail and an annotated holin 3 genes downstream (see note).
- **NC_014459.2:** negative tail (-4) and an annotated holin directly upstream. It is not excluded as an accessory membrane protein, but holin is not the best explanation.

## Note: the three "minor tail protein" hits are one finding
NC_027627.1, NC_027628.1 and NC_027629.1 have the same start (MSWFTPALVA), the same C-terminal motif (~PxHLPDxPEFLKDTV(N/D)GGGE), near-identical lengths (87/89/87) and identical neighbourhoods (tape measure, minor tails, lectin, this ORF, collagen-like tail, endolysin, holin). They are sibling genomes carrying one protein, so they count as a single lead, not three. That protein sits in the tail module and is annotated as a tail protein, with a hydrophobic N-terminal stretch more consistent with a tail/baseplate component than a holin. The "strong candidate" status comes only from its proximity to the endolysin. This is a score artefact from lysis-region adjacency, not independent support.

## Caveats
- The hydropathy screen is crude. Class I-III holins and some pinholins have weak or atypical profiles, and neither the strict nor the loose criterion substitutes for TMHMM/DeepTMHMM and membrane-topology reporter assays.
- Proximity to an endolysin is expected for any gene in a lysis or late region and is weak evidence. Seven of ten candidates have a separately annotated holin nearby, so the ML model may be recognizing holin-like neighbours rather than new holins.
- No homology search against non-holin databases, structure prediction, or functional test was done. Nothing here is a confirmed or known holin.
