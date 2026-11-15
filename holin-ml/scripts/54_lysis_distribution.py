"""How lysis genes are built and arranged across phage families -- from the blind DNA-only calls, no annotation names.

For every genome of each group scanned by scripts/52b, using the frozen calls (reports/<set>/pred/) and the protein
sequences re-derived exactly as the predictor called them (scripts/genecall.py):
  holin      length, Pfam holin family if any, membrane segments (Kyte-Doolittle heuristic -- recorded but NOT used
             for classification: it reads lambda S, a 3-TM holin, as 1),
             copy number = proteins in the genome with P(holin) >= 0.9
  endolysin  catalytic class from its Pfam domains (glycosidase, lytic transglycosylase, amidase, peptidase, other
             endolysin family; >1 class = multi-catalytic), any cell-wall-binding domain, SAR-type N terminus (a
             hydrophobic segment starting in the first 30 residues, by the same heuristic: a lower bound, since SAR domains
             are weakly hydrophobic by nature), length
  spanin     (confident calls only) the call plus its partner (another protein with P(spanin) >= 0.5 overlapping it or within 2 genes):
             embedded (one inside the other) / overlapping / separate / single (no partner); lipobox on either
  cassette   all three confident and within 6 genes (co-located), all three confident but spread (dispersed), or
             incomplete; gene order in the direction of transcription
Every value is a model call or a sequence property, so this is a map of what the predictor sees, with its error rates
(reports/groups/groups_scan.md) -- not curated biology.

Output: reports/distribution/lysis_by_genome.csv, summary.json, figures/*.png
Usage: python3 scripts/54_lysis_distribution.py [--sets n4 lambda ...] [--time-limit S]
"""
import argparse, csv, importlib, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import domains as D
import genecall as G
B = Path(__file__).resolve().parent.parent
SETS = ["n4", "lambda", "t7", "p2", "drexler", "t5", "herelle", "t4", "jumbo"]
CLASSES = ("holin", "endolysin", "spanin")
CAT = {"glycosidase": {"PF00959", "PF01183", "PF05838", "PF11860", "PF13702", "PF01832"},
       "transglycosylase": {"PF01464", "PF13406", "PF06737"},
       "amidase": {"PF01510", "PF01520", "PF05382"},
       "peptidase": {"PF00877", "PF01551", "PF02557", "PF05257", "PF08291", "PF13539"},
       "other endolysin family": {"PF31067", "PF31186", "PF25309", "PF07486"}}


