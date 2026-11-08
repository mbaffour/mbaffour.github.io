"""Shared batching, submission, collection and raw-output parsing for Phobius, DeepTMHMM and TOPCONS2.

Batches are planned once per organism and method (raw/<Method>/plan.json) from the exact inventory sequences of eligible proteins,
in inventory order, within each service's documented limits (see config.METHOD_RULES). Every batch has a job record
(raw/<Method>/<batch>.job.json) with the exact FASTA checksum, settings, job ID, times, status and output checksums.
Runners skip complete batches and never resubmit a batch that already has a job ID; re-runs create new, separately named batches.
"""
import io, json, re, tarfile, time, zipfile
from pathlib import Path
import requests
from config import ORGANISMS, METHOD_RULES, TOPCONS_MAX_ACTIVE, project_dir
from jobrecord import sha, now, atomic_write, load, save  # noqa: F401 (load re-exported for rerun.py)

KEEP_ZIP_MAX_BYTES = 15 * 1024 * 1024

def inventory(key):
    return json.loads((project_dir(key) / "inventory.json").read_text())

def fasta_for(proteins):
    return "".join(f">{p['protein_id'].replace('|', '__')}\n{p['sequence']}\n" for p in proteins)

def chunk(proteins, rules):
    out, cur, res = [], [], 0
    for p in proteins:
        n = len(p["sequence"])
        if cur and (len(cur) >= rules["max_seqs"] or (rules["max_res"] and res + n > rules["max_res"])):
            out.append(cur); cur, res = [], 0
        cur.append(p); res += n
    if cur: out.append(cur)
    return out

def plan(key, method, protein_ids=None, prefix="b"):
    """Return the batch plan; creates it (or appends a re-run plan when protein_ids/prefix given)."""
    rd = project_dir(key) / "raw" / method; rd.mkdir(parents=True, exist_ok=True)
    pp = rd / "plan.json"; pl = load(pp) or {"method": method, "batches": []}
    if pl["batches"] and protein_ids is None and prefix == "b": return pl
    inv = inventory(key)["proteins"]
    elig = [p for p in inv if p["eligibility"][method][0] and (protein_ids is None or p["protein_id"] in protein_ids)]
    covered = set()
    if protein_ids is None and prefix == "b":
        for jp in rd.glob("*.job.json"):  # legacy whole-inventory batches already run
            j = load(jp)
            if j.get("status") == "complete" and not j.get("format") and j.get("fasta"):
                covered |= set(re.findall(r">(\S+)", (project_dir(key) / j["fasta"]).read_text()))
    todo = [p for p in elig if p["protein_id"].replace("|", "__") not in covered]
    for i, ch in enumerate(chunk(todo, METHOD_RULES[method]), 1):
        name = f"{prefix}{i:03d}"
        fa = fasta_for(ch); atomic_write(rd / f"{name}.fasta", fa)
        pl["batches"].append({"batch": name, "fasta": f"raw/{method}/{name}.fasta", "fasta_sha256": sha(fa), "n_sequences": len(ch),
                              "n_residues": sum(len(p["sequence"]) for p in ch), "planned_utc": now(), "rerun": prefix != "b"})
    save(pp, pl); return pl

# ---------------- Phobius ----------------
PHOBIUS = "https://phobius.sbc.su.se/api/"
def run_phobius(key, pause=1.0):
    pd = project_dir(key); rd = pd / "raw" / "Phobius"; plot = ORGANISMS[key]["kind"] == "phage"
    for b in plan(key, "Phobius")["batches"]:
        rp = rd / f"{b['batch']}.job.json"; rec = load(rp)
        if rec and rec.get("status") == "complete": continue
        fa = (pd / b["fasta"]).read_text(); assert sha(fa) == b["fasta_sha256"]
        prev = (rec.get("previous_attempts", []) + [{k: rec.get(k) for k in ("submitted_utc", "status", "error", "http_status")}]) if rec else []
        rec = {"method": "Phobius", "endpoint": PHOBIUS + "predict", **b, "settings": {"plot": plot}, "submitted_utc": now(), "outputs": {}, "previous_attempts": prev}
        try:
            r = requests.post(PHOBIUS + "predict", json={"sequence": fa, "plot": plot}, timeout=900); rec["http_status"] = r.status_code; r.raise_for_status()
            preds = r.json()["predictions"]
            if plot:
                for p in preds:
                    if p.get("svg"):
                        f = rd / "plots" / f"{p['id']}.svg"; atomic_write(f, p["svg"].encode()); p["svg"] = f"raw/Phobius/plots/{p['id']}.svg"
                body = json.dumps({"predictions": preds}).encode()
            else: body = r.content
            out = rd / f"{b['batch']}.json"; atomic_write(out, body)
            rec["outputs"]["json"] = {"file": f"raw/Phobius/{out.name}", "sha256": sha(body), "note": "SVG plots split into raw/Phobius/plots/ and replaced by their paths" if plot else ""}
            rec["returned_ids"] = [p["id"] for p in preds]; rec["status"] = "complete"; rec["completed_utc"] = now()
        except Exception as e:
            rec["status"] = "failed"; rec["error"] = repr(e)[:500]
        save(rp, rec); print(key, "Phobius", b["batch"], rec["status"], flush=True); time.sleep(pause)

