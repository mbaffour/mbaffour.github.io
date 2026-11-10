# Lysis genes in *Bacteroides* phage DAC15 (NC_055832.1)

**Genome:** 99,494 bp, linear. *Crassvirales; Steigviridae; Asinivirinae; Wulfhauvirus* (crAss-like); host
*Bacteroides*. 118 scorable CDS of 120, nearly all annotated "hypothetical protein".

**Out-of-sample status:** no DAC15 protein is in any training set (verified by exact sequence match against all
three positive sets). Every candidate below is out-of-sample.

**Models used:** holin `holin_model_curated.pkl` (arm B), endolysin `endolysin_model.pkl` (**v1** — the v2
family-expanded model regressed and was not shipped, see `reports/retrain_v2_report.md`), spanin
`spanin_model.pkl` (**v2**, family-expanded, +0.077 strict AP).

**Reproduce:**
```
python3 scripts/32_predict_lysis.py --genbank data/raw/genomes/NC_055832.1.gb \
        --domains --show-cassettes --top 5 --out reports/dac15_final.tsv
python3 scripts/33_verify_calls.py --tsv reports/dac15_final.tsv \
        --genbank data/raw/genomes/NC_055832.1.gb --top 3
```

---

## The answer

### Endolysin — **gp039**, the only credible candidate in the genome

| | |
|---|---|
| location | **86,545–87,018 (−)**, 157 aa |
| domain | **PF01832 Glucosaminidase (GH73)**, aa 53–156, **E = 8.7e-17** — the *only* lysis domain in 118 proteins vs 69 lysis HMMs |
| topology | Phobius signal peptide, cleavage 27/28 (`n8-23c27/28o`), 0 TM → N-terminally membrane-targeted; **export route uncertain, see below** |
| nearest training relative | endolysin **0.803 identity at coverage 1.00** (of 2,788) vs holin 0.379, spanin 0.321 |
| model score | P(endolysin) = **0.0059**, **rank 25 of 118** |
| context | among nucleotide/NAD-salvage genes (gp038 ribose-phosphate pyrophosphokinase, gp036 nicotinamide phosphoribosyltransferase) |

**The model missed it, and so would the ranking.** 0.0059 is below any threshold and rank 25 is not a position
anyone inspects. It was found only by the model-independent domain scan (`--domains`).

The nearest-neighbour figures settle *why*: gp039 is 80.3% identical at full coverage to PF01832 lysins already in
UniProt — from crAss-like phages (`uncultured phage cr126_1`, `uncultured phage cr151_1`, `Kolpuevirus frurule`).
This was never a novel-family problem. It was a **training-data coverage gap**, and adding that family still only
moved the score to 0.107 (see `retrain_v2_report.md`), which is why endolysin detection should be domain-driven.

*Caveat 1 — the N-terminus is NOT cleanly a cleaved signal peptide.* Inspecting it by hand (`MKQRFINILLVIAIVALG
VLVFLNHEAIEQC…`) rather than trusting the Phobius label:
- h-region (8–23) `ILLVIAIVALGVLVFLN`, mean Kyte–Doolittle **+3.05** — strongly hydrophobic, so a genuine signal
  peptide *or* a membrane anchor;
- n-region charge **+2**, canonical;
- but the predicted cleavage at 27/28 gives **−3 = His**, which is not the small residue a canonical Sec AXA
  cleavage motif requires, so cleavage is doubtful;
- and it is **not SAR-like**: signal-anchor-release domains are characteristically *weakly* hydrophobic and
  Gly/Ala-rich, whereas this is +3.05 with only 18% G+A;
- Cys31 is **not** in a lipobox (`I-E-Q-C` fails `[LVI][ASTVI][GAS]C`), so not a lipoprotein.

So gp039 is N-terminally membrane-targeted, but whether it is cleaved and released, signal-anchored, or retained
is unresolved by prediction. Calling it "secreted" overstates the evidence; that wording has been corrected here.

*Caveat 2:* GH73 domains also occur in non-lytic proteins (FlgJ, bacterial autolysins). What argues for lysis is
the membrane-targeting N-terminus plus its position outside the structural module — not the domain alone.

### Holin — **gp095**, plausible and genuinely novel

| | |
|---|---|
| location | **25,829–26,230 (+)**, 133 aa |
| model | P(holin) = **0.9664**, **rank 1 of 118** |
| topology | Phobius 1 TM, `o6-25i`; C-terminal charge −1 |
| nearest training relative | holin **0.375** at coverage ≥0.8 (of 5,055) — no close relative |
| domain | none of the 38 holin Pfam families hits |

