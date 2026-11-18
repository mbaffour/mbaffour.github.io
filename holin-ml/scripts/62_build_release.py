"""Build release/: every individual prediction, score and decision of the project as flat, documented tables, so any
number in the manuscript can be traced to the rows behind it and the work can be shared or picked up later.

Tables (release/README.md is the data dictionary):
  genomes.csv               every genome in every benchmark and scan: organism, size, relatedness clusters
  prediction_versions.csv   each set of frozen predictions: commit, date, model files used (SHA-256 at that commit)
  scan_calls.csv            per scan x prediction version x genome x class: the call, its rank and score, the
                            top 5, the annotated gene(s), agreement, and the annotated gene's identity to training
  scan_proteins.csv.gz      every protein of every scanned genome (shipped prediction version): scores, ranks, calls,
                            and the product name of the annotated CDS it matches
  call_proteins.csv / .faa  every called lysis protein (+ second holin, spanin partner) with sequence and membrane
                            topology from our predictor, DeepTMHMM and SignalP 6.0, and the derived classes
  topology_reference.csv    the Swiss-Prot phage lysis proteins run through all three topology tools
  benchmark_genes.csv       each curated benchmark gene (CPT, experimental, reviewed) under each removal protocol:
                            rank, score; and its PHROGs best hit and Pfam lysis domains
  benchmark_genomes.csv     per benchmark x class x method x genome: call / top 5 / coverage (all methods)
  family_features.csv       per genome of the nine group scans: cassette, domains, topology consensus
  candidates_*.csv          predictions for follow-up (unannotated o-spanins, holins missing from annotations, ...)
  decisions.csv             every development decision: rule, result, decision, report, commit
  commit_log.csv            the project's full git history (each run and result is a commit)
  lysis_release.xlsx        all of the above except scan_proteins, one sheet each
Usage: python3 scripts/62_build_release.py [--phrogs DIR]   (run scripts/62a collect, ours, external first)
"""
import argparse, csv, glob, gzip, hashlib, importlib, json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
OUT = B / "release"; W = B / "reports/release_work"
S5 = importlib.import_module("05_scan_genome")
SC = importlib.import_module("52c_score_blind")
RP = importlib.import_module("62a_release_proteins")
SUBYEAR = importlib.import_module("60_baselines").submitted_year
CLASSES = ("holin", "endolysin", "spanin")
GROUPS = RP.GROUPS
SETS = {"blind": "Blind set 1: GenBank Caudoviricetes deposited from June 2026, max 15 per host genus",
        "blind2": "Blind set 2: a second fresh sample, used to test the endolysin virion fix",
        "n4": "N4-like (Schitoviridae)", "lambda": "Lambdoid / P22-like (mixed group)", "t7": "T7-like (Autographiviridae)",
        "p2": "P2-like (Peduoviridae)", "drexler": "Drexlerviridae", "t5": "T5-like (Demerecviridae)",
        "herelle": "Herelleviridae (Gram-positive hosts)", "t4": "T4-like (Straboviridae)", "jumbo": "Jumbo phages (> 200 kb)",
        "final": "Pre-registered final test set (reports/final/FROZEN.md)",
        "cpt": "CPT hand-curated benchmark", "validated": "Experimental benchmark (UniProt protein-level evidence)",
        "reviewed": "Swiss-Prot reviewed lysis-protein benchmark"}
VERSIONS = [  # set, prediction dir, description, endolysin model file used, shipped in the reports?
    ("blind", "pred", "evidence-only endolysin model, before the virion fix", "endolysin_model.pkl", False),
    ("blind", "pred_new", "virion-fixed endolysin model", "endolysin_model.pkl", True),
    ("blind", "pred_new_d05", "virion-fixed + distance decay 0.5 (tested, not adopted)", "endolysin_model.pkl", False),
    ("blind2", "pred_old", "evidence-only endolysin model (retired)", "endolysin_model_v1_evidence_retired.pkl", False),
    ("blind2", "pred_new", "virion-fixed endolysin model", "endolysin_model.pkl", True),
    ("blind2", "pred_new_d05", "virion-fixed + distance decay 0.5 (tested, not adopted)", "endolysin_model.pkl", False),
    *[(s, "pred", "virion-fixed endolysin; spanin model before the label audit", "endolysin_model.pkl", True) for s in GROUPS],
    ("final", "pred", "frozen pipeline (FROZEN.md)", "endolysin_model.pkl", True),
    ("final", "pred_old_endolysin", "frozen pipeline with the retired endolysin model (H1 comparator)",
     "endolysin_model_v1_evidence_retired.pkl", False),
]


def git(*a):
    return subprocess.run(["git", *a], cwd=B, capture_output=True, text=True).stdout


