"""Figures for a blind phage-group scan (scripts/52a-c): one set, or a comparison across sets.

Per set (reports/<set>/figures/):
  1_agreement.png   per class: the one call is the annotated gene / annotated gene in top 2 / in top 5
                    (spanin also at pair level: the call is the annotated spanin or overlaps it, i.e. its partner)
  2_novelty.png     call correct, split by the annotated gene's identity to that class's training positives
  3_cassette.png    gene order of co-located confident calls, and how many genes the three calls span
  4_holin_pair.png  (when the model's holin pick is often the annotated holin's neighbour) P of each, per genome
Comparison (reports/figures/groups_*.png): the same measures side by side for several sets.

Usage: python3 scripts/53_set_figures.py n4
       python3 scripts/53_set_figures.py --compare n4 lambda t4 t7 t5 drexler herelle p2 jumbo
"""
import argparse, importlib, json, re, sys
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
S5 = importlib.import_module("05_scan_genome")
SC = importlib.import_module("52c_score_blind")
CLASSES = ("holin", "endolysin", "spanin")
COL = {"holin": "#3B6EA8", "endolysin": "#C8553D", "spanin": "#5B8E5A"}
INK, MUTED, GRID = "#1f2328", "#6b7280", "#e5e7eb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 100, "savefig.dpi": 200, "savefig.bbox": "tight"})
LABEL = {"n4": "N4-like (Schitoviridae)", "lambda": "Lambdoid (λ, P22, HK97-like)", "t4": "T4-like (Straboviridae)",
         "t7": "T7-like (Autographiviridae)", "t5": "T5-like (Demerecviridae)", "drexler": "Drexlerviridae",
         "herelle": "Herelleviridae", "p2": "P2-like (Peduoviridae)", "jumbo": "Jumbo (> 200 kb)",
         "blind": "Recent genomes, set 1", "blind2": "Recent genomes, set 2"}


def boot(x, n=2000, seed=0):
    x = np.asarray(x, float)
    if not len(x): return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed); m = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(n)]
    return x.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


def key(r): return (r["strand"], int(r["stop"]) if r["strand"] == "+" else int(r["start"]))


def load_set(s):
    """per-genome records: predictions, annotation labels per row, calls"""
    sel = json.load(open(B / f"data/raw/{s}/selection.json"))["accessions"]
    G = []
    for acc in sel:
        pf = B / f"reports/{s}/pred/{acc}.tsv"
        if not pf.exists(): continue
        L = pf.read_text().splitlines(); h = L[0].split("\t"); R = [dict(zip(h, l.split("\t"))) for l in L[1:] if l.strip()]
        ann = {(x["strand"], x["stop"] if x["strand"] == "+" else x["start"]): x
               for x in S5.annotated_proteins(B / f"data/raw/{s}/sealed/{acc}.gb")}
        lab = [SC.labels(((ann.get(key(r)) or {}).get("product") or "")) for r in R]
        calls = {}
        for i, r in enumerate(R):
            for x in r["lysis_call"].split(","):
                if x: c, t = x.split(":"); calls[c] = (i, t)
        G.append({"acc": acc, "rows": R, "lab": lab, "calls": calls})
    return G


def measures(G):
    """per class: lists of per-genome booleans over genomes whose annotation has the class"""
    M = {}
    for c in CLASSES:
        m = {"call": [], "top2": [], "top5": [], "pair": []}
        for g in G:
            hits = [i for i, l in enumerate(g["lab"]) if c in l]
            if not hits: continue
            R = g["rows"]; best = min(int(R[i][f"rank_{c}"]) for i in hits)
            m["top2"].append(best <= 2); m["top5"].append(best <= 5)
            if c not in g["calls"]:                    # no call at all counts as a miss (as in scripts/52c)
                m["call"].append(False); m["pair"].append(False); continue
            ci = g["calls"][c][0]
            m["call"].append(ci in hits)
            s0, e0 = int(R[ci]["start"]), int(R[ci]["stop"])
            m["pair"].append(ci in hits or any(min(e0, int(R[j]["stop"])) - max(s0, int(R[j]["start"])) > 0 for j in hits))
        M[c] = m
    return M


