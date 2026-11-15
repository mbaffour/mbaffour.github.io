"""Compare our transmembrane predictor (scripts/55) with DeepTMHMM and SignalP 6.0 (scripts/56) on the lysis proteins.

1. Benchmark on the 59 Swiss-Prot phage lysis proteins with curated helices: exact helix count for ours, DeepTMHMM and
   the hydropathy heuristic; the reference holins (lambda S, T4 t, pinholins) individually.
2. Holin class per phage family by DeepTMHMM next to ours, and how often the two agree.
3. SignalP 6.0 on the spanin members and endolysins: LIPO (lipoprotein, Sec/SPII) vs our lipobox rule; what SignalP
   says about SAR endolysins and i-spanins (signal anchors).
Output: reports/external/comparison.json, reports/external/comparison.md, figures in reports/external/figures/
Usage: python3 scripts/56b_compare_predictors.py
"""
import glob, importlib, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
import genecall as G
TM = importlib.import_module("55_tm_predictor")
B = Path(__file__).resolve().parent.parent
OUT = B / "reports/external"
SETS = ["n4", "lambda", "p2", "drexler", "t7", "t5", "t4", "herelle", "jumbo"]
SHORT = {"n4": "N4-like", "lambda": "Lambdoid", "t7": "T7-like", "p2": "P2-like", "drexler": "Drexlerviridae",
         "t5": "T5-like", "herelle": "Herelleviridae", "t4": "T4-like", "jumbo": "Jumbo"}


def read_deeptmhmm():
    """{id: {"type", "n", "nterm", "topology"}} from predicted_topologies.3line"""
    out = {}
    for f in glob.glob(str(OUT / "deeptmhmm/chunk_*/**/predicted_topologies.3line"), recursive=True):
        L = Path(f).read_text().splitlines()
        for i in range(0, len(L) - 2, 3):
            if not L[i].startswith(">"): continue
            pid, typ = L[i][1:].split(" | ")[0].strip(), L[i].split(" | ")[-1].strip()
            topo = L[i + 2].strip()
            n = len(re.findall(r"M+", topo))
            first = topo.lstrip("S")[:1]
            out[pid] = {"type": typ, "n": n, "nterm": {"I": "in", "O": "out", "P": "out"}.get(first), "topology": topo}
    return out


def read_signalp():
    out = {}
    for f in glob.glob(str(OUT / "signalp/chunk_*/**/prediction_results.txt"), recursive=True):
        for ln in Path(f).read_text().splitlines():
            if ln.startswith("#") or not ln.strip(): continue
            c = ln.split("\t"); out[c[0].split()[0]] = {"prediction": c[1],
                                                       "probs": [float(x) for x in c[2:8] if re.match(r"^[0-9.eE+-]+$", x)]}
    return out


def holin_class(n):
    return {1: "III", 2: "II", 3: "I"}.get(n, "none" if n == 0 else "4+")


