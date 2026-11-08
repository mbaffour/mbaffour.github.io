"""Submit/poll/collect TOPCONS2 batches (WSDL API), at most config.TOPCONS_MAX_ACTIVE active jobs. Loops until every planned batch is
complete or failed (use --once for a single pass). Resumable; never resubmits a batch that has a job ID."""
import sys, time; from pathlib import Path; sys.path.insert(0, str(Path(__file__).parent))
from config import selected, project_dir; import predictors
from jobrecord import load
keys = selected(sys.argv)
while True:
    for k in keys:
        while predictors.topcons_submit_next(k, keys): pass
    pending = sum(predictors.topcons_collect(k) for k in keys)
    unsub = sum(1 for k in keys for b in predictors.plan(k, "TOPCONS2")["batches"] if not (load(project_dir(k) / "raw/TOPCONS2" / f"{b['batch']}.job.json") or {}).get("jobid"))
    print(time.strftime("%H:%M:%S"), "pending", pending, "unsubmitted", unsub, flush=True) if (pending, unsub) != globals().get("_last") else None; _last = (pending, unsub)
    if "--once" in sys.argv or (pending == 0 and unsub == 0): break
    time.sleep(60)
