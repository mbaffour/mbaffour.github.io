"""Protein inventory from RefSeq GenBank CDS features (all replicons): exact /translation used as-is; reconciled with NCBI CDS FASTA;
independently re-derived from coordinates (strand, joins, codon_start, transl_table, transl_except) as a check; flags; per-method eligibility.
Usage: python3 scripts/02_inventory.py [--org k1,k2]"""
import csv, gzip, hashlib, io, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import ORGANISMS, project_dir, selected, CURATOR_ALIASES, METHOD_RULES, eligibility
from Bio import SeqIO
from Bio.Data.IUPACData import protein_letters_3to1_extended
STD = set("ACDEFGHIKLMNPQRSTVWY")
AA3 = {**{k.upper(): v for k, v in protein_letters_3to1_extended.items()}, "SEC": "U", "PYL": "O", "TERM": "*", "OTHER": "X"}

def read_gb(path):
    raw = gzip.open(path, "rt") if str(path).endswith(".gz") else open(path)
    with raw as fh: return list(SeqIO.parse(fh, "genbank"))

def cds_positions(f):
    pos = []
    for part in f.location.parts:
        rng = list(range(int(part.start), int(part.end)))
        pos += rng if part.strand != -1 else rng[::-1]
    return pos

def derive(f, rec, tt, cs):
    nt = f.location.extract(rec.seq)[cs - 1:]
    aa = list(str(nt.translate(table=tt)))
    pos = cds_positions(f)[cs - 1:]
    for te in f.qualifiers.get("transl_except", []):
        m = re.match(r"\(pos:(?:complement\()?(\d+)\.\.(\d+)\)?,aa:(\w+)\)", te)
        if not m: continue
        p0 = int(m.group(1)) - 1 if f.location.strand != -1 else int(m.group(2)) - 1
        if p0 in pos:
            i = pos.index(p0) // 3
            if i < len(aa): aa[i] = AA3.get(m.group(3).upper(), "X")
    return "".join(aa)

