"""Figures for the lysis-gene distribution across phage families (data: scripts/54, reports/distribution/).

  1_toolkit_heatmap.png   one row per family, one column per feature, cell = % of genomes
  2_endolysin_classes.png catalytic class of the called endolysin, with cell-wall-binding domains and SAR-like N termini
  3_spanin_architecture.png  embedded / overlapping / separate / single, and lipoboxes
  4_holins.png            holin length and holin copy number (P >= 0.9) per genome
  5_cassettes.png         co-located / dispersed / incomplete, and the gene orders of co-located cassettes
Every figure goes through the text-overlap check of scripts/53 before it is written.
Usage: python3 scripts/54b_distribution_figures.py
"""
import csv, importlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
FG = importlib.import_module("53_set_figures")
plt, save, COL, INK, MUTED, GRID = FG.plt, FG.save, FG.COL, FG.INK, FG.MUTED, FG.GRID
B = Path(__file__).resolve().parent.parent
SETS = ["n4", "lambda", "p2", "drexler", "t7", "t5", "t4", "herelle", "jumbo"]
SHORT = {"n4": "N4-like", "lambda": "Lambdoid", "t7": "T7-like", "p2": "P2-like", "drexler": "Drexlerviridae",
         "t5": "T5-like", "herelle": "Herelleviridae", "t4": "T4-like", "jumbo": "Jumbo (>200 kb)"}
OUT = B / "reports/distribution/figures"


def load():
    R = list(csv.DictReader(open(B / "reports/distribution/lysis_by_genome.csv")))
    for tp in (B / "reports/distribution/topology_by_genome.csv", B / "reports/distribution/topology_consensus_by_genome.csv"):
      if tp.exists():
        T = {(r["set"], r["genome"]): r for r in csv.DictReader(open(tp))}
        for r in R:
            for k, v in T.get((r["set"], r["genome"]), {}).items():
                if k not in ("set", "genome"): r[k] = v
    by = defaultdict(list)
    for r in R: by[r["set"]].append(r)
    return by


def frac(rows, f):
    return 100.0 * sum(1 for r in rows if f(r)) / len(rows) if rows else np.nan


def ylabels(by):
    return [f"{SHORT[s]}  (n={len(by[s])}, {np.median([float(r['genome_kb']) for r in by[s]]):.0f} kb)" for s in SETS]


