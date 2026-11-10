"""Build phage-derived negatives, so the training set matches the task the model is actually used for.

Why this exists. The 9,503 original negatives are 7,884 bacterial TM proteins + 1,619 Swiss-Prot phage proteins,
but they contain 0 spanins and no proteins mined from a lysis cassette. (An earlier version of this note claimed
"0 phage proteins"; that was a bug -- it counted an is_phage flag that only the mined negatives carry. The
phage proteins were there; the HARD phage confusables were not.) So the model had few examples of the things it
most needs to reject when scanning a genome -- above all spanins, which are small phage lysis-cassette membrane
proteins. The genome scan showed the cost: Rz-like spanins scored 0.86-0.96 because no spanin was ever a
top hits (0.86-0.96) because no spanin was ever shown to the model as a negative.

What a candidate negative must satisfy:
  1. It comes from a genome that is NOT used in any evaluation (the 12 benchmark genomes and the 16 phages of the
     topology atlas are excluded by accession), so adding these cannot inflate a later genome-level score.
  2. Its own annotation does not say holin.
  3. It is not within 3 genes of an annotated lysis gene -- i.e. not in a lysis cassette, where an unannotated
     holin is most likely to be hiding.
  4. Its genome has an annotated holin somewhere else, so that genome's holin is accounted for and this protein
     is unlikely to be the unannotated one.
  5. It is not in the same family as ANY known holin, train or gold holdout: Smith-Waterman identity < MIN_ID
     (0.30) at coverage >= MIN_COV, the same bar scripts/03 uses to define a family. Anything at or above it is
     dropped as ambiguous, never relabelled.
     The bar is identity, not raw SW score. Screening on "any hit at score >= 80" instead removed 51% of
     candidates, but 309 of those 411 hits sat at 20-30% identity -- background similarity between short
     proteins, not homology. Dropping those would have left a negative set systematically unlike holins, making
     the task easier than reality, which is the opposite of what hard negatives are for. At identity >= 0.30
     only 12% are dropped, and the weakly-similar remainder is kept precisely because it is hard.

Spanins are added separately and deliberately as HARD negatives: Rz/Rz1-like spanins are lysis-cassette membrane
proteins that are not holins, and they are the dominant false-positive class, so they are exactly what the model
needs to see. For them rule 3 is waived (they live in the cassette by definition) but every other rule holds.

Cluster ids: new negatives are clustered among themselves (greedy, same settings as scripts/03) and offset past
the existing ids, so grouped cross-validation cannot split homologous negatives across folds.

Usage: python3 scripts/12_phage_negatives.py [--per-genome 20] [--max 6000]
"""
import argparse, importlib, json, re, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
CL = importlib.import_module("03_cluster")
BM = importlib.import_module("06_benchmark_genomes")

B = Path(__file__).resolve().parent.parent
HOLIN_WORD = re.compile(r"holin", re.I)
SPANIN = re.compile(r"spanin|\brz\b|rz1", re.I)
# the 16 phages of the sibling topology atlas: they are the membrane cross-check set, so they must not train anything
ATLAS_ACCESSIONS = ("NC_001422.1,NC_003287.2,NC_001417.2,NC_001890.1,NC_001416.1,NC_000866.4,NC_001604.1,"
                    "NC_005859.1,NC_005856.1,NC_000929.1,NC_002167.1,NC_002371.2,NC_001421.2,NC_003715.1,"
                    "NC_003716.1,NC_003714.1,NC_011048.1,NC_004166.2").split(",")
