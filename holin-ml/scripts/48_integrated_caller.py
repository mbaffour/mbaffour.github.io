"""Integrated caller: a second-stage model per class that combines all the evidence for each protein.

The three first-stage models score proteins one at a time; the context rule (scripts/46) then adds one hand-shaped term.
This learns the combination instead. For protein i and class c, the features are:

  own evidence     logit P_holin, logit P_endolysin, logit P_spanin
  genome-relative  rank of P_c in the genome (as rank/n and log rank); gap between logit P_c and the genome's best
  neighbourhood    for each class, the strongest P among neighbours within 1, 2, 3 and 5 genes; distance in genes to
                   the genome's top-scoring protein of each class
  protein          length, log length, transmembrane segments (Kyte-Doolittle scan), lipobox in the first 35 aa
  genome           number of proteins (log)

Leakage control. Every first-stage score is a leave-one-genome-out checkpoint from scripts/40: a genome's curated genes
(near-copies, or the whole family, by protocol) were removed from training before it was scored, and for classes with
no curated gene in a genome, every training positive >= 95% identical to any of its proteins was removed (--score-all).
The second stage itself is trained and judged with genome-grouped cross-validation, so no genome is ever scored by a
second-stage model that saw it. Both protocols' rows of the training genomes are pooled, so one model serves both
regimes; it is judged on each protocol separately.

Judged against the context rule on the SAME folds (rule parameters chosen on the training folds), paired by genome.
Then trained on all CPT genomes, frozen, and tested on the experimental set, which it never sees.

Also reported: a SAME-GENE reading, where a top-ranked protein counts as the curated gene if it is the same locus read
from a different start codon (same strand, overlapping, sharing the last 20 residues) -- e.g. lambda S105 / S107.
It is reported beside the strict reading, never in place of it.

Usage: python3 scripts/48_integrated_caller.py            (CV on CPT, held-out test on the experimental set)
       python3 scripts/48_integrated_caller.py --final    (also train on all CPT and save models/integrated_caller.pkl)
"""
import glob, importlib, json, pickle, re, sys
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
sys.path.insert(0, str(Path(__file__).resolve().parent))
C = importlib.import_module("46_context_rerank")
L = importlib.import_module("40_logo_benchmark")
S5 = importlib.import_module("05_scan_genome")
import features as F
B = Path(__file__).resolve().parent.parent
CLASSES = ("holin", "endolysin", "spanin")
# the current shipped models' training sets: which checkpoints to read
C.SHIPPED.update({"endolysin": ("endolysin_positives_v1_evidence.json", False, "spanin_positives.json"),
                  "holin": ("endolysin_positives.json", "auto", "spanin_positives.json"),
                  "spanin": ("endolysin_positives.json", "auto", "spanin_positives_signal.json")})
LIPO = re.compile(r"[LVI][ASTVI][GAS]C")
WINDOWS = (1, 2, 3, 5)
FEATURES = (["lP_holin", "lP_endolysin", "lP_spanin", "rank_frac", "log_rank", "gap_to_best"]
            + [f"nb{w}_{c}" for w in WINDOWS for c in CLASSES] + [f"dist_top_{c}" for c in CLASSES]
            + ["length", "log_length", "tm_segments", "lipobox", "log_genome_size"])


def lg(p): p = np.clip(p, 1e-6, 1 - 1e-6); return np.log(p / (1 - p))


# --no-shape: drop the protein-shape features (length, TM segments, lipobox). With family-grouped folds the full feature
# set let the second stage recognise a family from shape alone and did worse than the context rule on new families;
# without them it can only learn genome logic (scores, ranks, neighbours).
SHAPE = ("length", "log_length", "tm_segments", "lipobox")
KEEP = [i for i, f in enumerate(FEATURES) if not ("--no-shape" in sys.argv and f in SHAPE)]


def genome_features(P, pos, seqs, cls):
    return _genome_features(P, pos, seqs, cls)[:, KEEP]


def _genome_features(P, pos, seqs, cls):
    """feature matrix (n x len(FEATURES)) for one genome and target class; P: {class: probabilities}, pos: positions"""
    n = len(seqs); order = np.argsort(pos); byp = {c: P[c][order] for c in CLASSES}   # by genomic position
    rk = np.empty(n); rk[np.argsort(-P[cls], kind="stable")] = np.arange(1, n + 1)
    lc = lg(P[cls]); top = {c: pos[int(np.argmax(P[c]))] for c in CLASSES}
    X = np.zeros((n, len(FEATURES)))
    for i in range(n):
        p = pos[i]; row = [lg(P["holin"][i]), lg(P["endolysin"][i]), lg(P["spanin"][i]), rk[i] / n, np.log(rk[i]),
                           lc[i] - lc.max()]
        for w in WINDOWS:
            idx = [q for q in range(max(0, p - w), min(n, p + w + 1)) if q != p]
            for c in CLASSES: row.append(max(byp[c][idx]) if idx else 0.0)
        row += [abs(p - top[c]) for c in CLASSES]
        s = seqs[i]
        row += [len(s), np.log(len(s)), len(F.tm_segments(s)), float(bool(LIPO.search(s[:35]))), np.log(n)]
        X[i] = row
    return X


