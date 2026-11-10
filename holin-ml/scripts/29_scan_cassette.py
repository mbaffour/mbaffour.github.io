"""Score every protein of a phage genome with the holin, endolysin and spanin models (independent probabilities)
and flag lysis cassettes where high-scoring holin + endolysin + spanin genes co-locate.

Feature pipeline is copied exactly from scripts/24_discover_novel.py / 28_train_eval_lysis.py:
  X = hstack([handcrafted(s) (36), ESM-2 embed (480)])  -> 516-d, built ONCE, scored by all three models.
Usage: python3 scripts/29_scan_cassette.py [--genomes lambda,T7,P22,HK97 | --gb file.gb] [--cassette-window 6] [--threshold 0.5]
"""
import argparse, importlib, itertools, json, os, pickle, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F

B = Path(__file__).resolve().parent.parent
DSC = "/home/user/mbaffour.github.io/dirty-science-canvas"
CLASSES = ["holin", "endolysin", "spanin"]
MODELS = {"holin": "holin_model_curated.pkl", "endolysin": "endolysin_model.pkl", "spanin": "spanin_model.pkl"}


def load_atlas(key):
    d = json.load(open(f"{DSC}/{key}_Topology_Lab_Reference/data.json"))
    ps = [{"id": r["protein_id"].split("|")[-1], "gene": r.get("gene") or "", "product": r.get("product") or "",
           "start": r["start"], "stop": r["stop"], "strand": r["strand"], "sequence": r["sequence"]} for r in d["proteins"]]
    return d.get("organism", key), ps


def load_gb(path):
    S = importlib.import_module("05_scan_genome")
    return Path(path).stem, S.annotated_proteins(path)


