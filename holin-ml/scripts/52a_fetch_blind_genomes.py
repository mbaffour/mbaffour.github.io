"""Select and download the genomes for the BLIND scan (scripts/52b), then seal their annotations.

Selection, fixed before any genome is scanned or any annotation is read:
  - NCBI nuccore: "Caudoviricetes"[Organism] AND complete genome[Title], published 2026/06/01 onward (PDAT), GenBank
    only (no RefSeq copies) -- deposited after the training data were assembled
  - not an evaluation or training-pool genome (CPT, experimental set, panels, pool, the 5,247 mining genomes), by
    accession and by DNA
  - at least 10 annotated CDS (counted, product names not read), so the annotation can score the scan afterwards
  - at most 15 genomes per host genus (first word of the organism name), then a seeded random sample of --n

Outputs:
  data/raw/blind/selection.json   accessions, query, seed (committed)
  data/raw/blind/fna/<acc>.fna    DNA only: the scan's ONLY input
  data/raw/blind/sealed/<acc>.gb  full GenBank records, read only by the scoring step (scripts/52c)
Usage: python3 scripts/52a_fetch_blind_genomes.py [--n 200] [--seed 0]
"""
import argparse, glob, hashlib, importlib, json, random, re, sys, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
QUERY = '"Caudoviricetes"[Organism] AND complete genome[Title] AND 2026/06/01:3000/12/31[PDAT] NOT srcdb_refseq[PROP]'
OUT = B / "data/raw/blind"
EXCLUDE = ["data/raw/cpt/genomes/*.gb", "data/raw/validated/genomes/*.gb", "data/raw/panel/*.gb",
           "data/raw/genomes/*.gb", "data/raw/pool/*.gb", "data/raw/mine/*.gb"]


def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=300) as r: return r.read().decode()
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 ** (i + 1))


def dna_hash(s):
    from Bio.Seq import Seq
    s = s.upper(); return hashlib.sha1(min(s, str(Seq(s).reverse_complement())).encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--per-genus", type=int, default=15)
    a = ap.parse_args()
    from Bio import SeqIO
    import io
    for d in ("fna", "sealed", "_all"): (OUT / d).mkdir(parents=True, exist_ok=True)

    ex_acc, ex_dna = set(), set()
    for g in EXCLUDE:
        for p in glob.glob(str(B / g)):
            try:
                r = next(SeqIO.parse(p, "genbank")); ex_acc.add(r.id.split(".")[0]); ex_dna.add(dna_hash(str(r.seq)))
            except Exception: pass
    print(f"excluded: {len(ex_acc)} accessions already used for evaluation, training or mining", flush=True)

    q = urllib.parse.quote(QUERY)
    accs = json.loads(get(f"{EU}/esearch.fcgi?db=nuccore&term={q}&retmax=5000&retmode=json&idtype=acc"))["esearchresult"]["idlist"]
    print(f"{len(accs)} genomes match the query", flush=True)
    for i in range(0, len(accs), 100):
        batch = [x for x in accs[i:i + 100] if not (OUT / "_all" / f"{x}.gb").exists()]
        if not batch: continue
        txt = get(f"{EU}/efetch.fcgi?db=nuccore&id={','.join(batch)}&rettype=gbwithparts&retmode=text")
        for rec in txt.split("\n//\n"):
            m = re.search(r"^VERSION\s+(\S+)", rec, re.M)
            if m and rec.strip(): (OUT / "_all" / f"{m.group(1)}.gb").write_text(rec.strip("\n") + "\n//\n")
        time.sleep(0.4)

    elig, seen = defaultdict(list), set()
    for p in sorted(glob.glob(str(OUT / "_all/*.gb"))):
        try: r = next(SeqIO.parse(p, "genbank"))
        except Exception: continue
        k = dna_hash(str(r.seq))
        if r.id.split(".")[0] in ex_acc or k in ex_dna or k in seen: continue
        n_cds = sum(1 for f in r.features if f.type == "CDS")          # counted only; products are not read
        if n_cds < 10 or not str(r.seq).strip("Nn"): continue
        seen.add(k)
        genus = (r.annotations.get("organism", "") or "unknown").split()[0]
        elig[genus].append(r.id)
    rng = random.Random(a.seed); pool = []
    for g in sorted(elig):
        v = sorted(elig[g]); rng.shuffle(v); pool += v[:a.per_genus]
    rng.shuffle(pool); pick = sorted(pool[:a.n])
    for acc in pick:
        r = next(SeqIO.parse(OUT / "_all" / f"{acc}.gb", "genbank"))
        (OUT / "fna" / f"{acc}.fna").write_text(f">{acc}\n{str(r.seq)}\n")
        (OUT / "sealed" / f"{acc}.gb").write_text((OUT / "_all" / f"{acc}.gb").read_text())
    (OUT / "selection.json").write_text(json.dumps({
        "query": QUERY, "date": time.strftime("%Y-%m-%d"), "seed": a.seed, "per_genus_cap": a.per_genus,
        "n_matching": len(accs), "n_eligible": sum(len(v) for v in elig.values()), "n_genera": len(elig),
        "genera_in_sample": dict(sorted(defaultdict(int, {g: sum(1 for x in pick if x in elig[g]) for g in elig}).items())),
        "accessions": pick}, indent=1))
    print(f"{sum(len(v) for v in elig.values())} eligible in {len(elig)} host genera; sampled {len(pick)}", flush=True)


if __name__ == "__main__":
    main()