def write_csv(name, rows, cols=None):
    cols = cols or list(dict.fromkeys(k for r in rows for k in r))
    p = OUT / name; op = gzip.open if name.endswith(".gz") else open
    with op(p, "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n", extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    print(f"  {name}: {len(rows)} rows", flush=True)
    TABLES[name] = (rows, cols)


TABLES = {}


# ---------------------------------------------------------------- genomes
def gb_meta(p):
    from Bio import SeqIO
    rec = next(SeqIO.parse(p, "genbank"))
    src = next((f for f in rec.features if f.type == "source"), None)
    q = src.qualifiers if src else {}
    org = rec.annotations.get("organism", "")
    m = re.match(r"^([A-Z][a-z]+)\s+(phage|virus|bacteriophage)", org)
    return {"organism": org, "description": rec.description, "length_bp": len(rec.seq),
            "host_genus": m.group(1) if m else "", "lab_host": (q.get("lab_host") or q.get("host") or [""])[0],
            "genbank_date": rec.annotations.get("date", ""), "first_submitted_year": SUBYEAR(p),
            "taxonomy": "; ".join(rec.annotations.get("taxonomy", [])[-4:]),
            "n_annotated_cds": sum(f.type == "CDS" for f in rec.features)}


def genome_files(s):
    if s in ("cpt", "validated", "reviewed"):
        T = json.load(open(B / f"data/raw/{s}/truth.json"))
        return {Path(p).stem: p for p in sorted(glob.glob(str(B / f"data/raw/{s}/genomes/*.gb"))) if Path(p).stem in T}
    return {a: B / f"data/raw/{s}/sealed/{a}.gb" for a in json.load(open(B / f"data/raw/{s}/selection.json"))["accessions"]
            if (B / f"data/raw/{s}/sealed/{a}.gb").exists()}


def genomes_table():
    rows = []
    for s in SETS:
        cl = json.load(open(B / f"reports/clusters/{s}.json")) if (B / f"reports/clusters/{s}.json").exists() else {}
        for g, p in genome_files(s).items():
            r = {"set": s, "genome": g, **gb_meta(p)}
            c = cl.get(g, {})
            r["ani95_cluster"] = f"{s}:ani{c['ani95']}" if "ani95" in c else ""
            r["gene_content_cluster"] = f"{s}:g{c['gene']}" if "gene" in c else ""
            if s in RP.CANON and (B / f"reports/{s}/{RP.CANON[s]}/{g}.tsv").exists():
                R = RP.read_pred(s, RP.CANON[s], g)
                r["n_genes_called_denovo"] = len(R); r["n_nested_lipoprotein_orfs"] = sum("nested" in x["id"] for x in R)
            rows.append(r)
    write_csv("genomes.csv", rows, ["set", "genome", "organism", "host_genus", "lab_host", "length_bp", "n_annotated_cds",
                                    "n_genes_called_denovo", "n_nested_lipoprotein_orfs", "ani95_cluster",
                                    "gene_content_cluster", "taxonomy", "first_submitted_year", "genbank_date", "description"])


# ---------------------------------------------------------------- prediction versions
def first_commit(path):
    L = git("log", "--diff-filter=A", "--format=%h %ad", "--date=short", "--", str(path)).split("\n")
    L = [l for l in L if l.strip()]
    return L[-1].split() if L else ["", ""]


def blob_sha(commit, f):
    rel = (B / "models" / f).relative_to(Path(git("rev-parse", "--show-toplevel").strip()))
    data = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=B, capture_output=True).stdout
    return hashlib.sha256(data).hexdigest() if data else ""


def versions_table():
    rows = []
    for s, pred, desc, endo, shipped in VERSIONS:
        commit, date = first_commit(B / f"reports/{s}/{pred}")
        rows.append({"set": s, "prediction_version": pred, "description": desc, "used_in_reports": shipped,
                     "frozen_in_commit": commit, "date": date,
                     "n_genomes": len(glob.glob(str(B / f"reports/{s}/{pred}/*.tsv"))),
                     "holin_model_sha256": blob_sha(commit, "holin_model_curated.pkl"),
                     "endolysin_model": endo, "endolysin_model_sha256": blob_sha(commit, endo),
                     "spanin_model_sha256": blob_sha(commit, "spanin_model.pkl"),
                     "spanin_caller_sha256": blob_sha(commit, "spanin_caller.pkl"),
                     "context_params_sha256": blob_sha(commit, "context_params.json")})
    write_csv("prediction_versions.csv", rows)


# ---------------------------------------------------------------- scans: calls and proteins
def annotation_map(s, acc):
    """{de novo id: annotated CDS or None}, matched as in scripts/52c (strand + stop, else sequence)"""
    cache = W / "annmap" / s / f"{acc}.json"
    if cache.exists(): return json.loads(cache.read_text())
    ann = [x for x in S5.annotated_proteins(B / f"data/raw/{s}/sealed/{acc}.gb") if x.get("sequence")]
    prot = RP.proteins(s, acc)
    R = RP.read_pred(s, RP.CANON.get(s, "pred"), acc)
    by_stop = {(a["strand"], a["stop"] if a["strand"] == "+" else a["start"]): a for a in ann}
    out = {}
    for r in R:
        seq = prot.get(r["id"], "")
        a = by_stop.get((r["strand"], int(r["stop"]) if r["strand"] == "+" else int(r["start"])))
        if a is None and seq:
            a = next((x for x in ann if x["sequence"] == seq or (len(x["sequence"]) >= 20 and (
                x["sequence"] in seq or seq in x["sequence"]))), None)
        out[r["id"]] = None if a is None else {k: a[k] for k in ("id", "product", "start", "stop", "strand", "sequence")}
    lys = {c: [{k: a[k] for k in ("id", "product", "start", "stop", "strand", "sequence")} for a in ann
               if c in SC.labels(a.get("product") or "")] for c in CLASSES}
    res = {"map": out, "lysis": lys}
    cache.parent.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(res))
    return res


def novelty(seqs_by_class):
    f = W / "novelty.json"; nov = json.load(open(f)) if f.exists() else {c: {} for c in CLASSES}
    from multiprocessing import Pool
    TP = SC.training_positives()
    for c in CLASSES:
        todo = sorted(set(seqs_by_class[c]) - set(nov[c]))
        if not todo: continue
        print(f"  identity to training: {len(todo)} {c} sequences", flush=True)
        with Pool(4, initializer=SC._init, initargs=(TP[c],)) as pool: ids = pool.map(SC._best, todo, chunksize=4)
        nov[c].update({q: round(float(i), 3) for q, i in zip(todo, ids)}); f.write_text(json.dumps(nov))
    return nov


def stratum(i):
    return "" if i is None else "near-copy (>=95%)" if i >= 0.95 else "known family (30-95%)" if i >= 0.30 else "new family (<30%)"


