"""Leave-one-genome-out recall benchmark: can the model find a known holin in a genome it was never trained on?

For each genome:
  1. take the RefSeq annotated CDS translations;
  2. ground truth = any protein that matches a holin in the reference set at >= 95% identity over >= 90% of its length
     (so we know what the right answer is, and which evidence tier it carries);
  3. REMOVE from training every holin with a >= 30% identity / >= 50% coverage local alignment to ANY protein of this
     genome - that deletes the answer and its whole family, not just the exact entry;
  4. refit the best model on what is left and score every protein of the genome;
  5. report the rank of the true holin among all proteins of that genome.

A genome with no ground-truth match is still scanned and its top candidates reported, flagged as 'no reference holin'.
Usage: python3 scripts/06_benchmark_genomes.py [--genomes NC_001416.1,NC_008720.1] [--top 10]
"""
import argparse, json, pickle, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import importlib
C = importlib.import_module("03_cluster")
S = importlib.import_module("05_scan_genome")
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

B = Path(__file__).resolve().parent.parent
GENOMES = [
    ("NC_008720.1", "Escherichia phage N4", "SAR endolysin-holin system defined in Awuah et al. 2026 J Bacteriol doi:10.1128/jb.00538-25"),
    ("NC_001416.1", "Enterobacteria phage lambda", "S105/S107 holin-antiholin, the canonical holin"),
    ("NC_000866.4", "Enterobacteria phage T4", "holin T (gene t), protein-level evidence"),
    ("NC_001604.1", "Enterobacteria phage T7", "holin gp17.5"),
    ("NC_001895.1", "Enterobacteria phage P2", "holin Y, protein-level evidence"),
    ("NC_011048.1", "Bacillus phage phi29", "holin gp14 (dual start)"),
    ("NC_004166.2", "Bacillus phage SPP1", "SPP1 holin family"),
    ("NC_002371.2", "Salmonella phage P22", "holin gene 13"),
    ("NC_005045.1", "Pseudomonas phage phiKMV", "holin gp44, protein-level evidence"),
    ("NC_001900.1", "Mycobacterium phage D29", "gene 11 holin, protein-level evidence"),
    ("NC_015274.1", "Streptococcus phage Dp-1", "holin, protein-level evidence"),
    ("NC_001825.1", "Streptococcus phage Cp-1", "holin (lysis protein), protein-level evidence"),
]
GT_ID, GT_COV = 0.95, 0.90


