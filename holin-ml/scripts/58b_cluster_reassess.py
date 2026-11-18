"""Re-test every headline paired comparison with resampling that respects genome relatedness (scripts/58).

For each comparison the same per-genome outcomes are resampled three ways: by genome (what the reports used), by
ANI-95% cluster, and by gene-content cluster; 4,000 paired bootstrap draws each, 95% CI and two-sided p on the
difference. A result counts as holding up if its CI still excludes 0 under gene-content clustering, the strictest.
Output: reports/clusters/reassessment.json and .md
Usage: python3 scripts/58b_cluster_reassess.py
"""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
B = Path(__file__).resolve().parent.parent


def cl(s): return json.load(open(B / f"reports/clusters/{s}.json"))


def paired(per_genome, clusters, n=4000, seed=0):
    """per_genome: {genome: (base_value, new_value)} -> {unit: (delta, lo, hi, p)} for genome / ani95 / gene"""
    out = {}
    G = sorted(per_genome); a = np.array([per_genome[g][0] for g in G], float); b = np.array([per_genome[g][1] for g in G], float)
    delta = b.mean() - a.mean()
    for unit in ("genome", "ani95", "gene"):
        if unit == "genome": groups = [[i] for i in range(len(G))]
        else:
            d = defaultdict(list)
            for i, g in enumerate(G): d[clusters.get(g, {}).get(unit, f"solo_{g}")].append(i)
            groups = list(d.values())
        rng = np.random.default_rng(seed); ds = []
        for _ in range(n):
            pick = [i for k in rng.integers(0, len(groups), len(groups)) for i in groups[k]]
            ds.append(b[pick].mean() - a[pick].mean())
        ds = np.array(ds); p = min(1.0, 2 * min((ds <= 0).mean(), (ds >= 0).mean()))
        out[unit] = {"units": len(groups), "delta": round(float(delta), 3), "CI95": [round(float(np.percentile(ds, 2.5)), 3),
                     round(float(np.percentile(ds, 97.5)), 3)], "p": round(float(p), 4)}
    out["base"], out["new"] = round(float(a.mean()), 3), round(float(b.mean()), 3)
    return out


def ranks(f, cls, proto, keep):
    R = defaultdict(list)
    for t in json.load(open(B / f))["classes"][cls][proto]["truth_ranks"]:
        if t["genome"] in keep: R[t["genome"]].append(t["rank"])
    return R


def rank_cmp(set_, base, new, cls, proto, metric):
    keep = set(json.load(open(B / f"data/raw/{set_}/truth.json")))
    a, b = ranks(base, cls, proto, keep), ranks(new, cls, proto, keep)
    f = {"top1": lambda r: np.mean([x == 1 for x in r]), "top5": lambda r: np.mean([x <= 5 for x in r]),
         "best1": lambda r: float(min(r) == 1)}[metric]
    return {g: (f(a[g]), f(b[g])) for g in set(a) & set(b)}


def denovo_spanin(base, new, proto):
    """share of ALL curated spanins in the top 5 (not found by gene calling = miss), per genome"""
    T = json.load(open(B / "data/raw/cpt/truth.json")); out = {}
    get = lambda f: {g: [t["rank"] for t in json.load(open(B / f))["classes"]["spanin"][proto]["truth_ranks"] if t["genome"] == g] for g in T}
    A, Bn = get(base), get(new)
    for g, v in T.items():
        if not v.get("spanin"): continue
        n = len(v["spanin"]); out[g] = (sum(x <= 5 for x in A[g]) / n, sum(x <= 5 for x in Bn[g]) / n)
    return out


def blind_call(set_, base, new, cls):
    o = {p["genome"]: p["call_correct"] for p in json.load(open(B / f"reports/{set_}/{base}"))["classes"][cls]["per_genome"]}
    n = {p["genome"]: p["call_correct"] for p in json.load(open(B / f"reports/{set_}/{new}"))["classes"][cls]["per_genome"]}
    return {g: (float(o[g]), float(n[g])) for g in set(o) & set(n)}


COMPARISONS = [
    ("Endolysin virion fix, CPT, unseen family, ranked 1st", "cpt",
     lambda: rank_cmp("cpt", "reports/cpt_endolysin_evidence.json", "reports/cpt_endolysin_novirion.json", "endolysin", "family_removal", "top1"), "adopted"),
    ("Endolysin virion fix, CPT, known family, top 5", "cpt",
     lambda: rank_cmp("cpt", "reports/cpt_endolysin_evidence.json", "reports/cpt_endolysin_novirion.json", "endolysin", "sequence_removal", "top5"), "adopted"),
    ("Endolysin virion fix, blind set 2, call = annotated endolysin", "blind2",
     lambda: blind_call("blind2", "score_pred_old.json", "score_pred_new.json", "endolysin"), "adopted"),
    ("Nested o-spanin finder, CPT bare DNA, unseen family, curated spanins in top 5", "cpt",
     lambda: denovo_spanin("reports/cpt_denovo_spanin_signal.json", "reports/cpt_denovo_nested_spanin_signal.json", "family_removal"), "adopted"),
    ("Nested o-spanin finder, CPT bare DNA, known family, curated spanins in top 5", "cpt",
     lambda: denovo_spanin("reports/cpt_denovo_spanin_signal.json", "reports/cpt_denovo_nested_spanin_signal.json", "sequence_removal"), "adopted"),
    ("Holin ESM-2 150M, CPT, unseen family, top 5", "cpt",
     lambda: rank_cmp("cpt", "reports/cpt_holin_spanin.json", "reports/cpt_holin_esm150.json", "holin", "family_removal", "top5"), "rejected"),
    ("Holin mined families v1, CPT, unseen family, ranked 1st", "cpt",
     lambda: rank_cmp("cpt", "reports/cpt_holin_spanin.json", "reports/cpt_holin_ctxmined.json", "holin", "family_removal", "top1"), "rejected"),
    ("Holin mined families v2, CPT, known family, ranked 1st", "cpt",
     lambda: rank_cmp("cpt", "reports/cpt_holin_spanin.json", "reports/cpt_holin_ctxmined2.json", "holin", "sequence_removal", "top1"), "rejected"),
]


def main():
    res = []
    for name, set_, fn, decision in COMPARISONS:
        r = paired(fn(), cl(set_)); r["name"], r["decision"] = name, decision; res.append(r)
        print(f"{name}\n   {r['base']} -> {r['new']}  " + " | ".join(
            f"{u}: {r[u]['delta']:+.3f} [{r[u]['CI95'][0]:+.3f}, {r[u]['CI95'][1]:+.3f}] p={r[u]['p']} (n={r[u]['units']})"
            for u in ("genome", "ani95", "gene")), flush=True)
    (B / "reports/clusters/reassessment.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
