"""Stratify the scripts/37 hybrid evaluation by genome group, because the pooled number hides the point.

The question DAC15 raised is not "does domain evidence help on well-studied coliphages" -- it is "does it help on
a genome unlike the training data". Pooling 50 classic panel phages with a handful of crAss-like ones answers the
first and buries the second, so this splits them:

  crass     Crassvirales (crAss-like), read from the GenBank ORGANISM lineage -- DAC15's neighbourhood
  serwaa    Escherichia phage Serwaa, kept separate: it is the one genome here with all four lysis genes
            independently annotated, including an i-spanin, the class absent from training until this week
  classic   everything else: the 50-genome panel of well-studied phages

The circularity caveat from scripts/37 applies to every row and is reprinted below: ground truth is the GenBank
product name, phage lysis annotations are usually made by homology or domain search, so the HMM half shares a
lineage with the labels. Discount the HMM column accordingly; the model-only column is unaffected.

Usage: python3 scripts/38_hybrid_summary.py [--eval reports/hybrid_eval.json]
"""
import argparse, glob, json, re
from pathlib import Path
import numpy as np

B = Path(__file__).resolve().parent.parent
CLASSES = ("holin", "endolysin", "spanin")


def group_of(stem, lineage_cache={}):
    if not lineage_cache:
        for p in glob.glob(str(B / "data/raw/**/*.gb"), recursive=True):
            try:
                head = open(p, errors="replace").read(6000)
            except OSError:
                continue
            lineage_cache[Path(p).stem] = head
    head = lineage_cache.get(stem, "")
    if re.search(r"phage Serwaa", head, re.I): return "serwaa"
    if re.search(r"Crassvirales", head, re.I): return "crass"
    return "classic"


def agg(rows):
    if not rows: return None
    m = [r["model_rank"] for r in rows]; e = [r["evidence_rank"] for r in rows]
    return {"n": len(rows), "med_model": float(np.median(m)), "med_evid": float(np.median(e)),
            "top1_model": sum(x == 1 for x in m) / len(m), "top1_evid": sum(x == 1 for x in e) / len(e),
            "r5_model": sum(x <= 5 for x in m) / len(m), "r5_evid": sum(x <= 5 for x in e) / len(e),
            "better": sum(a < b for a, b in zip(e, m)), "worse": sum(a > b for a, b in zip(e, m)),
            "with_domain": sum(r["tier"] >= 2 for r in rows)}


def table(title, rows):
    print(f"\n=== {title} (n={len(rows)}) ===")
    if not rows: print("  (no annotated lysis genes)"); return
    print(f"{'class':<11}{'n':>4}{'med rank':>16}{'top-1':>16}{'recall@5':>16}{'better':>8}{'worse':>7}{'dom':>5}")
    print(f"{'':<11}{'':>4}{'model->evid':>16}{'model->evid':>16}{'model->evid':>16}")
    for c in CLASSES:
        v = agg([r for r in rows if r["class"] == c])
        if not v: print(f"{c:<11}{0:>4}   --"); continue
        print(f"{c:<11}{v['n']:>4}{v['med_model']:>7.0f} ->{v['med_evid']:>6.0f}"
              f"{v['top1_model']:>9.2f} ->{v['top1_evid']:>5.2f}"
              f"{v['r5_model']:>9.2f} ->{v['r5_evid']:>5.2f}{v['better']:>8}{v['worse']:>7}{v['with_domain']:>5}")
    v = agg(rows)
    print(f"{'ALL':<11}{v['n']:>4}{v['med_model']:>7.0f} ->{v['med_evid']:>6.0f}"
          f"{v['top1_model']:>9.2f} ->{v['top1_evid']:>5.2f}"
          f"{v['r5_model']:>9.2f} ->{v['r5_evid']:>5.2f}{v['better']:>8}{v['worse']:>7}{v['with_domain']:>5}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--eval", default="reports/hybrid_eval.json")
    a = ap.parse_args()
    d = json.load(open(B / a.eval))
    genes = d["genes"]
    for r in genes: r["group"] = group_of(r["genome"])

    print(f"{d['n_genomes']} genomes scanned; {d['n_truth_genes']} annotated lysis genes in "
          f"{d['n_genomes_with_truth']} of them; {len(d['discovery'])} genomes had none to grade against.")
    print("\nCAVEAT: " + d["caveat"])

    for g, title in (("classic", "CLASSIC panel phages"), ("crass", "crAss-like (Crassvirales)"),
                     ("serwaa", "Escherichia phage Serwaa")):
        rows = [r for r in genes if r["group"] == g]
        table(title, rows)
        table(f"{title} -- EXIT lysins only (virion-named truths removed)",
              [r for r in rows if not r["virion_named"]])

    print("\n=== Serwaa, gene by gene ===")
    sr = sorted([r for r in genes if r["group"] == "serwaa"], key=lambda r: r["id"])
    if sr:
        print(f"{'gene':<20}{'class':<11}{'len':>5}{'P':>9}{'model rk':>10}{'evid rk':>9}{'tier':>6}  domains")
        for r in sr:
            print(f"{r['id']:<20}{r['class']:<11}{r['length']:>5}{r['P']:>9.4f}"
                  f"{r['model_rank']:>10}{r['evidence_rank']:>9}{r['tier']:>6}  {r['domains'] or '-'}")
    else:
        print("  (Serwaa not in this evaluation)")

    print("\n=== genomes with NO annotated lysis gene: what the pipeline found ===")
    for g in d["discovery"]:
        dom = {c: [h for h in g["by_class"][c]["domain_hits"]] for c in CLASSES}
        n = sum(len(v) for v in dom.values())
        print(f"{g['genome']:<15} {g['n_cds']:>4} CDS  domain hits: {n}")
        for c in CLASSES:
            for h in dom[c]:
                print(f"    {c:<10} {h['id']:<16} P={h['P']}  {h['domains']}")


if __name__ == "__main__":
    main()
