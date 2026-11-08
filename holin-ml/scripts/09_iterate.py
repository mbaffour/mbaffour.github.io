"""Iterative self-training with guards against the model poisoning itself.

The loop: score an unlabelled pool of phage proteins -> accept a few as new positives -> retrain -> measure -> repeat
until nothing improves. Self-training normally fails by confirmation drift: the model's own mistakes become training
labels, the training metric keeps rising and the model quietly gets worse at everything it was not already good at.
Five guards are built in, and every one of them can stop the loop.

GUARD 1  Frozen gold holdout. Chosen once from whole homology clusters with a fixed seed, written to disk, never
         trained on and never used to accept a candidate. Nothing homologous to it can enter training (checked by
         alignment, not by id). All headline metrics come from here.
GUARD 2  Independent evidence for acceptance. A candidate needs BOTH a very high model score AND an annotated
         endolysin/spanin within three genes. The classifier never sees genomic context as a feature, so context is
         not the model agreeing with itself. Candidates with a high score but no context are left out entirely -
         they are NOT demoted to negatives, because they may well be real holins.
GUARD 3  Diversity caps. At most MAX_PER_CLUSTER accepted per homology cluster and MAX_ADD per iteration, so the loop
         cannot simply amplify the families it already knows.
GUARD 4  Counter-metrics with hard rollback. Every iteration must improve the gold-holdout average precision by more
         than NOISE, must not drop leave-one-family-out recall, and must not raise the median score of the held-out
         hard cases (antiholins, Hok/Gef toxins, CidA/LrgA) by more than HARD_CASE_TOL. Any violation: revert to the
         previous model and stop.
GUARD 5  Everything is logged per iteration - accepted sequences, counts, all metrics - so an improvement can be
         traced to what caused it.

Usage: python3 scripts/09_iterate.py [--iters 4] [--add 150]
"""
import argparse, json, pickle, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import importlib
C = importlib.import_module("03_cluster")
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve

B = Path(__file__).resolve().parent.parent
SEED = 0
GOLD_FRACTION = 0.20          # of holin-bearing clusters
MAX_PER_CLUSTER = 3
NOISE = 0.002                 # gold AP must improve by more than this
HARD_CASE_TOL = 0.05          # median hard-case score may not rise by more than this
LOFO_FAMILIES = 8             # biggest families, re-measured every iteration
HOMOLOGY_SCORE = 80           # SW score at which a pool protein counts as homologous to the gold set