def heatmap(by):
    ALL = lambda r: True
    HOL = lambda r: bool(r.get("holin_class_deeptmhmm"))
    END = lambda r: bool(r.get("endolysin_class"))
    ENC = lambda r: bool(r.get("endolysin_type"))
    feats = [  # (column label, group, which genomes form the denominator, predicate)
        ("co-located", "cassette", ALL, lambda r: r["cassette"] == "co-located"),
        ("dispersed", "cassette", ALL, lambda r: r["cassette"] == "dispersed"),
        ("incomplete", "cassette", ALL, lambda r: r["cassette"] == "incomplete"),
        ("class I (3 helices)", "holin", HOL, lambda r: r["holin_class_deeptmhmm"].startswith("I ")),
        ("class II (2 helices)", "holin", HOL, lambda r: r["holin_class_deeptmhmm"].startswith("II ")),
        ("class III (1 helix)", "holin", HOL, lambda r: r["holin_class_deeptmhmm"].startswith("III ")),
        ("N terminus inside", "holin", HOL, lambda r: r.get("holin_nterm_deeptmhmm") == "in"),
        ("our predictor agrees", "holin", lambda r: bool(r.get("holin_class_ours")),
         lambda r: r.get("holin_class_agree") == "True"),
        ("known Pfam holin family", "holin", HOL, lambda r: r.get("holin_pfam") not in ("", "none", None)),
        ("≥ 2 strong holin genes", "holin", ALL, lambda r: int(r["holin_copies_P90"]) >= 2),
        ("glycosidase", "endolysin", END, lambda r: r["endolysin_class"] == "glycosidase"),
        ("transglycosylase", "endolysin", END, lambda r: r["endolysin_class"] == "transglycosylase"),
        ("amidase", "endolysin", END, lambda r: r["endolysin_class"] == "amidase"),
        ("peptidase", "endolysin", END, lambda r: r["endolysin_class"] == "peptidase"),
        ("no domain detected", "endolysin", END, lambda r: r["endolysin_class"] == "no domain detected"),
        ("cell-wall binding", "endolysin", END, lambda r: r.get("endolysin_binding") == "True"),
        ("SAR (ours + DeepTMHMM agree)", "endolysin", lambda r: bool(r.get("endolysin_SAR")),
         lambda r: r["endolysin_SAR"] == "SAR (both)"),
        ("two-component (i + o)", "spanin", ALL, lambda r: r.get("spanin_type_signalp") == "two-component (i + o)"),
        ("unimolecular (u)", "spanin", ALL, lambda r: r.get("spanin_type_signalp") == "unimolecular (u)"),
        ("embedded pair", "spanin", ALL, lambda r: r.get("spanin_arch") == "embedded"),
        ("overlapping pair", "spanin", ALL, lambda r: r.get("spanin_arch") == "overlapping"),
        ("no confident spanin", "spanin", ALL, lambda r: r.get("spanin_arch") == "no confident spanin")]
    M = np.array([[frac([r for r in by[s] if d(r)], f) for _, _, d, f in feats] for s in SETS])
    fig, ax = plt.subplots(figsize=(16.0, 5.8))
    cmap = plt.get_cmap("Greys")
    ax.imshow(M, cmap=cmap, vmin=0, vmax=140, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8.5, color="white" if v > 75 else INK)
    ax.set_xticks(range(len(feats)))
    ax.set_xticklabels([l for l, _, _, _ in feats], fontsize=8.5, rotation=90,
                       ha="center", va="bottom")
    ax.set_yticks(range(len(SETS))); ax.set_yticklabels(ylabels(by), fontsize=9)
    ax.tick_params(length=0); ax.xaxis.tick_top()
    for sp in ax.spines.values(): sp.set_visible(False)
    groups = [(g, [j for j, (_, gg, _, _) in enumerate(feats) if gg == g]) for g in ("cassette", "holin", "endolysin", "spanin")]
    for g, js in groups:
        c = COL.get(g, INK)
        ax.annotate("", xy=(js[0] - 0.4, len(SETS) - 0.35), xytext=(js[-1] + 0.4, len(SETS) - 0.35),
                    arrowprops=dict(arrowstyle="-", color=c, lw=2.5), annotation_clip=False)
        ax.text((js[0] + js[-1]) / 2, len(SETS) + 0.15, g, ha="center", va="top", fontsize=10, color=c, fontweight="bold")
        if js[0] > 0: ax.axvline(js[0] - 0.5, color="white", lw=3)
    ax.set_ylim(len(SETS) + 0.5, -0.5)
    ax.set_title("The lysis toolkit of each phage family, as called from DNA\n"
                 "% of genomes (cassette, spanin) · % of confident holin calls (holin) · % of called endolysins (endolysin)",
                 loc="left", fontsize=11.5, pad=12, x=-0.2, linespacing=1.6)
    return save(fig, OUT / "1_toolkit_heatmap.png")


def stacked(ax, by, cats, colors, key, title):
    left = np.zeros(len(SETS))
    for c, col in zip(cats, colors):
        v = np.array([frac(by[s], lambda r: key(r) == c) for s in SETS])
        ax.barh(range(len(SETS)), v, left=left, color=col, height=0.7, label=c, edgecolor="white", linewidth=0.6)
        for i, (l, w) in enumerate(zip(left, v)):
            if w >= 9: ax.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", fontsize=7.5, color=FG.ink_on(col))
        left += v
    ax.set_xlim(0, 100); ax.set_yticks(range(len(SETS))); ax.invert_yaxis()
    ax.set_xlabel("% of genomes"); ax.set_title(title, loc="left", fontsize=10, color=INK)


