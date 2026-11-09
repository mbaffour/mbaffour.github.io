"""Curate the Pfam holin family members into training records, tiered by how strong the evidence is.

Pfam membership is weaker evidence than a Swiss-Prot holin annotation: it is assigned by profile match, and for an
unreviewed entry nobody has checked it. So members are tiered rather than pooled, and scripts/21 tests whether
each tier earns its place against the frozen gold holdout and the leave-one-genome-out scan.

  tier pfam_reviewed    - a reviewed (Swiss-Prot) member of a holin family
  tier pfam_unreviewed  - an unreviewed (TrEMBL) member

Antiholin families are labelled holin_like, never holin. An antiholin is the holin's antagonist, not a holin, and
mislabelling them would repeat the conflict that silently deleted lambda S from an earlier version of this
dataset. Entries whose own protein name says antiholin are moved to holin_like too, whatever family they are in.

Subsampling keeps ARCHITECTURAL spread rather than raw count: every reviewed member is kept, and unreviewed
members are drawn evenly across the family's length deciles. Taking the first N instead would over-sample whatever
length the family happens to be dense in, which is the opposite of the point -- the training set already has 558
holins with a median length of 100 and only 52 above 150 aa.

Usage: python3 scripts/20_curate_more_holins.py [--per-family 150]
"""
import argparse, gzip, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

B = Path(__file__).resolve().parent.parent
RAW = B / "data/raw/pfam"
ANTIHOLIN = re.compile(r"antiholin|anti-holin|antagonist", re.I)
AA20 = set("ACDEFGHIKLMNPQRSTVWY")
MIN_LEN, MAX_LEN = 25, 400


