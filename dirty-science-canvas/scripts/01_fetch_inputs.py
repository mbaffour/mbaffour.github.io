"""Download RefSeq GenBank records + NCBI CDS translations for every replicon; record URLs, dates, SHA-256.
Large host records are stored gzip-compressed (checksums recorded for the uncompressed bytes as downloaded and for the .gz).
Skips files already present (provenance keeps the original retrieval time). Usage: python3 scripts/01_fetch_inputs.py [--org k1,k2]"""
import datetime, gzip, hashlib, json, sys, time, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import ORGANISMS, project_dir, selected
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=300) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < tries - 1: time.sleep(2 ** (i + 1)); continue
            raise
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
for key in selected(sys.argv):
    o = ORGANISMS[key]; d = project_dir(key) / "inputs"; d.mkdir(parents=True, exist_ok=True)
    pp = d / "provenance.json"; old = json.loads(pp.read_text()) if pp.exists() else {}
    oldfiles = {f["file"]: f for f in old.get("files", [])}
    prov = {"organism": o["name"], "accessions": o["accessions"], "files": [], "ncbi_summaries": []}
    compress = o["kind"] == "host"
    for acc in o["accessions"]:
        kinds = [("gbwithparts", f"{acc}.gb"), ("fasta_cds_aa", f"{acc}.cds_aa.fasta")] + ([] if compress else [("fasta", f"{acc}.fna")])
        for rettype, fname in kinds:
            url = f"{EU}efetch.fcgi?db=nuccore&id={acc}&rettype={rettype}&retmode=text"
            gz = compress and rettype == "gbwithparts"
            target = d / (fname + ".gz" if gz else fname); rel = f"inputs/{target.name}"
            if target.exists() and rel in oldfiles: prov["files"].append(oldfiles[rel]); continue
            data = get(url); time.sleep(1.0)
            rec = {"file": rel, "url": url, "retrieved_utc": now(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            if gz:
                target.write_bytes(gzip.compress(data, mtime=0)); rec["sha256_gz"] = hashlib.sha256(target.read_bytes()).hexdigest(); rec["note"] = "stored gzip-compressed; sha256/bytes refer to the uncompressed download"
            else: target.write_bytes(data)
            prov["files"].append(rec); print(key, rel, len(data))
        s = json.loads(get(f"{EU}esummary.fcgi?db=nuccore&id={acc}&retmode=json")); time.sleep(1.0)
        r = s["result"][s["result"]["uids"][0]]
        prov["ncbi_summaries"].append({k: r.get(k) for k in ["accessionversion", "title", "slen", "createdate", "updatedate", "taxid", "biomol", "topology"]})
    if "ncbi_summary" in old and len(o["accessions"]) == 1: prov["ncbi_summary"] = prov["ncbi_summaries"][0]
    prov["ncbi_summary"] = prov["ncbi_summaries"][0]
    pp.write_text(json.dumps(prov, indent=2)); print(key, "ok", [x["title"] for x in prov["ncbi_summaries"]])
