"""A larger curated benchmark: Swiss-Prot REVIEWED phage lysis proteins (any evidence level), placed in their genomes.

The experimental benchmark (scripts/43) keeps only protein-level evidence (PE=1): 22 endolysins, 8 holins, 7 spanins.
Swiss-Prot entries are expert-curated even when not directly proven, so their standardised names are a much stronger
truth than automated GenBank annotation (they are still names, and are reported as "curated", not "proven").

Selection: reviewed viral proteins with keyword KW-0578 (host cell lysis by virus), KW-0081 (bacteriolytic enzyme) or
KW-1188 (viral release from host cell); class from the curated name:
  holin       "holin" / "pinholin" (antiholins excluded, except the three holin genes UniProt names by their antiholin
              isoform: P03705 lambda S, P09962 P22 13, P27360 P21 S -- as in scripts/43)
  endolysin   endolysin, lysozyme, lysin, amidase, endopeptidase, muramidase, glucosaminidase, transglycosylase,
              peptidoglycan hydrolase -- EXCEPT virion / entry enzymes (tail, baseplate, internal, virion, spike,
              ejection, pilot, entry) and the scripts/43 exclusions
  spanin      spanin, Rz, Rz1, LysC, "outer lipoprotein subunit"
Placement in a complete genome by SEQUENCE, with the scripts/43 machinery.
Output: data/raw/reviewed/{genomes/*.gb, truth.json, mapping.json}
Usage: python3 scripts/43b_fetch_reviewed.py
"""
import importlib, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
M43 = importlib.import_module("43_fetch_validated")
B = Path(__file__).resolve().parent.parent
EXCLUDE = {"P03726", "P16009", "P27380", "Q6QGE7", "P07582", "P15132", "Q8SCY1", "Q7Y2C9", "O64205", "Q7Y3F3",
           "Q7LYX0", "Q77WJ4", "P13304", "P03639", "Q8LTE2"}
ANTIHOLIN_ISOFORM_HOLINS = {"P03705", "P09962", "P27360"}


def classify(name, acc):
    nl = name.lower()
    if acc in EXCLUDE: return None
    if acc in ANTIHOLIN_ISOFORM_HOLINS: return "holin"
    if re.search(r"tail|baseplate|internal|virion|spike|ejection|pilot|entry", nl): return None
    if nl.startswith("antiholin") or "antiholin" in nl.split("(")[0]: return None
    if re.search(r"\bholin|pinholin", nl): return "holin"
    if re.search(r"spanin|\brz1?\b|lysc|outer lipoprotein subunit", nl): return "spanin"
    if re.search(r"endolysin|lysozyme|lysin|amidase|endopeptidase|muramidase|glucosaminidase|transglycosylase|"
                 r"peptidoglycan hydrolase", nl): return "endolysin"
    return None


def main():
    q = "(reviewed:true) AND (taxonomy_id:10239) AND (keyword:KW-0578 OR keyword:KW-0081 OR keyword:KW-1188)"
    url = ("https://rest.uniprot.org/uniprotkb/search?format=tsv&size=500&fields=accession,protein_name&query="
           + urllib.parse.quote(q))
    cls = {"endolysin": [], "holin": [], "spanin": []}
    while url:
        with urllib.request.urlopen(url, timeout=120) as r:
            L = r.read().decode().splitlines(); link = r.headers.get("Link", "")
        for l in L[1:]:
            acc, name = l.split("\t")[:2]; c = classify(name, acc)
            if c: cls[c].append(acc)
        m = re.search(r'<([^>]+)>; rel="next"', link); url = m.group(1) if m else None
        time.sleep(0.3)
    print({k: len(v) for k, v in cls.items()}, flush=True)
    M43.CLASS = cls
    M43.OUT = B / "data/raw/reviewed"
    M43.main()


if __name__ == "__main__":
    main()
