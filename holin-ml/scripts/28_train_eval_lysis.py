"""Train and evaluate an endolysin or spanin one-vs-rest model, with the holin pipeline's leakage discipline.

One model per call (--class endolysin|spanin). Positives = that class's curated set (scripts/27). Negatives = the
OTHER two lysis classes + bacterial + phage negatives, so the model is forced to tell endolysin from holin from
spanin -- the discrimination that matters in a real cassette, and the one that bit the holin model (spanins scored
0.86-0.96 on it because they were never negatives).

Primary metric: leave-one-genome-out genome scan over the 16 atlas phages, which carry annotated endolysins and
spanins. For each genome the target class's family is removed from training (by homology) before that genome is
scored, so the model cannot score a protein from a family it has memorised. Two removal protocols, as for holins:
  family   (strict)    remove every training positive >=30% identical to the genome's annotated protein(s)
  sequence (realistic) remove only >=95%-identical near-duplicates, keeping the family
Secondary: AP on the class's frozen gold holdout clusters (scripts/27) against a held-out negative sample.

Saves models/{cls}_model.pkl + reports/{cls}_eval.json.
Usage: python3 scripts/28_train_eval_lysis.py --class endolysin [--boot 2000]
"""
import argparse, glob, importlib, json, os, pickle, re, sys, time
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
CL = importlib.import_module("03_cluster")

B = Path(__file__).resolve().parent.parent
DSC = "/home/user/mbaffour.github.io/dirty-science-canvas"
NAME = {"endolysin": re.compile(r"endolysin|lysozyme|muramidase|amidase|peptidoglycan|murein|glucosaminidase|\blysin\b|"
                                r"transglycosylase|glycoside hydrolase", re.I),
        "spanin": re.compile(r"spanin|\bRz\b|\bRz1\b", re.I)}
ES = "auto"   # sklearn default; --early-stopping False overrides. 'auto' turns early stopping ON above 10k rows,
              # which every lysis training set exceeds, and its validation split is a RANDOM 10% -- full of
              # homologs of the training rows. reports/capacity_sweep.md measures what that costs.
def hgb(): return HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_leaf_nodes=31,
                                                 random_state=0, early_stopping=ES)


