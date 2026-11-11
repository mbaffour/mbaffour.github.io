"""Paired genome-level bootstrap of the DIFFERENCE in AP between two capacity-sweep configs.

Why this and not the CIs already in the reports. Each report carries a marginal CI for its own AP,
and across the sweep those intervals overlap heavily -- yet v1 beat v2 on all six AP comparisons.
Overlapping marginal intervals cannot settle that, because both configs are scored on THE SAME
genomes with the same protocol: the comparison is paired, and the paired difference has far less
variance than either AP alone. So this resamples genomes once and recomputes BOTH APs on the same
resample, giving a CI for delta = AP(b) - AP(a) directly.

It needs no refitting. scripts/40 checkpoints every genome's per-protein score vector under
.fitckpt/<hash>/, so the scores for both configs are already on disk; this only has to rebuild the
labels, which come from the GenBank product names exactly as scripts/40 derives them.

A delta CI that excludes zero means the direction is real at this sample size. One that includes
zero means the benchmark cannot resolve it, however consistent the sign looks across configs.

Usage: python3 scripts/41_paired_delta.py --a .fitckpt/<hash_a> --b .fitckpt/<hash_b> [--boot 4000]
"""
import argparse, glob, importlib, json, sys
from pathlib import Path
import numpy as np
from sklearn.metrics import average_precision_score
sys.path.insert(0, str(Path(__file__).resolve().parent))
S5 = importlib.import_module("05_scan_genome")
B = Path(__file__).resolve().parent.parent
L = importlib.import_module("40_logo_benchmark")


def genomes_with_truth(cls, patterns):
    out = []
    for p in sorted({q for g in patterns for q in glob.glob(str(B / g))}):
        try:
            ps = [x for x in S5.annotated_proteins(p)
                  if x.get("sequence") and 20 <= len(x["sequence"]) <= 2000]
        except Exception:
            continue
        if not ps: continue
        tr = []
        for i, x in enumerate(ps):
            prod = x.get("product") or ""
            if L.ANTI.search(prod): continue
            if L.TRUTH[cls].search(prod): tr.append(i)
        if tr: out.append({"name": Path(p).stem, "n": len(ps), "truth": set(tr)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True, nargs="+")
    ap.add_argument("--cls", default="endolysin"); ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--genbanks", nargs="+", default=["data/raw/panel/*.gb", "data/raw/genomes/*.gb"])
    ap.add_argument("--out")
    a = ap.parse_args()
    da = Path(a.a); dbs = [Path(x) for x in a.b]
    ca = json.loads((da / "config.json").read_text())
    cbs = [json.loads((d / "config.json").read_text()) for d in dbs]
    desc = lambda c: (f"{c['hp']['max_iter']}/{c['hp']['max_leaf_nodes']} es={c['hp']['early_stopping']} "
                      f"{Path(c['endolysin']).name}" + (f" sub={c['extra']}" if c.get("extra") else ""))
    print("A:", desc(ca))
    for c in cbs: print("B:", desc(c))
    if len(dbs) > 1:
        print(f"   ({len(dbs)} B replicates: each resample averages the per-replicate deltas, so the CI "
              f"covers replicate variance as well as genome variance)")

    gs = genomes_with_truth(a.cls, a.genbanks)
    res = {"A": ca, "B": cbs if len(cbs) > 1 else cbs[0], "class": a.cls, "boot": a.boot, "protocols": {}}
    for mode in ("family", "sequence"):
        gn, y, xa, xbs = [], [], [], [[] for _ in dbs]
        for g in gs:
            sa = L.ck_load(da, a.cls, mode, g["name"], g["n"])
            sb = [L.ck_load(d, a.cls, mode, g["name"], g["n"]) for d in dbs]
            if sa is None or any(x is None for x in sb):
                print(f"  {mode}: missing checkpoint for {g['name']}, skipped"); continue
            for i in range(g["n"]):
                gn.append(g["name"]); y.append(int(i in g["truth"])); xa.append(float(sa[i]))
                for k in range(len(dbs)): xbs[k].append(float(sb[k][i]))
        if not gn: print(f"  {mode}: nothing to compare"); continue
        gn, y, xa = np.array(gn), np.array(y), np.array(xa); xbs = [np.array(x) for x in xbs]
        apa = average_precision_score(y, xa)
        apbs = [average_precision_score(y, x) for x in xbs]
        uq = sorted(set(gn)); idx = {q: np.where(gn == q)[0] for q in uq}
        rng = np.random.default_rng(0); d = []
        for _ in range(a.boot):
            pick = rng.choice(uq, size=len(uq), replace=True)
            ix = np.concatenate([idx[q] for q in pick])
            if len(set(y[ix])) < 2: continue
            base = average_precision_score(y[ix], xa[ix])
            d.append(np.mean([average_precision_score(y[ix], x[ix]) - base for x in xbs]))
        d = np.array(d)
        lo, hi = np.percentile(d, [2.5, 97.5])
        p = 2 * min((d <= 0).mean(), (d >= 0).mean())
        apb = float(np.mean(apbs))
        v = {"AP_A": round(float(apa), 4), "AP_B": round(apb, 4),
             "AP_B_per_replicate": [round(float(x), 4) for x in apbs],
             "delta_B_minus_A": round(apb - float(apa), 4),
             "delta_CI95": [round(float(lo), 4), round(float(hi), 4)],
             "p_two_sided": round(float(min(p, 1.0)), 4),
             "n_genomes": len(uq), "n_truths": int(y.sum()), "n_resamples_used": int(len(d)),
             "frac_resamples_B_worse": round(float((d < 0).mean()), 4)}
        res["protocols"][mode] = v
        rep = "" if len(apbs) == 1 else f" (reps {', '.join(f'{x:.4f}' for x in apbs)})"
        print(f"  {mode:<9} AP_A={v['AP_A']:.4f} AP_B={v['AP_B']:.4f}{rep} "
              f"delta={v['delta_B_minus_A']:+.4f} CI95={v['delta_CI95']} "
              f"p={v['p_two_sided']:.4f} (B worse in {v['frac_resamples_B_worse']*100:.0f}% of resamples)")
    if a.out:
        (B / a.out).write_text(json.dumps(res, indent=1)); print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