def scans():
    scan_sets = [s for s in SETS if s in RP.CANON]
    A = {}
    for s in scan_sets:
        for acc in json.load(open(B / f"data/raw/{s}/selection.json"))["accessions"]:
            if (B / f"reports/{s}/{RP.CANON[s]}/{acc}.tsv").exists(): A[(s, acc)] = annotation_map(s, acc)
        print(f"  annotation matched: {s}", flush=True)
    nov = novelty({c: [a["sequence"] for m in A.values() for a in m["lysis"][c]] for c in CLASSES})
    rows, check = [], defaultdict(list)
    for s, pred, desc, _, shipped in VERSIONS:
        for (s2, acc), M in A.items():
            if s2 != s or not (B / f"reports/{s}/{pred}/{acc}.tsv").exists(): continue
            R = RP.read_pred(s, pred, acc); C = RP.calls_of(R); amap = M["map"]
            for c in CLASSES:
                annc = M["lysis"][c]
                hits = [i for i, r in enumerate(R) if amap.get(r["id"]) and c in SC.labels(amap[r["id"]]["product"] or "")]
                best = min((int(R[i][f"rank_{c}"]) for i in hits), default=None)
                top5 = sorted(R, key=lambda r: int(r[f"rank_{c}"]))[:5]
                row = {"set": s, "prediction_version": pred, "genome": acc, "class": c,
                       "top5_ids": ";".join(r["id"] for r in top5),
                       "top5_P": ";".join(r[f"P_{c}"] for r in top5),
                       "genome_annotates_class": bool(annc), "n_annotated_genes": len(annc),
                       "annotated_genes": " | ".join(f"{a['id']}:{a['product']}:{a['start']}..{a['stop']}{a['strand']}" for a in annc),
                       "annotated_best_rank": best, "annotated_found_by_gene_finder": bool(hits) if annc else None}
                if c in C:
                    i, tier = C[c]; r = R[i]; a = amap.get(r["id"])
                    prod = None if a is None else (a["product"] or "")
                    lab = SC.labels(prod or "")
                    verdict = ("agrees" if c in lab else "unannotated gene (not in the annotation)" if a is None else
                               "annotated hypothetical/unknown" if SC.UNKNOWN.search(prod) else
                               "annotated as another lysis class" if lab else "annotated with another function")
                    s0, e0 = int(r["start"]), int(r["stop"])
                    row.update({"call_id": r["id"], "call_tier": tier, "call_start": s0, "call_stop": e0,
                                "call_strand": r["strand"], "call_length_aa": r["length"], "call_P": r[f"P_{c}"],
                                "call_rank_by_P": r[f"rank_{c}"], "call_annotated_as": prod if a else "(not in annotation)",
                                "call_annotated_id": a["id"] if a else "", "call_verdict": verdict,
                                "call_is_annotated_gene": (i in hits) if annc else None,
                                "call_is_annotated_gene_or_overlapping_partner": (i in hits or any(
                                    min(e0, int(R[j]["stop"])) - max(s0, int(R[j]["start"])) > 0 for j in hits)) if annc else None})
                elif annc:
                    row.update({"call_tier": "no call", "call_is_annotated_gene": False,
                                "call_is_annotated_gene_or_overlapping_partner": False})
                if annc:
                    idn = max(nov[c].get(a["sequence"], 0.0) for a in annc)
                    row["annotated_max_identity_to_training"] = idn; row["annotated_novelty"] = stratum(idn)
                    row["annotated_in_top5"] = bool(best and best <= 5)
                    check[(s, pred, c)].append((row["call_is_annotated_gene"], row["annotated_in_top5"]))
                rows.append(row)
    cols = ["set", "prediction_version", "genome", "class", "call_id", "call_tier", "call_start", "call_stop", "call_strand",
            "call_length_aa", "call_P", "call_rank_by_P", "call_annotated_as", "call_annotated_id", "call_verdict",
            "genome_annotates_class", "n_annotated_genes", "annotated_genes", "annotated_best_rank", "annotated_in_top5",
            "annotated_found_by_gene_finder", "call_is_annotated_gene", "call_is_annotated_gene_or_overlapping_partner",
            "annotated_max_identity_to_training", "annotated_novelty", "top5_ids", "top5_P"]
    write_csv("scan_calls.csv", rows, cols)
    # check against the scores reported at the time (scripts/52c)
    bad = []
    for (s, pred, c), v in check.items():
        f = B / f"reports/{s}/" / ("score.json" if pred == "pred" else f"score_{pred}.json")
        if not f.exists(): continue
        ref = json.load(open(f))["classes"][c]
        mine = (round(np.mean([x[0] for x in v]), 3), round(np.mean([x[1] for x in v]), 3))
        if mine != (ref["call_is_annotated_gene"], ref["annotated_in_top5"]): bad.append((s, pred, c, mine, ref["call_is_annotated_gene"], ref["annotated_in_top5"]))
    print("  check vs reported scores:", "all match" if not bad else bad, flush=True)
    CHECKS["scan_calls_match_reported_scores"] = not bad; CHECKS["scan_calls_mismatches"] = bad
    # every protein, shipped version
    prows = []
    for (s, acc), M in A.items():
        for r in RP.read_pred(s, RP.CANON[s], acc):
            a = M["map"].get(r["id"])
            prows.append({"set": s, "genome": acc, **{k: r[k] for k in r if k not in ("product", "gene")},
                          "annotated_id": a["id"] if a else "", "annotated_product": a["product"] if a else ""})
    write_csv("scan_proteins.csv.gz", prows)


CHECKS = {}


# ---------------------------------------------------------------- call proteins with topology
def read_external():
    M = importlib.import_module("56b_compare_predictors")
    DT, SP = {}, {}
    for d in (B / "reports/external", B / "reports/external/extra", B / "reports/external/extra/rest"):
        M.OUT = d; DT.update(M.read_deeptmhmm()); SP.update(M.read_signalp())
    return DT, SP


