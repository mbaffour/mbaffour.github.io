"""Compare the lysis-gene predictor with established annotation methods on the same curated benchmarks.

Baselines, each producing a per-genome ranking of proteins for each class:
  PHROGs   the profile database behind Pharokka (v4 HMMs, as distributed in the Pharokka v1.11.0 database bundle,
           Zenodo 21755221). As Pharokka does, a protein takes the annotation of its BEST hit among all 109,404
           PHROGs (E <= 1e-5); proteins whose best PHROG is a holin / endolysin / spanin PHROG are ranked by its bit
           score. The bundle's HMM file holds 38,880 PHROG profiles (305 in the lysis category); for speed the lysis
           profiles are searched first and only the proteins they hit are then searched against all 38,880.
  Pfam     the lysis Pfam families of scripts/domains.py: proteins with a catalytic or family-defining domain of the
           class (tier 2) ranked by domain E-value.
PHROGs v4 was built from essentially all RefSeq phage genomes, so most benchmark genes are effectively in its training
data: it is compared with our KNOWN-family estimate, not the unseen-family one.
Class from a PHROG's annotation uses the benchmark's own name rules (scripts/52c), with "holin/anti-holin" counted as
holin. Metrics per genome with a curated gene: the top-ranked protein is the curated gene (call); a curated gene is in
the top 5; and coverage (the method assigns the class to the curated gene at all). 95% CI by gene-content cluster
bootstrap (scripts/58).
Output: reports/baselines/{cpt,validated}.json and baselines.md
Usage: python3 scripts/60_baselines.py --phrogs DIR_WITH_all_phrogs.h3m
"""
import argparse, glob, importlib, json, re, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import domains as D
S5 = importlib.import_module("05_scan_genome")
SC = importlib.import_module("52c_score_blind")
B = Path(__file__).resolve().parent.parent
CLASSES = ("holin", "endolysin", "spanin")


def phrog_class(annot):
    a = annot.strip()
    if a.lower() == "holin/anti-holin": return "holin"
    lab = SC.labels(a)
    return next(iter(lab)) if len(lab) == 1 else None


def load_benchmark(name):
    gdir = {"cpt": "data/raw/cpt/genomes", "validated": "data/raw/validated/genomes"}[name]
    T = json.load(open(B / f"data/raw/{name}/truth.json")); G = []
    for p in sorted(glob.glob(str(B / gdir / "*.gb"))):
        g = Path(p).stem
        if g not in T: continue
        ps = [x for x in S5.annotated_proteins(p) if x.get("sequence") and 20 <= len(x["sequence"]) <= 2000]
        G.append({"genome": g, "seqs": [x["sequence"] for x in ps],
                  "truth": {c: [i for i, x in enumerate(ps) if x["id"] in set(T[g].get(c, []))] for c in CLASSES}})
    return G


def phrog_scores(G, pdir):
    import pyhmmer
    alpha = pyhmmer.easel.Alphabet.amino()
    annot = {}
    for ln in open(Path(pdir) / "phrog_annot_v4.tsv"):
        c = ln.rstrip("\n").split("\t")
        if c[0] != "phrog": annot[f"phrog_{c[0]}"] = (c[2], c[3])
    allp = [(gi, i, s) for gi, g in enumerate(G) for i, s in enumerate(g["seqs"])]
    seqs = [pyhmmer.easel.TextSequence(name=f"{k}".encode(), sequence=s).digitize(alpha) for k, (_, _, s) in enumerate(allp)]
    block = pyhmmer.easel.DigitalSequenceBlock(alpha, seqs)
    t = time.time()
    with pyhmmer.plan7.HMMFile(str(Path(pdir) / "all_phrogs.h3m")) as hf:
        hmms = list(hf)
    name = lambda h: h.name.decode() if isinstance(h.name, bytes) else h.name
    lysis = [h for h in hmms if annot.get(name(h), ("", ""))[1] == "lysis"]
    print(f"loaded {len(hmms)} PHROG HMMs ({len(lysis)} lysis) in {time.time()-t:.0f}s; {len(allp)} proteins", flush=True)
    cand = set()
    for hits in pyhmmer.hmmer.hmmsearch(lysis, block, E=1e-5, cpus=4):
        for h in hits:
            if h.evalue <= 1e-5: cand.add(int(name(h)))
    cand = sorted(cand)
    sub = pyhmmer.easel.DigitalSequenceBlock(alpha, [seqs[k] for k in cand])
    best = {}
    t = time.time()
    for hits in pyhmmer.hmmer.hmmsearch(hmms, sub, E=1e-5, cpus=4):
        q = name(hits.query)
        for h in hits:
            if h.evalue > 1e-5: continue
            k = int(name(h))
            if k not in best or h.score > best[k][1]: best[k] = (q, h.score)
    print(f"{len(cand)} candidate proteins searched against all PHROGs in {time.time()-t:.0f}s", flush=True)
    S = [{c: np.full(len(g["seqs"]), -np.inf) for c in CLASSES} for g in G]
    for k, (q, sc) in best.items():
        cls = phrog_class(annot.get(q, ("", ""))[0])
        if cls: gi, i, _ = allp[k]; S[gi][cls][i] = sc
    return S


def pfam_scores(G):
    hmms, cls_of = D.lysis_hmms(None)
    allp = {f"{gi}|{i}": s for gi, g in enumerate(G) for i, s in enumerate(g["seqs"])}
    hits = D.scan(allp, hmms, cls_of)
    S = [{c: np.full(len(g["seqs"]), -np.inf) for c in CLASSES} for g in G]
    for key, hs in hits.items():
        gi, i = map(int, key.split("|"))
        for c in CLASSES:
            if D.tier(hs, c) >= 2:
                ev = min(h["ievalue"] for h in hs if h["class"] == c)
                S[gi][c][i] = -np.log10(max(ev, 1e-300))
    return S


