"""Phobius JSON API (documented at https://phobius.sbc.su.se/api): primary Phobius source, incl. per-sequence SVG posterior plots.
Also saves the plain-text long and short formats from /api/predict.txt. Resumable."""
import json, sys, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir
from jobrecord import sha, now, atomic_write, load, save
B = "https://phobius.sbc.su.se/api/"
for key in PHAGES:
    pd = project_dir(key); rd = pd / "raw" / "Phobius"; fa = (pd / "inputs" / "proteins_submitted.fasta").read_text()
    rec_path = rd / "batch1_api.job.json"; rec = load(rec_path)
    if rec and rec.get("status") == "complete": print(key, "complete"); continue
    rec = {"method": "Phobius", "endpoint": B + "predict", "batch": 1, "fasta": "raw/Phobius/batch1.fasta", "fasta_sha256": sha(fa), "submitted_utc": now(), "settings": {"plot": True}, "outputs": {}}
    r = requests.post(B + "predict", json={"sequence": fa, "plot": True}, timeout=600); r.raise_for_status()
    atomic_write(rd / "batch1_api.json", r.content); rec["outputs"]["json"] = {"file": "raw/Phobius/batch1_api.json", "sha256": sha(r.content)}
    for suffix, params in [("long", {}), ("short", {"format": "short"})]:
        t = requests.post(B + "predict.txt", params=params, json={"sequence": fa}, timeout=600); t.raise_for_status()
        atomic_write(rd / f"batch1_api_{suffix}.txt", t.content); rec["outputs"][suffix] = {"file": f"raw/Phobius/batch1_api_{suffix}.txt", "sha256": sha(t.content)}
    preds = r.json()["predictions"]
    for p in preds:
        if p.get("svg"):
            b = p["svg"].encode(); f = rd / "plots" / f"{p['id']}.svg"; atomic_write(f, b)
            rec["outputs"].setdefault("plots", []).append({"file": f"raw/Phobius/plots/{f.name}", "sha256": sha(b)})
    rec["returned_ids"] = [p["id"] for p in preds]; rec["status"] = "complete"; rec["completed_utc"] = now(); rec["http_status"] = r.status_code
    save(rec_path, rec); print(key, len(preds))