Hand-checked topology supports the call: TM 6–25 mean Kyte–Doolittle **+1.70** (moderate, as holin TMs tend to
be), a basic **RRK** cluster immediately C-terminal to the TM (the positive-inside rule), N-out/C-in orientation,
and a mixed/acidic C-terminal tail. That is a class III / pinholin-like single-TM architecture.

Right size, right topology, top-ranked, and **37.5% max identity to any of 5,055 known holins** — so this is a real
novel-family call the model made unaided. It is the one result here where the ML did the work. Unconfirmed by
family or domain evidence, and not adjacent to gp039.

### Spanin — **gp004 / gp008**, weak and unresolved

Identical 50-aa copies at **1,337–1,489 (−)** and **98,989–99,141 (−)** — the terminal repeat, so one gene in two
copies. P(spanin) = **0.5746** (ranks 1–2). Phobius: signal peptide cleaved at 22, 0 TM. **No o-spanin lipobox**
(`[LVI][ASTVI][GAS]C`), no i-spanin partner, max identity 0.349 to 2,160 known spanins.

Treat as unresolved. Spanins are expected in a Gram-negative host, but crAss-like phages may use an unrecognised
equivalent. Note the shipped spanin v2 model scores this *lower* than v1 did (0.865 → 0.575) — being less
confident about a lipobox-less call is the correct direction.

### Rejected: gp080

P(endolysin) = 0.8385, rank 1 — **but no lysis domain, no TM (`i`), 832 aa, and a structural-protein neighbour.**
Almost certainly a virion protein or a false positive. This is the entry-vs-exit lysin confusion the project keeps
running into (T4 gp5, T7 gp16): a large multidomain protein in the structural module is not an exit endolysin.

### No lysis cassette
`--show-cassettes` finds none. The candidates are scattered across the genome — gp039 at 86.5 kb, gp095 at 25.8 kb,
gp004/gp008 in the terminal repeats. This is exactly the case the per-gene callers were built for.

---

## Full candidate table

| gene | location | len | P(hol) | P(end) | P(spa) | rank h/e/s | call | Pfam | TM | SP |
|---|---|---|---|---|---|---|---|---|---|---|
| **gp039** | 86,545–87,018 − | 157 | 0.001 | 0.006 | 0.002 | 29/**25**/52 | none | **PF01832** | 0 | **yes (27)** |
| gp095 | 25,829–26,230 + | 133 | **0.966** | 0.000 | 0.141 | **1**/112/4 | holin | – | 1 | no |
| gp012 | 97,466–97,561 − | 31 | 0.728 | 0.000 | 0.001 | 2/–/– | holin | – | 1 | no |
| gp080 | 41,176–43,674 + | 832 | 0.000 | **0.839** | 0.001 | –/**1**/– | endolysin | – | 0 | no |
| gp004 | 1,337–1,489 − | 50 | 0.006 | 0.001 | **0.575** | –/–/**1** | spanin | – | 0 | yes (22) |
| gp008 | 98,989–99,141 − | 50 | 0.006 | 0.001 | **0.575** | –/–/**2** | spanin | – | 0 | yes (22) |
| gp098 | 24,573–25,184 + | 203 | 0.000 | 0.002 | 0.179 | –/–/3 | none | – | 1 | no |
| gp077 | 51,785–55,894 − | 1369 | 0.000 | 0.173 | 0.001 | –/2/– | none | – | 0 | no |
| gp079 | 43,678–45,045 + | 455 | 0.000 | 0.087 | 0.002 | –/3/– | none | – | 0 | no |

gp012 (31 aa) and gp018 (27 aa) are too short to be holins — treat as false positives.

---

## What would settle it

1. **Experiment.** Express gp039 and run a zymogram / turbidity assay on *Bacteroides* peptidoglycan; co-express
   gp095 with gp039 in a heterologous host to test holin-dependent lysis timing.
2. **gp004/gp008.** Check for lipidation experimentally, or search the genome for an unrecognised i-spanin partner;
   the absence of a lipobox is the main thing against the current call.
3. **Tooling.** This genome is the case for per-fold endolysin models gated by the HMM scan, rather than one
   classifier covering five unrelated catalytic folds (proposed, not built — `retrain_v2_report.md`).

## Honest summary

One of the three genes was found by the model (**gp095**, a genuine novel-family holin call at rank 1 of 118). One
was found *only* by model-independent domain evidence (**gp039**, scored 0.0059 at rank 25). One remains
unresolved (**gp004/gp008**). And the model's top endolysin call (**gp080**) is probably wrong. On an
out-of-distribution genome the domain scan is not a nice-to-have — it is what produced the answer.