def genome_features(s, acc, hmms, cls_of):
    from Bio import SeqIO
    L = (B / f"reports/{s}/pred/{acc}.tsv").read_text().splitlines(); h = L[0].split("\t")
    R = [dict(zip(h, l.split("\t"))) for l in L[1:] if l.strip()]
    rec = next(SeqIO.parse(B / f"data/raw/{s}/fna/{acc}.fna", "fasta"))
    prot = {p["id"]: p["sequence"] for p in G.denovo([(rec.id, str(rec.seq))], nested=True)}
    calls = {}
    for i, r in enumerate(R):
        for x in r["lysis_call"].split(","):
            if x: c, t = x.split(":"); calls[c] = (i, t)
    f = {"set": s, "genome": acc, "genome_kb": round(len(rec.seq) / 1000, 1), "n_genes": len(R),
         "holin_copies_P90": sum(float(r["P_holin"]) >= 0.9 for r in R)}
    seqs = {c: prot.get(R[calls[c][0]]["id"], "") for c in calls}
    hits = D.scan({c: s_ for c, s_ in seqs.items() if s_}, hmms, cls_of) if seqs else {}
    for c in CLASSES:
        f[f"{c}_tier"] = calls[c][1] if c in calls else "none"
    if "holin" in calls:
        sq = seqs["holin"]; f["holin_tm"] = len(F.tm_segments(sq)); f["holin_len"] = len(sq)
        fam = sorted({x["name"] for x in hits.get("holin", []) if x["class"] == "holin" and x["ievalue"] <= 1e-5})
        f["holin_pfam"] = ";".join(fam) or "none"
    if "endolysin" in calls:
        sq = seqs["endolysin"]; f["endolysin_len"] = len(sq)
        tms = F.tm_segments(sq); f["endolysin_SAR"] = bool(tms and tms[0][0] < 30)
        H = [x for x in hits.get("endolysin", []) if x["ievalue"] <= 1e-5]
        cats = sorted({k for x in H for k, v in CAT.items() if x["pfam"] in v})
        f["endolysin_class"] = cats[0] if len(cats) == 1 else ("multi-catalytic" if cats else "no domain detected")
        f["endolysin_domains"] = ";".join(sorted({x["name"] for x in H})) or "none"
        f["endolysin_binding"] = any(x["grade"] == "binding" for x in H)
    if calls.get("spanin", (0, ""))[1] != "confident":
        f["spanin_arch"] = "no confident spanin"
    else:
        i = calls["spanin"][0]; r = R[i]; s0, e0 = int(r["start"]), int(r["stop"])
        cand = []
        for j, q in enumerate(R):
            if j == i or float(q["P_spanin"]) < 0.5: continue
            a0, a1 = int(q["start"]), int(q["stop"]); ov = min(e0, a1) - max(s0, a0)
            if ov > 0 or abs(j - i) <= 2: cand.append((ov > 0, -float(q["P_spanin"]), j, a0, a1))
        if cand:
            ov, _, j, a0, a1 = sorted(cand)[-1] if any(c_[0] for c_ in cand) else sorted(cand, key=lambda c_: c_[1])[0]
            if ov:
                inside = (s0 <= a0 and a1 <= e0) or (a0 <= s0 and e0 <= a1)
                f["spanin_arch"] = "embedded" if inside else "overlapping"
            else:
                f["spanin_arch"] = "separate"
            f["spanin_lipobox"] = G.lipo_signal(seqs["spanin"]) or G.lipo_signal(prot.get(R[j]["id"], ""))
            f["spanin_nested_orf"] = "nested" in R[i]["id"] or "nested" in R[j]["id"]
        else:
            f["spanin_arch"] = "single"; f["spanin_lipobox"] = G.lipo_signal(seqs["spanin"])
            f["spanin_nested_orf"] = "nested" in R[i]["id"]
    if all(f[f"{c}_tier"] == "confident" for c in CLASSES):
        idx = {c: calls[c][0] for c in CLASSES}; span = max(idx.values()) - min(idx.values())
        f["cassette"] = "co-located" if span <= 6 else "dispersed"; f["cassette_span"] = span
        st = R[idx["endolysin"]]["strand"]
        f["order"] = "-".join(c[0].upper() for c in sorted(idx, key=lambda c: idx[c] if st == "+" else -idx[c])) if span <= 6 else ""
    else:
        f["cassette"] = "incomplete"
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", nargs="+", default=SETS); ap.add_argument("--time-limit", type=float, default=1e9)
    a = ap.parse_args(); t0 = time.time()
    out = B / "reports/distribution"; (out / "cache").mkdir(parents=True, exist_ok=True)
    hmms, cls_of = D.lysis_hmms(None)
    done_all = True
    for s in a.sets:
        cf = out / "cache" / f"{s}.json"
        cache = json.loads(cf.read_text()) if cf.exists() else {}
        sel = json.load(open(B / f"data/raw/{s}/selection.json"))["accessions"]
        for acc in sel:
            if acc in cache: continue
            if time.time() - t0 > a.time_limit: done_all = False; break
            cache[acc] = genome_features(s, acc, hmms, cls_of)
            if len(cache) % 20 == 0: cf.write_text(json.dumps(cache))
        cf.write_text(json.dumps(cache))
        print(f"{s}: {len(cache)}/{len(sel)} genomes", flush=True)
        if len(cache) < len(sel): done_all = False
    if not done_all: print("incomplete; rerun to resume"); return
    rows = [r for s in a.sets for r in json.loads((out / "cache" / f"{s}.json").read_text()).values()]
    cols = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("set", "genome"), k))
    with open(out / "lysis_by_genome.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} genomes to reports/distribution/lysis_by_genome.csv")


if __name__ == "__main__":
    main()
