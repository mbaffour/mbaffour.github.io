"""A transmembrane-helix predictor built from ESM-2 per-residue embeddings, trained on Swiss-Prot topology.

Why. The project's hydropathy heuristic (features.tm_segments) undercounts membrane helices -- it reads lambda S as one
helix -- so holins could not be classed by topology. No external TM predictor could be installed here, so this trains
one from data, with the phage lysis proteins held out to test it.

Data (scripts/55a): Swiss-Prot bacterial/viral proteins with helical TRANSMEM features (tm), soluble proteins
(soluble), and signal-peptide proteins without TM helices (signal); phage lysis proteins (KW-0578) never trained on.
Per residue: the ESM-2 35M last-layer embedding (480) + Kyte-Doolittle hydropathy averaged over windows of 7, 11 and 19.
Label: inside a TRANSMEM helix or not (signal-peptide residues count as NOT helix).
Model: logistic regression on standardised features (fit on 80% of proteins; 20% for validation, split by protein).
Decoding: probabilities smoothed over 5 residues; runs >= 0.5 of at least 12 residues are helices; a run longer than 35
residues is split into round(length / 23) helices.
Topology: N-terminus side by the positive-inside rule (K+R in the loops on the two sides of the membrane; the side
with more is cytoplasmic).

Outputs: models/tm_predictor.pkl, reports/tm_predictor.json (validation and lysis-protein test vs the heuristic)
Usage: python3 scripts/55_tm_predictor.py [--time-limit S]     (per-residue embeddings cached: resumable)
       import: TM = importlib.import_module("55_tm_predictor"); TM.predict(seqs) -> [{"helices": [...], ...}]
"""
import argparse, hashlib, json, pickle, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
B = Path(__file__).resolve().parent.parent
CACHE = B / "models/esm_res_cache"
MODEL = B / "models/tm_predictor.pkl"
_ESM = None


def _esm():
    global _ESM
    if _ESM is None: _ESM = F.ESM(B / "models/esm_cache")
    return _ESM


def residue_embedding(seq):
    """L x 480 float16, cached on disk by sequence hash"""
    p = CACHE / f"{hashlib.sha256(seq.encode()).hexdigest()}.npy"
    if p.exists(): return np.load(p)
    e = _esm(); torch = e.torch
    parts = []
    for k in range(0, len(seq), e.MAXLEN):
        enc = e.tok([seq[k:k + e.MAXLEN]], return_tensors="pt")
        with torch.no_grad(): hs = e.model(**enc).last_hidden_state[0, 1:-1].numpy()
        parts.append(hs)
    x = np.vstack(parts).astype(np.float16)
    CACHE.mkdir(parents=True, exist_ok=True); np.save(p, x)
    return x


def hydro(seq):
    h = np.array([F.KD.get(a, 0.0) for a in seq])
    out = []
    for w in (7, 11, 19):
        k = np.ones(w) / w; out.append(np.convolve(h, k, mode="same"))
    return np.vstack(out).T


def residue_features(seq):
    return np.hstack([residue_embedding(seq).astype(np.float32), hydro(seq)])


def labels(p):
    y = np.zeros(len(p["seq"]), np.int8)
    for a, b in p["tm"]: y[a - 1:b] = 1
    return y


def decode(prob, min_len=12, split_len=35):
    """probabilities -> list of (start, end) 1-based helices"""
    s = np.convolve(prob, np.ones(5) / 5, mode="same")
    on = s >= 0.5; segs = []; i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j + 1 < len(on) and on[j + 1]: j += 1
            L = j - i + 1
            if L >= min_len:
                n = max(1, int(round(L / 23))) if L > split_len else 1
                step = L / n
                for k in range(n): segs.append((i + int(round(k * step)) + 1, i + int(round((k + 1) * step))))
            i = j + 1
        else: i += 1
    return segs


def n_terminus_side(seq, helices, flank=15):
    """'in' (cytoplasmic) or 'out' by the positive-inside rule; None without helices. Counts K+R only within `flank`
    residues of the membrane on each side: a large soluble domain (e.g. T4 t's periplasmic domain) is full of K/R
    far from the membrane and would otherwise swamp the signal."""
    if not helices: return None
    side_kr = [0, 0]                       # side 0 = the N-terminal side, side 1 = the other
    for k, (a, b) in enumerate(helices):
        before = seq[max(0, a - 1 - flank):a - 1]; after = seq[b:b + flank]
        side_kr[k % 2] += sum(c in "KR" for c in before)
        side_kr[(k + 1) % 2] += sum(c in "KR" for c in after)
    return "in" if side_kr[0] >= side_kr[1] else "out"