def hclass(n):
    if n is None or n == "": return ""
    n = int(n); return {1: "III (1 helix)", 2: "II (2 helices)", 3: "I (3 helices)"}.get(n, "no helix" if n == 0 else "4+ helices")


def spanin_member(seq, helices, signalp):
    if signalp == "LIPO":
        after = [x for x in helices if x[0] > 35]
        if not after: return "o-spanin"
        return "u-spanin" if any(a > len(seq) * 0.5 for a, b in after) else "other"
    if helices and helices[0][0] <= 40: return "i-spanin"
    return "other"


def call_proteins():
    P = json.load(open(W / "call_proteins.json")); OT = json.load(open(W / "ours_topology.json")); DT, SP = read_external()
    rows, fa = [], {}
    for p in P:
        k = p["sid"]; o = OT.get(k, {}); d = DT.get(k, {}); sp = SP.get(k, {})
        r = {**{x: p[x] for x in ("set", "pred", "genome", "role", "tier", "id", "start", "stop", "strand")},
             "length_aa": len(p["sequence"]), "sequence_id": k,
             "ours_helices": o.get("n"), "ours_helix_spans": ";".join(f"{a}-{b}" for a, b in o.get("helices", [])),
             "ours_n_terminus": o.get("n_terminus"), "ours_sar_rule": o.get("sar_rule"),
             "deeptmhmm_type": d.get("type"), "deeptmhmm_helices": d.get("n"), "deeptmhmm_n_terminus": d.get("nterm"),
             "deeptmhmm_topology": d.get("topology"), "signalp": sp.get("prediction"),
             "signalp_probs": ";".join(str(x) for x in sp.get("probs", [])), "sequence": p["sequence"]}
        if p["role"] in ("holin", "holin2"):
            r["holin_class_deeptmhmm"] = hclass(d.get("n")); r["holin_class_ours"] = hclass(o.get("n"))
            r["holin_class_agree"] = (r["holin_class_deeptmhmm"] == r["holin_class_ours"]) if d and o else None
        if p["role"] == "endolysin" and d and o:
            ours, deep = o["sar_rule"] == "SAR", d["type"] in ("SP", "SP+TM")
            r["endolysin_SAR_consensus"] = ("SAR (both)" if ours and deep else "canonical (both)" if not ours and not deep
                                            else "SAR, ours only" if ours else "SAR, DeepTMHMM only")
        if p["role"] in ("spanin", "spanin_partner") and sp and o:
            r["spanin_member_type"] = spanin_member(p["sequence"], o["helices"], sp["prediction"])
        rows.append(r); fa[k] = p["sequence"]
    cols = list(dict.fromkeys([k for r in rows for k in r if k != "sequence"] + ["sequence"]))
    write_csv("call_proteins.csv", rows, cols)
    (OUT / "call_proteins.faa").write_text("".join(f">{k}\n{v}\n" for k, v in sorted(fa.items())))
    cov = {t: sum(r.get(t) is not None for r in rows) for t in ("ours_helices", "deeptmhmm_type", "signalp")}
    print(f"  topology coverage of {len(rows)} call proteins: {cov}", flush=True); CHECKS["topology_coverage"] = cov
    ref = [p for p in csv.DictReader(open(B / "reports/external/per_protein.csv")) if "swissprot" in p["roles"]]
    write_csv("topology_reference.csv", ref)


# ---------------------------------------------------------------- benchmarks
BENCH_FILES = {("cpt", "holin"): "cpt_holin_remote.json", ("cpt", "endolysin"): "cpt_endolysin_remote.json",
               ("cpt", "spanin"): "cpt_spanin_remote.json", ("validated", "holin"): "validated_holin_spanin.json",
               ("validated", "endolysin"): "validated_endolysin_novirion.json",
               ("validated", "spanin"): "validated_spanin_audited.json", ("reviewed", "holin"): "reviewed_holin.json",
               ("reviewed", "endolysin"): "reviewed_endolysin.json", ("reviewed", "spanin"): "reviewed_spanin.json"}
PROTO = {"sequence_removal": "known_family", "family_removal": "unseen_family", "remote_removal": "remote_removed"}


def ranks(scores, truth):
    sc = np.asarray(scores); assigned = np.isfinite(sc)
    order = [i for i in np.argsort(-sc) if assigned[i]]
    rank = {i: r for r, i in enumerate(order, 1)}
    return order, rank


