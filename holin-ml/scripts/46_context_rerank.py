"""Genomic context: re-rank each class's candidates using the OTHER lysis genes' scores nearby.

Holin, endolysin and spanin genes sit together in the lysis cassette, but each model scores a protein in isolation.
Here, for class c, a protein's score is combined with the strongest OTHER-class score among its genomic neighbours:

    z_c(i) = logit(P_c(i)) + beta * max_{j within W genes of i, j != i}  max_{c' != c} P_c'(j)

Within one neighbourhood the ranking is unchanged (same context term); what changes is that a weak candidate sitting
next to a strong holin/endolysin/spanin can overtake a strong candidate elsewhere in the genome.

Leakage control. Every score used -- the candidate's and its neighbours' -- comes from the leave-one-genome-out
checkpoints of scripts/40, i.e. from models with that genome's curated genes (near-copies, or the whole family) removed.
Where a class has no checkpoint for a genome (no curated gene of that class there), that class contributes no context:
nothing is filled in from a model that trained on the genome.

Selection. beta and W are chosen on ONE benchmark (--tune) and then frozen and reported on another (--test), so the
reported gain is not fitted to the set it is measured on.

Usage: python3 scripts/46_context_rerank.py --tune cpt --test validated_denovo
"""
import argparse, glob, importlib, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
L = importlib.import_module("40_logo_benchmark")
S5 = importlib.import_module("05_scan_genome")
B = Path(__file__).resolve().parent.parent
CLASSES = ("holin", "endolysin", "spanin")
SETS = {  # name: (genome glob, truth file, checkpoint root, de novo?)
    "cpt": ("data/raw/cpt/genomes/*.gb", "data/raw/cpt/truth.json", ".fitckpt_cpt", False),
    "validated": ("data/raw/validated/genomes/*.gb", "data/raw/validated/truth.json", ".fitckpt_validated", False),
    "validated_denovo": ("data/raw/validated/genomes/*.gb", "data/raw/validated/truth.json", ".fitckpt_validated_denovo", True)}
SHIPPED = {"endolysin": ("endolysin_positives_v1.json", False), "holin": ("endolysin_positives.json", "auto"),
           "spanin": ("endolysin_positives.json", "auto")}
# --endo-positives FILE: read the endolysin scores of a candidate training set instead of the shipped one
if "--endo-positives" in sys.argv:
    SHIPPED["endolysin"] = (sys.argv[sys.argv.index("--endo-positives") + 1], False)


def ckdirs(root):
    out = {}
    for d in glob.glob(str(B / root / "*")):
        c = json.load(open(Path(d) / "config.json"))
        for cls, (epos, es) in SHIPPED.items():
            if c["endolysin"].endswith(epos) and c["hp"]["early_stopping"] == es and not c.get("extra"): out[cls] = Path(d)
    return out


def load(name):
    pat, tf, root, denovo = SETS[name]
    TF = json.load(open(B / tf)); dirs = ckdirs(root); G = []
    for p in sorted(glob.glob(str(B / pat))):
        stem = Path(p).stem
        if stem not in TF: continue
        ann = [x for x in S5.annotated_proteins(p) if x.get("sequence")]
        ps = [x for x in (L.denovo_from_genbank(p) if denovo else ann) if 20 <= len(x["sequence"]) <= 2000]
        aseq = {x["id"]: x["sequence"] for x in ann}; idx = {x["id"]: i for i, x in enumerate(ps)}
        truth = {}
        for c, ids in TF[stem].items():
            t = [L.seq_place(aseq.get(pid, ""), ps) if denovo else idx.get(pid) for pid in ids]
            truth[c] = [i for i in t if i is not None]
        order = np.argsort([x["start"] for x in ps]); pos = np.empty(len(ps), int); pos[order] = np.arange(len(ps))
        sc = {m: {} for m in ("family", "sequence")}
        for m in sc:
            for c in CLASSES:
                if c in dirs:
                    v = L.ck_load(dirs[c], c, m, stem, len(ps))
                    if v is not None: sc[m][c] = v
        G.append({"name": stem, "pos": pos, "truth": truth, "scores": sc, "n": len(ps)})
    return G


def logit(p): p = np.clip(p, 1e-6, 1 - 1e-6); return np.log(p / (1 - p))


def ranks_for(G, cls, mode, beta, W):
    out = []
    for g in G:
        if not g["truth"].get(cls) or cls not in g["scores"][mode]: continue
        z = logit(g["scores"][mode][cls])
        if beta:
            other = [g["scores"][mode][c] for c in CLASSES if c != cls and c in g["scores"][mode]]
            if other:
                o = np.max(np.vstack(other), 0); pos = g["pos"]; ctx = np.zeros(g["n"])
                byp = np.empty(g["n"]); byp[pos] = o            # other-class score by genomic position
                for i in range(g["n"]):
                    lo, hi = max(0, pos[i] - W), min(g["n"], pos[i] + W + 1)
                    nb = [byp[k] for k in range(lo, hi) if k != pos[i]]
                    ctx[i] = max(nb) if nb else 0.0
                z = z + beta * ctx
        order = np.argsort(-z, kind="stable"); r = np.empty(g["n"], int); r[order] = np.arange(1, g["n"] + 1)
        out.append([int(r[i]) for i in g["truth"][cls]])
    return out


