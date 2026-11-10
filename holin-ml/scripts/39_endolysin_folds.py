"""Per-fold endolysin models: make the disjunction explicit in the architecture instead of inside one model.

WHY. "Endolysin" is not one learnable class. It is five unrelated catalytic folds that share only a substrate,
and a single one-vs-rest classifier is being asked to learn their disjunction. Three results say so:
  - adding 14 catalytic families made the single model WORSE, not better (reports/retrain_v2_report.md:
    strict AP 0.729 -> 0.652), while the same kind of expansion IMPROVED spanin, a genuine structural class;
  - DAC15 gp039 scored 0.0059 while the model held a training positive 80.3% identical to it at full coverage;
  - Serwaa CPT_Serwaa_011 scored 0.3641 and ranked 6th behind a head-tail joining protein at 0.9692, with its
    nearest training endolysin 50.4% identical -- so not a coverage gap, a model failure.

DESIGN.
  1. Folds are assigned by our own HMM scan (scripts/domains.py), not by the record's provenance string, so
     reviewed/curated/pool positives are assigned on the same footing as Pfam-tier ones. A modular lysin hitting
     two catalytic folds belongs to BOTH -- that is real biology, not a labelling problem.
  2. One one-vs-rest model per fold. Positives = that fold. Negatives = holins, spanins, bacterial and phage
     negatives -- NOT the other folds' endolysins. Those are EXCLUDED from both classes, applying the lesson the
     confusables experiment taught: a protein you cannot separate from the target by the available features
     poisons the boundary when labelled negative, and a different-fold endolysin is still an endolysin.
  3. Combination is MAX over folds. A protein is an endolysin if it looks like ANY fold, so max is the natural
     disjunction operator; this is the whole point of the redesign.
  4. Negatives are subsampled per fold to a bounded ratio. With a few hundred positives per fold, all ~16k
     negatives are wasteful; AP on the genome scan is rank-based, so training-set subsampling changes the model,
     not the fairness of the metric.

EVALUATION is deliberately identical to scripts/28 so the numbers are comparable to the shipped single model:
leave-one-genome-out over the atlas phages that carry an annotated endolysin, with both removal protocols
(family = drop every training positive >=30% identical to the genome's annotated endolysin; sequence = drop only
>=95% near-duplicates). Each genome's removal is applied to EVERY fold model before that genome is scored.

Usage: python3 scripts/39_endolysin_folds.py [--boot 2000] [--neg-ratio 8] [--min-fold 40]
Writes models/endolysin_folds.pkl and reports/endolysin_folds_eval.json
"""
import argparse, importlib, json, pickle, sys, time
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import domains as D
CL = importlib.import_module("03_cluster")
S28 = importlib.import_module("28_train_eval_lysis")

B = Path(__file__).resolve().parent.parent
FOLD = {
    "glycosidase":      ["PF00959", "PF01183", "PF01832", "PF05838", "PF13702", "PF11860"],
    "transglycosylase": ["PF01464", "PF06737", "PF13406", "PF19489"],
    "amidase":          ["PF01510", "PF01520", "PF05382", "PF07313"],
    "endopeptidase":    ["PF05257", "PF00877", "PF01551", "PF02557", "PF08291", "PF13539"],
    "other_cwh":        ["PF07486", "PF31186", "PF25309", "PF31067"],
}
OF = {acc: f for f, accs in FOLD.items() for acc in accs}