def benchmarks(pdir):
    B60 = importlib.import_module("60_baselines"); D = B60.D
    gene_rows, gen_rows = [], []
    for name in ("cpt", "validated", "reviewed"):
        cf = W / f"bench_{name}.json"
        G = B60.load_benchmark(name)
        if cf.exists():
            PB = {tuple(map(int, k.split("|"))): v for k, v in json.load(open(cf))["phrogs"].items()}
            PF = {tuple(map(int, k.split("|"))): v for k, v in json.load(open(cf))["pfam"].items()}
        else:
            PB = B60.phrog_best(G, pdir, extra={(gi, i) for gi, g in enumerate(G) for c in CLASSES for i in g["truth"][c]})
            allp = {f"{gi}|{i}": s for gi, g in enumerate(G) for i, s in enumerate(g["seqs"])}
            hits = D.scan(allp, *D.lysis_hmms(None))
            PF = {tuple(map(int, k.split("|"))): [(h["pfam"], h["name"], h["class"], h["grade"], h["ievalue"]) for h in hs]
                  for k, hs in hits.items() if hs}
            cf.write_text(json.dumps({"phrogs": {f"{a}|{b}": v for (a, b), v in PB.items()},
                                      "pfam": {f"{a}|{b}": v for (a, b), v in PF.items()}}))
        T = json.load(open(B / f"data/raw/{name}/truth.json"))
        ann = {}
        for g in G:
            gb = genome_files(name)[g["genome"]]
            ann[g["genome"]] = [x for x in S5.annotated_proteins(gb) if x.get("sequence") and 20 <= len(x["sequence"]) <= 2000]
        for c in CLASSES:
            R = json.load(open(B / "reports" / BENCH_FILES[(name, c)]))["classes"][c]
            TR = {p: {(t["genome"], t["id"]): t for t in R[p]["truth_ranks"]} for p in PROTO if p in R}
            # PHROGs and Pfam scores per protein, ranked within the genome as in scripts/60
            for gi, g in enumerate(G):
                tr = g["truth"][c]
                if not tr: continue
                n = len(g["seqs"])
                ph = np.full(n, -np.inf); pf = np.full(n, -np.inf)
                for i in range(n):
                    b = PB.get((gi, i))
                    if b and B60.phrog_class(b[3]) == c: ph[i] = b[1]
                    hs = [h for h in PF.get((gi, i), []) if h[2] == c and h[3] in ("catalytic", "family") and h[4] <= 1e-5]
                    if hs: pf[i] = -np.log10(max(min(h[4] for h in hs), 1e-300))
                meth = {}
                for lab, sc in (("PHROGs", ph), ("Pfam lysis domains", pf)):
                    order, rank = ranks(sc, tr)
                    meth[lab] = {"call": bool(order) and order[0] in tr, "top5": any(rank.get(i, 10**9) <= 5 for i in tr),
                                 "coverage": any(np.isfinite(sc[i]) for i in tr), "has_call": bool(order), "rank": rank}
                for p, lab in PROTO.items():
                    if p not in TR: continue
                    rk = [TR[p][(g["genome"], ann[g["genome"]][i]["id"])]["rank"] for i in tr if (g["genome"], ann[g["genome"]][i]["id"]) in TR[p]]
                    if rk: meth[f"ours, {lab}"] = {"call": min(rk) == 1, "top5": min(rk) <= 5, "coverage": True, "has_call": True}
                for lab in ("known_family", "unseen_family"):
                    o = meth.get(f"ours, {lab}")
                    if o: meth[f"PHROGs, else ours ({lab})"] = meth["PHROGs"] if meth["PHROGs"]["has_call"] else o
                for m, v in meth.items():
                    gen_rows.append({"benchmark": name, "class": c, "method": m, "genome": g["genome"], "call": v["call"],
                                     "top5": v["top5"], "coverage": v["coverage"]})
                for i in tr:
                    a = ann[g["genome"]][i]; r = {"benchmark": name, "genome": g["genome"], "class": c, "gene_id": a["id"],
                                                  "product": a["product"], "start": a["start"], "stop": a["stop"],
                                                  "strand": a["strand"], "length_aa": len(a["sequence"])}
                    for p, lab in PROTO.items():
                        t = TR.get(p, {}).get((g["genome"], a["id"]))
                        if t: r[f"{lab}_rank"], r[f"{lab}_score"], r["proteins_in_genome"] = t["rank"], t["score"], t["of"]
                    b = PB.get((gi, i))
                    if b: r.update({"phrogs_best": b[0], "phrogs_bitscore": b[1], "phrogs_evalue": f"{b[2]:.1e}",
                                    "phrogs_annotation": b[3], "phrogs_category": b[4]})
                    r["phrogs_rank_for_class"] = meth["PHROGs"]["rank"].get(i)
                    r["pfam_lysis_domains"] = ";".join(f"{h[0]} {h[1]} ({h[2]}, {h[3]}, {h[4]:.1e})" for h in PF.get((gi, i), []))
                    r["pfam_rank_for_class"] = meth["Pfam lysis domains"]["rank"].get(i)
                    r["sequence"] = a["sequence"]
                    gene_rows.append(r)
        print(f"  benchmark {name} done", flush=True)
    cols = ["benchmark", "genome", "class", "gene_id", "product", "start", "stop", "strand", "length_aa", "proteins_in_genome",
            "known_family_rank", "known_family_score", "unseen_family_rank", "unseen_family_score", "remote_removed_rank",
            "remote_removed_score", "phrogs_best", "phrogs_annotation", "phrogs_category", "phrogs_bitscore", "phrogs_evalue",
            "phrogs_rank_for_class", "pfam_lysis_domains", "pfam_rank_for_class", "sequence"]
    write_csv("benchmark_genes.csv", gene_rows, cols)
    write_csv("benchmark_genomes.csv", gen_rows)
    # check against the reported baseline summaries
    bad = []
    for name in ("cpt", "validated", "reviewed"):
        ref = json.load(open(B / f"reports/baselines/{name}.json"))
        for c in CLASSES:
            for m_rel, m_ref in (("PHROGs", "PHROGs (Pharokka database)"), ("Pfam lysis domains", "Pfam lysis domains"),
                                 ("ours, known_family", "ours, known family"), ("ours, unseen_family", "ours, unseen family (30%)"),
                                 ("ours, remote_removed", "ours, remote homology removed"),
                                 ("PHROGs, else ours (unseen_family)", "PHROGs, else ours, unseen family (30%)")):
                v = [r["call"] for r in gen_rows if r["benchmark"] == name and r["class"] == c and r["method"] == m_rel]
                if not v or m_ref not in ref[c]: continue
                if round(float(np.mean(v)), 3) != ref[c][m_ref]["call"][0]: bad.append((name, c, m_rel, round(float(np.mean(v)), 3), ref[c][m_ref]["call"][0]))
    print("  check vs reported baselines:", "all match" if not bad else bad, flush=True)
    CHECKS["benchmarks_match_reported_baselines"] = not bad; CHECKS["benchmark_mismatches"] = bad


