"""Score the mined pool with the production model and surface PUTATIVE NOVEL holins.

This is the payoff: of 24,064 proteins from 300 phage genomes (none used in the benchmark), which un-annotated
ones does the curated model call holins with high confidence AND independent support?

The whole result hinges on one anti-contamination step. A "discovery" is only novel if it is NOT already a known
holin wearing a different name. So every high-scoring un-annotated candidate is homology-screened against ALL
known holins (the 558 Swiss-Prot/TCDB holins + the 4,497 curated Pfam holins); anything within MIN_ID identity is
a member of a KNOWN family (useful, but not novel) and is separated out. Only candidates with no such homology
are called putative-novel. This is exactly the trap an earlier pass fell into ("12 of 13 recovered" turned out to
be scoring training examples), so the filter is strict and runs against the full 5,055-holin reference.

Order of operations is chosen for cost: score all 24,064 first (one model call over cached ESM features), then
homology-screen ONLY the high-scoring candidates (a few hundred) rather than all 24,064.

Independent evidence, kept separate from the model's own score:
  - has_lysis_neighbour: an annotated endolysin/spanin within 3 genes (the model never sees genomic context).
A candidate that scores high AND sits in a lysis cassette AND has no homology to a known holin is the strongest
class, because three independent signals agree.

Outputs reports/novel_holin_candidates.json and reports/novel_holin_candidates.md.
Usage: python3 scripts/24_discover_novel.py [--threshold 0.9] [--min-id 0.30]
"""
import argparse, importlib, json, pickle, re, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
CL = importlib.import_module("03_cluster")

