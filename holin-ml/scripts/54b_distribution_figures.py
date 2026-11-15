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
    by = defaultdict(list)
    for r in R: by[r["set"]].append(r)
    return by


def frac(rows, f):
    return 100.0 * sum(1 for r in rows if f(r)) / len(rows) if rows else np.nan


def ylabels(by):
    return [f"{SHORT[s]}  (n={len(by[s])}, {np.median([float(r['genome_kb']) for r in by[s]]):.0f} kb)" for s in SETS]


def heatmap(by):
    feats = [  # (column label, group, function over a genome row; denominators are all genomes of the family)
        ("co-located", "cassette", lambda r: r["cassette"] == "co-located"),
        ("dispersed", "cassette", lambda r: r["cassette"] == "dispersed"),
        ("incomplete", "cassette", lambda r: r["cassette"] == "incomplete"),
        ("known Pfam\nholin family", "holin", lambda r: r.get("holin_pfam") not in ("", "none", None)),
        ("≥ 2 strong\nholin genes", "holin", lambda r: int(r["holin_copies_P90"]) >= 2),
        ("glycosidase", "endolysin", lambda r: r.get("endolysin_class") == "glycosidase"),
        ("transglyco-\nsylase", "endolysin", lambda r: r.get("endolysin_class") == "transglycosylase"),
        ("amidase", "endolysin", lambda r: r.get("endolysin_class") == "amidase"),
        ("peptidase", "endolysin", lambda r: r.get("endolysin_class") == "peptidase"),
        ("no domain\ndetected", "endolysin", lambda r: r.get("endolysin_class") == "no domain detected"),
        ("cell-wall\nbinding", "endolysin", lambda r: r.get("endolysin_binding") == "True"),
        ("SAR-like\nN terminus", "endolysin", lambda r: r.get("endolysin_SAR") == "True"),
        ("embedded", "spanin", lambda r: r.get("spanin_arch") == "embedded"),
        ("overlapping", "spanin", lambda r: r.get("spanin_arch") == "overlapping"),
        ("separate", "spanin", lambda r: r.get("spanin_arch") == "separate"),
        ("single gene", "spanin", lambda r: r.get("spanin_arch") == "single"),
        ("none\nconfident", "spanin", lambda r: r.get("spanin_arch") == "no confident spanin"),
        ("lipobox", "spanin", lambda r: r.get("spanin_lipobox") == "True")]
    M = np.array([[frac(by[s], f) for _, _, f in feats] for s in SETS])
    fig, ax = plt.subplots(figsize=(14.5, 5.4))
    cmap = plt.get_cmap("Greys")
    ax.imshow(M, cmap=cmap, vmin=0, vmax=140, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8.5, color="white" if v > 75 else INK)
    ax.set_xticks(range(len(feats)))
    ax.set_xticklabels([l.replace("\n", " ").replace("- ", "") for l, _, _ in feats], fontsize=8.5, rotation=90,
                       ha="center", va="bottom")
    ax.set_yticks(range(len(SETS))); ax.set_yticklabels(ylabels(by), fontsize=9)
    ax.tick_params(length=0); ax.xaxis.tick_top()
    for sp in ax.spines.values(): sp.set_visible(False)
    groups = [(g, [j for j, (_, gg, _) in enumerate(feats) if gg == g]) for g in ("cassette", "holin", "endolysin", "spanin")]
    for g, js in groups:
        c = COL.get(g, INK)
        ax.annotate("", xy=(js[0] - 0.4, len(SETS) - 0.35), xytext=(js[-1] + 0.4, len(SETS) - 0.35),
                    arrowprops=dict(arrowstyle="-", color=c, lw=2.5), annotation_clip=False)
        ax.text((js[0] + js[-1]) / 2, len(SETS) + 0.15, g, ha="center", va="top", fontsize=10, color=c, fontweight="bold")
        if js[0] > 0: ax.axvline(js[0] - 0.5, color="white", lw=3)
    ax.set_ylim(len(SETS) + 0.5, -0.5)
    ax.set_title("The lysis toolkit of each phage family, as called from DNA (% of genomes)", loc="left",
                 fontsize=12, pad=118, x=-0.22)
    return save(fig, OUT / "1_toolkit_heatmap.png")


def stacked(ax, by, cats, colors, key, title):
    left = np.zeros(len(SETS))
    for c, col in zip(cats, colors):
        v = np.array([frac(by[s], lambda r: key(r) == c) for s in SETS])
        ax.barh(range(len(SETS)), v, left=left, color=col, height=0.7, label=c, edgecolor="white", linewidth=0.6)
        for i, (l, w) in enumerate(zip(left, v)):
            if w >= 9: ax.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", fontsize=7.5,
                               color="white" if col not in ("#d9d9d9", "#eeeeee", "#c9c9c9") else INK)
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
    sar = [frac([r for r in by[s] if r.get("endolysin_class")], lambda r: r["endolysin_SAR"] == "True") for s in SETS]
    a2.barh(y - 0.18, b, 0.34, color=COL["endolysin"], label="cell-wall-binding domain")
    a2.barh(y + 0.18, sar, 0.34, color=COL["endolysin"], alpha=0.4, label="SAR-like N terminus (lower bound)")
    for i in range(len(SETS)):
        a2.text(b[i] + 1, y[i] - 0.18, f"{b[i]:.0f}", va="center", fontsize=7.5)
        a2.text(sar[i] + 1, y[i] + 0.18, f"{sar[i]:.0f}", va="center", fontsize=7.5)
    a2.set_yticks(y); a2.set_yticklabels([]); a2.invert_yaxis(); a2.set_xlim(0, 60)
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
            if w >= 9: ax_c = "white" if col in ("#2171b5", "#08306b") else INK; a2.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", fontsize=7.5, color=ax_c)
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
            if w >= 12: a2.text(l + w / 2, i, f"{w:.0f}", ha="center", va="center", fontsize=7.5, color="white")
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


def main():
    OUT.mkdir(parents=True, exist_ok=True); by = load()
    ok = [heatmap(by), endolysin_fig(by), spanin_fig(by), holin_fig(by), cassette_fig(by)]
    print(f"{sum(ok)}/{len(ok)} figures passed the overlap check; written to {OUT.relative_to(B)}")


if __name__ == "__main__":
    main()
