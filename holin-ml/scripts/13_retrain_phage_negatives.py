"""Retrain with phage-derived negatives and judge the model on the task it is actually used for.

Two models, same recipe (handcrafted + ESM-2 features, HistGradientBoosting), differing only in training data:
  baseline  = the original 10,061 records (558 holins, 9,503 negatives: 7,884 bacterial + 1,619 phage,
              but 0 spanins and no lysis-cassette-mined hard negatives)
  phage-neg = baseline + 3,382 phage-derived negatives (101 of them Rz-like spanins)

Two evaluations, deliberately ranked:
  PRIMARY   genome scan. Rank all proteins of the 16 topology-atlas phages (1,067 proteins, 13 annotated holins)
            and measure average precision and precision/recall at thresholds. This is the deployment task: pick
            the holin out of a phage genome. None of those genomes contributed a training negative.
  SECONDARY frozen gold holdout (2,978 records, 194 holins). Its negatives are drawn from the original pool
            (bacterial + Swiss-Prot phage) and contain no mined spanin/lysis-cassette hard negatives, so it shares the
            blind spot being fixed here; it is kept only as a regression check that the old task is not broken.

Gold holdout membership is unchanged -- new negatives all receive fresh cluster ids, so the holdout is identical
across both models and the comparison is like-for-like.

Genome-level confidence intervals resample GENOMES, not proteins: proteins within one genome are not independent.

Usage: python3 scripts/13_retrain_phage_negatives.py [--boot 2000]
"""
import argparse, glob, json, os, pickle, re, sys, time
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F

B = Path(__file__).resolve().parent.parent
DSC = "/home/user/mbaffour.github.io/dirty-science-canvas"
METHODS = ("Phobius", "DeepTMHMM", "TOPCONS2")
HOLIN_WORD = re.compile(r"holin", re.I)
SPANIN = re.compile(r"spanin|\brz\b|rz1", re.I)
def hgb(): return HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_leaf_nodes=31, random_state=0)


def atlas_phages():
    """Every annotated protein of the topology-atlas phages, with its annotation and TM-method agreement."""
    out = []
    for p in sorted(glob.glob(os.path.join(DSC, "*_Topology_Lab_Reference", "data.json"))):
        d = json.load(open(p))
        if d.get("kind") != "phage": continue
        prots = []
        for r in d["proteins"]:
            prod = r.get("product") or ""
            tm = sum(1 for m in METHODS if sum(1 for s in ((r["pred"].get(m) or {}).get("spans") or [])
                                               if len(s) > 2 and s[2] == "M") >= 1)
            prots.append({"id": r["protein_id"], "gene": r.get("gene") or "", "product": prod,
                          "sequence": r["sequence"], "length": r["length"], "n_methods_membrane": tm,
                          "is_holin": bool(HOLIN_WORD.search(prod)), "is_spanin": bool(SPANIN.search(prod))})
        if prots: out.append({"key": d["key"], "organism": d["organism"], "proteins": prots})
    return out


def pr_at(y, s, thr):
    k = s >= thr; n = int(k.sum()); tp = int((k & (y == 1)).sum())
    return {"called": n, "true": tp, "precision": round(tp / n, 3) if n else None,
            "recall": round(tp / int(y.sum()), 3) if y.sum() else None}


