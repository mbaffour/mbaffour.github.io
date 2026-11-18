"""Group benchmark genomes by relatedness, so resampling for confidence intervals respects that related phages are not
independent observations (near-clonal groups such as the three lambda immunity variants in CPT would otherwise count
three times).

Two levels, both single-linkage:
  ani95    whole-genome average nucleotide identity >= 95% (the usual phage species threshold), estimated from
           bottom-2000 MinHash sketches of canonical DNA 21-mers (Mash distance; ANI ~ 1 - D)
  gene     shared gene content: Jaccard >= 0.10 between bottom-2000 MinHash sketches of all amino-acid 5-mers of the
           genome's proteins (Pyrodigal genes) -- related genomes far below 95% ANI still share many proteins. A looser,
           genus-like level used as a sensitivity check.
Output: reports/clusters/<set>.json  {genome key: {"ani95": id, "gene": id}} with the keys the benchmark reports use.
Usage: python3 scripts/58_genome_clusters.py cpt validated blind blind2 n4 lambda t7 p2 drexler t5 herelle t4 jumbo
"""
import glob, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
K, S, KA = 21, 2000, 5
M64 = np.uint64(0xFFFFFFFFFFFFFFFF)


def mix(x):
    """splitmix64 finaliser, vectorised"""
    x = x.astype(np.uint64)
    with np.errstate(over="ignore"):
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        x = x ^ (x >> np.uint64(31))
    return x


def dna_sketch(seq):
    lut = np.full(256, 255, np.uint8)
    for i, c in enumerate("ACGT"): lut[ord(c)] = i; lut[ord(c.lower())] = i
    a = lut[np.frombuffer(seq.encode(), np.uint8)]
    n = len(a) - K + 1
    if n <= 0: return np.zeros(0, np.uint64)
    bad = (a == 255).astype(np.int32); badw = np.convolve(bad, np.ones(K, np.int32), "valid") > 0
    a = np.where(a == 255, 0, a).astype(np.uint64)
    fw = np.zeros(n, np.uint64); rc = np.zeros(n, np.uint64)
    for j in range(K):
        fw = (fw << np.uint64(2)) | a[j:j + n]
        rc = rc | ((np.uint64(3) - a[j:j + n]) << np.uint64(2 * j))
    can = np.minimum(fw, rc)[~badw]
    return np.unique(mix(can))[:S]


def prot_sketch(prots):
    aa = "ACDEFGHIKLMNPQRSTVWY"; lut = np.full(256, 255, np.uint8)
    for i, c in enumerate(aa): lut[ord(c)] = i
    hs = []
    for p in prots:
        a = lut[np.frombuffer(p.encode(), np.uint8)]
        n = len(a) - KA + 1
        if n <= 0: continue
        bad = np.convolve((a == 255).astype(np.int32), np.ones(KA, np.int32), "valid") > 0
        a = np.where(a == 255, 0, a).astype(np.uint64); code = np.zeros(n, np.uint64)
        for j in range(KA): code = code * np.uint64(20) + a[j:j + n]
        hs.append(code[~bad])
    return np.unique(mix(np.concatenate(hs)))[:S] if hs else np.zeros(0, np.uint64)


def jaccard(a, b):
    if not len(a) or not len(b): return 0.0
    u = np.union1d(a, b)[:S]
    return len(np.intersect1d(np.intersect1d(a, u), np.intersect1d(b, u))) / len(u)


def ani(j):
    if j <= 0: return 0.0
    d = -np.log(2 * j / (1 + j)) / K
    return max(0.0, 1 - d)


def clusters(n, linked):
    parent = list(range(n))
    def f(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i, j in linked: parent[f(i)] = f(j)
    ids = {}
    return [ids.setdefault(f(i), len(ids)) for i in range(n)]


def genomes(s):
    """(key, dna) pairs with the keys the reports use"""
    from Bio import SeqIO
    if s in ("cpt", "validated"):
        d = {"cpt": "data/raw/cpt/genomes", "validated": "data/raw/validated/genomes"}[s]
        tf = json.load(open(B / f"data/raw/{s}/truth.json"))
        for p in sorted(glob.glob(str(B / d / "*.gb"))):
            if Path(p).stem in tf: yield Path(p).stem, str(next(SeqIO.parse(p, "genbank")).seq)
    else:
        for acc in json.load(open(B / f"data/raw/{s}/selection.json"))["accessions"]:
            yield acc, str(next(SeqIO.parse(B / f"data/raw/{s}/fna/{acc}.fna", "fasta")).seq)


def main():
    import genecall as G
    out = B / "reports/clusters"; out.mkdir(parents=True, exist_ok=True)
    for s in sys.argv[1:]:
        G_ = list(genomes(s)); keys = [k for k, _ in G_]
        dsk = [dna_sketch(x) for _, x in G_]
        psk = [prot_sketch([p["sequence"] for p in G.denovo([(k, x)])]) for k, x in G_]
        n = len(G_); la, lg = [], []
        for i in range(n):
            for j in range(i + 1, n):
                if ani(jaccard(dsk[i], dsk[j])) >= 0.95: la.append((i, j))
                if jaccard(psk[i], psk[j]) >= 0.10: lg.append((i, j))
        ca, cg = clusters(n, la), clusters(n, lg)
        res = {k: {"ani95": a, "gene": g} for k, a, g in zip(keys, ca, cg)}
        (out / f"{s}.json").write_text(json.dumps(res, indent=0))
        sz = lambda c: sorted(np.bincount(c), reverse=True)
        print(f"{s}: {n} genomes -> {len(set(ca))} ANI-95% clusters (largest {sz(ca)[:4]}), "
              f"{len(set(cg))} gene-content clusters (largest {sz(cg)[:4]})", flush=True)


if __name__ == "__main__":
    main()