def fig_agreement(s, M, out):
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    bars = [("call", "the call is the annotated gene"), ("top2", "annotated gene in top 2"), ("top5", "annotated gene in top 5")]
    y0 = 0.6; ticks = []
    for c in CLASSES:
        ax.text(0.0, y0 - 0.95, f"{c}  ·  {len(M[c]['call'])} genomes annotate one", fontsize=9.5, color=COL[c],
                fontweight="bold", va="center")
        rows = bars + ([("pair", "call is the annotated spanin or its partner")] if c == "spanin" else [])
        for k, (m, lbl) in enumerate(rows):
            v, lo, hi = boot(M[c][m]); y = y0 + k
            alpha = [1.0, 0.55, 0.3, 0.8][k]
            ax.barh(y, v, color=COL[c], alpha=alpha, height=0.72)
            ax.errorbar(v, y, xerr=[[v - lo], [hi - v]], fmt="none", ecolor=INK, elinewidth=0.9, capsize=2)
            ax.text(min(hi + 0.012, 1.005), y, f"{v:.2f}", va="center", fontsize=8.5, color=INK)
            ticks.append((y, lbl))
        y0 += len(rows) + 1.4
    ax.set_yticks([t for t, _ in ticks]); ax.set_yticklabels([l for _, l in ticks], fontsize=8.5)
    ax.tick_params(axis="y", pad=4, length=0)
    ax.set_xlim(0, 1.08); ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    ax.set_xlabel("fraction of genomes whose annotation has the gene (95% bootstrap CI)")
    ax.set_title(f"{LABEL.get(s, s)}: blind calls from DNA vs the genomes' annotations", loc="left", fontsize=11, color=INK)
    ax.set_ylim(y0 - 1.2, -0.9)
    fig.savefig(out / "1_agreement.png"); plt.close(fig)


def fig_novelty(s, out):
    sc = json.load(open(B / f"reports/{s}/score.json"))["classes"]
    order = ["near-copy (>=95%)", "known family (30-95%)", "new family (<30%)"]
    short = ["≥ 95%\nnear-copy", "30–95%\nknown family", "< 30%\nnew family"]
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.2), sharey=True)
    for ax, c in zip(axs, CLASSES):
        st = sc[c].get("by_novelty", {})
        for k, o in enumerate(order):
            d = st.get(o, {"n": 0, "call_correct": 0, "top5": 0}); n = d["n"]
            if n:
                ax.bar(k - 0.18, d["call_correct"] / n, 0.34, color=COL[c])
                ax.bar(k + 0.18, d["top5"] / n, 0.34, color=COL[c], alpha=0.35)
            ax.text(k, 1.03, f"n={n}", ha="center", fontsize=8, color=MUTED)
        ax.set_xticks(range(3)); ax.set_xticklabels(short, fontsize=8); ax.set_ylim(0, 1.1)
        ax.set_xlabel("identity to the closest training gene", fontsize=8.5, color=MUTED)
        ax.set_title(c, color=COL[c], fontweight="bold", fontsize=10); ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    axs[0].set_ylabel("fraction of annotated genes")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=MUTED), Patch(color=MUTED, alpha=0.35)], labels=["call is that gene", "in top 5"],
               loc="upper left", frameon=False, fontsize=8.5, ncol=2, bbox_to_anchor=(0.005, 1.04))
    fig.suptitle(f"{LABEL.get(s, s)}: agreement by how similar each annotated gene is to the training data", x=0.01,
                 ha="left", fontsize=11, color=INK, y=1.12)
    fig.savefig(out / "2_novelty.png"); plt.close(fig)


