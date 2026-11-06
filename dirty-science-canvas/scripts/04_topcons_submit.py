"""Submit each phage's exact FASTA to TOPCONS2 via the official WSDL API (https://topcons.net/pred/help-wsdl-api/),
using the same submitjob(seq, fixtop, jobname, email) call as the official topcons2_wsdl.py client. Never resubmits a batch that
already has a job ID. Documented limit: input file < 9 MB (from the official client)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir
from jobrecord import sha, now, atomic_write, load, save
from suds.client import Client
WSDL = "https://topcons.net/pred/api_submitseq/?wsdl"
client = None
for key in PHAGES:
    rd = project_dir(key) / "raw" / "TOPCONS2"; rec_path = rd / "batch1.job.json"; rec = load(rec_path)
    if rec and rec.get("jobid"): print(key, "already submitted", rec["jobid"], rec.get("status")); continue
    fa = (project_dir(key) / "inputs" / "proteins_submitted.fasta").read_text()
    assert len(fa.encode()) < 9 * 1024 * 1024
    atomic_write(rd / "batch1.fasta", fa)
    client = client or Client(WSDL, cache=None)
    rec = {"method": "TOPCONS2", "wsdl": WSDL, "batch": 1, "fasta": "raw/TOPCONS2/batch1.fasta", "fasta_sha256": sha(fa), "n_sequences": fa.count(">"),
           "jobname": f"dsc_{key}", "fixtop": "", "email": "", "submitted_utc": now()}
    ret = client.service.submitjob(fa, "", rec["jobname"], "")
    s = [str(x) for x in ret[0]]
    rec.update({"raw_return": s, "jobid": s[0] if s[0] not in ("None", "") else None, "result_url": s[1], "numseq_accepted": s[2], "error": s[3], "warning": s[4]})
    rec["status"] = "submitted" if rec["jobid"] else "rejected"
    save(rec_path, rec); print(key, rec["status"], s)
