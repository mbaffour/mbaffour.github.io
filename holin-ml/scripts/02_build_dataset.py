"""Assemble the labelled protein set.


Positives = phage holins: TCDB superfamily 1.E members of phage-holin families + Swiss-Prot phage holins.
Evidence tiers: 'tested' (UniProt protein existence 1 = evidence at protein level), 'curated' (Swiss-Prot reviewed, or a
named TCDB phage-holin family), 'putative' (TCDB families named 'Putative').
Holin-like (kept out of training, reported separately): bacterial / toxin / GTA / spore / immunity / releasin families,
CidA/LrgA and antiholins.
Negatives = Swiss-Prot bacteriophage proteins + Swiss-Prot bacterial membrane proteins (30-250 aa) with no lysis-related
annotation. Exact duplicate sequences are merged (all sources kept); conflicting labels are resolved or dropped and reported.

Usage: python3 scripts/02_build_dataset.py   (no arguments; reads data/raw/, writes data/processed/dataset.json)
"""
import csv, gzip, hashlib, io, json, re
from pathlib import Path

B = Path(__file__).resolve().parent.parent
R, O = B / "data" / "raw", B / "data" / "processed"
O.mkdir(parents=True, exist_ok=True)
STD = set("ACDEFGHIKLMNPQRSTVWY")
HOLIN_LIKE_FAMILIES = {
    "1.E.9": "T4 superinfection immunity (not a holin)", "1.E.14": "bacterial CidA/LrgA holin-like",
    "1.E.19": "C. difficile TcdE toxin-release holin-like", "1.E.23": "Bacillus spore morphogenesis/germination holin-like",
    "1.E.42": "holin-like toxin", "1.E.43": "transglycosylase-associated bacterial holin-like",
    "1.E.52": "Flp/Fap pilin putative holin", "1.E.53": "Hok/Gef toxin", "1.E.54": "gene-transfer-agent release holin",
    "1.E.55": "Brachyspira (GTA-associated) holin", "1.E.66": "phage Mu releasin (holin-like, not a holin)",
    "1.E.70": "archaeal putative holin", "1.E.72": "archaeal/bacterial putative holin"}
LYSIS_WORDS = re.compile(r"holin|pinholin|lysis|lytic|spanin|endolysin|lysozyme|lysin\b|murein|peptidoglycan|cell wall hydrolase|"
                         r"amidase|transglycosylase|\brz\b|rz1|releasin|immunity", re.I)
ORDER = {"holin": 0, "holin_like": 1, "negative": 2}


def uniprot(name):
    return list(csv.DictReader(io.StringIO(gzip.open(R / f"uniprot_{name}.tsv.gz", "rt").read()), delimiter="\t"))


def tcdb():
    seqs, h = {}, None
    for line in open(R / "tcdb.fasta"):
        if line.startswith(">"):
            h = line[1:].strip(); seqs[h] = []
        else:
            seqs[h].append(line.strip())
    fam = {}
    for line in open(R / "tcdb_families.tsv"):
        f = line.rstrip("\n").split("\t")
        if len(f) >= 2: fam[f[0]] = f[1].strip()
    return {h: "".join(s) for h, s in seqs.items()}, fam


recs, stats = {}, {"merged_duplicates": 0, "label_resolved": 0, "conflicts_dropped": 0}


def add(seq, label, **meta):
    seq = seq.upper()
    if not seq: return
    r = recs.get(seq)
    if r is None:
        recs[seq] = {"sequence": seq, "label": label, "sources": [meta]}; return
    stats["merged_duplicates"] += 1; r["sources"].append(meta)
    if r["label"] == label: return
    pair = {r["label"], label}
    if "negative" in pair:  # an explicit (holin / holin-like) annotation outranks membership of the generic negative pool
        r["label"] = min(pair, key=ORDER.get); stats["label_resolved"] += 1
        r.setdefault("notes", []).append("annotated holin/holin-like sequence also present in a negative pool; annotation kept")
    elif pair == {"holin", "holin_like"}:
        # dual-start holin genes (lambda S105/S107, phi29 gp14, P21 S21, SPP1): UniProt names the long product
        # "antiholin" while TCDB files the gene in a phage holin family. The ORF is the holin gene: keep it positive.
        fam_src = [s for s in r["sources"] if s.get("tier")]
        if fam_src:
            r["label"] = "holin"; stats["label_resolved"] += 1
            r.setdefault("notes", []).append("dual-start / antiholin annotation on a phage holin-family gene; labelled holin, flagged")
            r["dual_start_or_antiholin"] = True
        else:
            r["conflict"] = True


