"""Uncertainty for the lysis-gene distribution across phage families (scripts/54, 54b, 55b, 57).

For each family and key feature: the percentage, its 95% CI from resampling gene-content clusters of related genomes
within the family (scripts/58; related phages are not independent), the number of clusters (the effective sample),
and the reliability of the underlying calls in that family (how often the call matched the annotation in the blind
group scans, reports/groups/groups_scan.md). Same denominators as the toolkit heatmap.
Output: reports/distribution/uncertainty.csv, uncertainty.md, figures/8_key_features_ci.png
Usage: python3 scripts/54c_distribution_uncertainty.py
"""
import csv, importlib, json, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
FB = importlib.import_module("54b_distribution_figures")
FG = importlib.import_module("53_set_figures")
B = Path(__file__).resolve().parent.parent
SETS, SHORT = FB.SETS, FB.SHORT
FEATS = [  # (label, class whose call it rests on, denominator, predicate)
    ("cassette co-located", None, lambda r: True, lambda r: r["cassette"] == "co-located"),
    ("holin class I (3 helices)", "holin", lambda r: bool(r.get("holin_class_deeptmhmm")), lambda r: r["holin_class_deeptmhmm"].startswith("I ")),
    ("holin class II (2 helices)", "holin", lambda r: bool(r.get("holin_class_deeptmhmm")), lambda r: r["holin_class_deeptmhmm"].startswith("II ")),
    ("holin class III (1 helix)", "holin", lambda r: bool(r.get("holin_class_deeptmhmm")), lambda r: r["holin_class_deeptmhmm"].startswith("III ")),
    (">= 2 strong holin genes", "holin", lambda r: True, lambda r: int(r["holin_copies_P90"]) >= 2),
    ("endolysin glycosidase", "endolysin", lambda r: bool(r.get("endolysin_class")), lambda r: r["endolysin_class"] == "glycosidase"),
    ("endolysin amidase", "endolysin", lambda r: bool(r.get("endolysin_class")), lambda r: r["endolysin_class"] == "amidase"),
    ("endolysin peptidase", "endolysin", lambda r: bool(r.get("endolysin_class")), lambda r: r["endolysin_class"] == "peptidase"),
    ("SAR endolysin (two tools agree)", "endolysin", lambda r: bool(r.get("endolysin_SAR")), lambda r: r["endolysin_SAR"] == "SAR (both)"),
    ("spanin two-component (i + o)", "spanin", lambda r: True, lambda r: r.get("spanin_type_signalp") == "two-component (i + o)"),
    ("spanin unimolecular (u)", "spanin", lambda r: True, lambda r: r.get("spanin_type_signalp") == "unimolecular (u)"),
    ("no confident spanin", "spanin", lambda r: True, lambda r: r.get("spanin_arch") == "no confident spanin")]


def main():
    by = FB.load()
    groups = json.load(open(B / "reports/figures/groups_summary.json"))
    rows = []
    for s in SETS:
        cl = json.load(open(B / f"reports/clusters/{s}.json"))
        for lab, cls, den, pred in FEATS:
            rr = [r for r in by[s] if den(r)]
            if not rr: continue
            v = np.array([float(pred(r)) for r in rr])
            d = defaultdict(list)
            for i, r in enumerate(rr): d[cl.get(r["genome"], {}).get("gene", r["genome"])].append(i)
            U = list(d.values()); rng = np.random.default_rng(0)
            bs = [v[[i for u in rng.integers(0, len(U), len(U)) for i in U[u]]].mean() for _ in range(2000)]
            rel = groups.get(s, {}).get(f"{cls}_call") if cls else None
            if cls == "spanin" and s in groups: rel = groups[s].get("spanin_pair")
            rows.append({"family": SHORT[s], "set": s, "feature": lab, "percent": round(100 * v.mean(), 1),
                         "ci_low": round(100 * np.percentile(bs, 2.5), 1), "ci_high": round(100 * np.percentile(bs, 97.5), 1),
                         "genomes": len(rr), "clusters": len(U),
                         "call_agreement_in_blind_scan": None if rel is None else round(rel, 2)})
    out = B / "reports/distribution"
    with open(out / "uncertainty.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(rows)
    figure(rows)
    print(f"wrote {len(rows)} rows to reports/distribution/uncertainty.csv")


def figure(rows):
    plt, INK, MUTED, GRID = FG.plt, FG.INK, FG.MUTED, FG.GRID
    feats = [f for f, *_ in FEATS]
    fig, axs = plt.subplots(3, 4, figsize=(15.5, 10.5), sharey=True)
    for ax, f in zip(axs.flat, feats):
        cls = next(c for l, c, *_ in FEATS if l == f)
        col = FG.COL.get(cls, "#4a4a68")
        for i, s in enumerate(SETS):
            r = next((x for x in rows if x["set"] == s and x["feature"] == f), None)
            if not r: continue
            weak = r["call_agreement_in_blind_scan"] is not None and r["call_agreement_in_blind_scan"] < 0.8
            ax.plot([r["ci_low"], r["ci_high"]], [i, i], color=col, lw=2, alpha=0.45 if weak else 0.9, solid_capstyle="butt")
            ax.plot(r["percent"], i, "o", color=col if not weak else "white", markeredgecolor=col, markersize=6, mew=1.5)
        ax.set_xlim(-3, 103); ax.set_xticks([0, 50, 100]); ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
        ax.set_title(f, loc="left", fontsize=9.5, color=col)
    for ax in axs[:, 0]:
        ax.set_yticks(range(len(SETS))); ax.set_yticklabels([SHORT[s] for s in SETS], fontsize=8.5)
    axs[0, 0].invert_yaxis()
    for ax in axs[-1]: ax.set_xlabel("% (95% CI, related genomes resampled together)", fontsize=8)
    fig.suptitle("Key lysis features by phage family, with uncertainty\nfilled dot: the family's calls for that gene "
                 "matched the annotation in >= 80% of genomes; open dot and faint bar: below 80%",
                 x=0.01, ha="left", fontsize=11.5, y=0.985, linespacing=1.5)
    fig.subplots_adjust(hspace=0.45, wspace=0.12, top=0.9)
    FG.save(fig, B / "reports/distribution/figures/8_key_features_ci.png")


if __name__ == "__main__":
    main()
