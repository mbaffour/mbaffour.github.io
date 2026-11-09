"""Does adding TM-anchored local features recover the long holins? Leave-one-genome-out, phage negatives in both.

Both arms train on the same records (original training set minus the gold holdout, plus the 3,382 phage-derived
negatives) and differ only in the features:
  pooled  = handcrafted(36) + mean-pooled ESM of the whole protein(480)                      -- the current model
  local   = the above + TM-anchored local features(17) + ESM of the anchor TM +/- 40 aa(480)

The target is the failure this was built for: T4 holin T and T5 C1, both ~218 aa with a single N-terminal TM and a
long C-terminal tail, which the pooled model scores 0.0000 out of family. Each genome's holin family is removed
from training before that genome is scored, exactly as in scripts/14.


The naive genome scan is worthless as a generalization test. The holins of the classic phages -- lambda S,
P22 13, T7, T4 t, T5 C1, P1 lydA/lydD, SPP1, HK97, PRD1, phi29 gp14 -- are themselves Swiss-Prot/TCDB training
examples, so a model trained on them scores every one at 1.000 and the scan reports perfect recall by
memorization. Any claim of "n of 13 holins recovered" from such a scan says nothing about a novel phage.

Here, for each of the 16 atlas phages in turn:
  1. every training holin in the same family as one of that genome's annotated holins is found by
     Smith-Waterman (identity >= MIN_ID at coverage >= MIN_COV),
  2. those holins' ENTIRE homology clusters are removed from the training set, so no close relative remains,
  3. a model is fitted on what is left and used to score that genome's proteins.
Scores are therefore out-of-family for the holin being looked for, which is the situation a new phage presents.

Run for both training sets (with and without phage-derived negatives) so the comparison is like-for-like.
Confidence intervals resample genomes, since proteins within a genome are not independent.

Usage: python3 scripts/14_genome_loo_eval.py [--boot 2000]
"""
import argparse, glob, importlib, json, os, re, sys, time
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
CL = importlib.import_module("03_cluster")

B = Path(__file__).resolve().parent.parent
DSC = "/home/user/mbaffour.github.io/dirty-science-canvas"
METHODS = ("Phobius", "DeepTMHMM", "TOPCONS2")
HOLIN_WORD = re.compile(r"holin", re.I)
SPANIN = re.compile(r"spanin|\brz\b|rz1", re.I)
def hgb(): return HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_leaf_nodes=31, random_state=0)