def endolysin_fig(by):
    cats = ["glycosidase", "transglycosylase", "amidase", "peptidase", "other endolysin family", "multi-catalytic",
            "no domain detected", ""]
    cols = ["#8c2d04", "#d94801", "#fd8d3c", "#fdbe85", "#a1887f", "#5d4037", "#d9d9d9", "#eeeeee"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.6), gridspec_kw={"width_ratios": [2.3, 1]})
    stacked(a1, by, cats, cols, lambda r: r.get("endolysin_class", ""), "catalytic class of the called endolysin (Pfam)")
    a1.set_yticklabels(ylabels(by), fontsize=8.5)
    h, l = a1.get_legend_handles_labels()
    a1.legend(h[:-1], l[:-1], loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=4, frameon=False, fontsize=8)
    y = np.arange(len(SETS))
    b = [frac([r for r in by[s] if r.get("endolysin_class")], lambda r: r["endolysin_binding"] == "True") for s in SETS]
    sar = [frac([r for r in by[s] if r.get("endolysin_SAR")], lambda r: r["endolysin_SAR"] == "SAR (both)") for s in SETS]
    a2.barh(y - 0.18, b, 0.34, color=COL["endolysin"], label="cell-wall-binding domain")
    a2.barh(y + 0.18, sar, 0.34, color=COL["endolysin"], alpha=0.4, label="SAR endolysin (ours + DeepTMHMM agree)")
    for i in range(len(SETS)):
        a2.text(b[i] + 1, y[i] - 0.18, f"{b[i]:.0f}", va="center", fontsize=7.5)
        a2.text(sar[i] + 1, y[i] + 0.18, f"{sar[i]:.0f}", va="center", fontsize=7.5)
    a2.set_yticks(y); a2.set_yticklabels([]); a2.invert_yaxis(); a2.set_xlim(0, 108); a2.set_xticks([0, 25, 50, 75, 100])
    a2.set_xlabel("% of called endolysins"); a2.set_title("modules", loc="left", fontsize=10)
    a2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), frameon=False, fontsize=8)
    a2.xaxis.grid(True, color=GRID); a2.set_axisbelow(True)
    fig.suptitle("Endolysins by phage family", x=0.01, ha="left", fontsize=12, y=1.0)
    return save(fig, OUT / "2_endolysin_classes.png")


def spanin_fig(by):
    cats = ["embedded", "overlapping", "separate", "single", "no confident spanin"]
    cols = ["#1b5e20", "#43a047", "#a5d6a7", "#8d6e63", "#d9d9d9"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.6), gridspec_kw={"width_ratios": [2.3, 1]})
    stacked(a1, by, cats, cols, lambda r: r.get("spanin_arch", ""), "spanin genes: how the pair is arranged")
    a1.set_yticklabels(ylabels(by), fontsize=8.5)
    a1.legend(["embedded (one gene inside the other)", "overlapping", "separate", "single gene (u-spanin-like)",
               "no confident spanin"], loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False, fontsize=8)
    y = np.arange(len(SETS))
    lip = [frac([r for r in by[s] if r.get("spanin_arch") not in ("", "no confident spanin")],
                lambda r: r["spanin_lipobox"] == "True") for s in SETS]
    a2.barh(y, lip, 0.6, color=COL["spanin"])
    for i, v in enumerate(lip): a2.text((0 if np.isnan(v) else v) + 1, i, "–" if np.isnan(v) else f"{v:.0f}", va="center", fontsize=7.5)
    a2.set_yticks(y); a2.set_yticklabels([]); a2.invert_yaxis(); a2.set_xlim(0, 115); a2.set_xticks([0, 25, 50, 75, 100])
    a2.set_xlabel("% of confident spanin calls"); a2.set_title("lipobox (outer-membrane lipoprotein)", loc="left", fontsize=10)
    a2.xaxis.grid(True, color=GRID); a2.set_axisbelow(True)
    fig.suptitle("Spanins by phage family (Herelleviridae infect Gram-positive hosts, which have no outer membrane)",
                 x=0.01, ha="left", fontsize=12, y=1.0)
    return save(fig, OUT / "3_spanin_architecture.png")


