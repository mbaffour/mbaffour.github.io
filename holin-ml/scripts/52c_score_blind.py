"""Score the BLIND scan (scripts/52b) against the genomes' own annotations. Run only after the predictions are committed.

Rules fixed before any annotation was read:
  annotation labels (product names; the only place names are used in this whole pipeline)
    holin      \\b(pin)?holin\\b, not antiholin
    endolysin  the benchmark's terms (endolysin, lysozyme, muramidase, amidase, peptidoglycan hydrolase, murein,
               glucosaminidase, lysin, transglycosylase, glycoside hydrolase) EXCEPT products naming a virion part
               (tail, baseplate, virion, structural, tape measure, needle, spike, capsid, portal, head)
    spanin     spanin, Rz, Rz1
  gene matching: a de novo gene IS an annotated CDS if they share strand and stop codon; otherwise by sequence
               (identical, or one contains the other)
  measures, per class
    agreement  genomes whose annotation has a gene of the class: is the predictor's one call per class that gene?
               And is an annotated gene of the class in the predictor's top 5?
    calls      every CONFIDENT call: annotated as that class (agrees), as hypothetical/unknown (no annotation to agree
               or disagree: a candidate addition), or as something else (conflict)
    novelty    each annotated lysis gene's max identity to that class's training positives (benchmark homology rule),
               so agreement can be read separately for near-copies of training data (>= 0.95), known families
               (0.30-0.95) and new families (< 0.30)
Output: reports/blind/score.json and per-call tables.
"""
import glob, importlib, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
S5 = importlib.import_module("05_scan_genome")
CL = importlib.import_module("03_cluster")
CLASSES = ("holin", "endolysin", "spanin")
LAB = {"holin": re.compile(r"\b(pin)?holin\b", re.I),
       "endolysin": re.compile(r"endolysin|lysozyme|muramidase|amidase|peptidoglycan hydrolase|murein|glucosaminidase|"
                               r"\blysin\b|transglycosylase|glycoside hydrolase", re.I),
       "spanin": re.compile(r"spanin|\bRz1?\b", re.I)}
ANTI = re.compile(r"anti-?holin", re.I)
VIRION = re.compile(r"tail|baseplate|virion|structural|tape.?measure|needle|spike|capsid|portal|head", re.I)
UNKNOWN = re.compile(r"^\s*$|hypothetical|unknown|uncharacteri[sz]ed|DUF\d|putative protein$|^gp\d+$|^protein$", re.I)


def labels(prod):
    if ANTI.search(prod): return set()
    out = {c for c in CLASSES if LAB[c].search(prod)}
    if "endolysin" in out and VIRION.search(prod): out.discard("endolysin")
    return out


