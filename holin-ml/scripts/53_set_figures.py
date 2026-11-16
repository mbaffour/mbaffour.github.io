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


def _lum(c):
    import matplotlib.colors as mc
    r, g, b, a = mc.to_rgba(c)
    r, g, b = (a * x + (1 - a) for x in (r, g, b))            # blend on a white background
    f = lambda x: x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(c1, c2):
    """WCAG contrast ratio between two colours (1 = none, 21 = black on white)"""
    l1, l2 = sorted((_lum(c1), _lum(c2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def ink_on(face):
    """text colour for a label printed on a bar of colour `face`: whichever of white / dark ink contrasts more"""
    return "white" if contrast("white", face) >= contrast(INK, face) else INK


def drawn_texts(fig):
    """the text artists matplotlib actually draws: every visible non-tick text, plus only the tick labels of ticks
    inside each axis's view (findobj also returns labels of ticks outside the limits, which are never drawn)"""
    tick_lbls, keep = set(), []
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for tk in axis.get_major_ticks() + axis.get_minor_ticks():
                tick_lbls |= {id(tk.label1), id(tk.label2)}
            for tk in axis._update_ticks():
                keep += [l for l in (tk.label1, tk.label2) if l.get_visible() and l.get_text().strip()]
    others = [t for t in fig.findobj(matplotlib.text.Text)
              if id(t) not in tick_lbls and t.get_visible() and t.get_text().strip()]
    return others + keep


def text_overlaps(fig, pad=1.0):
    """Every pair of drawn text labels whose rendered boxes overlap (display pixels, after drawing). Labels outside
    the nominal canvas are not flagged: figures are saved with a tight bounding box, which keeps them."""
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    boxes = [(t, t.get_window_extent(r)) for t in drawn_texts(fig)]
    bad = []
    for i in range(len(boxes)):
        a, ba = boxes[i]
        for j in range(i + 1, len(boxes)):
            b, bb = boxes[j]
            if ba.x0 < bb.x1 - pad and bb.x0 < ba.x1 - pad and ba.y0 < bb.y1 - pad and bb.y0 < ba.y1 - pad:
                bad.append(("overlap", a.get_text(), b.get_text()))
    return bad


def obstructions(fig, pad=1.5):
    """Text or legends drawn ON TOP of data, hiding part of it. For every annotation text, every legend and the
    titles, checks the rendered box against every data artist in every axes:
      bars / boxes   a text may sit inside the ONE bar it labels (box fully inside that bar); touching any other bar,
                     or only partly covering one (a number wider than its stacked segment), is an obstruction
      lines          error bars, whiskers, reference lines and plotted lines crossing a text box
      points         scatter points inside a text box
    Images (heatmap cells) are not checked: their numbers are meant to be printed on them."""
    from matplotlib.transforms import Bbox
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    def area(a, b):
        w = min(a.x1, b.x1) - max(a.x0, b.x0); h = min(a.y1, b.y1) - max(a.y0, b.y0)
        return w * h if w > pad and h > pad else 0.0
    data, clipped = [], []
    for ax in fig.axes:
        for p in ax.patches:
            if p.get_visible() and p is not ax.patch:
                bb = p.get_window_extent(r)
                if bb.width > 0.5 and bb.height > 0.5:
                    ab = ax.bbox
                    if p.get_clip_on():
                        if bb.x1 > ab.x1 + 2 or bb.x0 < ab.x0 - 2 or bb.y1 > ab.y1 + 2 or bb.y0 < ab.y0 - 2: clipped.append(ax)
                        bb = Bbox.intersection(bb, ab)          # only the drawn part can cover anything
                        if bb is None: continue
                    data.append(("bar", p, bb))
        for l in ax.lines:
            if l.get_visible() and len(l.get_xdata()) > 0: data.append(("line", l, ax))
        for c in ax.collections:
            if c.get_visible(): data.append(("points" if isinstance(c, matplotlib.collections.PathCollection) else "line", c, ax))
    items = [(t.get_text().strip().replace("\n", " ")[:40], t.get_window_extent(r)) for ax in fig.axes for t in ax.texts
             if t.get_visible() and t.get_text().strip()]
    colour_of = {t.get_text().strip().replace("\n", " ")[:40] + str(t.get_window_extent(r).bounds): t.get_color()
                 for ax in fig.axes for t in ax.texts if t.get_visible() and t.get_text().strip()}
    items += [(f"title {t.get_text()[:30]!r}", t.get_window_extent(r)) for ax in fig.axes for t in (ax.title, ax._left_title, ax._right_title)
              if t.get_visible() and t.get_text().strip()]
    if fig._suptitle is not None and fig._suptitle.get_text().strip():
        items.append((f"suptitle {fig._suptitle.get_text()[:30]!r}", fig._suptitle.get_window_extent(r)))
    # tick labels and axis labels sit outside their own axes; check them against every axes' data (a neighbouring
    # panel's bars can run under them)
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for tk in axis._update_ticks():
                for l in (tk.label1, tk.label2):
                    if l.get_visible() and l.get_text().strip(): items.append((f"tick {l.get_text()[:25]!r}", l.get_window_extent(r)))
            lab = axis.label
            if lab.get_visible() and lab.get_text().strip(): items.append((f"axis label {lab.get_text()[:25]!r}", lab.get_window_extent(r)))
    legs = [ax.get_legend() for ax in fig.axes if ax.get_legend()] + list(fig.legends)
    items += [("legend", lg.get_window_extent(r)) for lg in legs if lg.get_visible()]
    bad = []
    for name, tb in items:
        tb_in = Bbox.from_extents(tb.x0 + pad, tb.y0 + pad, tb.x1 - pad, tb.y1 - pad)
        bars = [(p, bb, area(tb, bb)) for kind, p, bb in data if kind == "bar"]
        hits = [(p, bb, a) for p, bb, a in bars if a > 0]
        host = [p for p, bb, a in hits if bb.x0 - pad <= tb.x0 and tb.x1 <= bb.x1 + pad and bb.y0 - pad <= tb.y0 and tb.y1 <= bb.y1 + pad]
        if name == "legend" or name.startswith(("title", "suptitle", "tick", "axis label")): host = []
        others = [p for p, bb, a in hits if not host or p is not host[0]]
        if others: bad.append(("covers a bar", name, f"{len(others)} bar(s)"))
        tc = colour_of.get(name + str(tb.bounds))
        if host and tc is not None and contrast(tc, host[0].get_facecolor()) < 3.0:
            bad.append(("low contrast on its bar", name, f"ratio {contrast(tc, host[0].get_facecolor()):.1f}"))
        for kind, a_, ax_ in data:
            if kind == "bar": continue
            # only the part of an artist that is actually drawn: clipped artists end at their axes
            box = Bbox.intersection(tb_in, ax_.bbox) if a_.get_clip_on() else tb_in
            if box is None: continue
            if kind == "line":
                paths = [a_.get_transform().transform_path(a_.get_path())] if isinstance(a_, matplotlib.lines.Line2D) else \
                        [a_.get_transform().transform_path(pth) for pth in a_.get_paths()]
                if any(pth.intersects_bbox(box) for pth in paths): bad.append(("covers a line", name, "")); break
            elif kind == "points":
                off = a_.get_offset_transform().transform(a_.get_offsets()) if len(a_.get_offsets()) else []
                if any(box.contains(x, y) for x, y in off): bad.append(("covers data points", name, "")); break
    for ax in dict.fromkeys(clipped):
        bad.append(("data clipped by the axis limits", ax.get_title() or "panel", ""))
    return bad


def save(fig, path):
    """save, refusing silently-broken layouts: report overlapping text, and text or legends hiding data"""
    bad = text_overlaps(fig) + obstructions(fig)
    for kind, a, b in bad: print(f"  LAYOUT {path.name}: {kind}: {a[:40]!r} {('x ' + repr(b[:40])) if b else ''}")
    fig.savefig(path); plt.close(fig)
    return not bad


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
    save(fig, out / "1_agreement.png")


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
        ns = [st.get(o, {"n": 0})["n"] for o in order]
        ax.set_xticks(range(3)); ax.set_xticklabels([f"{lb}\nn = {n_}" for lb, n_ in zip(short, ns)], fontsize=8)
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("identity to the closest training gene", fontsize=8.5, color=MUTED)
        ax.set_title(c, color=COL[c], fontweight="bold", fontsize=10); ax.yaxis.grid(True, color=GRID); ax.set_axisbelow(True)
    axs[0].set_ylabel("fraction of annotated genes")
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=MUTED), Patch(color=MUTED, alpha=0.35)], labels=["call is that gene", "in top 5"],
               loc="upper left", frameon=False, fontsize=8.5, ncol=2, bbox_to_anchor=(0.005, 1.04))
    fig.suptitle(f"{LABEL.get(s, s)}: agreement by how similar each annotated gene is to the training data", x=0.01,
                 ha="left", fontsize=11, color=INK, y=1.12)
    save(fig, out / "2_novelty.png")


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
    save(fig, out / "3_cassette.png")


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
    a1.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
    a1.grid(True, color=GRID); a1.set_axisbelow(True)
    a1.set_title(f"{len(adj)} of {len(pts)} disagreements: the pick is the\nannotated holin's neighbour", fontsize=9.5, loc="left")
    rk = Counter(min(p[3], 6) for p in pts)
    a2.bar(list(rk), [rk[k] for k in rk], color=COL["holin"], alpha=0.7, width=0.7)
    a2.set_xticks([1, 2, 3, 4, 5, 6]); a2.set_xticklabels(["1", "2", "3", "4", "5", "6+"])
    a2.set_xlabel("rank of the annotated holin"); a2.set_ylabel("genomes")
    a2.set_title("where the annotated holin ranks instead", fontsize=9.5, loc="left"); a2.yaxis.grid(True, color=GRID); a2.set_axisbelow(True)
    fig.suptitle(f"{LABEL.get(s, s)}: two adjacent holin-family genes", x=0.01, ha="left", fontsize=11, y=1.04)
    save(fig, out / "4_holin_pair.png")
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
            if not M[c][m]:
                ax.text(0.02, k, "none annotated" + (" (Gram-positive hosts: no outer membrane)" if s == "herelle" else ""),
                        va="center", fontsize=7.5, color=MUTED, style="italic")
                continue
            v, lo, hi = boot(M[c][m]); t5 = np.mean(M[c]["top5"]) if M[c]["top5"] else np.nan
            ax.barh(k, t5, color=COL[c], alpha=0.25, height=0.7)
            ax.barh(k, v, color=COL[c], height=0.42)
            ax.errorbar(v, k, xerr=[[v - lo], [hi - v]], fmt="none", ecolor=INK, elinewidth=0.8, capsize=1.5)
            ax.text(1.06, k, f"{len(M[c]['call'])}", va="center", fontsize=7.5, color=MUTED)
        ax.set_xlim(0, 1.15); ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0]); ax.xaxis.grid(True, color=GRID); ax.set_axisbelow(True)
        ax.set_title(c + (" (pair level)" if c == "spanin" else ""), color=COL[c], fontweight="bold", fontsize=10)
    axs[0].set_yticks(range(len(rows)))
    axs[0].set_yticklabels([f"{LABEL.get(s, s)}  ({n})" for s, n, _, _ in rows], fontsize=8.5); axs[0].invert_yaxis()
    axs[1].set_xlabel("dark: the call is the annotated gene (95% CI)   ·   light: annotated gene in the top 5   ·   "
                      "grey number: genomes with that gene annotated", fontsize=8.5)
    fig.suptitle("Blind lysis-gene calls from DNA, scored against each group's annotations", x=0.01, ha="left",
                 fontsize=11.5, y=1.0)
    save(fig, out / "groups_agreement.png")
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
