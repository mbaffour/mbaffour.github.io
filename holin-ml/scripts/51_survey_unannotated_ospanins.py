"""Survey: o-spanins that RefSeq phage genomes carry but do not annotate.

Standard gene finders do not call a gene embedded in another gene's reading frame, and embedded o-spanins are exactly
that (reports/denovo_gene_calling.md: Pyrodigal misses 30% of CPT's curated spanins from bare DNA). RefSeq phage
annotations are mostly built with such gene finders. This scans every RefSeq complete tailed-phage genome
(scripts/49a) with RefSeq's OWN annotated genes as hosts, so every ORF found is, by construction, absent from the
RefSeq annotation (an ORF ending at an annotated CDS's stop is excluded by genecall).

Evidence attached to each candidate, all from sequence:
  P_spanin        the shipped spanin model's probability for the ORF (models/spanin_model.pkl)
  host_P_spanin   the same for the gene it sits in (an o-spanin's host is normally the i-spanin)
  cassette        a catalytic endolysin Pfam domain within 5 genes of the host (lysis-cassette context)
Tiers: A = P_spanin >= 0.5 and cassette; B = P_spanin >= 0.5 without cassette; C = the rest (lipoprotein ORF only).
Evaluation genomes (CPT, experimental set, panels) are skipped, as in scripts/49.

Output: reports/unannotated_ospanins.json (every candidate, with genome, coordinates, host, scores) and a summary.
Usage: python3 scripts/51_survey_unannotated_ospanins.py
"""
import glob, importlib, json, pickle, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import domains as D
import genecall
S5 = importlib.import_module("05_scan_genome")
M49 = importlib.import_module("49_mine_context_holins")
B = Path(__file__).resolve().parent.parent


def main():
    from Bio import SeqIO
    ev_acc, ev_dna = set(), set()
    for g in M49.EVAL:
        for p in glob.glob(str(B / g)):
            try: acc, k = M49.dna_key(p); ev_acc.add(acc); ev_dna.add(k)
            except Exception: pass
    paths = sorted(glob.glob(str(B / "data/raw/mine/*.gb")))
    t = time.time(); cands, seen, n_g, hosts_all = [], set(), 0, {}
    for p in paths:
        try:
            rec = next(SeqIO.parse(p, "genbank")); acc, k = M49.dna_key(p)
        except Exception: continue
        if acc in ev_acc or k in ev_dna or k in seen: continue
        seen.add(k); n_g += 1
        ann = sorted([x for x in S5.annotated_proteins(p) if x.get("sequence")], key=lambda x: x["start"])
        orfs = genecall.nested_lipoprotein_orfs(str(rec.seq), ann, rec.id)
        if not orfs: continue
        idx = {x["id"]: i for i, x in enumerate(ann)}
        for o in orfs:
            hi = idx[o["host"]]
            cands.append({"genome": rec.id, "organism": rec.annotations.get("organism", ""), "id": o["id"],
                          "start": o["start"], "stop": o["stop"], "strand": o["strand"], "length": len(o["sequence"]),
                          "sequence": o["sequence"], "host": o["host"], "host_product": ann[hi].get("product", ""),
                          "host_sequence": ann[hi]["sequence"],
                          "_nb": [ann[j]["sequence"] for j in range(max(0, hi - 5), min(len(ann), hi + 6)) if j != hi]})
    print(f"{n_g} genomes scanned in {time.time()-t:.0f}s; {len(cands)} unannotated nested lipoprotein ORFs "
          f"in {len({c['genome'] for c in cands})} genomes", flush=True)

    # lysis-cassette context: a catalytic endolysin domain among the host's neighbours
    t = time.time(); hmms, cls_of = D.lysis_hmms(None)
    nb = {f"{i}|{j}": s for i, c in enumerate(cands) for j, s in enumerate(c["_nb"])}
    hits = D.scan(nb, hmms, cls_of)
    for i, c in enumerate(cands):
        c["cassette"] = any(D.tier(hits.get(f"{i}|{j}"), "endolysin") >= 2 for j in range(len(c["_nb"])))
        del c["_nb"]
    print(f"cassette context in {time.time()-t:.0f}s", flush=True)

    bund = pickle.load(open(B / "models/spanin_model.pkl", "rb"))
    esm = F.ESM(B / "models/esm_cache")
    seqs = sorted({c["sequence"] for c in cands} | {c["host_sequence"] for c in cands})
    t = time.time()
    X = np.hstack([np.array([F.handcrafted(s) for s in seqs]), esm.embed(seqs)])
    P = dict(zip(seqs, bund["model"].predict_proba(X)[:, 1]))
    print(f"spanin model on {len(seqs)} sequences in {time.time()-t:.0f}s", flush=True)
    for c in cands:
        c["P_spanin"] = round(float(P[c["sequence"]]), 4); c["host_P_spanin"] = round(float(P[c.pop("host_sequence")]), 4)
        c["tier"] = "A" if c["P_spanin"] >= 0.5 and c["cassette"] else "B" if c["P_spanin"] >= 0.5 else "C"
    cands.sort(key=lambda c: (c["tier"], -c["P_spanin"]))
    summ = {"genomes_scanned": n_g, "orfs": len(cands), "genomes_with_orf": len({c["genome"] for c in cands}),
            "tier_counts": {t_: sum(c["tier"] == t_ for c in cands) for t_ in "ABC"},
            "genomes_with_tier_A": len({c["genome"] for c in cands if c["tier"] == "A"})}
    print(json.dumps(summ), flush=True)
    (B / "reports/unannotated_ospanins.json").write_text(json.dumps({"summary": summ, "candidates": cands}, indent=1))
    print("wrote reports/unannotated_ospanins.json")


if __name__ == "__main__":
    main()