def summary(rk):
    genes = np.concatenate([np.array(x) for x in rk]) if rk else np.array([])
    return {"genes": int(len(genes)), "genomes": len(rk), "top1": float(np.mean(genes == 1)),
            "top5": float(np.mean(genes <= 5)), "best1": float(np.mean([min(x) == 1 for x in rk])),
            "best5": float(np.mean([min(x) <= 5 for x in rk]))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--endo-positives"); ap.add_argument("--tune", default="cpt"); ap.add_argument("--test", nargs="+",
        default=["validated_denovo", "validated"]); ap.add_argument("--out", default="reports/context_rerank.json")
    a = ap.parse_args()
    T = load(a.tune); print(f"tune set {a.tune}: {len(T)} genomes", flush=True)
    grid = [(b, w) for b in (0.0, 1, 2, 3, 4, 6, 8, 10, 12, 16) for w in (1, 2, 3, 4, 6)]
    best = {}
    for cls in CLASSES:
        def obj(b, w):  # mean over both protocols of best-per-genome top-1 (fair for spanin pairs)
            return np.mean([summary(ranks_for(T, cls, m, b, w))["best1"] for m in ("family", "sequence")])
        sc = {bw: obj(*bw) for bw in grid}
        best[cls] = max(sc, key=lambda bw: (round(sc[bw], 6), -bw[0]))   # ties -> smaller beta
        print(f"  {cls}: chosen beta={best[cls][0]} W={best[cls][1]} (tune objective {sc[best[cls]]:.3f} vs "
              f"{sc[(0.0, 1)]:.3f} without context)", flush=True)
    res = {"chosen_on": a.tune, "params": {c: {"beta": b, "W": w} for c, (b, w) in best.items()}, "sets": {}}
    for name in [a.tune] + a.test:
        G = T if name == a.tune else load(name); res["sets"][name] = {}
        print(f"\n== {name}{' (TUNING SET -- optimistic)' if name == a.tune else ' (held out)'}: {len(G)} genomes")
        for cls in CLASSES:
            for m, lab in (("family", "novel"), ("sequence", "known")):
                s0 = summary(ranks_for(G, cls, m, 0.0, 1)); s1 = summary(ranks_for(G, cls, m, *best[cls]))
                res["sets"][name].setdefault(cls, {})[lab] = {"model_only": s0, "with_context": s1}
                print(f"  {cls:<9} {lab:<6} n={s0['genes']:>3}/{s0['genomes']:>3}  ranked 1st {s0['top1']:.3f} -> {s1['top1']:.3f}"
                      f"   top5 {s0['top5']:.3f} -> {s1['top5']:.3f}   best-per-genome 1st {s0['best1']:.3f} -> {s1['best1']:.3f}")
    (B / a.out).write_text(json.dumps(res, indent=1)); print(f"\nwrote {a.out}")


if __name__ == "__main__" and "--cv" not in sys.argv and "--calls" not in sys.argv:
    main()


