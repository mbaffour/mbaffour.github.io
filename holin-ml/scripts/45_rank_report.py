"""Rank metrics, with genome-bootstrap 95% CIs, for a truth-file benchmark (scripts/40 --truth-file output).

Reads each truth's rank in its genome (truth_ranks) and keeps only genomes still listed in the truth file, so a run made
before de-duplication is reported on the de-duplicated set without refitting: a genome's ranks depend only on its own
truths, not on which other genomes were in the run.

Reported per class and protocol: top-1 and top-5 over genes; and per genome, whether the BEST-ranked curated gene is 1st
or in the top 5 -- the fair measure for spanins, where an i/o pair cannot both rank first.

Usage: python3 scripts/45_rank_report.py --truth-file data/raw/cpt/truth.json --results reports/cpt_*.json
"""
import argparse, glob, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
B = Path(__file__).resolve().parent.parent


def boot(groups, stat, n=2000):
    keys = sorted(groups); rng = np.random.default_rng(0); vals = []
    for _ in range(n):
        pick = rng.choice(len(keys), size=len(keys), replace=True)
        vals.append(stat([groups[keys[i]] for i in pick]))
    return [round(float(np.percentile(vals, 2.5)), 3), round(float(np.percentile(vals, 97.5)), 3)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth-file", required=True); ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    keep = set(json.load(open(B / a.truth_file)))
    out = {}
    for f in sorted({p for r in a.results for p in glob.glob(str(B / r))}):
        for cls, e in json.load(open(f))["classes"].items():
            for proto, lab in (("sequence_removal", "known_family"), ("family_removal", "novel_family")):
                g = defaultdict(list)
                for t in e[proto]["truth_ranks"]:
                    if t["genome"] in keep: g[t["genome"]].append(t["rank"])
                genes = lambda gs: np.concatenate([np.array(x) for x in gs])
                top1 = lambda gs: float(np.mean(genes(gs) == 1)); top5 = lambda gs: float(np.mean(genes(gs) <= 5))
                b1 = lambda gs: float(np.mean([min(x) == 1 for x in gs])); b5 = lambda gs: float(np.mean([min(x) <= 5 for x in gs]))
                allg = list(g.values())
                out.setdefault(cls, {})[lab] = {
                    "genes": int(sum(len(x) for x in allg)), "genomes": len(allg),
                    "gene_top1": round(top1(allg), 3), "gene_top1_CI95": boot(g, top1),
                    "gene_top5": round(top5(allg), 3), "gene_top5_CI95": boot(g, top5),
                    "median_rank": float(np.median(genes(allg))),
                    "genome_best_top1": round(b1(allg), 3), "genome_best_top1_CI95": boot(g, b1),
                    "genome_best_top5": round(b5(allg), 3), "genome_best_top5_CI95": boot(g, b5)}
    for cls, v in out.items():
        for lab, m in v.items():
            print(f"{cls:<10} {lab:<13} genes {m['genes']:>3} genomes {m['genomes']:>3} | top1 {m['gene_top1']:.3f} {m['gene_top1_CI95']}"
                  f" top5 {m['gene_top5']:.3f} {m['gene_top5_CI95']} median {m['median_rank']:.0f} | best-per-genome 1st "
                  f"{m['genome_best_top1']:.3f} top5 {m['genome_best_top5']:.3f}")
    if a.out: (B / a.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__" and "--compare" not in sys.argv:
    main()


def compare(truth_file, base_file, new_file, cls):
    """Paired comparison of two runs on the same truth set: per genome the same curated genes, ranked by each model;
    genome-bootstrap 95% CI and two-sided p on the difference (new - base)."""
    keep = set(json.load(open(B / truth_file)))
    get = lambda f, proto: {(t["genome"], t["id"]): t["rank"] for t in json.load(open(B / f))["classes"][cls][proto]["truth_ranks"]
                            if t["genome"] in keep}
    out = {}
    for proto, lab in (("family_removal", "novel_family"), ("sequence_removal", "known_family")):
        a_, b_ = get(base_file, proto), get(new_file, proto)
        keys = sorted(set(a_) & set(b_)); byg = defaultdict(list)
        for k in keys: byg[k[0]].append(k)
        gs = sorted(byg)
        def stat(sel, R, f):
            if f == "best1": return float(np.mean([min(R[k] for k in byg[g]) == 1 for g in sel]))
            ks = [k for g in sel for k in byg[g]]
            return float(np.mean([R[k] == 1 for k in ks])) if f == "top1" else float(np.mean([R[k] <= 5 for k in ks]))
        row = {"genomes": len(gs), "genes": len(keys)}
        for f in ("top1", "top5", "best1"):
            rng = np.random.default_rng(0); d = []
            for _ in range(4000):
                sel = [gs[i] for i in rng.integers(0, len(gs), len(gs))]; d.append(stat(sel, b_, f) - stat(sel, a_, f))
            d = np.array(d); p = 2 * min((d <= 0).mean(), (d >= 0).mean())
            row[f] = {"base": round(stat(gs, a_, f), 3), "new": round(stat(gs, b_, f), 3),
                      "delta": round(stat(gs, b_, f) - stat(gs, a_, f), 3),
                      "CI95": [round(float(np.percentile(d, 2.5)), 3), round(float(np.percentile(d, 97.5)), 3)],
                      "p": round(float(min(p, 1.0)), 4)}
        out[lab] = row
        print(f"  {cls:<9} {lab:<13} genomes {len(gs):>3} | " + " | ".join(
            f"{f} {row[f]['base']:.3f}->{row[f]['new']:.3f} ({row[f]['delta']:+.3f} {row[f]['CI95']} p={row[f]['p']})"
            for f in ("top1", "top5", "best1")))
    return out


if __name__ == "__main__" and "--compare" in sys.argv:
    # usage: 45_rank_report.py --compare TRUTH BASE.json NEW.json CLASS [OUT.json]
    i = sys.argv.index("--compare"); args = sys.argv[i + 1:]
    res = compare(*args[:4])
    if len(args) > 4: (B / args[4]).write_text(json.dumps(res, indent=1))
