"""Verify predict_lysis calls with evidence the model never used: Pfam domains, membrane topology, genomic context.

The classifier sees sequence only. Three independent checks tell you whether a call is believable:
  1. Pfam domains (pyhmmer, local) against a targeted set of lysis-relevant families: endolysin catalytic and
     cell-wall-binding domains, the 38 Pfam holin families, and the spanin families. A hit supports the class; for
     endolysins it also names the enzymatic activity (lysozyme, amidase, peptidase, transglycosylase).
  2. Membrane topology from Phobius (the same service the topology atlas uses): transmembrane-helix count and signal
     peptide. Holins and spanins should be membrane proteins; a classical endolysin is soluble, while a SAR endolysin
     carries an N-terminal signal-anchor; an o-spanin is typically a lipoprotein (signal peptide).
  3. Genomic context: a call sitting among virion structural / head / tail / portal / terminase genes is flagged.
     This matters most for endolysins -- a large peptidoglycan hydrolase in the tail module is usually a
     VIRION-ASSOCIATED lysin used for ENTRY, which shares catalytic domains with endolysins and which a
     sequence-only model cannot tell apart from the exit lysin.
Plus whether the exact sequence was in training (so a call is not just recall of training data).

Usage: python3 scripts/33_verify_calls.py --tsv reports/X_lysis.tsv --genbank genome.gb [--top 3] [--threshold 0.5]
Writes <tsv stem>_verified.json and .md next to the TSV.
"""
import argparse, csv, gzip, importlib, json, re, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
S5 = importlib.import_module("05_scan_genome")

B = Path(__file__).resolve().parent.parent
PHOBIUS = "https://phobius.sbc.su.se/api/predict"
# Domain machinery now lives in scripts/domains.py, shared with the predictor (scripts/32) so the deployable
# entrypoint does not import this verification script. Names re-exported for callers and for backwards
# compatibility.
import domains as D
HMMDIR = D.HMMDIR
ENDOLYSIN_PFAM, SPANIN_PFAM = D.ENDOLYSIN_PFAM, D.SPANIN_PFAM
STRUCT, NOT_HOLIN = D.STRUCT, D.NOT_HOLIN
holin_pfam, fetch_hmms, scan = D.holin_pfam, D.fetch_hmms, D.scan