def cross_validate(name="cpt", k=5, seed=0, out=None):
    out = out or ("reports/context_rerank_cv.json" if "--endo-positives" not in sys.argv else "reports/context_rerank_cv_evidence.json")
    """Honest estimate on the large set: genomes split into k folds; for each fold, beta and W are chosen on the other
    k-1 folds only, then frozen and applied to the held-out fold. Paired genome-bootstrap CI on the difference."""
    G = load(name); rng = np.random.default_rng(seed); fold = rng.permutation(len(G)) % k
    grid = [(b, w) for b in (0.0, 1, 2, 3, 4, 6, 8, 10, 12, 16) for w in (1, 2, 3, 4, 6)]
    res = {}
    for cls in CLASSES:
        for m, lab in (("family", "novel"), ("sequence", "known")):
            base, ctx, chosen = {}, {}, []
            for f in range(k):
                tr = [g for g, ff in zip(G, fold) if ff != f]; te = [g for g, ff in zip(G, fold) if ff == f]
                obj = lambda bw: np.mean([summary(ranks_for(tr, cls, mm, *bw))["best1"] for mm in ("family", "sequence")])
                sc = {bw: obj(bw) for bw in grid}; bw = max(sc, key=lambda x: (round(sc[x], 6), -x[0])); chosen.append(bw)
                tg = [g for g in te if g["truth"].get(cls) and cls in g["scores"][m]]
                for g, r0, r1 in zip(tg, ranks_for(tg, cls, m, 0.0, 1), ranks_for(tg, cls, m, *bw)):
                    base[g["name"]] = r0; ctx[g["name"]] = r1
            names = sorted(base)
            def stat(ns, R, f):
                if f == "top1": v = np.concatenate([np.array(R[n]) == 1 for n in ns])
                elif f == "top5": v = np.concatenate([np.array(R[n]) <= 5 for n in ns])
                else: v = np.array([min(R[n]) == 1 for n in ns])
                return float(np.mean(v))
            row = {"genomes": len(names), "chosen_per_fold": [list(x) for x in chosen]}
            for f in ("top1", "top5", "best1"):
                d = []; r = np.random.default_rng(0)
                for _ in range(2000):
                    ns = [names[i] for i in r.integers(0, len(names), len(names))]
                    d.append(stat(ns, ctx, f) - stat(ns, base, f))
                row[f] = {"model_only": round(stat(names, base, f), 3), "with_context": round(stat(names, ctx, f), 3),
                          "delta": round(stat(names, ctx, f) - stat(names, base, f), 3),
                          "delta_CI95": [round(float(np.percentile(d, 2.5)), 3), round(float(np.percentile(d, 97.5)), 3)]}
            res.setdefault(cls, {})[lab] = row
            print(f"  {cls:<9} {lab:<6} genomes {len(names):>3} | " + " | ".join(
                f"{f} {row[f]['model_only']:.3f}->{row[f]['with_context']:.3f} ({row[f]['delta']:+.3f} {row[f]['delta_CI95']})"
                for f in ("top1", "top5", "best1")) + f" | params per fold {sorted(set(map(tuple, row['chosen_per_fold'])))}", flush=True)
    (B / out).write_text(json.dumps(res, indent=1)); print(f"wrote {out}")


if __name__ == "__main__" and "--cv" in sys.argv:
    cross_validate()


def call_curve(name="cpt", k=5, seed=0, out=None):
    out = out or ("reports/context_calls_cv.json" if "--endo-positives" not in sys.argv else "reports/context_calls_cv_evidence.json")
    """What a CALL is worth. Per genome and class, the caller names the top context-ranked protein if its context score
    z clears a cut-off. Out-of-fold only (context parameters chosen on the other folds). For each cut-off: precision =
    calls that are the curated gene; recall = genomes whose curated gene was called. Genomes are those with a curated
    gene of the class -- a genome lacking the gene cannot be scored here (see the report)."""
    G = load(name); rng = np.random.default_rng(seed); fold = rng.permutation(len(G)) % k
    grid = [(b, w) for b in (0.0, 1, 2, 3, 4, 6, 8, 10, 12, 16) for w in (1, 2, 3, 4, 6)]
    res = {}
    for cls in CLASSES:
        for m, lab in (("family", "novel"), ("sequence", "known")):
            pairs = []
            for f in range(k):
                tr = [g for g, ff in zip(G, fold) if ff != f]; te = [g for g, ff in zip(G, fold) if ff == f]
                obj = lambda bw: np.mean([summary(ranks_for(tr, cls, mm, *bw))["best1"] for mm in ("family", "sequence")])
                sc = {bw: obj(bw) for bw in grid}; b, w = max(sc, key=lambda x: (round(sc[x], 6), -x[0]))
                for g in te:
                    if not g["truth"].get(cls) or cls not in g["scores"][m]: continue
                    z = logit(g["scores"][m][cls])
                    other = [g["scores"][m][c] for c in CLASSES if c != cls and c in g["scores"][m]]
                    if other and b:
                        o = np.max(np.vstack(other), 0); byp = np.empty(g["n"]); byp[g["pos"]] = o
                        for i in range(g["n"]):
                            p = g["pos"][i]; nb = [byp[q] for q in range(max(0, p - w), min(g["n"], p + w + 1)) if q != p]
                            z[i] += b * (max(nb) if nb else 0.0)
                    top = int(np.argmax(z)); pairs.append((float(z[top]), top in g["truth"][cls]))
            zs = np.array([p[0] for p in pairs]); ok = np.array([p[1] for p in pairs]); n = len(pairs)
            curve = []
            for t in (-6, -4, -2, 0, 2, 4, 6, 8, 10):
                c = zs >= t
                curve.append({"z_cutoff": t, "calls": int(c.sum()), "precision": round(float(ok[c].mean()), 3) if c.any() else None,
                              "recall": round(float((c & ok).sum() / n), 3)})
            res.setdefault(cls, {})[lab] = {"genomes": n, "top1_correct_if_always_called": round(float(ok.mean()), 3),
                                            "curve": curve}
            print(f"  {cls:<9} {lab:<6} n={n:>3}  always-call precision {ok.mean():.3f} | " + "  ".join(
                f"z>={r['z_cutoff']}: P {r['precision']} R {r['recall']}" for r in curve if r["precision"] is not None), flush=True)
    (B / out).write_text(json.dumps(res, indent=1)); print(f"wrote {out}")


if __name__ == "__main__" and "--calls" in sys.argv:
    call_curve()