def rows(path):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            f = line.rstrip("\n").split("\t")
            if len(f) == len(head): yield dict(zip(head, f))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--per-family", type=int, default=150)
    a = ap.parse_args()
    prov = json.load(open(RAW / "provenance.json"))
    data = json.load(open(B / "data/processed/dataset.json"))
    have = {r["sequence"] for r in data}
    print(f"{len(prov)} families downloaded; existing dataset holds {len(have)} distinct sequences", flush=True)

    kept, per_fam, drop = [], {}, Counter()
    for acc, meta in sorted(prov.items()):
        f = RAW / f"{acc}.tsv.gz"
        if not f.exists(): continue
        anti_family = meta.get("is_antiholin_family", False)
        cand = []
        for r in rows(f):
            seq = (r.get("Sequence") or "").strip().upper()
            name = r.get("Protein names") or ""
            if not seq: drop["no_sequence"] += 1; continue
            if not (MIN_LEN <= len(seq) <= MAX_LEN): drop["length_out_of_range"] += 1; continue
            if set(seq) - AA20: drop["non_standard_residue"] += 1; continue
            if seq in have: drop["already_in_dataset"] += 1; continue
            cand.append({"acc": r.get("Entry") or "", "reviewed": (r.get("Reviewed") or "").lower() == "reviewed",
                         "name": name, "organism": r.get("Organism") or "", "organism_id": r.get("Organism (ID)") or "",
                         "hosts": r.get("Virus hosts") or "", "seq": seq, "pfam": acc,
                         "antiholin": anti_family or bool(ANTIHOLIN.search(name)),
                         "existence": r.get("Protein existence") or ""})
        # distinct sequences only, reviewed entry preferred as the representative
        uniq = {}
        for c in sorted(cand, key=lambda c: (not c["reviewed"], len(c["seq"]))):
            uniq.setdefault(c["seq"], c)
        cand = list(uniq.values())
        rev = [c for c in cand if c["reviewed"]]
        unrev = [c for c in cand if not c["reviewed"]]
        # even draw across length deciles so long architectures are not crowded out by the family's dense band
        take = max(0, a.per_family - len(rev))
        if len(unrev) > take and take > 0:
            lens = np.array([len(c["seq"]) for c in unrev])
            edges = np.quantile(lens, np.linspace(0, 1, 11))
            buckets = defaultdict(list)
            for i, c in enumerate(unrev): buckets[min(int(np.searchsorted(edges, lens[i], "right")) - 1, 9)].append(c)
            rng = np.random.default_rng(0); picked = []
            per = max(1, take // max(len(buckets), 1))
            for b in sorted(buckets):
                grp = buckets[b]
                idx = rng.permutation(len(grp))[:per]
                picked += [grp[i] for i in idx]
            if len(picked) < take:                     # top up from what is left, still at random
                rest = [c for c in unrev if c not in picked]
                idx = rng.permutation(len(rest))[:take - len(picked)]
                picked += [rest[i] for i in idx]
            unrev = picked[:take]
        sel = rev + unrev
        per_fam[acc] = {"pfam_name": meta.get("pfam_name"), "antiholin_family": anti_family,
                        "members_downloaded": meta.get("rows"), "usable_distinct": len(cand),
                        "reviewed_kept": len(rev), "unreviewed_kept": len(unrev),
                        "median_length": int(np.median([len(c["seq"]) for c in sel])) if sel else None,
                        "over_150_aa": sum(1 for c in sel if len(c["seq"]) > 150)}
        kept += sel

    # a sequence may belong to several families; keep one record, remembering all of them
    byseq = {}
    for c in kept:
        if c["seq"] in byseq:
            byseq[c["seq"]]["pfams"].append(c["pfam"])
            byseq[c["seq"]]["antiholin"] |= c["antiholin"]
        else:
            byseq[c["seq"]] = dict(c, pfams=[c["pfam"]])
    out = []
    for i, (seq, c) in enumerate(sorted(byseq.items(), key=lambda kv: kv[1]["acc"])):
        label = "holin_like" if c["antiholin"] else "holin"
        out.append({"id": f"pfam_{c['acc'] or i}", "sequence": seq, "length": len(seq), "label": label,
                    "tier": "pfam_reviewed" if c["reviewed"] else "pfam_unreviewed",
                    "pfam_families": sorted(set(c["pfams"])), "is_phage": True,
                    "antiholin": bool(c["antiholin"]),
                    "sources": [{"source": "UniProt via Pfam holin family", "accession": c["acc"],
                                 "description": c["name"], "organism": c["organism"],
                                 "organism_id": c["organism_id"], "virus_hosts": c["hosts"],
                                 "protein_existence": c["existence"], "pfam": sorted(set(c["pfams"]))}]})
    (B / "data/processed/holins_extra.json").write_text(json.dumps(out, indent=1))
    L = [r["length"] for r in out if r["label"] == "holin"]
    rep = {"dropped": dict(drop), "per_family": per_fam,
           "final": {"records": len(out),
                     "holin": sum(1 for r in out if r["label"] == "holin"),
                     "holin_like_antiholin": sum(1 for r in out if r["label"] == "holin_like"),
                     "pfam_reviewed": sum(1 for r in out if r["tier"] == "pfam_reviewed"),
                     "pfam_unreviewed": sum(1 for r in out if r["tier"] == "pfam_unreviewed"),
                     "holin_median_length": int(np.median(L)) if L else None,
                     "holin_over_150_aa": sum(1 for x in L if x > 150),
                     "holin_over_200_aa": sum(1 for x in L if x > 200)}}
    (B / "reports/curation_report.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep["final"], indent=1))
    print("\nfamilies contributing most length diversity (>150 aa):")
    for acc, v in sorted(per_fam.items(), key=lambda kv: -(kv[1]["over_150_aa"] or 0))[:12]:
        print(f"  {acc} {str(v['pfam_name'])[:44]:<44} kept {v['reviewed_kept']+v['unreviewed_kept']:>4} "
              f"median {v['median_length']}  >150aa {v['over_150_aa']}")


if __name__ == "__main__":
    main()
