"""predict_lysis -- the deployable entrypoint. Find holins, endolysins and spanins in ANY phage sequence.

Input (choose one):
  --proteins FILE.faa    protein FASTA: scored directly (one row per sequence). No positions, so no cassette calls.
  --genome   FILE.fna    nucleotide FASTA (genome/contig/MAG bin): genes are called de novo with Pyrodigal, then
                         scored. This is how you run it on a raw assembly with no annotation.
  --genbank  FILE.gb     GenBank with CDS annotations: the annotated proteins are scored in genome order.
  --acc      ACCESSION   fetch that nucleotide record from NCBI and treat as --genbank.

For every protein it reports independent probabilities P(holin), P(endolysin), P(spanin) -- the three genes are
called INDEPENDENTLY, wherever they sit -- and, when positions are known, flags lysis cassettes where all three
co-locate. Output is TSV (stdout or --out), plus a short summary and optional --show-cassettes to stderr.

Honest performance (leave-one-genome-out, reports/*_eval.json): holin realistic 0.965 / strict 0.785; endolysin
0.843 / 0.729; spanin 0.834 / 0.729. "Strict" (a family the model has never seen) gives a shortlist, not a verdict.
Precision ~0.75 at P>=0.9, so use --threshold 0.95 for high-confidence calls.

Dependencies: numpy, scikit-learn (must match the version the models were pickled with), torch + transformers
(ESM-2 facebook/esm2_t12_35M_UR50D, ~130 MB, downloaded on first run), and pyrodigal for --genome. See DEPLOY.md.

Usage: python3 scripts/32_predict_lysis.py (--proteins F | --genome F | --genbank F | --acc ACC) [--threshold 0.5]
                                           [--out F.tsv] [--show-cassettes] [--cassette-window 6]
"""
import argparse, importlib, json, pickle, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
SC = importlib.import_module("29_scan_cassette")
S5 = importlib.import_module("05_scan_genome")

B = Path(__file__).resolve().parent.parent
CLASSES = SC.CLASSES
MODELS = SC.MODELS


def read_faa(path):
    out, name, buf = [], None, []
    for ln in Path(path).read_text().splitlines():
        if ln.startswith(">"):
            if name is not None: out.append((name, "".join(buf)))
            name = ln[1:].split()[0]; buf = []
        else: buf.append(ln.strip())
    if name is not None: out.append((name, "".join(buf)))
    return [{"id": n, "product": "", "gene": "", "start": i, "stop": i, "strand": ".", "sequence": s, "caller": "input FASTA"}
            for i, (n, s) in enumerate(out) if s]


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--proteins"); g.add_argument("--genome"); g.add_argument("--genbank"); g.add_argument("--acc")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--cassette-window", type=int, default=6)
    ap.add_argument("--show-cassettes", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()

    positional = True
    if a.proteins:
        ps = read_faa(a.proteins); positional = False; src = a.proteins
    elif a.genome:
        ps = S5.denovo_proteins(a.genome); src = a.genome
    elif a.genbank:
        ps = S5.annotated_proteins(a.genbank); src = a.genbank
    else:
        gb = S5.fetch(a.acc, "gbwithparts", "gb"); ps = S5.annotated_proteins(gb); src = a.acc
    ps = [p for p in ps if p.get("sequence") and 20 <= len(p["sequence"]) <= 2000]
    if not ps: sys.exit("no scorable proteins (need 20-2000 aa)")
    if positional: ps.sort(key=lambda p: p["start"])
    print(f"# {src}: {len(ps)} proteins", file=sys.stderr)

    models = {c: pickle.load(open(B / "models" / MODELS[c], "rb"))["model"] for c in CLASSES}
    esm = F.ESM(B / "models/esm_cache")
    X = np.hstack([np.array([F.handcrafted(p["sequence"]) for p in ps]), esm.embed([p["sequence"] for p in ps])])
    assert X.shape[1] == 516, X.shape
    P = {c: models[c].predict_proba(X)[:, 1] for c in CLASSES}
    for i, p in enumerate(ps):
        p["P"] = {c: float(P[c][i]) for c in CLASSES}
        b = max(CLASSES, key=lambda c: p["P"][c]); p["call"] = b if p["P"][b] >= a.threshold else "none"
        p["cassette"] = ""
    cass = SC.find_cassettes(ps, a.threshold, a.cassette_window) if positional else []
    for k, cs in enumerate(cass, 1):
        for m in cs["members"]: ps[m["index"]]["cassette"] = str(k)

    cols = ["id", "gene", "product", "start", "stop", "strand", "length", "P_holin", "P_endolysin", "P_spanin", "call", "cassette"]
    lines = ["\t".join(cols)]
    for p in ps:
        lines.append("\t".join(str(x) for x in [p["id"], p.get("gene", ""), (p.get("product") or "").replace("\t", " "),
                      p["start"], p["stop"], p["strand"], len(p["sequence"]),
                      f"{p['P']['holin']:.4f}", f"{p['P']['endolysin']:.4f}", f"{p['P']['spanin']:.4f}", p["call"], p["cassette"]]))
    (Path(a.out).write_text("\n".join(lines) + "\n") if a.out else print("\n".join(lines)))

    called = {c: sum(1 for p in ps if p["call"] == c) for c in CLASSES}
    print(f"# called at >={a.threshold}: " + ", ".join(f"{c} {called[c]}" for c in CLASSES) +
          f"; cassettes {len(cass)}" + ("" if positional else " (n/a for protein FASTA)"), file=sys.stderr)
    if a.show_cassettes:
        for k, cs in enumerate(cass, 1):
            mem = ", ".join(f"{m['gene'] or m['id']}[{'/'.join(m['classes_called'])}]" for m in cs["members"])
            print(f"# cassette {k} (genes {cs['gene_index_range']}): {mem}", file=sys.stderr)


if __name__ == "__main__":
    main()
