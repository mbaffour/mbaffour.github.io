"""Training and test data for the transmembrane-helix predictor (scripts/55).

From UniProtKB/Swiss-Prot (reviewed), bacteria and viruses, 30-600 aa:
  tm       proteins with HELICAL transmembrane features (proteins with beta-strand TRANSMEM are left out)
  soluble  no transmembrane feature and no signal peptide
  signal   a signal peptide but no transmembrane feature -- so the predictor learns a signal peptide is not a helix
           (it matters here: o-spanins and SAR endolysins start with hydrophobic signals)
  lysis    phage proteins with keyword KW-0578 (host cell lysis by virus) -- HELD OUT: never trained on; the test of
           holin and spanin topology. Removed from the other three sets.
Output: data/raw/tm/{tm,soluble,signal,lysis}.json  [{acc, name, seq, tm: [[start, end], ...] 1-based, signal: end}]
Usage: python3 scripts/55a_fetch_tm_training.py
"""
import json, re, time, urllib.parse, urllib.request
from pathlib import Path
B = Path(__file__).resolve().parent.parent
OUT = B / "data/raw/tm"
BASE = "(reviewed:true) AND (taxonomy_id:2 OR taxonomy_id:10239) AND (length:[30 TO 600])"
SETS = {"lysis": ("(reviewed:true) AND (taxonomy_id:10239) AND (keyword:KW-0578)", 1000),
        "tm": (BASE + " AND (ft_transmem:*) AND NOT (keyword:KW-0578)", 2500),
        "soluble": (BASE + " AND NOT (ft_transmem:*) AND NOT (ft_signal:*) AND NOT (keyword:KW-0578)", 1000),
        "signal": (BASE + " AND (ft_signal:*) AND NOT (ft_transmem:*) AND NOT (keyword:KW-0578)", 600)}


def fetch(query, n):
    url = ("https://rest.uniprot.org/uniprotkb/search?format=tsv&size=500&fields=accession,protein_name,sequence,"
           "ft_transmem,ft_signal&query=" + urllib.parse.quote(query))
    rows = []
    while url and len(rows) < n:
        for i in range(5):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    txt = r.read().decode(); link = r.headers.get("Link", ""); break
            except Exception:
                if i == 4: raise
                time.sleep(2 ** (i + 1))
        lines = txt.splitlines()
        rows += [dict(zip(lines[0].split("\t"), l.split("\t"))) for l in lines[1:]]
        m = re.search(r'<([^>]+)>; rel="next"', link); url = m.group(1) if m else None
        time.sleep(0.3)
    return rows[:n]


def parse(r):
    tm_raw = r.get("Transmembrane", "")
    if "Beta stranded" in tm_raw: return None
    tm = [[int(a), int(b)] for a, b in re.findall(r"TRANSMEM (\d+)\.\.(\d+)", tm_raw)]
    sig = re.search(r"SIGNAL \d+\.\.(\d+)", r.get("Signal peptide", ""))
    return {"acc": r["Entry"], "name": r.get("Protein names", "")[:80], "seq": r["Sequence"], "tm": tm,
            "signal": int(sig.group(1)) if sig else 0}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (q, n) in SETS.items():
        recs = [p for p in (parse(r) for r in fetch(q, n)) if p and not re.search(r"[^ACDEFGHIKLMNPQRSTVWY]", p["seq"])]
        (OUT / f"{name}.json").write_text(json.dumps(recs))
        print(f"{name}: {len(recs)} proteins ({sum(len(p['tm']) for p in recs)} helices)", flush=True)


if __name__ == "__main__":
    main()
