"""Extract the CPT (Young lab) curated spanins from the Kongari et al. 2018 supplementary spreadsheet.

Kongari R, Rajaure M, Cahill J, et al. Phage spanins: diversity, topological dynamics and gene convergence.
BMC Bioinformatics 2018;19:326. doi:10.1186/s12859-018-2342-8 -- Additional file 2 (MOESM2), the published
origin of the CPT spanin database. Table S1a holds two-component spanins (i-spanin primary sequence in column 13,
o-spanin in column 29); Table S1b holds unimolecular u-spanins (column 10). The FASTA-header columns in the sheet
are Excel formulas, so the clean primary-sequence columns are read instead.

Downloads the xlsx if absent (gitignored), writes data/raw/kongari2018/spanins.json + provenance.json.
Usage: python3 scripts/25b_extract_kongari_spanins.py
"""
import hashlib, json, re, time, urllib.request
from pathlib import Path
import openpyxl

B = Path(__file__).resolve().parent.parent
D = B / "data/raw/kongari2018"; D.mkdir(parents=True, exist_ok=True)
URL = ("https://static-content.springer.com/esm/art%3A10.1186%2Fs12859-018-2342-8/MediaObjects/"
       "12859_2018_2342_MOESM2_ESM.xlsx")
AA = set("ACDEFGHIKLMNPQRSTVWY")


def clean(s):
    if not s: return None
    s = re.sub(r"[^A-Za-z]", "", str(s)).upper()
    return s if s and 20 <= len(s) <= 400 and not (set(s) - AA) else None


def main():
    f = D / "MOESM2_ESM.xlsx"
    if not f.exists(): f.write_bytes(urllib.request.urlopen(URL, timeout=600).read())
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    out = []
    for r in wb["Table S1a-Sequences for 2CS"].iter_rows(min_row=2, values_only=True):
        for idx, typ in ((12, "i-spanin"), (28, "o-spanin")):
            seq = clean(r[idx]) if idx < len(r) else None
            if seq: out.append({"seq": seq, "type": typ, "name": f"{r[0]}_{typ}", "accession": str(r[2] or ""), "host": str(r[8] or "")})
    for r in wb["Table S1b- Sequences for 1CS"].iter_rows(min_row=2, values_only=True):
        seq = clean(r[9]) if len(r) > 9 else None
        if seq: out.append({"seq": seq, "type": "u-spanin", "name": f"{r[0]}_u-spanin", "accession": str(r[2] or ""), "host": str(r[5] or "")})
    uniq = {}
    for o in out: uniq.setdefault(o["seq"], o)
    recs = list(uniq.values())
    (D / "spanins.json").write_text(json.dumps(recs, indent=1))
    (D / "provenance.json").write_text(json.dumps({
        "source": "Kongari et al. 2018, BMC Bioinformatics, doi:10.1186/s12859-018-2342-8, Additional file 2 (MOESM2)",
        "url": URL, "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "xlsx_sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
        "extracted": {k: sum(1 for o in out if o["type"] == k) for k in ("i-spanin", "o-spanin", "u-spanin")},
        "distinct_sequences": len(recs)}, indent=1))
    print(f"{len(recs)} distinct curated spanins -> data/raw/kongari2018/spanins.json")


if __name__ == "__main__":
    main()