def atlas_phages():
    out = []
    for p in sorted(glob.glob(os.path.join(DSC, "*_Topology_Lab_Reference", "data.json"))):
        d = json.load(open(p))
        if d.get("kind") != "phage": continue
        ps = []
        for r in d["proteins"]:
            prod = r.get("product") or ""
            tm = sum(1 for m in METHODS if sum(1 for s in ((r["pred"].get(m) or {}).get("spans") or [])
                                               if len(s) > 2 and s[2] == "M") >= 1)
            ps.append({"id": r["protein_id"], "gene": r.get("gene") or r["protein_id"], "product": prod,
                       "sequence": r["sequence"], "length": r["length"], "n_methods_membrane": tm,
                       "is_holin": bool(HOLIN_WORD.search(prod)), "is_spanin": bool(SPANIN.search(prod)),
                       "phage": d["key"]})
        if ps: out.append({"key": d["key"], "organism": d["organism"], "proteins": ps})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    esm = F.ESM(B / "models/esm_cache")

    base = json.load(open(B / "data/processed/dataset.json"))
    extra = json.load(open(B / "data/processed/phage_negatives.json"))
    gold_ids = set(json.load(open(B / "data/processed/gold_holdout.json"))["ids"])
    tr = [r for r in base if r["label"] in ("holin", "negative") and r["id"] not in gold_ids]
    genomes = atlas_phages()
    gp = [p for g in genomes for p in g["proteins"]]
    print(f"train {len(tr)} ({sum(r['label']=='holin' for r in tr)} holins) | phage negatives {len(extra)} | "
          f"{len(genomes)} phages, {len(gp)} proteins, {sum(p['is_holin'] for p in gp)} annotated holins", flush=True)

    def pooled(seqs): return np.hstack([np.array([F.handcrafted(s) for s in seqs]), esm.embed(seqs)])

    def localised(seqs):
        lv, win = [], []
        for s in seqs:
            v, w = F.local(s); lv.append(v); win.append(w)
        return np.hstack([pooled(seqs), np.array(lv), esm.embed(win)])

    tr_seqs = [r["sequence"] for r in tr]; ex_seqs = [r["sequence"] for r in extra]
    g_seqs = [p["sequence"] for p in gp]
    t0 = time.time()
    FS = {"pooled": (pooled(tr_seqs), pooled(ex_seqs), pooled(g_seqs))}
    print(f"  pooled features in {int(time.time()-t0)}s", flush=True)
    t0 = time.time()
    FS["local"] = (localised(tr_seqs), localised(ex_seqs), localised(g_seqs))
    print(f"  local features in {int(time.time()-t0)}s ({FS['local'][0].shape[1]} dims)", flush=True)
    ytr = np.array([r["label"] == "holin" for r in tr], int)
    Xtr, Xex, Xg = FS["pooled"]
    cl = np.array([r["cluster"] for r in tr])

    # which training clusters must go, per genome: those holding a holin in the same family as a holin of that genome
    hol_idx = [i for i, r in enumerate(tr) if r["label"] == "holin"]
    hol_seqs = [tr[i]["sequence"] for i in hol_idx]
    drop_clusters, rep = {}, {}
    for g in genomes:
        qs = [p["sequence"] for p in g["proteins"] if p["is_holin"]]
        if not qs: drop_clusters[g["key"]] = set(); rep[g["key"]] = {"annotated_holins": 0, "clusters_removed": 0, "holins_removed": 0}; continue
        ident = CL.search(qs, hol_seqs, 80)          # identity of each training holin to this genome's holins
        hit = [hol_idx[i] for i, v in enumerate(ident) if v >= CL.MIN_ID]
        dc = {tr[i]["cluster"] for i in hit}
        drop_clusters[g["key"]] = dc
        rep[g["key"]] = {"annotated_holins": len(qs), "clusters_removed": len(dc),
                         "holins_removed": int(sum(1 for i in hol_idx if tr[i]["cluster"] in dc))}
        print(f"  {g['key']:<9} {len(qs)} annotated holin(s) -> remove {len(dc)} cluster(s), "
              f"{rep[g['key']]['holins_removed']} training holins", flush=True)

    out = {}
    for name in ("pooled", "local"):
        Xtr, Xex, Xg = FS[name]
        addX, addy = Xex, np.zeros(len(extra), int)
        scores = np.zeros(len(gp)); t0 = time.time()
        for g in genomes:
            keep = ~np.isin(cl, list(drop_clusters[g["key"]])) if drop_clusters[g["key"]] else np.ones(len(tr), bool)
            X, y = Xtr[keep], ytr[keep]
            if addX is not None: X, y = np.vstack([X, addX]), np.concatenate([y, addy])
            m = hgb().fit(X, y)
            sel = [i for i, p in enumerate(gp) if p["phage"] == g["key"]]
            scores[sel] = m.predict_proba(Xg[sel])[:, 1]
        y = np.array([p["is_holin"] for p in gp], int)
        grp = np.array([p["phage"] for p in gp])
        rngb = np.random.default_rng(0); gs = sorted(set(grp)); vals = []
        for _ in range(a.boot):
            pick = rngb.choice(gs, size=len(gs), replace=True)
            idx = np.concatenate([np.where(grp == q)[0] for q in pick])
            if len(set(y[idx])) > 1: vals.append(average_precision_score(y[idx], scores[idx]))
        thr = {}
        for t_ in (0.5, 0.9, 0.95):
            k = scores >= t_; n = int(k.sum()); tp = int((k & (y == 1)).sum())
            thr[str(t_)] = {"called": n, "true": tp, "precision": round(tp / n, 3) if n else None,
                            "recall": round(tp / int(y.sum()), 3)}
        ranked = sorted([{"phage": p["phage"], "gene": p["gene"][:14], "length": p["length"],
                          "score": round(float(s), 4), "rank_in_genome": int((scores[grp == p["phage"]] > s).sum()) + 1,
                          "n_in_genome": int((grp == p["phage"]).sum()), "n_methods_membrane": p["n_methods_membrane"]}
                         for p, s in zip(gp, scores) if p["is_holin"]], key=lambda d: -d["score"])
        sp = [s for p, s in zip(gp, scores) if p["is_spanin"]]
        out[name] = {"average_precision": round(float(average_precision_score(y, scores)), 4),
                     "average_precision_CI95_by_genome": [round(float(np.percentile(vals, 2.5)), 4),
                                                          round(float(np.percentile(vals, 97.5)), 4)] if vals else None,
                     "at_thresholds": thr, "top1_per_genome_hit_rate": round(float(np.mean(
                         [1.0 if any(h["rank_in_genome"] == 1 for h in ranked if h["phage"] == k_) else 0.0
                          for k_ in sorted({p["phage"] for p in gp if p["is_holin"]})])), 3),
                     "median_holin_rank_in_genome": int(np.median([h["rank_in_genome"] for h in ranked])),
                     "spanin_median": round(float(np.median(sp)), 4), "spanins_over_0.5": int(sum(1 for s in sp if s >= 0.5)),
                     "false_positives_over_0.9": int(((scores >= 0.9) & (y == 0)).sum()), "holins": ranked,
                     "fit_seconds": int(time.time() - t0)}
        r = out[name]
        print(f"\n== {name} (leave-one-genome-out)  AP {r['average_precision']} CI95 {r['average_precision_CI95_by_genome']}", flush=True)
        for k, v in thr.items(): print(f"    >={k}: called {v['called']:>3} true {v['true']:>2} precision {v['precision']} recall {v['recall']}")
        print(f"    top-1 in genome: {r['top1_per_genome_hit_rate']}, median holin rank {r['median_holin_rank_in_genome']}, "
              f"spanins>=0.5 {r['spanins_over_0.5']}, FP>=0.9 {r['false_positives_over_0.9']}")
    (B / "reports/genome_loo_local.json").write_text(json.dumps(
        {"design": {"what": "leave-one-genome-out, phage negatives in both arms; pooled vs TM-anchored local features",
                    "why": "the classic phage holins are themselves training examples; a plain scan scores them "
                           "1.000 and reports perfect recall by memorization",
                    "removal_rule": f"SW identity >= {CL.MIN_ID} at coverage >= {CL.MIN_COV} to an annotated holin "
                                    f"of that genome, then the whole homology cluster",
                    "ci": "95% percentile bootstrap resampling genomes"},
         "per_genome_removal": rep, "models": out}, indent=2))
    print("\n" + json.dumps({k: {"AP": v["average_precision"], "CI": v["average_precision_CI95_by_genome"],
                                 "recall@0.9": v["at_thresholds"]["0.9"]["recall"],
                                 "precision@0.9": v["at_thresholds"]["0.9"]["precision"],
                                 "top1": v["top1_per_genome_hit_rate"]} for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main()