# ---------------------------------------------------------------- family features, candidates, decisions, log
def families():
    L = {(r["set"], r["genome"]): r for r in csv.DictReader(open(B / "reports/distribution/lysis_by_genome.csv"))}
    T = {(r["set"], r["genome"]): r for r in csv.DictReader(open(B / "reports/distribution/topology_consensus_by_genome.csv"))}
    rows = [{**L[k], **{f"topo_{x}": v for x, v in T.get(k, {}).items() if x not in ("set", "genome")}} for k in L]
    write_csv("family_features.csv", rows)
    write_csv("family_uncertainty.csv", list(csv.DictReader(open(B / "reports/distribution/uncertainty.csv"))))


def candidates():
    u = json.load(open(B / "reports/unannotated_ospanins.json"))["candidates"]
    write_csv("candidates_unannotated_ospanins.csv", u)
    write_csv("candidates_blind_additions.csv", list(csv.DictReader(open(B / "reports/blind/candidate_additions.tsv"), delimiter="\t")))
    write_csv("candidates_second_holins.csv", json.load(open(B / "reports/dual_holin_analysis.json"))["top_second_genes"])
    # the two recurrent disagreements examined in the group scans
    sc = TABLES["scan_calls.csv"][0]
    n4 = [r for r in sc if r["set"] == "n4" and r["prediction_version"] == "pred" and r["class"] == "holin"
          and r.get("call_is_annotated_gene") is False]
    write_csv("candidates_n4_adjacent_holins.csv", n4)
    t4 = [r for r in sc if r["set"] == "t4" and r["prediction_version"] == "pred" and r["class"] == "endolysin"
          and r.get("call_is_annotated_gene") is False]
    write_csv("candidates_t4_endolysin_confusers.csv", t4)


DECISIONS = [
    # area, change, rule set before the run, result, decision, report
    ("negatives", "phage-derived hard negatives incl. Rz-like spanins", "fewer confident false positives on held-out genomes",
     "Rz-like spanin false positives removed", "adopted", "reports/hard_negatives (PROTOCOL.md)"),
    ("spanin positives", "CPT/Kongari curated spanins", "strict-protocol recall > 0", "class went from zero strict recall to working", "adopted", "MANUSCRIPT.md 3.5"),
    ("endolysin training", "early stopping off", "paired AP interval excludes 0", "+0.046 [+0.017, +0.070] (genome resampling)", "adopted", "reports/capacity_sweep.md"),
    ("endolysin training", "family expansion (+14 catalytic families)", "paired AP interval excludes 0", "-0.061 [-0.113, -0.011]", "rejected", "reports/capacity_sweep.md"),
    ("endolysin training", "larger trees / more rounds", "paired AP interval excludes 0", "lower in all four contrasts", "rejected", "reports/capacity_sweep.md"),
    ("endolysin labels", "evidence-only positives (name-labelled removed)", "non-inferior on CPT", "ranked first -0.024 unseen, +0.040 known (n.s.)", "adopted", "reports/evidence_only.md"),
    ("endolysin labels", "51 virion proteins moved to negatives", "blind set 2 improvement", "+0.061 per set (p~0.07 by cluster); pooled +0.060 [+0.020, +0.103]", "adopted", "reports/endolysin_virion_fix.md; reports/clusters/reassessment.md"),
    ("endolysin labels", "virion fix on the final set (H1, pre-registered)", "one-sided p < 0.05, cluster bootstrap", "+0.025, p = 0.37", "not confirmed (fix kept: corrects labels)", "reports/final/final_results.md"),
    ("spanin labels", "signal-corroborated TrEMBL positives", "unseen-family gain without known-family loss", "top 5 +5.6 points (p = 0.049, genome resampling)", "adopted", "reports/evidence_only.md"),
    ("spanin labels", "label audit (7 removed)", "lower 95% bound of change > -0.05", "+0.006 [0, +0.023]", "adopted", "reports/label_audit/label_audit.md"),
    ("holin labels", "label audit (50 removed)", "lower 95% bound of change > -0.05", "-0.026 [-0.093, +0.043]", "not adopted", "reports/label_audit/label_audit.md"),
    ("holin training", "family-balanced / 1/sqrt weighting, biophysics only, topology features", "paired interval excludes 0", "none better", "rejected", "reports/holin_generalisation.md"),
    ("holin training", "ESM-2 150M embedding", "paired interval excludes 0", "-0.077 top 5 unseen ([-0.225, 0] by cluster)", "rejected", "reports/holin_generalisation.md; reports/clusters/reassessment.md"),
    ("holin training", "context-mined new families (v1, v2)", "paired interval excludes 0", "-0.051 / -0.064 (n.s. by cluster)", "rejected", "reports/holin_context_mining.md"),
    ("holin training", "three ensembles; T4-aware mined ensemble", "paired interval excludes 0", "none beyond noise", "rejected (T4-aware kept as opt-in mode)", "reports/holin_generalisation.md"),
    ("features", "similarity-to-training features", "paired interval excludes 0", "halved unseen-family AP (shortcut)", "rejected", "reports/similarity_features.md"),
    ("models", "stacked specialists; self-training on the mined pool", "gold hold-out AP improves", "lower AP; contaminated candidate set", "rejected", "MANUSCRIPT.md 3.5"),
    ("calling", "genomic-context rule", "5-fold CV over CPT genomes, no measure worse", "holin ranked first +10 points", "adopted", "reports/integrated_caller.md"),
    ("calling", "learned second-stage caller", "family-grouped validation", "holin gain vanished; spanin 0.91/0.80 vs 0.83/0.73", "adopted for spanins only", "reports/integrated_caller.md"),
    ("calling", "distance decay in context", "improvement on both blind sets", "net zero", "rejected", "reports/endolysin_virion_fix.md"),
    ("gene finding", "nested lipoprotein ORF finder", "curated spanins in top 5 from DNA improve", "+0.131 [+0.065, +0.216] (cluster)", "adopted", "reports/denovo_gene_calling.md"),
    ("topology", "holin class source", "agreement with experimental topologies", "DeepTMHMM 0.95 vs ours 0.86 exact (bacteria/viruses)", "DeepTMHMM primary, ours as concordance", "reports/tm_experimental.md"),
    ("topology", "SAR endolysins", "agreement of rule and DeepTMHMM", "N4-like 39% vs 1%", "consensus only", "reports/external/comparison.md"),
    ("topology", "lipoproteins", "agreement with SignalP 6.0", "577/579 agree; SignalP finds 103 more", "SignalP LIPO", "reports/external/comparison.md"),
    ("baselines", "PHROGs pre-filter: lysis-named PHROGs as well as the lysis category (bug fix)", "release rows must reproduce reported numbers",
     "PHROGs endolysin call CPT 0.69 -> 0.78, 2022+ 0.58 -> 0.82; 'ours clearly better on endolysins' withdrawn", "corrected", "reports/baselines/baselines.md"),
    ("statistics", "resample gene-content clusters instead of genomes", "-", "effective n about half the genomes", "adopted for all intervals", "reports/clusters/reassessment.md"),
]


