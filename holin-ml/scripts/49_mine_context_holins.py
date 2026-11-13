"""Mine candidate holins from NEW families by genomic context, without using the holin model.

Why. Eight changes to the holin model (bigger embeddings, biophysical/topology features, family reweighting) left
unseen-family performance where it was (reports/holin_generalisation.md). What the model lacks is training diversity:
the 3,250 training holins sit in 99 families. This script looks for holins from OTHER families, using the lysis genes
we already detect reliably as a guide.

The rule (sequence only; annotations are recorded for provenance and NEVER used to select):
  anchor     a protein carrying a catalytic endolysin Pfam domain (domains.tier >= 2), at most 500 aa (larger
             proteins with a lysozyme domain are tail spikes, e.g. T4 gp5, which sit next to unrelated genes)
  candidate  the gene IMMEDIATELY UPSTREAM of the anchor in its direction of transcription (the holin-endolysin
             order of most lysis cassettes), on the same strand, 50-250 aa, 1-3 hydrophobic TM segments, no
             catalytic endolysin domain itself, and no lipobox in its first 35 residues (that is an o-spanin)
  new family max identity < 0.30 (coverage >= 0.5) to every training holin, endolysin and spanin -- the same bar the
             novel-family protocol uses -- so only proteins from families absent from training are kept

Measured precision of the rule before mining (scratch analysis on the 78 CPT genomes with a curated holin): the
upstream neighbour of a catalytic-domain endolysin is the curated holin in 31 of 41 picks (76%), 31 of 38 (82%) once
the 500-aa anchor cap removes tail-spike anchors. So roughly one pick in five is not a holin; the decision on whether
the mined set helps is made by the novel-family benchmark, not assumed.

Evaluation genomes (CPT, the experimental set, the name-graded panel) are excluded by accession and by DNA hash, so
nothing mined comes from a genome that is later scored.

Output: data/processed/holins_context_mined.json, records shaped like holins_extra_clustered.json (id, sequence, label
"holin", cluster ids offset past every existing id) plus provenance and the identities that admitted them.

Usage: python3 scripts/49_mine_context_holins.py --genbanks "data/raw/pool/*.gb" "data/raw/mine/*.gb"
"""
import argparse, glob, hashlib, importlib, json, re, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import domains as D
S5 = importlib.import_module("05_scan_genome")
CL = importlib.import_module("03_cluster")
B = Path(__file__).resolve().parent.parent
LIPO = re.compile(r"[LVI][ASTVI][GAS]C")
EVAL = ["data/raw/cpt/genomes/*.gb", "data/raw/validated/genomes/*.gb", "data/raw/panel/*.gb", "data/raw/genomes/*.gb"]


def dna_key(path):
    from Bio import SeqIO
    r = next(SeqIO.parse(path, "genbank"))
    s = str(r.seq).upper()
    return r.id.split(".")[0], hashlib.sha1(min(s, str(r.seq.reverse_complement()).upper()).encode()).hexdigest()


def max_identity(queries, targets, procs=4):
    """for each query: max identity to any target under the benchmark's homology rule (coverage >= MIN_COV and
    Smith-Waterman score >= 80, as scripts/40 removes homologues). Without the score floor, chance local alignments
    between short membrane proteins pass 30% identity and every pick looks like a known family."""
    from multiprocessing import Pool
    with Pool(procs, initializer=_init, initargs=(targets,)) as pool:
        return np.array(pool.map(_best, queries, chunksize=4))
_T = None
def _init(t):
    global _T; _T = t
