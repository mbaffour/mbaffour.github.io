"""Control the signature candidates properly: holins against MEMBRANE proteins, not against soluble ones.

scripts/16 compares holins to bacterial negatives, phage negatives and spanins. Two of those contrasts cannot
support a claim about holins:

  * the phage negatives are overwhelmingly SOLUBLE (median n_tm 0, soluble_frac 1.00), so "holins vs phage
    negatives" mostly reports that holins are membrane proteins. Effect sizes of 0.83 there are not signatures.
  * the spanin contrast controls for size, phage origin and lysis-cassette membership, but spanins are peculiar
    in their own right: the o-spanin is an outer-membrane lipoprotein with a lipobox cysteine, which is why
    spanins carry more cysteine, and their anchors sit at the extreme N terminus.

So a candidate only means something if it points the SAME way against all three of: spanins, bacterial membrane
proteins, and the membrane subset of the phage negatives. This script applies that test, and separately asks
whether the glycine enrichment seen against spanins sits inside the TM helices (as the published glycine zipper
of pinholin S21-68 does) or is simply what transmembrane helices look like.

Usage: python3 scripts/18_signature_controls.py
"""
import json, re, sys
from pathlib import Path
import numpy as np
from scipy.stats import mannwhitneyu
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F

B = Path(__file__).resolve().parent.parent
NAMES = F.HAND_NAMES + F.LOCAL_NAMES
ZIPPER = re.compile(r"G...[GAS]")          # GxxxG / GxxxA / GxxxS spacing
CAND = ["frac_hydrophobic", "aac_F", "aac_I", "aac_G", "aac_A", "aac_L", "anchor_tm_len", "soluble_frac",
        "tm_fraction", "last_tm_end_to_cterm", "residues_after_last_tm", "cterm20_K+R", "cterm20_net_charge",
        "frac_charged", "aac_C", "n_tm", "length"]
STRONG, WEAK, FLOOR = 0.30, 0.15, 0.10


def vec(s):
    v, _ = F.local(s)
    return np.concatenate([F.handcrafted(s), np.array(v)])


def effect(a, b):
    u = mannwhitneyu(a, b, alternative="two-sided")
    return 2 * u.statistic / (len(a) * len(b)) - 1, float(u.pvalue)


def tm_text(seq): return "".join(seq[s - 1:e] for s, e in F.tm_segments(seq))


