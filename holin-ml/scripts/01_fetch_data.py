"""Download training/evaluation sources with provenance (URL, UTC time, SHA-256).
- UniProtKB Swiss-Prot entries named or classified as holin / antiholin (with evidence fields)
- Swiss-Prot bacteriophage proteins (negative pool candidates) and Swiss-Prot bacterial small membrane proteins (hard negatives)
- TCDB: all sequences + family names (holin superfamily 1.E)
- InterPro: Pfam entries whose name/description mention holin
Re-running skips files already present."""
import datetime, hashlib, json, sys, time, urllib.parse, urllib.request
from pathlib import Path
R = Path(__file__).resolve().parent.parent / "data" / "raw"; R.mkdir(parents=True, exist_ok=True)
FIELDS = "accession,id,reviewed,protein_name,gene_names,organism_name,organism_id,lineage_ids,virus_hosts,length,protein_existence,protein_families,cc_function,keyword,ft_transmem,xref_pfam,xref_interpro,xref_tcdb,sequence"
QUERIES = {
    "sp_holin": "reviewed:true AND (protein_name:holin OR family:holin OR protein_name:antiholin OR protein_name:pinholin)",
    "sp_phage": "reviewed:true AND taxonomy_id:10239 AND virus_host_id:2",
    "sp_bact_small_tm": "reviewed:true AND taxonomy_id:2 AND length:[30 TO 250] AND ft_transmem:*",
    "tr_holin_family": "reviewed:false AND family:holin",
}
prov_path = R / "provenance.json"; prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=600) as r: return r.read(), dict(r.headers)
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 ** (i + 1))
def save(name, url, data, extra=None):
    (R / name).write_bytes(data)
    prov[name] = {"url": url, "retrieved_utc": now(), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), **(extra or {})}
    prov_path.write_text(json.dumps(prov, indent=2)); print(name, len(data), flush=True)
for name, q in QUERIES.items():
    fn = f"uniprot_{name}.tsv.gz"
    if (R / fn).exists(): continue
    url = f"https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=tsv&fields={FIELDS}&query={urllib.parse.quote(q)}"
    data, h = get(url); save(fn, url, data, {"query": q, "uniprot_release": h.get("X-UniProt-Release"), "uniprot_release_date": h.get("X-UniProt-Release-Date")})
for fn, url in [("tcdb.fasta", "https://www.tcdb.org/public/tcdb"), ("tcdb_families.tsv", "https://www.tcdb.org/cgi-bin/projectv/public/families.py")]:
    if not (R / fn).exists(): data, _ = get(url); save(fn, url, data)
if not (R / "interpro_pfam_holin.json").exists():
    url = "https://www.ebi.ac.uk/interpro/api/entry/pfam/?search=holin&page_size=200"
    data, _ = get(url); save("interpro_pfam_holin.json", url, data)
