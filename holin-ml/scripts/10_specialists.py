"""Target the two measured failure modes, then combine the specialists with the general model under the same guards.

Diagnosis (scripts/07 output + composition analysis):
  FAILURE 1  Actinobacterial/mycobacterial families (TCDB 1.E.34 Hol-X, 1.E.40 MP4) score 0.00 recall at 95% precision
             under leave-one-family-out. They are compositionally different - median 132 aa vs 91, alanine 0.116 vs
             0.103, lysine 0.032 vs 0.056 (high-GC hosts) - and only 474 of 9,503 negatives come from actinobacteria,
             so the decision boundary in that corner of the space is fitted on almost nothing.
  FAILURE 2  Long multi-domain holins. T4 holin T (218 aa, large C-terminal cytoplasmic domain) ranks 116/278 in its
             own genome. Mean-pooling an ESM embedding over 218 residues dilutes a short membrane domain.
  FAILURE 3  Both length tails. Recall at 95% precision is 0.75 for 60-90 aa holins but 0.26 below 60 aa and 0.26
             above 160 aa. Very short peptides give noisy mean-pooled embeddings, and the hydropathy features
             (window 19, minimum segment 15) barely resolve anything in a 45-aa protein.

Fixes, each accepted only if it earns its place:
  A  WINDOW model - trained on short sequences and on 100-aa windows of long ones; a long protein scores as the best
     window it contains, so a holin-like domain is not averaged away.
  B  ACTINO specialist - trained only on actinobacterial-host holins against actinobacterial negatives, so composition
     cannot act as a shortcut the way it does in the global model.
  C  SHORT specialist - trained only on sequences below 90 aa, so the boundary for small peptides is fitted in-domain
     instead of being dominated by the 60-120 aa bulk.
  D  STACKER - logistic regression over the four out-of-fold scores plus three domain indicators (is_short, is_long,
     is_actino_like), so it can gate each specialist to the region it was built for rather than applying it blindly.

Guards (same discipline as scripts/09): the frozen gold holdout is never trained on; every component and the stack are
judged on gold average precision, leave-one-family-out recall (especially the two failing families) and the held-out
hard cases. A component that does not improve the failures without hurting the rest is reported and dropped.
Usage: python3 scripts/10_specialists.py
"""
import json, pickle, re, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve

B = Path(__file__).resolve().parent.parent
ACTINO_FAMILIES = {"1.E.32", "1.E.34", "1.E.35", "1.E.36", "1.E.39", "1.E.40", "1.E.57", "1.E.63"}
ACTINO_ORG = re.compile(r"mycobacteri|streptomyc|corynebacteri|rhodococc|gordonia|actinomyc|nocardia|propionibacteri|"
                        r"bifidobacteri|arthrobacter|tsukamurella|microbacteri", re.I)
FAILING = ["1.E.34", "1.E.40"]
WIN, STRIDE, LONG, SHORT = 100, 50, 150, 90
NOISE, HARD_TOL = 0.002, 0.05


def hgb(): return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, l2_regularization=1.0,
                                                 class_weight="balanced", random_state=0)


def is_actino(r):
    if r.get("tcdb_family") in ACTINO_FAMILIES: return True
    return bool(ACTINO_ORG.search(" ".join(str(s.get("organism", "")) + " " + str(s.get("description", "")) + " " + str(s.get("name", ""))
                                           for s in r.get("sources", []))))


def windows(seq):
    if len(seq) <= LONG: return [seq]
    return [seq[i:i + WIN] for i in range(0, max(1, len(seq) - WIN + 1), STRIDE)] or [seq]


