"""Does adding the HMM scan actually make the pipeline better? Measure it, per class, over many genomes.

The claim to test is narrow and falsifiable: for a lysis gene we know is there, does EVIDENCE-AWARE ranking
(domain tier first, then model probability -- scripts/32 --domains) put it nearer the top than MODEL-ONLY
ranking does? Reported per class as median rank, top-1 rate and recall@5 over every annotated lysis gene in the
panel.

READ THE CIRCULARITY CAVEAT. Ground truth here is the GenBank product name, and phage lysis-gene annotations are
themselves usually produced by homology or domain search. So the HMM half of the pipeline shares a lineage with
the labels it is being scored against, and its advantage on annotated genes is partly circular. The model-only
number does not have that problem. Two consequences:
  - an HMM win on ANNOTATED genes is weaker evidence than it looks;
  - the case that matters (an unannotated 'hypothetical protein' in an out-of-distribution genome, i.e. DAC15
    gp039) has no ground truth at all, so it cannot be scored here -- only inspected.
Both numbers are reported so the reader can discount the first.

Also reported separately: truths whose product name marks them VIRION-associated (T4 gp5 'baseplate hub subunit
and tail lysozyme', T7 p51 'internal virion protein with endolysin domain'). Those are ENTRY lysins, not exit
lysins; the benchmark's name-based label conflates them, and scripts/domains.py deliberately grades their family
(PF18013) as never-promoting. Scoring them as endolysins penalises the pipeline for being right, so the
'exit-only' row is the fairer of the two.

Genomes with no annotated lysis gene are not scored; they are reported under "discovery" with whatever the
pipeline found, which is the only thing that can be said about them honestly.

Usage: python3 scripts/37_eval_hybrid.py --genbanks data/raw/panel/*.gb data/raw/genomes/*.gb
                                         [--out reports/hybrid_eval.json]
"""
import argparse, glob, importlib, json, pickle, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import domains as D
S5 = importlib.import_module("05_scan_genome")
SC = importlib.import_module("29_scan_cassette")

B = Path(__file__).resolve().parent.parent
CLASSES = SC.CLASSES
TRUTH = {
    "holin": re.compile(r"\bholin\b", re.I),
    "endolysin": re.compile(r"endolysin|lysozyme|muramidase|amidase|peptidoglycan hydrolase|murein|"
                            r"glucosaminidase|\blysin\b|transglycosylase|glycoside hydrolase", re.I),
    "spanin": re.compile(r"spanin|\bRz1?\b", re.I)}
ANTI = re.compile(r"antiholin|anti-holin", re.I)


