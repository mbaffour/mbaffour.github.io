"""Paired, cross-validated comparison of two whole systems (three models + context), class by class.

Both systems use the SAME 5 folds over the CPT genomes; within each, the context parameters are chosen on the other
four folds for each system separately, and the held-out genomes' curated-gene ranks are compared gene by gene.
Genome-bootstrap 95% CIs on the difference (B - A).

Usage: python3 scripts/47_system_compare.py   (A = previous shipped models, B = evidence-only endolysin + signal spanin)
"""
import importlib, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
C = importlib.import_module("46_context_rerank")
B = Path(__file__).resolve().parent.parent
SYSTEMS = {"A_previous": {"endolysin": ("endolysin_positives_v1.json", False, "spanin_positives.json"),
                          "spanin": ("endolysin_positives.json", "auto", "spanin_positives.json")},
           "B_new": {"endolysin": ("endolysin_positives_v1_evidence.json", False, "spanin_positives.json"),
                     "spanin": ("endolysin_positives.json", "auto", "spanin_positives_signal.json")}}
GRID = [(b, w) for b in (0.0, 1, 2, 3, 4, 6, 8, 10, 12, 16) for w in (1, 2, 3, 4, 6)]


def oof(G, cls, mode, fold, k=5):
    R = {}
    for f in range(k):
        tr = [g for g, ff in zip(G, fold) if ff != f]; te = [g for g, ff in zip(G, fold) if ff == f]
        obj = lambda bw: np.mean([C.summary(C.ranks_for(tr, cls, mm, *bw))["best1"] for mm in ("family", "sequence")])
        sc = {bw: obj(bw) for bw in GRID}; bw = max(sc, key=lambda x: (round(sc[x], 6), -x[0]))
        tg = [g for g in te if g["truth"].get(cls) and cls in g["scores"][mode]]
        for g, r in zip(tg, C.ranks_for(tg, cls, mode, *bw)): R[g["name"]] = r
    return R


def main():
    loaded = {}
    for name, over in SYSTEMS.items():
        C.SHIPPED.update(over); loaded[name] = C.load("cpt")
    names = [g["name"] for g in loaded["A_previous"]]
    assert names == [g["name"] for g in loaded["B_new"]]
    fold = np.random.default_rng(0).permutation(len(names)) % 5
    out = {}
    for cls in C.CLASSES:
        for mode, lab in (("family", "novel"), ("sequence", "known")):
            RA, RB = oof(loaded["A_previous"], cls, mode, fold), oof(loaded["B_new"], cls, mode, fold)
            gs = sorted(set(RA) & set(RB))
            def st(sel, R, f):
                if f == "best1": return float(np.mean([min(R[g]) == 1 for g in sel]))
                v = np.concatenate([np.array(R[g]) for g in sel]); return float(np.mean(v == 1 if f == "top1" else v <= 5))
            row = {"genomes": len(gs)}
            for f in ("top1", "top5", "best1"):
                rng = np.random.default_rng(0); d = []
                for _ in range(4000):
                    sel = [gs[i] for i in rng.integers(0, len(gs), len(gs))]; d.append(st(sel, RB, f) - st(sel, RA, f))
                d = np.array(d)
                row[f] = {"A": round(st(gs, RA, f), 3), "B": round(st(gs, RB, f), 3), "delta": round(st(gs, RB, f) - st(gs, RA, f), 3),
                          "CI95": [round(float(np.percentile(d, 2.5)), 3), round(float(np.percentile(d, 97.5)), 3)],
                          "p": round(float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))), 4)}
            out.setdefault(cls, {})[lab] = row
            print(f"  {cls:<9} {lab:<6} genomes {len(gs):>3} | " + " | ".join(
                f"{f} {row[f]['A']:.3f}->{row[f]['B']:.3f} ({row[f]['delta']:+.3f} {row[f]['CI95']} p={row[f]['p']})"
                for f in ("top1", "top5", "best1")), flush=True)
    (B / "reports/system_compare_cv.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
