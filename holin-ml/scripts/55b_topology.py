"""Membrane topology of the called lysis genes across phage families, with the ESM transmembrane predictor (scripts/55).

For every genome in the blind group scans (frozen DNA-only calls; sequences re-derived as the predictor called them):
  holin       class by predicted helices: I = 3, II = 2, III = 1 (0 / 4+ reported as such); N terminus in/out by the
              positive-inside rule. In genomes with >= 2 strong holin-like genes (P >= 0.9), the second one too.
  spanin      each member of the called pair (call + partner: P(spanin) >= 0.5, overlapping or within 2 genes):
              o-spanin = lipobox signal and no helix after it; u-spanin = lipobox signal and a C-terminal helix;
              i-spanin = an N-terminal helix (starting in the first 40 residues) and no lipobox. Pair type:
              two-component (i + o), unimolecular (one u-spanin), or other.
  endolysin   SAR if the predictor's smoothed helix probability over the first 50 residues reaches 0.06, or the
              hydropathy heuristic finds an N-terminal segment (start < 30); else canonical. On the 44 Swiss-Prot
              phage endolysins this separates all 13 SAR endolysins from all 31 canonical ones -- the rule was set on
              those same proteins (the only labelled SAR data), so it is calibrated, not independently tested.
Output: reports/distribution/topology_by_genome.csv
Usage: python3 scripts/55b_topology.py [--time-limit S]   (resumable; per-residue embeddings cached)
"""
import argparse, csv, importlib, json, pickle, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import genecall as G
TM = importlib.import_module("55_tm_predictor")
B = Path(__file__).resolve().parent.parent
SETS = ["n4", "lambda", "t7", "p2", "drexler", "t5", "herelle", "t4", "jumbo"]
_M = None


def prof(seq):
    global _M
    if _M is None: _M = pickle.load(open(TM.MODEL, "rb"))
    p = _M["clf"].predict_proba(_M["scaler"].transform(TM.residue_features(seq)))[:, 1]
    h = TM.decode(p)
    return h, np.convolve(p, np.ones(5) / 5, mode="same")


def holin_class(n):
    return {1: "III (1 helix)", 2: "II (2 helices)", 3: "I (3 helices)"}.get(n, "no helix" if n == 0 else "4+ helices")


def spanin_member(seq):
    if not seq: return "?"
    h, _ = prof(seq); lip = G.lipo_signal(seq)
    if lip:
        after = [x for x in h if x[0] > 35]                       # helices beyond the signal peptide
        return "u-spanin" if any(a > len(seq) * 0.5 for a, b in after) else ("o-spanin" if not after else "other")
    if h and h[0][0] <= 40: return "i-spanin"
    return "other"


def endolysin_type(seq):
    _, sm = prof(seq)
    tms = F.tm_segments(seq)
    return "SAR" if (sm[:50].max() >= 0.06 or (tms and tms[0][0] < 30)) else "canonical"


def genome(s, acc):
    from Bio import SeqIO
    L = (B / f"reports/{s}/pred/{acc}.tsv").read_text().splitlines(); hd = L[0].split("\t")
    R = [dict(zip(hd, l.split("\t"))) for l in L[1:] if l.strip()]
    rec = next(SeqIO.parse(B / f"data/raw/{s}/fna/{acc}.fna", "fasta"))
    prot = {p["id"]: p["sequence"] for p in G.denovo([(rec.id, str(rec.seq))], nested=True)}
    calls = {}
    for i, r in enumerate(R):
        for x in r["lysis_call"].split(","):
            if x: c, t = x.split(":"); calls[c] = (i, t)
    f = {"set": s, "genome": acc}
    if calls.get("holin", (0, ""))[1] == "confident":
        i = calls["holin"][0]; sq = prot.get(R[i]["id"], "")
        h, _ = prof(sq); f["holin_class"] = holin_class(len(h)); f["holin_nterm"] = TM.n_terminus_side(sq, h) or ""
        strong = sorted([j for j, r in enumerate(R) if float(r["P_holin"]) >= 0.9 and j != i], key=lambda j: -float(R[j]["P_holin"]))
        if strong:
            h2, _ = prof(prot.get(R[strong[0]]["id"], "")); f["holin2_class"] = holin_class(len(h2))
            f["holin2_adjacent"] = abs(strong[0] - i) <= 1
    if calls.get("endolysin", (0, ""))[1] == "confident":
        f["endolysin_type"] = endolysin_type(prot.get(R[calls["endolysin"][0]]["id"], ""))
    if calls.get("spanin", (0, ""))[1] == "confident":
        i = calls["spanin"][0]; r = R[i]; s0, e0 = int(r["start"]), int(r["stop"]); cand = []
        for j, q in enumerate(R):
            if j == i or float(q["P_spanin"]) < 0.5: continue
            ov = min(e0, int(q["stop"])) - max(s0, int(q["start"]))
            if ov > 0 or abs(j - i) <= 2: cand.append((ov > 0, float(q["P_spanin"]), j))
        m1 = spanin_member(prot.get(r["id"], ""))
        m2 = spanin_member(prot.get(R[max(cand)[2]]["id"], "")) if cand else None
        mem = sorted(x for x in (m1, m2) if x)
        f["spanin_members"] = "+".join(mem)
        f["spanin_type"] = ("two-component (i + o)" if {"i-spanin", "o-spanin"} <= set(mem) else
                            "unimolecular (u)" if "u-spanin" in mem else "i-spanin only" if mem == ["i-spanin"] or mem == ["i-spanin", "i-spanin"] else "other")
    return f


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--time-limit", type=float, default=1e9)
    a = ap.parse_args(); t0 = time.time()
    out = B / "reports/distribution"; cdir = out / "cache_topology"; cdir.mkdir(parents=True, exist_ok=True)
    complete = True
    for s in SETS:
        cf = cdir / f"{s}.json"; cache = json.loads(cf.read_text()) if cf.exists() else {}
        sel = json.load(open(B / f"data/raw/{s}/selection.json"))["accessions"]
        for acc in sel:
            if acc in cache: continue
            if time.time() - t0 > a.time_limit: complete = False; break
            cache[acc] = genome(s, acc)
            if len(cache) % 10 == 0: cf.write_text(json.dumps(cache))
        cf.write_text(json.dumps(cache)); print(f"{s}: {len(cache)}/{len(sel)}", flush=True)
        if len(cache) < len(sel): complete = False
    if not complete: print("incomplete; rerun to resume"); return
    rows = [r for s in SETS for r in json.loads((cdir / f"{s}.json").read_text()).values()]
    cols = ["set", "genome", "holin_class", "holin_nterm", "holin2_class", "holin2_adjacent", "endolysin_type",
            "spanin_type", "spanin_members"]
    with open(out / "topology_by_genome.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"wrote reports/distribution/topology_by_genome.csv ({len(rows)} genomes)")


if __name__ == "__main__":
    main()