# ---------------- DeepTMHMM ----------------
def run_deeptmhmm(key):
    import biolib, os
    pd = project_dir(key); rd = pd / "raw" / "DeepTMHMM"
    for b in plan(key, "DeepTMHMM")["batches"]:
        rp = rd / f"{b['batch']}.job.json"; rec = load(rp)
        if rec and rec.get("status") in ("complete", "running"): continue
        bd = rd / b["batch"]; bd.mkdir(parents=True, exist_ok=True)
        fa = (pd / b["fasta"]).read_text(); atomic_write(bd / "input.fasta", fa)
        prev = (rec.get("previous_attempts", []) + [{k: rec.get(k) for k in ("submitted_utc", "status", "error", "job_id")}]) if rec else []
        rec = {"previous_attempts": prev, "method": "DeepTMHMM", "service": "BioLib app DTU/DeepTMHMM", "client": f"pybiolib {getattr(biolib, '_version', '') or ''}".strip(), **b, "args": ["--fasta", "input.fasta"], "submitted_utc": now(), "status": "running"}
        save(rp, rec)
        try:
            app = biolib.load("DTU/DeepTMHMM")
            rec["app_version"] = app._app_version.get("app_uri"); rec["app_version_published"] = app._app_version.get("created_at")
            cwd = os.getcwd(); os.chdir(bd)
            try: job = app.cli(args=["--fasta", "input.fasta"], blocking=True)
            finally: os.chdir(cwd)
            rec["job_id"] = getattr(job, "id", None)
            job.save_files(str(bd / "results"))
            rec["outputs"] = [{"file": str(p.relative_to(pd)), "sha256": sha(p.read_bytes())} for p in sorted((bd / "results").rglob("*")) if p.is_file()]
            ok = (bd / "results" / "predicted_topologies.3line").exists()
            rec["status"] = "complete" if ok else "failed"; rec["completed_utc"] = now()
            if not ok: rec["error"] = "no predicted_topologies.3line in results"
        except Exception as e:
            rec["status"] = "failed"; rec["error"] = repr(e)[:500]
        save(rp, rec); print(key, "DeepTMHMM", b["batch"], rec["status"], rec.get("job_id"), flush=True)

# ---------------- TOPCONS2 ----------------
WSDL = "https://topcons.net/pred/api_submitseq/?wsdl"
_client = None
def client():
    global _client
    if _client is None:
        from suds.client import Client
        _client = Client(WSDL, cache=None)
    return _client

def topcons_active(keys):
    n = 0
    for k in keys:
        for jp in (project_dir(k) / "raw" / "TOPCONS2").glob("*.job.json"):
            if (load(jp) or {}).get("status") == "submitted": n += 1
    return n

