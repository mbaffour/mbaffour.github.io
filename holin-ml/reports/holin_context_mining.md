# Mining new holin families from genomic context

**Question.** The holin model's weak point is holins from families it has never seen (ranked first in their genome
54% of the time, top five 85%). Eight model changes did not move that (`holin_generalisation.md`); the remaining lever
is training diversity. Can the lysis genes we already detect reliably find holins from NEW families, and do those
make the model generalise better?

## The mining rule (sequence only; `scripts/49_mine_context_holins.py`)

- **anchor:** a protein with a catalytic endolysin Pfam domain, at most 500 aa (larger ones are tail spikes)
- **candidate:** the gene immediately upstream of the anchor in its direction of transcription, same strand,
  50-250 aa, 1-3 TM segments, no catalytic domain, no lipobox in the first 35 residues (that would be an o-spanin)
- **new family:** < 30% identity (coverage >= 0.5, SW score >= 80, the benchmark's own homology rule) to every
  training holin, endolysin and spanin

The holin model is never used, so the rule cannot simply re-find what the model already knows. Annotations are kept
for provenance only.

**Precision measured first, on the 78 CPT genomes with a curated holin:** the rule picked 41 proteins, 31 of them
the curated holin (76%); 31/38 (82%) after the 500-aa anchor cap. A looser rule (any 1-3 TM gene within 2-4 genes)
was only 25-40% precise, because in about half the CPT genomes the holin is not next to the endolysin.

## What it found

5,111 genomes mined (all 5,247 RefSeq complete tailed-phage genomes, `scripts/49a`, plus the 300-genome pool, minus
the 141 that are evaluation genomes or duplicates). 1,272 distinct picks; **1,170 (92%) belong to known training
holin families**, which is independent evidence that the rule picks holins. **77 are from families absent from
training (37 families)**; 59 of them annotated "hypothetical protein", 5 "holin".

## Does adding them help? Paired against the shipped holin model

Decision rule set before the runs: adopt only if novel-family top-1 or top-5 improves with no significant loss on
either, and the known-family CI is not wholly below 0. Two variants, declared in advance as the only two.

| CPT, 78 genomes | shipped | v1: 77 new-family picks | v2: anchor also called by the endolysin model (59 picks) |
|---|---|---|---|
| novel family, ranked 1st | 0.538 | 0.487 (-0.051 [-0.115, 0.000]) | 0.526 (-0.013 [-0.052, +0.026]) |
| novel family, top 5 | 0.846 | 0.846 (0.000) | 0.846 (0.000) |
| known family, ranked 1st | 0.705 | 0.679 (-0.026 [-0.064, 0.000]) | **0.641 (-0.064 [-0.128, -0.013])** |
| known family, top 5 | 0.936 | 0.949 (+0.013) | 0.936 (0.000) |
| 8 proven holins, novel family, ranked 1st | 7/8 | 6/8 | 7/8 |

T4-type holins (the clearest gap), novel family, rank in genome:

| | Marfa | EI | pKp20 | Hypnos | Nesoi | Persephone |
|---|---|---|---|---|---|---|
| shipped | 67 | 39 | 36 | 10 | 17 | 15 |
| v1 | **28** | **9** | **8** | **4** | **7** | **3** |
| v2 | 42 | 18 | 19 | 9 | 10 | 9 |

**Neither variant is adopted.** v1 does not improve the headline figures and leans negative on top-1; v2 is
significantly worse on known families. The shipped holin model is unchanged.

## What this says

- **The mined set carries real signal for one hard group.** v1 moved all six T4-type holins up, three of them from
  rank 36-39 to 8-9 -- the first change in nine that helps them. Under the novel-family protocol any mined protein
  >= 30% identical to the scored holin is removed, so this is not the test holin leaking back in.
- **About one pick in five is not a holin, and that noise costs about as much as the new families give.** The gain
  on T4-type holins is paid for elsewhere (v1: 12 genomes better, 16 worse).
- **With today's public data, unseen-family holin detection looks close to its ceiling** for this model family:
  nine attempts, none better overall. What would move it is cleaner new-family positives: experimental confirmation
  of a few of the 37 mined families, which would then go in as clean labels. The list is in
  `data/processed/holins_context_mined.json` (genome, protein, anchor domain, identities), ready for that.
