"""Scan MANY phage genomes with the three-gene lysis caller and aggregate how well it does across diversity.

Reuses the verified scanner (scripts/29): same 516-d feature matrix and the same find_cassettes(). Two sources:
  --pool            the 300 Caudoviricetes RefSeq genomes already mined (data/processed/pool.json); ESM is cached
                    for these, so this is fast. BREADTH test. Caveat: endolysin/spanin positives were partly drawn
                    from pool annotations, so a recovered endolysin/spanin here may be IN-SAMPLE; this script marks
                    the in-sample fraction so the recovery rate is not read as generalization. Holins were not
                    taken from the pool, so holin calls are out-of-sample.
  --accessions F    a text file of RefSeq accessions (one per line, optional "name<TAB>acc"); missing GenBank is
                    fetched to data/raw/panel/. Use this for a clean OUT-OF-SAMPLE panel.

For each genome: score all proteins, call argmax>=threshold, detect cassettes, and for each class check whether the
model recovers the annotated gene(s) of that class (top-scoring protein is annotated that class = "top hit correct";
any annotated gene of that class scored >=threshold = "recovered"). Aggregates across genomes, flags the
actinobacterial-host subset (the model's historical weak spot) and any high-confidence UN-annotated calls.

Usage: python3 scripts/30_scan_many.py --pool [--limit N] [--threshold 0.5] [--cassette-window 6]
       python3 scripts/30_scan_many.py --accessions panel.txt
"""
import argparse, hashlib, importlib, json, re, sys, time, urllib.request
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
SC = importlib.import_module("29_scan_cassette")

B = Path(__file__).resolve().parent.parent
CLASSES = SC.CLASSES
NAME = {"holin": re.compile(r"holin", re.I),
        "endolysin": re.compile(r"endolysin|lysozyme|muramidase|amidase|peptidoglycan|murein|glucosaminidase|\blysin\b|transglycosylase", re.I),
        "spanin": re.compile(r"spanin|\bRz\b|\bRz1\b", re.I)}
ANTI = re.compile(r"anti-?holin", re.I)
ACTINO = re.compile(r"mycobacteri|streptomyc|corynebacteri|rhodococc|gordonia|actinomyc|nocardia|propionibacteri|"
                    r"bifidobacteri|arthrobacter|tsukamurella|microbacteri|dietzia|kineococc|clavibacter", re.I)


def pool_genomes():
    pool = json.load(open(B / "data/processed/pool.json"))
    by = defaultdict(list)
    for p in pool: by[p["accession"]].append(p)
    out = []
    for acc, ps in by.items():
        ps = [{"id": p.get("id") or p.get("gene") or "", "gene": p.get("gene") or "", "product": p.get("product") or "",
               "start": p["start"], "sequence": p["sequence"], "organism": ""} for p in sorted(ps, key=lambda p: p["start"])]
        out.append((acc, "", ps))
    return out


