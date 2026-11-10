"""Download PHAGE-ONLY members of the lysis Pfam families, to add depth and ARCHITECTURAL breadth per class.

Same approach as scripts/19_fetch_holin_families.py, but every query is restricted to viral taxonomy
(taxonomy_id:10239) so bacterial autolysins and host homologues are not pulled in. PF00335 (Tetraspanin) is
deliberately excluded: it is a eukaryotic family and a false name match for "spanin".

Family list v2 (2026-11), after Bacteroides phage DAC15 (reports/dac15_report.md) exposed the cost of thin family
coverage: the only lysis domain in that genome was Glucosaminidase PF01832, which was absent from the endolysin
training families, so the endolysin model scored the real candidate 0.006 and a whole-proteome HMM scan had to
find it. Families were enumerated from the InterPro API by name search, not from memory, and each was read before
being assigned a class. What changed:

  endolysin  8 -> 25 families, chosen to cover all five catalytic (EAD) classes rather than to add raw count:
             glycosidase   PF00959 GH24, PF01183 GH25, PF01832 GH73, PF05838 GH108, PF13702, PF11860
             transglycosylase (GH23)  PF01464 SLT, PF06737, PF13406 SLT_2, PF19489 SLT_4
             amidase       PF01510 Amidase_2, PF01520 Amidase_3, PF05382 Amidase_5, PF07313 AmiA-like
             endopeptidase PF05257 CHAP, PF00877 NlpC/P60, PF01551 M23, PF02557 VanY, PF08291 M15_3, PF13539 M15_4
             other/CWH     PF07486 Cell Wall Hydrolase, plus the named families PF31186, PF31067, PF25309, PF18341
  spanin     2 -> 6 families. The old set held only T7-like OUTER subunits, so the i-spanin class was absent
             outright: PF03245 (Rz, inner-membrane i-spanin) and PF06085 (Rz1, outer-membrane o-spanin lipoprotein)
             are the canonical pair and were both missing. PF23793 (LysC) and PF28595 (RzoQ) are Rz1-like.
  holin      33 of the real holin families are already covered by scripts/19-21 across all four architectural
             classes, so only the two newer families it predates are added: PF37872, PF51202.

CONFUSABLES are downloaded but labelled role="confusable", never as positives. These are the proteins that look
like a lysis gene to a classifier and are not one:
  PF18013 phage TAIL lysozyme and PF16754 pesticin carry an endolysin-like fold but act at ENTRY or as a
          bacteriocin, not at exit -- the T4 gp5 / T7 gp16 problem, and the likely identity of DAC15 gp080, an
          832-aa protein in the structural module that the endolysin model called at 0.839.
  PF04517 microvirus E and PF11125 MS2 L cause lysis as single-gene membrane proteins that inhibit cell-wall
          synthesis; they are not holins, and they are the sharpest available negatives for the holin model.
  PF02402 colicin-release lysis protein and PF26810 phage disruptin lyse by other routes again.
Whether they earn their place as negatives is tested, not assumed: scripts/28 trains with and without them.

Binding-only domains (PF01471 PG_binding_1, PF01476 LysM, PF08239 SH3_3, PF09374, PF01473) are deliberately NOT
label sources. A phage protein carrying LysM need not be a lysin, so they would inject noise; they stay in the
scripts/33 verification domain list, where a hit is reported as evidence rather than used as a label.

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
    # ---- endolysin: glycosidases ----
    ("PF00959", "Phage lysozyme (GH24)", "endolysin", "positive"),
    ("PF01183", "Glycosyl hydrolases family 25", "endolysin", "positive"),
    ("PF01832", "Mannosyl-glycoprotein endo-beta-N-acetylglucosaminidase (GH73)", "endolysin", "positive"),
    ("PF05838", "Glycosyl hydrolase 108", "endolysin", "positive"),
    ("PF13702", "Lysozyme-like", "endolysin", "positive"),
    ("PF11860", "N-acetylmuramidase", "endolysin", "positive"),
    # ---- endolysin: lytic transglycosylases (GH23) ----
    ("PF01464", "Transglycosylase SLT domain", "endolysin", "positive"),
    ("PF06737", "Transglycosylase-like domain", "endolysin", "positive"),
    ("PF13406", "Transglycosylase SLT domain 2", "endolysin", "positive"),
    ("PF19489", "Transglycosylase SLT domain 4", "endolysin", "positive"),
    # ---- endolysin: amidases ----
    ("PF01510", "Amidase_2", "endolysin", "positive"),
    ("PF01520", "Amidase_3", "endolysin", "positive"),
    ("PF05382", "Bacteriophage peptidoglycan hydrolase (Amidase_5)", "endolysin", "positive"),
    ("PF07313", "N-acetylmuramoyl-L-alanine amidase-like (AmiA-like)", "endolysin", "positive"),
    # ---- endolysin: endopeptidases ----
    ("PF05257", "CHAP domain", "endolysin", "positive"),
    ("PF00877", "NlpC/P60 family", "endolysin", "positive"),
    ("PF01551", "Peptidase family M23", "endolysin", "positive"),
    ("PF02557", "D-alanyl-D-alanine carboxypeptidase (VanY)", "endolysin", "positive"),
    ("PF08291", "Peptidase M15", "endolysin", "positive"),
    ("PF13539", "D-alanyl-D-alanine carboxypeptidase (M15_4)", "endolysin", "positive"),
    # ---- endolysin: other cell-wall hydrolase / named endolysin families ----
    ("PF07486", "Cell Wall Hydrolase", "endolysin", "positive"),
    ("PF18341", "PSA endolysin CBD", "endolysin", "positive"),
    ("PF31186", "Endolysin", "endolysin", "positive"),
    ("PF25309", "Endolysin-like domain", "endolysin", "positive"),
    ("PF31067", "Endolysin A", "endolysin", "positive"),
    # ---- spanin: i-spanin (inner membrane), o-spanin (outer-membrane lipoprotein), u-spanin ----
    ("PF03245", "Bacteriophage Rz lysis protein (i-spanin)", "spanin", "positive"),
    ("PF06085", "Lipoprotein Rz1 precursor (o-spanin)", "spanin", "positive"),
    ("PF23793", "Rz1-like lysis system protein LysC", "spanin", "positive"),
    ("PF28595", "Putative lipoprotein RzoQ", "spanin", "positive"),
    ("PF17531", "Spanin, outer lipoprotein, T7-like", "spanin", "positive"),
    ("PF26831", "Phage spanin outer lipoprotein subunit", "spanin", "positive"),
    # ---- holin: the two families scripts/19 predates (33 others already curated by scripts/19-21) ----
    ("PF37872", "Actinomycetota putative holin", "holin", "positive"),
    ("PF51202", "NGO1622-like phage-associated putative holin", "holin", "positive"),
    # ---- confusables: lysis-adjacent but NOT holin/endolysin/spanin (negatives, tested in scripts/28) ----
    ("PF18013", "Phage TAIL lysozyme (virion-associated, entry not exit)", "confusable", "confusable"),
    ("PF16754", "Pesticin, bacterial toxin homologue of phage lysozyme", "confusable", "confusable"),
    ("PF04517", "Microvirus lysis protein E (MraY inhibitor, not a holin)", "confusable", "confusable"),
    ("PF11125", "Bacteriophage MS2 lysis protein L (not a holin)", "confusable", "confusable"),
    ("PF02402", "Colicin-release lysis protein", "confusable", "confusable"),
    ("PF26810", "Phage disruptin, cationic AMP for OM disruption", "confusable", "confusable"),
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
    for acc, name, cls, role in FAMILIES:
        f = RAW / f"{acc}.tsv.gz"
        if f.exists() and acc in prov:
            print(f"  {acc} cached ({prov[acc].get('rows', '?')} rows)", flush=True); continue
        q = f"xref:pfam-{acc} AND taxonomy_id:10239"
        url = (f"https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=tsv"
               f"&fields={FIELDS}&query={urllib.parse.quote(q)}")
        rec = {"pfam_id": acc, "pfam_name": name, "class": cls, "role": role, "query": q, "url": url}
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
    print(f"\n{'family':<9}| {'class':<11}| {'role':<11}| rows  | name")
    for acc, name, cls, role in FAMILIES:
        print(f"{acc:<9}| {cls:<11}| {role:<11}| {prov.get(acc, {}).get('rows', 0):<6}| {name[:50]}")
    tot = sum(v.get("rows", 0) for v in prov.values())
    print(json.dumps({"families": len(prov), "member_rows_total": tot,
                      "by_class": {c: sum(v.get("rows", 0) for v in prov.values() if v.get("class") == c)
                                   for c in ("endolysin", "spanin", "holin", "confusable")},
                      "failed_or_empty": [k for k, v in prov.items() if v.get("rows", 0) == 0],
                      "megabytes": round(sum(v.get("bytes", 0) for v in prov.values()) / 1e6, 2)}, indent=1))


if __name__ == "__main__":
    main()