def metrics(G, S, cls, clusters, keep_rows=None):
    rows = {}
    for g, s in zip(G, S):
        tr = g["truth"][cls]
        if not tr: continue
        sc = s[cls]; assigned = np.isfinite(sc)
        order = [i for i in np.argsort(-sc) if assigned[i]]
        rank = {i: r for r, i in enumerate(order, 1)}
        rows[g["genome"]] = {"call": float(bool(order) and order[0] in tr),
                             "top5": float(any(rank.get(i, 10**9) <= 5 for i in tr)),
                             "coverage": float(any(assigned[i] for i in tr)), "has_call": float(bool(order))}
    if keep_rows is not None: keep_rows.update(rows)
    return summarise(rows, clusters)


ROWS = {}            # (benchmark, class, method) -> per-genome rows, saved for subset analyses


def summarise(rows, clusters, key=None):
    if key: ROWS[key] = rows
    out = {}
    G = sorted(rows)
    d = defaultdict(list)
    for k, g in enumerate(G): d[clusters.get(g, {}).get("gene", g)].append(k)
    U = list(d.values())
    for m in ("call", "top5", "coverage"):
        v = np.array([rows[g][m] for g in G]); rng = np.random.default_rng(0)
        bs = [v[[k for u in rng.integers(0, len(U), len(U)) for k in U[u]]].mean() for _ in range(2000)]
        out[m] = [round(float(v.mean()), 3), round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)]
    out["genomes"] = len(G)
    return out


def ours_rows(name, cls, proto):
    f = {("cpt", "holin"): "cpt_holin_remote.json", ("cpt", "endolysin"): "cpt_endolysin_remote.json",
         ("cpt", "spanin"): "cpt_spanin_remote.json", ("validated", "holin"): "validated_holin_spanin.json",
         ("validated", "endolysin"): "validated_endolysin_novirion.json", ("validated", "spanin"): "validated_spanin_audited.json"}[(name, cls)]
    r = json.load(open(B / "reports" / f))["classes"][cls]
    if proto not in r: return None
    keep = set(json.load(open(B / f"data/raw/{name}/truth.json"))); R = defaultdict(list)
    for t in r[proto]["truth_ranks"]:
        if t["genome"] in keep: R[t["genome"]].append(t["rank"])
    return {g: {"call": float(min(v) == 1), "top5": float(min(v) <= 5), "coverage": 1.0} for g, v in R.items()}


def ours(name, cls, proto, clusters):
    """our model's per-genome call / top 5 from the benchmark reports (shipped recipes)"""
    f = {("cpt", "holin"): "cpt_holin_remote.json", ("cpt", "endolysin"): "cpt_endolysin_remote.json",
         ("cpt", "spanin"): "cpt_spanin_remote.json", ("validated", "holin"): "validated_holin_spanin.json",
         ("validated", "endolysin"): "validated_endolysin_novirion.json", ("validated", "spanin"): "validated_spanin_audited.json"}[(name, cls)]
    r = json.load(open(B / "reports" / f))["classes"][cls]
    if proto not in r: return None
    keep = set(json.load(open(B / f"data/raw/{name}/truth.json"))); R = defaultdict(list)
    for t in r[proto]["truth_ranks"]:
        if t["genome"] in keep: R[t["genome"]].append(t["rank"])
    rows = {g: {"call": float(min(v) == 1), "top5": float(min(v) <= 5), "coverage": 1.0} for g, v in R.items()}
    return summarise(rows, clusters)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--phrogs", required=True); a = ap.parse_args()
    out_dir = B / "reports/baselines"; out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("cpt", "validated"):
        G = load_benchmark(name); clusters = json.load(open(B / f"reports/clusters/{name}.json"))
        P, F_ = phrog_scores(G, a.phrogs), pfam_scores(G)
        res = {}
        for cls in CLASSES:
            prow = {}
            res[cls] = {"PHROGs (Pharokka database)": metrics(G, P, cls, clusters, prow), "Pfam lysis domains": metrics(G, F_, cls, clusters)}
            ROWS[(name, cls, "PHROGs (Pharokka database)")] = prow
            for proto, lab in (("sequence_removal", "ours, known family"), ("family_removal", "ours, unseen family (30%)"),
                               ("remote_removal", "ours, remote homology removed")):
                o = ours(name, cls, proto, clusters)
                if o: res[cls][lab] = o
                orow = ours_rows(name, cls, proto)
                if orow: ROWS[(name, cls, lab)] = orow
                if orow and proto != "remote_removal":
                    # PHROGs where it assigns the class in this genome, our model where it assigns nothing
                    hyb = {g: (prow[g] if prow[g]["has_call"] else orow[g]) for g in prow if g in orow}
                    res[cls][f"PHROGs, else {lab}"] = summarise(hyb, clusters, (name, cls, f"PHROGs, else {lab}"))
            print(f"== {name} {cls}")
            for k, v in res[cls].items():
                print(f"   {k:32s} call {v['call'][0]:.2f} [{v['call'][1]:.2f},{v['call'][2]:.2f}]  top5 {v['top5'][0]:.2f} "
                      f"[{v['top5'][1]:.2f},{v['top5'][2]:.2f}]  coverage {v['coverage'][0]:.2f}  (n={v['genomes']})", flush=True)
        (out_dir / f"{name}.json").write_text(json.dumps(res, indent=1))
    (out_dir / "per_genome_rows.json").write_text(json.dumps({"|".join(k): v for k, v in ROWS.items()}))


if __name__ == "__main__":
    main()