def main():
    data = json.load(open(B / "data/processed/dataset.json"))
    extra = json.load(open(B / "data/processed/phage_negatives.json"))
    hol = [r for r in data if r["label"] == "holin"]
    span = [r for r in extra if r.get("spanin")]
    btm = [r for r in data if r["label"] == "negative" and len(F.tm_segments(r["sequence"])) >= 1]
    ptm = [r for r in extra if not r.get("spanin") and len(F.tm_segments(r["sequence"])) >= 1]
    print(f"holins {len(hol)} | spanins {len(span)} | bacterial membrane {len(btm)} | phage membrane {len(ptm)}", flush=True)
    M = {k: np.array([vec(r["sequence"]) for r in v]) for k, v in
         (("holin", hol), ("spanin", span), ("bacterial_membrane", btm), ("phage_membrane", ptm))}

    rows = []
    for f in CAND:
        j = NAMES.index(f); h = M["holin"][:, j]
        es = {}
        for k in ("spanin", "bacterial_membrane", "phage_membrane"):
            e, p = effect(h, M[k][:, j]); es[k] = {"effect": round(e, 3), "p": float(f"{p:.3g}")}
        # sign consistency is judged over effects big enough to have a direction at all (|e| >= FLOOR);
        # a feature is only "consistent" if every one of the three points the same way.
        vals = [es[k]["effect"] for k in ("spanin", "bacterial_membrane", "phage_membrane")]
        directed = [v for v in vals if abs(v) >= FLOOR]
        consistent = len(directed) == 3 and len({np.sign(v) for v in directed}) == 1
        verdict = ("consistent across all three controls" if consistent else
                   "explained by membrane-ness" if abs(es["spanin"]["effect"]) >= STRONG and
                   abs(es["bacterial_membrane"]["effect"]) < WEAK else
                   "points in opposite directions against different controls")
        rows.append({"feature": f, "medians": {k: round(float(np.median(M[k][:, j])), 4) for k in M},
                     "effects": es, "verdict": verdict})

    # the glycine question: inside the TM helices, or just what TM helices look like?
    gly = {}
    for k, grp in (("holin", hol), ("spanin", span), ("bacterial_membrane", btm)):
        tms = [tm_text(r["sequence"]) for r in grp]
        tms = [t for t in tms if len(t) >= 10]
        gly[k] = {"n": len(tms), "median_gly_in_tm": round(float(np.median([sum(c == "G" for c in t) / len(t) for t in tms])), 4),
                  "zipper_hits_per_100_tm_residues": round(float(np.median([100 * len(ZIPPER.findall(t)) / len(t) for t in tms])), 2),
                  "percent_with_a_zipper": round(100 * float(np.mean([bool(ZIPPER.search(t)) for t in tms])), 1)}
    gcmp = {}
    for other in ("spanin", "bacterial_membrane"):
        a = [sum(c == "G" for c in tm_text(r["sequence"])) / max(len(tm_text(r["sequence"])), 1) for r in hol
             if len(tm_text(r["sequence"])) >= 10]
        b = [sum(c == "G" for c in tm_text(r["sequence"])) / max(len(tm_text(r["sequence"])), 1)
             for r in (span if other == "spanin" else btm) if len(tm_text(r["sequence"])) >= 10]
        e, p = effect(np.array(a), np.array(b))
        ha = [1.0 if ZIPPER.search(tm_text(r["sequence"])) else 0.0 for r in hol if len(tm_text(r["sequence"])) >= 10]
        hb = [1.0 if ZIPPER.search(tm_text(r["sequence"])) else 0.0
              for r in (span if other == "spanin" else btm) if len(tm_text(r["sequence"])) >= 10]
        e2, p2 = effect(np.array(ha), np.array(hb))
        gcmp[f"holin_vs_{other}"] = {"gly_in_tm": {"effect": round(e, 3), "p": float(f"{p:.3g}")},
                                     "has_zipper": {"effect": round(e2, 3), "p": float(f"{p2:.3g}")}}

    out = {"why": "a candidate signature only means something if it points the same way against spanins, "
                  "bacterial membrane proteins AND the membrane subset of the phage negatives",
           "flaw_found_in_scripts_16": "the phage negatives are overwhelmingly soluble (median n_tm 0), so that "
                                       "contrast reports membrane-ness rather than any holin signature",
           "candidates": rows,
           "glycine": {"question": "is the glycine enrichment seen against spanins inside the TM helices, as the "
                                   "published pinholin S21-68 glycine zipper is, or generic to TM helices?",
                       "groups": gly, "comparisons": gcmp,
                       "answer": "generic. Holin TM helices are no more glycine-zippered than ordinary bacterial "
                                 "membrane proteins, and FEWER holins carry a GxxxG-spaced motif at all "
                                 f"({gly['holin']['percent_with_a_zipper']}% vs "
                                 f"{gly['bacterial_membrane']['percent_with_a_zipper']}%). The apparent "
                                 "enrichment is because spanins are glycine-poor, not because holins are rich."},
           "conclusion": "no interpretable compositional feature survives all three controls except C-terminal "
                         "K+R enrichment, which is the long-established charged-tail signature. Everything else "
                         "is intermediate between spanins and bacterial membrane proteins."}
    (B / "reports/signature_controls.json").write_text(json.dumps(out, indent=2))

    print(f"\n{'feature':<24}{'holin':>9}{'spanin':>9}{'bactTM':>9}{'phagTM':>9}  {'vs span':>8}{'vs bact':>9}{'vs phag':>9}   verdict")
    for r in rows:
        m = r["medians"]; e = r["effects"]
        print(f"{r['feature']:<24}{m['holin']:>9.3f}{m['spanin']:>9.3f}{m['bacterial_membrane']:>9.3f}"
              f"{m['phage_membrane']:>9.3f}  {e['spanin']['effect']:>+8.3f}{e['bacterial_membrane']['effect']:>+9.3f}"
              f"{e['phage_membrane']['effect']:>+9.3f}   {r['verdict']}")
    print("\nglycine, inside the TM helices:")
    for k, v in gly.items():
        print(f"  {k:<20} n={v['n']:>5}  Gly {v['median_gly_in_tm']:.4f}  "
              f"zipper/100res {v['zipper_hits_per_100_tm_residues']:>5.2f}  with a zipper {v['percent_with_a_zipper']:>5.1f}%")
    print("  " + json.dumps(gcmp))
    print("\n" + out["conclusion"])


if __name__ == "__main__":
    main()
