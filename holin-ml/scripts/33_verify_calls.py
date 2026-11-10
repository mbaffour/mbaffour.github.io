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
HMMDIR = B / "data/raw/pfam_hmm"
PHOBIUS = "https://phobius.sbc.su.se/api/predict"
ENDOLYSIN_PFAM = {  # catalytic and cell-wall-binding domains found in phage lysins
    "PF00959": "Phage_lysozyme (GH24)", "PF01183": "Glyco_hydro_25 lysozyme", "PF01510": "Amidase_2",
    "PF01520": "Amidase_3", "PF05257": "CHAP", "PF00877": "NLPC_P60", "PF01464": "SLT transglycosylase",
    "PF01551": "Peptidase_M23", "PF02557": "VanY (M15)", "PF08291": "Peptidase_M15_3", "PF13539": "Peptidase_M15_4",
    "PF01832": "Glucosaminidase", "PF05838": "Glyco_hydro_108", "PF13702": "Lysozyme_like", "PF07486": "Hydrolase_2",
    "PF01471": "PG_binding_1", "PF01476": "LysM", "PF18341": "PSA endolysin CBD", "PF16754": "Pesticin",
    # newer Pfam families named for phage endolysins -- lambda R is PF31186, NOT PF00959 (found via a positive control)
    "PF31186": "Endolysin", "PF25309": "Endolysin-like domain", "PF31067": "Endolysin A",
    "PF13406": "SLT_2 transglycosylase", "PF06737": "Transglycosylase", "PF01473": "CW_binding_1 (choline-binding)",
    "PF08230": "CW_7 cell-wall binding", "PF09374": "PG_binding_3"}
SPANIN_PFAM = {"PF17531": "Spanin outer lipoprotein (T7-like)", "PF26831": "Phage spanin outer lipoprotein",
               "PF03245": "Phage_lysis (Rz)", "PF06085": "Rz1 lipoprotein"}
STRUCT = re.compile(r"virion|structural|head|capsid|tail|fib(er|re)|baseplate|portal|terminase|tape.?measure|neck", re.I)
NOT_HOLIN = re.compile(r"choline|cholinesterase|carnitine|betaine|sulfatase|kinase|acyltransferase|cell wall binding", re.I)


def holin_pfam():
    d = json.load(open(B / "data/raw/interpro_pfam_holin.json"))
    return {r["metadata"]["accession"]: r["metadata"]["name"] for r in d["results"] if not NOT_HOLIN.search(r["metadata"]["name"])}


def fetch_hmms(accs):
    HMMDIR.mkdir(parents=True, exist_ok=True)
    prov_p = HMMDIR / "provenance.json"
    prov = json.loads(prov_p.read_text()) if prov_p.exists() else {}
    for acc in accs:
        f = HMMDIR / f"{acc}.hmm"
        if f.exists(): continue
        url = f"https://www.ebi.ac.uk/interpro/api/entry/pfam/{acc}?annotation=hmm"
        try:
            raw = urllib.request.urlopen(url, timeout=120).read()
            txt = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
            if not txt.startswith(b"HMMER"): raise ValueError("not an HMM")
            f.write_bytes(txt); prov[acc] = {"url": url, "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        except Exception as e:
            prov[acc] = {"url": url, "error": f"{type(e).__name__}: {str(e)[:80]}"}
        time.sleep(0.3)
    prov_p.write_text(json.dumps(prov, indent=1))
    return [HMMDIR / f"{a}.hmm" for a in accs if (HMMDIR / f"{a}.hmm").exists()]


def scan(seqs, hmm_files, cls_of):
    import pyhmmer
    alpha = pyhmmer.easel.Alphabet.amino()
    hmms = []
    for f in hmm_files:
        with pyhmmer.plan7.HMMFile(str(f)) as h: hmms.extend(list(h))
    digital = [pyhmmer.easel.TextSequence(name=k.encode(), sequence=v).digitize(alpha) for k, v in seqs.items()]
    out = {k: [] for k in seqs}
    for hits in pyhmmer.hmmer.hmmscan(digital, hmms, E=1e-3, domE=1e-3):
        q = hits.query.name.decode() if isinstance(hits.query.name, bytes) else hits.query.name
        for h in hits:
            if not h.included: continue
            for d in h.domains.included:
                acc = (h.accession or h.name).decode().split(".")[0] if isinstance(h.accession or h.name, bytes) else str(h.accession or h.name).split(".")[0]
                name = h.name.decode() if isinstance(h.name, bytes) else h.name
                out[q].append({"pfam": acc, "name": name, "class": cls_of.get(acc, "?"), "from": d.env_from, "to": d.env_to,
                               "ievalue": float(f"{d.i_evalue:.2e}")})
    return out


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
    a = ap.parse_args()
    rows = sorted(csv.DictReader(open(a.tsv), delimiter="\t"), key=lambda r: int(r["start"]))
    seq = {p["id"]: p["sequence"] for p in S5.annotated_proteins(a.genbank)}
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
                    "in_training": {c: s in tr[c] for c in classes}})
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
    for x in rescue:
        topo_x = phobius({x["id"]: [p["sequence"] for p in allp if p["id"] == x["id"]][0]}).get(x["id"])
        x["phobius"] = topo_summary(topo_x)
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
