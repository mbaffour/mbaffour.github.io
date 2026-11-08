"""Train and honestly evaluate holin classifiers.

Evaluation is grouped by homology cluster (GroupKFold): no sequence in a test fold has a >=30% identity / >=50% coverage
local alignment to any training sequence, so scores are not inflated by near-duplicates.

Three feature sets are compared, plus a homology baseline that the ML model must beat to be worth anything:
  hand  - interpretable biophysical features (length, hydropathy TM segments, terminal charge, composition)
  esm   - ESM-2 (35M) mean-pooled embeddings
  both  - concatenation
  blast-like baseline - max Smith-Waterman identity to the training holins of the same fold (no ML)

'holin_like' sequences (antiholins that are not dual-start holin genes, bacterial CidA/LrgA, toxins, GTA and spore
holin-like families) are held out of training and scored separately as a hard-case set.
Usage: python3 scripts/04_train.py [--quick]
"""
import json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve

B = Path(__file__).resolve().parent.parent
QUICK = "--quick" in sys.argv


def load():
    data = json.loads((B / "data/processed/dataset.json").read_text())
    if "cluster" not in data[0]: sys.exit("run scripts/03_cluster.py first")
    return data


def metrics(y, s):
    out = {"auroc": float(roc_auc_score(y, s)), "average_precision": float(average_precision_score(y, s))}
    p, r, t = precision_recall_curve(y, s)
    for target in (0.90, 0.95, 0.99):
        ok = r[:-1][p[:-1] >= target]
        out[f"recall_at_precision_{int(target * 100)}"] = float(ok.max()) if len(ok) else 0.0
    out["precision_at_recall_50"] = float(p[:-1][r[:-1] >= 0.5].max()) if (r[:-1] >= 0.5).any() else 0.0
    return out


def main():
    data = load()
    train = [r for r in data if r["label"] in ("holin", "negative")]
    hard = [r for r in data if r["label"] == "holin_like"]
    y = np.array([r["label"] == "holin" for r in train], int)
    groups = np.array([r["cluster"] for r in train])
    seqs = [r["sequence"] for r in train]
    print(f"{len(train)} training sequences ({y.sum()} holins), {len(set(groups))} clusters, {len(hard)} holin-like held out", flush=True)

    t = time.time(); Xh = np.stack([F.handcrafted(s) for s in seqs]); print(f"handcrafted {Xh.shape} in {time.time()-t:.1f}s", flush=True)
    esm = F.ESM(B / "models/esm_cache")
    t = time.time(); Xe = esm.embed(seqs); print(f"esm {Xe.shape} in {time.time()-t:.1f}s", flush=True)
    Xhard_h = np.stack([F.handcrafted(r["sequence"]) for r in hard]); Xhard_e = esm.embed([r["sequence"] for r in hard])
    FEATS = {"hand": (Xh, Xhard_h), "esm": (Xe, Xhard_e), "both": (np.hstack([Xh, Xe]), np.hstack([Xhard_h, Xhard_e]))}
    MODELS = {"logreg": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=4000, C=1.0, class_weight="balanced")),
              "hgb": lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, l2_regularization=1.0,
                                                            class_weight="balanced", random_state=0)}
    if QUICK: MODELS.pop("hgb")
    n_splits = 5
    cv = list(GroupKFold(n_splits=n_splits).split(np.zeros(len(y)), y, groups))
    report = {"n_train": len(train), "n_holin": int(y.sum()), "n_clusters": int(len(set(groups))), "n_holin_like_heldout": len(hard),
              "cv": f"GroupKFold({n_splits}) on homology clusters", "results": {}, "hard_case_scores": {}}

    # homology baseline: max SW identity to the fold's training holins
    import importlib
    C = importlib.import_module("03_cluster")
    t = time.time(); base = np.zeros(len(y))
    for tr, te in cv:
        q = [seqs[i] for i in tr if y[i] == 1]
        base[te] = C.search(q, [seqs[i] for i in te], min_score=0)
    report["results"]["homology_baseline (max SW identity to fold's training holins)"] = metrics(y, base)
    print("homology baseline", json.dumps(report["results"]["homology_baseline (max SW identity to fold's training holins)"]), f"{time.time()-t:.0f}s", flush=True)

    best = None
    for fname, (X, Xhard) in FEATS.items():
        for mname, mk in MODELS.items():
            t = time.time(); oof = np.zeros(len(y))
            for tr, te in cv:
                m = mk(); m.fit(X[tr], y[tr]); oof[te] = m.predict_proba(X[te])[:, 1]
            mt = metrics(y, oof); mt["seconds"] = round(time.time() - t, 1)
            report["results"][f"{fname}+{mname}"] = mt
            print(f"{fname}+{mname}", json.dumps({k: round(v, 4) for k, v in mt.items()}), flush=True)
            if best is None or mt["average_precision"] > best[0]: best = (mt["average_precision"], fname, mname, X, Xhard)
            # per-tier recall at a fixed high-precision threshold
            p, r, th = precision_recall_curve(y, oof)
            idx = np.where(p[:-1] >= 0.95)[0]
            if len(idx):
                cut = th[idx[0]]
                mt["tier_recall_at_precision_95"] = {tier: round(float(np.mean([oof[i] >= cut for i, rr in enumerate(train) if rr.get("tier") == tier])), 3)
                                                     for tier in ("tested", "curated", "putative")}
    _, fname, mname, X, Xhard = best
    final = MODELS[mname](); final.fit(X, y)
    import pickle
    (B / "models").mkdir(exist_ok=True)
    (B / "models/holin_model.pkl").write_bytes(pickle.dumps({"model": final, "features": fname, "algorithm": mname,
                                                             "hand_feature_names": F.HAND_NAMES, "esm_model": F.ESM.MODEL,
                                                             "trained_on": {"n": len(train), "n_holin": int(y.sum())}}))
    hs = final.predict_proba(Xhard)[:, 1]
    import collections
    byreason = collections.defaultdict(list)
    for r, s in zip(hard, hs):
        byreason[r["sources"][0].get("holin_like_reason", "?")].append(float(s))
    report["best_model"] = {"features": fname, "algorithm": mname}
    report["hard_case_scores"] = {k: {"n": len(v), "median_score": round(float(np.median(v)), 3), "frac_above_0.5": round(float(np.mean(np.array(v) > 0.5)), 3)}
                                  for k, v in sorted(byreason.items())}
    (B / "reports/training_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"best": report["best_model"], "hard_cases": report["hard_case_scores"]}, indent=2))


if __name__ == "__main__":
    main()
