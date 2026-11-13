"""Train and save the deployable curated model -- the artifact scripts/22 proved best but never saved.

scripts/22 showed that adding the 2,886 curated holins lifts leave-one-genome-out genome-scan AP from 0.823 to
0.965 (realistic protocol) and recovers T4 t and T5 C1. But scripts/22 only trained models INSIDE its
leave-one-genome-out loop to measure that; it never fitted and saved a model on the full data. This script does.

A deployment model trains on every label available, so it is NOT the model to quote a number from: it has seen
the gold holdout, so its gold-holdout score is memorisation, not an estimate. The honest performance estimate is
the leave-one-genome-out figure from scripts/22 (reports/curated_retrain_eval.json), recorded in the model card.

Composition (same winning recipe as scripts/22 arm B: handcrafted + mean-pooled ESM, no local features):
  positives  558 Swiss-Prot/TCDB holins  + 4,497 curated Pfam-family holins
  negatives  9,503 bacterial             + 3,382 phage-derived (incl. 101 spanins)
  excluded   holin_like / antiholins (not holins; kept out of training as in every prior script)

Usage: python3 scripts/23_train_production.py
"""
import argparse, hashlib, json, pickle, sys, time
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F

B = Path(__file__).resolve().parent.parent
def hgb(): return HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_leaf_nodes=31, random_state=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crossclass", action="store_true",
                    help="add the scripts/27 endolysin and spanin positives plus the scripts/26 confusables as "
                         "negatives, so this model is held to the same three-class discrimination as the other "
                         "two. Ship it only if scripts/22 arm C beats arm B on leave-one-genome-out.")
    ap.add_argument("--extra-positives", default=None,
                    help="JSON of additional holin positives (scripts/49 output, list or {records: [...]}). Used to "
                         "build models/holin_model_mined.pkl, the second half of the predictor's --holin-mode t4aware.")
    ap.add_argument("--out", default="models/holin_model_curated.pkl")
    a = ap.parse_args()
    base = json.load(open(B / "data/processed/dataset.json"))
    negs = json.load(open(B / "data/processed/phage_negatives.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))

    pos = [r for r in base if r["label"] == "holin"] + [r for r in cur if r["label"] == "holin"]
    neg = [r for r in base if r["label"] == "negative"] + negs
    n_x = 0; n_extra = 0
    if a.extra_positives:
        ex = json.load(open(B / a.extra_positives)); ex = ex["records"] if isinstance(ex, dict) else ex
        have = {r["sequence"] for r in pos}
        ex = [r for r in ex if r["sequence"] not in have]
        pos += ex; n_extra = len(ex)
        print(f"+ {n_extra} extra holin positives from {a.extra_positives}", flush=True)
    if a.crossclass:
        hol = {r["sequence"] for r in pos}
        xc = []
        for f in ("endolysin_positives.json", "spanin_positives.json", "lysis_confusables.json"):
            fp = B / "data/processed" / f
            if fp.exists(): xc += [r for r in json.load(open(fp)) if r["sequence"] not in hol]
        seen = set(); xc = [r for r in xc if not (r["sequence"] in seen or seen.add(r["sequence"]))]
        neg += xc; n_x = len(xc)
        print(f"+ {n_x} cross-class negatives (endolysins, spanins, lysis confusables)", flush=True)
    recs = pos + neg
    y = np.array([1] * len(pos) + [0] * len(neg), int)
    print(f"training rows {len(recs)}: {len(pos)} holins ({sum(r['label']=='holin' for r in base)} original + "
          f"{sum(r['label']=='holin' for r in cur)} curated), {len(neg)} negatives "
          f"({sum(r['label']=='negative' for r in base)} bacterial + {len(negs)} phage)", flush=True)

    esm = F.ESM(B / "models/esm_cache")
    t = time.time()
    X = np.hstack([np.array([F.handcrafted(r["sequence"]) for r in recs]), esm.embed([r["sequence"] for r in recs])])
    print(f"features {X.shape} in {int(time.time()-t)}s", flush=True)
    model = hgb().fit(X, y)

    bundle = {"model": model, "features": "both", "algorithm": "hgb",
              "hand_feature_names": list(F.HAND_NAMES), "esm_model": F.ESM.MODEL,
              "trained_on": {"rows": len(recs), "holins": int(len(pos)),
                             "holins_original": sum(r["label"] == "holin" for r in base),
                             "holins_curated": sum(r["label"] == "holin" for r in cur),
                             "negatives_bacterial": sum(r["label"] == "negative" for r in base),
                             "negatives_phage": len(negs), "negatives_crossclass": n_x,
                             "holins_extra": n_extra, "extra_positives": a.extra_positives},
              "note": "DEPLOYMENT model: trained on all labels including the gold holdout. Do not quote a "
                      "gold-holdout score from it. Honest estimate = leave-one-genome-out in "
                      "reports/curated_retrain_eval.json (AP 0.965 realistic / 0.785 strict)."}
    out = B / a.out
    pickle.dump(bundle, open(out, "wb"))
    sha = hashlib.sha256(out.read_bytes()).hexdigest()

    card = {"model": a.out.split("/")[-1], "sha256": sha, "trained_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "purpose": "rank the proteins of a phage genome by probability of being a holin",
            "recipe": "HistGradientBoosting over 36 handcrafted features + 480-d mean-pooled ESM-2 (t12_35M). "
                      "TM-anchored local features were tested and rejected (scripts/15).",
            "training_composition": bundle["trained_on"],
            "honest_performance_leave_one_genome_out": {
                "note": "measured in scripts/22 by removing each genome's holin family before scoring it; "
                        "this deployment model trains on everything, so these are the estimate, not its own score",
                "realistic_>=95pct_identity_removed": {"genome_AP": 0.9647, "CI95": [0.8928, 1.0],
                    "recall_at_0.9": 0.923, "precision_at_0.9": 0.75, "top1_per_genome": 1.0},
                "strict_>=30pct_identity_family_removed": {"genome_AP": 0.7847, "CI95": [0.5381, 0.9619],
                    "recall_at_0.9": 0.692, "precision_at_0.9": 0.75, "top1_per_genome": 0.8}},
            "known_limits": ["profile-match evidence: only 7 of 2,886 curated holins are Swiss-Prot reviewed",
                             "Pfam is exhausted as a source: 4,700 of 4,701 curated records joined existing families",
                             "P1 lydD remains the weakest annotated holin (0.60, rank 3/110)",
                             "precision falls vs the pre-curation model (0.75 vs 0.82 at >=0.9); use the 0.95 "
                             "threshold for high-confidence calls",
                             "a genuinely novel holin family gets a shortlist, not an answer (strict AP 0.785)"],
            "usage": "import pickle, features as F; m=pickle.load(open('models/holin_model_curated.pkl','rb')); "
                     "X=hstack([handcrafted, esm.embed(seqs)]); m['model'].predict_proba(X)[:,1]"}
    if a.extra_positives:
        card["honest_performance_leave_one_genome_out"] = {
            "note": "this model is used only AVERAGED with holin_model_curated.pkl (predictor --holin-mode t4aware). "
                    "Leave-one-genome-out on 78 CPT genomes, novel family, for that average (scripts/50, "
                    "reports/holin_generalisation.md): ranked 1st 0.513 vs 0.538 for the standard model "
                    "(-0.026 [-0.064, 0.000]), top 5 0.846 vs 0.846, T4-type holins ranked 3-30 vs 10-67; "
                    "experimental set 6/8 vs 7/8 ranked 1st."}
        card["known_limits"] = ["about one mined positive in five is not a holin (rule precision 76-82% on CPT)",
                                "not better than the standard model overall; use it for T4-like phages"]
    cardp = "reports/model_card.json" if a.out == "models/holin_model_curated.pkl" else \
            f"reports/model_card_{Path(a.out).stem}.json"
    (B / cardp).write_text(json.dumps(card, indent=2))
    print(f"saved {out.name} ({out.stat().st_size//1024} KiB, sha {sha[:12]})")
    print(f"wrote {cardp}")


if __name__ == "__main__":
    main()
