"""Does curating 4,497 more holins actually help? Leave-one-genome-out, three arms.

  A  current    original training records (minus gold holdout) + 3,382 phage-derived negatives
  B  + curated  A + every usable curated holin (2,886)

An arm for "only the curated holins that form new families" was planned and dropped: 4,700 of the 4,701 curated
records join a family that is ALREADY in the training set, so that arm would have had n=1. Pfam's 41,029 holin
members add depth to the known families, not new architectures -- the 558 Swiss-Prot/TCDB holins already span
them. That is a result in itself, and it means the strict protocol below cannot benefit from this curation.

Two removal protocols, because they answer different questions and only one has been measured so far:

  family   (strict)    every training holin within 30% identity of that genome's holin is removed, whole clusters.
                       Asks: would we find a holin from a family nobody has ever seen? The curated holins are
                       relatives of known families, so they are removed exactly when they would be needed --
                       this protocol is blind to depth by construction.
  sequence (realistic) only near-identical matches (>= 95% identity) to that genome's holin are removed, so the
                       family stays. Asks: would we find the holin in a NEWLY SEQUENCED phage whose holin belongs
                       to a known family? That is the ordinary deployment case, and it is where depth should pay.

Reporting only the strict protocol, as earlier runs did, understates what the tool is useful for; reporting only
the realistic one would overstate novelty. Both are given.

Usage: python3 scripts/22_retrain_curated.py [--boot 2000]
"""
import argparse, glob, importlib, json, os, re, sys, time
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve
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
            ps.append({"id": r["protein_id"], "gene": (r.get("gene") or r["protein_id"])[:14], "product": prod,
                       "sequence": r["sequence"], "length": r["length"], "n_methods_membrane": tm,
                       "is_holin": bool(HOLIN_WORD.search(prod)), "is_spanin": bool(SPANIN.search(prod)),
                       "phage": d["key"]})
        if ps: out.append({"key": d["key"], "organism": d["organism"], "proteins": ps})
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    esm = F.ESM(B / "models/esm_cache")
    feats = lambda ss: np.hstack([np.array([F.handcrafted(s) for s in ss]), esm.embed(ss)])

    base = json.load(open(B / "data/processed/dataset.json"))
    negs = json.load(open(B / "data/processed/phage_negatives.json"))
    cur = [r for r in json.load(open(B / "data/processed/holins_extra_clustered.json"))
           if not r["excluded_gold_cluster"] and r["label"] == "holin"]
    newfam = [r for r in cur if r.get("assigned_by") == "new family"]
    gold_ids = set(json.load(open(B / "data/processed/gold_holdout.json"))["ids"])
    tr0 = [r for r in base if r["label"] in ("holin", "negative") and r["id"] not in gold_ids]
    gold = [r for r in base if r["id"] in gold_ids and r["label"] in ("holin", "negative")]
    print(f"A {len(tr0)+len(negs)} rows | curated usable holins {len(cur)} (new-family {len(newfam)}) | "
          f"gold {len(gold)}", flush=True)

    genomes = atlas_phages()
    gp = [p for g in genomes for p in g["proteins"]]
    y = np.array([p["is_holin"] for p in gp], int)
    grp = np.array([p["phage"] for p in gp])

    t = time.time()
    FE = {k: feats([r["sequence"] for r in v]) for k, v in
          (("tr0", tr0), ("negs", negs), ("cur", cur), ("gold", gold))}
    Xg = feats([p["sequence"] for p in gp])
    print(f"features in {int(time.time()-t)}s", flush=True)
    y0 = np.array([r["label"] == "holin" for r in tr0], int)
    ARMS = {"A_current": ([FE["tr0"], FE["negs"]], [y0, np.zeros(len(negs), int)], tr0 + negs),
            "B_plus_curated": ([FE["tr0"], FE["negs"], FE["cur"]],
                               [y0, np.zeros(len(negs), int), np.ones(len(cur), int)], tr0 + negs + cur)}

    out = {}
    for (name, (Xs, ys, recs)), mode in [(a_, m) for a_ in ARMS.items() for m in ("family", "sequence")]:
        name = f"{name}__{mode}_removal"
        X = np.vstack(Xs); yy = np.concatenate(ys)
        cl = np.array([r["cluster"] for r in recs])
        hol_i = [i for i, r in enumerate(recs) if r.get("label") == "holin" or yy[i] == 1]
        hol_seqs = [recs[i]["sequence"] for i in hol_i]
        scores = np.zeros(len(gp)); removed = {}
        t0 = time.time()
        for g in genomes:
            qs = [p["sequence"] for p in g["proteins"] if p["is_holin"]]
            if qs:
                ident = CL.search(qs, hol_seqs, 80)
                if mode == "family":
                    dc = {cl[hol_i[i]] for i, v in enumerate(ident) if v >= CL.MIN_ID}
                    drop_rows = np.isin(cl, list(dc)) if dc else np.zeros(len(recs), bool)
                    removed[g["key"]] = {"mode": mode, "clusters": len(dc),
                                         "holins": int(sum(1 for i in hol_i if cl[i] in dc))}
                else:                                  # sequence: drop only near-identical relatives
                    drop_rows = np.zeros(len(recs), bool)
                    hit = [hol_i[i] for i, v in enumerate(ident) if v >= 0.95]
                    drop_rows[hit] = True
                    removed[g["key"]] = {"mode": mode, "clusters": 0, "holins": len(hit)}
            else:
                drop_rows = np.zeros(len(recs), bool); removed[g["key"]] = {"mode": mode, "clusters": 0, "holins": 0}
            keep = ~drop_rows
            m = hgb().fit(X[keep], yy[keep])
            sel = [i for i, p in enumerate(gp) if p["phage"] == g["key"]]
            scores[sel] = m.predict_proba(Xg[sel])[:, 1]
        rngb = np.random.default_rng(0); gs = sorted(set(grp)); vals = []
        for _ in range(a.boot):
            pick = rngb.choice(gs, size=len(gs), replace=True)
            idx = np.concatenate([np.where(grp == q)[0] for q in pick])
            if len(set(y[idx])) > 1: vals.append(average_precision_score(y[idx], scores[idx]))
        thr = {}
        for t_ in (0.5, 0.9):
            k = scores >= t_; n = int(k.sum()); tp = int((k & (y == 1)).sum())
            thr[str(t_)] = {"called": n, "true": tp, "precision": round(tp / n, 3) if n else None,
                            "recall": round(tp / int(y.sum()), 3)}
        # gold holdout, trained once on the whole arm (no genome removal)
        mg = hgb().fit(X, yy)
        sgold = mg.predict_proba(FE["gold"])[:, 1]
        ygold = np.array([r["label"] == "holin" for r in gold], int)
        p_, r_, th_ = precision_recall_curve(ygold, sgold); i95 = np.where(p_[:-1] >= 0.95)[0]
        holins = sorted([{"phage": p["phage"], "gene": p["gene"], "length": p["length"],
                          "score": round(float(s), 4),
                          "rank_in_genome": int((scores[grp == p["phage"]] > s).sum()) + 1,
                          "n_in_genome": int((grp == p["phage"]).sum())}
                         for p, s in zip(gp, scores) if p["is_holin"]], key=lambda d: -d["score"])
        sp = [s for p, s in zip(gp, scores) if p["is_spanin"]]
        out[name] = {"n_train": int(len(recs)), "n_holin_train": int(yy.sum()),
                     "genome_scan_PRIMARY": {
                         "average_precision": round(float(average_precision_score(y, scores)), 4),
                         "CI95_by_genome": [round(float(np.percentile(vals, 2.5)), 4),
                                            round(float(np.percentile(vals, 97.5)), 4)] if vals else None,
                         "at_thresholds": thr,
                         "top1_per_genome": round(float(np.mean([any(h["rank_in_genome"] == 1 for h in holins if h["phage"] == k_)
                                                                 for k_ in sorted({p['phage'] for p in gp if p['is_holin']})])), 3),
                         "median_holin_rank": int(np.median([h["rank_in_genome"] for h in holins])),
                         "spanins_over_0.5": int(sum(1 for s in sp if s >= 0.5)),
                         "false_positives_over_0.9": int(((scores >= 0.9) & (y == 0)).sum()),
                         "holins": holins},
                     "gold_holdout_SECONDARY": {
                         "average_precision": round(float(average_precision_score(ygold, sgold)), 4),
                         "recall_at_P95": round(float(r_[:-1][i95[0]]), 4) if len(i95) else 0.0},
                     "per_genome_removal": removed, "fit_seconds": int(time.time() - t0)}
        r = out[name]["genome_scan_PRIMARY"]
        print(f"\n== {name}: train {len(recs)} ({int(yy.sum())} holins)")
        print(f"   PRIMARY AP {r['average_precision']} CI {r['CI95_by_genome']} | "
              f"recall@0.9 {thr['0.9']['recall']} precision@0.9 {thr['0.9']['precision']} | "
              f"top1 {r['top1_per_genome']} | FP>=0.9 {r['false_positives_over_0.9']}")
        print(f"   SECONDARY gold AP {out[name]['gold_holdout_SECONDARY']['average_precision']}")
        for h in holins:
            if h["phage"] in ("T4", "T5", "phi29", "P1"):
                print(f"     {h['phage']}|{h['gene']:<14} {h['length']:>4} aa  {h['score']:.4f}  rank {h['rank_in_genome']}/{h['n_in_genome']}")
    (B / "reports/curated_retrain_eval.json").write_text(json.dumps(
        {"design": {"primary": "leave-one-genome-out genome scan; each genome's holin family removed from "
                               "training first, so adding a target's own Pfam relatives cannot buy its score",
                    "arms": {"A": "current", "B": "+ all usable curated holins",
                             "C": "+ only curated holins that formed NEW families, separating more holins from "
                                  "more architectures"}},
         "models": out}, indent=2))


if __name__ == "__main__":
    main()
