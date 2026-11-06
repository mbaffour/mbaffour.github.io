"""Run DeepTMHMM (DTU/DeepTMHMM on BioLib, https://dtu.biolib.com/DeepTMHMM) on each phage's exact FASTA via the pybiolib Python API.
Resumable: skips batches with status complete; never resubmits a batch with an active job record."""
import shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir
from jobrecord import sha, now, atomic_write, load, save
import biolib
only = sys.argv[1:] or list(PHAGES)
for key in only:
    bd = project_dir(key) / "raw" / "DeepTMHMM" / "batch1"; rec_path = bd.parent / "batch1.job.json"; rec = load(rec_path)
    if rec and rec.get("status") in ("complete", "running"): print(key, "skip", rec["status"]); continue
    fa = (project_dir(key) / "inputs" / "proteins_submitted.fasta").read_text()
    atomic_write(bd / "batch1.fasta", fa)
    rec = {"method": "DeepTMHMM", "service": "BioLib app DTU/DeepTMHMM", "client": f"pybiolib {biolib.__version__ if hasattr(biolib,'__version__') else ''}".strip(),
           "batch": 1, "fasta": "raw/DeepTMHMM/batch1/batch1.fasta", "fasta_sha256": sha(fa), "n_sequences": fa.count(">"), "args": ["--fasta", "batch1.fasta"],
           "submitted_utc": now(), "status": "running"}
    save(rec_path, rec)
    try:
        app = biolib.load("DTU/DeepTMHMM")
        try: rec["app_version"] = app._app_version["app_uri"]; rec["app_version_published"] = app._app_version.get("created_at")
        except Exception: rec["app_version"] = None
        import os; cwd = os.getcwd(); os.chdir(bd)
        try: job = app.cli(args=["--fasta", "batch1.fasta"], blocking=True)
        finally: os.chdir(cwd)
        rec["job_id"] = getattr(job, "id", None)
        job.save_files(str(bd / "results"))
        rec["outputs"] = [{"file": str(p.relative_to(project_dir(key))), "sha256": sha(p.read_bytes())} for p in sorted((bd / "results").rglob("*")) if p.is_file()]
        rec["status"] = "complete"; rec["completed_utc"] = now()
    except Exception as e:
        rec["status"] = "failed"; rec["error"] = repr(e)
    save(rec_path, rec); print(key, rec["status"], rec.get("job_id"), rec.get("error"))