B = Path(__file__).resolve().parent.parent
HOLIN_WORD = re.compile(r"holin", re.I)
SPANIN = re.compile(r"spanin|\brz\b|rz1", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.9, help="score at/above which to treat as a candidate")
    ap.add_argument("--min-id", type=float, default=CL.MIN_ID, help="identity to a known holin that counts as 'known family'")
    a = ap.parse_args()

    bundle = pickle.load(open(B / "models/holin_model_curated.pkl", "rb"))
    model = bundle["model"]
    pool = json.load(open(B / "data/processed/pool.json"))
    base = json.load(open(B / "data/processed/dataset.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))
    known = [r["sequence"] for r in base if r["label"] == "holin"] + [r["sequence"] for r in cur if r["label"] == "holin"]
    print(f"pool {len(pool)} proteins | known holins to screen against {len(known)}", flush=True)

    esm = F.ESM(B / "models/esm_cache")
    t = time.time()
    seqs = [p["sequence"] for p in pool]
    X = np.hstack([np.array([F.handcrafted(s) for s in seqs]), esm.embed(seqs)])
    score = model.predict_proba(X)[:, 1]
    for p, s in zip(pool, score): p["score"] = float(s)
    print(f"scored all {len(pool)} in {int(time.time()-t)}s", flush=True)

    # sanity check: does the model recover the pool's OWN annotated holins? (recovery, not discovery)
    ann = [p for p in pool if p.get("annotated_holin")]
    rec = sum(1 for p in ann if p["score"] >= a.threshold)
    print(f"recovery check: {rec}/{len(ann)} pool-annotated holins score >= {a.threshold}", flush=True)

    # candidates: high score, NOT annotated holin. Spanins are excluded -- they score high and are not holins.
    cand = [p for p in pool if p["score"] >= a.threshold and not p.get("annotated_holin")
            and not SPANIN.search(p.get("product") or "")]
    print(f"{len(cand)} high-scoring un-annotated non-spanin candidates; homology-screening against known holins...", flush=True)
    t = time.time()
    ident = CL.search(known, [p["sequence"] for p in cand], 80)
    for p, i in zip(cand, ident): p["max_identity_to_known_holin"] = float(i)
    print(f"homology screen in {int(time.time()-t)}s", flush=True)

    novel = [p for p in cand if p["max_identity_to_known_holin"] < a.min_id]
    known_member = [p for p in cand if p["max_identity_to_known_holin"] >= a.min_id]

    def row(p):
        return {"accession": p["accession"], "gene": p.get("gene") or "", "product": p.get("product") or "",
                "organism": p.get("organism") or "", "length": len(p["sequence"]), "score": round(p["score"], 4),
                "max_identity_to_known_holin": round(p["max_identity_to_known_holin"], 3),
                "has_lysis_neighbour": bool(p.get("has_lysis_neighbour")),
                "lysis_neighbours": p.get("lysis_neighbours") or [], "sequence": p["sequence"]}

    novel.sort(key=lambda p: (-int(bool(p.get("has_lysis_neighbour"))), -p["score"]))
    known_member.sort(key=lambda p: -p["score"])
    strong_rows = [row(p) for p in novel if p.get("has_lysis_neighbour")]
    novel_nocontext_rows = [row(p) for p in novel if not p.get("has_lysis_neighbour")]
    known_member_rows = [row(p) for p in known_member]

    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "model": "holin_model_curated.pkl", "pool_proteins": len(pool),
           "thresholds": {"score": a.threshold, "known_family_identity": a.min_id},
           "definitions": {
               "putative_novel": f"score >= {a.threshold}, not annotated holin, not a spanin, and < {a.min_id} "
                                 "identity to ANY of the 5,055 known holins",
               "known_family_new_member": f"same but >= {a.min_id} identity to a known holin -- a real holin, just "
                                          "unannotated in its genome, not a discovery",
               "strong": "putative_novel AND sitting within 3 genes of an annotated endolysin/spanin (independent "
                         "of the model, which never sees genomic context)"},
           "recovery_check": {"pool_annotated_holins": len(ann), "scored_over_threshold": rec},
           "counts": {"candidates": len(cand), "putative_novel": len(novel),
                      "putative_novel_with_lysis_context_STRONG": len(strong_rows),
                      "known_family_new_members": len(known_member)},
           "strong_candidates": strong_rows,
           "putative_novel_no_context": novel_nocontext_rows[:60],
           "known_family_new_members": known_member_rows[:60]}
    (B / "reports/novel_holin_candidates.json").write_text(json.dumps(out, indent=2))

    def md_table(rows, n):
        L = ["| score | id→known | len | lysis context | accession | gene | product |",
             "|---|---|---|---|---|---|---|"]
        for p in rows[:n]:
            ctx = ", ".join(p["lysis_neighbours"][:2]) if p["lysis_neighbours"] else "—"
            L.append(f"| {p['score']:.3f} | {p['max_identity_to_known_holin']:.2f} | {p['length']} | "
                     f"{ctx} | {p['accession']} | {(p['gene'] or '—')[:10]} | {(p['product'] or '—')[:38]} |")
        return "\n".join(L)
    md = [f"# Putative novel holins from the mined pool", "",
          f"Model `holin_model_curated.pkl` scored {len(pool):,} proteins from 300 phage genomes "
          f"(none in the benchmark). Recovery check: {rec}/{len(ann)} of the pool's own annotated holins score "
          f"≥ {a.threshold}.", "",
          f"**Putative novel** = score ≥ {a.threshold}, un-annotated, not a spanin, and < {a.min_id} identity to "
          f"any of 5,055 known holins. **Strong** adds a lysis-cassette neighbour (evidence the model never sees).",
          "", f"- Strong (score + context + no homology): **{len(strong_rows)}**",
          f"- Putative novel, no genomic context: **{len(novel_nocontext_rows)}**",
          f"- Known family, just unannotated here (not novel): **{len(known_member)}**", "",
          "## Strongest candidates — high score, lysis-cassette context, no homology to a known holin", "",
          md_table(strong_rows, 40) if strong_rows else "_none_", "",
          "## Putative novel without genomic context (treat with more caution)", "",
          md_table(novel_nocontext_rows, 25), "",
          "## Known families, newly found members (validation, not discovery)", "",
          md_table(known_member_rows, 15)]
    (B / "reports/novel_holin_candidates.md").write_text("\n".join(md))
    print(json.dumps(out["counts"], indent=1))
    print("wrote reports/novel_holin_candidates.{json,md}")


if __name__ == "__main__":
    main()
