"""The expanded leave-one-genome-out benchmark: 66 genomes, 180 annotated lysis genes, all three classes.

WHY THIS EXISTS. Every model comparison in this project has been inconclusive, and the reason is statistical, not
biological: the atlas evaluation uses 19 endolysins in 12 genomes and 15 spanins in 9, so the bootstrap intervals
span [0.52, 0.88], [0.54, 0.96], [0.59, 1.00]. A 0.65 cannot be told from a 0.73. Four architecture experiments
(family expansion, confusable negatives, per-fold decomposition, HMM routing) all ended inside the noise.

Meanwhile the 72-genome scan (scripts/37) had already collected 180 annotated lysis genes across 66 genomes --
roughly five times the ground truth the evaluation was using, sitting unused. This script evaluates on all of it.
Nothing new had to be downloaded; the measurement was simply never pointed at the data we had.

It also gives HOLIN a leave-one-genome-out evaluation it has never had at scale: 53 genes in 50 genomes, where
scripts/22 used the 16-phage atlas.

PROTOCOL, unchanged from scripts/22 and scripts/28 so the numbers stay comparable:
  family   (strict)     before scoring a genome, drop every training positive of that class in a homology cluster
                        containing a sequence >=30% identical to one of the genome's annotated genes
  sequence (realistic)  drop only >=95%-identical near-duplicates
Per class, the shipped negative recipe is used, so the numbers describe the models as deployed.

Fits are CACHED by the exact set of dropped training positives. Genomes that share a family share a model, and
under the realistic protocol most genomes drop nothing at all, so this is an exact optimisation -- not an
approximation -- and it turns ~260 fits into a few dozen.

Two strata are reported because the product-name ground truth conflates them:
  all        every annotated lysis gene
  exit_only  virion-named truths removed (T4 gp5 'baseplate hub subunit and tail lysozyme', T7 p51 'internal
             virion protein with endolysin domain', phi29 gp13). Those are ENTRY lysins; scoring them as
             endolysins penalises a pipeline for being right about them.

Usage: python3 scripts/40_logo_benchmark.py [--classes holin endolysin spanin] [--boot 2000]
                                            [--endolysin-positives data/processed/endolysin_positives_v1.json]
Writes reports/logo_benchmark.json
"""
import argparse, hashlib, glob, importlib, json, re, sys, time
from pathlib import Path
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import domains as D
CL = importlib.import_module("03_cluster")
S5 = importlib.import_module("05_scan_genome")

B = Path(__file__).resolve().parent.parent
CLASSES = ("holin", "endolysin", "spanin")
TRUTH = {
    "holin": re.compile(r"\bholin\b", re.I),
    "endolysin": re.compile(r"endolysin|lysozyme|muramidase|amidase|peptidoglycan hydrolase|murein|"
                            r"glucosaminidase|\blysin\b|transglycosylase|glycoside hydrolase", re.I),
    "spanin": re.compile(r"spanin|\bRz1?\b", re.I)}
ANTI = re.compile(r"antiholin|anti-holin", re.I)


HP = {"max_iter": 400, "learning_rate": 0.06, "max_leaf_nodes": 31, "early_stopping": "auto"}


def hgb():
    """The estimator, with capacity under explicit control.

    Note on early stopping, which is why these flags exist. The shipped models all stop well short of their
    max_iter (holin 269/400, endolysin 104/400, spanin 90/400), so max_iter was never the binding constraint.
    Worse, sklearn's early stopping holds out 10% of rows AT RANDOM, and the training sets contain thousands of
    near-duplicate homologs -- so that internal validation split is homology-contaminated and the model stops
    when it stops improving on a leaked signal, not on novel families. This project controls homology leakage in
    the clustering, the frozen gold holdout and the LOGO protocols, but never inside the estimator.
    --early-stopping False removes that confound and makes max_iter a real capacity dial.
    """
    return HistGradientBoostingClassifier(random_state=0, **HP)


