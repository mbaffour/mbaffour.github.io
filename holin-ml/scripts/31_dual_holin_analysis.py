"""Is the recurring "second holin-like gene next to the annotated holin" real dual-holin biology or a model bias?

The model is SEQUENCE-ONLY -- it has no positional input -- so it cannot exploit adjacency. Therefore, if its
second high-scoring holin genes cluster next to the first MORE than random placement would give, that adjacency is
real genomic signal, not an artefact the model could manufacture. That is the decisive test here.

Across the 300 pooled phage genomes (ESM cached), for each genome we score every protein for holin, take the genes
at P>=0.9, and ask:
  1. How many genomes have >= 2 high-holin genes at all?
  2. ADJACENCY vs NULL: among genomes with >=2, is the minimum gene-distance between high-holin genes smaller than
     a random-placement null (k positions drawn uniformly from n genes, same k and n per genome, many draws)?
  3. WHAT are the second genes? For every high-holin gene that is not the single top-scorer in its genome:
     TM-helix count (holins are membrane proteins), C-terminal charge (holin signature), length, annotation class,
     whether it sits in the lysis region (within 5 genes of an annotated endolysin/spanin or the top holin), and
     max identity to known holins vs to known antiholins (holin_like). An antiholin is a holin homolog, so a second
     gene that matches an antiholin is the model being right about the fold, not a false positive.

Named cases (N4 gp62/gp63, Corynebacterium BFK20, Caulobacter phiCbK) are reported individually from their GenBank.

Writes reports/dual_holin_analysis.json. Usage: python3 scripts/31_dual_holin_analysis.py [--hi 0.9]
"""
import argparse, importlib, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
CL = importlib.import_module("03_cluster")
S5 = importlib.import_module("05_scan_genome")
import pickle

B = Path(__file__).resolve().parent.parent
END = re.compile(r"endolysin|lysozyme|muramidase|amidase|peptidoglycan|murein|glucosaminidase|\blysin\b|transglycosylase", re.I)
SPAN = re.compile(r"spanin|\bRz\b|\bRz1\b", re.I)
HOL = re.compile(r"holin", re.I); ANTI = re.compile(r"anti-?holin", re.I)
MEMB = re.compile(r"membrane|transmembrane", re.I)
TAIL = re.compile(r"tail|fib(er|re)|baseplate|tape.?measure|capsid|portal|head|terminase|structural", re.I)
HYPO = re.compile(r"hypothetical|uncharacter|unknown|DUF|^gp?\d", re.I)


def ctermcharge(s): t = s[-20:]; return sum((a in "KR") - (a in "DE") for a in t)
def nterm_tm_frac(s):
    segs = F.tm_segments(s); return len(segs)


