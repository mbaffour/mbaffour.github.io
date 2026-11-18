"""Audit the holin and spanin training positives for proteins that are probably not what their label says -- the check
that found 51 virion proteins among the endolysin positives (reports/endolysin_virion_fix.md).

Holin positives (all 5,055: dataset.json + holins_extra_clustered.json). Flags, each from evidence independent of the
model being trained:
  no_helix        our transmembrane predictor finds no membrane helix (a holin must cross the membrane)
  lipobox         a lipoprotein signal (lipobox) -- the signature of an o-spanin, not a holin
  description     the protein's own database description names something else (tail/virion part, endolysin or lysozyme,
                  spanin/Rz, terminase, integrase, transcription regulator ...)
  bacterial       not from a phage or prophage record (Pfam holin-like families also hold bacterial proteins such as
                  CidA/LrgA, which are not phage holins)
Spanin positives (spanin_positives_signal.json, 1,804): no_topology (no lipobox and no N-terminal helix -- neither an
o-spanin nor an i-spanin shape) and description (virion part, endolysin, holin).
Output: reports/label_audit/{holin,spanin}_audit.json (per record) and summary.json
Usage: python3 scripts/59_label_audit.py [--time-limit S]   (per-residue embeddings cached; resumable)
"""
import argparse, hashlib, importlib, json, re, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import genecall as G
TM = importlib.import_module("55_tm_predictor")
B = Path(__file__).resolve().parent.parent
OUT = B / "reports/label_audit"
NOT_HOLIN = re.compile(r"tail|baseplate|capsid|portal|head|virion|structural|tape.?measure|endolysin|lysozyme|lysin\b|"
                       r"amidase|peptidase|spanin|\bRz1?\b|terminase|integrase|recombinase|transcription|repressor|"
                       r"helicase|polymerase|primase|nuclease|kinase|methyltransferase|transport|permease|ABC", re.I)
NOT_SPANIN = re.compile(r"tail|baseplate|capsid|portal|head|virion|structural|tape.?measure|endolysin|lysozyme|"
                        r"\bholin\b|terminase|integrase|transcription", re.I)


def desc(r):
    return " | ".join(s.get("description", "") or "" for s in r.get("sources", []))


def is_phage(r):
    if "is_phage" in r: return bool(r["is_phage"])
    return any(re.search(r"phage|virus|prophage", (s.get("organism") or "") + " " + (s.get("description") or ""), re.I)
               for s in r.get("sources", []))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--time-limit", type=float, default=1e9)
    a = ap.parse_args(); t0 = time.time()
    base = json.load(open(B / "data/processed/dataset.json")); cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))
    H = [r for r in base + cur if r["label"] == "holin"]
    S = json.load(open(B / "data/processed/spanin_positives_signal.json"))
    seqs = sorted({r["sequence"] for r in H + S})
    todo = [s for s in seqs if not (TM.CACHE / f"{hashlib.sha256(s.encode()).hexdigest()}.npy").exists()]
    print(f"{len(seqs)} distinct sequences, {len(todo)} to embed", flush=True)
    for k, s in enumerate(todo):
        if time.time() - t0 > a.time_limit: print(f"embedded {k}; rerun to resume", flush=True); return
        TM.residue_embedding(s)
    OUT.mkdir(parents=True, exist_ok=True)
    pred = {s: TM.predict([s])[0] for s in seqs}
    hol = []
    for r in H:
        s = r["sequence"]; p = pred[s]; d = desc(r)
        fl = {"no_helix": p["n"] == 0, "lipobox": G.lipo_signal(s), "description": bool(NOT_HOLIN.search(d)),
              "bacterial": not is_phage(r)}
        hol.append({"id": r["id"], "length": len(s), "helices": p["n"], "pfam": r.get("pfam_families"),
                    "tier": r.get("tier"), "description": d[:160], "flags": [k for k, v in fl.items() if v]})
    spa = []
    for r in S:
        s = r["sequence"]; p = pred[s]; d = desc(r)
        shape = G.lipo_signal(s) or (p["helices"] and p["helices"][0][0] <= 40)
        fl = {"no_topology": not shape, "description": bool(NOT_SPANIN.search(d))}
        spa.append({"id": r["id"], "length": len(s), "helices": p["n"], "tier": r.get("tier"), "description": d[:160],
                    "flags": [k for k, v in fl.items() if v]})
    (OUT / "holin_audit.json").write_text(json.dumps(hol, indent=0)); (OUT / "spanin_audit.json").write_text(json.dumps(spa, indent=0))
    summ = {}
    for name, recs in (("holin", hol), ("spanin", spa)):
        c = Counter(f for r in recs for f in r["flags"])
        summ[name] = {"records": len(recs), "flagged_any": sum(bool(r["flags"]) for r in recs), "by_flag": dict(c),
                      "by_tier_flagged": dict(Counter(r["tier"] for r in recs if r["flags"]))}
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1)); print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