def fit(features, algorithm, X, y):
    m = (make_pipeline(StandardScaler(), LogisticRegression(max_iter=4000, class_weight="balanced")) if algorithm == "logreg"
         else HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, l2_regularization=1.0, class_weight="balanced", random_state=0))
    m.fit(X, y); return m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--genomes", default=""); ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--min-score", type=int, default=80, dest="min_score",
                    help="Smith-Waterman score a holin must reach against a genome protein to count as homologous and be "
                         "removed from training. 0 removes on identity/coverage alone, which short spurious local "
                         "alignments trigger constantly (it wiped out 556 of 558 holins for T4).")
    a = ap.parse_args()
    want = [g.strip() for g in a.genomes.split(",") if g.strip()]
    genomes = [g for g in GENOMES if not want or g[0] in want]
    bundle = pickle.loads((B / "models/holin_model.pkl").read_bytes())
    data = json.loads((B / "data/processed/dataset.json").read_text())
    holins = [r for r in data if r["label"] == "holin"]
    negs = [r for r in data if r["label"] == "negative"]
    esm = F.ESM(B / "models/esm_cache")

    def mat(seqs):
        h = np.stack([F.handcrafted(s) for s in seqs])
        if bundle["features"] == "hand": return h
        e = esm.embed(seqs)
        return e if bundle["features"] == "esm" else np.hstack([h, e])

    results = []
    for acc, name, note in genomes:
        t0 = time.time()
        gb, url = S.fetch(acc, "gbwithparts", "gb")
        prots = [p for p in S.annotated_proteins(gb) if 20 <= len(p["sequence"]) <= 2000]
        pseqs = [p["sequence"] for p in prots]
        # ground truth: genome protein ~identical to a reference holin
        gt = []
        for h in holins:
            hits = C.align_pairs(h["sequence"], pseqs)
            for pi, (ident, cov, sc) in enumerate(hits):
                shorter = min(len(h["sequence"]), len(pseqs[pi]))
                if ident >= GT_ID and cov >= GT_COV and abs(len(h["sequence"]) - len(pseqs[pi])) / shorter < 0.15:
                    src = h["sources"][0]
                    gt.append({"protein_index": pi, "id": prots[pi]["id"], "product": prots[pi]["product"],
                               "length": len(pseqs[pi]),
                               "reference": src.get("accession"), "reference_name": (src.get("name") or src.get("description", ""))[:70],
                               "tier": h.get("tier"), "identity": round(float(ident), 3)})
        seen = set(); gt = [g for g in gt if not (g["protein_index"] in seen or seen.add(g["protein_index"]))]
        # holdout: drop every training holin homologous to anything in this genome
        best = C.search(pseqs, [h["sequence"] for h in holins], min_score=a.min_score)
        keep = [h for h, b in zip(holins, best) if b < C.MIN_ID]
        removed = int(len(holins) - len(keep))
        train = keep + negs
        y = np.array([r["label"] == "holin" for r in train], int)
        X = mat([r["sequence"] for r in train])
        model = fit(bundle["features"], bundle["algorithm"], X, y)
        score = model.predict_proba(mat(pseqs))[:, 1]
        order = np.argsort(-score)
        rank = {int(np.where(order == g["protein_index"])[0][0]) + 1: g for g in gt}
        rec = {"accession": acc, "organism": name, "expected": note, "source_url": url, "n_proteins": len(prots),
               "holdout_min_sw_score": a.min_score,
               "training_holins_removed": removed, "training_holins_left": len(keep),
               "ground_truth": [dict(g, rank=int(np.where(order == g["protein_index"])[0][0]) + 1,
                                     score=round(float(score[g["protein_index"]]), 4)) for g in gt],
               "top": [{"rank": i + 1, "id": prots[j]["id"], "gene": prots[j]["gene"], "product": prots[j]["product"][:70],
                        "length": len(pseqs[j]), "n_tm_hydropathy": len(F.tm_segments(pseqs[j])),
                        "score": round(float(score[j]), 4), "is_ground_truth": j in {g["protein_index"] for g in gt}}
                       for i, j in enumerate(order[:a.top])]}
        results.append(rec)
        gts = ", ".join(f"rank {g['rank']}/{len(prots)} score {g['score']:.3f} ({g['id']} {g['tier']})" for g in rec["ground_truth"]) or "no reference holin in this genome"
        print(f"{acc} {name:32} {len(prots):4} proteins, removed {removed:3} homologous training holins -> {gts}  [{time.time()-t0:.0f}s]", flush=True)
        for r in rec["top"][:5]:
            print(f'      {r["score"]:.3f} {"<<" if r["is_ground_truth"] else "  "} {r["id"]:16} {r["length"]:4} aa TM={r["n_tm_hydropathy"]} {r["gene"] or "":6} {r["product"][:60]}', flush=True)

    with_gt = [r for r in results if r["ground_truth"]]
    ranks = [g["rank"] for r in with_gt for g in r["ground_truth"]]
    summary = {"model": {k: bundle[k] for k in ("features", "algorithm", "esm_model")},
               "protocol": f"leave-one-genome-out: every training holin with >={C.MIN_ID:.0%} identity, >={C.MIN_COV:.0%} coverage and Smith-Waterman score >={a.min_score} against any protein of the scanned genome was removed before refitting",
               "holdout_min_sw_score": a.min_score,
               "ground_truth_rule": f">={GT_ID:.0%} identity over >={GT_COV:.0%} coverage to a reference holin, lengths within 15%",
               "genomes": len(results), "genomes_with_ground_truth": len(with_gt), "ground_truth_proteins": len(ranks),
               "rank_1": sum(r == 1 for r in ranks), "top_3": sum(r <= 3 for r in ranks), "top_10": sum(r <= 10 for r in ranks),
               "median_rank": float(np.median(ranks)) if ranks else None, "ranks": sorted(ranks), "results": results}
    (B / f"reports/genome_benchmark_s{a.min_score}.json").write_text(json.dumps(summary, indent=1))
    print("\n" + json.dumps({k: summary[k] for k in ("genomes", "genomes_with_ground_truth", "ground_truth_proteins", "rank_1", "top_3", "top_10", "median_rank", "ranks")}, indent=1))


if __name__ == "__main__":
    main()
