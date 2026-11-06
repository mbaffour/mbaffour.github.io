"""Download reference GenBank records and NCBI CDS translations; record provenance."""
import hashlib, json, sys, time, datetime, urllib.request
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from config import PHAGES, project_dir
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
def get(url):
    with urllib.request.urlopen(url, timeout=60) as r: return r.read()
for key, p in PHAGES.items():
    d = project_dir(key) / "inputs"; d.mkdir(parents=True, exist_ok=True)
    prov = {"accession": p["accession"], "files": []}
    for rettype, fname in [("gbwithparts", f"{p['accession']}.gb"), ("fasta_cds_aa", f"{p['accession']}.cds_aa.fasta"), ("fasta", f"{p['accession']}.fna")]:
        url = f"{EU}efetch.fcgi?db=nuccore&id={p['accession']}&rettype={rettype}&retmode=text"
        if (d / fname).exists():
            data = (d / fname).read_bytes()
        else:
            data = get(url); (d / fname).write_bytes(data); time.sleep(1.5)
        prov["files"].append({"file": f"inputs/{fname}", "url": url, "retrieved_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    time.sleep(1.5); summ = json.loads(get(f"{EU}esummary.fcgi?db=nuccore&id={p['accession']}&retmode=json"))
    uid = summ["result"]["uids"][0]; r = summ["result"][uid]
    prov["ncbi_summary"] = {k: r.get(k) for k in ["accessionversion", "title", "slen", "createdate", "updatedate", "taxid", "biomol", "topology"]}
    prov_path = d / "provenance.json"
    if prov_path.exists():  # keep original retrieval timestamps
        old = json.loads(prov_path.read_text()); prov["files"] = old["files"]
    prov_path.write_text(json.dumps(prov, indent=2))
    print(key, prov["ncbi_summary"])