def figures(res, ours, DT, SP, roles, seqs):
    FG = importlib.import_module("53_set_figures")
    plt, save, COL, INK, MUTED, GRID = FG.plt, FG.save, FG.COL, FG.INK, FG.MUTED, FG.GRID
    out = OUT / "figures"; out.mkdir(parents=True, exist_ok=True)
    cats = ["I", "II", "III", "none", "4+"]; cols = ["#08306b", "#2171b5", "#9ecae1", "#d9d9d9", "#6a51a3"]
    fig, ax = plt.subplots(figsize=(11.5, 6.2))
    y = 0; ticks = []
    for s in SETS:
        f = res["holins_by_family"][s]
        for tool, lab in (("ours", "ours"), ("deeptmhmm", "DeepTMHMM")):
            n = sum(f[tool].values()); left = 0
            for c, col in zip(cats, cols):
                w = 100 * f[tool].get(c, 0) / max(n, 1)
                ax.barh(y, w, left=left, color=col, height=0.8, edgecolor="white", linewidth=0.5,
                        label=(f"class {c}" if c in ("I", "II", "III") else c) if y == 0 else None)
                if w >= 9: ax.text(left + w / 2, y, f"{w:.0f}", ha="center", va="center", fontsize=7,
                                   color="white" if c in ("I", "II") else INK)
                left += w
            ticks.append((y, f"{SHORT[s]} · {lab}")); y += 1
        ax.text(101.5, y - 1.5, f"agree {100 * f['class_agreement']:.0f}%\n(n={f['n']})", va="center", fontsize=7.5, color=MUTED)
        y += 0.6
    ax.set_yticks([t for t, _ in ticks]); ax.set_yticklabels([l for _, l in ticks], fontsize=8); ax.invert_yaxis()
    ax.set_xlim(0, 113); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xlabel("% of confident holin calls")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.08), ncol=5, frameon=False, fontsize=8)
    ax.set_title("Holin class (number of membrane helices): our predictor vs DeepTMHMM, by phage family",
                 loc="left", fontsize=11.5)
    save(fig, out / "1_holin_class_ours_vs_deeptmhmm.png")
    # SignalP / DeepTMHMM on endolysins
    E = res["endolysins"]; rows = [s for s in SETS if s in E] + (["Swiss-Prot SAR endolysins"] if "Swiss-Prot SAR endolysins" in E else [])
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.6), sharey=True)
    spec = [("ours", ["SAR", "canonical"], ["#C8553D", "#f2d0c9"], "our call"),
            ("deeptmhmm", ["SP", "SP+TM", "TM", "GLOB"], ["#8c2d04", "#d94801", "#fd8d3c", "#eeeeee"], "DeepTMHMM type"),
            ("signalp", ["SP", "LIPO", "TAT", "OTHER"], ["#8c2d04", "#d94801", "#fd8d3c", "#eeeeee"], "SignalP 6.0")]
    for ax, (m, cs, cl, title) in zip(axs, spec):
        for i, s in enumerate(rows):
            c = E[s].get(m, {}); n = sum(c.values()); left = 0
            for cat, col in zip(cs, cl):
                w = 100 * c.get(cat, 0) / max(n, 1)
                ax.barh(i, w, left=left, color=col, height=0.7, edgecolor="white", linewidth=0.5, label=cat if i == 0 else None)
                if w >= 12: ax.text(left + w / 2, i, f"{w:.0f}", ha="center", va="center", fontsize=7,
                                    color="white" if col in ("#8c2d04", "#d94801", "#C8553D") else INK)
                left += w
        ax.set_xlim(0, 100); ax.set_title(title, loc="left", fontsize=10); ax.set_xlabel("% of called endolysins")
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=4, frameon=False, fontsize=7.5)
    axs[0].set_yticks(range(len(rows))); axs[0].set_yticklabels([SHORT.get(s, s) for s in rows], fontsize=8.5); axs[0].invert_yaxis()
    fig.suptitle("Endolysin N termini: our SAR call, DeepTMHMM and SignalP 6.0", x=0.01, ha="left", fontsize=12, y=1.0)
    save(fig, out / "2_endolysins_three_tools.png")


