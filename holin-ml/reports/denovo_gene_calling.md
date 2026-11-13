# Bare DNA: finding the lysis genes standard gene finders miss

Running on a raw assembly means calling genes first (Pyrodigal, meta mode). Two lysis-specific gaps of standard gene
finders were found on the experimental benchmark: **embedded o-spanins** (lambda Rz1, T7 gp18.7, Mu), which lie inside
their i-spanin gene in another reading frame and are never called, and **intron-split genes** (phage K LysK), which
come out as two fragments. On the larger CPT set the first gap turned out to be big: **from bare DNA Pyrodigal does
not produce 48 of the 162 curated spanins (30%).**

## What was added (`scripts/genecall.py`)

**Nested lipoprotein ORFs.** For every called gene of 60-300 aa, the two other reading frames on the same strand are
scanned for an ORF that starts inside it (ATG/GTG/TTG, 40-200 codons, not already called) and begins with a
lipoprotein signal: lipobox `[LVI][ASTVI][GAS]C` with the cysteine at residue 15-35 and a hydrophobic h-region. That
is the defining signal of an o-spanin, so the finder is narrow: it adds 0.5 ORFs per genome. The extra ORFs are
scored like any other protein (nothing is promoted) and labelled `nested lipoprotein ORF in <host>` in the output.
On by default for `--genome`; `--no-nested` turns it off.

Settings were chosen on gene-finding counts only (spanins recovered vs ORFs added, CPT), never on model scores:

| variant | CPT spanins recovered (of 48 missed) | ORFs added (90 genomes) |
|---|---|---|
| lipobox as above, host must have an N-terminal TM | 23 | 27 |
| **lipobox as above, any host of 60-300 aa (chosen)** | **24** | **45** |
| broader lipobox consensus, cysteine up to residue 55 | 30 | 64 |

The TM requirement was dropped because the hydropathy heuristic misses real i-spanins (T7 gp18.5 has none by it).
Still not found: o-spanins that start upstream of their i-spanin, and lipoboxes outside the consensus (e.g. `MSGC`).

**Split genes, in the benchmark.** When a proven gene is not called whole, it is now placed on the called fragment
that shares the longest stretch with it (at least 30% of the gene), and reported as a fragment placement. LysK is
placed on its 267-aa N-terminal fragment, which carries the catalytic CHAP domain. The predictor itself is unchanged
here: it scores fragments as proteins, which is what a user sees.

## Results, from bare DNA

**CPT, 89 genomes, shipped spanin recipe** (`reports/cpt_denovo_spanin_signal.json` vs
`cpt_denovo_nested_spanin_signal.json`). Curated spanins the gene caller does not produce count as misses. Paired
genome bootstrap.

| | novel family: without | with nested ORFs | change (95% CI) | known family: without | with |
|---|---|---|---|---|---|
| spanins found by gene calling | 114 / 162 | **138 / 162** | | | |
| curated spanins in their genome's top 5 | 0.611 | **0.759** | **+0.148 [+0.099, +0.199]** | 0.630 | **0.778** (+0.148 [+0.100, +0.199]) |
| genomes with a spanin ranked 1st | 0.567 | **0.611** | **+0.044 [+0.011, +0.089]** | 0.744 | 0.767 (+0.022 [-0.022, +0.067]) |
| genomes with a spanin in top 5 | 0.922 | 0.922 | 0 | 0.922 | 0.922 |

**Experimental set, 24 genomes** (`validated_denovo_*` vs `validated_denovo_nested_*`):

| proven genes in top 5 | novel family: before | after | known family: before | after |
|---|---|---|---|---|
| spanin (7) | 3 (4 found) | **6** (7 found) | 4 | **7** |
| endolysin (22) | 20 (21 found) | **21** (LysK fragment ranked 3rd) | 21 | **22** |
| holin (8) | 7 | 7 | 8 | 8 |

**Adopted.** Nothing got worse; the nested finder is on by default in `scripts/32_predict_lysis.py --genome`.
Holin and endolysin rankings were checked on the experimental set only (unchanged there); the extra ORFs are
lipoproteins, 0.5 per genome, so they rarely compete with either.
