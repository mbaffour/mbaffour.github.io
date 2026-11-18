"""The pre-registered analysis of the final test (reports/final/FROZEN.md), and nothing else.

H1 (confirmatory): the shipped endolysin model's call matches the annotated endolysin more often than the retired
model's; paired, one-sided alpha 0.05, bootstrap over gene-content clusters of the final genomes.
Estimation: per class, the call matches the annotated gene (spanin: or its overlapping partner) and the annotated gene
is in the top 5, with 95% cluster-bootstrap CIs, overall and by the annotated gene's identity to the training data.
Output: reports/final/final_results.json
Usage: python3 scripts/61_final_report.py
"""
import importlib, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
FG = importlib.import_module("53_set_figures")
CL = json.load(open(B / "reports/clusters/final.json"))


def units(keys):
    d = defaultdict(list)
    for k in keys: d[CL.get(k, {}).get("gene", k)].append(k)
    return list(d.values())


def ci(per_genome, n=4000):
    G = sorted(per_genome); v = np.array([per_genome[g] for g in G], float); idx = {g: i for i, g in enumerate(G)}
    U = [[idx[g] for g in u] for u in units(G)]; rng = np.random.default_rng(0)
    bs = [v[[i for k in rng.integers(0, len(U), len(U)) for i in U[k]]].mean() for _ in range(n)]
    return {"value": round(float(v.mean()), 3), "CI95": [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)],
            "genomes": len(G), "clusters": len(U)}


def main():
    new = json.load(open(B / "reports/final/score.json"))["classes"]
    old = json.load(open(B / "reports/final/score_pred_old_endolysin.json"))["classes"]
    res = {}
    # H1
    a = {p["genome"]: float(p["call_correct"]) for p in old["endolysin"]["per_genome"]}
    b = {p["genome"]: float(p["call_correct"]) for p in new["endolysin"]["per_genome"]}
    G = sorted(set(a) & set(b)); idx = {g: i for i, g in enumerate(G)}
    va, vb = np.array([a[g] for g in G]), np.array([b[g] for g in G])
    U = [[idx[g] for g in u] for u in units(G)]; rng = np.random.default_rng(0)
    d = np.array([(vb[p] - va[p]).mean() for p in ([i for k in rng.integers(0, len(U), len(U)) for i in U[k]] for _ in range(4000))])
    res["H1_endolysin_fix"] = {"retired": round(float(va.mean()), 3), "shipped": round(float(vb.mean()), 3),
                               "delta": round(float(vb.mean() - va.mean()), 3),
                               "one_sided_95_lower": round(float(np.percentile(d, 5)), 3),
                               "p_one_sided": round(float((d <= 0).mean()), 4), "genomes": len(G), "clusters": len(U),
                               "fixed": int(((vb == 1) & (va == 0)).sum()), "broken": int(((vb == 0) & (va == 1)).sum())}
    print("H1:", res["H1_endolysin_fix"], flush=True)
    # estimation, with spanin at pair level from the figure module's measures
    M = FG.measures(FG.load_set("final"))
    for cls in ("holin", "endolysin", "spanin"):
        pg = new[cls]["per_genome"]
        call = {p["genome"]: float(p["call_correct"]) for p in pg}
        top5 = {p["genome"]: float(bool(p["best_rank"]) and p["best_rank"] <= 5) for p in pg}
        r = {"call_is_annotated_gene": ci(call), "annotated_in_top5": ci(top5)}
        if cls == "spanin":
            G2 = [g["acc"] for g in FG.load_set("final") if any("spanin" in l for l in g["lab"])]
            r["call_is_annotated_spanin_or_partner"] = ci(dict(zip(G2, M["spanin"]["pair"])))
        r["by_identity_to_training"] = new[cls]["by_novelty"]
        res[cls] = r
        print(cls, {k: v for k, v in r.items() if k != "by_identity_to_training"}, flush=True)
        print("   by identity:", r["by_identity_to_training"], flush=True)
    (B / "reports/final/final_results.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