HOMOLOGY_SCORE = 80


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-genome", type=int, default=20, help="cap per source genome, for diversity")
    ap.add_argument("--max", type=int, default=6000)
    a = ap.parse_args()

    data = json.load(open(B / "data/processed/dataset.json"))
    pool = json.load(open(B / "data/processed/pool.json"))
    # gold_holdout.json stores ids into dataset.json, not separate records, so `data` already holds every known
    # holin -- train and gold alike. Screening against all of them covers the holdout too.
    gold = json.load(open(B / "data/processed/gold_holdout.json"))
    gold_ids = set(gold["ids"])
    holins = [r for r in data if r["label"] == "holin"]
    n_gold_holins = sum(1 for r in holins if r["id"] in gold_ids)
    have = {r["sequence"] for r in data}

    excl = {acc.split(".")[0] for acc, _, _ in BM.GENOMES} | {a_.split(".")[0] for a_ in ATLAS_ACCESSIONS}
    by_genome = {}
    for p in pool:
        by_genome.setdefault(p["accession"], []).append(p)
    genome_has_holin = {g: any(p.get("annotated_holin") for p in ps) for g, ps in by_genome.items()}

    stats = {"pool": len(pool), "genomes": len(by_genome),
             "known_holins_screened_against": len(holins), "of_which_gold_holdout": n_gold_holins,
             "genomes_excluded_as_evaluation": sum(1 for g in by_genome if g.split(".")[0] in excl),
             "genomes_with_an_annotated_holin": sum(genome_has_holin.values())}

    cand, spanins, drop = [], [], {"evaluation_genome": 0, "annotated_holin": 0, "lysis_neighbourhood": 0,
                                   "genome_has_no_annotated_holin": 0, "already_in_dataset": 0, "per_genome_cap": 0}
    for g, ps in sorted(by_genome.items()):
        if g.split(".")[0] in excl:
            drop["evaluation_genome"] += len(ps); continue
        kept = 0
        for p in sorted(ps, key=lambda q: q["index"]):
            prod = p.get("product") or ""
            if p["sequence"] in have: drop["already_in_dataset"] += 1; continue
            if SPANIN.search(prod) and not HOLIN_WORD.search(prod):
                spanins.append(p); continue              # hard negative: rule 3 waived, see module docstring
            if HOLIN_WORD.search(prod) or p.get("annotated_holin"): drop["annotated_holin"] += 1; continue
            if p.get("has_lysis_neighbour"): drop["lysis_neighbourhood"] += 1; continue
            if not genome_has_holin.get(g): drop["genome_has_no_annotated_holin"] += 1; continue
            if kept >= a.per_genome: drop["per_genome_cap"] += 1; continue
            cand.append(p); kept += 1

    # one representative per distinct sequence, then trim to --max while keeping genomes balanced
    uniq = {}
    for p in cand: uniq.setdefault(p["sequence"], p)
    cand = list(uniq.values())
    if len(cand) > a.max:
        rng = np.random.default_rng(0); idx = rng.permutation(len(cand))[:a.max]
        cand = [cand[i] for i in sorted(idx)]
    suniq = {}
    for p in spanins: suniq.setdefault(p["sequence"], p)
    spanins = list(suniq.values())
    stats |= {"candidates_after_rules": len(cand), "spanin_hard_negatives": len(spanins), "dropped": drop}
    print(json.dumps(stats, indent=1), flush=True)

    # rule 5: drop anything with homology to any known holin (train or gold). Ambiguous is excluded, not relabelled.
    seqs = [p["sequence"] for p in cand + spanins]
    t = time.time()
    ident = CL.search([r["sequence"] for r in holins], seqs, HOMOLOGY_SCORE)
    print(f"homology screen of {len(seqs)} candidates against {len(holins)} known holins in {int(time.time()-t)}s", flush=True)
    keep = [p for p, i in zip(cand + spanins, ident) if i < CL.MIN_ID]
    dropped_hom = len(seqs) - len(keep)
    weak = sum(1 for i in ident if 0 < i < CL.MIN_ID)
    print(f"  dropped {dropped_hom} at identity >= {CL.MIN_ID}; kept {weak} with weak (<{CL.MIN_ID}) similarity as hard negatives", flush=True)
    n_span = sum(1 for p in keep if SPANIN.search(p.get("product") or ""))

    # cluster the new negatives among themselves so grouped CV cannot split homologues across folds
    t = time.time()
    ks = [p["sequence"] for p in keep]
    edges = CL.all_edges(ks)
    cl = CL.greedy(len(ks), edges, [len(s) for s in ks], HOMOLOGY_SCORE)
    base = max(r["cluster"] for r in data) + 1
    print(f"clustered {len(ks)} new negatives into {len(set(cl))} clusters in {int(time.time()-t)}s", flush=True)

    out = []
    for p, c in zip(keep, cl):
        prod = p.get("product") or ""
        out.append({"id": f"phageneg_{p['accession']}_{p['index']}", "sequence": p["sequence"], "length": len(p["sequence"]),
                    "label": "negative", "cluster": base + c, "tcdb_family": None, "is_phage": True,
                    "phage_negative": True, "spanin": bool(SPANIN.search(prod)),
                    "sources": [{"source": "RefSeq phage genome", "accession": p["accession"], "description": prod,
                                 "organism": p.get("organism", ""), "gene_index": p["index"]}]})
    (B / "data/processed/phage_negatives.json").write_text(json.dumps(out, indent=1))
    rep = {"rules": {"1_evaluation_genomes_excluded": sorted(excl),
                     "2_own_annotation_not_holin": True, "3_not_within_3_genes_of_a_lysis_gene": "waived for spanins",
                     "4_source_genome_has_an_annotated_holin_elsewhere": True,
                     "5_not_same_family_as_any_known_holin": f"SW identity < {CL.MIN_ID} at coverage >= {CL.MIN_COV} (screen score >= {HOMOLOGY_SCORE})"},
           "weakly_similar_kept_as_hard_negatives": weak,
           "selection": stats, "dropped_by_holin_homology": dropped_hom,
           "final": {"phage_negatives": len(out), "of_which_spanins": n_span, "clusters": len(set(cl)),
                     "cluster_id_offset": base, "genomes_contributing": len({p['accession'] for p in keep})}}
    (B / "reports/phage_negatives_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep["final"] | {"dropped_by_holin_homology": dropped_hom}, indent=1))


if __name__ == "__main__":
    main()