def _best(q):
    return max((i for i, c, s in CL.align_pairs(q, _T) if c >= CL.MIN_COV and s >= 80), default=0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genbanks", nargs="+", required=True)
    ap.add_argument("--out", default="data/processed/holins_context_mined.json")
    ap.add_argument("--max-anchor", type=int, default=500)
    ap.add_argument("--anchor-model-min", type=float, default=None,
                    help="also require the shipped ENDOLYSIN model to score the anchor >= this (two independent "
                         "endolysin signals: a catalytic domain and the model). Removes virion-associated hydrolases "
                         "(tail lysozymes, M23/SLT tape-measure domains) that carry a catalytic domain but are not "
                         "the lysis endolysin. The holin model is never used.")
    a = ap.parse_args()

    ev_acc, ev_dna = set(), set()
    for g in EVAL:
        for p in glob.glob(str(B / g)):
            try: acc, k = dna_key(p); ev_acc.add(acc); ev_dna.add(k)
            except Exception: pass
    print(f"evaluation genomes excluded: {len(ev_acc)} accessions", flush=True)

    paths = sorted({p for g in a.genbanks for p in glob.glob(str(B / g) if not Path(g).is_absolute() else g)})
    genomes, seen, n_ex = [], set(), 0
    for p in paths:
        try: acc, k = dna_key(p)
        except Exception: continue
        if acc in ev_acc or k in ev_dna: n_ex += 1; continue
        if k in seen: continue
        seen.add(k)
        try: ps = [x for x in S5.annotated_proteins(p) if x.get("sequence") and 20 <= len(x["sequence"]) <= 2000]
        except Exception: continue
        if ps: genomes.append((acc, sorted(ps, key=lambda x: x["start"])))
    print(f"{len(genomes)} mining genomes ({n_ex} skipped as evaluation genomes, duplicates dropped)", flush=True)

    t = time.time(); hmms, cls_of = D.lysis_hmms(None)
    allp = {f"{gi}|{i}": x["sequence"] for gi, (_, ps) in enumerate(genomes) for i, x in enumerate(ps)}
    hits = D.scan(allp, hmms, cls_of)
    print(f"domain scan of {len(allp)} proteins in {time.time()-t:.0f}s", flush=True)

    picks = []
    for gi, (acc, ps) in enumerate(genomes):
        tier = [D.tier(hits.get(f"{gi}|{i}"), "endolysin") for i in range(len(ps))]
        for a_ in range(len(ps)):
            if tier[a_] < 2 or len(ps[a_]["sequence"]) > a.max_anchor: continue
            st = ps[a_].get("strand"); j = a_ - 1 if st in ("+", 1, "1") else a_ + 1
            if not 0 <= j < len(ps) or ps[j].get("strand") != st or tier[j] >= 2: continue
            s = ps[j]["sequence"]; ntm = len(F.tm_segments(s))
            if not (50 <= len(s) <= 250 and 1 <= ntm <= 3) or LIPO.search(s[:35]): continue
            picks.append({"id": f"ctxmined_{acc}_{ps[j]['id']}", "sequence": s, "length": len(s), "label": "holin",
                          "n_tm": ntm, "genome": acc,
                          "anchor": {"id": ps[a_]["id"], "length": len(ps[a_]["sequence"]),
                                     "domains": D.summarise(hits.get(f"{gi}|{a_}"))},
                          "provenance_product_not_used": ps[j].get("product", ""),
                          "_anchor_seq": ps[a_]["sequence"]})
    if a.anchor_model_min is not None:
        import pickle
        bund = pickle.load(open(B / "models/endolysin_model.pkl", "rb"))
        esm = F.ESM(B / "models/esm_cache")
        aseqs = sorted({r["_anchor_seq"] for r in picks})
        t = time.time()
        X = np.hstack([np.array([F.handcrafted(s) for s in aseqs]), esm.embed(aseqs)])
        Pa = dict(zip(aseqs, bund["model"].predict_proba(X)[:, 1]))
        print(f"endolysin model on {len(aseqs)} anchors in {time.time()-t:.0f}s", flush=True)
        for r in picks: r["anchor"]["P_endolysin_model"] = round(float(Pa[r["_anchor_seq"]]), 4)
        n0 = len(picks); picks = [r for r in picks if r["anchor"]["P_endolysin_model"] >= a.anchor_model_min]
        print(f"anchor model filter >= {a.anchor_model_min}: {n0} -> {len(picks)} picks", flush=True)
    for r in picks: r.pop("_anchor_seq", None)
    # identical sequences picked in several genomes are one training example
    uniq = {}
    for r in picks: uniq.setdefault(r["sequence"], r)
    picks = list(uniq.values())
    print(f"{len(picks)} distinct context picks", flush=True)

    base = json.load(open(B / "data/processed/dataset.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))
    hol = [r["sequence"] for r in base if r["label"] == "holin"] + [r["sequence"] for r in cur if r["label"] == "holin"]
    endo = [r["sequence"] for r in json.load(open(B / "data/processed/endolysin_positives_v1_evidence.json"))]
    spa = [r["sequence"] for r in json.load(open(B / "data/processed/spanin_positives_signal.json"))]
    qs = [r["sequence"] for r in picks]
    t = time.time()
    idh, ide, ids = max_identity(qs, hol), max_identity(qs, endo), max_identity(qs, spa)
    print(f"identity to training sets in {time.time()-t:.0f}s", flush=True)
    for r, h, e, s in zip(picks, idh, ide, ids):
        r["max_id_training_holin"], r["max_id_endolysin"], r["max_id_spanin"] = round(float(h), 3), round(float(e), 3), round(float(s), 3)
    new = [r for r in picks if r["max_id_training_holin"] < CL.MIN_ID and r["max_id_endolysin"] < CL.MIN_ID
           and r["max_id_spanin"] < CL.MIN_ID]
    print(f"{len(new)} from families absent from training (known-family picks: "
          f"{sum(r['max_id_training_holin'] >= CL.MIN_ID for r in picks)})", flush=True)

    # cluster the new ones among themselves (same rule as scripts/03) and offset past every existing cluster id
    seqs = [r["sequence"] for r in new]
    edges = CL.all_edges(seqs) if len(seqs) > 1 else []
    cl = CL.greedy(len(seqs), edges, [len(s) for s in seqs], 0) if seqs else []
    off = 1 + max(int(r.get("cluster", -1) or -1) for r in base + cur)
    for r, c in zip(new, cl): r["cluster"] = off + c
    print(f"{len(set(cl))} new families", flush=True)
    out = {"rule": __doc__.split("Output:")[0].strip(), "n_genomes": len(genomes), "n_picks": len(picks),
           "known_family_picks": [{k: r[k] for k in ("id", "genome", "max_id_training_holin")} for r in picks
                                  if r["max_id_training_holin"] >= CL.MIN_ID],
           "records": new}
    Path(B / a.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