_M = None
def predict(seqs):
    global _M
    if _M is None: _M = pickle.load(open(MODEL, "rb"))
    out = []
    for s in seqs:
        X = residue_features(s)
        prob = _M["clf"].predict_proba(_M["scaler"].transform(X))[:, 1]
        h = decode(prob)
        out.append({"helices": h, "n": len(h), "n_terminus": n_terminus_side(s, h)})
    return out


def seg_match(pred, true):
    """helices matched one-to-one when they overlap by >= half the shorter one"""
    used, m = set(), 0
    for a, b in pred:
        for k, (c, d) in enumerate(true):
            if k in used: continue
            ov = min(b, d) - max(a, c) + 1
            if ov >= 0.5 * min(b - a + 1, d - c + 1): used.add(k); m += 1; break
    return m


def evaluate(recs, pred_fn):
    exact = 0; mp = mt = mm = 0
    for p in recs:
        pr = pred_fn(p["seq"]); exact += len(pr) == len(p["tm"])
        mp += len(pr); mt += len(p["tm"]); mm += seg_match(pr, p["tm"])
    return {"proteins": len(recs), "helix_count_exact": round(exact / len(recs), 3),
            "helix_precision": round(mm / max(mp, 1), 3), "helix_recall": round(mm / max(mt, 1), 3)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--time-limit", type=float, default=1e9)
    a = ap.parse_args(); t0 = time.time()
    D = {k: json.load(open(B / f"data/raw/tm/{k}.json")) for k in ("tm", "soluble", "signal", "lysis")}
    allp = D["tm"] + D["soluble"] + D["signal"] + D["lysis"]
    todo = [p for p in allp if not (CACHE / f"{hashlib.sha256(p['seq'].encode()).hexdigest()}.npy").exists()]
    print(f"{len(allp)} proteins, {len(todo)} to embed", flush=True)
    for k, p in enumerate(todo):
        if time.time() - t0 > a.time_limit: print(f"embedded {k}; time limit, rerun to resume", flush=True); return
        residue_embedding(p["seq"])
    rng = np.random.default_rng(0)
    train, val = [], []
    for k in ("tm", "soluble", "signal"):
        idx = rng.permutation(len(D[k])); cut = int(0.8 * len(idx))
        train += [D[k][i] for i in idx[:cut]]; val += [D[k][i] for i in idx[cut:]]
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    t = time.time()
    X = np.vstack([residue_features(p["seq"]) for p in train]); y = np.concatenate([labels(p) for p in train])
    sc = StandardScaler().fit(X)
    clf = LogisticRegression(max_iter=300, C=0.1).fit(sc.transform(X), y)
    print(f"trained on {len(train)} proteins / {len(y)} residues in {time.time()-t:.0f}s", flush=True)
    pickle.dump({"clf": clf, "scaler": sc, "esm": F.ESM.MODEL, "note": __doc__.split("Outputs:")[0].strip()}, open(MODEL, "wb"))
    global _M; _M = None
    ours = lambda s: predict([s])[0]["helices"]
    heur = lambda s: [(i + 1, j + 1) for i, j in F.tm_segments(s)]
    res = {}
    for name, recs in (("validation (held-out Swiss-Prot)", val), ("validation, membrane proteins only", [p for p in val if p["tm"]]),
                       ("validation, signal-peptide proteins", [p for p in val if p["signal"] and not p["tm"]]),
                       ("phage lysis proteins with curated helices (never trained on)", [p for p in D["lysis"] if p["tm"]])):
        res[name] = {"esm_predictor": evaluate(recs, ours), "hydropathy_heuristic": evaluate(recs, heur)}
        print(name, json.dumps(res[name]), flush=True)
    lysis = []
    for p in D["lysis"]:
        if not p["tm"]: continue
        pr = predict([p["seq"]])[0]
        lysis.append({"acc": p["acc"], "name": p["name"], "length": len(p["seq"]), "curated": len(p["tm"]),
                      "predicted": pr["n"], "heuristic": len(F.tm_segments(p["seq"])), "n_terminus": pr["n_terminus"]})
    res["lysis_proteins"] = lysis
    (B / "reports/tm_predictor.json").write_text(json.dumps(res, indent=1))
    print("wrote models/tm_predictor.pkl, reports/tm_predictor.json")


if __name__ == "__main__":
    main()
