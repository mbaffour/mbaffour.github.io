"""Holin ensembles scored from the LOGO checkpoints of scripts/40 (no refitting): mean probability of the shipped model
and variants. Usage: python3 scripts/50_holin_ensemble.py cpt|validated  (run from the repository root)."""
# Holin ensembles from checkpointed LOGO scores (no refitting). Primary (declared before looking): mean probability of
# shipped + mined-v1. Secondary: shipped + ESM-150M; shipped + mined-v1 + ESM-150M.
import json, sys, glob, importlib
from pathlib import Path
import numpy as np
sys.path.insert(0, "scripts"); S5 = importlib.import_module("05_scan_genome")
SET = sys.argv[1]
TF = json.load(open(f"data/raw/{SET}/truth.json"))
CK = Path(f".fitckpt_{SET}")
M = {"shipped": "19bbfc1b12adb229", "mined1": "4367dd8d445262e7", "mined2": "b40da7d300354582", "esm150": "4e3997066aa26163"}
rep = json.load(open(f"reports/{SET}_holin_{'spanin' if SET=='cpt' else 'spanin'}.json"))
G = sorted(g for g in {t["genome"] for t in rep["classes"]["holin"]["family_removal"]["truth_ranks"]} if g in TF and TF[g].get("holin"))
gdir = "data/raw/cpt/genomes" if SET == "cpt" else "data/raw/validated/genomes"
data = {}
for g in G:
    ps = [x for x in S5.annotated_proteins(f"{gdir}/{g}.gb") if x.get("sequence") and 20 <= len(x["sequence"]) <= 2000]
    tr = [i for i, x in enumerate(ps) if x["id"] in set(TF[g]["holin"])]
    sc = {}
    for mode in ("family", "sequence"):
        for k, d in M.items():
            f = CK / d / f"holin__{mode}__{g}.json"
            if f.exists():
                s = np.array(json.loads(f.read_text()))
                if len(s) == len(ps): sc[(k, mode)] = s
    data[g] = (tr, sc, ps)
def ranks(score, tr): return [1 + int((score > score[t]).sum()) for t in tr]
def combo(sc, keys, mode): 
    if not all((k, mode) in sc for k in keys): return None
    return np.mean([sc[(k, mode)] for k in keys], axis=0)
CANDS = {"shipped": ["shipped"], "shipped+mined1 (PRIMARY)": ["shipped", "mined1"], "shipped+esm150": ["shipped", "esm150"],
         "shipped+mined1+esm150": ["shipped", "mined1", "esm150"], "mined1": ["mined1"]}
rng = np.random.default_rng(0)
for mode, label in (("family", "novel family"), ("sequence", "known family")):
    R = {}
    for name, keys in CANDS.items():
        r = {}
        for g, (tr, sc, ps) in data.items():
            s = combo(sc, keys, mode)
            if s is not None: r[g] = min(ranks(s, tr))
        R[name] = r
    base = R["shipped"]
    print(f"--- {SET} {label}: {len(base)} genomes")
    for name, r in R.items():
        gs = [g for g in base if g in r]
        if len(gs) < len(base): print(f"  {name}: only {len(gs)} genomes scored, skipped"); continue
        a = np.array([base[g] for g in gs]); b = np.array([r[g] for g in gs])
        out = []
        for k in (1, 5):
            xa, xb = (a <= k).astype(float), (b <= k).astype(float)
            bs = [xb[i].mean() - xa[i].mean() for i in (rng.integers(0, len(gs), len(gs)) for _ in range(2000))]
            lo, hi = np.percentile(bs, [2.5, 97.5])
            out.append(f"top{k} {xb.mean():.3f} ({xb.mean()-xa.mean():+.3f} [{lo:+.3f}, {hi:+.3f}])")
        print(f"  {name:28s} " + "  ".join(out) + f"  median rank {np.median(b):.0f}")
    if SET == "cpt" and mode == "family":
        t4 = [g for g, (tr, sc, ps) in data.items() if any(n in ps[tr[0]]["id"] for n in ("Marfa", "EI1", "pKp20", "Hypnos", "Nesoi", "Persephone"))]
        for name in CANDS: print(f"  T4-type ranks {name:28s}", [R[name].get(g) for g in t4])