def hgb():
    return HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_leaf_nodes=31, random_state=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--neg-ratio", type=int, default=8)
    ap.add_argument("--arch", choices=["folds", "single", "routed"], default="folds",
                    help="CONTROL: 'single' runs one pooled model through the identical code path, negatives, "
                         "subsampling rule and removal protocol, so the only thing that differs is the "
                         "architecture. Without this the per-fold numbers are confounded by the per-fold "
                         "negative budget and cannot be compared with the shipped model. 'routed' is the "
                         "design the evidence points to: a protein whose HMM scan confirms a catalytic fold is "
                         "scored by THAT fold's model; one with no domain falls back to the pooled model. "
                         "Max-over-all-folds gives six chances to produce a false positive, which is why pure "
                         "'folds' inflates known false positives (Serwaa head-tail 0.969 -> 1.000).")
    ap.add_argument("--tag", default="")
    ap.add_argument("--min-fold", type=int, default=40, help="a fold with fewer positives is folded into "
                                                             "'unassigned' rather than given its own model")
    a = ap.parse_args()

    pos = json.load(open(B / "data/processed/endolysin_positives.json"))
    spa = json.load(open(B / "data/processed/spanin_positives.json"))
    base = json.load(open(B / "data/processed/dataset.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))
    negs = json.load(open(B / "data/processed/phage_negatives.json"))
    holins = [r for r in base if r["label"] == "holin"] + [r for r in cur if r["label"] == "holin"]
    bact = [r for r in base if r["label"] == "negative"]

    # ---- 1. assign folds by HMM scan of the positives themselves ----
    t = time.time()
    hmms, cls_of = D.lysis_hmms()
    hits = D.scan({f"p{i}": r["sequence"] for i, r in enumerate(pos)}, hmms, cls_of)
    folds_of = {}
    for i, r in enumerate(pos):
        fs = {OF[h["pfam"]] for h in hits.get(f"p{i}", [])
              if h["pfam"] in OF and h["grade"] == "catalytic" and h["ievalue"] <= 1e-5}
        folds_of[i] = fs or {"unassigned"}
    counts = {}
    for i in folds_of:
        for f in folds_of[i]: counts[f] = counts.get(f, 0) + 1
    small = {f for f, n in counts.items() if n < a.min_fold and f != "unassigned"}
    if small:
        for i in folds_of:
            folds_of[i] = {("unassigned" if f in small else f) for f in folds_of[i]}
        counts = {}
        for i in folds_of:
            for f in folds_of[i]: counts[f] = counts.get(f, 0) + 1
    if a.arch == "single":
        folds_of = {i: {"all"} for i in folds_of}
        counts = {"all": len(folds_of)}
        print("ARCH=single: one pooled model, same negatives/subsampling/protocol as the per-fold run")
    names = sorted(counts)
    print(f"fold assignment in {int(time.time()-t)}s (folds merged for n<{a.min_fold}: {sorted(small) or 'none'})")
    for f in names: print(f"  {f:<18}{counts[f]:>5} positives")
    multi = sum(1 for i in folds_of if len(folds_of[i]) > 1)
    print(f"  {multi} positives belong to more than one fold (modular lysins, counted in each)")

    # ---- 2. features once ----
    esm = F.ESM(B / "models/esm_cache")
    feats = lambda ss: np.hstack([np.array([F.handcrafted(s) for s in ss]), esm.embed(ss)])
    tr_pos = [i for i, r in enumerate(pos) if not r["in_gold_holdout"]]
    gold_pos = [i for i, r in enumerate(pos) if r["in_gold_holdout"]]
    negpool = [("otherclass", r) for r in spa] + [("holin", r) for r in holins] \
              + [("bacterial", r) for r in bact] + [("phage_neg", r) for r in negs]
    rng = np.random.default_rng(0); nidx = rng.permutation(len(negpool))
    n_gold = int(0.2 * len(negpool))
    gold_neg = [negpool[i][1] for i in nidx[:n_gold]]
    tr_neg = [negpool[i][1] for i in nidx[n_gold:]]
    t = time.time()
    Xp = feats([pos[i]["sequence"] for i in range(len(pos))])
    Xn = feats([r["sequence"] for r in tr_neg])
    Xgn = feats([r["sequence"] for r in gold_neg])
    print(f"features in {int(time.time()-t)}s: pos {Xp.shape} neg {Xn.shape}", flush=True)

    atlas_folds = None
    genomes = S28.atlas_phages("endolysin")
    gp = [p for g in genomes for p in g["proteins"]]
    yscan = np.array([p["is_pos"] for p in gp], int)
    grp = np.array([p["phage"] for p in gp])
    Xs = feats([p["sequence"] for p in gp])
    print(f"{len(genomes)} atlas phages, {int(yscan.sum())} annotated endolysins to recover", flush=True)

    if a.arch == "routed":
        ah = D.scan({f"a{i}": p["sequence"] for i, p in enumerate(gp)}, hmms, cls_of)
        atlas_folds = [{OF[h["pfam"]] for h in ah.get(f"a{i}", [])
                        if h["pfam"] in OF and h["grade"] == "catalytic" and h["ievalue"] <= 1e-5}
                       for i in range(len(gp))]
        print(f"routed: {sum(1 for f in atlas_folds if f)} of {len(gp)} atlas proteins have a confirmed "
              f"catalytic fold; the rest fall back to the pooled model", flush=True)

    pos_seqs = [pos[i]["sequence"] for i in tr_pos]
    cl_of_trpos = np.array([pos[i].get("cluster", -1) for i in tr_pos])

    def fit_pooled(drop_trpos):
        pi = [k for k in range(len(tr_pos)) if not drop_trpos[k]]
        if len(pi) < 10: return None
        nneed = min(len(tr_neg), max(a.neg_ratio * len(pi), 2000))
        ni = np.random.default_rng(7).permutation(len(tr_neg))[:nneed]
        X = np.vstack([Xp[[tr_pos[k] for k in pi]], Xn[ni]])
        y = np.concatenate([np.ones(len(pi), int), np.zeros(len(ni), int)])
        return hgb().fit(X, y)

    def fit_fold(f, drop_trpos):
        """one fold's model; drop_trpos = boolean mask over tr_pos to remove (leakage control)."""
        pi = [k for k, i in enumerate(tr_pos) if f in folds_of[i] and not drop_trpos[k]]
        if len(pi) < 10: return None
        other = [k for k, i in enumerate(tr_pos) if f not in folds_of[i]]   # EXCLUDED, not negative
        del other
        nneed = min(len(tr_neg), max(a.neg_ratio * len(pi), 2000))
        ni = np.random.default_rng(abs(hash(f)) % 2**31).permutation(len(tr_neg))[:nneed]
        X = np.vstack([Xp[[tr_pos[k] for k in pi]], Xn[ni]])
        y = np.concatenate([np.ones(len(pi), int), np.zeros(len(ni), int)])
        return hgb().fit(X, y)

    # ---- 3. leave-one-genome-out, both protocols, score = max over folds ----
    out = {"class": "endolysin", "architecture": "per-fold one-vs-rest, combined by max",
           "folds": {f: counts[f] for f in names}, "n_atlas_genomes": len(genomes),
           "n_annotated_in_atlas": int(yscan.sum()), "neg_ratio": a.neg_ratio,
           "design_note": "other folds' endolysins are EXCLUDED from each fold model, never used as negatives: "
                          "a different-fold endolysin is still an endolysin, and the confusables experiment "
                          "showed that labelling an inseparable protein as negative costs recall.",
           "baseline_single_model": {"strict": 0.7286, "realistic": 0.8430,
                                     "source": "reports/endolysin_eval.json (shipped v1)"}}
    for mode in ("family", "sequence"):
        t = time.time()
        scores = np.zeros(len(gp)); per_fold_win = {}
        for g in genomes:
            qs = [p["sequence"] for p in g["proteins"] if p["is_pos"]]
            drop = np.zeros(len(tr_pos), bool)
            if qs:
                ident = CL.search(qs, pos_seqs, 80)
                if mode == "family":
                    dc = {cl_of_trpos[i] for i, v in enumerate(ident) if v >= CL.MIN_ID}
                    if dc: drop = np.isin(cl_of_trpos, list(dc))
                else:
                    hit = [i for i, v in enumerate(ident) if v >= 0.95]
                    if hit: drop[np.array(hit, int)] = True
            sel = [i for i, p in enumerate(gp) if p["phage"] == g["key"]]
            best = np.zeros(len(sel)); win = [""] * len(sel)
            fitted = {f: fit_fold(f, drop) for f in names}
            pooled = fit_pooled(drop) if a.arch == "routed" else None
            if a.arch == "routed":
                sp = pooled.predict_proba(Xs[sel])[:, 1] if pooled is not None else np.zeros(len(sel))
                sf = {f: (m.predict_proba(Xs[sel])[:, 1] if m is not None else None)
                      for f, m in fitted.items()}
                for j, i in enumerate(sel):
                    conf = atlas_folds[i] & set(names)
                    cand = [(sf[f][j], f) for f in conf if sf.get(f) is not None]
                    best[j], win[j] = max(cand) if cand else (sp[j], "pooled(no domain)")
            else:
                for f in names:
                    m = fitted[f]
                    if m is None: continue
                    s = m.predict_proba(Xs[sel])[:, 1]
                    for j in range(len(sel)):
                        if s[j] > best[j]: best[j], win[j] = s[j], f
            scores[sel] = best
            for j, i in enumerate(sel):
                if yscan[i]: per_fold_win[gp[i]["gene"]] = {"fold": win[j], "score": round(float(best[j]), 4)}
        ap_ = float(average_precision_score(yscan, scores))
        rngb = np.random.default_rng(0); gs = sorted(set(grp)); vals = []
        for _ in range(a.boot):
            pick = rngb.choice(gs, size=len(gs), replace=True)
            ix = np.concatenate([np.where(grp == q)[0] for q in pick])
            if len(set(yscan[ix])) > 1: vals.append(average_precision_score(yscan[ix], scores[ix]))
        ci = [round(float(np.percentile(vals, 2.5)), 4), round(float(np.percentile(vals, 97.5)), 4)] if vals else None
        thr = {}
        for t_ in (0.5, 0.9):
            k = scores >= t_; n = int(k.sum()); tp = int((k & (yscan == 1)).sum())
            thr[str(t_)] = {"called": n, "true": tp, "precision": round(tp / n, 3) if n else None,
                            "recall": round(tp / int(yscan.sum()), 3)}
        top1 = float(np.mean([int(yscan[max([i for i, p in enumerate(gp) if p["phage"] == k],
                                            key=lambda i: scores[i])] == 1) for k in sorted(set(grp))]))
        out[f"{mode}_removal"] = {"genome_AP": round(ap_, 4), "CI95_by_genome": ci, "at_thresholds": thr,
                                 "top1_per_genome": round(top1, 3), "which_fold_won": per_fold_win,
                                 "seconds": int(time.time() - t)}
        print(f"{mode:<9} AP={ap_:.4f} CI={ci} top1={top1:.2f} ({int(time.time()-t)}s)", flush=True)

    # ---- 4. gold holdout, then ship a model per fold trained on everything ----
    prod, sg = {}, np.zeros(len(gold_pos) + len(gold_neg))
    Xg = np.vstack([Xp[gold_pos], Xgn])
    yg = np.array([1] * len(gold_pos) + [0] * len(gold_neg))
    allmask = np.zeros(len(tr_pos), bool)
    for f in names:
        m = fit_fold(f, allmask)
        if m is None: continue
        prod[f] = m
        sg = np.maximum(sg, m.predict_proba(Xg)[:, 1])
    out["gold_holdout"] = {"AP": round(float(average_precision_score(yg, sg)), 4),
                           "n_pos": len(gold_pos), "n_neg": len(gold_neg),
                           "note": "not comparable across dataset versions: scripts/27 re-draws the clusters"}
    if a.arch == "routed": prod["__pooled__"] = fit_pooled(allmask)
    pickle.dump({"models": prod, "folds": {f: counts[f] for f in names},
                 "combine": ("route by HMM-confirmed catalytic fold, else __pooled__" if a.arch == "routed"
                             else "max"),
                 "arch": a.arch,
                 "features": "both", "algorithm": "hgb", "class": "endolysin",
                 "hand_feature_names": list(F.HAND_NAMES), "esm_model": F.ESM.MODEL,
                 "fold_pfam": FOLD,
                 "note": "per-fold endolysin models; score = max over folds. Honest estimate = the "
                         "leave-one-genome-out figures in reports/endolysin_folds_eval.json."},
                open(B / f"models/endolysin_folds{a.tag}.pkl", "wb"))
    out["arch"] = a.arch
    (B / f"reports/endolysin_folds_eval{a.tag}.json").write_text(json.dumps(out, indent=2))
    bl = out["baseline_single_model"]
    print(f"\nstrict    per-fold {out['family_removal']['genome_AP']:.4f}  vs single {bl['strict']:.4f}")
    print(f"realistic per-fold {out['sequence_removal']['genome_AP']:.4f}  vs single {bl['realistic']:.4f}")
    print(f"saved models/endolysin_folds{a.tag}.pkl, reports/endolysin_folds_eval{a.tag}.json")


if __name__ == "__main__":
    main()