def holin_fig(by):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.6), gridspec_kw={"width_ratios": [1.6, 1]})
    data = [[int(r["holin_len"]) for r in by[s] if r.get("holin_len")] for s in SETS]
    bp = a1.boxplot(data, orientation="horizontal", widths=0.6, patch_artist=True, showfliers=False,
                    medianprops=dict(color=INK), boxprops=dict(facecolor=COL["holin"], alpha=0.35, edgecolor=COL["holin"]),
                    whiskerprops=dict(color=COL["holin"]), capprops=dict(color=COL["holin"]))
    rng = np.random.default_rng(0)
    for i, d in enumerate(data, 1):
        a1.scatter(d, i + rng.uniform(-0.18, 0.18, len(d)), s=5, color=COL["holin"], alpha=0.45, linewidths=0)
    a1.set_yticks(range(1, len(SETS) + 1)); a1.set_yticklabels(ylabels(by), fontsize=8.5); a1.invert_yaxis()
    a1.set_xlabel("length of the called holin (aa)"); a1.set_xlim(40, 260)
    a1.xaxis.grid(True, color=GRID); a1.set_axisbelow(True)
    a1.set_title("holin size", loc="left", fontsize=10)
    cats = ["1", "2", "3", "4+"]; cols = ["#c6dbef", "#6baed6", "#2171b5", "#08306b"]
    left = np.zeros(len(SETS))
    for c, col in zip(cats, cols):
        f = (lambda r, c=c: int(r["holin_copies_P90"]) >= 4) if c == "4+" else (lambda r, c=c: int(r["holin_copies_P90"]) == int(c))
        v = np.array([frac(by[s], f) for s in SETS])
        a2.barh(range(len(SETS)), v, left=left, color=col, height=0.7, label=c, edgecolor="white", linewidth=0.6)
        for i, (l, w) in enumerate(zip(left, v)):
            if w >= 9: a2.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", fontsize=7.5, color=FG.ink_on(col))
        left += v
    a2.set_yticks(range(len(SETS))); a2.set_yticklabels([]); a2.invert_yaxis(); a2.set_xlim(0, 100)
    a2.set_xlabel("% of genomes (rest: none at P ≥ 0.9)")
    a2.set_title("strong holin-like genes per genome (P ≥ 0.9)", loc="left", fontsize=10)
    a2.legend(title="genes", loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=4, frameon=False, fontsize=8, title_fontsize=8)
    fig.suptitle("Holins by phage family", x=0.01, ha="left", fontsize=12, y=1.0)
    return save(fig, OUT / "4_holins.png")


def cassette_fig(by):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.6), gridspec_kw={"width_ratios": [1.5, 1.2]})
    stacked(a1, by, ["co-located", "dispersed", "incomplete"], ["#4a4a68", "#9b9bb5", "#dcdce6"],
            lambda r: r["cassette"], "all three genes confident: together (≤ 6 genes) or spread out")
    a1.set_yticklabels(ylabels(by), fontsize=8.5)
    a1.legend(["co-located", "dispersed", "incomplete (a gene not confidently found)"], loc="upper center",
              bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False, fontsize=8)
    orders = ["H-E-S", "E-S-H", "E-H-S", "S-H-E", "H-S-E", "S-E-H"]
    ocol = ["#3B6EA8", "#C8553D", "#e6a23c", "#5B8E5A", "#8e7cc3", "#999999"]
    left = np.zeros(len(SETS))
    for o, col in zip(orders, ocol):
        v = np.array([frac([r for r in by[s] if r["cassette"] == "co-located"], lambda r: r["order"] == o) for s in SETS])
        v = np.nan_to_num(v)
        a2.barh(range(len(SETS)), v, left=left, color=col, height=0.7, label=o, edgecolor="white", linewidth=0.6)
        for i, (l, w) in enumerate(zip(left, v)):
            if w >= 12: a2.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", fontsize=7.5, color=FG.ink_on(col))
        left += v
    for i, s in enumerate(SETS):
        n = sum(r["cassette"] == "co-located" for r in by[s])
        a2.text(101, i, f"n={n}", va="center", fontsize=7.5, color=MUTED)
    a2.set_yticks(range(len(SETS))); a2.set_yticklabels([]); a2.invert_yaxis(); a2.set_xlim(0, 112)
    a2.set_xticks([0, 25, 50, 75, 100])
    a2.set_xlabel("% of co-located cassettes"); a2.set_title("gene order, in the direction of transcription", loc="left", fontsize=10)
    a2.legend(title="H holin · E endolysin · S spanin", loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=6,
              frameon=False, fontsize=8, title_fontsize=8)
    fig.suptitle("Lysis cassette organisation by phage family", x=0.01, ha="left", fontsize=12, y=1.0)
    return save(fig, OUT / "5_cassettes.png")


