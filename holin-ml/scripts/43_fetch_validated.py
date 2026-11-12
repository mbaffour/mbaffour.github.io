"""Benchmark built on EXPERIMENTAL evidence, not on genome annotation.

Truth here is a protein whose lysis function was shown experimentally: UniProt Swiss-Prot (reviewed) entries for phage
proteins with evidence at PROTEIN level (PE=1). Each is located in its phage's complete genome by SEQUENCE, never by a
product name. The model is then judged on where that protein ranks among every protein of the genome -- a rank needs no
label on any other protein, so unnamed lysins elsewhere in the genome (e.g. mycobacteriophage "gpNN" genes) cannot be
miscounted.

Classes are assigned by hand from the curated UniProt entries below, with each exclusion and its reason written here:
  excluded, entry/virion lysins (act on the way IN, not at lysis): P03726 T7 gp16, P16009 T4 gp5, P27380 PRD1 P7,
     Q6QGE7 T5 pb2, P07582 phi6 P5, P15132 phi29 gp13, Q8SCY1 phiKZ gp181, Q7Y2C9 phiKMV gp36
  excluded, not a peptidoglycan hydrolase: O64205 D29 LysB (mycolylarabinogalactan esterase)
  excluded, binding subunit only: Q7Y3F3 PlyCB
  excluded, archaeal pseudomurein enzymes (out of scope): Q7LYX0, Q77WJ4
  excluded, not holin/endolysin/spanin: P13304 T4 rI antiholin (separate gene), P03639 phiX174 E and Q8LTE2 Qbeta A2
     (single-gene lysis proteins)
  holin genes that UniProt names by their antiholin isoform (same gene, alternative start): P03705 lambda S,
     P09962 P22 13, P27360 P21 S -- counted as holins

Usage: python3 scripts/43_fetch_validated.py      writes data/raw/validated/{genomes/*.gb, truth.json, mapping.json}
"""
import csv, importlib, json, sys, time, urllib.request, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
S5 = importlib.import_module("05_scan_genome")
B = Path(__file__).resolve().parent.parent
OUT = B / "data/raw/validated"

CLASS = {
  "endolysin": ["B8QIR1", "Q6Y7T6", "P03706", "Q37875", "P00720", "P00806", "Q8SD18", "Q7Y3F1", "Q8SDS7", "P13559",
                "P11187", "D6QY02", "Q9T1X2", "Q8HA43", "P15057", "O64203", "P09963", "P27359", "Q7Y2C0", "Q6QGP7",
                "D1L2U8", "Q3ZFI3", "O56788", "P19385", "O03979", "Q4ZD58", "P33486", "P32762"],
  "holin": ["P06808", "P51773", "O64204", "O03978", "Q38008", "Q7Y2C1", "P03705", "P09962", "P27360"],
  "spanin": ["Q37935", "P00726", "P03803", "P03788", "Q9T1X1", "P0DTL7", "Q6XQ97"],
}


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r: return r.read().decode()
        except Exception:
            if k == tries - 1: raise
            time.sleep(2 ** k)


def uniprot(acc):
    j = json.loads(get(f"https://rest.uniprot.org/uniprotkb/{acc}.json"))
    embl = [x["id"] for x in j.get("uniProtKBCrossReferences", []) if x["database"] == "EMBL"]
    name = j["proteinDescription"].get("recommendedName", {}).get("fullName", {}).get("value", "")
    return {"acc": acc, "name": name, "organism": j["organism"]["scientificName"],
            "sequence": j["sequence"]["value"], "embl": embl}


def best_match(seq, ps):
    """index of the genome protein matching the UniProt sequence: exact, or one contains the other (alternative starts),
    else best identity over the shorter length if >= 0.95."""
    best = (None, 0.0)
    for i, p in enumerate(ps):
        q = p["sequence"]
        if q == seq or (len(q) >= 0.8 * len(seq) and (q in seq or seq in q)): return i, 1.0
    for i, p in enumerate(ps):
        q = p["sequence"]
        if abs(len(q) - len(seq)) > 0.2 * len(seq): continue
        n = min(len(q), len(seq)); m = sum(a == b for a, b in zip(q, seq)) / n
        if m > best[1]: best = (i, m)
    return best if best[1] >= 0.95 else (None, best[1])


