"""Assemble labelled endolysin and spanin positive sets with the same discipline as the holin set.

Sources per class, deduplicated by sequence:
  endolysin  UniProt reviewed endolysins + Swiss-Prot phage proteins named as a lysin/amidase/etc + pool proteins
             annotated endolysin + phage-only members of the endolysin catalytic Pfam families (data/raw/pfam_lysis)
  spanin     UniProt reviewed spanins + Swiss-Prot phage Rz/Rz1/spanin + pool spanins + the spanins already flagged
             in phage_negatives + phage-only members of the spanin Pfam families

Three guards carried over from the holin build:
  1. A sequence that is a known holin (in dataset.json or holins_extra_clustered.json) is NEVER a positive here.
  2. endolysin and spanin positive sets are disjoint; a sequence claimed by both is dropped as ambiguous.
  3. tiers record evidence strength (reviewed > pool/named > pfam), so scripts/28 can test whether the weak tiers
     earn their place, exactly as the holin curation was tiered.

Subsampling keeps ARCHITECTURAL spread, not raw count: every reviewed/named member is kept; the pfam depth is drawn
evenly across length deciles (endolysins span 100-900 aa), capped per family, so long multidomain lysins are not
crowded out by whatever length band a family is dense in.

Clustering: each class is clustered among itself (greedy set-cover, scripts/03) so a frozen gold holdout can be
drawn as whole homology clusters (seed 0, 20%), never split across train/test. Cross-class leakage into the holin
gold holdout is avoided because holin sequences are excluded outright (guard 1).

Writes data/processed/{endolysin,spanin}_positives.json and reports/lysis_build_report.json.
Usage: python3 scripts/27_build_lysis_dataset.py [--per-family 150] [--cap-endolysin 3000] [--gold-fraction 0.2]
"""
import argparse, gzip, csv, importlib, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
CL = importlib.import_module("03_cluster")

B = Path(__file__).resolve().parent.parent
R = B / "data/raw"
AA20 = set("ACDEFGHIKLMNPQRSTVWY")
MINL, MAXL = 30, 1200
END_NAME = re.compile(r"endolysin|lysozyme|muramidase|amidase|peptidoglycan|murein|glucosaminidase|\blysin\b|"
                      r"\bCHAP\b|transglycosylase|glycoside hydrolase|N-acetylmuramoyl", re.I)
SPA_NAME = re.compile(r"spanin|\bRz\b|\bRz1\b", re.I)
# A phage protein can carry a peptidoglycan-hydrolase domain and still not be an exit lysin: tail, baseplate and
# spike proteins use the same chemistry to get IN (T4 gp5, T7 gp16). Those are dropped from the Pfam depth tier,
# whose members are labelled by family membership alone and so cannot otherwise be told apart. The named and
# reviewed tiers are left alone -- there the annotation itself is the evidence.
STRUCT_NAME = re.compile(r"\btail\b|baseplate|base plate|\bcapsid\b|portal|\bvirion\b|structural|"
                         r"\bspike\b|tape ?measure|\bfib(er|re)\b|\bsheath\b|\bneck\b|whisker|"
                         r"terminase|major head|minor head|internal (head|virion) protein", re.I)
PFAM_CLASS = json.load(open(R / "pfam_lysis/provenance.json"))


def tsv(path):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        yield from csv.DictReader(fh, delimiter="\t")