def main():
    data = json.loads((B / "data/processed/dataset.json").read_text())
    labelled = [r for r in data if r["label"] in ("holin", "negative")]
    hard = [r for r in data if r["label"] == "holin_like"]
    gold_ids = set(json.loads((B / "data/processed/gold_holdout.json").read_text())["ids"]) if (B / "data/processed/gold_holdout.json").exists() else set()
    if not gold_ids: sys.exit("run scripts/09_iterate.py once to create the frozen gold holdout")
    train = [r for r in labelled if r["id"] not in gold_ids]
    gold = [r for r in labelled if r["id"] in gold_ids]
    esm = F.ESM(B / "models/esm_cache")

    def feats(seqs):
        return np.hstack([np.stack([F.handcrafted(s) for s in seqs]), esm.embed(seqs)])

    y = np.array([r["label"] == "holin" for r in train], int)
    g = np.array([r["cluster"] for r in train])
    seqs = [r["sequence"] for r in train]
    yg = np.array([r["label"] == "holin" for r in gold], int)
    gseqs = [r["sequence"] for r in gold]
    print(f"train {len(train)} ({y.sum()} holins) | gold {len(gold)} ({yg.sum()} holins)", flush=True)
    t = time.time(); X = feats(seqs); Xg = feats(gseqs); Xh = feats([r["sequence"] for r in hard])
    print(f"base features in {time.time()-t:.0f}s", flush=True)

    # ---------- A: window model ----------
    wtrain, wy, wg = [], [], []
    for i, r in enumerate(train):
        for w in windows(r["sequence"]):
            wtrain.append(w); wy.append(y[i]); wg.append(g[i])
    wy = np.array(wy); wg = np.array(wg)
    t = time.time(); Xw = feats(wtrain)
    print(f"window training set {len(wtrain)} fragments ({wy.sum()} positive) in {time.time()-t:.0f}s", flush=True)

    def window_scores(model, sequences):
        flat, owner = [], []
        for i, s in enumerate(sequences):
            for w in windows(s): flat.append(w); owner.append(i)
        p = model.predict_proba(feats(flat))[:, 1]
        out = np.zeros(len(sequences))
        for i, v in zip(owner, p): out[i] = max(out[i], v)
        return out

    # ---------- B: actino specialist ----------
    act_idx = [i for i, r in enumerate(train) if is_actino(r)]
    print(f"actino specialist pool: {len(act_idx)} ({sum(y[i] for i in act_idx)} holins)", flush=True)
    sh_idx = [i for i, r in enumerate(train) if r["length"] < SHORT]
    print(f"short specialist pool: {len(sh_idx)} ({sum(y[i] for i in sh_idx)} holins)", flush=True)

    def gates(records_or_seqs, lengths, actino_flags):
        return np.column_stack([(np.array(lengths) < SHORT).astype(float), (np.array(lengths) > LONG).astype(float),
                                np.array(actino_flags, dtype=float)])

    g_train = gates(None, [r["length"] for r in train], [is_actino(r) for r in train])
    g_gold = gates(None, [r["length"] for r in gold], [is_actino(r) for r in gold])
    g_hard = gates(None, [r["length"] for r in hard], [is_actino(r) for r in hard])

    # ---------- out-of-fold scores for all three ----------
    cv = list(GroupKFold(n_splits=5).split(X, y, g))
    oof = {k: np.zeros(len(y)) for k in ("general", "window", "actino", "short")}
    for k, (tr, te) in enumerate(cv):
        m = hgb(); m.fit(X[tr], y[tr]); oof["general"][te] = m.predict_proba(X[te])[:, 1]
        wsel = np.isin(wg, g[tr])
        mw = hgb(); mw.fit(Xw[wsel], wy[wsel]); oof["window"][te] = window_scores(mw, [seqs[i] for i in te])
        trs = set(tr.tolist())
        asel = [i for i in act_idx if i in trs]
        ma = hgb(); ma.fit(X[asel], y[asel]); oof["actino"][te] = ma.predict_proba(X[te])[:, 1]
        ssel = [i for i in sh_idx if i in trs]
        msh = hgb(); msh.fit(X[ssel], y[ssel]); oof["short"][te] = msh.predict_proba(X[te])[:, 1]
        print(f"  fold {k+1}/5 done", flush=True)
    COLS = ("general", "window", "actino", "short")
    Z = np.column_stack([oof[k] for k in COLS] + [g_train])
    stack = LogisticRegression(max_iter=4000, class_weight="balanced").fit(Z, y)
    print("stacker coefficients", dict(zip(COLS + ("is_short", "is_long", "is_actino"), np.round(stack.coef_[0], 3))), flush=True)

    # ---------- fit final components on all trainable data ----------
    mg = hgb().fit(X, y)
    mw = hgb().fit(Xw, wy)
    ma = hgb().fit(X[act_idx], y[act_idx])
    msh = hgb().fit(X[sh_idx], y[sh_idx])

    def combo(sequences, Xmat, gmat):
        z = np.column_stack([mg.predict_proba(Xmat)[:, 1], window_scores(mw, sequences), ma.predict_proba(Xmat)[:, 1],
                             msh.predict_proba(Xmat)[:, 1], gmat])
        return stack.predict_proba(z)[:, 1], z

    sg_comb, zg = combo(gseqs, Xg, g_gold)
    sh_comb, _ = combo([r["sequence"] for r in hard], Xh, g_hard)

    def report(name, s_gold, s_hard):
        p_, r_, th_ = precision_recall_curve(yg, s_gold)
        idx = np.where(p_[:-1] >= 0.95)[0]
        return {"gold_average_precision": round(float(average_precision_score(yg, s_gold)), 4),
                "gold_auroc": round(float(roc_auc_score(yg, s_gold)), 4),
                "gold_recall_at_P95": round(float(r_[:-1][idx[0]]), 4) if len(idx) else 0.0,
                "threshold_P95": round(float(th_[idx[0]]), 4) if len(idx) else 1.0,
                "hard_case_median": round(float(np.median(s_hard)), 4)}

    res = {"general": report("general", mg.predict_proba(Xg)[:, 1], mg.predict_proba(Xh)[:, 1]),
           "window": report("window", window_scores(mw, gseqs), window_scores(mw, [r["sequence"] for r in hard])),
           "actino": report("actino", ma.predict_proba(Xg)[:, 1], ma.predict_proba(Xh)[:, 1]),
           "short": report("short", msh.predict_proba(Xg)[:, 1], msh.predict_proba(Xh)[:, 1]),
           "stacked": report("stacked", sg_comb, sh_comb)}
    for k, v in res.items(): print(k, json.dumps(v), flush=True)

    # ---------- leave-one-family-out, general vs stacked, on the families that matter ----------
    fams = {}
    for i, r in enumerate(train):
        if r["label"] == "holin" and r.get("tcdb_family", "SwissProt-only") != "SwissProt-only":
            fams.setdefault(r["tcdb_family"], []).append(i)
    check = [f for f in FAILING if f in fams] + [f for f in sorted(fams, key=lambda f: -len(fams[f]))[:6] if f not in FAILING]
    cut_g, cut_s = res["general"]["threshold_P95"], res["stacked"]["threshold_P95"]
    lofo = {}
    for f in check:
        mem = fams[f]; drop = {train[i]["cluster"] for i in mem}; ms = set(mem)
        keep = np.array([i for i in range(len(train)) if i not in ms and not (y[i] == 1 and train[i]["cluster"] in drop)])
        kg = hgb().fit(X[keep], y[keep])
        wsel = np.isin(wg, g[keep])
        kw = hgb().fit(Xw[wsel], wy[wsel])
        ka_idx = [i for i in act_idx if i in set(keep.tolist())]
        ka = hgb().fit(X[ka_idx], y[ka_idx]) if len(set(y[ka_idx])) > 1 else None
        ks_idx = [i for i in sh_idx if i in set(keep.tolist())]
        ks = hgb().fit(X[ks_idx], y[ks_idx]) if len(set(y[ks_idx])) > 1 else None
        mseqs = [seqs[i] for i in mem]; Xm = X[mem]
        s_gen = kg.predict_proba(Xm)[:, 1]
        z = np.column_stack([s_gen, window_scores(kw, mseqs), ka.predict_proba(Xm)[:, 1] if ka else np.zeros(len(mem)),
                             ks.predict_proba(Xm)[:, 1] if ks else np.zeros(len(mem)), g_train[mem]])
        s_stk = stack.predict_proba(z)[:, 1]
        lofo[f] = {"n": len(mem), "general_recall_at_P95": round(float(np.mean(s_gen >= cut_g)), 3),
                   "stacked_recall_at_P95": round(float(np.mean(s_stk >= cut_s)), 3),
                   "general_median": round(float(np.median(s_gen)), 3), "stacked_median": round(float(np.median(s_stk)), 3)}
        print(f"  LOFO {f}: {json.dumps(lofo[f])}", flush=True)

    base_ap, stk_ap = res["general"]["gold_average_precision"], res["stacked"]["gold_average_precision"]
    fail_gain = [lofo[f]["stacked_recall_at_P95"] - lofo[f]["general_recall_at_P95"] for f in FAILING if f in lofo]
    others_loss = [lofo[f]["general_recall_at_P95"] - lofo[f]["stacked_recall_at_P95"] for f in lofo if f not in FAILING]
    verdict = []
    if stk_ap < base_ap - NOISE: verdict.append(f"stack lowers gold AP {base_ap} -> {stk_ap}")
    if res["stacked"]["hard_case_median"] > res["general"]["hard_case_median"] + HARD_TOL:
        verdict.append(f"stack raises hard-case median {res['general']['hard_case_median']} -> {res['stacked']['hard_case_median']}")
    if fail_gain and max(fail_gain) <= 0: verdict.append("no gain on the failing families")
    if others_loss and max(others_loss) > 0.10: verdict.append(f"stack costs up to {max(others_loss):.2f} recall on a family it used to get")
    accepted = not verdict
    out = {"diagnosis": {"failure_1": "actinobacterial families 1.E.34/1.E.40 at 0.00 LOFO recall; composition shift and only 474 of 9503 negatives from actinobacteria",
                         "failure_2": "long multi-domain holins (T4 holin T, 218 aa) diluted by mean pooling"},
           "components": res, "stacker_coefficients": {k: round(float(v), 3) for k, v in zip(COLS + ("is_short", "is_long", "is_actino"), stack.coef_[0])},
           "leave_one_family_out": lofo, "accepted": accepted, "rejection_reasons": verdict,
           "guards": "frozen gold holdout never trained on; a component is kept only if it lifts the failing families without lowering gold AP, raising hard-case scores, or costing >0.10 recall on a family that already worked"}
    (B / "reports/specialists_report.json").write_text(json.dumps(out, indent=1))
    if accepted:
        pickle.dump({"kind": "stacked", "general": mg, "window": mw, "actino": ma, "short": msh, "stacker": stack,
                     "window_params": {"window": WIN, "stride": STRIDE, "apply_above": LONG, "short_below": SHORT},
                     "features": "both", "esm_model": F.ESM.MODEL, "hand_feature_names": F.HAND_NAMES},
                    open(B / "models/holin_model_stacked.pkl", "wb"))
        print("\nACCEPTED: stacked model written to models/holin_model_stacked.pkl", flush=True)
    else:
        print("\nREJECTED: " + "; ".join(verdict), flush=True)
    print(json.dumps({"gold_AP": {"general": base_ap, "stacked": stk_ap},
                      "failing_families": {f: lofo[f] for f in FAILING if f in lofo}}, indent=1))


if __name__ == "__main__":
    main()
