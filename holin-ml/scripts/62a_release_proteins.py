"""Collect every lysis call (any tier) from every DNA-only scan, with its protein sequence, and complete the membrane
topology for all of them: our ESM predictor (scripts/55) locally, DeepTMHMM and SignalP 6.0 (scripts/56, BioLib cloud;
public phage proteins) for sequences not already run in reports/external/.

Roles collected per genome and class: the call (holin / endolysin / spanin, tier confident or candidate), the second
strong holin (P >= 0.9, next best), and the spanin partner (as in scripts/56: overlapping or within 2 genes, P >= 0.5).

Steps:
  collect    reports/release_work/call_proteins.json  [{set, pred, genome, role, tier, id, start, stop, strand, sequence}]
  ours       reports/release_work/ours_topology.json  {sid: {helices, n, n_terminus, sar_rule, spanin_member_lipobox}}
  external   DeepTMHMM + SignalP for new sequences -> reports/external/extra/{deeptmhmm,signalp}/chunk_NNN/
Usage: python3 scripts/62a_release_proteins.py collect|ours|external
"""
import argparse, importlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
W = B / "reports/release_work"
GROUPS = ["n4", "lambda", "t7", "p2", "drexler", "t5", "herelle", "t4", "jumbo"]
# the prediction directory used for each scan in the reports (later model versions are in the release's call table)
CANON = {**{s: "pred" for s in GROUPS}, "blind": "pred_new", "blind2": "pred_new", "final": "pred"}


def sid(seq):
    import hashlib
    return "s" + hashlib.sha256(seq.encode()).hexdigest()[:15]


def read_pred(s, pred, acc):
    L = (B / f"reports/{s}/{pred}/{acc}.tsv").read_text().splitlines(); h = L[0].split("\t")
    return [dict(zip(h, l.split("\t"))) for l in L[1:] if l.strip()]


def calls_of(R):
    out = {}
    for i, r in enumerate(R):
        for x in r["lysis_call"].split(","):
            if x: c, t = x.split(":"); out[c] = (i, t)
    return out


def roles(R):
    """[(role, tier, row index)] for one genome's prediction table"""
    C = calls_of(R); out = []
    for c in ("holin", "endolysin", "spanin"):
        if c in C: out.append((c, C[c][1], C[c][0]))
    if "holin" in C:
        i = C["holin"][0]
        strong = sorted([j for j, r in enumerate(R) if float(r["P_holin"]) >= 0.9 and j != i], key=lambda j: -float(R[j]["P_holin"]))
        if strong: out.append(("holin2", "", strong[0]))
    if "spanin" in C:
        i = C["spanin"][0]; s0, e0 = int(R[i]["start"]), int(R[i]["stop"]); cand = []
        for j, q in enumerate(R):
            if j == i or float(q["P_spanin"]) < 0.5: continue
            ov = min(e0, int(q["stop"])) - max(s0, int(q["start"]))
            if ov > 0 or abs(j - i) <= 2: cand.append((ov > 0, float(q["P_spanin"]), j))
        if cand: out.append(("spanin_partner", "", max(cand)[2]))
    return out


def proteins(s, acc):
    import genecall as G
    from Bio import SeqIO
    rec = next(SeqIO.parse(B / f"data/raw/{s}/fna/{acc}.fna", "fasta"))
    return {p["id"]: p["sequence"] for p in G.denovo([(rec.id, str(rec.seq))], nested=True)}


def collect():
    out = []
    for s, pred in CANON.items():
        for acc in json.load(open(B / f"data/raw/{s}/selection.json"))["accessions"]:
            if not (B / f"reports/{s}/{pred}/{acc}.tsv").exists(): continue
            R = read_pred(s, pred, acc); P = proteins(s, acc)
            for role, tier, i in roles(R):
                r = R[i]; seq = P.get(r["id"], "")
                out.append({"set": s, "pred": pred, "genome": acc, "role": role, "tier": tier, "id": r["id"],
                            "start": int(r["start"]), "stop": int(r["stop"]), "strand": r["strand"], "sequence": seq,
                            "sid": sid(seq) if seq else ""})
        print(s, len(out), flush=True)
    W.mkdir(parents=True, exist_ok=True)
    (W / "call_proteins.json").write_text(json.dumps(out))
    print(f"{len(out)} call proteins, {len({o['sid'] for o in out})} distinct sequences")


def ours():
    TM = importlib.import_module("55_tm_predictor"); T55 = importlib.import_module("55b_topology")
    P = json.load(open(W / "call_proteins.json"))
    f = W / "ours_topology.json"; done = json.load(open(f)) if f.exists() else {}
    todo = {p["sid"]: p["sequence"] for p in P if p["sid"] and p["sid"] not in done}
    for k, (i, seq) in enumerate(todo.items()):
        r = TM.predict([seq])[0]
        done[i] = {"helices": r["helices"], "n": r["n"], "n_terminus": r["n_terminus"],
                   "sar_rule": T55.endolysin_type(seq), "spanin_member_lipobox": T55.spanin_member(seq)}
        if k % 200 == 0: f.write_text(json.dumps(done)); print(k, len(todo), flush=True)
    f.write_text(json.dumps(done)); print(f"ours: {len(done)} sequences")


def external():
    M = importlib.import_module("56_external_predictors")
    have = set()
    for ln in (B / "reports/external/input.fasta").read_text().splitlines():
        if ln.startswith(">"): have.add(ln[1:])
    P = json.load(open(W / "call_proteins.json"))
    new = {p["sid"]: p["sequence"] for p in P if p["sid"] and p["sid"] not in have}
    M.OUT = B / "reports/external/extra"; M.OUT.mkdir(parents=True, exist_ok=True)
    (M.OUT / "input.fasta").write_text("".join(f">{k}\n{v}\n" for k, v in sorted(new.items())))
    print(f"{len(new)} sequences not yet run externally", flush=True)
    M.run("deeptmhmm", 500); M.run("signalp", 500)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("step", choices=["collect", "ours", "external"]); a = ap.parse_args()
    {"collect": collect, "ours": ours, "external": external}[a.step]()