def topcons_submit_next(key, keys):
    pd = project_dir(key); rd = pd / "raw" / "TOPCONS2"
    for b in plan(key, "TOPCONS2")["batches"]:
        rp = rd / f"{b['batch']}.job.json"; rec = load(rp)
        if rec and rec.get("jobid"): continue
        if topcons_active(keys) >= TOPCONS_MAX_ACTIVE: return False
        fa = (pd / b["fasta"]).read_text(); assert len(fa.encode()) < 9 * 1024 * 1024
        rec = {"method": "TOPCONS2", "wsdl": WSDL, **b, "jobname": f"dsc_{key}_{b['batch']}", "fixtop": "", "email": "", "submitted_utc": now()}
        try:
            s = [str(x) for x in client().service.submitjob(fa, "", rec["jobname"], "")[0]]
            rec.update({"raw_return": s, "jobid": s[0] if s[0] not in ("None", "") else None, "result_url": s[1], "numseq_accepted": s[2], "error": s[3], "warning": s[4]})
            if rec["jobid"] and str(rec["numseq_accepted"]) != str(b["n_sequences"]): rec["warning_count"] = f"accepted {rec['numseq_accepted']} of {b['n_sequences']}"
            rec["status"] = "submitted" if rec["jobid"] else "rejected"
        except Exception as e:
            rec["status"] = "submit_error"; rec["error"] = repr(e)[:500]; rec.pop("jobid", None)
        save(rp, rec); print(key, "TOPCONS2 submit", b["batch"], rec["status"], rec.get("jobid"), flush=True)
        return True
    return False

TEXT_MEMBERS = re.compile(r"(^|/)(finished_seqs\.txt|stat\.txt|seq_\d+/(seq\.fa|query\.result\.txt|Topcons/reliability\.final))$")
def topcons_collect(key):
    """Poll submitted jobs; on Finished download the result zip. Keep the zip if small, otherwise archive the text members (xz) and record the zip's checksum/URL."""
    pd = project_dir(key); rd = pd / "raw" / "TOPCONS2"; pending = 0
    for jp in sorted(rd.glob("*.job.json")):
        rec = load(jp)
        if rec.get("status") != "submitted": continue
        try: s = [str(x) for x in client().service.checkjob(rec["jobid"])[0]]
        except Exception as e: print("checkjob error", e, flush=True); pending += 1; continue
        changed = rec.get("server_status") != s[0]
        if changed: rec.setdefault("checks", []).append({"utc": now(), "status": s[0]}); rec["checks"] = rec["checks"][-20:]; rec["server_status"] = s[0]
        if s[0] == "Finished":
            r = requests.get(s[1], timeout=1800); r.raise_for_status(); data = r.content
            rec.update({"result_zip_url": s[1], "result_zip_sha256": sha(data), "result_zip_bytes": len(data), "completed_utc": now()})
            name = jp.name.replace(".job.json", "")
            z = zipfile.ZipFile(io.BytesIO(data))
            if len(data) <= KEEP_ZIP_MAX_BYTES:
                atomic_write(rd / f"{rec['jobid']}.zip", data); rec["result_zip"] = f"raw/TOPCONS2/{rec['jobid']}.zip"
            else:
                buf = io.BytesIO()
                with tarfile.open(fileobj=buf, mode="w:xz") as t:
                    for m in z.namelist():
                        if TEXT_MEMBERS.search(m):
                            b = z.read(m); ti = tarfile.TarInfo(m); ti.size = len(b); ti.mtime = 0; t.addfile(ti, io.BytesIO(b))
                atomic_write(rd / f"{name}.text.tar.xz", buf.getvalue())
                rec["result_text_archive"] = f"raw/TOPCONS2/{name}.text.tar.xz"; rec["result_text_archive_sha256"] = sha(buf.getvalue())
                rec["archive_note"] = (f"Result zip ({len(data)} bytes, sha256 above) not stored because of its size (mostly per-sequence images); "
                                       "the text members needed to reproduce every prediction (seq.fa, query.result.txt, reliability.final, finished_seqs.txt, stat.txt) are archived unmodified.")
            rec["status"] = "complete"
        elif s[0] == "Failed": rec.update({"status": "failed", "error": s[2]})
        else: pending += 1
        if changed or rec.get("status") != "submitted": save(jp, rec); print(key, "TOPCONS2", jp.name, s[0], flush=True)
    return pending

def topcons_members(pd, rec):
    """Yield {name: bytes} dicts per seq dir from a stored zip or text archive."""
    files = {}
    if rec.get("result_zip") and (pd / rec["result_zip"]).exists():
        z = zipfile.ZipFile(pd / rec["result_zip"])
        for m in z.namelist():
            if TEXT_MEMBERS.search(m): files[m] = z.read(m)
    elif rec.get("result_text_archive"):
        with tarfile.open(pd / rec["result_text_archive"], "r:xz") as t:
            for m in t.getmembers():
                if m.isfile(): files[m.name] = t.extractfile(m).read()
    return files