def phobius(seqs):
    fa = "".join(f">{k}\n{v}\n" for k, v in seqs.items())
    try:
        req = urllib.request.Request(PHOBIUS, data=json.dumps({"sequence": fa, "plot": False}).encode(),
                                     headers={"Content-Type": "application/json"})
        preds = json.loads(urllib.request.urlopen(req, timeout=600).read())["predictions"]
        return {p["id"]: p for p in preds}
    except Exception as e:
        print(f"Phobius unavailable: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr); return {}


def topo_summary(p):
    """Phobius returns per-protein fields; summarise TM count and signal peptide from whatever it gives."""
    if not p: return {"tm": None, "sp": None, "raw": None}
    txt = json.dumps(p)
    tm = p.get("tm") if isinstance(p.get("tm"), int) else None
    sp = p.get("sp") if p.get("sp") in (True, False, "Y", "0", "N") else None
    m = re.search(r'"(?:prediction|topology|cls|summary)"\s*:\s*"([^"]+)"', txt)
    raw = m.group(1) if m else None
    if tm is None and raw:
        tm = len(re.findall(r"\d+-\d+", raw.split("o")[-1])) if False else None
    return {"tm": tm, "sp": sp, "raw": raw, "fields": {k: p[k] for k in p if k not in ("sequence", "svg")}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True); ap.add_argument("--genbank", required=True)
    ap.add_argument("--top", type=int, default=3); ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--min-cov", type=float, default=0.8,
                    help="coverage floor for the nearest-training-neighbour identity. A local alignment of a few "
                         "residues can read as 100%% identical, so an identity quoted without a coverage floor is "
                         "meaningless: DAC15 gp095 scores 1.000 unfiltered and 0.375 at coverage 0.8.")
    a = ap.parse_args()
    rows = sorted(csv.DictReader(open(a.tsv), delimiter="\t"), key=lambda r: int(r["start"]))
    seq = {p["id"]: p["sequence"] for p in S5.annotated_proteins(a.genbank)}
    seq_all = dict(seq)          # every protein, including any over the predictor's length cap
    idx = {r["id"]: i for i, r in enumerate(rows)}
    classes = ("holin", "endolysin", "spanin")
    cand = {}
    for c in classes:
        k = f"P_{c}"
        for r in sorted(rows, key=lambda r: -float(r[k]))[:a.top]: cand.setdefault(r["id"], set()).add(c)
        for r in rows:
            if float(r[k]) >= a.threshold: cand.setdefault(r["id"], set()).add(c)
    hol = holin_pfam()
    cls_of = {**{x: "endolysin" for x in ENDOLYSIN_PFAM}, **{x: "holin" for x in hol}, **{x: "spanin" for x in SPANIN_PFAM}}
    hmm_files = fetch_hmms(list(ENDOLYSIN_PFAM) + list(hol) + list(SPANIN_PFAM))
    print(f"# {len(cand)} candidates; {len(hmm_files)} lysis Pfam HMMs available", file=sys.stderr)
    cs = {k: seq[k] for k in cand}
    dom = scan(cs, hmm_files, cls_of)
    topo = phobius(cs)
    tr = {"holin": {r["sequence"] for r in json.load(open(B / "data/processed/dataset.json")) if r["label"] == "holin"}
                   | {r["sequence"] for r in json.load(open(B / "data/processed/holins_extra_clustered.json")) if r["label"] == "holin"},
          "endolysin": {r["sequence"] for r in json.load(open(B / "data/processed/endolysin_positives.json"))},
          "spanin": {r["sequence"] for r in json.load(open(B / "data/processed/spanin_positives.json"))}}
    # Nearest training neighbour, per class. This is what separates "the model had never seen this family" from
    # "the family was simply missing from our data". DAC15 made the distinction concrete: its endolysin gp039 has
    # an 80%-identical relative at full coverage among crAss-like phage PF01832 lysins that were in UniProt all
    # along, so that miss was a coverage gap; its holin gp095 sits at 37.5% to any known holin, which is a real
    # novel-family call. Identity is reported with the coverage floor applied, never without.
    def nearest(ids):
        """max identity to each class's training positives, at or above the coverage floor, per id."""
        res = {}
        try:
            CL = importlib.import_module("03_cluster")       # pyopal; verification-only, never needed to predict
        except ImportError:
            print("# pyopal not installed: skipping nearest-training-neighbour identity", file=sys.stderr)
            return res
        for c in classes:
            tgt = sorted(tr[c])
            for gid in ids:
                best = (0.0, 0.0)
                for ident, cov, _ in CL.align_pairs(seq_all[gid], tgt):
                    if cov >= a.min_cov and ident > best[0]: best = (ident, cov)
                res.setdefault(gid, {})[c] = {"max_identity": round(best[0], 3), "coverage": round(best[1], 2),
                                              "n_targets": len(tgt)}
        return res

    nn = nearest(list(cand))

    out = []
    for gid in sorted(cand, key=lambda g: idx[g]):
        r = rows[idx[gid]]; i = idx[gid]
        near = [rows[j]["product"] for j in range(max(0, i - 3), min(len(rows), i + 4)) if j != i]
        struct_ctx = sum(1 for p in near if STRUCT.search(p))
        s = seq[gid]
        out.append({"id": gid, "index": i, "start": int(r["start"]), "strand": r["strand"], "length": len(s), "product": r["product"],
                    "P": {c: float(r[f"P_{c}"]) for c in classes}, "candidate_for": sorted(cand[gid]),
                    "pfam_domains": dom.get(gid, []), "phobius": topo_summary(topo.get(gid)),
                    "kd_tm_segments": len(F.tm_segments(s)), "cterm20_charge": sum((x in "KR") - (x in "DE") for x in s[-20:]),
                    "structural_neighbours_within_3": struct_ctx, "neighbour_products": near,
                    "in_training": {c: s in tr[c] for c in classes},
                    "nearest_training_neighbour": nn.get(gid),
                    "nn_coverage_floor": a.min_cov})
    # DOMAIN RESCUE: scan the WHOLE proteome (incl. proteins over the predictor's length cap) for lysis domains, and
    # report any domain-bearing protein the model did NOT nominate. On Bacteroides phage DAC15 this is what found the
    # real endolysin candidate (gp039, Glucosaminidase + signal peptide) that the model scored 0.006.
    allp = S5.annotated_proteins(a.genbank)
    dom_all = scan({p["id"]: p["sequence"] for p in allp}, hmm_files, cls_of)
    rescue = []
    for p in sorted(allp, key=lambda p: p["start"]):
        if p["id"] in cand or not dom_all[p["id"]]: continue
        r = rows[idx[p["id"]]] if p["id"] in idx else None
        rescue.append({"id": p["id"], "start": p["start"], "strand": p["strand"], "length": len(p["sequence"]),
                       "product": p["product"], "pfam_domains": dom_all[p["id"]],
                       "P": {c: float(r[f"P_{c}"]) for c in classes} if r else None,
                       "note": "model did not nominate this protein; lysis-domain evidence only" +
                               ("" if r else " (over the predictor's 2000-aa length cap, never scored)")})
    for p in allp: seq_all.setdefault(p["id"], p["sequence"])
    nn_r = nearest([x["id"] for x in rescue])
    for x in rescue:
        topo_x = phobius({x["id"]: seq_all[x["id"]]}).get(x["id"])
        x["phobius"] = topo_summary(topo_x)
        x["nearest_training_neighbour"] = nn_r.get(x["id"])
        x["nn_coverage_floor"] = a.min_cov
    stem = Path(a.tsv).with_suffix("")
    Path(f"{stem}_verified.json").write_text(json.dumps({"model_candidates": out, "domain_rescue": rescue}, indent=1))
    if rescue:
        print("\nDOMAIN RESCUE -- lysis domains on proteins the model did not nominate:")
        for x in rescue:
            d = "; ".join(f"{y['pfam']} {y['name']} [{y['class']}] {y['from']}-{y['to']} E={y['ievalue']}" for y in x["pfam_domains"])
            pp = "never scored (length cap)" if not x["P"] else f"P h/e/s={x['P']['holin']:.3f}/{x['P']['endolysin']:.3f}/{x['P']['spanin']:.3f}"
            f = x["phobius"].get("fields") or {}
            print(f"  {x['id']:<12} {x['start']:>6}{x['strand']} {x['length']:>4}aa  {pp}  Pfam: {d}  "
                  f"Phobius TM={f.get('transmembrane_count')} SP={f.get('signal_peptide')}")
    for o in out:
        d = "; ".join(f"{x['pfam']} {x['name']} [{x['class']}] {x['from']}-{x['to']} E={x['ievalue']}" for x in o["pfam_domains"]) or "none"
        print(f"{o['id']:<12} #{o['index']:>3} {o['length']:>4}aa  P h/e/s={o['P']['holin']:.2f}/{o['P']['endolysin']:.2f}/{o['P']['spanin']:.2f}  "
              f"KD-TM={o['kd_tm_segments']} ct={o['cterm20_charge']:+d} struct_nbrs={o['structural_neighbours_within_3']}  Pfam: {d}")
        if o["phobius"].get("fields"): print(f"{'':14}Phobius: {json.dumps(o['phobius']['fields'])[:150]}")


if __name__ == "__main__":
    main()
