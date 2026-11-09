"""How much of the model's ability is recognising a holin, and how much is recognising its family?

Scoring each atlas-phage holin twice -- once with its homology family in the training set, once with that family
removed (the leave-one-genome-out scores from scripts/14) -- separates the two. The difference, the "collapse",
is how much of the score was family recognition.

It also records two control experiments that killed earlier hypotheses:
  length prior   -- T4 t (218 aa) scores 0.989 at full length with its family present, so long proteins are not
                    vetoed on length; the leave-one-genome-out failure is not a length effect.
  anchor window  -- the anchor TM +/- 40 aa of T4 t scores 0.0025 and of T5 C1 0.0013, far BELOW the full
                    protein, so the holin signal is not concentrated in the membrane anchor. This is why the
                    TM-anchored local features of scripts/15 did not help and in fact cost recall.
                    Caveat: the model was trained only on whole proteins, so a fragment is out of distribution
                    for it. This test cannot cleanly separate "the anchor carries little signal" from
                    "fragments are unfamiliar"; it only shows the anchor-window route does not work here.

Usage: python3 scripts/17_family_dependence.py
"""
import glob, json, os, pickle, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import features as F

B = Path(__file__).resolve().parent.parent
DSC = "/home/user/mbaffour.github.io/dirty-science-canvas"
HOLIN_WORD = re.compile(r"holin", re.I)
COLLAPSE = 0.25          # above this, the score was mostly family recognition


def main():
    mdl = pickle.load(open(B / "models/holin_model_phageneg.pkl", "rb"))
    esm = F.ESM(B / "models/esm_cache")
    feats = lambda ss: np.hstack([np.array([F.handcrafted(s) for s in ss]), esm.embed(ss)])

    gp = []
    for p in sorted(glob.glob(os.path.join(DSC, "*_Topology_Lab_Reference", "data.json"))):
        d = json.load(open(p))
        if d.get("kind") != "phage": continue
        for r in d["proteins"]:
            if HOLIN_WORD.search(r.get("product") or ""):
                gp.append({"phage": d["key"], "gene": (r.get("gene") or r["protein_id"])[:14],
                           "length": r["length"], "sequence": r["sequence"]})
    infam = mdl["model"].predict_proba(feats([x["sequence"] for x in gp]))[:, 1]
    loo = {h["phage"] + "|" + h["gene"]: h["score"]
           for h in json.load(open(B / "reports/genome_loo_eval.json"))["models"]["phage_negatives"]["holins"]}

    rows = []
    for x, s in zip(gp, infam):
        o = loo.get(x["phage"] + "|" + x["gene"])
        if o is None: continue
        rows.append({"phage": x["phage"], "gene": x["gene"], "length": x["length"],
                     "in_family": round(float(s), 4), "out_of_family": round(float(o), 4),
                     "collapse": round(float(s) - float(o), 4),
                     "verdict": ("fails either way" if s < 0.5 else
                                 "family recognition only" if float(s) - float(o) > COLLAPSE else "generalises")})
    rows.sort(key=lambda r: -r["collapse"])

    # control: full protein vs its anchor window, for the two architectures that fail out of family
    ctl = []
    for x in gp:
        if x["length"] < 150 and x["phage"] not in ("lambda", "phi29"): continue
        _, w = F.local(x["sequence"])
        sc = mdl["model"].predict_proba(feats([x["sequence"], w]))[:, 1]
        ctl.append({"phage": x["phage"], "gene": x["gene"], "full_length": x["length"],
                    "full_score": round(float(sc[0]), 4), "window_length": len(w),
                    "window_score": round(float(sc[1]), 4)})

    by = {}
    for r in rows: by[r["verdict"]] = by.get(r["verdict"], 0) + 1
    out = {"question": "how much of the score is recognising a holin vs recognising its family",
           "method": "each atlas-phage holin scored with its homology family in training and with it removed "
                     "(leave-one-genome-out, scripts/14); the difference is the collapse",
           "caveat": "13 annotated holins, so these are case-by-case observations, not rates with useful error bars",
           "summary": by, "holins": rows,
           "control_full_protein_vs_anchor_window": {
               "finding": "the anchor window scores far BELOW the full protein, so the signal is not concentrated "
                          "in the membrane anchor; the model was trained on whole proteins only, so a fragment is "
                          "also out of distribution for it",
               "rows": ctl},
           "conclusion": "the model generalises to the small multi-TM class I holins and to little else; T4 t and "
                         "T5 C1 (~218 aa, single N-terminal TM, large C-terminal domain) are recognised only when "
                         "their own family is in training, and only 52 of 558 training holins exceed 150 aa"}
    (B / "reports/family_dependence.json").write_text(json.dumps(out, indent=2))

    print(f"{'holin':<24}{'len':>5}{'in-family':>11}{'out-of-family':>15}{'collapse':>10}   verdict")
    for r in rows:
        print(f"{r['phage']+'|'+r['gene']:<24}{r['length']:>5}{r['in_family']:>11.4f}{r['out_of_family']:>15.4f}"
              f"{r['collapse']:>10.4f}   {r['verdict']}")
    print("\n" + json.dumps(by, indent=1))
    print("\ncontrol -- full protein vs anchor window:")
    for c in ctl:
        print(f"  {c['phage']+'|'+c['gene']:<22} full {c['full_length']:>4} aa {c['full_score']:.4f}   "
              f"window {c['window_length']:>4} aa {c['window_score']:.4f}")


if __name__ == "__main__":
    main()