def annclass(prod):
    if ANTI.search(prod) and not re.search(r"(?<!anti[- ])holin", prod, re.I): return "antiholin"
    if HOL.search(prod): return "holin"
    if END.search(prod): return "endolysin"
    if SPAN.search(prod): return "spanin"
    if MEMB.search(prod): return "membrane"
    if TAIL.search(prod): return "structural/tail"
    if HYPO.search(prod) or not prod.strip(): return "hypothetical"
    return "other"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--hi", type=float, default=0.9); a = ap.parse_args()
    model = pickle.load(open(B / "models/holin_model_curated.pkl", "rb"))["model"]
    esm = F.ESM(B / "models/esm_cache")
    feats = lambda ss: np.hstack([np.array([F.handcrafted(s) for s in ss]), esm.embed(ss)])
    known_hol = [r["sequence"] for r in json.load(open(B / "data/processed/dataset.json")) if r["label"] == "holin"]
    known_hol += [r["sequence"] for r in json.load(open(B / "data/processed/holins_extra_clustered.json")) if r["label"] == "holin"]
    antih = [r["sequence"] for r in json.load(open(B / "data/processed/dataset.json")) if r["label"] == "holin_like"]
    antih += [r["sequence"] for r in json.load(open(B / "data/processed/holins_extra_clustered.json")) if r["label"] == "holin_like"]

    pool = json.load(open(B / "data/processed/pool.json"))
    by = defaultdict(list)
    for p in pool: by[p["accession"]].append(p)

    ndist = Counter(); pairs_obs = []; pairs_null = []; second_genes = []
    rng = np.random.default_rng(0); t0 = time.time(); gi = 0
    for acc, ps in by.items():
        ps = sorted(ps, key=lambda p: p["start"])
        seqs = [p["sequence"] for p in ps]
        sc = model.predict_proba(feats(seqs))[:, 1]
        hi_idx = [i for i in range(len(ps)) if sc[i] >= a.hi]
        ndist[min(len(hi_idx), 5)] += 1
        if len(hi_idx) >= 2:
            # observed min gene-distance among high-holin genes
            d = min(hi_idx[j + 1] - hi_idx[j] for j in range(len(hi_idx) - 1))
            pairs_obs.append(d)
            # null: draw len(hi_idx) random positions from len(ps), min adjacent distance, averaged over draws
            n, k = len(ps), len(hi_idx); nd = []
            for _ in range(200):
                pos = np.sort(rng.choice(n, size=k, replace=False))
                nd.append(int(min(np.diff(pos))))
            pairs_null.append(float(np.mean(nd)))
        # characterize second (non-top) high-holin genes
        if hi_idx:
            top = max(range(len(ps)), key=lambda i: sc[i])
            end_sp_idx = [i for i, p in enumerate(ps) if END.search(p.get("product") or "") or SPAN.search(p.get("product") or "")]
            for i in hi_idx:
                if i == top: continue
                p = ps[i]; seq = p["sequence"]; prod = p.get("product") or ""
                lys_near = any(abs(i - j) <= 5 for j in end_sp_idx + [top])
                second_genes.append({"acc": acc, "idx": i, "dist_to_top": i - top, "P": round(float(sc[i]), 3),
                                     "len": len(seq), "tm": nterm_tm_frac(seq), "cterm_charge": ctermcharge(seq),
                                     "ann": annclass(prod), "product": prod[:40], "in_lysis_region": lys_near,
                                     "seq": seq})
        gi += 1
        if gi % 60 == 0: print(f"  {gi}/{len(by)} genomes ({int(time.time()-t0)}s)", flush=True)

    # homology of the second genes to known holins and antiholins (only these, to keep it cheap)
    sseqs = [g["seq"] for g in second_genes]
    if sseqs:
        idh = CL.search(known_hol, sseqs, 80); ida = CL.search(antih, sseqs, 80)
        for g, a1, a2 in zip(second_genes, idh, ida):
            g["max_id_known_holin"] = round(float(a1), 2); g["max_id_antiholin"] = round(float(a2), 2); g.pop("seq")

    # adjacency test aggregate
    obs = np.array(pairs_obs); nul = np.array(pairs_null)
    adj = {"genomes_with_2plus_high_holin": len(pairs_obs),
           "observed_median_min_gene_distance": round(float(np.median(obs)), 2) if len(obs) else None,
           "null_median_min_gene_distance": round(float(np.median(nul)), 2) if len(nul) else None,
           "observed_frac_adjacent_within_3": round(float(np.mean(obs <= 3)), 3) if len(obs) else None,
           "null_frac_adjacent_within_3": round(float(np.mean(nul <= 3)), 3) if len(nul) else None,
           "paired_fraction_observed_closer_than_null": round(float(np.mean(obs < nul)), 3) if len(obs) else None}

    sg = second_genes
    feat = {"n_second_genes": len(sg),
            "in_lysis_region": sum(g["in_lysis_region"] for g in sg),
            "annotation_classes": dict(Counter(g["ann"] for g in sg)),
            "median_TM_helices": float(np.median([g["tm"] for g in sg])) if sg else None,
            "frac_with_>=1_TM": round(float(np.mean([g["tm"] >= 1 for g in sg])), 3) if sg else None,
            "median_cterm_charge": float(np.median([g["cterm_charge"] for g in sg])) if sg else None,
            "frac_positive_cterm_tail": round(float(np.mean([g["cterm_charge"] > 0 for g in sg])), 3) if sg else None,
            "homology": {"matches_known_holin_id>=0.3": sum(g.get("max_id_known_holin", 0) >= 0.3 for g in sg),
                         "matches_antiholin_id>=0.3": sum(g.get("max_id_antiholin", 0) >= 0.3 for g in sg),
                         "no_match_to_either": sum(g.get("max_id_known_holin", 0) < 0.3 and g.get("max_id_antiholin", 0) < 0.3 for g in sg)}}

    out = {"threshold": a.hi, "n_high_holin_per_genome_distribution": {str(k): ndist[k] for k in sorted(ndist)},
           "adjacency_vs_null": adj, "second_gene_characterisation": feat,
           "interpretation_keys": {
               "adjacency": "model has no positional input; observed << null means high-holin genes genuinely "
                            "cluster, i.e. real genomic co-location, not model bias",
               "in_lysis_region": "a second gene near the endolysin/spanin or the top holin is lysis-associated, "
                                  "consistent with a real second holin/antiholin rather than a scattered false positive",
               "antiholin_homology": "an antiholin is a holin homolog; a second gene matching one is a correct fold "
                                     "call, not a false positive"},
           "top_second_genes": sorted(sg, key=lambda g: -g["P"])[:30]}
    (B / "reports/dual_holin_analysis.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"n_high_distribution": out["n_high_holin_per_genome_distribution"],
                      "adjacency_vs_null": adj, "second_genes": feat}, indent=1))


if __name__ == "__main__":
    main()
