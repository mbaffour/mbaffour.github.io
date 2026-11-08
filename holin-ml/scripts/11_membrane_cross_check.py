"""Scan real phage genomes with the holin model and test the hits against INDEPENDENT membrane evidence.

Holins are integral membrane proteins, so a true holin call should also be a transmembrane protein. The model
never sees a topology prediction: its only hydrophobicity inputs are Kyte-Doolittle derived, computed from the
sequence itself. The membrane evidence used here comes from the sibling dirty-science-canvas project, where
every annotated phage protein was submitted to Phobius, DeepTMHMM and TOPCONS2 and the returned topologies
were normalized. That makes "is it in the membrane?" an outside check rather than the model restating itself.

For every protein of every phage with complete topology we record:
  - the model's holin score
  - TM-segment counts from each of the three predictors, and how many of the three call >= 1 TM
  - the GenBank product annotation, and whether it says "holin"
  - whether the protein is homologous to a training holin, so recovered training material is separable
    from genuinely new calls

Usage: python3 scripts/11_membrane_cross_check.py [--dsc <path>] [--top 10] [--min-score 80]
"""
import argparse, glob, importlib, json, os, pickle, re, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
CL = importlib.import_module("03_cluster")

B = Path(__file__).resolve().parent.parent
DSC_DEFAULT = "/home/user/mbaffour.github.io/dirty-science-canvas"
METHODS = ("Phobius", "DeepTMHMM", "TOPCONS2")
HOLIN_WORD = re.compile(r"holin", re.I)
ANTI_ONLY = re.compile(r"anti-?holin", re.I)


