"""Submit each phage's exact protein FASTA to the Phobius server (phobius.sbc.su.se), formats 'nog' (long, no graphics) and 'short'.
One batch per phage (limits: 100 sequences, 50,000 residues per request, as stated on the server form). Resumable: completed batches are not resubmitted."""
import sys, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir
from jobrecord import sha, now, atomic_write, load, save
URL = "https://phobius.sbc.su.se/predict"
for key in PHAGES:
    pd = project_dir(key); fa = (pd / "inputs" / "proteins_submitted.fasta").read_text()
    n = fa.count(">"); res = sum(len(l) for l in fa.splitlines() if not l.startswith(">"))
    assert n <= 100 and res <= 50000, "batch exceeds documented limit; split required"
    for fmt in ["nog", "short"]:
        rd = pd / "raw" / "Phobius"; rec_path = rd / f"batch1_{fmt}.job.json"
        rec = load(rec_path)
        if rec and rec.get("status") == "complete": print(key, fmt, "already complete"); continue
        batch_fa = rd / "batch1.fasta"; atomic_write(batch_fa, fa)
        rec = {"method": "Phobius", "server": URL, "batch": 1, "format": fmt, "fasta": "raw/Phobius/batch1.fasta", "fasta_sha256": sha(fa),
               "n_sequences": n, "n_residues": res, "submitted_utc": now(), "submission": "multipart/form-data POST (protseq file field, format radio)"}
        r = requests.post(URL, files={"protfile": ("batch1.fasta", fa, "text/plain")}, data={"format": fmt}, timeout=300)
        rec["http_status"] = r.status_code; rec["final_url"] = r.url
        out = rd / f"batch1_{fmt}.html"; atomic_write(out, r.content)
        rec["output"] = f"raw/Phobius/{out.name}"; rec["output_sha256"] = sha(r.content)
        rec["status"] = "complete" if r.ok else "failed"; rec["completed_utc"] = now()
        save(rec_path, rec); print(key, fmt, r.status_code, len(r.content))