def fig_cassette(s, G, out):
    orders, spans = Counter(), []
    for g in G:
        cs = g["calls"]
        if not all(cs.get(c, (0, ""))[1] == "confident" for c in CLASSES): continue
        idx = {c: cs[c][0] for c in CLASSES}; span = max(idx.values()) - min(idx.values()); spans.append(span)
        if span <= 6:
            st = g["rows"][idx["endolysin"]]["strand"]
            orders["–".join(c[0].upper() for c in sorted(idx, key=lambda c: idx[c] if st == "+" else -idx[c]))] += 1
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.0), gridspec_kw={"width_ratios": [1.15, 1]})
    top = orders.most_common(6)
    if top:
        a1.barh(range(len(top)), [v for _, v in top], color="#7a7a8c", height=0.65)
        a1.set_yticks(range(len(top))); a1.set_yticklabels([k for k, _ in top], fontsize=9.5, family="DejaVu Sans Mono")
        a1.invert_yaxis()
        for i, (_, v) in enumerate(top): a1.text(v, i, f" {v}", va="center", fontsize=8.5)
    a1.set_xlabel("genomes"); a1.set_title("order, in the direction of transcription\n(H holin · E endolysin · S spanin)",
                                           fontsize=9.5, loc="left", color=INK)
    a1.xaxis.grid(True, color=GRID); a1.set_axisbelow(True)
    if spans:
        cap = 15; v = np.minimum(spans, cap)
        a2.hist(v, bins=np.arange(-0.5, cap + 1.5, 1), color="#7a7a8c")
        a2.set_xticks([0, 2, 4, 6, 8, 10, 12, 14]); a2.axvline(6.5, color=INK, lw=0.8, ls="--")
        a2.text(6.7, a2.get_ylim()[1] * 0.92, "co-located\n(≤ 6 genes)", fontsize=8, color=MUTED, va="top")
    a2.set_xlabel(f"genes spanned by the three calls ({cap} = {cap} or more)"); a2.set_ylabel("genomes")
    a2.set_title("how tightly the three calls cluster", fontsize=9.5, loc="left", color=INK)
    n3 = len(spans); nco = sum(x <= 6 for x in spans)
    fig.suptitle(f"{LABEL.get(s, s)}: lysis cassettes found from DNA\n"
                 f"all three genes confident in {n3} of {len(G)} genomes; co-located in {nco}", x=0.01, ha="left",
                 fontsize=11, color=INK, y=1.16, linespacing=1.5)
    fig.savefig(out / "3_cassette.png"); plt.close(fig)


def fig_holin_pair(s, G, out):
    pts = []
    for g in G:
        hits = [i for i, l in enumerate(g["lab"]) if "holin" in l]
        if not hits or "holin" not in g["calls"]: continue
        ci = g["calls"]["holin"][0]
        if ci in hits: continue
        R = g["rows"]; j = min(hits, key=lambda j: int(R[j]["rank_holin"]))
        pts.append((float(R[ci]["P_holin"]), float(R[j]["P_holin"]), abs(ci - j) == 1, int(R[j]["rank_holin"])))
    if len(pts) < 5: return False
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.3), gridspec_kw={"width_ratios": [1.2, 1]})
    adj = [p for p in pts if p[2]]; far = [p for p in pts if not p[2]]
    a1.scatter([p[1] for p in adj], [p[0] for p in adj], s=22, color=COL["holin"], label="neighbour of the annotated holin")
    if far: a1.scatter([p[1] for p in far], [p[0] for p in far], s=22, facecolor="none", edgecolor=COL["holin"], label="elsewhere")
    a1.plot([0, 1], [0, 1], color=MUTED, lw=0.8, ls="--"); a1.set_xlim(-0.02, 1.02); a1.set_ylim(-0.02, 1.02)
    a1.set_xlabel("P(holin), gene the annotation calls holin"); a1.set_ylabel("P(holin), the model's pick")
    a1.legend(frameon=False, fontsize=8, loc="lower right"); a1.grid(True, color=GRID); a1.set_axisbelow(True)
    a1.set_title(f"{len(adj)} of {len(pts)} disagreements: the pick is the\nannotated holin's neighbour", fontsize=9.5, loc="left")
    rk = Counter(min(p[3], 6) for p in pts)
    a2.bar(list(rk), [rk[k] for k in rk], color=COL["holin"], alpha=0.7, width=0.7)
    a2.set_xticks([1, 2, 3, 4, 5, 6]); a2.set_xticklabels(["1", "2", "3", "4", "5", "6+"])
    a2.set_xlabel("rank of the annotated holin"); a2.set_ylabel("genomes")
    a2.set_title("where the annotated holin ranks instead", fontsize=9.5, loc="left"); a2.yaxis.grid(True, color=GRID); a2.set_axisbelow(True)
    fig.suptitle(f"{LABEL.get(s, s)}: two adjacent holin-family genes", x=0.01, ha="left", fontsize=11, y=1.04)
    fig.savefig(out / "4_holin_pair.png"); plt.close(fig)
    return True


