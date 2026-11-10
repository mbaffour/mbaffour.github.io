"""Compare the v2 family-expanded models against the shipped v1 models, and pick what to ship.

The decision rule is fixed before the numbers are read, so the choice is not made by looking at the outcome:

  primary    leave-one-genome-out genome-scan average precision, STRICT protocol (the genome's whole family is
             removed at >=30% identity). This is the only arm that measures what the family expansion was for --
             finding a lysis gene whose family the model has never seen, which is what DAC15 asked of it.
  tie-break  the realistic protocol (>=95% identical near-duplicates removed), then false positives over 0.9.
  ship       the confusable-negative variant only if it does not LOSE strict AP; it is there to suppress entry
             lysins and single-gene lysis proteins, a precision claim, so it must not cost recall-driven AP.

Why gold-holdout AP is NOT the primary number here: scripts/27 re-draws the homology clusters and the frozen gold
holdout over the new, larger positive set, so the v1 and v2 gold holdouts are different sequence sets and their
APs are not comparable. The leave-one-genome-out figure is defined by the 16 atlas phages, not by the holdout, so
it is comparable across versions. Quoting the gold number across a dataset change would be a false comparison.

Usage: python3 scripts/35_compare_retrain.py
Writes reports/retrain_v2_comparison.json
"""
import json
from pathlib import Path

B = Path(__file__).resolve().parent.parent
R = B / "reports"
PROTO = {"family_removal": "strict", "sequence_removal": "realistic"}


def lysis(cls, tag):
    """(strict, realistic, config) for an endolysin/spanin eval report, or None if the run is missing."""
    f = R / f"{cls}_eval{tag}.json"
    if not f.exists(): return None
    d = json.load(open(f))
    return {"strict": d.get("family_removal", {}).get("genome_AP"),
            "realistic": d.get("sequence_removal", {}).get("genome_AP"),
            "gold_AP": d.get("gold_holdout", {}).get("AP"),
            "n_annotated": d.get("n_annotated_in_atlas"), "config": d.get("config", {}), "report": f.name}


def holin_arms():
    f = R / "curated_retrain_eval.json"
    if not f.exists(): return {}
    d = json.load(open(f))["models"]
    arms = {}
    for k, v in d.items():
        arm, _, mode = k.partition("__")
        g = v.get("genome_scan_PRIMARY", {})
        arms.setdefault(arm, {})[PROTO.get(mode, mode)] = {
            "AP": g.get("average_precision"), "CI95": g.get("CI95_by_genome"),
            "fp_over_0.9": g.get("false_positives_over_0.9"), "top1_per_genome": g.get("top1_per_genome")}
    return arms


def main():
    out = {"decision_rule": "strict LOGO genome AP primary; realistic as tie-break; confusables must not lose "
                            "strict AP. Gold-holdout AP is not comparable across versions (clusters re-drawn).",
           "endolysin": {}, "spanin": {}, "holin": holin_arms()}

    print(f"{'model':<34}{'strict':>9}{'realistic':>11}{'gold':>8}  note")
    print("-" * 78)
    for cls in ("endolysin", "spanin"):
        for label, tag in (("v1 shipped", ""), ("v2 families", "_v2_noconf"), ("v2 families+confusables", "_v2_conf")):
            r = lysis(cls, tag)
            if not r: print(f"{cls+' '+label:<34}{'(missing)':>9}"); continue
            out[cls][label] = r
            nc = r["config"].get("confusable_negatives", 0)
            s, rl, g = r["strict"], r["realistic"], r["gold_AP"]
            print(f"{cls+' '+label:<34}{s if s is None else format(s,'.4f'):>9}"
                  f"{rl if rl is None else format(rl,'.4f'):>11}{g if g is None else format(g,'.4f'):>8}"
                  f"  {'+'+str(nc)+' confusable negs' if nc else ''}")
        v1, c2 = out[cls].get("v1 shipped"), out[cls].get("v2 families")
        if v1 and c2 and v1["strict"] is not None and c2["strict"] is not None:
            d = c2["strict"] - v1["strict"]
            print(f"{'  -> strict change from families':<34}{d:+.4f}"
                  f"   ({'families help' if d > 0 else 'families do NOT help'} on never-seen-family recall)")

    print(f"\n{'holin arm':<34}{'strict':>9}{'realistic':>11}{'FP>0.9':>8}")
    print("-" * 78)
    for arm, v in sorted(out["holin"].items()):
        s, rl = v.get("strict", {}), v.get("realistic", {})
        print(f"{arm:<34}{s.get('AP') if s.get('AP') is None else format(s['AP'],'.4f'):>9}"
              f"{rl.get('AP') if rl.get('AP') is None else format(rl['AP'],'.4f'):>11}"
              f"{str(rl.get('fp_over_0.9')):>8}")

    # ---- apply the rule ----
    rec = {}
    for cls in ("endolysin", "spanin"):
        cands = {k: v for k, v in out[cls].items() if k.startswith("v2") and v["strict"] is not None}
        if not cands: rec[cls] = "no v2 run available"; continue
        nf, cf = cands.get("v2 families"), cands.get("v2 families+confusables")
        best = "v2 families"
        if cf and nf and cf["strict"] >= nf["strict"]:
            best = "v2 families+confusables"
        elif cf and not nf:
            best = "v2 families+confusables"
        v1 = out[cls].get("v1 shipped")
        if v1 and v1["strict"] is not None and cands[best]["strict"] < v1["strict"]:
            rec[cls] = (f"KEEP v1: {best} strict {cands[best]['strict']:.4f} < v1 {v1['strict']:.4f}")
        else:
            rec[cls] = f"SHIP {best} ({cands[best]['report']})"
    hb, hc = out["holin"].get("B_plus_curated"), out["holin"].get("C_plus_crossclass")
    if hb and hc:
        bs, cs = hb.get("strict", {}).get("AP"), hc.get("strict", {}).get("AP")
        if bs is not None and cs is not None:
            rec["holin"] = (f"SHIP arm C with --crossclass (strict {cs:.4f} >= B {bs:.4f})" if cs >= bs
                            else f"KEEP arm B (arm C strict {cs:.4f} < B {bs:.4f}); cross-class negatives cost recall")
    elif hb:
        rec["holin"] = "arm C not run yet"
    out["recommendation"] = rec
    print("\nrecommendation:")
    for k, v in rec.items(): print(f"  {k:<11} {v}")
    (R / "retrain_v2_comparison.json").write_text(json.dumps(out, indent=2))
    print("\nwrote reports/retrain_v2_comparison.json")


if __name__ == "__main__":
    main()
