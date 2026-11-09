"""What measurable properties separate holins from the phage proteins they sit beside?

This is an interpretability pass, not a claim of mechanism. Everything below is a statistical association in a set
of 558 holins, and the honest reading of any single line is "holins in this collection differ from these
comparison sets in this way", not "holins require this".

Three comparisons, chosen so that each controls for something different:
  vs bacterial negatives   -- the original training contrast; mostly re-derives "holins are small and membranous"
  vs PHAGE negatives       -- same genomes, same evolutionary pressure, so size and phage-ness are controlled
  vs SPANINS               -- the hardest contrast: also small, also phage, also in the lysis cassette, also
                              membrane proteins. Anything separating holins from spanins is specific to holins
                              rather than to "small phage membrane protein".

For each interpretable feature (36 handcrafted + 17 TM-anchored local) we report the group medians, a
Mann-Whitney U test, the rank-biserial effect size with a bootstrap CI, and -- because 53 features are tested --
a Benjamini-Hochberg q-value. Permutation importance on the fitted model is reported separately, so "the model
leans on this" and "this differs between groups" stay distinguishable.

Usage: python3 scripts/16_signature_discovery.py [--boot 2000] [--top 15]
"""
import argparse, json, pickle, re, sys
from pathlib import Path
import numpy as np
from scipy.stats import mannwhitneyu
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F

B = Path(__file__).resolve().parent.parent
SPANIN = re.compile(r"spanin|\brz\b|rz1", re.I)
NAMES = F.HAND_NAMES + F.LOCAL_NAMES


def vec(seq):
    v, _ = F.local(seq)
    return np.concatenate([F.handcrafted(seq), np.array(v)])


def bh(ps):
    """Benjamini-Hochberg q-values."""
    p = np.asarray(ps); o = np.argsort(p); q = np.empty_like(p)
    m = len(p); prev = 1.0
    for rank, i in enumerate(o[::-1]):
        k = m - rank
        prev = min(prev, p[i] * m / k); q[i] = prev
    return q


def rank_biserial(a, b, rng, boot):
    """Effect size in [-1, 1]: the probability a random `a` exceeds a random `b`, rescaled. CI by bootstrap."""
    def rb(x, y):
        u = mannwhitneyu(x, y, alternative="two-sided").statistic
        return 2 * u / (len(x) * len(y)) - 1
    point = rb(a, b)
    vals = [rb(rng.choice(a, len(a), replace=True), rng.choice(b, len(b), replace=True)) for _ in range(boot)]
    return point, float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def compare(name, A, Bset, rng, boot):
    rows = []
    for j, f in enumerate(NAMES):
        a, b = A[:, j], Bset[:, j]
        if np.allclose(a, a[0]) and np.allclose(b, b[0]): continue
        try: p = float(mannwhitneyu(a, b, alternative="two-sided").pvalue)
        except ValueError: continue
        e, lo, hi = rank_biserial(a, b, rng, boot)
        rows.append({"feature": f, "holin_median": round(float(np.median(a)), 4),
                     "other_median": round(float(np.median(b)), 4), "effect": round(e, 3),
                     "effect_CI95": [round(lo, 3), round(hi, 3)], "p": p})
    q = bh([r["p"] for r in rows])
    for r, qq in zip(rows, q): r["q"] = float(qq); r["p"] = float(f"{r['p']:.3g}")
    rows.sort(key=lambda r: -abs(r["effect"]))
    return {"comparison": name, "n_holin": len(A), "n_other": len(Bset), "features": rows}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--boot", type=int, default=2000); ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()
    data = json.load(open(B / "data/processed/dataset.json"))
    extra = json.load(open(B / "data/processed/phage_negatives.json"))
    hol = [r for r in data if r["label"] == "holin"]
    bact = [r for r in data if r["label"] == "negative"]
    phage = [r for r in extra if not r.get("spanin")]
    span = [r for r in extra if r.get("spanin")]
    print(f"holins {len(hol)} | bacterial negatives {len(bact)} | phage negatives {len(phage)} | spanins {len(span)}", flush=True)

    M = {k: np.array([vec(r["sequence"]) for r in v]) for k, v in
         (("holin", hol), ("bacterial", bact), ("phage", phage), ("spanin", span))}
    rng = np.random.default_rng(0)
    out = [compare("holins vs bacterial negatives", M["holin"], M["bacterial"], rng, a.boot),
           compare("holins vs phage negatives", M["holin"], M["phage"], rng, a.boot),
           compare("holins vs spanins", M["holin"], M["spanin"], rng, a.boot)]

    # permutation importance over the interpretable block only, on the shipped phage-negative model's own features
    imp = None
    mp = B / "models/holin_model_phageneg.pkl"
    if mp.exists():
        from sklearn.metrics import average_precision_score
        mdl = pickle.load(open(mp, "rb"))
        esm = F.ESM(B / "models/esm_cache")
        gold_ids = set(json.load(open(B / "data/processed/gold_holdout.json"))["ids"])
        gold = [r for r in data if r["id"] in gold_ids and r["label"] in ("holin", "negative")]
        gs = [r["sequence"] for r in gold]
        Xg = np.hstack([np.array([F.handcrafted(s) for s in gs]), esm.embed(gs)])
        yg = np.array([r["label"] == "holin" for r in gold], int)
        base = average_precision_score(yg, mdl["model"].predict_proba(Xg)[:, 1])
        imp = []
        for j, f in enumerate(F.HAND_NAMES):      # the shipped model has no local block, so only these are permutable
            d = []
            for rep in range(5):
                Xp = Xg.copy(); r2 = np.random.default_rng(rep)
                Xp[:, j] = Xp[r2.permutation(len(Xp)), j]
                d.append(base - average_precision_score(yg, mdl["model"].predict_proba(Xp)[:, 1]))
            imp.append({"feature": f, "mean_AP_drop": round(float(np.mean(d)), 5), "sd": round(float(np.std(d)), 5)})
        imp.sort(key=lambda r: -r["mean_AP_drop"])
        print(f"permutation importance on the gold holdout (base AP {base:.4f}); top 8:", flush=True)
        for r in imp[:8]: print(f"   {r['feature']:<26} AP drop {r['mean_AP_drop']:+.4f} +/- {r['sd']:.4f}")

    (B / "reports/signature_discovery.json").write_text(json.dumps(
        {"caveat": "statistical associations in 558 holins, not mechanism; medians are of the stated groups",
         "effect_size": "rank-biserial correlation, 95% percentile bootstrap, Benjamini-Hochberg q over 53 features",
         "comparisons": out, "permutation_importance_gold_holdout": imp}, indent=2))

    for c in out:
        print(f"\n=== {c['comparison']}  (holins {c['n_holin']} vs {c['n_other']})", flush=True)
        print(f"  {'feature':<28}{'holin':>10}{'other':>10}{'effect':>9}  CI95            q")
        for r in c["features"][:a.top]:
            print(f"  {r['feature']:<28}{r['holin_median']:>10.3f}{r['other_median']:>10.3f}{r['effect']:>9.3f}  "
                  f"[{r['effect_CI95'][0]:+.2f},{r['effect_CI95'][1]:+.2f}]   {r['q']:.2g}")


if __name__ == "__main__":
    main()
