"""Homology clusters for leakage-free evaluation (MMseqs2-style: k-mer prefilter + Smith-Waterman verification).

Exhaustive all-vs-all Smith-Waterman (a k-mer prefilter was tried and rejected: only ~10% recall of true holin-holin edges).
Verification: pyopal Smith-Waterman (BLOSUM62, gap open 11 / extend 1), identity = identical aligned positions / alignment length,
coverage = aligned residues / length of the shorter sequence. Edge if identity >= MIN_ID and coverage >= MIN_COV.
Clusters = connected components (single linkage), which is conservative for leakage control.
Also exposes search(): best hits of query sequences against a set, used to exclude test-genome homologs from training.
"""
import json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import pyopal

B = Path(__file__).resolve().parent.parent
MIN_ID, MIN_COV, K, MIN_SHARED, MAX_CAND = 0.30, 0.50, 3, 3, 400
# reduced alphabet (Murphy et al. 2000, 10 groups) for the prefilter only
RED = {a: g for g, s in enumerate(["LVIM", "C", "A", "G", "ST", "P", "FYW", "EDNQ", "KR", "H"]) for a in s}
ALPHA = pyopal.Alphabet()


def kmers(seq):
    r = [RED.get(a, 10) for a in seq]
    return {tuple(r[i:i + K]) for i in range(len(r) - K + 1)}


def candidates(qseqs, dseqs, same=False):
    index = defaultdict(list)
    dk = [kmers(s) for s in dseqs]
    df = defaultdict(int)
    for ks in dk:
        for k in ks: df[k] += 1
    common = {k for k, c in df.items() if c > max(50, 0.02 * len(dseqs))}  # ignore very frequent k-mers (low information)
    for j, ks in enumerate(dk):
        for k in ks - common: index[k].append(j)
    out = []
    for i, s in enumerate(qseqs):
        cnt = defaultdict(int)
        for k in kmers(s) - common:
            for j in index[k]: cnt[j] += 1
        c = [j for j, n in cnt.items() if n >= MIN_SHARED and (not same or j > i)]
        c.sort(key=lambda j: -cnt[j]); out.append(c[:MAX_CAND])
    return out


def align_pairs(q, targets):
    """identity and shorter-sequence coverage of q against each target (local alignment)."""
    if not targets: return []
    db = pyopal.Database(targets)
    out = [(0.0, 0.0, 0)] * len(targets)
    # NB: pyopal yields results in arbitrary order; each carries target_index (verified on a toy example)
    for r in pyopal.align(q, db, mode="full", algorithm="sw", gap_open=11, gap_extend=1):
        t = targets[r.target_index]
        aln = r.alignment  # 'M' identical, 'X' mismatch, 'I'/'D' gap columns
        ident = aln.count("M") / len(aln) if aln else 0.0
        cov = (r.query_end - r.query_start + 1 if len(q) <= len(t) else r.target_end - r.target_start + 1) / min(len(q), len(t))
        out[r.target_index] = (ident, cov, r.score)
    return out


_SEQS = None
def _init(seqs):
    global _SEQS; _SEQS = seqs
def _row(i):
    """all pairs (i, j>i) passing identity/coverage, with SW score"""
    if i + 1 >= len(_SEQS): return []
    return [(i, i + 1 + j, ident, cov, sc) for j, (ident, cov, sc) in enumerate(align_pairs(_SEQS[i], _SEQS[i + 1:]))
            if ident >= MIN_ID and cov >= MIN_COV]


def all_edges(seqs, procs=4):
    from multiprocessing import Pool
    with Pool(procs, initializer=_init, initargs=(seqs,)) as pool:
        edges = []
        for k, e in enumerate(pool.imap(_row, range(len(seqs)), chunksize=32)):
            edges += e
            if k % 2000 == 0: print(f"  {k}/{len(seqs)} rows, {len(edges)} candidate edges", flush=True)
    return edges


def components(n, edges):
    parent = list(range(n))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i, j, *_ in edges: parent[find(j)] = find(i)
    roots = {}
    return [roots.setdefault(find(i), len(roots)) for i in range(n)]


def search(queries, targets, min_score):
    """For each target: max identity (coverage >= MIN_COV, SW score >= min_score) to any query (exhaustive)."""
    best = np.zeros(len(targets))
    for t, s in enumerate(targets):
        for ident, cov, sc in align_pairs(s, queries):
            if cov >= MIN_COV and sc >= min_score: best[t] = max(best[t], ident)
    return best


def greedy(n, edges, lengths, min_score):
    """CD-HIT / MMseqs-style greedy set-cover clustering: longest sequence first becomes a centroid and absorbs every
    still-unassigned neighbour. Unlike single linkage this does not chain distant sequences into one giant component."""
    nb = [[] for _ in range(n)]
    for i, j, ident, cov, sc in edges:
        if sc >= min_score: nb[i].append(j); nb[j].append(i)
    cl = [-1] * n; c = 0
    for i in sorted(range(n), key=lambda x: -lengths[x]):
        if cl[i] != -1: continue
        cl[i] = c
        for j in nb[i]:
            if cl[j] == -1: cl[j] = c
        c += 1
    return cl


if __name__ == "__main__":
    import collections, pickle
    data = json.loads((B / "data/processed/dataset.json").read_text())
    seqs = [r["sequence"] for r in data]; lens = [len(s) for s in seqs]; lab = [r["label"] for r in data]
    ep = B / "data/processed/edges.pkl"
    if ep.exists(): edges = pickle.loads(ep.read_bytes())
    else: edges = all_edges(seqs); ep.write_bytes(pickle.dumps(edges))
    scan = {}
    for ms in [0, 50, 60, 70]:
        cl = greedy(len(seqs), edges, lens, ms); cnt = collections.Counter(cl)
        hc = collections.Counter(c for c, l in zip(cl, lab) if l == "holin")
        scan[ms] = {"clusters": len(cnt), "largest": max(cnt.values()), "holin_clusters": len(hc), "largest_holin_cluster": max(hc.values()),
                    "holin_singletons": sum(1 for v in hc.values() if v == 1)}
        print(ms, scan[ms], flush=True)
    MIN_SCORE = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    cl = greedy(len(seqs), edges, lens, MIN_SCORE)
    for r, c in zip(data, cl): r["cluster"] = c
    (B / "data/processed/dataset.json").write_text(json.dumps(data))
    summ = {"params": {"min_identity": MIN_ID, "min_coverage_shorter": MIN_COV, "min_sw_score": MIN_SCORE,
                       "scoring": "Smith-Waterman, BLOSUM62, gap open 11 / extend 1 (pyopal); exhaustive all-vs-all",
                       "clustering": "greedy set-cover, longest-first (CD-HIT/MMseqs-style)"},
            "candidate_edges": len(edges), "score_threshold_scan": scan, "chosen": scan[MIN_SCORE]}
    (B / "data/processed/cluster_summary.json").write_text(json.dumps(summ, indent=2)); print(json.dumps(summ["chosen"]))