def collect(cls):
    """(sequence -> record) for one class, from all its sources, reviewed preferred as representative."""
    name_re = END_NAME if cls == "endolysin" else SPA_NAME
    cand = []
    # reviewed UniProt set
    for r in tsv(R / f"uniprot_sp_{cls}.tsv.gz"):
        s = (r.get("Sequence") or "").strip().upper()
        if s: cand.append(dict(seq=s, name=r.get("Protein names") or "", org=r.get("Organism") or "",
                               acc=r.get("Entry") or "", reviewed=True, tier="reviewed", src="uniprot_reviewed"))
    # experimentally-validated gold tier (UniProt evidence at protein level, PE=1)
    vf = R / f"uniprot_validated_{cls}.tsv.gz"
    if vf.exists():
        for r in tsv(vf):
            s = (r.get("Sequence") or "").strip().upper()
            if s: cand.append(dict(seq=s, name=r.get("Protein names") or "", org=r.get("Organism") or "",
                                   acc=r.get("Entry") or "", reviewed=(r.get("Reviewed") or "").lower() == "reviewed",
                                   tier="validated", src="uniprot_validated"))
    # spanin breadth: phage-taxonomy spanins incl. unreviewed gene:rz/rz1 (the classic spanin gene names)
    if cls == "spanin" and (R / "uniprot_phage_spanin.tsv.gz").exists():
        for r in tsv(R / "uniprot_phage_spanin.tsv.gz"):
            s = (r.get("Sequence") or "").strip().upper()
            rev = (r.get("Reviewed") or "").lower() == "reviewed"
            if s: cand.append(dict(seq=s, name=r.get("Protein names") or "", org=r.get("Organism") or "",
                                   acc=r.get("Entry") or "", reviewed=rev, tier=("reviewed" if rev else "trembl"), src="phage_spanin"))
    # CPT (Young lab) curated spanins -- Kongari et al. 2018, the published origin of the CPT spanin database
    if cls == "spanin" and (R / "kongari2018/spanins.json").exists():
        for o in json.load(open(R / "kongari2018/spanins.json")):
            cand.append(dict(seq=o["seq"], name=f"{o['type']} (Kongari2018)", org=o.get("host") or "",
                             acc=o.get("accession") or "", reviewed=False, tier="curated", src="kongari2018"))
    # Swiss-Prot phage proteins named for this class
    for r in tsv(R / "uniprot_sp_phage.tsv.gz"):
        nm = r.get("Protein names") or ""
        if name_re.search(nm):
            s = (r.get("Sequence") or "").strip().upper()
            if s: cand.append(dict(seq=s, name=nm, org=r.get("Organism") or "", acc=r.get("Entry") or "",
                                   reviewed=(r.get("Reviewed") or "").lower() == "reviewed", tier="reviewed", src="sp_phage"))
    # pool proteins annotated for this class
    for p in json.load(open(B / "data/processed/pool.json")):
        if name_re.search(p.get("product") or ""):
            cand.append(dict(seq=p["sequence"], name=p.get("product") or "", org="", acc=p.get("accession") or "",
                             reviewed=False, tier="pool", src="pool"))
    # spanins already flagged among phage negatives
    if cls == "spanin":
        for r in json.load(open(B / "data/processed/phage_negatives.json")):
            if r.get("spanin"):
                cand.append(dict(seq=r["sequence"], name="Rz-like spanin", org="", acc=r.get("id") or "",
                                 reviewed=False, tier="pool", src="phage_negatives"))
    # phage-only Pfam family members (depth), per-family decile subsample applied later
    fams = [acc for acc, m in PFAM_CLASS.items() if m.get("class") == cls and m.get("rows")]
    pfam_members = defaultdict(list)
    for acc in fams:
        for r in tsv(R / f"pfam_lysis/{acc}.tsv.gz"):
            s = (r.get("Sequence") or "").strip().upper()
            nm = r.get("Protein names") or ""
            if s and not STRUCT_NAME.search(nm):
                pfam_members[acc].append(dict(seq=s, name=nm, org=r.get("Organism") or "",
                                              acc=r.get("Entry") or "", reviewed=(r.get("Reviewed") or "").lower() == "reviewed",
                                              tier="pfam", src=f"pfam:{acc}", pfam=acc))
    return cand, pfam_members