def boot_ap(y, s, groups, n, rng):
    """Average precision with a CI from resampling genomes."""
    gs = sorted(set(groups)); vals = []
    for _ in range(n):
        pick = rng.choice(gs, size=len(gs), replace=True)
        idx = np.concatenate([np.where(groups == g)[0] for g in pick])
        if len(set(y[idx])) < 2: continue
        vals.append(average_precision_score(y[idx], s[idx]))
    return (round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)) if vals else (None, None)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    esm = F.ESM(B / "models/esm_cache")
    feats = lambda seqs: np.hstack([np.array([F.handcrafted(s) for s in seqs]), esm.embed(seqs)])

    base = json.load(open(B / "data/processed/dataset.json"))
    extra = json.load(open(B / "data/processed/phage_negatives.json"))
    gold_ids = set(json.load(open(B / "data/processed/gold_holdout.json"))["ids"])
    labelled = [r for r in base if r["label"] in ("holin", "negative")]
    gold = [r for r in labelled if r["id"] in gold_ids]
    tr_base = [r for r in labelled if r["id"] not in gold_ids]
    assert not any(r["id"] in gold_ids for r in extra)
    tr_phage = tr_base + extra
    print(f"baseline train {len(tr_base)} ({sum(r['label']=='holin' for r in tr_base)} holins) | "
          f"+phage-neg {len(tr_phage)} (+{len(extra)} negatives) | gold {len(gold)} ({sum(r['label']=='holin' for r in gold)} holins)", flush=True)

    t = time.time()
    Xb = feats([r["sequence"] for r in tr_base]); yb = np.array([r["label"] == "holin" for r in tr_base], int)
    Xe = feats([r["sequence"] for r in extra])
    Xp = np.vstack([Xb, Xe]); yp = np.concatenate([yb, np.zeros(len(extra), int)])
    Xg = feats([r["sequence"] for r in gold]); yg = np.array([r["label"] == "holin" for r in gold], int)
    print(f"features in {int(time.time()-t)}s", flush=True)

    genomes = atlas_phages()
    gp = [dict(p, phage=g["key"]) for g in genomes for p in g["proteins"]]
    Xs = feats([p["sequence"] for p in gp])
    ys = np.array([p["is_holin"] for p in gp], int)
    grp = np.array([g["key"] for g in genomes for _ in g["proteins"]])
    print(f"genome scan set: {len(genomes)} phages, {len(gp)} proteins, {int(ys.sum())} annotated holins", flush=True)

    rng = np.random.default_rng(0)
    res = {}
    for name, X, y in (("baseline", Xb, yb), ("phage_negatives", Xp, yp)):
        m = hgb().fit(X, y)
        sg = m.predict_proba(Xg)[:, 1]; ss = m.predict_proba(Xs)[:, 1]
        lo, hi = boot_ap(ys, ss, grp, a.boot, np.random.default_rng(0))
        p_, r_, th_ = precision_recall_curve(yg, sg); i95 = np.where(p_[:-1] >= 0.95)[0]
        res[name] = {
            "genome_scan_PRIMARY": {
                "average_precision": round(float(average_precision_score(ys, ss)), 4),
                "average_precision_CI95_by_genome": [lo, hi],
                "at_thresholds": {str(t_): pr_at(ys, ss, t_) for t_ in (0.5, 0.9, 0.95)},
                "median_score_annotated_holins": round(float(np.median(ss[ys == 1])), 4),
                "median_score_spanins": round(float(np.median(ss[[p["is_spanin"] for p in gp]])), 4),
                "n_spanins_over_0.5": int(sum(1 for p, s in zip(gp, ss) if p["is_spanin"] and s >= 0.5)),
                "n_false_positives_over_0.9": int(((ss >= 0.9) & (ys == 0)).sum()),
                "holins_ranked": sorted([{"phage": p["phage"], "gene": p["gene"] or p["id"], "length": p["length"],
                                          "score": round(float(sc), 3), "rank_overall": int((ss > sc).sum()) + 1,
                                          "rank_in_genome": int((ss[grp == p["phage"]] > sc).sum()) + 1,
                                          "n_methods_membrane": p["n_methods_membrane"]}
                                         for p, sc in zip(gp, ss) if p["is_holin"]], key=lambda d: d["rank_overall"])},
            "gold_holdout_SECONDARY": {
                "average_precision": round(float(average_precision_score(yg, sg)), 4),
                "auroc": round(float(roc_auc_score(yg, sg)), 4),
                "recall_at_P95": round(float(r_[:-1][i95[0]]), 4) if len(i95) else 0.0,
                "threshold_P95": round(float(th_[i95[0]]), 4) if len(i95) else None}}
        print(f"\n== {name}\n  PRIMARY genome scan AP {res[name]['genome_scan_PRIMARY']['average_precision']} "
              f"CI95 {res[name]['genome_scan_PRIMARY']['average_precision_CI95_by_genome']}", flush=True)
        for k, v in res[name]["genome_scan_PRIMARY"]["at_thresholds"].items():
            print(f"    >={k}: called {v['called']:>3} true {v['true']:>2} precision {v['precision']} recall {v['recall']}")
        print(f"    spanin median {res[name]['genome_scan_PRIMARY']['median_score_spanins']}, "
              f"spanins>=0.5 {res[name]['genome_scan_PRIMARY']['n_spanins_over_0.5']}, "
              f"false positives>=0.9 {res[name]['genome_scan_PRIMARY']['n_false_positives_over_0.9']}")
        print(f"  SECONDARY gold AP {res[name]['gold_holdout_SECONDARY']['average_precision']} "
              f"recall@P95 {res[name]['gold_holdout_SECONDARY']['recall_at_P95']}", flush=True)
        if name == "phage_negatives":
            pickle.dump({"model": m, "features": "both", "algorithm": "hgb", "esm_model": F.ESM.MODEL,
                         "hand_feature_names": F.HAND_NAMES,
                         "trained_on": {"n": len(tr_phage), "n_holin": int(yp.sum()), "phage_negatives": len(extra)},
                         "note": "trained with phage-derived negatives; gold holdout excluded"},
                        open(B / "models/holin_model_phageneg.pkl", "wb"))
    delta = {"genome_scan_AP": [res["baseline"]["genome_scan_PRIMARY"]["average_precision"],
                               res["phage_negatives"]["genome_scan_PRIMARY"]["average_precision"]],
             "gold_AP": [res["baseline"]["gold_holdout_SECONDARY"]["average_precision"],
                         res["phage_negatives"]["gold_holdout_SECONDARY"]["average_precision"]],
             "spanins_over_0.5": [res["baseline"]["genome_scan_PRIMARY"]["n_spanins_over_0.5"],
                                  res["phage_negatives"]["genome_scan_PRIMARY"]["n_spanins_over_0.5"]]}
    (B / "reports/phage_negatives_eval.json").write_text(json.dumps(
        {"design": {"primary": "genome scan over 16 atlas phages, none of which contributed a training negative",
                    "secondary": "frozen gold holdout; original negatives (no mined spanin/lysis hard negatives), a regression check",
                    "ci": "95% percentile bootstrap resampling genomes, not proteins"},
         "models": res, "baseline_to_phage_negatives": delta}, indent=2))
    print("\n" + json.dumps(delta, indent=1))


if __name__ == "__main__":
    main()