def compare(sets):
    out = B / "reports/figures"; out.mkdir(parents=True, exist_ok=True)
    rows = []
    for s in sets:
        if not (B / f"reports/{s}/score.json").exists(): continue
        G = load_set(s); M = measures(G)
        n3 = sum(all(g["calls"].get(c, (0, ""))[1] == "confident" for c in CLASSES) for g in G)
        rows.append((s, len(G), M, n3))
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 0.42 * len(rows) + 1.6), sharey=True)
    for ax, c in zip(axs, CLASSES):
        for k, (s, n, M, _) in enumerate(rows):
            m = "pair" if c == "spanin" else "call"
            v, lo, hi = boot(M[c][m]); t5 = np.mean(M[c]["top5"]) if M[c]["top5"] else np.nan
            ax.barh(k, t5, color=COL[c], alpha=0.25, height=0.7)
            ax.barh(k, v, color=COL[c], height=0.42)
            ax.errorbar(v, k, xerr=[[v - lo], [hi - v]], fmt="none", ecolor=INK, elinewidth=0.8, capsize=1.5)
            ax.text(1.01, k, f"{len(M[c]['call'])}", va="center", fontsize=7.5, color=MUTED)
        ax.set_xlim(0, 1.08); ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
        ax.set_title(c + (" (pair level)" if c == "spanin" else ""), color=COL[c], fontweight="bold", fontsize=10)
    axs[0].set_yticks(range(len(rows)))
    axs[0].set_yticklabels([f"{LABEL.get(s, s)}  ({n})" for s, n, _, _ in rows], fontsize=8.5); axs[0].invert_yaxis()
    axs[1].set_xlabel("dark: the call is the annotated gene (95% CI)   ·   light: annotated gene in the top 5   ·   "
                      "grey number: genomes with that gene annotated", fontsize=8.5)
    fig.suptitle("Blind lysis-gene calls from DNA, scored against each group's annotations", x=0.01, ha="left",
                 fontsize=11.5, y=1.0)
    fig.savefig(out / "groups_agreement.png"); plt.close(fig)
    summ = {s: {"genomes": n, "all_three_confident": n3,
                **{f"{c}_{m}": round(float(np.mean(M[c][m])), 3) if M[c][m] else None
                   for c in CLASSES for m in ("call", "top5", "pair")},
                **{f"{c}_n": len(M[c]["call"]) for c in CLASSES}} for s, n, M, n3 in rows}
    (out / "groups_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("set", nargs="?"); ap.add_argument("--compare", nargs="+")
    a = ap.parse_args()
    if a.compare: compare(a.compare); return
    s = a.set; out = B / f"reports/{s}/figures"; out.mkdir(parents=True, exist_ok=True)
    G = load_set(s); M = measures(G)
    fig_agreement(s, M, out); fig_novelty(s, out); fig_cassette(s, G, out)
    hp = fig_holin_pair(s, G, out)
    print(f"{s}: figures in {out.relative_to(B)} ({'with' if hp else 'no'} holin-pair figure)")


if __name__ == "__main__":
    main()