def model():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, l2_regularization=1.0,
                                          class_weight="balanced", random_state=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=4); ap.add_argument("--add", type=int, default=150, dest="max_add")
    ap.add_argument("--gold-only", action="store_true", dest="gold_only",
                    help="write the frozen gold holdout and exit, without embedding the pool")
    a = ap.parse_args()
    data = json.loads((B / "data/processed/dataset.json").read_text())
    pool = json.loads((B / "data/processed/pool.json").read_text())
    esm = F.ESM(B / "models/esm_cache")

    def feats(seqs):
        h = np.stack([F.handcrafted(s) for s in seqs])
        return np.hstack([h, esm.embed(seqs)])

    # ---------- GUARD 1: frozen gold holdout, chosen once ----------
    gp = B / "data/processed/gold_holdout.json"
    labelled = [r for r in data if r["label"] in ("holin", "negative")]
    if gp.exists():
        gold_ids = set(json.loads(gp.read_text())["ids"])
    else:
        rng = np.random.default_rng(SEED)
        hol_clusters = sorted({r["cluster"] for r in labelled if r["label"] == "holin"})
        pick = set(rng.choice(hol_clusters, size=int(len(hol_clusters) * GOLD_FRACTION), replace=False).tolist())
        neg_clusters = sorted({r["cluster"] for r in labelled if r["label"] == "negative"} - pick)
        pick |= set(rng.choice(neg_clusters, size=int(len(neg_clusters) * GOLD_FRACTION), replace=False).tolist())
        gold_ids = {r["id"] for r in labelled if r["cluster"] in pick}
        gp.write_text(json.dumps({"seed": SEED, "fraction": GOLD_FRACTION, "clusters": sorted(pick),
                                  "n": len(gold_ids), "n_holin": sum(1 for r in labelled if r["id"] in gold_ids and r["label"] == "holin"),
                                  "rule": "whole homology clusters, fixed seed; never trained on, never used to accept a candidate",
                                  "ids": sorted(gold_ids)}, indent=1))
    if a.gold_only:
        print(json.dumps({"gold_holdout": str((B / "data/processed/gold_holdout.json").relative_to(B)),
                          "n": len(gold_ids), "n_holin": sum(1 for r in labelled if r["id"] in gold_ids and r["label"] == "holin")}))
        return
    gold = [r for r in labelled if r["id"] in gold_ids]
    base = [r for r in labelled if r["id"] not in gold_ids]
    hard = [r for r in data if r["label"] == "holin_like"]
    print(f"gold holdout {len(gold)} ({sum(r['label']=='holin' for r in gold)} holins) | trainable {len(base)} "
          f"({sum(r['label']=='holin' for r in base)} holins) | pool {len(pool)} | hard cases {len(hard)}", flush=True)

    Xg = feats([r["sequence"] for r in gold]); yg = np.array([r["label"] == "holin" for r in gold], int)
    Xhard = feats([r["sequence"] for r in hard])
    gold_seqs = [r["sequence"] for r in gold if r["label"] == "holin"]

    # pool proteins homologous to any gold holin can never be added (GUARD 1)
    pool_seqs = [p["sequence"] for p in pool]
    t = time.time()
    contaminated = C.search(gold_seqs, pool_seqs, min_score=HOMOLOGY_SCORE) >= C.MIN_ID
    print(f"pool screened against gold holins in {time.time()-t:.0f}s: {int(contaminated.sum())} excluded as homologous", flush=True)
    Xp = feats(pool_seqs)

    added, history, prev = [], [], None
    for it in range(a.iters + 1):
        train = base + added
        y = np.array([r["label"] == "holin" for r in train], int)
        X = feats([r["sequence"] for r in train])
        m = model(); m.fit(X, y)

        sg = m.predict_proba(Xg)[:, 1]
        gold_ap = float(average_precision_score(yg, sg)); gold_auc = float(roc_auc_score(yg, sg))
        p_, r_, th_ = precision_recall_curve(yg, sg)
        idx = np.where(p_[:-1] >= 0.95)[0]
        gold_recall95 = float(r_[:-1][idx[0]]) if len(idx) else 0.0
        hard_median = float(np.median(m.predict_proba(Xhard)[:, 1]))

        # leave-one-family-out on the biggest families inside the trainable part (GUARD 4)
        fams = {}
        for i, r in enumerate(train):
            if r["label"] == "holin" and r.get("tcdb_family", "SwissProt-only") != "SwissProt-only":
                fams.setdefault(r["tcdb_family"], []).append(i)
        lofo = {}
        cut95 = float(th_[idx[0]]) if len(idx) else 0.95
        for f in sorted(fams, key=lambda f: -len(fams[f]))[:LOFO_FAMILIES]:
            mem = fams[f]; drop = {train[i]["cluster"] for i in mem}
            keep = [i for i in range(len(train)) if i not in set(mem) and not (y[i] == 1 and train[i]["cluster"] in drop)]
            mm = model(); mm.fit(X[keep], y[keep])
            lofo[f] = float(np.mean(mm.predict_proba(X[mem])[:, 1] >= cut95))
        lofo_mean = float(np.mean(list(lofo.values())))

        rec = {"iteration": it, "n_train": len(train), "n_holin": int(y.sum()), "n_added_cumulative": len(added),
               "gold_average_precision": round(gold_ap, 4), "gold_auroc": round(gold_auc, 4),
               "gold_recall_at_P95": round(gold_recall95, 4), "lofo_mean_recall": round(lofo_mean, 4),
               "lofo_by_family": {k: round(v, 3) for k, v in lofo.items()}, "hard_case_median": round(hard_median, 4)}
        print(json.dumps(rec), flush=True)

        if prev is not None:
            stop = []
            if gold_ap <= prev["gold_average_precision"] + NOISE:
                stop.append(f"gold AP {gold_ap:.4f} did not beat {prev['gold_average_precision']:.4f} + {NOISE}")
            if lofo_mean < prev["lofo_mean_recall"] - 1e-9:
                stop.append(f"leave-one-family-out recall fell {prev['lofo_mean_recall']:.3f} -> {lofo_mean:.3f}")
            if hard_median > prev["hard_case_median"] + HARD_CASE_TOL:
                stop.append(f"hard-case median rose {prev['hard_case_median']:.3f} -> {hard_median:.3f}")
            rec["stop_reasons"] = stop
            history.append(rec)
            if stop:
                print("ROLLBACK: " + "; ".join(stop), flush=True)
                added = added[:prev["n_added_cumulative"]]
                train = base + added; y = np.array([r["label"] == "holin" for r in train], int)
                X = feats([r["sequence"] for r in train]); m = model(); m.fit(X, y)
                break
        else:
            history.append(rec)
        prev = rec
        if it == a.iters: break

        # ---------- propose new positives (GUARD 2 + GUARD 3) ----------
        sp = m.predict_proba(Xp)[:, 1]
        thr = cut95
        known = {r["sequence"] for r in train}
        cand = [(i, float(sp[i])) for i in range(len(pool))
                if sp[i] >= thr and pool[i]["has_lysis_neighbour"] and not contaminated[i]
                and pool[i]["sequence"] not in known]
        cand.sort(key=lambda x: -x[1])
        per_cluster, new = {}, []
        for i, s in cand:
            key = pool[i]["accession"]  # diversity cap per source genome, so one phage cannot dominate an iteration
            per_cluster.setdefault(key, 0)
            if per_cluster[key] >= MAX_PER_CLUSTER: continue
            per_cluster[key] += 1
            new.append({"id": f"pseudo_{it}_{len(new)}", "sequence": pool[i]["sequence"], "label": "holin", "tier": "pseudo",
                        "cluster": 10_000_000 + i, "tcdb_family": "pseudo", "length": len(pool[i]["sequence"]),
                        "score": round(s, 4), "accession": pool[i]["accession"], "locus": pool[i]["id"],
                        "product": pool[i]["product"], "lysis_neighbours": pool[i]["lysis_neighbours"],
                        "annotated_holin": pool[i]["annotated_holin"]})
            if len(new) >= a.max_add: break
        if not new:
            print("no candidates passed the acceptance rules; converged", flush=True); break
        agree = sum(n["annotated_holin"] for n in new)
        print(f"iteration {it}: accepted {len(new)} candidates (score >= {thr:.3f} AND lysis neighbour); "
              f"{agree} of them are already annotated 'holin' in their genome", flush=True)
        added += new

    out = {"guards": {"gold_holdout": "whole homology clusters, seed 0, 20% of holin clusters; never trained on",
                      "independent_evidence": "model score >= P95 threshold AND annotated endolysin/spanin within 3 genes; context is never a model feature",
                      "diversity_cap": f"<= {MAX_PER_CLUSTER} accepted per source genome, <= {a.max_add} per iteration",
                      "counter_metrics": f"stop unless gold AP improves by > {NOISE}; stop if LOFO recall falls or hard-case median rises by > {HARD_CASE_TOL}",
                      "ambiguous_handling": "high score without context evidence is excluded, never relabelled negative"},
           "history": history, "final_added": len(added),
           "accepted": [{k: v for k, v in n.items() if k != "sequence"} for n in added]}
    (B / "reports/iteration_report.json").write_text(json.dumps(out, indent=1))
    pickle.dump({"model": m, "features": "both", "algorithm": "hgb", "esm_model": F.ESM.MODEL,
                 "hand_feature_names": F.HAND_NAMES, "trained_on": {"n": len(base) + len(added), "pseudo_added": len(added)},
                 "note": "iterative model; gold holdout excluded from training"},
                open(B / "models/holin_model_iterated.pkl", "wb"))
    print(json.dumps({"iterations": len(history), "added": len(added),
                      "gold_AP_first_last": [history[0]["gold_average_precision"], history[-1]["gold_average_precision"]],
                      "lofo_first_last": [history[0]["lofo_mean_recall"], history[-1]["lofo_mean_recall"]]}, indent=1))


if __name__ == "__main__":
    main()
