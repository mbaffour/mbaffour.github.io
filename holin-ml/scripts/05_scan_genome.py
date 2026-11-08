"""Predict holins in a genome: call genes, score every protein, rank candidates.

Two modes of honesty matter here:
  --annotated    use the GenBank record's own CDS translations (what the curators annotated)
  --denovo       call genes with Pyrodigal (meta mode) and score those ORFs - gene calling is an extra inference
Both can be run; the report says which.

Leakage control for benchmarking: --holdout removes from the training set every holin with a >=30% identity / >=50%
coverage local alignment to any protein of the scanned genome, retrains, and scores with that model. Without --holdout
the shipped model is used, and the report says plainly that the genome's own holin may have been in training.

Usage:
  python3 scripts/05_scan_genome.py --acc NC_001416.1 --annotated --holdout
  python3 scripts/05_scan_genome.py --acc NC_008720.1 --annotated --denovo
"""
import argparse, hashlib, json, pickle, sys, urllib.request, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import importlib
C = importlib.import_module("03_cluster")

B = Path(__file__).resolve().parent.parent
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch(acc, rettype, ext):
    d = B / "data/raw/genomes"; d.mkdir(parents=True, exist_ok=True)
    p = d / f"{acc}.{ext}"
    url = f"{EU}?db=nuccore&id={acc}&rettype={rettype}&retmode=text"
    if not p.exists():
        for i in range(5):
            try:
                with urllib.request.urlopen(url, timeout=300) as r: p.write_bytes(r.read()); break
            except Exception:
                if i == 4: raise
                time.sleep(2 ** (i + 1))
        time.sleep(1)
    return p, url


def annotated_proteins(gb):
    from Bio import SeqIO
    out = []
    for rec in SeqIO.parse(gb, "genbank"):
        for f in rec.features:
            if f.type != "CDS" or "translation" not in f.qualifiers: continue
            q = f.qualifiers
            out.append({"id": q.get("locus_tag", [q.get("protein_id", ["?"])[0]])[0], "product": q.get("product", [""])[0],
                        "gene": q.get("gene", [""])[0], "start": int(f.location.start) + 1, "stop": int(f.location.end),
                        "strand": "-" if f.location.strand == -1 else "+", "sequence": q["translation"][0], "caller": "GenBank annotation"})
    return out


def denovo_proteins(fna):
    import pyrodigal
    from Bio import SeqIO
    recs = list(SeqIO.parse(fna, "fasta"))
    orf = pyrodigal.GeneFinder(meta=True)
    out = []
    for rec in recs:
        for i, g in enumerate(orf.find_genes(bytes(rec.seq)), 1):
            out.append({"id": f"{rec.id}_orf{i:04d}", "product": "", "gene": "", "start": g.begin, "stop": g.end,
                        "strand": "+" if g.strand == 1 else "-", "sequence": g.translate().rstrip("*"),
                        "caller": f"Pyrodigal {pyrodigal.__version__} (meta)"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acc", required=True); ap.add_argument("--annotated", action="store_true")
    ap.add_argument("--denovo", action="store_true"); ap.add_argument("--holdout", action="store_true")
    ap.add_argument("--top", type=int, default=15)
    a = ap.parse_args()
    if not (a.annotated or a.denovo): a.annotated = True
    gb, gb_url = fetch(a.acc, "gbwithparts", "gb")
    prots = []
    if a.annotated: prots += annotated_proteins(gb)
    if a.denovo:
        fna, _ = fetch(a.acc, "fasta", "fna"); prots += denovo_proteins(fna)
    prots = [p for p in prots if 20 <= len(p["sequence"]) <= 2000]
    print(f"{a.acc}: scoring {len(prots)} proteins", flush=True)

    bundle = pickle.loads((B / "models/holin_model.pkl").read_bytes())
    data = json.loads((B / "data/processed/dataset.json").read_text())
    train = [r for r in data if r["label"] in ("holin", "negative")]
    note = "shipped model; the scanned genome's own holin may have been part of training"
    removed = []
    if a.holdout:
        hol = [r for r in train if r["label"] == "holin"]
        best = C.search([p["sequence"] for p in prots], [r["sequence"] for r in hol], min_score=0)
        keep_h = [r for r, b in zip(hol, best) if b < C.MIN_ID]
        removed = [{"id": r["id"], "identity_to_genome": round(float(b), 3),
                    "source": (r["sources"][0].get("name") or r["sources"][0].get("description", ""))[:80]}
                   for r, b in zip(hol, best) if b >= C.MIN_ID]
        train = keep_h + [r for r in train if r["label"] == "negative"]
        note = f"retrained after removing {len(removed)} training holins homologous to this genome (>={C.MIN_ID:.0%} id, >={C.MIN_COV:.0%} cov)"
        print(note, flush=True)
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import HistGradientBoostingClassifier
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        esm = F.ESM(B / "models/esm_cache")
        ys = np.array([r["label"] == "holin" for r in train], int)
        def mat(seqs):
            h = np.stack([F.handcrafted(s) for s in seqs]);
            return {"hand": h, "esm": esm.embed(seqs), "both": np.hstack([h, esm.embed(seqs)])}[bundle["features"]]
        X = mat([r["sequence"] for r in train])
        model = (make_pipeline(StandardScaler(), LogisticRegression(max_iter=4000, class_weight="balanced"))
                 if bundle["algorithm"] == "logreg" else
                 HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, l2_regularization=1.0, class_weight="balanced", random_state=0))
        model.fit(X, ys)
    else:
        model = bundle["model"]
        esm = F.ESM(B / "models/esm_cache")
        def mat(seqs):
            h = np.stack([F.handcrafted(s) for s in seqs])
            return {"hand": h, "esm": esm.embed(seqs), "both": np.hstack([h, esm.embed(seqs)])}[bundle["features"]]
    Xp = mat([p["sequence"] for p in prots])
    score = model.predict_proba(Xp)[:, 1]
    for p, s in zip(prots, score):
        p["holin_score"] = round(float(s), 4); p["n_tm_hydropathy"] = len(F.tm_segments(p["sequence"])); p["length"] = len(p["sequence"])
        p.pop("sequence_full", None)
    ranked = sorted(prots, key=lambda p: -p["holin_score"])
    out = {"accession": a.acc, "source_url": gb_url, "scanned_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "n_proteins": len(prots), "gene_sources": sorted({p["caller"] for p in prots}),
           "model": {k: bundle[k] for k in ("features", "algorithm", "esm_model")}, "leakage_note": note,
           "training_holins_removed": removed,
           "ranked": [{k: p[k] for k in ("id", "gene", "product", "start", "stop", "strand", "length", "n_tm_hydropathy", "holin_score", "caller")}
                      for p in ranked]}
    rp = B / "reports" / f"scan_{a.acc.replace('.', '_')}{'_holdout' if a.holdout else ''}.json"
    rp.write_text(json.dumps(out, indent=1))
    print(f"-> {rp.relative_to(B)}")
    for p in ranked[:a.top]:
        print(f'  {p["holin_score"]:.3f}  {p["id"]:14} {p["length"]:4} aa  TM={p["n_tm_hydropathy"]}  {p["gene"] or "":8} {p["product"][:58]}')


if __name__ == "__main__":
    main()