def load(name):
    """per genome: sequences, positions, coordinates, truth, and per-protocol first-stage scores for all classes"""
    pat, tf, root, denovo = C.SETS[name]
    TF = json.load(open(B / tf)); dirs = C.ckdirs(root); G = []
    for p in sorted(glob.glob(str(B / pat))):
        stem = Path(p).stem
        if stem not in TF: continue
        ps = [x for x in S5.annotated_proteins(p) if x.get("sequence") and 20 <= len(x["sequence"]) <= 2000]
        idx = {x["id"]: i for i, x in enumerate(ps)}
        truth = {c: [idx[t] for t in TF[stem].get(c, []) if t in idx] for c in CLASSES}
        order = np.argsort([x["start"] for x in ps]); pos = np.empty(len(ps), int); pos[order] = np.arange(len(ps))
        sc = {}
        for m in ("family", "sequence"):
            got = {c: L.ck_load(dirs[c], c, m, stem, len(ps)) for c in CLASSES if c in dirs}
            if all(got.get(c) is not None for c in CLASSES): sc[m] = got
        if len(sc) < 2: continue
        G.append({"name": stem, "ps": ps, "pos": pos, "truth": truth, "scores": sc})
    return G


def same_gene(a, b):
    """same locus from a different start codon: same strand, overlapping, identical last 20 residues"""
    return (a["strand"] == b["strand"] and a["start"] <= b["stop"] and b["start"] <= a["stop"]
            and a["sequence"][-20:] == b["sequence"][-20:])


def build(G, cls, modes):
    X, y, gid = [], [], []
    for k, g in enumerate(G):
        seqs = [x["sequence"] for x in g["ps"]]
        for m in modes:
            Xi = genome_features(g["scores"][m], g["pos"], seqs, cls)
            X.append(Xi); yy = np.zeros(len(seqs)); yy[g["truth"][cls]] = 1; y.append(yy); gid += [k] * len(seqs)
    return np.vstack(X), np.concatenate(y), np.array(gid)


def stacker():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40,
                                          l2_regularization=1.0, early_stopping=False, random_state=0)


def ranks(score, g, cls):
    order = np.argsort(-score, kind="stable"); r = np.empty(len(score), int); r[order] = np.arange(1, len(score) + 1)
    top = int(order[0])
    hit_same = any(top == t or same_gene(g["ps"][top], g["ps"][t]) for t in g["truth"][cls])
    return [int(r[t]) for t in g["truth"][cls]], hit_same


def context_score(g, cls, m, b, w):
    P = g["scores"][m]; z = lg(P[cls]).copy()
    if b:
        o = np.max(np.vstack([P[c] for c in CLASSES if c != cls]), 0); byp = np.empty(len(z)); byp[g["pos"]] = o
        for i in range(len(z)):
            p = g["pos"][i]; nb = [byp[q] for q in range(max(0, p - w), min(len(z), p + w + 1)) if q != p]
            z[i] += b * (max(nb) if nb else 0.0)
    return z


def tune_context(G, cls):
    grid = [(b, w) for b in (0.0, 1, 2, 3, 4, 6, 8, 10, 12, 16) for w in (1, 2, 3, 4, 6)]
    def obj(bw):
        v = []
        for m in ("family", "sequence"):
            for g in G:
                if g["truth"][cls]: v.append(min(ranks(context_score(g, cls, m, *bw), g, cls)[0]) == 1)
        return np.mean(v)
    sc = {bw: obj(bw) for bw in grid}; return max(sc, key=lambda x: (round(sc[x], 6), -x[0]))


def evaluate(train, test, cls):
    """train the stacker and tune the context rule on `train`, return per-genome results on `test` for both"""
    X, y, _ = build(train, cls, ("family", "sequence")); model = stacker().fit(X, y)
    bw = tune_context(train, cls); out = {}
    for m in ("family", "sequence"):
        for g in test:
            if not g["truth"][cls]: continue
            seqs = [x["sequence"] for x in g["ps"]]
            s_int = model.predict_proba(genome_features(g["scores"][m], g["pos"], seqs, cls))[:, 1]
            out.setdefault(m, {})[g["name"]] = {"integrated": ranks(s_int, g, cls), "context": ranks(context_score(g, cls, m, *bw), g, cls),
                                                "model_only": ranks(lg(g["scores"][m][cls]), g, cls)}
    return out, model, bw


