"""Download an unlabelled pool of phage proteomes to mine for new holins, and record each protein's genomic neighbourhood.

The neighbourhood is the key to a safe self-training loop: a candidate is only accepted later if an *independent* signal
agrees with the model, and that signal is "this ORF sits next to an annotated endolysin or spanin". The classifier never
sees context as a feature, so context is not the model agreeing with itself.

Genomes already used in the benchmark (scripts/06) are excluded so the mined pool cannot contaminate that test.
Usage: python3 scripts/08_mine_pool.py [--n 300]
"""
import argparse, hashlib, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib
S = importlib.import_module("05_scan_genome")
BM = importlib.import_module("06_benchmark_genomes")

B = Path(__file__).resolve().parent.parent
POOL = B / "data/raw/pool"; POOL.mkdir(parents=True, exist_ok=True)
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
QUERY = 'Caudoviricetes[Organism] AND "complete genome"[Title] AND refseq[filter] AND 10000:200000[SLEN]'
# A bare "lysis" matched T4's rI/rIIA/rIIB "lysis inhibitor" genes, counting lysis INHIBITION as evidence of a
# lysis cassette. Spanins are excluded as evidence too: the membrane cross-check (scripts/11) shows Rz-like spanins
# score 0.74-0.96 themselves, so a spanin neighbour cannot distinguish a holin from another spanin.
LYSIS = re.compile(r"endolysin|lysozyme|amidase|peptidoglycan hydrolase|murein hydrolase|glycosyl hydrolase", re.I)
LYSIS_WEAK = re.compile(r"spanin|\brz\b|rz1", re.I)
NOT_LYSIS = re.compile(r"inhibit", re.I)
HOLIN_WORD = re.compile(r"holin", re.I)


def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=600) as r: return r.read()
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 ** (i + 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=300)
    a = ap.parse_args()
    exclude = {acc.split(".")[0] for acc, _, _ in BM.GENOMES}
    idp = POOL / "accessions.json"
    if idp.exists(): accs = json.loads(idp.read_text())
    else:
        d = json.loads(get(f"{EU}esearch.fcgi?db=nuccore&retmax=4000&retmode=json&term={urllib.parse.quote(QUERY)}"))
        uids = d["esearchresult"]["idlist"]; accs = []
        for i in range(0, len(uids), 200):
            s = json.loads(get(f"{EU}esummary.fcgi?db=nuccore&retmode=json&id={','.join(uids[i:i+200])}"))["result"]
            accs += [s[u]["accessionversion"] for u in s["uids"]]; time.sleep(0.5)
        accs = sorted({x for x in accs if x.split(".")[0] not in exclude})
        idp.write_text(json.dumps(accs)); print(f"{len(accs)} candidate genomes", flush=True)
    accs = accs[:a.n]
    prov = json.loads((POOL / "provenance.json").read_text()) if (POOL / "provenance.json").exists() else {}
    out = []
    for k, acc in enumerate(accs, 1):
        f = POOL / f"{acc}.gb"
        if not f.exists():
            url = f"{EU}efetch.fcgi?db=nuccore&id={acc}&rettype=gbwithparts&retmode=text"
            b = get(url); f.write_bytes(b); time.sleep(0.4)
            prov[acc] = {"url": url, "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
        try: prots = S.annotated_proteins(f)
        except Exception as e: print("parse failed", acc, e, flush=True); continue
        prots.sort(key=lambda p: p["start"])
        for i, p in enumerate(prots):
            window = prots[max(0, i - 3):i + 4]
            near = [w["product"] for w in window if w is not p and LYSIS.search(w["product"] or "")
                    and not NOT_LYSIS.search(w["product"] or "")]
            weak = [w["product"] for w in window if w is not p and LYSIS_WEAK.search(w["product"] or "")]
            p.update({"accession": acc, "index": i, "n_in_genome": len(prots),
                      "lysis_neighbours": near[:3], "has_lysis_neighbour": bool(near),
                      "spanin_neighbours": weak[:3],
                      "annotated_holin": bool(HOLIN_WORD.search(p["product"] or ""))})
        out += [p for p in prots if 20 <= len(p["sequence"]) <= 2000]
        if k % 25 == 0: print(f"  {k}/{len(accs)} genomes, {len(out)} proteins", flush=True)
    (POOL / "provenance.json").write_text(json.dumps(prov, indent=1))
    uniq = {}
    for p in out: uniq.setdefault(p["sequence"], p)
    pool = list(uniq.values())
    (B / "data/processed/pool.json").write_text(json.dumps(pool))
    print(json.dumps({"genomes": len(accs), "proteins": len(out), "unique_sequences": len(pool),
                      "with_lysis_neighbour": sum(p["has_lysis_neighbour"] for p in pool),
                      "annotated_holin": sum(p["annotated_holin"] for p in pool)}, indent=1))


if __name__ == "__main__":
    main()
