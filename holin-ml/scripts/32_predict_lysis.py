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

Honest performance (leave-one-genome-out over 63 genomes, reports/logo_benchmark.json and capacity_sweep.md):
genome-scan AP, realistic / strict --  holin 0.754 / 0.613, endolysin 0.809 / 0.614, spanin 0.800 / 0.568.
The true gene is in the top 5 of its genome 87-100% of the time but ranked first only 50-70%: this is a SHORTLIST
generator, not a caller. "Strict" means a family the model has never seen.

High confidence is PER CLASS, read from each model bundle (column high_conf): holin and spanin 0.95; endolysin
0.9995, because the shipped endolysin model trains without early stopping and its probabilities are more
extreme -- at 0.9995 it beats the previous model's 0.95 on both precision and recall (see models bundle note).

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
    ap.add_argument("--top", type=int, default=5,
                    help="how many ranked candidates per class to print in the summary (default 5). The ranked "
                         "shortlist is printed whatever the threshold, because a novel-family gene can rank well "
                         "while scoring far below any threshold.")
    ap.add_argument("--domains", action="store_true",
                    help="also scan every protein with the lysis Pfam HMMs (pyhmmer) and add a pfam_lysis column. "
                         "Slower and needs the HMMs (cached in data/raw/pfam_hmm, fetched once from InterPro), but "
                         "it is the evidence that does NOT depend on the model: on Bacteroides phage DAC15 the "
                         "real endolysin candidate scored 0.006 and was found only this way.")
    ap.add_argument("--hmm-dir", help="directory of lysis Pfam .hmm files for --domains. Defaults to "
                                      "data/raw/pfam_hmm, downloading any that are missing from InterPro "
                                      "(one-off). Pre-populate it and pass this for an offline or HPC run.")
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

    bundles = {c: pickle.load(open(B / "models" / MODELS[c], "rb")) for c in CLASSES}
    models = {c: bundles[c]["model"] for c in CLASSES}
    # high-confidence cut-off per class: probabilities are not on a common scale across the three models
    HC = {c: float(bundles[c].get("high_confidence_threshold", 0.95)) for c in CLASSES}
    esm = F.ESM(B / "models/esm_cache")
    X = np.hstack([np.array([F.handcrafted(p["sequence"]) for p in ps]), esm.embed([p["sequence"] for p in ps])])
    assert X.shape[1] == 516, X.shape
    P = {c: models[c].predict_proba(X)[:, 1] for c in CLASSES}
    for i, p in enumerate(ps):
        p["P"] = {c: float(P[c][i]) for c in CLASSES}
        b = max(CLASSES, key=lambda c: p["P"][c]); p["call"] = b if p["P"][b] >= a.threshold else "none"
        p["high_conf"] = ",".join(c for c in CLASSES if p["P"][c] >= HC[c])
        p["cassette"] = ""
    # rank within this run, per class: 1 = highest P. Ranks are reported alongside the probabilities because the
    # probability alone is not safe to read as a verdict out of distribution -- the honest use of this tool is a
    # ranked shortlist per class, which is what the leave-one-genome-out numbers actually measure.
    for c in CLASSES:
        for r, i in enumerate(sorted(range(len(ps)), key=lambda i: -ps[i]["P"][c]), 1):
            ps[i].setdefault("rank", {})[c] = r
    cass = SC.find_cassettes(ps, a.threshold, a.cassette_window) if positional else []
    for k, cs in enumerate(cass, 1):
        for m in cs["members"]: ps[m["index"]]["cassette"] = str(k)

    dom, dtier = {}, {}
    if a.domains:
        try:
            import domains as D                       # pyhmmer; optional, predict works without it
            hmms, cls_of = D.lysis_hmms(a.hmm_dir)
            hits = D.scan({p["id"]: p["sequence"] for p in ps}, hmms, cls_of)
            dom = {k: D.summarise(v) for k, v in hits.items() if D.summarise(v)}
            dtier = {p["id"]: {c: D.tier(hits.get(p["id"]), c) for c in CLASSES} for p in ps}
            n2 = sum(1 for v in dtier.values() if max(v.values()) >= 2)
            print(f"# domain scan: {len(hmms)} lysis HMMs; {n2} of {len(ps)} proteins carry a CATALYTIC or "
                  f"family-defining lysis domain ({len(dom)} with any hit incl. binding-only)", file=sys.stderr)
        except Exception as e:
            print(f"# --domains unavailable ({type(e).__name__}: {e}); continuing without it", file=sys.stderr)
            dom, dtier, a.domains = {}, {}, False

    # Evidence-aware rank: domain tier first, then model probability. This is the integration that matters --
    # a catalytic lysis domain is model-independent evidence, so it outranks any probability. On DAC15 it moves
    # gp039 from model rank 25 to evidence rank 1 for endolysin, which is the whole point.
    if a.domains:
        for c in CLASSES:
            order = sorted(range(len(ps)), key=lambda i: (-dtier[ps[i]["id"]][c], -ps[i]["P"][c]))
            for r, i in enumerate(order, 1): ps[i].setdefault("ev_rank", {})[c] = r

    cols = ["id", "gene", "product", "start", "stop", "strand", "length",
            "P_holin", "P_endolysin", "P_spanin", "rank_holin", "rank_endolysin", "rank_spanin",
            "call", "high_conf", "cassette"] + (["pfam_lysis", "dom_tier_holin", "dom_tier_endolysin", "dom_tier_spanin",
                                    "ev_rank_holin", "ev_rank_endolysin", "ev_rank_spanin"] if a.domains else [])
    lines = ["\t".join(cols)]
    for p in ps:
        row = [p["id"], p.get("gene", ""), (p.get("product") or "").replace("\t", " "),
               p["start"], p["stop"], p["strand"], len(p["sequence"]),
               f"{p['P']['holin']:.4f}", f"{p['P']['endolysin']:.4f}", f"{p['P']['spanin']:.4f}",
               p["rank"]["holin"], p["rank"]["endolysin"], p["rank"]["spanin"], p["call"], p["high_conf"],
               p["cassette"]]
        if a.domains:
            row.append(dom.get(p["id"], ""))
            row += [dtier[p["id"]][c] for c in CLASSES] + [p["ev_rank"][c] for c in CLASSES]
        lines.append("\t".join(str(x) for x in row))
    (Path(a.out).write_text("\n".join(lines) + "\n") if a.out else print("\n".join(lines)))

    called = {c: sum(1 for p in ps if p["call"] == c) for c in CLASSES}
    print(f"# called at >={a.threshold}: " + ", ".join(f"{c} {called[c]}" for c in CLASSES) +
          f"; cassettes {len(cass)}" + ("" if positional else " (n/a for protein FASTA)"), file=sys.stderr)
    hc = {c: sum(1 for p in ps if c in p["high_conf"].split(",")) for c in CLASSES}
    print("# high confidence (per-class cut-offs " + ", ".join(f"{c} >={HC[c]:g}" for c in CLASSES) + "): "
          + ", ".join(f"{c} {hc[c]}" for c in CLASSES), file=sys.stderr)
    # ranked shortlist per class, printed whatever the threshold
    for c in CLASSES:
        key = (lambda p: (-dtier[p["id"]][c], -p["P"][c])) if a.domains else (lambda p: -p["P"][c])
        top = sorted(ps, key=key)[:a.top]
        how = "by domain evidence, then P" if a.domains else f"by P({c})"
        print(f"#\n# {c.upper()} -- top {len(top)} of {len(ps)} {how}", file=sys.stderr)
        print(f"# {'rank':>4} {'gene/id':<20} {'location':>22} {'len':>5} {'P':>8}"
              f"{'  ev  domain' if a.domains else ''}", file=sys.stderr)
        for p in top:
            loc = f"{p['start']}..{p['stop']}{p['strand']}" if positional else "n/a"
            mark = " *" if p["call"] == c else "  "
            ev = f"  {dtier[p['id']][c]}   {dom.get(p['id']) or '-'}" if a.domains else ""
            rk = p["ev_rank"][c] if a.domains else p["rank"][c]
            print(f"# {rk:>4} {(p.get('gene') or p['id'])[:20]:<20} {loc:>22} "
                  f"{len(p['sequence']):>5} {p['P'][c]:>8.4f}{mark}{ev}", file=sys.stderr)
    print(f"#\n# * = called at >={a.threshold}. A gene from a family the model has never seen can rank near the "
          f"top while scoring well below any threshold, so read the ranking, not only the call.", file=sys.stderr)
    if a.domains:
        missed = [p for p in ps if max(dtier[p["id"]].values()) >= 2 and p["call"] == "none"]
        if missed:
            print(f"# {len(missed)} protein(s) carry a lysis Pfam domain but were NOT called -- inspect these "
                  f"first: " + ", ".join(f"{p.get('gene') or p['id']} ({dom[p['id']]}, rank_e="
                  f"{p['rank']['endolysin']} -> ev_rank_e={p['ev_rank']['endolysin']})" for p in missed[:6]), file=sys.stderr)
    if a.show_cassettes:
        for k, cs in enumerate(cass, 1):
            mem = ", ".join(f"{m['gene'] or m['id']}[{'/'.join(m['classes_called'])}]" for m in cs["members"])
            print(f"# cassette {k} (genes {cs['gene_index_range']}): {mem}", file=sys.stderr)


if __name__ == "__main__":
    main()