def find_cassettes(ps, thr, W):
    """ps sorted by position. A window = genes i..j with j-i <= W. It is a cassette if distinct genes can be chosen
    for holin, endolysin, spanin each with P>=thr. Overlapping qualifying windows are merged."""
    n = len(ps); spans = []
    for i in range(n):
        win = range(i, min(n, i + W + 1))
        cand = [[k for k in win if ps[k]["P"][c] >= thr] for c in CLASSES]
        if any(not c for c in cand): continue
        if any(len({a, b, c}) == 3 for a, b, c in itertools.product(*cand)):
            spans.append((i, min(n, i + W + 1) - 1))
    merged = []
    for s in spans:
        if merged and s[0] <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], s[1])
        else: merged.append(list(s))
    out = []
    for lo, hi in merged:
        members = [k for k in range(lo, hi + 1) if any(ps[k]["P"][c] >= thr for c in CLASSES)]
        out.append({"gene_index_range": [lo, hi], "members": [
            {"index": k, "gene": ps[k]["gene"] or ps[k]["id"], "id": ps[k]["id"], "product": ps[k]["product"],
             "P": ps[k]["P"], "classes_called": [c for c in CLASSES if ps[k]["P"][c] >= thr]} for k in members]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genomes", default="lambda,T7,P22,HK97")
    ap.add_argument("--gb")
    ap.add_argument("--cassette-window", type=int, default=6)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--out", default=str(B / "reports/cassette_scan_demo"))
    a = ap.parse_args()

    models = {c: pickle.load(open(B / "models" / MODELS[c], "rb"))["model"] for c in CLASSES}
    esm = F.ESM(B / "models/esm_cache")
    genomes = [load_gb(a.gb)] if a.gb else [load_atlas(k.strip()) for k in a.genomes.split(",") if k.strip()]
    names = [a.gb and Path(a.gb).stem] if a.gb else [k.strip() for k in a.genomes.split(",") if k.strip()]
    res = {}
    for name, (org, ps) in zip(names, genomes):
        ps.sort(key=lambda p: p["start"])
        seqs = [p["sequence"] for p in ps]
        X = np.hstack([np.array([F.handcrafted(s) for s in seqs]), esm.embed(seqs)])
        assert X.shape[1] == 516, X.shape
        probs = {c: models[c].predict_proba(X)[:, 1] for c in CLASSES}
        for i, p in enumerate(ps):
            p["index"] = i; p["length"] = len(p["sequence"])
            p["P"] = {c: float(probs[c][i]) for c in CLASSES}
            best = max(CLASSES, key=lambda c: p["P"][c])
            p["call"] = best if p["P"][best] >= a.threshold else "none"
        cass = find_cassettes(ps, a.threshold, a.cassette_window)
        top = {}
        for c in CLASSES:
            t = max(ps, key=lambda p: p["P"][c])
            top[c] = {"gene": t["gene"] or t["id"], "id": t["id"], "product": t["product"], "P": t["P"][c], "index": t["index"]}
        print(f"\n=== {name} ({org}) : {len(ps)} proteins, {len(cass)} cassette(s) ===")
        print(f"{'idx':>3} {'gene':<10} {'product':<40} {'len':>5} {'P(hol)':>7} {'P(end)':>7} {'P(span)':>7}  call")
        for p in ps:
            print(f"{p['index']:>3} {(p['gene'] or p['id'])[:10]:<10} {p['product'][:40]:<40} {p['length']:>5} "
                  f"{p['P']['holin']:7.3f} {p['P']['endolysin']:7.3f} {p['P']['spanin']:7.3f}  {p['call']}")
        for c in CLASSES: print(f"top {c}: {top[c]['gene']} ({top[c]['product']}) P={top[c]['P']:.3f}")
        for k, cs in enumerate(cass, 1):
            print(f"cassette {k}: gene idx {cs['gene_index_range']}: " +
                  ", ".join(f"{m['gene']}@{m['index']}[{'/'.join(m['classes_called'])}]" for m in cs["members"]))
        res[name] = {"organism": org, "n_proteins": len(ps), "top": top, "cassettes": cass,
                     "proteins": [{k: p[k] for k in ("index", "id", "gene", "product", "start", "stop", "strand", "length", "P", "call")} for p in ps]}

    validation = None
    if "lambda" in res:
        validation = validate_lambda(res["lambda"], a.threshold)
        print("\n=== LAMBDA VALIDATION ===")
        for line in validation["lines"]: print(line)
        print("VERDICT:", validation["verdict"])
    out = {"threshold": a.threshold, "cassette_window": a.cassette_window, "lambda_validation": validation, "genomes": res}
    Path(a.out).parent.mkdir(exist_ok=True)
    json.dump(out, open(a.out + ".json", "w"), indent=1)
    write_md(out, a.out + ".md")
    print("\nCassette counts:", {k: len(v["cassettes"]) for k, v in res.items()})


def validate_lambda(r, thr):
    ps = r["proteins"]; known = {"holin": ["S", "S'"], "endolysin": ["R"], "spanin": ["Rz", "Rz1"]}
    lines = []; ok = True; rows = []
    for c, genes in known.items():
        rank = sorted(ps, key=lambda p: -p["P"][c])
        for g in genes:
            p = next((q for q in ps if q["gene"] == g), None)
            if p is None: lines.append(f"{c}: gene {g} not found"); continue
            rk = [q["index"] for q in rank].index(p["index"]) + 1
            lines.append(f"{c}: {g} ({p['product']}) P={p['P'][c]:.3f} rank {rk}/{len(ps)}; top is {rank[0]['gene'] or rank[0]['id']} ({rank[0]['product']}) P={rank[0]['P'][c]:.3f}")
            rows.append({"class": c, "gene": g, "P": p["P"][c], "rank": rk})
        if not any(x["P"] >= thr and x["rank"] <= 3 for x in rows if x["class"] == c): ok = False
    cass = r["cassettes"]
    found = [cs for cs in cass if {"S", "R"} <= {m["gene"] for m in cs["members"]} and {"Rz", "Rz1"} & {m["gene"] for m in cs["members"]}]
    lines.append(f"S-R-Rz/Rz1 cassette detected: {bool(found)}")
    if not found: ok = False
    verdict = "PASS: known lambda lysis genes score high for their class and the cassette is detected." if ok else \
        "FAIL/WARNING: a known lambda lysis gene did not score >=thr within top 3 of its class, or the cassette was not detected. Check the feature pipeline."
    return {"rows": rows, "lines": lines, "cassette_detected": bool(found), "passed": ok, "verdict": verdict}


def rows_for(rows, c): return [x["P"] for x in rows if x["class"] == c] or [0]


def write_md(out, path):
    L = ["# Lysis cassette scan (demo)", "", f"threshold={out['threshold']}, cassette window={out['cassette_window']} genes. "
         "Three independent one-vs-rest models (holin_curated, endolysin, spanin) on one 516-d feature matrix.", "",
         "CAVEAT: these are deployment models trained on all labels (incl. the atlas phages' own lysis genes), so the lambda check "
         "verifies pipeline wiring only; it is in-sample, not an accuracy estimate (see reports/*_eval.json for LOGO estimates).", ""]
    v = out["lambda_validation"]
    if v:
        L += ["## Lambda validation", "", f"**{v['verdict']}**", ""] + [f"- {x}" for x in v["lines"]] + [""]
    L += ["## Cassettes per genome", ""]
    for g, r in out["genomes"].items():
        L.append(f"**{g}** ({r['n_proteins']} proteins): {len(r['cassettes'])} cassette(s)")
        for cs in r["cassettes"]:
            L.append("- " + "; ".join(f"{m['gene']}#{m['index']} {m['product'][:30]} [{'/'.join(m['classes_called'])}]" for m in cs["members"]))
        L.append("")
    L += ["## Top call per class", "", "| genome | class | gene | product | P |", "|---|---|---|---|---|"]
    for g, r in out["genomes"].items():
        for c in CLASSES:
            t = r["top"][c]; L.append(f"| {g} | {c} | {t['gene']} | {t['product']} | {t['P']:.3f} |")
    open(path, "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