def decile_sample(recs, k, seed=0):
    if len(recs) <= k: return recs
    lens = np.array([len(r["seq"]) for r in recs])
    edges = np.quantile(lens, np.linspace(0, 1, 11))
    buckets = defaultdict(list)
    for i, r in enumerate(recs): buckets[min(int(np.searchsorted(edges, lens[i], "right")) - 1, 9)].append(r)
    rng = np.random.default_rng(seed); out = []; per = max(1, k // max(len(buckets), 1))
    for b in sorted(buckets):
        g = buckets[b]; out += [g[i] for i in rng.permutation(len(g))[:per]]
    if len(out) < k:
        rest = [r for r in recs if r not in out]; out += [rest[i] for i in rng.permutation(len(rest))[:k - len(out)]]
    return out[:k]


def stratified_cap(recs, k, per_family):
    """Bound the set for clustering cost WITHOUT letting any one Pfam family be sampled away.

    The old global decile_sample(recs, cap) drew across the whole class at once, so a family added for its
    architecture could be dropped wholesale by a cap set for an older, denser family -- the failure that left
    PF01832 Glucosaminidase effectively absent. Evidence-bearing tiers are kept outright; the pfam depth tier is
    sampled per family, by length decile within the family, and only then trimmed evenly if the cap still binds.
    """
    keep = [r for r in recs if r["tier"] != "pfam"]
    byfam = defaultdict(list)
    for r in recs:
        if r["tier"] == "pfam": byfam[r.get("pfam") or r["src"]].append(r)
    depth = []
    for fam in sorted(byfam):
        depth += decile_sample(byfam[fam], per_family)
    budget = max(k - len(keep), 0)
    while len(depth) > budget and budget > 0:
        per = max(1, budget // max(len(byfam), 1))
        trimmed = []
        for fam in sorted(byfam):
            g = [r for r in depth if (r.get("pfam") or r["src"]) == fam]
            trimmed += g[:per]
        if len(trimmed) >= len(depth): break
        depth = trimmed
    return keep + depth[:budget]


def collect_confusables():
    """Lysis-adjacent families that are NOT holin/endolysin/spanin (scripts/26 role="confusable").

    Virion-associated (entry) lysozymes, pesticin, single-gene lysis membrane proteins, colicin-release lysis
    proteins and disruptins. They are emitted as their own file so scripts/28 can add them to the negatives and
    MEASURE whether they help, rather than assuming it.
    """
    out = []
    for acc, m in sorted(PFAM_CLASS.items()):
        if m.get("role") != "confusable" or not m.get("rows"): continue
        for r in tsv(R / "pfam_lysis" / f"{acc}.tsv.gz"):
            sq = (r.get("Sequence") or "").strip().upper()
            if not sq or not (MINL <= len(sq) <= MAXL) or set(sq) - AA20: continue
            out.append({"id": f"confusable_{r.get('Entry') or len(out)}", "sequence": sq, "length": len(sq),
                        "label": "confusable", "pfam": acc, "pfam_name": m.get("pfam_name") or "",
                        "source": f"pfam:{acc}", "description": r.get("Protein names") or "",
                        "organism": r.get("Organism") or ""})
    u = {}
    for r in out: u.setdefault(r["sequence"], r)
    return list(u.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-family", type=int, default=150)
    ap.add_argument("--cap-endolysin", type=int, default=6000)
    ap.add_argument("--gold-fraction", type=float, default=0.2)
    ap.add_argument("--no-struct-guard", action="store_true",
                    help="ABLATION: keep Pfam-tier members whose product names them a tail/baseplate/virion "
                         "protein. Used to attribute the v2 endolysin regression between breadth dilution and "
                         "this guard; not for building a shipped dataset.")
    ap.add_argument("--suffix", default="", help="appended to output filenames so an ablation does not clobber "
                                                 "the real dataset")
    a = ap.parse_args()

    base = json.load(open(B / "data/processed/dataset.json"))
    cur = json.load(open(B / "data/processed/holins_extra_clustered.json"))
    holin_seqs = {r["sequence"] for r in base if r["label"] == "holin"} | {r["sequence"] for r in cur if r["label"] == "holin"}

    if a.no_struct_guard:
        global STRUCT_NAME
        STRUCT_NAME = re.compile(r"(?!x)x")           # matches nothing
        print("ABLATION: structural-name guard DISABLED", flush=True)
    raw = {}
    for cls in ("endolysin", "spanin"):
        cand, pfam_members = collect(cls)
        for acc, members in pfam_members.items():
            cand += decile_sample(members, a.per_family)
        raw[cls] = cand
        print(f"{cls}: {len(cand)} candidate rows before dedup", flush=True)

    # dedup within class (reviewed representative preferred); then resolve cross-class and holin overlaps
    TIER_RANK = {"validated": 0, "reviewed": 1, "curated": 2, "pool": 3, "trembl": 4, "pfam": 5}
    def dedup(cand):
        u = {}
        for c in sorted(cand, key=lambda c: (TIER_RANK[c["tier"]], len(c["seq"]))):
            u.setdefault(c["seq"], c)      # best-evidence representative wins per sequence
        return u
    end_u, spa_u = dedup(raw["endolysin"]), dedup(raw["spanin"])
    both = set(end_u) & set(spa_u)
    drop = {"is_known_holin": 0, "claimed_by_both_classes": len(both), "bad_length": 0, "nonstandard": 0}
    out = {}
    for cls, u in (("endolysin", end_u), ("spanin", spa_u)):
        recs = []
        for s, c in u.items():
            if s in both: continue
            if s in holin_seqs: drop["is_known_holin"] += 1; continue
            if not (MINL <= len(s) <= MAXL): drop["bad_length"] += 1; continue
            if set(s) - AA20: drop["nonstandard"] += 1; continue
            recs.append(c)
        if cls == "endolysin": recs = stratified_cap(recs, a.cap_endolysin, a.per_family)
        out[cls] = recs
        print(f"{cls}: {len(recs)} distinct positives after guards "
              f"(reviewed {sum(r['tier']=='reviewed' for r in recs)}, pool {sum(r['tier']=='pool' for r in recs)}, "
              f"pfam {sum(r['tier']=='pfam' for r in recs)})", flush=True)

    rep = {"dropped": drop, "classes": {}}
    for cls, recs in out.items():
        t = time.time(); seqs = [r["seq"] for r in recs]
        edges = CL.all_edges(seqs)
        cl = CL.greedy(len(seqs), edges, [len(s) for s in seqs], 80)
        print(f"{cls}: clustered {len(seqs)} into {len(set(cl))} clusters in {int(time.time()-t)}s", flush=True)
        # frozen gold holdout: whole clusters, seed 0
        clusters = sorted(set(cl)); rng = np.random.default_rng(0)
        gold_cl = set(rng.choice(clusters, size=max(1, int(len(clusters) * a.gold_fraction)), replace=False).tolist())
        records = []
        for r, c in zip(recs, cl):
            records.append({"id": f"{cls}_{r['acc'] or len(records)}", "sequence": r["seq"], "length": len(r["seq"]),
                            "label": cls, "tier": r["tier"], "source": r["src"], "cluster": int(c),
                            "in_gold_holdout": int(c) in gold_cl,
                            "sources": [{"source": r["src"], "accession": r["acc"], "description": r["name"], "organism": r["org"]}]})
        (B / f"data/processed/{cls}_positives{a.suffix}.json").write_text(json.dumps(records, indent=1))
        L = [len(r["seq"]) for r in recs]
        rep["classes"][cls] = {"positives": len(records), "clusters": len(clusters),
                               "gold_clusters": len(gold_cl), "gold_positives": sum(r["in_gold_holdout"] for r in records),
                               "tiers": dict(Counter(r["tier"] for r in recs)),
                               "length_median": int(np.median(L)), "length_p90": int(np.percentile(L, 90)),
                               "over_150aa": int(sum(x > 150 for x in L))}
    conf = collect_confusables()
    known = {r["seq"] for cls in out for r in out[cls]} | holin_seqs
    conf = [r for r in conf if r["sequence"] not in known]   # never contradict a positive label
    (B / f"data/processed/lysis_confusables{a.suffix}.json").write_text(json.dumps(conf, indent=1))
    from collections import Counter as _C
    rep["confusables"] = {"count": len(conf), "by_family": dict(_C(r["pfam"] for r in conf))}
    print(f"confusables: {len(conf)} sequences across {len(rep['confusables']['by_family'])} families", flush=True)
    (B / f"reports/lysis_build_report{a.suffix}.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