def ranks(vals, tiers=None):
    """1-based ranks, descending. With tiers, sort by (tier, value) -- the evidence-aware order."""
    key = (lambda i: (-tiers[i], -vals[i])) if tiers is not None else (lambda i: -vals[i])
    out = [0] * len(vals)
    for r, i in enumerate(sorted(range(len(vals)), key=key), 1): out[i] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genbanks", nargs="+", required=True)
    ap.add_argument("--out", default="reports/hybrid_eval.json")
    ap.add_argument("--hmm-dir")
    a = ap.parse_args()
    paths = sorted({p for g in a.genbanks for p in glob.glob(g)})
    print(f"{len(paths)} genomes", flush=True)

    models = {c: pickle.load(open(B / "models" / SC.MODELS[c], "rb"))["model"] for c in CLASSES}
    esm = F.ESM(B / "models/esm_cache")
    hmms, cls_of = D.lysis_hmms(a.hmm_dir)
    print(f"{len(hmms)} lysis HMMs", flush=True)

    per_gene, discovery, failed = [], [], []
    for n, path in enumerate(paths, 1):
        try:
            ps = [p for p in S5.annotated_proteins(path) if p.get("sequence")]
        except Exception as e:
            failed.append({"genome": Path(path).name, "error": f"{type(e).__name__}: {e}"}); continue
        scor = [p for p in ps if 20 <= len(p["sequence"]) <= 2000]
        if not scor: continue
        X = np.hstack([np.array([F.handcrafted(p["sequence"]) for p in scor]),
                       esm.embed([p["sequence"] for p in scor])])
        P = {c: models[c].predict_proba(X)[:, 1] for c in CLASSES}
        hits = D.scan({p["id"]: p["sequence"] for p in ps}, hmms, cls_of)   # ALL proteins, incl. over the cap
        tier = {p["id"]: {c: D.tier(hits.get(p["id"]), c) for c in CLASSES} for p in ps}

        name = Path(path).stem
        truths = []
        for i, p in enumerate(scor):
            prod = p.get("product") or ""
            if ANTI.search(prod): continue                      # an antiholin is not a holin
            for c in CLASSES:
                if TRUTH[c].search(prod): truths.append((i, c, prod))
        mr = {c: ranks(list(P[c])) for c in CLASSES}
        er = {c: ranks(list(P[c]), [tier[p["id"]][c] for p in scor]) for c in CLASSES}

        if truths:
            for i, c, prod in truths:
                pid = scor[i]["id"]
                per_gene.append({"genome": name, "id": pid, "class": c, "product": prod[:70],
                                 "length": len(scor[i]["sequence"]), "P": round(float(P[c][i]), 4),
                                 "model_rank": mr[c][i], "evidence_rank": er[c][i],
                                 "tier": tier[pid][c], "n_scored": len(scor),
                                 "virion_named": bool(D.STRUCT.search(prod)),
                                 "domains": D.summarise(hits.get(pid))})
        else:
            best = {}
            for c in CLASSES:
                j = int(np.argmax(P[c]))
                dom_i = [p["id"] for p in ps if tier[p["id"]][c] >= 2]
                best[c] = {"top_model": {"id": scor[j]["id"], "P": round(float(P[c][j]), 4),
                                         "start": scor[j]["start"], "strand": scor[j]["strand"],
                                         "length": len(scor[j]["sequence"])},
                           "domain_hits": [{"id": k, "domains": D.summarise(hits.get(k)),
                                            "P": round(float(P[c][[p["id"] for p in scor].index(k)]), 4)
                                                 if k in [p["id"] for p in scor] else None}
                                           for k in dom_i]}
            discovery.append({"genome": name, "n_cds": len(ps), "n_scored": len(scor), "by_class": best})
        if n % 10 == 0 or n == len(paths): print(f"  {n}/{len(paths)} {name}", flush=True)

    # ---- aggregate ----
    def agg(rows):
        if not rows: return None
        m = [r["model_rank"] for r in rows]; e = [r["evidence_rank"] for r in rows]
        return {"n": len(rows),
                "median_model_rank": float(np.median(m)), "median_evidence_rank": float(np.median(e)),
                "top1_model": round(sum(x == 1 for x in m) / len(m), 3),
                "top1_evidence": round(sum(x == 1 for x in e) / len(e), 3),
                "recall_at5_model": round(sum(x <= 5 for x in m) / len(m), 3),
                "recall_at5_evidence": round(sum(x <= 5 for x in e) / len(e), 3),
                "improved": sum(ev < mo for ev, mo in zip(e, m)),
                "worsened": sum(ev > mo for ev, mo in zip(e, m)),
                "unchanged": sum(ev == mo for ev, mo in zip(e, m)),
                "with_domain_evidence": sum(r["tier"] >= 2 for r in rows)}

    out = {"n_genomes": len(paths), "n_genomes_with_truth": len({r["genome"] for r in per_gene}),
           "n_truth_genes": len(per_gene), "failed": failed,
           "caveat": "Ground truth is the GenBank product name, and phage lysis annotations are themselves "
                     "usually made by homology/domain search, so the HMM half shares a lineage with the labels "
                     "and its advantage on annotated genes is partly circular. The model-only column does not "
                     "have that problem. An unannotated gene in an out-of-distribution genome cannot be scored "
                     "here at all.",
           "by_class": {}, "by_class_exit_only": {}, "genes": per_gene, "discovery": discovery}
    for c in CLASSES:
        out["by_class"][c] = agg([r for r in per_gene if r["class"] == c])
        out["by_class_exit_only"][c] = agg([r for r in per_gene if r["class"] == c and not r["virion_named"]])
    (B / a.out).write_text(json.dumps(out, indent=1))

    print(f"\n{len(per_gene)} annotated lysis genes in {out['n_genomes_with_truth']} genomes "
          f"({len(discovery)} genomes had none)\n")
    hdr = f"{'class':<11}{'n':>4}{'med rank':>19}{'top-1':>15}{'recall@5':>16}{'better':>8}{'worse':>7}"
    for label, key in (("ALL annotated truths", "by_class"), ("EXIT lysins only (fairer)", "by_class_exit_only")):
        print(f"-- {label}"); print(hdr); print(f"{'':<11}{'':>4}{'model -> evid':>19}{'model -> evid':>15}{'model -> evid':>16}")
        for c in CLASSES:
            v = out[key][c]
            if not v: print(f"{c:<11}{'0':>4}  (none)"); continue
            print(f"{c:<11}{v['n']:>4}{v['median_model_rank']:>9.0f} ->{v['median_evidence_rank']:>6.0f}"
                  f"{v['top1_model']:>8.2f} ->{v['top1_evidence']:>5.2f}"
                  f"{v['recall_at5_model']:>9.2f} ->{v['recall_at5_evidence']:>5.2f}"
                  f"{v['improved']:>8}{v['worsened']:>7}")
        print()
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