def main():
    (OUT / "genomes").mkdir(parents=True, exist_ok=True)
    mapping, truth, gb_cache = [], {}, {}
    for cls, accs in CLASS.items():
        for acc in accs:
            u = uniprot(acc); hit = None
            for nuc in u["embl"]:
                f = OUT / "genomes" / f"{nuc}.gb"
                if nuc not in gb_cache:
                    if not f.exists():
                        txt = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
                            {"db": "nuccore", "id": nuc, "rettype": "gbwithparts", "retmode": "text"}))
                        time.sleep(0.4); f.write_text(txt)
                    try:
                        ps = [p for p in S5.annotated_proteins(str(f)) if p.get("sequence")]
                    except Exception:
                        ps = []
                    gb_cache[nuc] = ps
                ps = gb_cache[nuc]
                if len(ps) < 15: continue                      # a gene or operon record, not a genome
                i, ident = best_match(u["sequence"], ps)
                if i is not None and (hit is None or len(ps) > hit[2]):
                    hit = (nuc, i, len(ps), ident)
            if hit is None:
                # UniProt links only a gene record: find the phage's complete genome through NCBI by organism, and
                # still place the protein by SEQUENCE match. The name finds the genome; it never decides the truth.
                q = f'"{u["organism"].split(" (")[0]}"[Organism] AND (complete genome[Title] OR complete sequence[Title])'
                ids = json.loads(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urllib.parse.urlencode(
                    {"db": "nuccore", "term": q, "retmax": 5, "retmode": "json"})))["esearchresult"]["idlist"]
                time.sleep(0.4)
                for gid in ids:
                    key = f"gi{gid}"; f = OUT / "genomes" / f"{key}.gb"
                    if key not in gb_cache:
                        if not f.exists():
                            f.write_text(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode(
                                {"db": "nuccore", "id": gid, "rettype": "gbwithparts", "retmode": "text"}))); time.sleep(0.4)
                        try: gb_cache[key] = [p for p in S5.annotated_proteins(str(f)) if p.get("sequence")]
                        except Exception: gb_cache[key] = []
                    ps = gb_cache[key]
                    if len(ps) < 15: continue
                    i, ident = best_match(u["sequence"], ps)
                    if i is not None: hit = (key, i, len(ps), ident); break
            row = {"class": cls, "uniprot": acc, "name": u["name"], "organism": u["organism"], "length": len(u["sequence"])}
            if hit:
                nuc, i, n, ident = hit; p = gb_cache[nuc][i]
                row.update({"genome": nuc, "protein_id": p["id"], "genome_product": p.get("product"), "n_proteins": n,
                            "match": round(ident, 3)})
                truth.setdefault(nuc, {}).setdefault(cls, []).append(p["id"])
            else:
                row["genome"] = None
            mapping.append(row)
            print(f"{cls:<10} {acc:<8} {u['organism'][:40]:<40} -> {row.get('genome') or 'NO COMPLETE GENOME'} "
                  f"{row.get('protein_id','')} [{row.get('genome_product') or ''}]", flush=True)
    # one genome per phage: if a phage's proven genes landed on different records (lambda: J02459 lacks a CDS for the
    # embedded Rz1), re-place ALL of them, by sequence, on the single record that holds the most, and drop the others
    seqs = {r["uniprot"]: None for r in mapping}
    by_org = {}
    for r in mapping:
        if r.get("genome"): by_org.setdefault(r["organism"], []).append(r)
    useq = {}
    for r in mapping:
        if r.get("genome") and r["organism"] in by_org and len({x["genome"] for x in by_org[r["organism"]]}) > 1:
            useq[r["uniprot"]] = uniprot(r["uniprot"])["sequence"]
    for org, rows in by_org.items():
        cands = sorted({x["genome"] for x in rows})
        if len(cands) < 2: continue
        def placed(g): return {x["uniprot"]: best_match(useq[x["uniprot"]], gb_cache[g]) for x in rows}
        score = {g: sum(v[0] is not None for v in placed(g).values()) for g in cands}
        keep = max(cands, key=lambda g: (score[g], len(gb_cache[g])))
        pl = placed(keep)
        for x in rows:
            i, ident = pl[x["uniprot"]]
            if i is None: print(f"  {org}: {x['uniprot']} not on {keep}; dropped"); x["genome"] = None; continue
            p = gb_cache[keep][i]
            x.update({"genome": keep, "protein_id": p["id"], "genome_product": p.get("product"),
                      "n_proteins": len(gb_cache[keep]), "match": round(ident, 3)})
        print(f"  {org}: merged {cands} -> {keep} ({score[keep]}/{len(rows)} proven genes)")
    truth = {}
    for r in mapping:
        if r.get("genome"): truth.setdefault(r["genome"], {}).setdefault(r["class"], []).append(r["protein_id"])
    (OUT / "truth.json").write_text(json.dumps(truth, indent=1))
    (OUT / "mapping.json").write_text(json.dumps(mapping, indent=1))
    for cls in CLASS:
        m = [r for r in mapping if r["class"] == cls]
        print(f"{cls}: {sum(1 for r in m if r['genome'])} of {len(m)} mapped into a complete genome by sequence")
    print(f"{len(truth)} genomes")


if __name__ == "__main__":
    main()
