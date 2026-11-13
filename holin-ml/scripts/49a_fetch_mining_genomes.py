"""Download the genomes scripts/49 mines for new holin families: every RefSeq complete tailed-phage genome.

Query (NCBI nuccore): "Caudoviricetes"[Organism] AND srcdb_refseq[PROP] AND complete genome[Title]
Records are fetched 100 at a time (efetch, gbwithparts) and split into data/raw/mine/<accession>.gb; files already
present are skipped, so an interrupted run resumes where it stopped. The accession list and query date are written to
data/raw/mine/accessions.json (committed); the GenBank files are not (gitignored, regenerable from that list).

Usage: python3 scripts/49a_fetch_mining_genomes.py [--max N] [--time-limit SECONDS]
"""
import argparse, json, re, time, urllib.parse, urllib.request
from pathlib import Path
B = Path(__file__).resolve().parent.parent
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
QUERY = '"Caudoviricetes"[Organism] AND srcdb_refseq[PROP] AND complete genome[Title]'
OUT = B / "data/raw/mine"


def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=300) as r: return r.read().decode()
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 ** (i + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=100000)
    ap.add_argument("--time-limit", type=float, default=1e9, help="stop cleanly after this many seconds")
    a = ap.parse_args()
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    meta = OUT / "accessions.json"
    if meta.exists():
        accs = json.loads(meta.read_text())["accessions"]
    else:
        q = urllib.parse.quote(QUERY)
        n = int(json.loads(get(f"{EU}/esearch.fcgi?db=nuccore&term={q}&retmax=0&retmode=json"))["esearchresult"]["count"])
        accs = []
        for start in range(0, n, 5000):
            r = json.loads(get(f"{EU}/esearch.fcgi?db=nuccore&term={q}&retstart={start}&retmax=5000&retmode=json&idtype=acc"))
            accs += r["esearchresult"]["idlist"]; time.sleep(0.4)
        meta.write_text(json.dumps({"query": QUERY, "date": time.strftime("%Y-%m-%d"), "n": len(accs),
                                    "accessions": accs}, indent=0))
    accs = accs[:a.max]
    todo = [x for x in accs if not (OUT / f"{x}.gb").exists()]
    print(f"{len(accs)} accessions, {len(todo)} to fetch", flush=True)
    for i in range(0, len(todo), 100):
        if time.time() - t0 > a.time_limit: print("time limit reached; rerun to resume", flush=True); break
        batch = todo[i:i + 100]
        txt = get(f"{EU}/efetch.fcgi?db=nuccore&id={','.join(batch)}&rettype=gbwithparts&retmode=text")
        n = 0
        for rec in txt.split("\n//\n"):
            m = re.search(r"^VERSION\s+(\S+)", rec, re.M)
            if m and rec.strip():
                (OUT / f"{m.group(1)}.gb").write_text(rec.strip("\n") + "\n//\n"); n += 1
        print(f"  {i + len(batch)}/{len(todo)}: wrote {n}", flush=True); time.sleep(0.4)
    print(f"have {sum(1 for x in accs if (OUT / f'{x}.gb').exists())}/{len(accs)}", flush=True)


if __name__ == "__main__":
    main()
