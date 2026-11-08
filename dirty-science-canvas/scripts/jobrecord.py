"""Atomic, resumable job records for predictor submissions."""
import datetime, hashlib, json, os, tempfile
from pathlib import Path
def sha(b): return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
def atomic_write(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_")
    with os.fdopen(fd, "wb") as fh: fh.write(data if isinstance(data, bytes) else data.encode())
    os.replace(tmp, path)
def load(path):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else None
def save(path, rec): atomic_write(path, json.dumps(rec, indent=2))
