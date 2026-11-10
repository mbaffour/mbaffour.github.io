"""Download PHAGE-ONLY members of endolysin and spanin Pfam families, to add depth to those training sets.

Same approach as scripts/19_fetch_holin_families.py, but every query is restricted to viral taxonomy
(taxonomy_id:10239) so bacterial autolysins and host homologues are not pulled in. PF00335 (Tetraspanin) is
deliberately excluded: it is a eukaryotic family and a false name match for "spanin".

Gzipped TSVs go to data/raw/pfam_lysis/ (gitignored, bulk data) with the URL, UTC and SHA-256 of each in
provenance.json, so the download is reproducible without committing it.

Usage: python3 scripts/26_fetch_lysis_depth.py [--sleep 0.8]
"""
import argparse, gzip, hashlib, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

B = Path(__file__).resolve().parent.parent
RAW = B / "data/raw/pfam_lysis"; RAW.mkdir(parents=True, exist_ok=True)
FIELDS = ("accession,reviewed,protein_name,gene_names,organism_name,organism_id,virus_hosts,length,"
          "protein_existence,keyword,xref_pfam,xref_tcdb,ft_transmem,sequence")
FAMILIES = [
    ("PF00959", "Phage lysozyme", "endolysin"),
    ("PF05257", "CHAP domain", "endolysin"),
    ("PF01520", "Amidase_3", "endolysin"),
    ("PF01510", "Amidase_2", "endolysin"),
    ("PF18341", "PSA endolysin CBD", "endolysin"),
    ("PF31186", "Endolysin", "endolysin"),
    ("PF25309", "Endolysin-like domain", "endolysin"),
    ("PF31067", "Endolysin A", "endolysin"),
    ("PF17531", "Spanin, outer lipoprotein, T7-like", "spanin"),
    ("PF26831", "Phage spanin outer lipoprotein subunit", "spanin"),
]


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=900) as r: return r.read(), dict(r.headers)
        except Exception as e:
            if i == tries - 1: raise
            print(f"    retry {i+1}: {type(e).__name__}", flush=True); time.sleep(2 ** (i + 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sleep", type=float, default=0.8)
    a = ap.parse_args()
    pp = RAW / "provenance.json"
    prov = json.loads(pp.read_text()) if pp.exists() else {}
    for acc, name, cls in FAMILIES:
        f = RAW / f"{acc}.tsv.gz"
        if f.exists() and acc in prov:
            print(f"  {acc} cached ({prov[acc].get('rows', '?')} rows)", flush=True); continue
        q = f"xref:pfam-{acc} AND taxonomy_id:10239"
        url = (f"https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=tsv"
               f"&fields={FIELDS}&query={urllib.parse.quote(q)}")
        rec = {"pfam_id": acc, "pfam_name": name, "class": cls, "query": q, "url": url}
        try:
            data, h = get(url)
            f.write_bytes(data)
            rows = max(gzip.decompress(data).decode("utf-8", "replace").count("\n") - 1, 0)
            rec.update({"retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "rows": rows,
                        "uniprot_release": h.get("X-UniProt-Release")})
            if rows == 0: rec["note"] = "query returned 0 rows"
        except Exception as e:
            rec.update({"retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": None, "bytes": 0, "rows": 0,
                        "note": f"download failed after retries: {type(e).__name__}: {e}"})
        prov[acc] = rec
        pp.write_text(json.dumps(prov, indent=1))
        print(f"  {acc} {cls:<9} {name[:40]:<40} {rec['rows']:>7} rows  {rec.get('note', '')}", flush=True)
        time.sleep(a.sleep)
    print(f"\n{'family':<9}| {'class':<10}| rows")
    for acc, name, cls in FAMILIES:
        print(f"{acc:<9}| {cls:<10}| {prov.get(acc, {}).get('rows', 0)}")
    tot = sum(v.get("rows", 0) for v in prov.values())
    print(json.dumps({"families": len(prov), "member_rows_total": tot,
                      "by_class": {c: sum(v.get("rows", 0) for v in prov.values() if v["class"] == c)
                                   for c in ("endolysin", "spanin")},
                      "failed_or_empty": [k for k, v in prov.items() if v.get("rows", 0) == 0],
                      "megabytes": round(sum(v.get("bytes", 0) for v in prov.values()) / 1e6, 2)}, indent=1))


if __name__ == "__main__":
    main()
