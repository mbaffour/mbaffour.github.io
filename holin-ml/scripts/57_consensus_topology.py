"""Consensus membrane topology per genome, combining our predictor (scripts/55), DeepTMHMM and SignalP 6.0 (scripts/56),
as recommended by the comparison (reports/external/comparison.md):

  holin       class from our predictor (I/II/III = 3/2/1 helices) and from DeepTMHMM, and whether they agree
              (T7-like holins: the two disagree for half the genomes -- reported, not resolved)
  endolysin   SAR only where our SAR rule AND DeepTMHMM (signal-like N terminus, "SP"/"SP+TM") agree;
              disagreements kept as "ours only" / "DeepTMHMM only"
  spanin      each member typed with SignalP's lipoprotein call (LIPO, Sec/SPII) instead of our lipobox motif:
              o-spanin = LIPO and no helix after residue 35; u-spanin = LIPO and a helix in the C-terminal half;
              i-spanin = not LIPO and a helix starting in the first 40 residues; else other.
              Pair: two-component (i + o), unimolecular (u), i-spanin only, other.
Input: reports/external/per_protein.csv (+ our predictor for helix positions). Output:
reports/distribution/topology_consensus_by_genome.csv
Usage: python3 scripts/57_consensus_topology.py
"""
import csv, importlib, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
TM = importlib.import_module("55_tm_predictor")
T55 = importlib.import_module("55b_topology")
B = Path(__file__).resolve().parent.parent
CLS = {1: "III (1 helix)", 2: "II (2 helices)", 3: "I (3 helices)"}


def cls(n):
    n = int(n); return CLS.get(n, "no helix" if n == 0 else "4+ helices")


def member(seq, signalp):
    h = TM.predict([seq])[0]["helices"]
    if signalp == "LIPO":
        after = [x for x in h if x[0] > 35]
        if not after: return "o-spanin"
        return "u-spanin" if any(a > len(seq) * 0.5 for a, b in after) else "other"
    if h and h[0][0] <= 40: return "i-spanin"
    return "other"


def main():
    P = list(csv.DictReader(open(B / "reports/external/per_protein.csv")))
    G = defaultdict(dict)
    for p in P:
        for role in p["roles"].split(";"):
            parts = role.split(":")
            if len(parts) != 3: continue
            s, g, r = parts; G[(s, g)].setdefault(r, p)
    rows = []
    for (s, g), d in sorted(G.items()):
        f = {"set": s, "genome": g}
        if "holin" in d:
            p = d["holin"]; f["holin_class_ours"] = cls(p["ours_helices"]); f["holin_class_deeptmhmm"] = cls(p["deeptmhmm_helices"] or 0)
            f["holin_class_agree"] = f["holin_class_ours"] == f["holin_class_deeptmhmm"]
            f["holin_nterm_ours"], f["holin_nterm_deeptmhmm"] = p["ours_nterm"], p["deeptmhmm_nterm"]
        if "endolysin" in d:
            p = d["endolysin"]; ours = T55.endolysin_type(p["sequence"]) == "SAR"; deep = p["deeptmhmm_type"] in ("SP", "SP+TM")
            f["endolysin_SAR"] = ("SAR (both)" if ours and deep else "canonical (both)" if not ours and not deep else
                                  "SAR, ours only" if ours else "SAR, DeepTMHMM only")
            f["endolysin_signalp"] = p["signalp"]
        if "spanin" in d:
            mem = [member(d["spanin"]["sequence"], d["spanin"]["signalp"])]
            if "spanin_partner" in d: mem.append(member(d["spanin_partner"]["sequence"], d["spanin_partner"]["signalp"]))
            mem.sort(); f["spanin_members_signalp"] = "+".join(mem)
            f["spanin_type_signalp"] = ("two-component (i + o)" if {"i-spanin", "o-spanin"} <= set(mem) else
                                        "unimolecular (u)" if "u-spanin" in mem else
                                        "i-spanin only" if set(mem) == {"i-spanin"} else "other")
        rows.append(f)
    cols = ["set", "genome", "holin_class_ours", "holin_class_deeptmhmm", "holin_class_agree", "holin_nterm_ours",
            "holin_nterm_deeptmhmm", "endolysin_SAR", "endolysin_signalp", "spanin_type_signalp", "spanin_members_signalp"]
    out = B / "reports/distribution/topology_consensus_by_genome.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"wrote {out.relative_to(B)} ({len(rows)} genomes)")


if __name__ == "__main__":
    main()