def fetch_panel(path):
    S = importlib.import_module("05_scan_genome")
    pd = B / "data/raw/panel"; pd.mkdir(parents=True, exist_ok=True)
    EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        acc = line.split("\t")[-1].strip()
        f = pd / f"{acc}.gb"
        if not f.exists():
            for i in range(5):
                try:
                    data = urllib.request.urlopen(f"{EU}?db=nuccore&id={acc}&rettype=gbwithparts&retmode=text", timeout=600).read()
                    f.write_bytes(data); time.sleep(0.5); break
                except Exception:
                    if i == 4: print("FETCH FAILED", acc, flush=True)
                    time.sleep(2 ** (i + 1))
        if not f.exists(): continue
        try:
            ps = S.annotated_proteins(str(f))
            org = ""
            out.append((acc, org, [dict(p, id=p.get("locus_tag") or p.get("protein_id") or "", gene=p.get("gene") or "") for p in ps]))
        except Exception as e:
            print("PARSE FAILED", acc, e, flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", action="store_true"); ap.add_argument("--accessions")
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--cassette-window", type=int, default=6)
    ap.add_argument("--out", default=str(B / "reports/many_phage_scan"))
    a = ap.parse_args()

    models = {c: __import__("pickle").load(open(B / "models" / SC.MODELS[c], "rb"))["model"] for c in CLASSES}
    esm = F.ESM(B / "models/esm_cache")
    # in-sample training sequences per class
    tr = {"holin": {r["sequence"] for r in json.load(open(B / "data/processed/dataset.json")) if r["label"] == "holin"}
                   | {r["sequence"] for r in json.load(open(B / "data/processed/holins_extra_clustered.json")) if r["label"] == "holin"},
          "endolysin": {r["sequence"] for r in json.load(open(B / "data/processed/endolysin_positives.json"))},
          "spanin": {r["sequence"] for r in json.load(open(B / "data/processed/spanin_positives.json"))}}

    genomes = pool_genomes() if a.pool else fetch_panel(a.accessions)
    if a.limit: genomes = genomes[:a.limit]
    print(f"scanning {len(genomes)} genomes", flush=True)

    agg = {"n_genomes": 0, "with_cassette": 0, "actino_genomes": 0, "actino_with_cassette": 0,
           "per_class": {c: {"genomes_with_annotation": 0, "recovered": 0, "top_hit_correct": 0,
                             "recovered_in_sample": 0} for c in CLASSES},
           "novel_calls": []}
    per_genome = []; t0 = time.time()
    for n, (acc, org, ps) in enumerate(genomes, 1):
        if not ps: continue
        seqs = [p["sequence"] for p in ps]
        X = np.hstack([np.array([F.handcrafted(s) for s in seqs]), esm.embed(seqs)])
        probs = {c: models[c].predict_proba(X)[:, 1] for c in CLASSES}
        for i, p in enumerate(ps):
            p["index"] = i; p["P"] = {c: float(probs[c][i]) for c in CLASSES}
            b = max(CLASSES, key=lambda c: p["P"][c]); p["call"] = b if p["P"][b] >= a.threshold else "none"
        cass = SC.find_cassettes(ps, a.threshold, a.cassette_window)
        org_txt = " ".join((p["product"] or "") + " " + (p.get("organism") or "") for p in ps)
        is_actino = bool(ACTINO.search(acc + " " + org_txt))  # organism rarely in pool rows; acc as weak proxy
        agg["n_genomes"] += 1; agg["with_cassette"] += bool(cass); agg["actino_genomes"] += is_actino
        agg["actino_with_cassette"] += bool(cass) and is_actino
        rec = {"accession": acc, "n_proteins": len(ps), "cassettes": len(cass), "class": {}}
        for c in CLASSES:
            ann = [p for p in ps if NAME[c].search(p["product"]) and not (c == "holin" and ANTI.search(p["product"]) and not re.search(r"(?<!anti[- ])holin", p["product"], re.I))]
            if ann:
                agg["per_class"][c]["genomes_with_annotation"] += 1
                hit = [p for p in ann if p["P"][c] >= a.threshold]
                agg["per_class"][c]["recovered"] += bool(hit)
                top = max(ps, key=lambda p: p["P"][c])
                agg["per_class"][c]["top_hit_correct"] += bool(NAME[c].search(top["product"]))
                if hit: agg["per_class"][c]["recovered_in_sample"] += any(p["sequence"] in tr[c] for p in hit)
                rec["class"][c] = {"annotated": len(ann), "recovered": bool(hit),
                                   "top_is_annotated": bool(NAME[c].search(top["product"]))}
            # high-confidence un-annotated calls (candidate findings): called a class, product not that class, not in training
            for p in ps:
                if p["call"] == c and p["P"][c] >= 0.9 and not NAME[c].search(p["product"]) and p["sequence"] not in tr[c] \
                   and not (c != "spanin" and NAME["spanin"].search(p["product"])):
                    agg["novel_calls"].append({"accession": acc, "class": c, "P": round(p["P"][c], 3),
                                               "gene": p["gene"] or p["id"], "product": p["product"][:50], "length": len(p["sequence"])})
        per_genome.append(rec)
        if n % 50 == 0: print(f"  {n}/{len(genomes)} ({int(time.time()-t0)}s)", flush=True)

    pc = agg["per_class"]
    summary = {"genomes_scanned": agg["n_genomes"],
               "genomes_with_a_detected_cassette": agg["with_cassette"],
               "cassette_rate": round(agg["with_cassette"] / max(agg["n_genomes"], 1), 3),
               "actino_genomes": agg["actino_genomes"], "actino_with_cassette": agg["actino_with_cassette"],
               "per_class_recovery": {c: {
                   "genomes_with_an_annotated_gene": pc[c]["genomes_with_annotation"],
                   "recovered_at_threshold": pc[c]["recovered"],
                   "recovery_rate": round(pc[c]["recovered"] / max(pc[c]["genomes_with_annotation"], 1), 3),
                   "top_scoring_protein_is_annotated_that_class": pc[c]["top_hit_correct"],
                   "of_recovered_how_many_in_sample": pc[c]["recovered_in_sample"]} for c in CLASSES},
               "high_conf_unannotated_calls": len(agg["novel_calls"])}
    out = {"source": "pool" if a.pool else a.accessions, "threshold": a.threshold,
           "cassette_window": a.cassette_window, "summary": summary,
           "caveat": ("pool endolysin/spanin annotations were partly used in training, so their recovery is partly "
                      "in-sample (see of_recovered_how_many_in_sample); holins were not drawn from the pool"),
           "novel_calls": sorted(agg["novel_calls"], key=lambda d: -d["P"])[:50], "per_genome": per_genome}
    Path(a.out).parent.mkdir(exist_ok=True)
    json.dump(out, open(a.out + ".json", "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