for key in selected(sys.argv):
    o = ORGANISMS[key]; pd = project_dir(key)
    proteins, pseudo, seen = [], [], set()
    fasta = {}
    for acc in o["accessions"]:
        for r in SeqIO.parse(pd / "inputs" / f"{acc}.cds_aa.fasta", "fasta"):
            m = re.search(r"_prot_([A-Z]{2}_\d+\.\d+)_", r.id)
            if m: fasta[m.group(1)] = (r.id, str(r.seq))
    n_cds = 0; gbfiles = []
    for acc in o["accessions"]:
        gb = pd / "inputs" / f"{acc}.gb"; gb = gb if gb.exists() else pd / "inputs" / f"{acc}.gb.gz"; gbfiles.append(gb.name)
        for rec in read_gb(gb):
            circ = rec.annotations.get("topology") == "circular"
            for i, f in enumerate([f for f in rec.features if f.type == "CDS"], 1):
                n_cds += 1; q = f.qualifiers
                gene = q.get("gene", [""])[0]; lt = q.get("locus_tag", [""])[0]; pid = q.get("protein_id", [""])[0]
                if "pseudo" in q or "pseudogene" in q or "translation" not in q:
                    pseudo.append({"replicon": rec.id, "locus_tag": lt, "gene": gene, "product": q.get("product", [""])[0], "location": str(f.location),
                                   "reason": "pseudo/pseudogene qualifier" if ("pseudo" in q or "pseudogene" in q) else "no /translation", "note": q.get("note", [""])[0]}); continue
                tr = q["translation"][0]; tt = int(q.get("transl_table", ["11"])[0]); cs = int(q.get("codon_start", ["1"])[0]); flags = []
                d = derive(f, rec, tt, cs)
                dc = d[:-1] if d.endswith("*") else d
                if not d.endswith("*"): flags.append("no_terminal_stop_in_coordinates")
                if dc and tr and dc[0] != tr[0] and tr[0] == "M": dc = "M" + dc[1:]; flags.append("alternative_start_codon_read_as_Met")
                if dc != tr: flags.append("translation_differs_from_coordinate_derivation")
                if "*" in tr: flags.append("internal_stop")
                if "U" in tr: flags.append("selenocysteine")
                if "O" in tr: flags.append("pyrrolysine")
                bad = sorted(set(tr) - STD - {"U", "O"})
                if bad: flags.append("nonstandard_residues:" + "".join(bad))
                if "transl_except" in q: flags.append("transl_except")
                if "<" in str(f.location) or ">" in str(f.location): flags.append("partial")
                if len(f.location.parts) > 1:
                    flags.append("joined_location_spans_circular_origin" if circ and any(int(p.start) == 0 for p in f.location.parts) and any(int(p.end) == len(rec) for p in f.location.parts) else "joined_location")
                if "ribosomal_slippage" in q: flags.append("ribosomal_slippage")
                if "exception" in q: flags.append("exception:" + q["exception"][0].replace(" ", "_"))
                fid, fseq = fasta.get(pid, (None, None))
                if fseq is None: flags.append("missing_in_cds_fasta")
                elif fseq != tr: flags.append("cds_fasta_sequence_mismatch")
                uid = f"{key}|{lt or pid or rec.id + '_' + str(i)}"
                if uid in seen: uid = f"{uid}|{pid}"
                seen.add(uid)
                parts = f.location.parts; strand = f.location.strand
                start = (int(parts[0].start) + 1) if strand != -1 else (int(parts[-1].start) + 1)
                stop = int(parts[-1].end) if strand != -1 else int(parts[0].end)
                proteins.append({
                    "protein_id": uid, "gene": gene, "locus_tag": lt, "product": q.get("product", [""])[0],
                    "synonyms": q.get("gene_synonym", []) + q.get("old_locus_tag", []), "curator_alias": CURATOR_ALIASES.get(uid, ""),
                    "note": q.get("note", [""])[0], "replicon": rec.id, "start": start, "stop": stop, "strand": "-" if strand == -1 else "+",
                    "location": str(f.location), "protein_accession": pid, "db_xref": q.get("db_xref", []), "transl_table": tt, "codon_start": cs,
                    "sequence": tr, "length": len(tr), "sequence_sha256": hashlib.sha256(tr.encode()).hexdigest(), "annotation_flags": flags,
                    "source_record": f"inputs/{gb.name}", "cds_fasta_id": fid,
                    "eligibility": {m: list(eligibility(m, tr)) for m in METHOD_RULES}})
    names = {}
    for p in proteins: names.setdefault(p["gene"], []).append(p["protein_id"])
    for p in proteins:
        if p["gene"] and len(names[p["gene"]]) > 1: p["annotation_flags"].append("duplicated_gene_name")
    seqs = {}
    for p in proteins: seqs.setdefault(p["sequence_sha256"], []).append(p["protein_id"])
    for p in proteins: p["identical_sequence_to"] = [x for x in seqs[p["sequence_sha256"]] if x != p["protein_id"]]
    matched = {p["cds_fasta_id"] for p in proteins}
    inv = {"organism": o["name"], "key": key, "kind": o["kind"], "accessions": o["accessions"], "gb_files": gbfiles, "n_cds_features": n_cds, "n_proteins": len(proteins),
           "n_pseudogenes": len(pseudo), "cds_fasta_records": len(fasta), "cds_fasta_unmatched": [v[0] for v in fasta.values() if v[0] not in matched],
           "proteins": proteins}
    (pd / "inventory.json").write_text(json.dumps(inv, indent=None if o["kind"] == "host" else 2))
    (pd / "pseudogene_inventory.json").write_text(json.dumps(pseudo, indent=2))
    with open(pd / "protein_inventory.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["protein_id", "gene", "locus_tag", "product", "synonyms", "replicon", "start", "stop", "strand", "curator_alias", "protein_accession", "length", "sequence_sha256", "annotation_flags", "ineligible_methods", "sequence"])
        for p in proteins:
            inel = ";".join(f"{m}:{r}" for m, (ok, r) in p["eligibility"].items() if not ok)
            w.writerow([p["protein_id"], p["gene"], p["locus_tag"], p["product"], ";".join(p["synonyms"]), p["replicon"], p["start"], p["stop"], p["strand"], p["curator_alias"], p["protein_accession"], p["length"], p["sequence_sha256"], ";".join(p["annotation_flags"]), inel, p["sequence"]])
    sub = pd / "inputs" / "proteins_submitted.fasta"
    txt = "".join(f">{p['protein_id'].replace('|', '__')}\n{p['sequence']}\n" for p in proteins)
    if not sub.exists() or sub.read_text() != txt: sub.write_text(txt)
    fl = {}
    for p in proteins:
        for f in p["annotation_flags"]: fl[f.split(":")[0]] = fl.get(f.split(":")[0], 0) + 1
    inel = {m: sum(not p["eligibility"][m][0] for p in proteins) for m in METHOD_RULES}
    print(f"{key}: {n_cds} CDS, {len(proteins)} proteins, {len(pseudo)} pseudo, unmatched FASTA {len(inv['cds_fasta_unmatched'])}, ineligible {inel}, flags {fl}")
