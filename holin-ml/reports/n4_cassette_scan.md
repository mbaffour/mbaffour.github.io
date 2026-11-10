# Lysis cassette scan (demo)

threshold=0.5, cassette window=6 genes. Three independent one-vs-rest models (holin_curated, endolysin, spanin) on one 516-d feature matrix.

CAVEAT: these are deployment models trained on all labels (incl. the atlas phages' own lysis genes), so the lambda check verifies pipeline wiring only; it is in-sample, not an accuracy estimate (see reports/*_eval.json for LOGO estimates).

## Cassettes per genome

**NC_008720.1** (72 proteins): 1 cassette(s)
- EPNV4_gp60#59 Rz-like spanin [spanin]; EPNV4_gp61#60 endolysin [endolysin]; EPNV4_gp62#61 holin [holin]; EPNV4_gp63#62 gp63 [holin]

## Top call per class

| genome | class | gene | product | P |
|---|---|---|---|---|
| NC_008720.1 | holin | EPNV4_gp63 | gp63 | 0.983 |
| NC_008720.1 | endolysin | EPNV4_gp61 | endolysin | 0.976 |
| NC_008720.1 | spanin | EPNV4_gp60 | Rz-like spanin | 0.983 |