def load_sets(cls, endo_pos_path, spa_pos_path):
    """(training positives, negatives) for one class, using that class's SHIPPED negative recipe."""
    base = json.load(open(B / "data/processed/dataset.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))
    negs = json.load(open(B / "data/processed/phage_negatives.json"))
    bact = [r for r in base if r["label"] == "negative"]
    gold_ids = set(json.load(open(B / "data/processed/gold_holdout.json"))["ids"])
    endo = json.load(open(B / endo_pos_path))
    spa = json.load(open(B / spa_pos_path))
    holins_all = [r for r in base if r["label"] == "holin"] + [r for r in cur if r["label"] == "holin"]
    if cls == "holin":
        pos = [r for r in base if r["label"] == "holin" and r["id"] not in gold_ids] \
              + [r for r in cur if r["label"] == "holin" and not r.get("excluded_gold_cluster")]
        neg = bact + negs                      # arm B recipe, as shipped (no cross-class)
    elif cls == "endolysin":
        pos = [r for r in endo if not r["in_gold_holdout"]]
        neg = spa + holins_all + bact + negs
    else:
        pos = [r for r in spa if not r["in_gold_holdout"]]
        neg = endo + holins_all + bact + negs
    return pos, neg


_SIM_T = None
def _sim_init(targets):
    global _SIM_T; _SIM_T = targets
def _sim_row(q):
    """identity of q to every target, under the SAME rule the protocols use to remove homologues (coverage of the
    shorter sequence >= CL.MIN_COV and Smith-Waterman score >= 80); 0 where that rule is not met."""
    return np.array([ident if (cov >= CL.MIN_COV and sc >= 80) else 0.0
                     for ident, cov, sc in CL.align_pairs(q, _SIM_T)], np.float32)


def sim_matrix(queries, targets, cache_dir, procs=4):
    """queries x targets identity matrix, cached on disk by content hash (it is the expensive part)."""
    h = hashlib.sha256(("\n".join(queries) + "\n#\n" + "\n".join(targets)).encode()).hexdigest()[:20]
    f = Path(cache_dir) / f"sim_{h}.npy"
    if f.exists(): return np.load(f)
    from multiprocessing import Pool
    with Pool(procs, initializer=_sim_init, initargs=(targets,)) as pool:
        M = np.vstack(pool.map(_sim_row, queries, chunksize=16)) if queries else np.zeros((0, len(targets)), np.float32)
    f.parent.mkdir(parents=True, exist_ok=True); np.save(f, M)
    return M


_PT = None
def _pt_init(truths):
    global _PT; _PT = truths
def _pt_row(pos_seq):
    """one training positive against every truth, in the SAME direction and with the SAME rule as CL.search
    (align_pairs(positive, truths); coverage >= CL.MIN_COV and SW score >= 80, else 0)"""
    return np.array([ident if (cov >= CL.MIN_COV and sc >= 80) else 0.0
                     for ident, cov, sc in CL.align_pairs(pos_seq, _PT)], np.float32)


def pos_truth_matrix(pos_seqs, truth_seqs, procs=4):
    """positives x truths identity, computed once per class instead of once per genome. Column j of this matrix,
    maxed over a genome's truths, equals CL.search(that genome's truths, pos_seqs, 80): align_pairs scores each target
    independently, so batching every truth into one database changes nothing but the cost."""
    from multiprocessing import Pool
    with Pool(procs, initializer=_pt_init, initargs=(truth_seqs,)) as pool:
        return np.vstack(pool.map(_pt_row, pos_seqs, chunksize=8))


def denovo_from_genbank(gb):
    """genes called from the bare DNA of a GenBank record with Pyrodigal (meta mode); no annotation is read"""
    import pyrodigal
    from Bio import SeqIO
    out = []
    for rec in SeqIO.parse(gb, "genbank"):
        for i, g in enumerate(pyrodigal.GeneFinder(meta=True).find_genes(bytes(rec.seq)), 1):
            out.append({"id": f"{rec.id}_orf{i:04d}", "product": "", "start": g.begin, "stop": g.end,
                        "strand": "+" if g.strand == 1 else "-", "sequence": g.translate().rstrip("*")})
    return out


def seq_place(target, ps):
    """index of the called protein carrying the target sequence: identical, or one contains the other (a different
    start codon gives the same C-terminal sequence), else >= 90% identity over the shorter end-aligned stretch"""
    if not target: return None
    for i, x in enumerate(ps):
        q = x["sequence"]
        if q == target or ((q.endswith(target) or target.endswith(q)) and min(len(q), len(target)) >= 0.7 * max(len(q), len(target))):
            return i
    best = (None, 0.0)
    for i, x in enumerate(ps):
        q = x["sequence"]; n = min(len(q), len(target))
        if n < 0.7 * max(len(q), len(target)): continue
        m = sum(a == b for a, b in zip(q[-n:], target[-n:])) / n
        if m > best[1]: best = (i, m)
    return best[0] if best[1] >= 0.9 else None


def pos_weights(cl, mode):
    """sample weights for the kept positives: by homology family, normalised to sum to the number of positives"""
    if mode == "none": return np.ones(len(cl))
    _, inv, cnt = np.unique(cl, return_inverse=True, return_counts=True)
    w = 1.0 / (cnt[inv] if mode == "cluster" else np.sqrt(cnt[inv]))
    return w * (len(cl) / w.sum())


def weighted_rows(Xp_keep, cl_keep, mode, seed=0):
    """Family weighting by RESAMPLING the kept positives (with replacement, probability proportional to pos_weights),
    the same number of rows as before. Equivalent to sample weights in expectation, and fast: passing sample_weight
    makes this scikit-learn compute weighted quantiles for every feature before each fit, which was ~10x slower."""
    if mode == "none": return Xp_keep
    w = pos_weights(cl_keep, mode); rng = np.random.default_rng(seed)
    return Xp_keep[rng.choice(len(w), size=len(w), replace=True, p=w / w.sum())]


def stratified_subsample(recs, n, seed, field):
    """Exactly n records, each stratum of `field` kept in proportion (largest-remainder rounding).
    Deterministic: records are ordered by id inside each stratum before the seeded draw."""
    if n >= len(recs): return list(recs), {}
    strata = {}
    for r in recs: strata.setdefault(str(r.get(field)), []).append(r)
    total = len(recs)
    quota = {k: n * len(v) / total for k, v in strata.items()}
    take = {k: int(q) for k, q in quota.items()}
    short = n - sum(take.values())
    for k in sorted(quota, key=lambda k: (-(quota[k] - take[k]), k))[:short]: take[k] += 1
    rng = np.random.default_rng(seed); out = []
    for k in sorted(strata):
        v = sorted(strata[k], key=lambda r: r["id"])
        ix = rng.choice(len(v), size=take[k], replace=False)
        out += [v[i] for i in sorted(ix)]
    return out, {k: [len(strata[k]), take[k]] for k in sorted(strata)}


def ck_dir(root, hp, epos, spos, extra=None):
    """One checkpoint directory per (estimator, dataset) combination, so configs cannot collide.
    `extra` (e.g. a positive subsample) joins the key only when present, so every directory written
    before it existed keeps its hash and stays readable."""
    key = {"hp": hp, "endolysin": epos, "spanin": spos}
    if extra: key["extra"] = extra
    sig = json.dumps(key, sort_keys=True)
    d = Path(root) / hashlib.sha256(sig.encode()).hexdigest()[:16]
    d.mkdir(parents=True, exist_ok=True)
    (d / "config.json").write_text(sig)
    return d


def ck_load(d, cls, mode, genome, n):
    """Per-protein scores for one (class, protocol, genome), or None if not computed yet."""
    f = d / f"{cls}__{mode}__{genome}.json"
    if not f.exists(): return None
    try:
        s = json.loads(f.read_text())
    except Exception:
        return None
    return np.array(s, float) if isinstance(s, list) and len(s) == n else None


def ck_save(d, cls, mode, genome, s):
    f = d / f"{cls}__{mode}__{genome}.json"
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps([float(x) for x in s]))   # full precision: 6dp moved bootstrap
                                                        # CI bounds by ~4e-4 on a resumed run
    tmp.replace(f)                      # atomic, so a kill mid-write cannot leave a short file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", nargs="+", default=list(CLASSES), choices=list(CLASSES))
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--genbanks", nargs="+",
                    default=["data/raw/panel/*.gb", "data/raw/genomes/*.gb"])
    ap.add_argument("--endolysin-positives", default="data/processed/endolysin_positives.json")
    ap.add_argument("--spanin-positives", default="data/processed/spanin_positives.json")
    ap.add_argument("--out", default="reports/logo_benchmark.json")
    ap.add_argument("--pos-subsample", type=int, default=0,
                    help="cut the evaluated class's TRAINING positives (after the gold holdout) to exactly "
                         "this many, stratified by --pos-subsample-strata; 0 = off")
    ap.add_argument("--pos-subsample-seed", type=int, default=0)
    ap.add_argument("--pos-subsample-strata", default="source")
    ap.add_argument("--truth-file",
                    help="JSON {genome_stem: {class: [protein ids]}}: take truth from this file (e.g. experimentally "
                         "validated genes placed by sequence, scripts/43) instead of from GenBank product names. Only "
                         "genomes in the file are scanned.")
    ap.add_argument("--de-novo", action="store_true",
                    help="ignore the GenBank annotation entirely: call genes from the bare DNA with Pyrodigal, score "
                         "those proteins, and place --truth-file genes on them by amino-acid SEQUENCE (needs --truth-file)."
                         " This is how a newly sequenced, unannotated phage is handled.")
    ap.add_argument("--score-all", action="store_true",
                    help="also write checkpoint scores for genomes with NO curated gene of the class (used as context "
                         "inputs by the integrated caller). For those genomes every training positive >= 95%% identical "
                         "to ANY of the genome's proteins is removed first, so an unannotated gene of the class cannot be "
                         "scored by a model that trained on it. They never enter this class's metrics.")
    ap.add_argument("--pos-weight", default="none", choices=["none", "cluster", "sqrt"],
                    help="weight training positives by homology family so the model cannot lean on a few large ones: "
                         "cluster = each family carries equal total weight (1/size); sqrt = 1/sqrt(size). Total positive "
                         "weight is kept equal to the number of positives.")
    ap.add_argument("--features", default="both", choices=["both", "hand", "esm", "hand+topo", "both+topo"],
                    help="hand = only the 36 biophysical sequence features; esm = only the ESM-2 embedding; +topo adds the "
                         "27 membrane-topology descriptors of features.topology_features")
    ap.add_argument("--sim-features", action="store_true",
                    help="append one feature: max identity to the class's KEPT training positives (self and exact "
                         "duplicates masked for training rows; for a scored genome, only positives surviving that "
                         "genome's homology removal count). Also reports a nearest-neighbour baseline that ranks "
                         "by that identity alone.")
    ap.add_argument("--checkpoint", default=".fitckpt",
                    help="directory for per-genome score checkpoints; a run resumes from these, so a "
                         "container restart or a command timeout costs only the genome in flight")
    ap.add_argument("--max-iter", type=int, default=400)
    ap.add_argument("--max-leaf-nodes", type=int, default=31)
    ap.add_argument("--learning-rate", type=float, default=0.06)
    ap.add_argument("--early-stopping", default="auto",
                    help="'auto' (sklearn default, homology-contaminated 10%% random split) or 'False'")
    a = ap.parse_args()

    HP.update({"max_iter": a.max_iter, "max_leaf_nodes": a.max_leaf_nodes,
               "learning_rate": a.learning_rate,
               "early_stopping": (False if str(a.early_stopping).lower() in ("false", "0", "no")
                                  else a.early_stopping)})
    print(f"estimator: {HP}", flush=True)
    SUB = ({"n": a.pos_subsample, "seed": a.pos_subsample_seed, "strata": a.pos_subsample_strata}
           if a.pos_subsample else None)
    EXTRA = dict(SUB or {})
    if a.pos_weight != "none": EXTRA["pos_weight"] = a.pos_weight + "_resample"   # see weighted_rows()
    if a.features != "both": EXTRA["features"] = a.features
    if a.sim_features: EXTRA["sim"] = "target_class_max_identity_v1"
    CK = ck_dir(B / a.checkpoint if not Path(a.checkpoint).is_absolute() else a.checkpoint,
                dict(HP), a.endolysin_positives, a.spanin_positives, EXTRA or None)
    print(f"checkpoints: {CK}", flush=True)
    paths = sorted({p for g in a.genbanks for p in glob.glob(str(B / g))})
    TF = json.load(open(B / a.truth_file)) if a.truth_file else None
    if TF is not None: paths = [p for p in paths if Path(p).stem in TF]
    esm = F.ESM(B / "models/esm_cache")
    FSEL = {"both": slice(0, 516), "hand": slice(0, 36), "esm": slice(36, 516),
            "hand+topo": slice(0, 36), "both+topo": slice(0, 516)}[a.features]
    TOPO = a.features.endswith("+topo")
    def feats(ss):
        if not ss: return np.zeros((0, (FSEL.stop - FSEL.start) + (len(F.TOPO_NAMES) if TOPO else 0)))
        base = np.hstack([np.array([F.handcrafted(s) for s in ss]), esm.embed(ss)])[:, FSEL]
        return np.hstack([base, np.array([F.topology_features(s) for s in ss], float)]) if TOPO else base

    # ---- genomes and ground truth ----
    genomes = []; _seen_dna = {}
    for p in paths:
        # one record per genome: the same DNA saved twice (an accession with and without its version, or a GenBank
        # record and its RefSeq copy) would be scored twice and tighten every interval for nothing
        try:
            import hashlib
            from Bio import SeqIO
            _r = next(SeqIO.parse(p, "genbank"))
            _k = hashlib.sha1(min(str(_r.seq).upper(), str(_r.seq.reverse_complement()).upper()).encode()).hexdigest()
            if str(_r.seq).strip("Nn") and _k in _seen_dna:
                print(f"duplicate genome skipped: {Path(p).stem} (same DNA as {_seen_dna[_k]})", flush=True); continue
            _seen_dna[_k] = Path(p).stem
        except Exception:
            pass
        try:
            ann = [x for x in S5.annotated_proteins(p) if x.get("sequence")]
            if a.de_novo:
                ps = [x for x in denovo_from_genbank(p) if 20 <= len(x["sequence"]) <= 2000]
            else:
                ps = [x for x in ann if 20 <= len(x["sequence"]) <= 2000]
        except Exception:
            continue
        if not ps: continue
        tr = {c: [] for c in CLASSES}
        if TF is not None:                          # truth from evidence, matched by protein id, never by name
            want = TF[Path(p).stem]
            idx = {x["id"]: i for i, x in enumerate(ps)}
            aseq = {x["id"]: x["sequence"] for x in ann}
            for c in CLASSES:
                for pid in want.get(c, []):
                    if a.de_novo:                   # place the proven protein on a gene-caller protein by sequence
                        j = seq_place(aseq.get(pid, ""), ps)
                        if j is not None: tr[c].append(j)
                        else: print(f"WARNING {Path(p).stem}: validated {c} {pid} not found by de novo gene calling", flush=True)
                    elif pid in idx: tr[c].append(idx[pid])
                    else: print(f"WARNING {Path(p).stem}: validated {c} {pid} not scorable (length filter?)", flush=True)
        else:
          for i, x in enumerate(ps):
            prod = x.get("product") or ""
            if ANTI.search(prod): continue
            for c in CLASSES:
                if TRUTH[c].search(prod): tr[c].append(i)
        genomes.append({"name": Path(p).stem, "proteins": ps, "truth": tr})
    print(f"{len(genomes)} genomes scanned; truths: "
          + ", ".join(f"{c} {sum(len(g['truth'][c]) for g in genomes)} in "
                      f"{sum(1 for g in genomes if g['truth'][c])} genomes" for c in CLASSES), flush=True)

    t = time.time()
    for g in genomes: g["X"] = feats([x["sequence"] for x in g["proteins"]])
    print(f"genome features in {int(time.time()-t)}s", flush=True)

    out = {"n_genomes_scanned": len(genomes), "boot": a.boot, "hyperparameters": dict(HP),
           "datasets": {"endolysin": a.endolysin_positives, "spanin": a.spanin_positives},
           "note": "Expanded LOGO: the atlas evaluation used 19 endolysins/12 genomes and 15 spanins/9 genomes, "
                   "which left every model comparison inside its confidence interval. This uses all annotated "
                   "lysis genes in the scanned panel. Protocol and negative recipes are unchanged from "
                   "scripts/22 and scripts/28, so the figures describe the models as deployed.",
           "classes": {}}

    for cls in a.classes:
        gs = [g for g in genomes if g["truth"][cls]]
        if not gs: print(f"{cls}: no truths, skipped"); continue
        pos, neg = load_sets(cls, a.endolysin_positives, a.spanin_positives)
        if SUB:
            n_before = len(pos)
            pos, strata = stratified_subsample(pos, SUB["n"], SUB["seed"], SUB["strata"])
            out.setdefault("subsample", {})[cls] = {
                **SUB, "n_before": n_before, "n_after": len(pos),
                "strata_before_after": strata, "ids": sorted(r["id"] for r in pos)}
            print(f"{cls}: subsampled training positives {n_before} -> {len(pos)} "
                  f"(seed {SUB['seed']}, strata {SUB['strata']})", flush=True)
        pos_seqs = [r["sequence"] for r in pos]
        cl_ids = np.array([r.get("cluster", -1) for r in pos])
        t = time.time()
        Xp, Xn = feats(pos_seqs), feats([r["sequence"] for r in neg])
        print(f"{cls}: {len(pos)} training positives, {len(neg)} negatives, {len(gs)} genomes, "
              f"{sum(len(g['truth'][cls]) for g in gs)} truths; features in {int(time.time()-t)}s", flush=True)
        if a.sim_features:
            t = time.time(); cdir = B / ".simcache"
            S_pos = sim_matrix(pos_seqs, pos_seqs, cdir)
            same = np.array([[x == y for y in pos_seqs] for x in pos_seqs])   # self AND exact duplicates
            S_pos[same] = 0.0
            S_neg = sim_matrix([r["sequence"] for r in neg], pos_seqs, cdir)
            allg = [x["sequence"] for g in gs for x in g["proteins"]]
            S_all = sim_matrix(allg, pos_seqs, cdir); o = 0
            for g in gs:
                g["S"] = S_all[o:o + len(g["proteins"])]; o += len(g["proteins"])
            print(f"{cls}: similarity matrices {S_pos.shape} {S_neg.shape} {S_all.shape} in {int(time.time()-t)}s",
                  flush=True)
        t = time.time()
        tseqs, tcol = [], {}
        for g in gs:
            for i in g["truth"][cls]:
                tcol.setdefault(g["name"], []).append(len(tseqs)); tseqs.append(g["proteins"][i]["sequence"])
        PT = pos_truth_matrix(pos_seqs, tseqs)
        print(f"{cls}: positive-vs-truth identity {PT.shape} in {int(time.time()-t)}s", flush=True)
        if a.score_all:
            rest = [g for g in genomes if not g["truth"][cls]]
            t = time.time(); pending = [g for g in rest if any(ck_load(CK, cls, m, g["name"], len(g["proteins"])) is None
                                                             for m in ("family", "sequence"))]
            if pending:
                allp = [x["sequence"] for g in pending for x in g["proteins"]]
                PA = pos_truth_matrix(pos_seqs, allp); o = 0; fcache = {}
                for g in pending:
                    n = len(g["proteins"]); drop = PA[:, o:o + n].max(1) >= 0.95; o += n
                    key = drop.tobytes()
                    if key not in fcache:
                        keep = ~drop
                        X = np.vstack([weighted_rows(Xp[keep], cl_ids[keep], a.pos_weight), Xn])
                        y = np.concatenate([np.ones(int(keep.sum()), int), np.zeros(len(neg), int)])
                        fcache[key] = hgb().fit(X, y)
                    sc = fcache[key].predict_proba(g["X"])[:, 1]
                    for m in ("family", "sequence"): ck_save(CK, cls, m, g["name"], sc)
            print(f"{cls}: context scores for {len(rest)} genomes without a curated {cls} "
                  f"({len(pending)} computed, {len(fcache) if pending else 0} fits) in {int(time.time()-t)}s", flush=True)
        res = {}
        for mode in ("family", "sequence"):
            t = time.time(); cache = {}; rows = []; resumed = 0; nn_rows = []
            for g in gs:
                s = ck_load(CK, cls, mode, g["name"], len(g["proteins"]))
                if s is not None:
                    resumed += 1
                else:
                    ident = PT[:, tcol[g["name"]]].max(1)
                    if mode == "family":
                        dc = {cl_ids[i] for i, v in enumerate(ident) if v >= CL.MIN_ID}
                        drop = np.isin(cl_ids, list(dc)) if dc else np.zeros(len(pos), bool)
                    else:
                        drop = np.array([v >= 0.95 for v in ident])
                    key = drop.tobytes()
                    if key not in cache:
                        keep = ~drop
                        if keep.sum() < 10: cache[key] = None
                        elif a.sim_features:
                            fp = S_pos[np.ix_(keep, keep)].max(1)[:, None]
                            fn = S_neg[:, keep].max(1)[:, None]
                            X = np.vstack([np.hstack([Xp[keep], fp]), np.hstack([Xn, fn])])
                            y = np.concatenate([np.ones(int(keep.sum()), int), np.zeros(len(neg), int)])
                            cache[key] = hgb().fit(X, y)
                        else:
                            X = np.vstack([weighted_rows(Xp[keep], cl_ids[keep], a.pos_weight), Xn])
                            y = np.concatenate([np.ones(int(keep.sum()), int), np.zeros(len(neg), int)])
                            cache[key] = hgb().fit(X, y)
                    m = cache[key]
                    Xg = g["X"]
                    if a.sim_features:
                        fg = g["S"][:, ~drop].max(1)[:, None]
                        Xg = np.hstack([Xg, fg])
                        ck_save(CK, cls + "-nn", mode, g["name"], fg[:, 0])
                    s = m.predict_proba(Xg)[:, 1] if m is not None else np.zeros(len(g["proteins"]))
                    ck_save(CK, cls, mode, g["name"], s)
                tset = set(g["truth"][cls])
                if a.sim_features:
                    snn = ck_load(CK, cls + "-nn", mode, g["name"], len(g["proteins"]))
                    for i in range(len(g["proteins"])):
                        nn_rows.append({"genome": g["name"], "y": int(i in tset), "score": float(snn[i])})
                order = np.argsort(-s)
                rank = {int(i): r for r, i in enumerate(order, 1)}
                for i in range(len(g["proteins"])):
                    prod = g["proteins"][i].get("product") or ""
                    rows.append({"genome": g["name"], "y": int(i in tset), "score": float(s[i]),
                                 "rank": rank[i], "virion": bool(D.STRUCT.search(prod)) if i in tset else False,
                                 "id": g["proteins"][i]["id"], "product": prod[:60] if i in tset else ""})
                del order, rank
            def agg(rs):
                y = np.array([r["y"] for r in rs]); sc = np.array([r["score"] for r in rs])
                if y.sum() == 0 or y.sum() == len(y): return None
                gnames = np.array([r["genome"] for r in rs])
                rngb = np.random.default_rng(0); uq = sorted(set(gnames)); vals = []
                for _ in range(a.boot):
                    pick = rngb.choice(uq, size=len(uq), replace=True)
                    ix = np.concatenate([np.where(gnames == q)[0] for q in pick])
                    if len(set(y[ix])) > 1: vals.append(average_precision_score(y[ix], sc[ix]))
                tr_rows = [r for r in rs if r["y"]]
                return {"AP": round(float(average_precision_score(y, sc)), 4),
                        "CI95_by_genome": [round(float(np.percentile(vals, 2.5)), 4),
                                           round(float(np.percentile(vals, 97.5)), 4)] if vals else None,
                        "n_truths": int(y.sum()), "n_scored": len(y), "n_genomes": len(uq),
                        "median_rank": float(np.median([r["rank"] for r in tr_rows])),
                        "top1": round(float(np.mean([r["rank"] == 1 for r in tr_rows])), 3),
                        "recall_at5": round(float(np.mean([r["rank"] <= 5 for r in tr_rows])), 3),
                        "recall_at0.5": round(float(np.mean([r["score"] >= 0.5 for r in tr_rows])), 3)}
            keep_exit = [r for r in rows if not (r["y"] and r["virion"])]
            res[f"{mode}_removal"] = {"all": agg(rows), "exit_only": agg(keep_exit),
                                      "unique_models_fitted": len(cache),
                                      "genomes_from_checkpoint": resumed,
                                      "fits_note": "unique_models_fitted counts fits done in THIS process; with "
                                                   "genomes_from_checkpoint > 0 the run resumed and earlier fits "
                                                   "are not counted. Scores are identical either way.",
                                      "seconds": int(time.time() - t)}
            if a.sim_features:
                # nearest-neighbour baseline: rank by identity alone. AP/CI only -- many ties at 0, so ranks are not
                # meaningful for it.
                res[f"{mode}_removal"]["nearest_neighbour_baseline"] = {
                    k: v for k, v in (agg([dict(r, rank=0) for r in nn_rows]) or {}).items()
                    if k in ("AP", "CI95_by_genome", "n_truths", "n_genomes")}
            v = res[f"{mode}_removal"]["all"]
            print(f"  {mode:<9} AP={v['AP']:.4f} CI={v['CI95_by_genome']} top1={v['top1']} "
                  f"r@5={v['recall_at5']} ({len(cache)} fits, {resumed} resumed, "
                  f"{int(time.time()-t)}s)", flush=True)
            res[f"{mode}_removal"]["truth_ranks"] = sorted(
                [{"genome": r["genome"], "id": r["id"], "rank": r["rank"], "score": round(r["score"], 4),
                  "of": sum(1 for q in rows if q["genome"] == r["genome"])} for r in rows if r["y"]],
                key=lambda r: (r["genome"], r["rank"]))
            res[f"{mode}_removal"]["missed_truths"] = sorted(
                [{"genome": r["genome"], "id": r["id"], "rank": r["rank"], "score": round(r["score"], 4),
                  "product": r["product"]} for r in rows if r["y"] and r["rank"] > 5],
                key=lambda r: -r["rank"])[:25]
        out["classes"][cls] = res
        (B / a.out).write_text(json.dumps(out, indent=1))

    print(f"\n{'class':<11}{'protocol':<11}{'n':>5}{'AP':>9}{'CI95':>20}{'top1':>7}{'r@5':>7}")
    for cls in out["classes"]:
        for mode in ("family_removal", "sequence_removal"):
            v = out["classes"][cls][mode]["all"]
            if not v: continue
            print(f"{cls:<11}{mode.replace('_removal',''):<11}{v['n_truths']:>5}{v['AP']:>9.4f}"
                  f"{str(v['CI95_by_genome']):>20}{v['top1']:>7.2f}{v['recall_at5']:>7.2f}")
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
