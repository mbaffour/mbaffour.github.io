"""Give the curated holins cluster ids WITHOUT disturbing the frozen gold holdout.

Re-clustering everything from scratch would be the obvious move and it would be wrong. The gold holdout was drawn
once as whole homology clusters under the original clustering; adding 4,497 sequences can bridge two previously
separate clusters, so a re-cluster can quietly place a training holin in the same family as a gold holdout holin
and leak. The holdout would still list the same ids, and the leak would be invisible.

So existing records keep their original cluster ids, and each new holin is ASSIGNED:
  - to the cluster of its best existing hit (identity >= MIN_ID at coverage >= MIN_COV), or
  - to a fresh cluster, clustered among the other unassigned new holins.
Any new holin that lands in a cluster containing a gold-holdout holin is flagged excluded_gold_cluster and is
never trained on, which keeps the holdout exactly as frozen as before.

Usage: python3 scripts/21_merge_curated.py
"""
import importlib, json, sys, time
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
CL = importlib.import_module("03_cluster")

B = Path(__file__).resolve().parent.parent


def best_existing(seq, targets):
    """(identity, index) of the best existing holin for `seq`, or (0, None)."""
    best = (0.0, None)
    for i, (ident, cov, sc) in enumerate(CL.align_pairs(seq, targets)):
        if cov >= CL.MIN_COV and ident >= CL.MIN_ID and ident > best[0]: best = (ident, i)
    return best


def main():
    data = json.load(open(B / "data/processed/dataset.json"))
    extra = json.load(open(B / "data/processed/holins_extra.json"))
    gold_ids = set(json.load(open(B / "data/processed/gold_holdout.json"))["ids"])
    hol = [r for r in data if r["label"] == "holin"]
    gold_clusters = {r["cluster"] for r in hol if r["id"] in gold_ids}
    hol_seqs = [r["sequence"] for r in hol]
    print(f"{len(extra)} curated records to place against {len(hol)} existing holins "
          f"({len(gold_clusters)} gold clusters)", flush=True)

    t = time.time(); assigned, unassigned = [], []
    for k, r in enumerate(extra):
        ident, i = best_existing(r["sequence"], hol_seqs)
        if i is not None:
            r["cluster"] = hol[i]["cluster"]; r["assigned_by"] = f"existing hit {ident:.2f}"
            assigned.append(r)
        else:
            unassigned.append(r)
        if k % 500 == 0: print(f"  {k}/{len(extra)} placed, {len(assigned)} joined an existing family", flush=True)
    print(f"placed against existing families in {int(time.time()-t)}s: "
          f"{len(assigned)} joined, {len(unassigned)} are new families", flush=True)

    t = time.time()
    useqs = [r["sequence"] for r in unassigned]
    edges = CL.all_edges(useqs)
    cl = CL.greedy(len(useqs), edges, [len(s) for s in useqs], 80)
    base = max(r["cluster"] for r in data) + 1
    for r, c in zip(unassigned, cl): r["cluster"] = base + int(c); r["assigned_by"] = "new family"
    print(f"clustered {len(useqs)} new-family holins into {len(set(cl))} clusters in {int(time.time()-t)}s", flush=True)

    out = assigned + unassigned
    for r in out:
        r["excluded_gold_cluster"] = r["cluster"] in gold_clusters
    excl = sum(r["excluded_gold_cluster"] for r in out)
    usable = [r for r in out if not r["excluded_gold_cluster"]]
    uh = [r for r in usable if r["label"] == "holin"]
    (B / "data/processed/holins_extra_clustered.json").write_text(json.dumps(out, indent=1))
    rep = {"rule": "existing records keep their original clusters; new holins join an existing family by "
                   f"identity >= {CL.MIN_ID} at coverage >= {CL.MIN_COV}, else form new families",
           "why_not_recluster": "adding sequences can bridge previously separate clusters, which would place a "
                                "training holin in a gold-holdout family and leak invisibly",
           "counts": {"curated": len(out), "joined_existing_family": len(assigned),
                      "formed_new_families": len(unassigned),
                      "new_clusters": len({r['cluster'] for r in unassigned}),
                      "excluded_as_gold_cluster": excl, "usable": len(usable),
                      "usable_holin": len(uh),
                      "usable_holin_like": sum(1 for r in usable if r["label"] == "holin_like"),
                      "usable_holin_over_150aa": sum(1 for r in uh if r["length"] > 150),
                      "usable_holin_over_200aa": sum(1 for r in uh if r["length"] > 200)},
           "tiers": dict(Counter(r["tier"] for r in usable)),
           "top_new_families_by_size": [{"cluster": c, "n": n} for c, n in
                                        Counter(r["cluster"] for r in unassigned).most_common(8)]}
    (B / "reports/merge_report.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep["counts"], indent=1))
    print("tiers:", json.dumps(rep["tiers"]))


if __name__ == "__main__":
    main()
