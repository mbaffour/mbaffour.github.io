"""Poll TOPCONS2 jobs (checkjob) and download the result zip once finished. Safe to rerun."""
import io, sys, zipfile, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir
from jobrecord import sha, now, atomic_write, load, save
from suds.client import Client
client = Client("https://topcons.net/pred/api_submitseq/?wsdl", cache=None)
pending = 0
for key in PHAGES:
    rd = project_dir(key) / "raw" / "TOPCONS2"; rec_path = rd / "batch1.job.json"; rec = load(rec_path)
    if not rec or not rec.get("jobid") or rec.get("status") == "complete": print(key, rec and rec.get("status")); continue
    s = [str(x) for x in client.service.checkjob(rec["jobid"])[0]]
    rec.setdefault("checks", []).append({"utc": now(), "status": s[0]}); rec["server_status"] = s[0]
    if s[0] == "Finished":
        r = requests.get(s[1], timeout=300); r.raise_for_status()
        zp = rd / f"{rec['jobid']}.zip"; atomic_write(zp, r.content)
        zipfile.ZipFile(io.BytesIO(r.content)).extractall(rd / "extracted")
        rec.update({"result_zip": f"raw/TOPCONS2/{zp.name}", "result_zip_sha256": sha(r.content), "result_zip_url": s[1], "status": "complete", "completed_utc": now()})
    elif s[0] == "Failed": rec.update({"status": "failed", "error": s[2]})
    else: pending += 1
    save(rec_path, rec); print(key, s[0])
sys.exit(2 if pending else 0)
