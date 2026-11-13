"""BLIND scan: run the shipped predictor on DNA only, before any annotation is looked at.

Input is data/raw/blind/fna/<acc>.fna (scripts/52a): the nucleotide sequence and nothing else. Each genome goes through
scripts/32_predict_lysis.py exactly as a user would run it on a raw assembly (--genome; defaults: Pyrodigal genes plus
nested lipoprotein ORFs, standard holin mode, genomic context, the spanin caller). The predictor's own main() is called
in-process so the logic is identical; the only change is that the ESM model is loaded once instead of per genome.

Output: reports/blind/pred/<acc>.tsv, the predictor's 17-column table. Resumable (finished genomes are skipped).
These files are committed BEFORE scripts/52c reads any annotation, so the calls cannot be adjusted after scoring.
Usage: python3 scripts/52b_blind_scan.py [--time-limit SECONDS]
"""
import argparse, glob, importlib, io, json, sys, time, contextlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
P32 = importlib.import_module("32_predict_lysis")

_esm = {}
_ESM = P32.F.ESM
def _cached_esm(cache_dir, model=None):
    k = (str(cache_dir), model)
    if k not in _esm: _esm[k] = _ESM(cache_dir, model)
    return _esm[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time-limit", type=float, default=1e9)
    ap.add_argument("--set", default="blind", help="data/raw/<set>/ (scripts/52a --name)")
    ap.add_argument("--endolysin-model", default=None,
                    help="score with this endolysin model file in models/ instead of the shipped one (for a paired "
                         "before/after comparison); predictions go to reports/<set>/pred_<tag>/")
    ap.add_argument("--tag", default=None)
    a = ap.parse_args()
    P32.F.ESM = _cached_esm
    if a.endolysin_model: P32.MODELS["endolysin"] = a.endolysin_model
    sel = json.load(open(B / f"data/raw/{a.set}/selection.json"))["accessions"]
    out = B / f"reports/{a.set}" / (f"pred_{a.tag}" if a.tag else "pred"); out.mkdir(parents=True, exist_ok=True)
    todo = [x for x in sel if not (out / f"{x}.tsv").exists()]
    print(f"{len(sel)} genomes selected, {len(todo)} to scan", flush=True)
    t0 = time.time()
    for k, acc in enumerate(todo, 1):
        if time.time() - t0 > a.time_limit: print("time limit; rerun to resume", flush=True); break
        t = time.time(); tmp = out / f"{acc}.tsv.part"
        sys.argv = ["32_predict_lysis.py", "--genome", str(B / f"data/raw/{a.set}/fna" / f"{acc}.fna"), "--out", str(tmp)]
        err = io.StringIO()
        with contextlib.redirect_stderr(err): P32.main()
        tmp.replace(out / f"{acc}.tsv")
        calls = [ln for ln in err.getvalue().splitlines() if "confident" in ln or "candidate" in ln][:3]
        print(f"  [{k}/{len(todo)}] {acc} {time.time()-t:.0f}s", flush=True)
    done = sum((out / f"{x}.tsv").exists() for x in sel)
    print(f"scanned {done}/{len(sel)}", flush=True)


if __name__ == "__main__":
    main()
