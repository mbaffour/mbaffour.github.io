"""Which holins does the model actually call, and which does it miss?

Two experiments, both with the best model from 04_train.py:

A. Cluster-grouped cross-validation (as in 04_train.py), but keeping the out-of-fold score of every protein, so recall can
   be broken down by TCDB family, evidence tier and length. Test holins have no >=30% identity / >=50% coverage homolog in
   training, but a distant same-family relative may still be there.

B. Leave-one-family-out: for each TCDB 1.E family with at least MIN_FAM members, delete the ENTIRE family from training
   (plus anything clustered with it) and score its members. This is the "new family" test - can the model recognise a
   holin type it has never seen? It is the number that matters for finding holins in unstudied phages.

Thresholds are fixed from experiment A at the score giving 95% and 90% precision, so recall numbers are comparable.
Usage: python3 scripts/07_family_analysis.py [--min-fam 6]
"""
import argparse, collections, json, pickle, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import precision_recall_curve, roc_auc_score, average_precision_score

B = Path(__file__).resolve().parent.parent


def build(algorithm):
    return (make_pipeline(StandardScaler(), LogisticRegression(max_iter=4000, class_weight="balanced")) if algorithm == "logreg"
            else HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, l2_regularization=1.0,
                                                class_weight="balanced", random_state=0))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--min-fam", type=int, default=6, dest="min_fam")
    a = ap.parse_args()
    bundle = pickle.loads((B / "models/holin_model.pkl").read_bytes())
    data = json.loads((B / "data/processed/dataset.json").read_text())
    train = [r for r in data if r["label"] in ("holin", "negative")]
    y = np.array([r["label"] == "holin" for r in train], int)
    groups = np.array([r["cluster"] for r in train])
    seqs = [r["sequence"] for r in train]
    esm = F.ESM(B / "models/esm_cache")
    Xh = np.stack([F.handcrafted(s) for s in seqs]); Xe = esm.embed(seqs)
    X = {"hand": Xh, "esm": Xe, "both": np.hstack([Xh, Xe])}[bundle["features"]]
    algo = bundle["algorithm"]
    print(f"{len(train)} sequences, {y.sum()} holins, features={bundle['features']}, model={algo}", flush=True)

    # ---- A: cluster-grouped CV, keep out-of-fold scores ----
    t = time.time(); oof = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups):
        m = build(algo); m.fit(X[tr], y[tr]); oof[te] = m.predict_proba(X[te])[:, 1]
    print(f"grouped CV in {time.time()-t:.0f}s  AUROC {roc_auc_score(y, oof):.4f}  AP {average_precision_score(y, oof):.4f}", flush=True)
    p, r, th = precision_recall_curve(y, oof)
    cuts = {}
    for target in (0.90, 0.95):
        idx = np.where(p[:-1] >= target)[0]
        cuts[target] = float(th[idx[0]]) if len(idx) else 1.0
    print("score thresholds:", {f"P{int(k*100)}": round(v, 4) for k, v in cuts.items()}, flush=True)

    hol = [(i, r_) for i, r_ in enumerate(train) if r_["label"] == "holin"]
    def recall(sel, cut): return round(float(np.mean([oof[i] >= cut for i, _ in sel])), 3) if sel else None

    fams = collections.defaultdict(list)
    for i, r_ in hol: fams[r_["tcdb_family"]].append((i, r_))
    famname = {}
    for _, r_ in hol:
        for s in r_["sources"]:
            if s.get("family") and s.get("family_name"): famname[s["family"]] = s["family_name"]
    byfam = {}
    for f, members in sorted(fams.items(), key=lambda kv: -len(kv[1])):
        byfam[f] = {"name": famname.get(f, "Swiss-Prot entries without a TCDB family"), "n": len(members),
                    "recall_at_P95": recall(members, cuts[0.95]), "recall_at_P90": recall(members, cuts[0.90]),
                    "median_score": round(float(np.median([oof[i] for i, _ in members])), 3)}
    bytier = {t_: {"n": sum(1 for _, r_ in hol if r_.get("tier") == t_),
                   "recall_at_P95": recall([(i, r_) for i, r_ in hol if r_.get("tier") == t_], cuts[0.95])}
              for t_ in ("tested", "curated", "putative")}
    bylen = {}
    for lo, hi in [(0, 60), (60, 90), (90, 120), (120, 160), (160, 10000)]:
        sel = [(i, r_) for i, r_ in hol if lo <= r_["length"] < hi]
        bylen[f"{lo}-{hi if hi < 10000 else '+'} aa"] = {"n": len(sel), "recall_at_P95": recall(sel, cuts[0.95])}

    # ---- B: leave-one-family-out ----
    lofo = {}
    big = [f for f, m in fams.items() if len(m) >= a.min_fam and f != "SwissProt-only"]
    print(f"leave-one-family-out over {len(big)} families with >= {a.min_fam} members", flush=True)
    for f in sorted(big, key=lambda f: -len(fams[f])):
        members = fams[f]; idx = {i for i, _ in members}
        # also drop anything sharing a homology cluster with a member, so no near-relative leaks in
        drop_clusters = {train[i]["cluster"] for i in idx}
        keep = np.array([i for i in range(len(train)) if i not in idx and not (y[i] == 1 and train[i]["cluster"] in drop_clusters)])
        t = time.time(); m = build(algo); m.fit(X[keep], y[keep])
        s = m.predict_proba(X[[i for i, _ in members]])[:, 1]
        lofo[f] = {"name": famname.get(f, ""), "n": len(members), "holins_left_in_training": int(y[keep].sum()),
                   "recall_at_P95": round(float(np.mean(s >= cuts[0.95])), 3), "recall_at_P90": round(float(np.mean(s >= cuts[0.90])), 3),
                   "median_score": round(float(np.median(s)), 3)}
        print(f"  {f:8} n={len(members):3} {lofo[f]['name'][:46]:46} recall@P95 {lofo[f]['recall_at_P95']:.2f} median {lofo[f]['median_score']:.3f} [{time.time()-t:.0f}s]", flush=True)

    weighted = float(np.average([v["recall_at_P95"] for v in lofo.values()], weights=[v["n"] for v in lofo.values()])) if lofo else None
    out = {"model": {k: bundle[k] for k in ("features", "algorithm", "esm_model")},
           "grouped_cv": {"auroc": float(roc_auc_score(y, oof)), "average_precision": float(average_precision_score(y, oof)),
                          "score_thresholds": {f"P{int(k*100)}": round(v, 4) for k, v in cuts.items()}},
           "by_family_grouped_cv": byfam, "by_tier": bytier, "by_length": bylen,
           "leave_one_family_out": {"min_family_size": a.min_fam, "families": lofo,
                                    "mean_recall_at_P95_unweighted": round(float(np.mean([v["recall_at_P95"] for v in lofo.values()])), 3) if lofo else None,
                                    "recall_at_P95_weighted_by_family_size": round(weighted, 3) if weighted is not None else None},
           "missed_families_grouped_cv": sorted([f for f, v in byfam.items() if v["recall_at_P95"] == 0 and v["n"] >= 3])}
    (B / "reports/family_analysis.json").write_text(json.dumps(out, indent=1))
    np.save(B / "reports/oof_scores.npy", oof)
    print("\nby tier:", json.dumps(bytier))
    print("by length:", json.dumps(bylen))
    print("LOFO mean recall@P95:", out["leave_one_family_out"]["mean_recall_at_P95_unweighted"],
          "weighted:", out["leave_one_family_out"]["recall_at_P95_weighted_by_family_size"])


if __name__ == "__main__":
    main()
