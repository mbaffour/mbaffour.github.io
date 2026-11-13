"""predict_lysis -- the deployable entrypoint. Find holins, endolysins and spanins in ANY phage sequence.

Input (choose one):
  --proteins FILE.faa    protein FASTA: scored directly (one row per sequence). No positions, so no cassette calls.
  --genome   FILE.fna    nucleotide FASTA (genome/contig/MAG bin): genes are called de novo with Pyrodigal, plus
                         nested lipoprotein ORFs (embedded o-spanins such as lambda Rz1, which standard gene finders
                         never call; scripts/genecall.py; --no-nested to skip), then scored. This is how you run it on
                         a raw assembly with no annotation.
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

Holin mode: --holin-mode t4aware averages the standard holin model with one that also learned 37 holin families mined
by genomic context. It ranks T4-type holins far higher (3-30 instead of 10-67 in their genomes, unseen-family test)
and is otherwise within noise of the standard model; see reports/holin_generalisation.md.

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
    ap.add_argument("--no-context", action="store_true",
                    help="rank by each model's P alone, ignoring neighbouring genes (genome/GenBank input only)")
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
    ap.add_argument("--no-nested", action="store_true",
                    help="--genome only: do not add nested lipoprotein ORFs (embedded o-spanins) to the Pyrodigal genes")
    ap.add_argument("--holin-mode", choices=["standard", "t4aware"], default="standard",
                    help="t4aware: P(holin) is the mean of the standard holin model and models/holin_model_mined.pkl "
                         "(the same recipe plus 77 holins from 37 families mined by genomic context, scripts/49). "
                         "Leave-one-genome-out on 78 CPT genomes, unseen families: T4-type holins ranked 3-30 in "
                         "their genomes instead of 10-67; overall ranked 1st 0.513 vs 0.538 and top 5 0.846 vs "
                         "0.846 (difference within noise). Use it for T4-like phages; standard is the default "
                         "because it is not better overall (reports/holin_generalisation.md).")
    ap.add_argument("--out")
    a = ap.parse_args()

    positional = True
    if a.proteins:
        ps = read_faa(a.proteins); positional = False; src = a.proteins
    elif a.genome:
        import genecall
        from Bio import SeqIO
        ps = genecall.denovo([(r.id, str(r.seq)) for r in SeqIO.parse(a.genome, "fasta")], nested=not a.no_nested)
        for q in ps:                       # say where the extra ORFs came from; nothing else in a de novo run has a product
            if q.get("caller") == "nested-lipoprotein": q["product"] = f"nested lipoprotein ORF in {q['host']}"
        src = a.genome
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
    if a.holin_mode == "t4aware":
        mined = pickle.load(open(B / "models/holin_model_mined.pkl", "rb"))["model"]
        P["holin"] = 0.5 * (P["holin"] + mined.predict_proba(X)[:, 1])
        print("# holin mode: t4aware (mean of the standard and mined-family holin models)", file=sys.stderr)
    for i, p in enumerate(ps):
        p["P"] = {c: float(P[c][i]) for c in CLASSES}
        b = max(CLASSES, key=lambda c: p["P"][c]); p["call"] = b if p["P"][b] >= a.threshold else "none"
        p["high_conf"] = ",".join(c for c in CLASSES if p["P"][c] >= HC[c])
        p["cassette"] = ""
    # genomic context (positional input only): a candidate next to a strong gene of another lysis class is lifted.
    # z = logit(P) + beta * strongest other-class P within W genes; parameters and measured gains in
    # models/context_params.json. Raw P columns are unchanged; ranks and calls use z.
    CTX = json.load(open(B / "models/context_params.json")) if (positional and not a.no_context) else None
    lg = lambda v: float(np.log(max(min(v, 1 - 1e-6), 1e-6) / (1 - max(min(v, 1 - 1e-6), 1e-6))))
    for p_ in ps: p_["z"] = {c: lg(p_["P"][c]) for c in CLASSES}
    if CTX:
        for c in CLASSES:
            b, w = CTX[c]["beta"], CTX[c]["W"]
            for i, p_ in enumerate(ps):
                nb = [max(ps[j]["P"][o] for o in CLASSES if o != c)
                      for j in range(max(0, i - w), min(len(ps), i + w + 1)) if j != i]
                p_["z"][c] += b * (max(nb) if nb else 0.0)
    # SPANIN: learned second-stage caller (models/spanin_caller.pkl, scripts/48), which beat the context rule for
    # spanins on unseen families; its score S replaces z for spanin ranking and calling. Holin and endolysin keep the
    # context rule, which the learned caller did not beat once related phages were kept out of its training folds.
    SPC = None
    if CTX and CTX["spanin"].get("caller") and (B / CTX["spanin"]["caller"]).exists():
        SPC = pickle.load(open(B / CTX["spanin"]["caller"], "rb"))
        I48 = importlib.import_module("48_integrated_caller")
        Pm = {c: np.array([q["P"][c] for q in ps]) for c in CLASSES}
        Xs = I48._genome_features(Pm, np.arange(len(ps)), [q["sequence"] for q in ps], "spanin")
        Xs = Xs[:, [I48.FEATURES.index(f) for f in SPC["features"]]]
        S = SPC["model"].predict_proba(Xs)[:, 1]
        for q, sv in zip(ps, S): q["S_spanin"] = float(sv); q["z"]["spanin"] = lg(float(sv))
    # rank within this run, per class: 1 = highest P (with context: highest z; spanin: highest S). Ranks are reported alongside the probabilities because the
    # probability alone is not safe to read as a verdict out of distribution -- the honest use of this tool is a
    # ranked shortlist per class, which is what the leave-one-genome-out numbers actually measure.
    for c in CLASSES:
        for r, i in enumerate(sorted(range(len(ps)), key=lambda i: -ps[i]["z"][c]), 1):
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
            order = sorted(range(len(ps)), key=lambda i: (-dtier[ps[i]["id"]][c], -ps[i]["z"][c]))
            for r, i in enumerate(order, 1): ps[i].setdefault("ev_rank", {})[c] = r

    # the CALL: per class, the top protein -- by domain evidence then context score with --domains, else by context
    # score. CONFIDENT if its z clears the class's measured cut-off (models/context_params.json) or, with --domains, it
    # carries a catalytic/family-defining lysis domain; otherwise CANDIDATE. One gene per class per genome; a spanin
    # pair's partner is usually ranked second.
    calls = {}
    for p_ in ps: p_["lysis_call"] = ""
    if positional:
        for c in CLASSES:
            key = (lambda q: q["ev_rank"][c]) if a.domains else (lambda q: q["rank"][c])
            top = min(ps, key=key)
            dom_ok = a.domains and dtier[top["id"]][c] >= 2
            if c == "spanin" and SPC:
                score_ok = top["S_spanin"] >= SPC["call_S"]
            else:
                score_ok = bool(CTX) and top["z"][c] >= CTX[c]["call_z"]
            tier = "confident" if score_ok or dom_ok else "candidate"
            calls[c] = (top, tier, "domain" if dom_ok else "context score")
            top["lysis_call"] = (top["lysis_call"] + "," if top["lysis_call"] else "") + f"{c}:{tier}"

    cols = ["id", "gene", "product", "start", "stop", "strand", "length",
            "P_holin", "P_endolysin", "P_spanin", "rank_holin", "rank_endolysin", "rank_spanin",
            "call", "high_conf", "lysis_call", "cassette"] + (["pfam_lysis", "dom_tier_holin", "dom_tier_endolysin", "dom_tier_spanin",
                                    "ev_rank_holin", "ev_rank_endolysin", "ev_rank_spanin"] if a.domains else [])
    lines = ["\t".join(cols)]
    for p in ps:
        row = [p["id"], p.get("gene", ""), (p.get("product") or "").replace("\t", " "),
               p["start"], p["stop"], p["strand"], len(p["sequence"]),
               f"{p['P']['holin']:.4f}", f"{p['P']['endolysin']:.4f}", f"{p['P']['spanin']:.4f}",
               p["rank"]["holin"], p["rank"]["endolysin"], p["rank"]["spanin"], p["call"], p["high_conf"],
               p["lysis_call"], p["cassette"]]
        if a.domains:
            row.append(dom.get(p["id"], ""))
            row += [dtier[p["id"]][c] for c in CLASSES] + [p["ev_rank"][c] for c in CLASSES]
        lines.append("\t".join(str(x) for x in row))
    (Path(a.out).write_text("\n".join(lines) + "\n") if a.out else print("\n".join(lines)))

    called = {c: sum(1 for p in ps if p["call"] == c) for c in CLASSES}
    print(f"# called at >={a.threshold}: " + ", ".join(f"{c} {called[c]}" for c in CLASSES) +
          f"; cassettes {len(cass)}" + ("" if positional else " (n/a for protein FASTA)"), file=sys.stderr)
    if calls:
        print("#\n# LYSIS GENE CALLS (top context-ranked protein per class; confident = clears the measured cut-off)",
              file=sys.stderr)
        for c in CLASSES:
            q, tier, why = calls[c]
            print(f"#   {c:<10} {tier.upper():<10} {(q.get('gene') or q['id'])[:24]:<24} {q['start']}..{q['stop']}{q['strand']}"
                  f"  {len(q['sequence'])} aa  P={q['P'][c]:.4f}  "
                  + (f"S={q['S_spanin']:.3f}" if c == "spanin" and SPC else f"z={q['z'][c]:.2f}")
                  + (f"  [{why}: {dom.get(q['id'])}]" if why == "domain" else ""), file=sys.stderr)
    hc = {c: sum(1 for p in ps if c in p["high_conf"].split(",")) for c in CLASSES}
    print("# high confidence (per-class cut-offs " + ", ".join(f"{c} >={HC[c]:g}" for c in CLASSES) + "): "
          + ", ".join(f"{c} {hc[c]}" for c in CLASSES), file=sys.stderr)
    # ranked shortlist per class, printed whatever the threshold
    for c in CLASSES:
        key = (lambda p: (-dtier[p["id"]][c], -p["z"][c])) if a.domains else (lambda p: -p["z"][c])
        top = sorted(ps, key=key)[:a.top]
        how = ("by domain evidence, then " if a.domains else "by ") + ("context-adjusted score" if CTX else f"P({c})")
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
