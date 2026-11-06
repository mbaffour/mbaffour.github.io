"""Build the protein inventory from GenBank CDS features; reconcile with NCBI CDS FASTA; flag issues."""
import csv, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir, CURATOR_ALIASES
from Bio import SeqIO
from Bio.Seq import Seq

STD = set("ACDEFGHIKLMNPQRSTVWY")
for key, p in PHAGES.items():
    pd = project_dir(key); acc = p["accession"]
    rec = SeqIO.read(pd / "inputs" / f"{acc}.gb", "genbank")
    fasta = {r.id: str(r.seq) for r in SeqIO.parse(pd / "inputs" / f"{acc}.cds_aa.fasta", "fasta")}
    fasta_by_pid = {}
    for rid, s in fasta.items():
        m = re.search(r"_prot_([A-Z]{2}_\d+\.\d+)_", rid)
        if m: fasta_by_pid[m.group(1)] = (rid, s)
    proteins, pseudo, names = [], [], {}
    for i, f in enumerate([f for f in rec.features if f.type == "CDS"], 1):
        q = f.qualifiers
        gene = q.get("gene", [""])[0]; lt = q.get("locus_tag", [""])[0]
        pid = q.get("protein_id", [""])[0]
        flags = []
        if "pseudo" in q or "translation" not in q:
            pseudo.append({"locus_tag": lt, "gene": gene, "product": q.get("product", [""])[0], "location": str(f.location), "reason": "pseudo or no /translation"}); continue
        tr = q["translation"][0]
        tt = int(q.get("transl_table", ["11"])[0]); cs = int(q.get("codon_start", ["1"])[0])
        # Independent derivation from coordinates (documented check, not a substitution)
        nt = f.location.extract(rec.seq)[cs - 1:]
        derived = str(nt.translate(table=tt, to_stop=False))
        if derived.endswith("*"): derived_cmp = derived[:-1]
        else: derived_cmp = derived; flags.append("no_terminal_stop_in_coordinates")
        if derived_cmp and derived_cmp[0] != "M" and tr[0] == "M": derived_cmp = "M" + derived_cmp[1:]  # alternative initiator read as Met
        if derived_cmp != tr: flags.append("translation_differs_from_coordinate_derivation")
        if "*" in tr: flags.append("internal_stop")
        bad = sorted(set(tr) - STD)
        if bad: flags.append("nonstandard_residues:" + "".join(bad))
        if "transl_except" in q: flags.append("transl_except")
        if "<" in str(f.location) or ">" in str(f.location): flags.append("partial")
        if len(f.location.parts) > 1:
            flags.append("joined_location_spans_circular_origin" if rec.annotations.get("topology") == "circular" and int(f.location.parts[-1].start) == 0 else "joined_location")
        if "ribosomal_slippage" in q: flags.append("ribosomal_slippage")
        fid, fseq = fasta_by_pid.get(pid, (None, None))
        if fseq is None: flags.append("missing_in_cds_fasta")
        elif fseq != tr: flags.append("cds_fasta_sequence_mismatch")
        names.setdefault(gene, []).append(lt)
        uid = f"{key}|{lt or pid or i}"
        proteins.append({
            "protein_id": uid, "gene": gene, "locus_tag": lt, "product": q.get("product", [""])[0],
            "synonyms": q.get("gene_synonym", []) + q.get("old_locus_tag", []),
            "curator_alias": CURATOR_ALIASES.get(f"{key}|{lt or pid or i}", ""), "note": q.get("note", [""])[0],
            "replicon": rec.id, "start": (int(f.location.parts[0].start) + 1) if f.location.strand == 1 else (int(f.location.parts[-1].start) + 1),
            "stop": int(f.location.parts[-1].end) if f.location.strand == 1 else int(f.location.parts[0].end),
            "strand": "+" if f.location.strand == 1 else "-", "location": str(f.location),
            "protein_accession": pid, "db_xref": q.get("db_xref", []), "transl_table": tt, "codon_start": cs,
            "sequence": tr, "length": len(tr), "sequence_sha256": hashlib.sha256(tr.encode()).hexdigest(),
            "annotation_flags": flags, "source_record": f"inputs/{acc}.gb", "cds_fasta_id": fid,
        })
    for g, lts in names.items():
        if g and len(lts) > 1:
            for pr in proteins:
                if pr["gene"] == g: pr["annotation_flags"].append("duplicated_gene_name")
    seqs = {}
    for pr in proteins: seqs.setdefault(pr["sequence_sha256"], []).append(pr["protein_id"])
    for pr in proteins:
        others = [x for x in seqs[pr["sequence_sha256"]] if x != pr["protein_id"]]
        if others: pr["identical_sequence_to"] = others
    unmatched_fasta = [rid for rid in fasta if rid not in {p_["cds_fasta_id"] for p_ in proteins}]
    inv = {"organism": p["name"], "key": key, "accession": acc, "record_description": rec.description,
           "n_cds_features": sum(1 for f in rec.features if f.type == "CDS"), "n_proteins": len(proteins),
           "n_pseudogenes": len(pseudo), "cds_fasta_records": len(fasta), "cds_fasta_unmatched": unmatched_fasta,
           "proteins": proteins}
    (pd / "inventory.json").write_text(json.dumps(inv, indent=2))
    (pd / "pseudogene_inventory.json").write_text(json.dumps(pseudo, indent=2))
    with open(pd / "protein_inventory.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["protein_id", "gene", "locus_tag", "product", "synonyms", "replicon", "start", "stop", "strand", "curator_alias", "protein_accession", "length", "sequence_sha256", "annotation_flags", "sequence"])
        for pr in proteins:
            w.writerow([pr["protein_id"], pr["gene"], pr["locus_tag"], pr["product"], ";".join(pr["synonyms"]), pr["replicon"], pr["start"], pr["stop"], pr["strand"], pr["curator_alias"], pr["protein_accession"], pr["length"], pr["sequence_sha256"], ";".join(pr["annotation_flags"]), pr["sequence"]])
    # exact FASTA for submission, IDs = safe short ids
    with open(pd / "inputs" / "proteins_submitted.fasta", "w") as fh:
        for pr in proteins: fh.write(f">{pr['protein_id'].replace('|','__')}\n{pr['sequence']}\n")
    print(key, len(proteins), "proteins;", len(pseudo), "pseudo; unmatched FASTA:", unmatched_fasta)
    for pr in proteins: print("  ", pr["protein_id"], pr["gene"], pr["length"], pr["product"][:40], pr["annotation_flags"])