def decisions_and_log():
    write_csv("decisions.csv", [dict(zip(("area", "change", "decision_rule", "result", "decision", "report"), d)) for d in DECISIONS])
    L = git("log", "--format=%h\t%ad\t%s", "--date=short", "--", ".").splitlines()
    write_csv("commit_log.csv", [dict(zip(("commit", "date", "message"), l.split("\t", 2))) for l in L])


def workbook():
    import pandas as pd
    order = ["genomes.csv", "prediction_versions.csv", "scan_calls.csv", "call_proteins.csv", "topology_reference.csv",
             "benchmark_genes.csv", "benchmark_genomes.csv", "family_features.csv", "family_uncertainty.csv",
             "candidates_unannotated_ospanins.csv", "candidates_blind_additions.csv", "candidates_second_holins.csv",
             "candidates_n4_adjacent_holins.csv", "candidates_t4_endolysin_confusers.csv", "decisions.csv", "commit_log.csv"]
    with pd.ExcelWriter(OUT / "lysis_release.xlsx", engine="openpyxl") as xw:
        for n in order:
            rows, cols = TABLES[n]
            df = pd.DataFrame([{k: r.get(k) for k in cols} for r in rows], columns=cols)
            df.to_excel(xw, sheet_name=n.replace(".csv", "").replace("candidates_", "cand_")[:31], index=False)
    print("  lysis_release.xlsx written", flush=True)