def main():
    seqs = {}
    cur = None
    for ln in (OUT / "input.fasta").read_text().splitlines():
        if ln.startswith(">"): cur = ln[1:]
        else: seqs[cur] = ln
    roles = json.loads((OUT / "mapping.json").read_text())
    DT, SP = read_deeptmhmm(), read_signalp()
    print(f"DeepTMHMM results for {len(DT)} of {len(seqs)} proteins; SignalP for {len(SP)}", flush=True)
    ours = {}
    for k, s in seqs.items():
        p = TM.predict([s])[0]; ours[k] = {"n": p["n"], "nterm": p["n_terminus"]}
    res = {"n_proteins": len(seqs), "n_deeptmhmm": len(DT), "n_signalp": len(SP)}

    # 1. curated benchmark
    bench = []
    for k, rs in roles.items():
        for r in rs:
            if "swissprot" in r and r["curated_tm"]:
                bench.append({"acc": r["swissprot"], "name": r["name"], "curated": len(r["curated_tm"]),
                              "ours": ours[k]["n"], "deeptmhmm": DT.get(k, {}).get("n"),
                              "heuristic": len(F.tm_segments(seqs[k])), "ours_nterm": ours[k]["nterm"],
                              "deeptmhmm_nterm": DT.get(k, {}).get("nterm"), "signalp": SP.get(k, {}).get("prediction")})
    def exact(key): v = [b for b in bench if b[key] is not None]; return round(sum(b[key] == b["curated"] for b in v) / max(len(v), 1), 3), len(v)
    res["curated_benchmark"] = {"proteins": len(bench), **{m: exact(m) for m in ("ours", "deeptmhmm", "heuristic")},
                                "ours_vs_deeptmhmm_helix_count_agree": round(np.mean([b["ours"] == b["deeptmhmm"] for b in bench if b["deeptmhmm"] is not None]), 3),
                                "rows": bench}
    print("curated benchmark (exact helix count):", {m: res["curated_benchmark"][m] for m in ("ours", "deeptmhmm", "heuristic")}, flush=True)

    # 2. holins by family, ours vs DeepTMHMM
    fam = {}
    for s in SETS:
        rows = [(k, r) for k, rs in roles.items() for r in rs if r.get("set") == s and r.get("role") == "holin" and k in DT]
        o = Counter(holin_class(ours[k]["n"]) for k, _ in rows); d = Counter(holin_class(DT[k]["n"]) for k, _ in rows)
        agree = np.mean([holin_class(ours[k]["n"]) == holin_class(DT[k]["n"]) for k, _ in rows]) if rows else np.nan
        nin_o = np.mean([ours[k]["nterm"] == "in" for k, _ in rows if ours[k]["nterm"]]) if rows else np.nan
        nin_d = np.mean([DT[k]["nterm"] == "in" for k, _ in rows if DT[k]["nterm"]]) if rows else np.nan
        fam[s] = {"n": len(rows), "ours": dict(o), "deeptmhmm": dict(d), "class_agreement": round(float(agree), 3),
                  "n_in_ours": round(float(nin_o), 3), "n_in_deeptmhmm": round(float(nin_d), 3)}
    res["holins_by_family"] = fam

    # 3. SignalP on spanins and endolysins
    sp = defaultdict(Counter)
    for k, rs in roles.items():
        if k not in SP: continue
        s = seqs[k]; lip = G.lipo_signal(s)
        for r in rs:
            role = r.get("role")
            if role in ("spanin", "spanin_partner"):
                h = ours[k]
                kind = ("lipobox (our rule)" if lip else "N-terminal helix (i-spanin-like)" if h["n"] else "neither")
                sp[f"spanin member, {kind}"][SP[k]["prediction"]] += 1
            elif role == "endolysin":
                _, sm = (None, None)
                sp["endolysin"][SP[k]["prediction"]] += 1
            elif role in ("holin", "holin2"):
                sp["holin"][SP[k]["prediction"]] += 1
            elif "swissprot" in r:
                nm = r["name"].lower()
                tag = ("Swiss-Prot o-spanin" if "outer" in nm and "spanin" in nm else "Swiss-Prot u-spanin" if "u-spanin" in nm
                       else "Swiss-Prot i-spanin" if "inner" in nm and "spanin" in nm else "Swiss-Prot SAR endolysin" if "sar-endolysin" in nm
                       else "Swiss-Prot holin/antiholin" if "holin" in nm else None)
                if tag: sp[tag][SP[k]["prediction"]] += 1
    res["signalp"] = {k: dict(v) for k, v in sp.items()}
    for k, v in sorted(res["signalp"].items()): print(f"  SignalP {k}: {v}", flush=True)
    # 4. endolysins and spanin members: our call vs DeepTMHMM type vs SignalP, per role and family
    T55b = importlib.import_module("55b_topology")
    endo = defaultdict(lambda: defaultdict(Counter))
    for k, rs in roles.items():
        for r in rs:
            if r.get("role") == "endolysin" and k in DT and k in SP:
                ours_t = T55b.endolysin_type(seqs[k])
                endo[r["set"]]["ours"][ours_t] += 1; endo[r["set"]]["deeptmhmm"][DT[k]["type"]] += 1
                endo[r["set"]]["signalp"][SP[k]["prediction"]] += 1
            if "swissprot" in r and "sar-endolysin" in r["name"].lower():
                endo["Swiss-Prot SAR endolysins"]["ours"][T55b.endolysin_type(seqs[k])] += 1
                if k in DT: endo["Swiss-Prot SAR endolysins"]["deeptmhmm"][DT[k]["type"]] += 1
                if k in SP: endo["Swiss-Prot SAR endolysins"]["signalp"][SP[k]["prediction"]] += 1
    res["endolysins"] = {s: {m: dict(c) for m, c in v.items()} for s, v in endo.items()}
    figures(res, ours, DT, SP, roles, seqs)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "comparison.json").write_text(json.dumps(res, indent=1))
    print("wrote reports/external/comparison.json")


if __name__ == "__main__":
    main()