def atlas_phages(cls):
    """Atlas-phage proteins; positive = annotated as this class. (Holin excluded from positives of other classes.)"""
    name = NAME[cls]; out = []
    for p in sorted(glob.glob(os.path.join(DSC, "*_Topology_Lab_Reference", "data.json"))):
        d = json.load(open(p))
        if d.get("kind") != "phage": continue
        ps = []
        for r in d["proteins"]:
            prod = r.get("product") or ""
            ps.append({"gene": (r.get("gene") or r["protein_id"])[:16], "product": prod, "sequence": r["sequence"],
                       "length": r["length"], "is_pos": bool(name.search(prod)), "phage": d["key"]})
        if any(x["is_pos"] for x in ps): out.append({"key": d["key"], "proteins": ps})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--class", dest="cls", required=True, choices=["endolysin", "spanin"])
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--confusables", action="store_true",
                    help="add data/processed/lysis_confusables.json to the negatives: phage TAIL lysozymes and "
                         "other lysis-adjacent proteins that are not holin/endolysin/spanin. Run both ways and "
                         "compare -- they are only worth shipping if the leave-one-genome-out number says so.")
    ap.add_argument("--pos-suffix", default="", help="read {cls}_positives<suffix>.json instead of the default, "
                                                     "for ablation datasets built by scripts/27 --suffix")
    ap.add_argument("--tag", default="", help="suffix for model/report filenames, so an ablation run does not "
                                              "overwrite the shipped model")
    ap.add_argument("--other-suffix", default=None,
                    help="suffix for the OTHER lysis class's positives (the cross-class negatives); defaults to "
                         "--pos-suffix. Lets the endolysin model take v1 positives with the current spanin set")
    ap.add_argument("--early-stopping", default="auto", help="auto (sklearn default) or False")
    a = ap.parse_args(); cls = a.cls
    global ES
    ES = False if str(a.early_stopping).lower() in ("false", "0", "no") else a.early_stopping
    other_suffix = a.pos_suffix if a.other_suffix is None else a.other_suffix
    esm = F.ESM(B / "models/esm_cache")
    feats = lambda ss: np.hstack([np.array([F.handcrafted(s) for s in ss]), esm.embed(ss)]) if ss else np.zeros((0, 516))

    pos = json.load(open(B / f"data/processed/{cls}_positives{a.pos_suffix}.json"))
    other = "spanin" if cls == "endolysin" else "endolysin"
    other_pos = json.load(open(B / f"data/processed/{other}_positives{other_suffix}.json"))
    base = json.load(open(B / "data/processed/dataset.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))
    negs = json.load(open(B / "data/processed/phage_negatives.json"))
    holins = [r for r in base if r["label"] == "holin"] + [r for r in cur if r["label"] == "holin"]
    bact = [r for r in base if r["label"] == "negative"]

    tr_pos = [r for r in pos if not r["in_gold_holdout"]]
    gold_pos = [r for r in pos if r["in_gold_holdout"]]
    # negative pool = other lysis class + holins + bacterial + phage negatives; hold out 20% (seed 0) as gold negatives
    negpool = ([("otherclass", r) for r in other_pos] + [("holin", r) for r in holins]
               + [("bacterial", r) for r in bact] + [("phage_neg", r) for r in negs])
    n_conf = 0
    if a.confusables:
        cf = json.load(open(B / "data/processed/lysis_confusables.json"))
        # leakage guard: a confusable family can contain the very protein of a genome we are about to score
        # (e.g. the microvirus E of phiX174). Training on it as a negative would flatter the genome scan, so any
        # exact sequence match to an atlas protein is dropped before it reaches the negative pool.
        atlas_seqs = {pr["sequence"] for g in atlas_phages(cls) for pr in g["proteins"]}
        n_drop = sum(r["sequence"] in atlas_seqs for r in cf)
        cf = [r for r in cf if r["sequence"] not in atlas_seqs]
        negpool += [("confusable", r) for r in cf]; n_conf = len(cf)
        print(f"{cls}: + {n_conf} confusable negatives (entry lysins, single-gene lysis proteins); "
              f"{n_drop} dropped as exact matches to a scored atlas protein", flush=True)
    rng = np.random.default_rng(0); idx = rng.permutation(len(negpool))
    n_gold_neg = int(0.2 * len(negpool))
    gold_neg = [negpool[i][1] for i in idx[:n_gold_neg]]
    tr_neg = [negpool[i][1] for i in idx[n_gold_neg:]]
    print(f"{cls}: train pos {len(tr_pos)} | train neg {len(tr_neg)} | gold pos {len(gold_pos)} | gold neg {len(gold_neg)}", flush=True)

    recs = tr_pos + tr_neg
    y = np.array([1] * len(tr_pos) + [0] * len(tr_neg), int)
    cl_ids = np.array([r.get("cluster", -1) for r in tr_pos] + [-1] * len(tr_neg))
    t = time.time()
    X = feats([r["sequence"] for r in recs])
    Xgp = feats([r["sequence"] for r in gold_pos]); Xgn = feats([r["sequence"] for r in gold_neg])
    print(f"features in {int(time.time()-t)}s", flush=True)

    genomes = atlas_phages(cls)
    gp = [p for g in genomes for p in g["proteins"]]
    yscan = np.array([p["is_pos"] for p in gp], int)
    grp = np.array([p["phage"] for p in gp])
    Xs = feats([p["sequence"] for p in gp])
    pos_seqs = [r["sequence"] for r in tr_pos]
    pos_rows = list(range(len(tr_pos)))      # indices into recs that are positives
    print(f"{len(genomes)} atlas phages carry an annotated {cls}; {int(yscan.sum())} annotated proteins to recover", flush=True)

    out = {"class": cls, "n_atlas_genomes": len(genomes), "n_annotated_in_atlas": int(yscan.sum())}
    for mode in ("family", "sequence"):
        scores = np.zeros(len(gp))
        for g in genomes:
            qs = [p["sequence"] for p in g["proteins"] if p["is_pos"]]
            drop = np.zeros(len(recs), bool)
            if qs:
                ident = CL.search(qs, pos_seqs, 80)
                if mode == "family":
                    dc = {cl_ids[i] for i, v in enumerate(ident) if v >= CL.MIN_ID}
                    drop[:len(tr_pos)] = np.isin(cl_ids[:len(tr_pos)], list(dc)) if dc else False
                else:
                    hit = [i for i, v in enumerate(ident) if v >= 0.95]
                    if hit: drop[np.array(hit, int)] = True
            keep = ~drop
            m = hgb().fit(X[keep], y[keep])
            sel = [i for i, p in enumerate(gp) if p["phage"] == g["key"]]
            scores[sel] = m.predict_proba(Xs[sel])[:, 1]
        rngb = np.random.default_rng(0); gs = sorted(set(grp)); vals = []
        for _ in range(a.boot):
            pick = rngb.choice(gs, size=len(gs), replace=True)
            ix = np.concatenate([np.where(grp == q)[0] for q in pick])
            if len(set(yscan[ix])) > 1: vals.append(average_precision_score(yscan[ix], scores[ix]))
        thr = {}
        for t_ in (0.5, 0.9):
            k = scores >= t_; n = int(k.sum()); tp = int((k & (yscan == 1)).sum())
            thr[str(t_)] = {"called": n, "true": tp, "precision": round(tp / n, 3) if n else None,
                            "recall": round(tp / int(yscan.sum()), 3)}
        # top-1: is the top-scored protein in each genome an annotated positive of this class?
        t1 = []
        for k_ in gs:
            m = grp == k_
            if yscan[m].sum() == 0: continue
            t1.append(1.0 if yscan[m][np.argmax(scores[m])] == 1 else 0.0)
        out[f"{mode}_removal"] = {"genome_AP": round(float(average_precision_score(yscan, scores)), 4),
                                  "CI95_by_genome": [round(float(np.percentile(vals, 2.5)), 4),
                                                     round(float(np.percentile(vals, 97.5)), 4)] if vals else None,
                                  "at_thresholds": thr, "top1_per_genome": round(float(np.mean(t1)), 3)}
        print(f"  {mode}: AP {out[f'{mode}_removal']['genome_AP']} CI {out[f'{mode}_removal']['CI95_by_genome']} "
              f"recall@0.9 {thr['0.9']['recall']} prec@0.9 {thr['0.9']['precision']} top1 {out[f'{mode}_removal']['top1_per_genome']}", flush=True)

    # gold holdout AP + production model on everything
    mfull = hgb().fit(X, y)
    sg = np.concatenate([mfull.predict_proba(Xgp)[:, 1], mfull.predict_proba(Xgn)[:, 1]])
    yg = np.array([1] * len(gold_pos) + [0] * len(gold_neg))
    out["gold_holdout"] = {"AP": round(float(average_precision_score(yg, sg)), 4),
                           "n_pos": len(gold_pos), "n_neg": len(gold_neg),
                           "note": "class gold-holdout clusters vs held-out negative sample; this model trains on all"}
    mprod = hgb().fit(np.vstack([X, Xgp]), np.concatenate([y, np.ones(len(gold_pos), int)]))  # ship on everything
    bundle = {"model": mprod, "features": "both", "algorithm": "hgb", "class": cls,
              "hand_feature_names": list(F.HAND_NAMES), "esm_model": F.ESM.MODEL,
              "trained_on": {"positives": len(pos), "negatives": len(negpool), "confusable_negatives": n_conf,
                             "positives_file": f"{cls}_positives{a.pos_suffix}.json",
                             "other_class_file": f"{other}_positives{other_suffix}.json",
                             "early_stopping": ES},
              "note": f"one-vs-rest {cls}; negatives include holins and {other}s. Honest estimate = leave-one-genome-out above."}
    out["config"] = {"confusable_negatives": n_conf, "train_positives": len(tr_pos), "train_negatives": len(tr_neg)}
    pickle.dump(bundle, open(B / f"models/{cls}_model{a.tag}.pkl", "wb"))
    (B / f"reports/{cls}_eval{a.tag}.json").write_text(json.dumps(out, indent=2))
    print(f"saved models/{cls}_model{a.tag}.pkl ; " + json.dumps({k: out[k].get("genome_AP") for k in out if k.endswith("removal")}))


if __name__ == "__main__":
    main()
