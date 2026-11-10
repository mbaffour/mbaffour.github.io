"""Fetch endolysin and spanin sources, to build class models alongside the holin model.

The lysis cassette is holin + endolysin + spanin. We already model holins; this adds the other two so a phage
genome can be scanned for all three. The pipeline (features.py, 03_cluster.py homology clustering, frozen gold
holdout, leave-one-genome-out eval on the 16 atlas phages) is reused unchanged -- only the positive class differs.

Staged, cheap first (like the holin build): this script pulls the REVIEWED UniProt sets and the InterPro Pfam
family LISTS only. The Pfam family MEMBER dumps (which for endolysin domains can run to 100k+ bacterial/eukaryotic
lysozymes) are fetched by scripts/26 for only the phage-relevant families, after inspecting sizes here.

Endolysins are enzymatically diverse (lysozyme, amidase, peptidase, transglycosylase, CHAP), so the query is by
the common phage-lysis protein NAMES, reviewed only, to stay high-quality and bounded. Spanins are small and few.

Usage: python3 scripts/25_fetch_lysis_sources.py
"""
import datetime, hashlib, json, time, urllib.parse, urllib.request
from pathlib import Path

B = Path(__file__).resolve().parent.parent
R = B / "data/raw"; R.mkdir(parents=True, exist_ok=True)
FIELDS = ("accession,id,reviewed,protein_name,gene_names,organism_name,organism_id,lineage_ids,virus_hosts,"
          "length,protein_existence,protein_families,keyword,ft_transmem,xref_pfam,xref_interpro,xref_tcdb,sequence")
UNIPROT = {
    "sp_endolysin": ('reviewed:true AND (protein_name:endolysin OR protein_name:"phage lysin" OR '
                     'protein_name:"peptidoglycan hydrolase" OR protein_name:"N-acetylmuramoyl-L-alanine amidase" OR '
                     'protein_name:"lysozyme RrrD" OR protein_name:"murein hydrolase")'),
    "sp_spanin": ('reviewed:true AND (protein_name:spanin OR protein_name:"Rz" OR protein_name:"Rz1" OR '
                  'gene:rz OR gene:rz1)'),
}
INTERPRO = {"interpro_pfam_endolysin.json": "endolysin", "interpro_pfam_spanin.json": "spanin"}

pp = R / "provenance.json"
prov = json.loads(pp.read_text()) if pp.exists() else {}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=600) as r: return r.read(), dict(r.headers)
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 ** (i + 1))


def save(name, url, data, extra=None):
    (R / name).write_bytes(data)
    prov[name] = {"url": url, "retrieved_utc": now(), "sha256": hashlib.sha256(data).hexdigest(),
                  "bytes": len(data), **(extra or {})}
    pp.write_text(json.dumps(prov, indent=1))


for name, q in UNIPROT.items():
    fn = f"uniprot_{name}.tsv.gz"
    if (R / fn).exists(): print(f"{fn} cached"); continue
    url = f"https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=tsv&fields={FIELDS}&query={urllib.parse.quote(q)}"
    data, h = get(url); save(fn, url, data, {"query": q, "uniprot_release": h.get("X-UniProt-Release")})
    import gzip
    print(f"{fn}: {gzip.decompress(data).decode('utf-8','replace').count(chr(10))-1} rows")

for fn, term in INTERPRO.items():
    if (R / fn).exists(): print(f"{fn} cached"); continue
    url = f"https://www.ebi.ac.uk/interpro/api/entry/pfam/?search={term}&page_size=200"
    data, _ = get(url); save(fn, url, data)
    entries = json.loads(data).get("results", [])
    print(f"{fn}: {len(entries)} Pfam entries matching '{term}'")
    for e in entries[:60]:
        m = e["metadata"]; print(f"    {m['accession']}  {m['name']}")
