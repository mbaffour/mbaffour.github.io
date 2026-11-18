"""Compact JSON for the release explorer page (release/explorer/index.html), from the release tables (scripts/62).

  data/genomes.json   scan and benchmark genomes: [set, genome, organism, host, length, genes called, nested ORFs,
                      ANI-95 group, gene-content group, first submitted year]
  data/scans.json     per scanned genome (version used in the reports): the three calls scored against the
                      annotation, and every called protein with its topology from the three tools
  data/bench.json     curated benchmark genes with ranks under the three protocols and their PHROGs / Pfam hits
  data/meta.json      sets, prediction versions, build checks, decisions
Usage: python3 scripts/63_release_explorer.py
"""
import csv, gzip, json, re
from collections import defaultdict
from pathlib import Path
B = Path(__file__).resolve().parent.parent
R = B / "release"; OUT = R / "explorer/data"


def rd(n): return list(csv.DictReader(open(R / n)))
def num(x, f=float):
    try: return f(x)
    except (TypeError, ValueError): return None
def tf(x): return None if x in ("", None) else x == "True"


def rle(topo):
    return "".join(f"{m.group(0)[0]}{len(m.group(0))}" for m in re.finditer(r"(.)\1*", topo or ""))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    G = rd("genomes.csv")
    genomes = [[g["set"], g["genome"], g["organism"], g["host_genus"], num(g["length_bp"], int), num(g["n_genes_called_denovo"], int),
                num(g["n_nested_lipoprotein_orfs"], int), g["ani95_cluster"], g["gene_content_cluster"],
                num(g["first_submitted_year"], int)] for g in G]
    used = {(v["set"], v["prediction_version"]) for v in rd("prediction_versions.csv") if v["used_in_reports"] == "True"}
    S = defaultdict(lambda: {"c": {}, "p": []})
    for r in rd("scan_calls.csv"):
        if (r["set"], r["prediction_version"]) not in used: continue
        S[f"{r['set']}|{r['genome']}"]["c"][r["class"]] = {
            "id": r["call_id"], "tier": r["call_tier"], "s": num(r["call_start"], int), "e": num(r["call_stop"], int),
            "str": r["call_strand"], "len": num(r["call_length_aa"], int), "P": num(r["call_P"]), "rk": num(r["call_rank"], int),
            "as": r["call_annotated_as"], "v": r["call_verdict"], "has": tf(r["genome_annotates_class"]),
            "ann": r["annotated_genes"], "best": num(r["annotated_best_rank"], int), "top5": tf(r["annotated_in_top5"]),
            "ok": tf(r["call_is_annotated_gene"]), "pair": tf(r["call_is_annotated_gene_or_overlapping_partner"]),
            "idn": num(r["annotated_max_identity_to_training"]), "nov": r["annotated_novelty"],
            "t5": list(zip(r["top5_ids"].split(";"), [num(x) for x in r["top5_P"].split(";")]))}
    for p in rd("call_proteins.csv"):
        k = f"{p['set']}|{p['genome']}"
        S[k]["p"].append({
            "role": p["role"], "tier": p["tier"], "id": p["id"], "s": int(p["start"]), "e": int(p["stop"]), "str": p["strand"],
            "len": int(p["length_aa"]), "sid": p["sequence_id"], "seq": p["sequence"],
            "o": {"n": num(p["ours_helices"], int), "sp": p["ours_helix_spans"], "nt": p["ours_n_terminus"], "sar": p["ours_sar_rule"]},
            "d": {"t": p["deeptmhmm_type"], "n": num(p["deeptmhmm_helices"], int), "nt": p["deeptmhmm_n_terminus"], "r": rle(p["deeptmhmm_topology"])},
            "sp": {"p": p["signalp"], "pr": [num(x) for x in p["signalp_probs"].split(";")] if p["signalp_probs"] else []},
            "hc": [p.get("holin_class_deeptmhmm", ""), p.get("holin_class_ours", "")],
            "sar": p.get("endolysin_SAR_consensus", ""), "sm": p.get("spanin_member_type", "")})
    (OUT / "scans.json").write_text(json.dumps(S, separators=(",", ":")))
    (OUT / "genomes.json").write_text(json.dumps(genomes, separators=(",", ":")))
    bench = []
    for b in rd("benchmark_genes.csv"):
        bench.append({k: (num(v, int) if k.endswith("_rank") or k in ("start", "stop", "length_aa", "proteins_in_genome") else
                          num(v) if k.endswith("_score") or k == "phrogs_bitscore" else v) for k, v in b.items()})
    (OUT / "bench.json").write_text(json.dumps(bench, separators=(",", ":")))
    sets = {}
    for ln in (R / "README.md").read_text().splitlines():
        m = re.match(r"\| `(\w+)` \| (.+) \| (\d+) \|", ln)
        if m: sets[m.group(1)] = m.group(2)
    meta = {"sets": sets, "versions": rd("prediction_versions.csv"), "checks": json.load(open(R / "build_checks.json")),
            "decisions": rd("decisions.csv"), "commit": rd("commit_log.csv")[0]}
    (OUT / "meta.json").write_text(json.dumps(meta, separators=(",", ":")))
    for f in sorted(OUT.iterdir()): print(f"{f.name}: {f.stat().st_size/1e6:.2f} MB")


if __name__ == "__main__":
    main()
