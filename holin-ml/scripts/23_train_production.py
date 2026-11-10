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
import hashlib, json, pickle, sys, time
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F

B = Path(__file__).resolve().parent.parent
def hgb(): return HistGradientBoostingClassifier(max_iter=400, learning_rate=0.06, max_leaf_nodes=31, random_state=0)


def main():
    base = json.load(open(B / "data/processed/dataset.json"))
    negs = json.load(open(B / "data/processed/phage_negatives.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))

    pos = [r for r in base if r["label"] == "holin"] + [r for r in cur if r["label"] == "holin"]
    neg = [r for r in base if r["label"] == "negative"] + negs
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
                             "negatives_phage": len(negs)},
              "note": "DEPLOYMENT model: trained on all labels including the gold holdout. Do not quote a "
                      "gold-holdout score from it. Honest estimate = leave-one-genome-out in "
                      "reports/curated_retrain_eval.json (AP 0.965 realistic / 0.785 strict)."}
    out = B / "models/holin_model_curated.pkl"
    pickle.dump(bundle, open(out, "wb"))
    sha = hashlib.sha256(out.read_bytes()).hexdigest()

    card = {"model": "holin_model_curated.pkl", "sha256": sha, "trained_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
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
    (B / "reports/model_card.json").write_text(json.dumps(card, indent=2))
    print(f"saved {out.name} ({out.stat().st_size//1024} KiB, sha {sha[:12]})")
    print("wrote reports/model_card.json")


if __name__ == "__main__":
    main()