DICTIONARY = {
    "genomes.csv": ("One row per genome per set (a genome can be in more than one set only if it is a benchmark genome).", {
        "set": "benchmark or scan (see the set list above)", "host_genus": "first word of the organism name when it reads '<Genus> phage ...'",
        "lab_host": "GenBank /lab_host or /host qualifier", "n_genes_called_denovo": "genes the predictor called from DNA (Pyrodigal + nested lipoprotein ORFs)",
        "ani95_cluster": "single-linkage group at >= 95% whole-genome ANI (scripts/58)",
        "gene_content_cluster": "single-linkage group at shared gene-content Jaccard >= 0.10: the resampling unit for every interval",
        "genbank_date": "date on the GenBank LOCUS line (last modification)",
        "first_submitted_year": "year of the earliest 'Submitted' reference: the time split against PHROGs uses >= 2022"}),
    "prediction_versions.csv": ("One row per frozen set of DNA-only predictions (reports/<set>/<version>/<genome>.tsv).", {
        "used_in_reports": "True for the version the scan reports and figures use", "frozen_in_commit": "commit that added the predictions, before any annotation was read",
        "*_sha256": "SHA-256 of the model file in that commit (compare with reports/final/FROZEN.md)"}),
    "scan_calls.csv": ("One row per scan x prediction version x genome x class. Scored against the genome's own GenBank annotation with the rules of scripts/52c: AGREEMENT WITH ANNOTATION, not accuracy.", {
        "call_*": "the predictor's one call for the class (empty when it made none)", "call_tier": "confident / candidate / 'no call'",
        "call_rank_by_P": "rank of the call by its raw class probability (the call is chosen after genomic-context re-ranking, so it need not be rank 1)",
        "call_annotated_as": "product name of the annotated CDS the call matches ('(not in annotation)' if none)",
        "call_verdict": "agrees / annotated hypothetical/unknown / annotated with another function / annotated as another lysis class / unannotated gene",
        "annotated_genes": "annotated CDS of the class: id:product:start..stop strand",
        "annotated_best_rank": "best rank among the annotated genes in the predictor's per-class ranking",
        "call_is_annotated_gene_or_overlapping_partner": "spanin pair-level agreement (the call overlaps an annotated gene of the class)",
        "annotated_max_identity_to_training": "max Smith-Waterman identity of the annotated gene(s) to that class's training positives",
        "annotated_novelty": "near-copy (>=95%) / known family (30-95%) / new family (<30%)"}),
    "scan_proteins.csv.gz": ("Every protein of every scanned genome, from the version used in the reports.", {
        "P_holin / P_endolysin / P_spanin": "class probabilities", "rank_*": "rank within the genome by that probability",
        "call / high_conf / lysis_call / cassette": "the predictor's own output columns (DEPLOY.md)",
        "annotated_id / annotated_product": "the annotated CDS this gene matches (same strand and stop codon, else sequence)"}),
    "call_proteins.csv": ("Every called lysis protein (any tier), the second strong holin and the spanin partner, in every scan, with sequence and membrane topology. call_proteins.faa holds the distinct sequences, named by sequence_id.", {
        "role": "holin / holin2 (next protein with P_holin >= 0.9) / endolysin / spanin / spanin_partner",
        "sequence_id": "'s' + first 15 hex of SHA-256 of the sequence: the key used by the topology runs",
        "ours_*": "our ESM-2 transmembrane predictor (scripts/55): helix count, spans, N-terminus side (positive-inside rule), SAR rule",
        "deeptmhmm_*": "DeepTMHMM (BioLib): type (TM / SP / SP+TM / GLOB / BETA), helix count, N-terminus side, per-residue topology string",
        "signalp / signalp_probs": "SignalP 6.0 (organism other, fast): prediction and class probabilities (OTHER, SP, LIPO, TAT, TATLIPO, PILIN)",
        "holin_class_*": "I/II/III = 3/2/1 helices; DeepTMHMM is primary (reports/tm_experimental.md)",
        "endolysin_SAR_consensus": "SAR only where our rule and DeepTMHMM (signal-like N terminus) agree",
        "spanin_member_type": "o-spanin (SignalP LIPO, no helix after residue 35) / u-spanin (LIPO + C-terminal-half helix) / i-spanin (helix starting in the first 40 residues) / other"}),
    "topology_reference.csv": ("Swiss-Prot phage lysis proteins through all three topology tools (the curated reference for call_proteins).", {}),
    "benchmark_genes.csv": ("One row per curated lysis gene in the CPT, experimental and reviewed benchmarks.", {
        "*_rank / *_score": "rank and score of the gene in its genome under leave-one-genome-out training with near-copies (known_family), >=30% families (unseen_family) or jackhmmer remote homologues (remote_removed) removed",
        "phrogs_*": "best PHROGs v4 hit (E <= 1e-5) as Pharokka assigns it; phrogs_rank_for_class is its rank among proteins whose best PHROG is of this class",
        "pfam_lysis_domains": "Pfam lysis-family hits: accession name (class, grade, i-Evalue)"}),
    "benchmark_genomes.csv": ("Per benchmark x class x method x genome with a curated gene: the method's top protein is the curated gene (call), a curated gene in its top 5, and whether it assigns the class to the curated gene at all (coverage). Aggregates are in reports/baselines/.", {}),
    "family_features.csv": ("Per genome of the nine group scans: cassette arrangement, endolysin domains and class, spanin architecture, holin copies, and topology consensus (topo_*).", {}),
    "family_uncertainty.csv": ("Family x feature percentages with 95% intervals resampling gene-content groups (reports/distribution/uncertainty.md).", {}),
    "candidates_unannotated_ospanins.csv": ("Nested lipoprotein ORFs in 5,113 RefSeq phage genomes that the annotation lacks; tier A = spanin model >= 0.5 and in a lysis cassette.", {}),
    "candidates_blind_additions.csv": ("Blind set 1: confident calls in genomes whose annotation has no gene of that class, with sequence evidence.", {}),
    "candidates_second_holins.csv": ("Top second holin-fold genes next to the main holin (reports/dual_holin_analysis.json).", {}),
    "candidates_n4_adjacent_holins.csv": ("N4-like genomes where the holin call is not the annotated holin (mostly the adjacent gene).", {}),
    "candidates_t4_endolysin_confusers.csv": ("T4-like genomes where the endolysin call is not the annotated endolysin: candidate hard negatives.", {}),
    "decisions.csv": ("Every development decision with the rule fixed before the run, the result, and the report.", {}),
    "commit_log.csv": ("The project's git history: every run, result and decision is a commit, so any row above can be traced to when it was made.", {}),
}


def readme():
    L = ["# Data release: every individual prediction, score and decision", "",
         "Generated by `scripts/62_build_release.py` (topology inputs by `scripts/62a_release_proteins.py`). Do not edit by",
         "hand: rebuild instead. `lysis_release.xlsx` has every table below except `scan_proteins.csv.gz`, one sheet each.",
         "", "**How to trace a number.** Manuscript figure -> report in `reports/` -> the rows here (filter by set, version,",
         "class) -> the per-genome prediction file `reports/<set>/<version>/<genome>.tsv` -> the commit that froze it",
         "(`prediction_versions.csv`, `commit_log.csv`). `build_checks.json` records that the rows reproduce the reported",
         "scores exactly.", "", "**Read with care.** Scan rows measure agreement with GenBank annotation, not accuracy; the",
         "benchmark rows (CPT, experimental, reviewed) are the independent ground truth. Related genomes are not independent:",
         "resample `gene_content_cluster`, not genomes.", "", "## Sets", "", "| set | what it is | genomes |", "|---|---|---|"]
    G = TABLES["genomes.csv"][0]
    for s, d in SETS.items(): L.append(f"| `{s}` | {d} | {sum(r['set'] == s for r in G)} |")
    L += ["", "## Tables", "", "| file | rows | columns |", "|---|---|---|"]
    for n in DICTIONARY:
        if n in TABLES: L.append(f"| [`{n}`](#{n.replace('.', '').replace('_', '')}) | {len(TABLES[n][0]):,} | {len(TABLES[n][1])} |")
    for n, (desc, cols) in DICTIONARY.items():
        if n not in TABLES: continue
        L += ["", f"### {n}", "", desc, "", "Columns: " + ", ".join(f"`{c}`" for c in TABLES[n][1])]
        if cols: L += [""] + [f"- `{k}`: {v}" for k, v in cols.items()]
    (OUT / "README.md").write_text("\n".join(L) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phrogs", default=None, help="directory with all_phrogs.h3m and phrog_annot_v4.tsv (only needed once)")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True); W.mkdir(parents=True, exist_ok=True)
    genomes_table(); versions_table(); scans(); call_proteins(); benchmarks(a.phrogs); families(); candidates()
    decisions_and_log(); workbook(); readme()
    (OUT / "build_checks.json").write_text(json.dumps(CHECKS, indent=1, default=str))


if __name__ == "__main__":
    main()
