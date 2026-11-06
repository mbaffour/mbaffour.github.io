"""Re-run predictions for selected proteins (or whole organisms) and rebuild everything.
Each re-run creates new, separately named batches (prefix r<UTC timestamp>_) with full job records; earlier results are kept and
listed as 'superseded' in data.json. TOPCONS2 may serve its cached result for an identical sequence (recorded per protein).
Usage:
  python3 scripts/rerun.py --org T4 --proteins "T4|T4p001,T4|T4p002" --methods Phobius,DeepTMHMM,TOPCONS2
  python3 scripts/rerun.py --org Ecoli_K12                  # all eligible proteins of an organism
  python3 scripts/rerun.py --org T4 --rebuild-only          # just normalize + rebuild atlases + validate"""
import argparse, datetime, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import ORGANISMS, project_dir, ROOT
import predictors
ap = argparse.ArgumentParser(); ap.add_argument("--org", required=True); ap.add_argument("--proteins", default="all")
ap.add_argument("--methods", default="Phobius,DeepTMHMM,TOPCONS2"); ap.add_argument("--rebuild-only", action="store_true"); ap.add_argument("--no-browser-check", action="store_true")
a = ap.parse_args()
orgs = [k.strip() for k in a.org.split(",") if k.strip()]
for k in orgs:
    if k not in ORGANISMS: sys.exit(f"unknown organism {k}; choose from {', '.join(ORGANISMS)}")
methods = [m.strip() for m in a.methods.split(",") if m.strip()]
ts = datetime.datetime.now(datetime.timezone.utc).strftime("r%Y%m%dT%H%M%SZ_")
if not a.rebuild_only:
    for k in orgs:
        inv = {p["protein_id"] for p in predictors.inventory(k)["proteins"]}
        ids = None if a.proteins.strip().lower() == "all" else {x.strip() for x in a.proteins.split(",") if x.strip()}
        if ids:
            ids = {i for i in ids if i.startswith(k + "|")}
            unknown = ids - inv
            if unknown: sys.exit(f"unknown protein IDs for {k}: {sorted(unknown)}")
            if not ids: continue
        for m in methods:
            pl = predictors.plan(k, m, protein_ids=ids if ids else None, prefix=ts)
            print(k, m, "re-run batches:", [b["batch"] for b in pl["batches"] if b["batch"].startswith(ts)], flush=True)
        if "Phobius" in methods: predictors.run_phobius(k)
        if "DeepTMHMM" in methods: predictors.run_deeptmhmm(k)
    if "TOPCONS2" in methods:
        while True:
            for k in orgs:
                while predictors.topcons_submit_next(k, orgs): pass
            pending = sum(predictors.topcons_collect(k) for k in orgs)
            if pending == 0 and not any(not (predictors.load(project_dir(k) / "raw/TOPCONS2" / f"{b['batch']}.job.json") or {}).get("jobid") for k in orgs for b in predictors.plan(k, "TOPCONS2")["batches"]): break
            time.sleep(60)
S = Path(__file__).parent; py = sys.executable; org_arg = ["--org", ",".join(orgs)]
subprocess.run([py, S / "06_normalize.py", *org_arg], check=True)
subprocess.run([py, S / "08_build_atlas.py", *org_arg], check=True)
if not a.no_browser_check:
    subprocess.run(["node", S / "09_browser_check.js", ROOT / "logs" / "browser_check.json"], check=True)
subprocess.run([py, S / "11_validate_package.py", *org_arg], check=True)
subprocess.run([py, S / "12_write_readmes.py"], check=True)