def load_phages(dsc):
    """Every phage organism whose three main methods are complete, with per-protein TM counts."""
    out = []
    for p in sorted(glob.glob(os.path.join(dsc, "*_Topology_Lab_Reference", "data.json"))):
        d = json.load(open(p))
        if d.get("kind") != "phage":
            continue
        prots = []
        for r in d["proteins"]:
            st = r.get("status", {})
            if any(st.get(m) != "complete" for m in METHODS):
                continue
            tm = {}
            for m in METHODS:
                spans = (r["pred"].get(m) or {}).get("spans") or []
                tm[m] = sum(1 for s in spans if len(s) > 2 and s[2] == "M")
            prod = r.get("product") or ""
            prots.append({"protein_id": r["protein_id"], "gene": r.get("gene") or "", "product": prod,
                          "length": r["length"], "sequence": r["sequence"], "tm": tm,
                          "n_methods_membrane": sum(1 for m in METHODS if tm[m] >= 1),
                          "annotated_holin": bool(HOLIN_WORD.search(prod)),
                          "annotated_antiholin_only": bool(ANTI_ONLY.search(prod)) and not re.search(r"(?<!anti[- ])holin", prod, re.I)})
        if prots:
            out.append({"organism": d["organism"], "key": d["key"], "accession": d.get("accession"), "proteins": prots})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsc", default=DSC_DEFAULT)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--min-score", type=int, default=80, help="SW score at which a protein counts as homologous to a training holin")
    a = ap.parse_args()

    mdl = pickle.load(open(B / "models/holin_model.pkl", "rb"))
    esm = F.ESM(B / "models/esm_cache")
    genomes = load_phages(a.dsc)
    if not genomes:
        print("no phage genomes with complete topology found under", a.dsc); return
    print(f"{len(genomes)} phage genomes, {sum(len(g['proteins']) for g in genomes)} proteins with all three topology methods", flush=True)

    seqs = [p["sequence"] for g in genomes for p in g["proteins"]]
    t = time.time()
    X = np.hstack([np.array([F.handcrafted(s) for s in seqs]), esm.embed(seqs)])
    score = mdl["model"].predict_proba(X)[:, 1]
    print(f"scored {len(seqs)} proteins in {int(time.time()-t)}s", flush=True)

    # homology to training holins, so "new call" and "recovered training holin" stay separable
    train = [r for r in json.load(open(B / "data/processed/dataset.json")) if r["label"] == "holin"]
    t = time.time()
    hom = CL.search([r["sequence"] for r in train], seqs, a.min_score)
    print(f"homology screen vs {len(train)} training holins in {int(time.time()-t)}s", flush=True)

    i = 0
    for g in genomes:
        for p in g["proteins"]:
            p["score"] = float(score[i]); p["homolog_identity_to_training_holin"] = float(hom[i]); i += 1

    allp = [dict(p, organism=g["organism"], key=g["key"]) for g in genomes for p in g["proteins"]]
    allp.sort(key=lambda p: -p["score"])

    # ---- does membrane evidence actually sharpen the model? annotated "holin" is the reference here ----
    ann = np.array([p["annotated_holin"] for p in allp])
    sc = np.array([p["score"] for p in allp])
    mem2 = np.array([p["n_methods_membrane"] >= 2 for p in allp])
    gates = {}
    for thr in (0.5, 0.9, 0.95, 0.99):
        for name, keep in (("score only", sc >= thr), ("score AND >=2/3 methods call TM", (sc >= thr) & mem2)):
            n = int(keep.sum()); tp = int((keep & ann).sum())
            gates.setdefault(f"score >= {thr}", {})[name] = {
                "n_called": n, "annotated_holin": tp,
                "precision_vs_annotation": round(tp / n, 3) if n else None,
                "recall_of_annotated": round(tp / int(ann.sum()), 3) if ann.sum() else None}

    print("\n=== top hits per genome " + "=" * 40)
    per_genome = {}
    for g in genomes:
        rows = sorted(g["proteins"], key=lambda p: -p["score"])[:a.top]
        per_genome[g["key"]] = rows
        print(f"\n{g['organism']} ({g['key']}, {g['accession']}, {len(g['proteins'])} proteins)")
        print(f"  {'#':>2} {'score':>6} {'TM Ph/DT/TC':>12} {'len':>4} {'hom':>5}  {'gene':<8} product")
        for n, p in enumerate(rows, 1):
            tm = f"{p['tm']['Phobius']}/{p['tm']['DeepTMHMM']}/{p['tm']['TOPCONS2']}"
            flag = " <-- annotated holin" if p["annotated_holin"] else ""
            print(f"  {n:>2} {p['score']:>6.3f} {tm:>12} {p['length']:>4} {p['homolog_identity_to_training_holin']:>5.2f}"
                  f"  {p['gene'][:8]:<8} {p['product'][:52]}{flag}")

    # ---- the three sets the question is really about ----
    annotated = [p for p in allp if p["annotated_holin"]]
    hit_and_membrane = [p for p in annotated if p["score"] >= 0.9 and p["n_methods_membrane"] >= 2]
    missed = [p for p in annotated if p["score"] < 0.9]
    NOVEL_CUT = 0.9
    novel = [p for p in allp if not p["annotated_holin"] and p["score"] >= NOVEL_CUT and p["n_methods_membrane"] >= 2
             and p["homolog_identity_to_training_holin"] == 0.0]
    # Recurring confusion: Rz-like spanins are also small lysis-cassette membrane proteins, so membrane
    # evidence cannot separate them from holins. Count them explicitly rather than leaving them in "novel".
    SPANIN = re.compile(r"spanin|\brz\b|rz1", re.I)
    spanin_hits = [p for p in allp if SPANIN.search(p["product"] or "") and p["score"] >= 0.5]
    novel = [p for p in novel if not SPANIN.search(p["product"] or "")]

    out = {"membrane_evidence": {"source": "dirty-science-canvas normalized Phobius / DeepTMHMM / TOPCONS2 output",
                                 "independent_of_model": "the classifier has no topology input; its only hydrophobicity features are Kyte-Doolittle"},
           "genomes": [{"organism": g["organism"], "key": g["key"], "accession": g["accession"],
                        "n_proteins": len(g["proteins"])} for g in genomes],
           "gate_comparison": gates,
           "annotated_holins": [{k: p[k] for k in ("organism", "protein_id", "gene", "product", "length", "score",
                                                   "tm", "n_methods_membrane", "homolog_identity_to_training_holin")} for p in annotated],
           "annotated_holin_and_membrane_and_called": len(hit_and_membrane),
           "annotated_holin_missed_by_model": [{k: p[k] for k in ("organism", "gene", "product", "score", "n_methods_membrane")} for p in missed],
           "spanin_confusion": {"note": "Rz/Rz1-like spanins are lysis-cassette membrane proteins too; membrane evidence does not separate them from holins",
                                "n_scored_over_0.5": len(spanin_hits),
                                "hits": [{k: p[k] for k in ("organism", "gene", "product", "score", "n_methods_membrane", "length")} for p in spanin_hits]},
           "novel_candidates_high_score_membrane_no_training_homolog":
               [{k: p[k] for k in ("organism", "protein_id", "gene", "product", "length", "score", "tm")} for p in novel[:40]],
           "top_hits_per_genome": {k: [{kk: p[kk] for kk in ("protein_id", "gene", "product", "score", "tm",
                                                             "n_methods_membrane", "annotated_holin",
                                                             "homolog_identity_to_training_holin")} for p in v]
                                   for k, v in per_genome.items()}}
    (B / "reports/membrane_cross_check.json").write_text(json.dumps(out, indent=1))

    print("\n=== does membrane evidence sharpen the call? (reference = GenBank 'holin' annotation) " + "=" * 5)
    for thr, d in gates.items():
        print(f"  {thr}")
        for name, v in d.items():
            print(f"    {name:34} called {v['n_called']:>4}  annotated-holin {v['annotated_holin']:>3}  "
                  f"precision {v['precision_vs_annotation']}  recall {v['recall_of_annotated']}")
    print(f"\nannotated holins in these genomes: {len(annotated)}")
    print(f"  scored >= 0.9 and membrane by >= 2/3 methods: {len(hit_and_membrane)}")
    print(f"  missed by the model (score < 0.9): {len(missed)}")
    for p in missed:
        print(f"    {p['organism'][:38]:38} {p['gene'][:8]:<8} score {p['score']:.3f} membrane {p['n_methods_membrane']}/3  {p['product'][:40]}")
    print(f"\nRz-like spanins scoring >= 0.5 (membrane proteins the model confuses with holins): {len(spanin_hits)}")
    for p in sorted(spanin_hits, key=lambda q: -q["score"])[:10]:
        print(f"    {p['organism'][:30]:30} {p['gene'][:8]:<8} {p['score']:.3f} membrane {p['n_methods_membrane']}/3 len {p['length']:>4}  {p['product'][:38]}")
    print(f"\nunannotated non-spanin, score >= {NOVEL_CUT}, membrane by >= 2/3, no training homolog: {len(novel)}")
    for p in novel[:15]:
        print(f"    {p['organism'][:30]:30} {p['gene'][:8]:<8} {p['score']:.3f} "
              f"TM {p['tm']['Phobius']}/{p['tm']['DeepTMHMM']}/{p['tm']['TOPCONS2']} len {p['length']:>4}  {p['product'][:44]}")


if __name__ == "__main__":
    main()