def training_positives():
    base = json.load(open(B / "data/processed/dataset.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))
    return {"holin": [r["sequence"] for r in base + cur if r["label"] == "holin"],
            "endolysin": [r["sequence"] for r in json.load(open(B / "data/processed/endolysin_positives_v1_evidence.json"))],
            "spanin": [r["sequence"] for r in json.load(open(B / "data/processed/spanin_positives_signal.json"))]}


_T = None
def _init(t):
    global _T; _T = t
def _best(q):
    return max((i for i, c, s in CL.align_pairs(q, _T) if c >= CL.MIN_COV and s >= 80), default=0.0)


def boot_ci(x, n=2000, seed=0):
    x = np.asarray(x, float)
    if len(x) == 0: return [None, None]
    rng = np.random.default_rng(seed)
    m = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(n)]
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def main():
    sel = json.load(open(B / "data/raw/blind/selection.json"))["accessions"]
    G = []
    for acc in sel:
        pf = B / "reports/blind/pred" / f"{acc}.tsv"
        if not pf.exists(): continue
        hdr = pf.read_text().splitlines()[0].split("\t")
        rows = [dict(zip(hdr, l.split("\t"))) for l in pf.read_text().splitlines()[1:] if l.strip()]
        ann = [x for x in S5.annotated_proteins(B / "data/raw/blind/sealed" / f"{acc}.gb") if x.get("sequence")]
        aseq = {}
        from Bio import SeqIO
        rec = next(SeqIO.parse(B / "data/raw/blind/fna" / f"{acc}.fna", "fasta"))
        # de novo protein sequences are not in the TSV; recompute them the same way the predictor did
        import genecall
        prot = {p["id"]: p["sequence"] for p in genecall.denovo([(rec.id, str(rec.seq))], nested=True)}
        by_stop = {(a["strand"], a["stop"] if a["strand"] == "+" else a["start"]): a for a in ann}
        for r in rows:
            r["seq"] = prot.get(r["id"], "")
            key = (r["strand"], int(r["stop"]) if r["strand"] == "+" else int(r["start"]))
            a = by_stop.get(key)
            if a is None and r["seq"]:
                a = next((x for x in ann if x["sequence"] == r["seq"] or (len(x["sequence"]) >= 20 and (
                    x["sequence"] in r["seq"] or r["seq"] in x["sequence"]))), None)
            r["ann"] = a
            r["ann_product"] = (a.get("product") or "") if a else None
            r["ann_labels"] = labels(r["ann_product"] or "")
        G.append({"acc": acc, "rows": rows, "ann": ann,
                  "ann_lysis": {c: [a for a in ann if c in labels(a.get("product") or "")] for c in CLASSES}})
    print(f"{len(G)} genomes scored", flush=True)

    # novelty of each annotated lysis gene relative to the training positives of its class
    from multiprocessing import Pool
    TP = training_positives(); nov = {}
    for c in CLASSES:
        qs = sorted({a["sequence"] for g in G for a in g["ann_lysis"][c]})
        with Pool(4, initializer=_init, initargs=(TP[c],)) as pool: ids = pool.map(_best, qs, chunksize=4)
        nov[c] = dict(zip(qs, ids))
    def stratum(i): return "near-copy (>=95%)" if i >= 0.95 else "known family (30-95%)" if i >= 0.30 else "new family (<30%)"

    res = {"n_genomes": len(G), "classes": {}}
    for c in CLASSES:
        R = {"genomes_with_annotated": 0, "per_genome": [], "confident_calls": Counter(), "calls": []}
        strat = defaultdict(lambda: {"n": 0, "call_correct": 0, "top5": 0, "not_called_by_genefinder": 0})
        for g in G:
            rows = g["rows"]; annc = g["ann_lysis"][c]
            call = next((r for r in rows if f"{c}:" in r["lysis_call"]), None)
            tier = call["lysis_call"].split(f"{c}:")[1].split(",")[0] if call else None
            if call:
                lab = call["ann_labels"]; prod = call["ann_product"]
                kind = ("agrees" if c in lab else "unannotated gene (not in the annotation)" if prod is None else
                        "annotated hypothetical/unknown" if UNKNOWN.search(prod) else
                        f"annotated as another lysis class" if lab else "annotated with another function")
                R["calls"].append({"genome": g["acc"], "tier": tier, "id": call["id"], "start": call["start"],
                                   "stop": call["stop"], "strand": call["strand"], "length": call["length"],
                                   f"P_{c}": call[f"P_{c}"], "annotation": prod, "verdict": kind,
                                   "genome_has_annotated": bool(annc)})
                if tier == "confident": R["confident_calls"][kind] += 1
            if not annc: continue
            R["genomes_with_annotated"] += 1
            # best-ranked annotated gene of the class in the predictor's ranking
            hits = [r for r in rows if c in r["ann_labels"]]
            best = min((int(r[f"rank_{c}"]) for r in hits), default=None)
            correct = bool(call and c in call["ann_labels"])
            R["per_genome"].append({"genome": g["acc"], "call_correct": correct, "best_rank": best,
                                    "annotated_found_by_genefinder": bool(hits)})
            i = max(nov[c][a["sequence"]] for a in annc); s = strat[stratum(i)]
            s["n"] += 1; s["call_correct"] += correct; s["top5"] += bool(best and best <= 5)
            s["not_called_by_genefinder"] += not hits
        pg = R["per_genome"]
        R["call_is_annotated_gene"] = round(np.mean([p["call_correct"] for p in pg]), 3) if pg else None
        R["call_is_annotated_gene_CI"] = boot_ci([p["call_correct"] for p in pg])
        R["annotated_in_top5"] = round(np.mean([bool(p["best_rank"] and p["best_rank"] <= 5) for p in pg]), 3) if pg else None
        R["annotated_in_top5_CI"] = boot_ci([bool(p["best_rank"] and p["best_rank"] <= 5) for p in pg])
        R["by_novelty"] = dict(strat); R["confident_calls"] = dict(R["confident_calls"])
        res["classes"][c] = R
        print(f"{c:9s} genomes with an annotated {c}: {R['genomes_with_annotated']:3d} | the call is that gene "
              f"{R['call_is_annotated_gene']} {R['call_is_annotated_gene_CI']} | annotated gene in top 5 "
              f"{R['annotated_in_top5']} {R['annotated_in_top5_CI']}", flush=True)
        print(f"          confident calls: {R['confident_calls']}", flush=True)
        for k, v in sorted(strat.items()): print(f"          {k:24s} {v}", flush=True)
    (B / "reports/blind/score.json").write_text(json.dumps(res, indent=1, default=str))
    print("wrote reports/blind/score.json")


if __name__ == "__main__":
    main()
