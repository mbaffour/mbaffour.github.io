# Label audit: holin and spanin training positives

The endolysin positives held 51 virion proteins (`../endolysin_virion_fix.md`). The same check for holins and
spanins (`scripts/59_label_audit.py`; per-record flags in `holin_audit.json`, `spanin_audit.json`):

| flag | holins (5,055) | used to remove? |
|---|---|---|
| database description names a non-holin function, never "holin"/"lysis protein" | 50 | **yes** |
| no membrane helix (our predictor) | 89 (63 also by the hydropathy heuristic) | no: it would remove real holins (T7 gp17.5, "Lysis S family protein") -- the predictor misses some holin helices |
| lipobox | 13 | no: all 13 are described as holins; chance matches |
| bacterial (not phage) record | 321 | no: they come from phage holin families (lambda S, phi11, PRD1 P35, P7 LydD ...), i.e. prophage holins |

The 50 removed "holins": 15 PTS mannose transporter subunits, 5 ribokinases, transporters, restriction endonucleases,
a transcriptional regulator, and endolysin-type enzymes (an amidase, a lysozyme, a murein endopeptidase) -- Pfam
holin-family members whose own descriptions say otherwise.

Spanins (1,804): 7 removed -- 3 plant (Arabidopsis) RNA-binding proteins, 2 peptidases, a phosphodiesterase and a
holin. The topology flag (no lipobox, no N-terminal helix) was not used: it mostly catches genuine o-spanins whose
lipobox falls outside our motif's window (T7 gp18.7). LysC (the P2 o-spanin) was kept.

## Retrained and tested (decision rule set before the runs)

Cleaning is justified by correctness, so it is adopted unless it hurts: the lower 95% bound on the change in CPT
unseen-family top-1 and top-5, resampling gene-content clusters, must stay above -0.05.

| CPT, unseen family | shipped | cleaned | change (95% CI, cluster bootstrap) | |
|---|---|---|---|---|
| holin, ranked 1st | 0.538 | 0.513 | -0.026 [-0.093, +0.043] | **fails** (bound below -0.05) |
| holin, top 5 | 0.846 | 0.846 | 0.000 [-0.037, +0.033] | |
| spanin, ranked 1st | 0.395 | 0.401 | +0.006 [0.000, +0.023] | **passes** |
| spanin, top 5 | 0.907 | 0.907 | 0.000 [-0.017, +0.020] | |

Experimental set: identical (holin 7/8 first, spanin 7/7 in the top 5, both versions).

**Spanin cleaning adopted** (`models/spanin_model.pkl`; previous model kept as `spanin_model_signal_retired.pkl`).
**Holin cleaning not adopted**: non-inferiority on top-1 cannot be shown with 78 genomes in 42 clusters, even though
the 50 removed proteins are clearly mislabelled. The removal list is kept (`data/processed/label_audit_removals.json`,
benchmark option `--holin-audit`) for a later test with more data.