seqs, fam = tcdb()
for h, s in seqs.items():
    m = re.search(r"\|([^|]+)\|(1\.E\.\d+)\.(\d+\.\d+)\s+(.*)$", h)
    if not m: continue
    acc, f, sub, desc = m.groups()
    pe = re.search(r"PE=(\d)", desc); org = re.search(r"OS=(.*?)(?: OX=| GN=| PE=| SV=|$)", desc)
    meta = {"source": "TCDB", "accession": acc, "tcdb_id": f"{f}.{sub}", "family": f, "family_name": fam.get(f, ""),
            "description": desc[:160], "organism": org.group(1) if org else "", "uniprot_pe": int(pe.group(1)) if pe else None}
    if f in HOLIN_LIKE_FAMILIES:
        add(s, "holin_like", **meta, holin_like_reason=HOLIN_LIKE_FAMILIES[f])
    else:
        tier = "tested" if meta["uniprot_pe"] == 1 else ("putative" if "putative" in fam.get(f, "").lower() else "curated")
        add(s, "holin", **meta, tier=tier)

PE = {"Evidence at protein level": 1, "Evidence at transcript level": 2, "Inferred from homology": 3, "Predicted": 4, "Uncertain": 5}
for r in uniprot("sp_holin"):
    meta = {"source": "Swiss-Prot", "accession": r["Entry"], "name": r["Protein names"][:160], "organism": r["Organism"],
            "family_name": r["Protein families"], "uniprot_pe": PE.get(r["Protein existence"]), "tcdb_xref": r["TCDB"]}
    name, famn = r["Protein names"].lower(), r["Protein families"].lower()
    lineage = [x.split()[0] for x in r["Taxonomic lineage (Ids)"].split(",") if x.strip()]
    is_phage = ("10239" in lineage or "phage" in r["Organism"].lower() or "virus" in r["Organism"].lower()
                or "phage" in name or "prophage" in name           # prophage-derived entries sit in bacterial proteomes
                or re.search(r"holin family", famn))
    if "antiholin" in name or "lrgb" in famn or "cidb" in famn or "antiholin" in famn:
        add(r["Sequence"], "holin_like", **meta, holin_like_reason="antiholin / CidB-LrgB (not a holin)")
    elif "cida/lrga" in famn or not is_phage:
        add(r["Sequence"], "holin_like", **meta, holin_like_reason="bacterial holin-like (CidA/LrgA or non-phage)")
    else:
        add(r["Sequence"], "holin", **meta, tier="tested" if meta["uniprot_pe"] == 1 else "curated")

pools = {"phage": 0, "bacterial_tm": 0, "excluded_lysis_related": 0}
for pool, src in [("sp_phage", "phage"), ("sp_bact_small_tm", "bacterial_tm")]:
    for r in uniprot(pool):
        text = " ".join([r["Protein names"], r["Protein families"], r["Function [CC]"], r["Keywords"]])
        if LYSIS_WORDS.search(text) or r["TCDB"].startswith("1.E"):
            pools["excluded_lysis_related"] += 1; continue
        add(r["Sequence"], "negative", source=f"Swiss-Prot {src}", accession=r["Entry"], name=r["Protein names"][:160],
            organism=r["Organism"], pool=src)
        pools[src] += 1

out, dropped = [], []
for r in recs.values():
    if r.get("conflict"):
        dropped.append({"sequence": r["sequence"], "sources": r["sources"]}); continue
    r["id"] = f"h{len(out):05d}"; r["length"] = len(r["sequence"]); r["sha256"] = hashlib.sha256(r["sequence"].encode()).hexdigest()
    r["nonstandard"] = bool(set(r["sequence"]) - STD)
    if r["label"] == "holin":
        tiers = {s.get("tier") for s in r["sources"]}
        r["tier"] = "tested" if "tested" in tiers else ("curated" if "curated" in tiers else "putative")
        fams = sorted({s["family"] for s in r["sources"] if s.get("family")})
        r["tcdb_family"] = fams[0] if fams else "SwissProt-only"
    if r["label"] == "negative": r["pool"] = sorted({s.get("pool") for s in r["sources"] if s.get("pool")})[0]
    out.append(r)
stats["conflicts_dropped"] = len(dropped)
(O / "dataset.json").write_text(json.dumps(out))
(O / "dropped_conflicts.json").write_text(json.dumps(dropped, indent=1))
with open(O / "dataset.fasta", "w") as fh:
    for r in out: fh.write(f">{r['id']}\n{r['sequence']}\n")
summ = {"total": len(out), "by_label": {l: sum(r["label"] == l for r in out) for l in ORDER},
        "holin_tiers": {t: sum(r.get("tier") == t for r in out) for t in ("tested", "curated", "putative")},
        "holin_families": len({r["tcdb_family"] for r in out if r["label"] == "holin"}),
        "negatives_by_pool": {p: sum(r.get("pool") == p for r in out) for p in ("phage", "bacterial_tm")},
        "pool_rows_before_dedup": pools, **stats, "nonstandard_sequences": sum(r["nonstandard"] for r in out)}
(O / "dataset_summary.json").write_text(json.dumps(summ, indent=2))
print(json.dumps(summ, indent=2))
