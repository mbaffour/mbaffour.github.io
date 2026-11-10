# Out-of-sample panel scan: three-gene lysis caller (holin / endolysin / spanin)

Source: `reports/panel_scan.json` (threshold 0.5, cassette window 6). Per-protein detail: scratchpad `detail.json` (re-scored with the same models and cached ESM; no script modified, no retraining).

**Frame.** None of the 12 genomes is in `data/raw/pool/accessions.json`, the atlas, or the holin benchmark, so this is a genome-level out-of-sample test. It is NOT fully sequence-level out-of-sample: the script's own exact-sequence check finds that many recovered proteins are identical to training positives (see below). Annotation is an imperfect ground truth, and all calls are predictions.

## Panel construction
- 22 candidates checked on NCBI. 10 dropped as already in the pool (in-sample): Bxb1 NC_002656, Twort NC_007021, K NC_005880, A511 NC_009811, SPO1 NC_011421, phiCD119 NC_007917, VP882 NC_009016, P-SSP7 NC_006882, Xp10 NC_004902, 186 NC_001317. None matched the benchmark/atlas exclusion list.
- Caulobacter CbK: NC_019528.1 is actually Aeromonas phage phiAS7 (wrong accession, dropped). Resolved by esearch to Caulobacter phage phiCbK NC_019405.1 (RefSeq, not in pool).
- Final 12: L5, TM4, Giles, phiC31, BFK20 (actinobacterial); TP901-1; phiKZ, LKA1, phiCbK; T3, N15, Felix O1. Only 5 actino genomes survived because Bxb1 was in the pool.

## Overall
- Genomes scanned 12; cassette (all three classes within 6 genes) detected in 5 (41.7%): phiKZ, LKA1, T3, N15, phiCbK.
- Per-class recovery (annotated gene scored >= 0.5) as computed by the script:

| class | genomes with annotated gene | recovered | top-scoring protein is annotated that class | recovered hits that are exact training sequences |
|---|---|---|---|---|
| holin | 8 | 8 | 6 | 4 |
| endolysin | 10 | 10 | 10 | 4 |
| spanin | 5 | 5 | 5 | **5** |

- **The in-sample number is not ~0.** Exact-sequence overlap with the training positives is 4/8 holin, 4/10 endolysin, 5/5 spanin, even though no accession is in the pool (the curated holin and endolysin/spanin positive sets contain these proteins or identical copies from other entries). Counting only genomes where a recovered protein is NOT an exact training sequence:
  - holin 4/4 (BFK20, TP901-1, N15, phiCbK)
  - endolysin 6/6 (TM4, BFK20, TP901-1, LKA1, Felix O1, phiCbK)
  - spanin 0 testable. All 5 annotated spanins are exact training sequences, so spanin recovery says nothing about generalization.
- Near-homolog leakage (non-identical but related to training sequences) is not measured here, so even the "clean" numbers are probably optimistic. N=4-6 per class is also tiny.
- Recovery here is lenient: a class counts as recovered if ANY annotated gene scores >= 0.5. Endolysin recovery is mostly name-based (lysozyme/amidase/etc. regex); LKA1's internal virion lysozyme-motif proteins scored 0.28 and 0.16 while its true lysozyme scored 0.945.

## Actinobacterial subset (the key question)
The script's own flag marks only 3 genomes as actino (TM4, Giles, BFK20); it misses L5 ("Fromanvirus L5") and phiC31 ("Bacteriophage phi-C31"). Using host by design: **5 actino genomes** (L5, TM4, Giles, phiC31, BFK20), 0 with a detected cassette.

| genome | holin | endolysin | spanin |
|---|---|---|---|
| L5 | annotated, 1.0 (exact training seq) | annotated, 0.98/0.92 (exact training seqs) | none annotated; top 0.10 |
| TM4 | annotated, 1.0 (exact training seq) | annotated 3 genes, 0.53/0.97/0.98 (not in training) | none annotated; top 0.49 |
| Giles | no annotation (gp only) | no annotation | none |
| phiC31 | no annotation (gp only) | no annotation | none |
| BFK20 | annotated "gp26, holin" 0.999 (not in training); top-scoring is neighbour gp27 (0.999) | annotated lysin 0.966 (not in training) | none annotated; top 0.11 |

- Annotated-gene recovery in actino: holin 3/3, endolysin 3/3 (spanin: no annotated genes, N/A). But 2 of the 3 holins and 1 of the 3 endolysins are exact training sequences. Truly unseen: BFK20 holin and BFK20 lysin, plus TM4 endolysins. That is 1 holin and 2 endolysin genomes, which is far too few to claim the actino weakness is fixed.
- **0/5 actino cassettes.** The cassette definition requires a spanin, and mycobacterial/streptomyces/corynebacterial phages generally have no Rz-like spanin, so this reflects the three-gene definition and biology as much as model failure. It does mean the "cassette" output is uninformative for actino hosts; holin+endolysin pairs are what to look at.
- Giles and phiC31 cannot be scored against annotation (no lysis product names). Unannotated high calls there: Giles gp31/gp32 endolysin-like (0.98/0.96), gp33/gp34 holin-like (1.0/0.999); phiC31 gp50 endolysin-like (0.996), gp29 and gp48 holin-like (0.996, 0.994). Plausible clustered lysis cassette in Giles, unverified; phiC31 calls are scattered (gp29 vs gp48 vs gp50) and not validated.
- Honest read: no clear sign of the historical actino holin weakness on this panel, but the evidence is thin (the one unseen annotated holin, BFK20, is recovered) and contaminated by in-sample hits. Not a demonstration that the Hol-X/1.E.34 weakness is solved.

