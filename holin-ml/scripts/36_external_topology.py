"""Run DeepTMHMM and SignalP 6.0 on named proteins, via DTU's BioLib cloud, and tabulate the disagreement.

Phobius (used inline by scripts/33) is fast and free but it is one method. For a call that turns on topology --
is an endolysin secreted, membrane-anchored or cytoplasmic? is a candidate holin really single-TM? -- one
predictor is not enough, and on DAC15 the three tools do NOT agree. This script makes that comparison
reproducible instead of a one-off.

  DeepTMHMM   topology + SP/TM class. Primarily a TOPOLOGY model; its SP-vs-signal-anchor axis is the weaker one.
  SignalP 6.0 the dedicated signal-peptide model, and the only one here that distinguishes Sec/SPI from
              Sec/SPII (LIPO, i.e. a LIPOPROTEIN). That LIPO score is what decides whether a spanin candidate
              can be an o-spanin at all, since o-spanins are lipidated outer-membrane lipoproteins.

Needs network access to biolib.com and `pip install pybiolib`. Jobs run on BioLib's cloud, so the input file
must live in the working directory -- an absolute path is NOT uploaded (the remote sees a bare relative name).

Usage: python3 scripts/36_external_topology.py --genbank data/raw/genomes/NC_055832.1.gb \
                                               --ids KNU90_gp039 KNU90_gp095 KNU90_gp004 --out reports/topology_dac15
"""
import argparse, importlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

B = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--genbank", required=True); ap.add_argument("--ids", nargs="+", required=True)
    ap.add_argument("--out", default="reports/topology_external")
    a = ap.parse_args()
    S5 = importlib.import_module("05_scan_genome")
    seqs = {p["id"]: p["sequence"] for p in S5.annotated_proteins(a.genbank)}
    missing = [i for i in a.ids if i not in seqs]
    if missing: sys.exit(f"not in {a.genbank}: {missing}")
    out = (B / a.out); out.mkdir(parents=True, exist_ok=True)

    work = Path(tempfile.mkdtemp(prefix="exttopo_"))
    (work / "query.fasta").write_text("".join(f">{i}\n{seqs[i]}\n" for i in a.ids))
    here = os.getcwd(); os.chdir(work)              # BioLib uploads relative paths only
    try:
        import biolib
        for app_name, args_, sub in (("DTU/DeepTMHMM", "--fasta query.fasta", "deeptmhmm"),
                                     ("DTU/SignalP_6", "--fastafile query.fasta --organism other "
                                                       "--format none --mode fast --output_dir output", "signalp6")):
            try:
                job = biolib.load(app_name).cli(args=args_)
                print(f"{app_name}: {job.get_status()}", flush=True)
                job.save_files(str(work / sub))
            except Exception as e:
                print(f"{app_name} FAILED: {type(e).__name__}: {e}", flush=True)
        for f in work.rglob("*"):
            if f.is_file() and f.name != "query.fasta": shutil.copy(f, out / f.name)
        shutil.copy(work / "query.fasta", out / "query.fasta")
    finally:
        os.chdir(here)
    print(f"wrote {out}")
    sp = out / "prediction_results.txt"
    if sp.exists(): print(sp.read_text())


if __name__ == "__main__":
    main()
