"""Benchmark built on Center for Phage Technology (CPT) genomes, whose lysis genes are curated by hand.

CPT annotates lysis genes manually with a controlled vocabulary (holin / pinholin, endolysin / SAR endolysin,
i-spanin / o-spanin / u-spanin), so these labels are expert curation rather than automatic transfer. They are still
annotation, not experiment: the experimental benchmark is scripts/43. Truth here comes only from that vocabulary on
CPT-curated genomes; the models never see it -- they score sequence alone, and with --de-novo the annotation is
discarded and genes are called from bare DNA.

Usage: python3 scripts/44_fetch_cpt.py   writes data/raw/cpt/{genomes/*.gb, truth.json, summary.json}
"""
import importlib, json, re, sys, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
S5 = importlib.import_module("05_scan_genome")
B = Path(__file__).resolve().parent.parent
OUT = B / "data/raw/cpt"
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
QUERY = '"Center for Phage Technology"[All Fields] AND viruses[filter]'
VOCAB = {"holin": re.compile(r"\b(pin)?holin\b", re.I),
         "endolysin": re.compile(r"endolysin", re.I),
         "spanin": re.compile(r"spanin", re.I)}
NOT = re.compile(r"anti-?holin|internal virion protein", re.I)   # antiholins; virion (entry) lysins, excluded everywhere


def get(url, tries=5):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=180) as r: return r.read().decode()
        except Exception:
            if k == tries - 1: raise
            time.sleep(2 ** k)


def main():
    gdir = OUT / "genomes"; gdir.mkdir(parents=True, exist_ok=True)
    if "--no-download" in sys.argv: return label(gdir)
    ids = json.loads(get(EU + "esearch.fcgi?" + urllib.parse.urlencode(
        {"db": "nuccore", "term": QUERY, "retmax": 1000, "retmode": "json"})))["esearchresult"]["idlist"]
    print(f"{len(ids)} records", flush=True)
    for k in range(0, len(ids), 20):
        batch = ids[k:k + 20]
        txt = get(EU + "efetch.fcgi?" + urllib.parse.urlencode(
            {"db": "nuccore", "id": ",".join(batch), "rettype": "gbwithparts", "retmode": "text"}))
        for rec in txt.split("\n//\n"):
            m = re.search(r"^LOCUS\s+(\S+)", rec, re.M)
            if m: (gdir / f"{m.group(1)}.gb").write_text(rec.strip() + "\n//\n")
        time.sleep(0.4)
        print(f"  {min(k + 20, len(ids))}/{len(ids)}", flush=True)
    label(gdir)


def label(gdir):
    truth, summ, prods = {}, [], Counter()
    for f in sorted(gdir.glob("*.gb")):
        try: ps = S5.annotated_proteins(str(f))
        except Exception: continue
        if len(ps) < 15: continue
        cpt = sum(p["id"].startswith("CPT_") for p in ps)
        t = {c: [] for c in VOCAB}
        for p in ps:
            prod = p.get("product") or ""
            if NOT.search(prod): continue
            for c, rx in VOCAB.items():
                if rx.search(prod): t[c].append(p["id"]); prods[(c, prod.lower())] += 1
        org = re.search(r"^\s+ORGANISM\s+(.+)$", f.read_text(errors="replace")[:5000], re.M)
        summ.append({"genome": f.stem, "organism": org.group(1).strip() if org else "", "n_proteins": len(ps),
                     "cpt_locus_tags": cpt, **{f"n_{c}": len(v) for c, v in t.items()}})
        if any(t.values()): truth[f.stem] = {c: v for c, v in t.items() if v}
    (OUT / "truth.json").write_text(json.dumps(truth, indent=1))
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1))
    print(f"\n{len(summ)} genomes parsed; {sum(s['cpt_locus_tags'] > 0 for s in summ)} with CPT_ locus tags; "
          f"{len(truth)} with at least one curated lysis gene")
    for c in VOCAB:
        print(f"  {c:<10} {sum(len(v.get(c, [])) for v in truth.values()):>4} genes in "
              f"{sum(1 for v in truth.values() if c in v):>4} genomes")
    print("\nproduct names used as truth (curated vocabulary):")
    for (c, p), n in prods.most_common(): print(f"  {n:>4}  {c:<10} {p}")


if __name__ == "__main__":
    main()
