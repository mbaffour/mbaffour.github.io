# Lysis cassette scan (demo)

threshold=0.5, cassette window=6 genes. Three independent one-vs-rest models (holin_curated, endolysin, spanin) on one 516-d feature matrix.

CAVEAT: these are deployment models trained on all labels (incl. the atlas phages' own lysis genes), so the lambda check verifies pipeline wiring only; it is in-sample, not an accuracy estimate (see reports/*_eval.json for LOGO estimates).

## Lambda validation

**PASS: known lambda lysis genes score high for their class and the cassette is detected.**

- holin: S (holin/anti-holin) P=1.000 rank 2/73; top is S' (holin/anti-holin) P=1.000
- holin: S' (holin/anti-holin) P=1.000 rank 1/73; top is S' (holin/anti-holin) P=1.000
- endolysin: R (endolysin) P=0.996 rank 1/73; top is R (endolysin) P=0.996
- spanin: Rz (Rz-like spanin) P=0.984 rank 1/73; top is Rz (Rz-like spanin) P=0.984
- spanin: Rz1 (Rz-like spanin) P=0.978 rank 2/73; top is Rz (Rz-like spanin) P=0.984
- S-R-Rz/Rz1 cassette detected: True

## Cassettes per genome

**lambda** (73 proteins): 1 cassette(s)
- S#65 holin/anti-holin [holin]; S'#66 holin/anti-holin [holin]; R#67 endolysin [endolysin]; Rz#68 Rz-like spanin [spanin]; Rz1#69 Rz-like spanin [spanin]

**T7** (60 proteins): 0 cassette(s)

**P22** (72 proteins): 1 cassette(s)
- 13#62 holin/anti-holin [holin]; 13'#63 holin/anti-holin [holin]; 19#64 endolysin [endolysin]; 15#65 Rz-like spanin [spanin]; Rz1#66 Rz-like spanin [spanin]

**HK97** (61 proteins): 1 cassette(s)
- HK97p57#55 holin/anti-holin [holin]; HK97p58#56 endolysin [endolysin]; Rz#57 Rz-like spanin [spanin]

## Top call per class

| genome | class | gene | product | P |
|---|---|---|---|---|
| lambda | holin | S' | holin/anti-holin | 1.000 |
| lambda | endolysin | R | endolysin | 0.996 |
| lambda | spanin | Rz | Rz-like spanin | 0.984 |
| T7 | holin | T7p53 | holin | 1.000 |
| T7 | endolysin | T7p20 | amidase | 0.996 |
| T7 | spanin | T7p55 | Rz-like spanin | 0.995 |
| P22 | holin | 13' | holin/anti-holin | 1.000 |
| P22 | endolysin | 19 | endolysin | 0.888 |
| P22 | spanin | Rz1 | Rz-like spanin | 0.989 |
| HK97 | holin | HK97p57 | holin/anti-holin | 1.000 |
| HK97 | endolysin | HK97p58 | endolysin | 0.996 |
| HK97 | spanin | Rz | Rz-like spanin | 0.977 |