def holin_topology_fig(by):
    cats = ["I (3 helices)", "II (2 helices)", "III (1 helix)", "no helix", "4+ helices"]
    cols = ["#08306b", "#2171b5", "#9ecae1", "#d9d9d9", "#6a51a3"]
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(14.2, 4.8), gridspec_kw={"width_ratios": [2.0, 0.9, 1.6]})
    sub = {s: [r for r in by[s] if r.get("holin_class_deeptmhmm")] for s in SETS}
    stacked(a1, sub, cats, cols, lambda r: r["holin_class_deeptmhmm"], "class of the called holin (DeepTMHMM helices)")
    def agree(s):
        rr = [r for r in by[s] if r.get("holin_class_ours")]
        return 100 * sum(r["holin_class_agree"] == "True" for r in rr) / max(len(rr), 1)
    a1.set_yticklabels([f"{SHORT[s]}  (n={len(sub[s])}; our predictor agrees {agree(s):.0f}%{' · unresolved' if agree(s) < 60 else ''})"
                        for s in SETS], fontsize=8.5)
    a1.set_xlabel("% of confident holin calls")
    a1.legend(["class I (3)", "class II (2)", "class III (1)", "no helix", "4+"], loc="upper center",
              bbox_to_anchor=(0.5, -0.16), ncol=5, frameon=False, fontsize=8)
    v = [frac(sub[s], lambda r: r.get("holin_nterm_deeptmhmm") == "in") for s in SETS]
    a2.barh(range(len(SETS)), v, color=COL["holin"], height=0.6)
    for i, x in enumerate(v): a2.text(x + 1.5, i, f"{x:.0f}", va="center", fontsize=7.5)
    a2.set_yticks(range(len(SETS))); a2.set_yticklabels([]); a2.invert_yaxis(); a2.set_xlim(0, 118)
    a2.set_xticks([0, 50, 100]); a2.set_xlabel("% with N terminus inside")
    a2.set_title("orientation", loc="left", fontsize=10); a2.xaxis.grid(True, color=GRID); a2.set_axisbelow(True)
    sub2 = {s: [r for r in by[s] if r.get("holin2_class_deeptmhmm")] for s in SETS}
    stacked(a3, sub2, cats, cols, lambda r: r["holin2_class_deeptmhmm"], "the second strong holin-like gene")
    a3.set_yticklabels([]); a3.set_xlabel("% of genomes with ≥ 2 strong holin-like genes")
    for i, s in enumerate(SETS): a3.text(101, i, f"n={len(sub2[s])}", va="center", fontsize=7.5, color=MUTED)
    a3.set_xlim(0, 115); a3.set_xticks([0, 25, 50, 75, 100])
    fig.suptitle("Holin membrane topology by phage family (DeepTMHMM; our predictor as concordance check)",
                 x=0.01, ha="left", fontsize=12, y=1.0)
    return save(fig, OUT / "6_holin_topology.png")


def spanin_type_fig(by):
    cats = ["two-component (i + o)", "unimolecular (u)", "i-spanin only", "other", "no confident spanin"]
    cols = ["#1b5e20", "#8d6e63", "#a5d6a7", "#c9c9c9", "#eeeeee"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.6, 4.6), gridspec_kw={"width_ratios": [2.0, 1]})
    stacked(a1, by, cats, cols, lambda r: r.get("spanin_type_signalp") or "no confident spanin",
            "spanin type (lipoproteins by SignalP 6.0, helices by our predictor)")
    a1.set_yticklabels(ylabels(by), fontsize=8.5)
    h, l = a1.get_legend_handles_labels()
    a1.legend(h[:4] + [h[4]], ["two-component (i-spanin + o-spanin)", "unimolecular (u-spanin)", "i-spanin, no partner found",
              "other", "no confident spanin"], loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False, fontsize=8)
    sub = {s: [r for r in by[s] if r.get("endolysin_SAR")] for s in SETS}
    stacked(a2, sub, ["SAR (both)", "SAR, ours only", "SAR, DeepTMHMM only", "canonical (both)"],
            ["#C8553D", "#e8a596", "#b0b0b0", "#f2efee"], lambda r: r["endolysin_SAR"], "SAR endolysins: two tools")
    a2.set_yticklabels([]); a2.set_xlabel("% of confident endolysin calls")
    a2.legend(["both tools", "ours only", "DeepTMHMM only", "canonical (both)"], loc="upper center",
              bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False, fontsize=8)
    a2.xaxis.grid(True, color=GRID); a2.set_axisbelow(True)
    fig.suptitle("Spanin types and SAR endolysins by phage family", x=0.01, ha="left", fontsize=12, y=1.0)
    return save(fig, OUT / "7_spanin_types_SAR.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True); by = load()
    ok = [heatmap(by), endolysin_fig(by), spanin_fig(by), holin_fig(by), cassette_fig(by), holin_topology_fig(by),
          spanin_type_fig(by)]
    print(f"{sum(ok)}/{len(ok)} figures passed the overlap check; written to {OUT.relative_to(B)}")


if __name__ == "__main__":
    main()