## Per-genome table
Cells: annotated gene recovered (Y/N/-no annotation); "top" = highest-scoring protein of that class is an annotated one; `*` = recovered hit is an exact training sequence.

| genome | host/organism | proteins | cassette | holin | endolysin | spanin |
|---|---|---|---|---|---|---|
| NC_001335 L5 | Mycobacterium (actino) | 90 | no | Y* top | Y* top | - |
| NC_003387 TM4 | Mycobacterium (actino) | 89 | no | Y* top | Y top | - |
| NC_009993 Giles | Mycobacterium (actino) | 79 | no | - | - | - |
| NC_001978 phiC31 | Streptomyces (actino) | 55 | no | - | - | - |
| NC_009799 BFK20 | Corynebacterium (actino) | 55 | no | Y, top is neighbour gp27 | Y top | - |
| NC_002747 TP901-1 | Lactococcus | 56 | no | Y top | Y top | - |
| NC_004629 phiKZ | Pseudomonas | 369 | yes | - | Y* top | Y* top |
| NC_009936 LKA1 | Pseudomonas | 57 | yes | Y* top | Y top | Y* top |
| NC_003298 T3 | Enterobacteria | 55 | yes | Y* top | Y* top | Y* top |
| NC_001901 N15 | Escherichia | 60 | yes | Y top | Y* top | - |
| NC_005282 Felix O1 | Salmonella | 127 | no | - | Y top | Y* top |
| NC_019405 phiCbK | Caulobacter | 338 | yes | Y, top is a hypothetical (0.998 vs annotated 0.995) | Y top | Y* top |

## Top high-confidence un-annotated calls (22 total in json)
| accession | class | P | product | read |
|---|---|---|---|---|
| NC_009993 Giles | holin | 1.0 | gp33 (136 aa) | Plausible: sits next to gp31/gp32 lysin-like calls, consistent with a lysis cassette. |
| NC_009993 Giles | holin | 0.999 | gp34 (106 aa) | Plausible, but two holin calls adjacent; one may be a false positive or an additional lysis accessory. |
| NC_009799 BFK20 | holin | 0.999 / 0.993 | gp27 / gp28 | gp27 is adjacent to annotated gp26 holin; tandem membrane proteins, plausible lysis accessories, but possibly sequence-similarity false positives. |
| NC_019405 phiCbK | holin | 0.998 | hypothetical (89 aa) | Scores higher than the annotated holin; could be the real holin or a paralog. Needs TM-topology check. |
| NC_001978 phiC31 | holin | 0.996 | gp29 (78 aa) | Unverified; location far from gp50 endolysin call. |
| NC_001978 phiC31 | endolysin | 0.996 | gp50 (362 aa) | Plausible lytic enzyme but unvalidated. |
| NC_003387 TM4 | holin | 0.984 | "minor tail protein" (139 aa) | Likely false positive or tail-associated membrane protein; annotation conflicts. |
| NC_004629 phiKZ | holin | 0.988 | PHIKZ253.1 (35 aa) | Very short; in a 369-gene genome, probably false positive although small holins exist. |
| NC_005282 Felix O1 | holin | 0.971 / 0.967 | conserved protein (64 aa) / membrane protein (68 aa) | Felix has no annotated holin, so a real holin is plausible. Best novel candidate in the set. |
| NC_001901 N15 | spanin | 0.947 | "Cor superinfection exclusion protein" (78 aa) | Contradicting annotation: likely false positive (Cor is an outer membrane protein, small-membrane-protein bias). |
| NC_005282 Felix O1 | spanin | 0.955 | hypothetical (85 aa) | Felix already has an annotated Rz-like spanin; second call likely false positive or the other spanin subunit. |
| NC_019405 phiCbK | spanin | 0.909 | lipoprotein (142 aa) | Plausible: spanin components (i-spanin/o-spanin) are lipoproteins. |

Some of these are high-probability simply because the models weight membrane-protein features; the 0.9-1.0 range is not calibrated evidence.

## Failures and weak spots
- **Not a miss, but a gap:** Giles and phiC31 have no lysis annotation, so the panel cannot score them as recovered or missed; reported only as un-annotated calls.
- **Felix O1:** annotated endolysin and Rz-like spanin recovered, but no annotated holin; the top holin call is a "Phage conserved protein" (0.971). No cassette detected there despite two annotated lysis components. Possible missing/unannotated holin or window issue.
- **Top-scoring mismatch:** holin top hit is not the annotated gene in BFK20 (gp27 vs annotated gp26) and phiCbK (hypothetical vs annotated), i.e. the model prefers a different protein; may be a legitimate additional holin-like protein or a false positive.
- **LKA1 endolysin:** internal-virion lysozyme-motif proteins scored 0.28/0.16 (below threshold). The true lysozyme was recovered, so this is name-matching noise in the annotation regex, not a real miss.
- **Spanin:** zero spanin-annotated actino genomes (expected biologically), and spanin recovery elsewhere is entirely in-sample, so spanin generalization is untested by this panel.
- **Small-protein false positives:** N15 Cor, phiKZ 35-aa ORF, TM4 minor tail protein are all likely false positives.

## Bottom line
Recovery of annotated lysis genes is high (8/8, 10/10, 5/5), but exact-sequence in-sample overlap is substantial (4, 4, 5), so these rates overstate generalization. Of the genuinely unseen cases, holin 4/4 and endolysin 6/6 genomes were recovered; spanin is untestable. Actino: no evidence of failure on the few unseen annotated genes (BFK20, TM4), but N is too small, and no cassette is detected in any actino genome by construction (no spanins).
