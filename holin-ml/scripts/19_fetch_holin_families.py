"""Download the members of every Pfam holin family, to cover the architectures the training set is missing.

The model generalises to small multi-TM class I holins and to little else (reports/family_dependence.json): T4
holin T and T5 C1 are recognised only when their own family is in training, and the actinobacterial families sit
at 0.00 leave-one-family-out recall. The training set has 558 holins, 52 of them longer than 150 aa, so there is
nothing for those architectures to generalise from.

InterPro lists 38 Pfam families whose name is a holin (data/raw/interpro_pfam_holin.json), and they include
exactly the gaps: PF11031 Bacteriophage T holin (T4 t), PF27028 T1 holin, PF07332 Actinobacterial Holin-X,
PF04020 and PF16081 mycobacterial holins, PF37872 Actinomycetota holin, PF26844 phiKMV, PF16938 Dp-1.

Three of the 38 are ANTIHOLIN families (PF16084 LydA-holin antagonist, PF24205 T4-like virus antiholin,
PF28015 Antiholin LysA-like). They are downloaded too but recorded separately: an antiholin is not a holin, and
mislabelling them would repeat the dual-start conflict that deleted lambda S from an earlier dataset.

Full member lists are kept in data/raw/pfam/ (gitignored, several hundred MB) with the URL, UTC and SHA-256 of
each in provenance.json, so the download is reproducible without committing it. scripts/20 does the curation.

Usage: python3 scripts/19_fetch_holin_families.py [--sleep 1.0]
"""
import argparse, hashlib, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

B = Path(__file__).resolve().parent.parent
RAW = B / "data/raw/pfam"; RAW.mkdir(parents=True, exist_ok=True)
FIELDS = ("accession,reviewed,protein_name,gene_names,organism_name,organism_id,virus_hosts,length,"
          "protein_existence,keyword,xref_pfam,xref_tcdb,ft_transmem,sequence")
# names that match "holin" in InterPro but are nothing to do with lysis
NOT_HOLIN = re.compile(r"choline|cholinesterase|carnitine|betaine|sulfatase|kinase|acyltransferase|"
                       r"cell wall binding", re.I)
ANTIHOLIN = re.compile(r"antiholin|anti-holin|antagonist", re.I)


def get(url, tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=900) as r: return r.read(), dict(r.headers)
        except Exception as e:
            if i == tries - 1: raise
            print(f"    retry {i+1}: {type(e).__name__}", flush=True); time.sleep(2 ** (i + 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sleep", type=float, default=1.0)
    a = ap.parse_args()
    entries = json.load(open(B / "data/raw/interpro_pfam_holin.json"))["results"]
    fams = [(r["metadata"]["accession"], r["metadata"]["name"]) for r in entries
            if not NOT_HOLIN.search(r["metadata"]["name"])]
    fams.sort()
    print(f"{len(fams)} holin Pfam families ({sum(bool(ANTIHOLIN.search(n)) for _, n in fams)} of them antiholin)", flush=True)

    pp = RAW / "provenance.json"
    prov = json.loads(pp.read_text()) if pp.exists() else {}
    for acc, name in fams:
        f = RAW / f"{acc}.tsv.gz"
        if f.exists() and acc in prov:
            print(f"  {acc} cached ({prov[acc].get('rows', '?')} rows)", flush=True); continue
        q = f"xref:pfam-{acc}"
        url = (f"https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=tsv"
               f"&fields={FIELDS}&query={urllib.parse.quote(q)}")
        data, h = get(url)
        f.write_bytes(data)
        import gzip
        rows = gzip.decompress(data).decode("utf-8", "replace").count("\n") - 1
        prov[acc] = {"pfam_name": name, "is_antiholin_family": bool(ANTIHOLIN.search(name)), "query": q,
                     "url": url, "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "rows": rows,
                     "uniprot_release": h.get("X-UniProt-Release")}
        pp.write_text(json.dumps(prov, indent=1))
        print(f"  {acc} {name[:46]:<46} {rows:>7} members  {len(data)/1e6:.1f} MB", flush=True)
        time.sleep(a.sleep)
    tot = sum(v.get("rows", 0) for v in prov.values())
    anti = sum(v.get("rows", 0) for v in prov.values() if v.get("is_antiholin_family"))
    print(json.dumps({"families": len(prov), "member_rows_total": tot, "of_which_antiholin_families": anti,
                      "megabytes": round(sum(v.get("bytes", 0) for v in prov.values()) / 1e6, 1)}, indent=1))


if __name__ == "__main__":
    main()