def summarise(R, label):
    res = {}
    for m, lab in (("family", "novel"), ("sequence", "known")):
        gs = sorted(R[m]); res[lab] = {}
        def st(sel, sysname, f):
            if f == "best1": return float(np.mean([min(R[m][g][sysname][0]) == 1 for g in sel]))
            if f == "same_gene_top1": return float(np.mean([R[m][g][sysname][1] for g in sel]))
            v = np.concatenate([np.array(R[m][g][sysname][0]) for g in sel]); return float(np.mean(v == 1 if f == "top1" else v <= 5))
        for f in ("top1", "top5", "best1", "same_gene_top1"):
            row = {s: round(st(gs, s, f), 3) for s in ("model_only", "context", "integrated")}
            rng = np.random.default_rng(0); d = []
            for _ in range(4000):
                sel = [gs[i] for i in rng.integers(0, len(gs), len(gs))]; d.append(st(sel, "integrated", f) - st(sel, "context", f))
            d = np.array(d)
            row["integrated_minus_context"] = round(row["integrated"] - row["context"], 3)
            row["CI95"] = [round(float(np.percentile(d, 2.5)), 3), round(float(np.percentile(d, 97.5)), 3)]
            row["p"] = round(float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))), 4)
            res[lab][f] = row
        res[lab]["genomes"] = len(gs)
        print(f"  {label:<9} {lab:<6} n={len(gs):>3} | " + " | ".join(
            f"{f} {res[lab][f]['model_only']:.3f}/{res[lab][f]['context']:.3f}/{res[lab][f]['integrated']:.3f} "
            f"(int-ctx {res[lab][f]['integrated_minus_context']:+.3f} {res[lab][f]['CI95']})"
            for f in ("top1", "top5", "same_gene_top1")), flush=True)
    return res


def family_folds(G, cls, k=5, seed=0):
    """Folds that never split a FAMILY: genomes whose curated genes of this class are >= 30% identical (the novel-family
    protocol's own rule: coverage >= 0.5, SW score >= 80) are joined into one group, and whole groups are assigned to
    folds. Without this, a related phage in the training folds lets the second stage learn the family from simple
    features (e.g. 'a 218-aa one-TM protein is the holin' from Marfa, applied to its sibling pKp20)."""
    seqs, owner = [], []
    for k_, g in enumerate(G):
        for t in g["truth"][cls]: seqs.append(g["ps"][t]["sequence"]); owner.append(k_)
    M = L.pos_truth_matrix(seqs, seqs)
    parent = list(range(len(G)))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i in range(len(seqs)):
        for j in range(len(seqs)):
            if i != j and M[i, j] >= 0.3: parent[find(owner[i])] = find(owner[j])
    groups = {}
    for k_ in range(len(G)): groups.setdefault(find(k_), []).append(k_)
    order = sorted(groups.values(), key=len, reverse=True); load_ = [0] * k; fold = {}
    rng = np.random.default_rng(seed); rng.shuffle(order); order = sorted(order, key=len, reverse=True)
    for grp in order:                                   # largest groups first, each to the emptiest fold
        f = int(np.argmin(load_)); load_[f] += len(grp)
        for k_ in grp: fold[G[k_]["name"]] = f
    sizes = sorted((len(v) for v in groups.values()), reverse=True)
    print(f"  {cls}: {len(groups)} family groups (largest {sizes[:5]}), fold sizes {load_}", flush=True)
    return fold


def main():
    G = load("cpt"); print(f"CPT: {len(G)} genomes with all three classes scored under both protocols", flush=True)
    names = sorted(g["name"] for g in G); fold_of = {n: f for n, f in zip(names, np.random.default_rng(0).permutation(len(names)) % 5)}
    grouped = "--genome-folds" not in sys.argv
    report = {"note": "columns: model_only / context rule / integrated caller; CI and p for integrated - context, paired by genome",
              "cv_cpt": {}, "heldout_validated": {}}
    print(f"\n== 5-fold CV on CPT, {'FAMILY-GROUPED' if grouped else 'by genome'} folds (model only / context rule / integrated)")
    report["folds"] = "family-grouped" if grouped else "by genome"
    for cls in CLASSES:
        R = {}
        if grouped: fold_of = family_folds(G, cls)
        for f in range(5):
            tr = [g for g in G if fold_of[g["name"]] != f]; te = [g for g in G if fold_of[g["name"]] == f]
            o, _, _ = evaluate(tr, te, cls)
            for m in o: R.setdefault(m, {}).update(o[m])
        report["cv_cpt"][cls] = summarise(R, cls)
    V = load("validated"); print(f"\n== held out: experimental set, {len(V)} genomes (trained on all CPT)")
    final = {}
    for cls in CLASSES:
        o, model, bw = evaluate(G, V, cls)
        report["heldout_validated"][cls] = summarise(o, cls); final[cls] = {"model": model, "context_beta_W": bw}
    out = ("reports/integrated_caller" + ("" if grouped else "_genomefolds") + ("_noshape" if "--no-shape" in sys.argv else "") + ".json")
    (B / out).write_text(json.dumps(report, indent=1)); print(f"wrote {out}")
    if "--final" in sys.argv:
        pickle.dump({"features": [FEATURES[i] for i in KEEP], "windows": WINDOWS, "models": {c: final[c]["model"] for c in CLASSES},
                     "note": "integrated second-stage caller, scripts/48; trained on leave-one-genome-out first-stage "
                             "scores of the 130 CPT-curated genomes (both protocols pooled). See reports/integrated_caller.json."},
                    open(B / ("models/integrated_caller" + ("_noshape" if "--no-shape" in sys.argv else "") + ".pkl"), "wb"))
        print("saved the integrated caller")


if __name__ == "__main__":
    main()
