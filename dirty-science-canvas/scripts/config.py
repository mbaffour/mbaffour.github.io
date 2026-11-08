"""Project configuration: organisms, predictor limits and eligibility rules (all limits from the services' own documentation)."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
REPO_SLUG = "mbaffour/mbaffour.github.io"
RERUN_WORKFLOW = "topology-rerun.yml"

_PHAGE_NOTE = "Membrane predictions refer to a generic membrane context (cytoplasmic vs non-cytoplasmic side); no specific host membrane is assigned, and these are not viral-envelope predictions."
ORGANISMS = {
    # ---- model bacteriophages ----
    "phiX174": {"kind": "phage", "name": "Escherichia phage phiX174", "accessions": ["NC_001422.1"], "host": "Escherichia coli"},
    "M13": {"kind": "phage", "name": "Enterobacteria phage M13", "accessions": ["NC_003287.2"], "host": "Escherichia coli (F+)"},
    "MS2": {"kind": "phage", "name": "Escherichia phage MS2", "accessions": ["NC_001417.2"], "host": "Escherichia coli (F+)"},
    "Qbeta": {"kind": "phage", "name": "Enterobacteria phage Qbeta", "accessions": ["NC_001890.1"], "host": "Escherichia coli (F+)"},
    "lambda": {"kind": "phage", "name": "Enterobacteria phage lambda", "accessions": ["NC_001416.1"], "host": "Escherichia coli"},
    "T4": {"kind": "phage", "name": "Enterobacteria phage T4", "accessions": ["NC_000866.4"], "host": "Escherichia coli"},
    "T7": {"kind": "phage", "name": "Enterobacteria phage T7", "accessions": ["NC_001604.1"], "host": "Escherichia coli"},
    "T5": {"kind": "phage", "name": "Enterobacteria phage T5", "accessions": ["NC_005859.1"], "host": "Escherichia coli"},
    "P1": {"kind": "phage", "name": "Enterobacteria phage P1", "accessions": ["NC_005856.1"], "host": "Escherichia coli"},
    "Mu": {"kind": "phage", "name": "Enterobacteria phage Mu", "accessions": ["NC_000929.1"], "host": "Escherichia coli"},
    "HK97": {"kind": "phage", "name": "Enterobacteria phage HK97", "accessions": ["NC_002167.1"], "host": "Escherichia coli"},
    "P22": {"kind": "phage", "name": "Salmonella phage P22", "accessions": ["NC_002371.2"], "host": "Salmonella enterica serovar Typhimurium"},
    "PRD1": {"kind": "phage", "name": "Enterobacteria phage PRD1", "accessions": ["NC_001421.2"], "host": "Gram-negative bacteria carrying IncP/N/W plasmids (e.g. E. coli, Salmonella)",
             "extra_note": "PRD1 has an internal virion lipid membrane; these predictions do not assign any protein to it."},
    "phi6": {"kind": "phage", "name": "Pseudomonas phage phi6", "accessions": ["NC_003715.1", "NC_003716.1", "NC_003714.1"], "host": "Pseudomonas syringae pv. phaseolicola",
             "extra_note": "phi6 is enveloped and its genome has three segments (L, M, S); these predictions do not assign any protein to the virion envelope."},
    "phi29": {"kind": "phage", "name": "Bacillus phage phi29", "accessions": ["NC_011048.1"], "host": "Bacillus subtilis"},
    "SPP1": {"kind": "phage", "name": "Bacillus phage SPP1", "accessions": ["NC_004166.2"], "host": "Bacillus subtilis"},
    # ---- model hosts ----
    "Ecoli_K12": {"kind": "host", "name": "Escherichia coli K-12 MG1655", "accessions": ["NC_000913.3"], "gram": "negative"},
    "Salmonella_LT2": {"kind": "host", "name": "Salmonella enterica serovar Typhimurium LT2", "accessions": ["NC_003197.2", "NC_003277.2"], "gram": "negative"},
    "Bsubtilis_168": {"kind": "host", "name": "Bacillus subtilis 168", "accessions": ["NC_000964.3"], "gram": "positive"},
}
for k, o in ORGANISMS.items():
    if o["kind"] == "phage":
        o["host_note"] = f"Host: {o['host']}. {_PHAGE_NOTE}" + (" " + o["extra_note"] if o.get("extra_note") else "")
    else:
        o["host_note"] = ("Bacterial proteome. Inside/outside are the models' cytoplasmic/non-cytoplasmic sides; the models do not say which membrane a protein is in. "
                          + ("Gram-negative: alpha-helical predictions are usually discussed for the inner membrane and beta-barrel predictions for the outer membrane, but no membrane is assigned here." if o["gram"] == "negative"
                             else "Gram-positive: a single cytoplasmic membrane; 'outside' is the non-cytoplasmic side."))

def project_dir(key):
    return ROOT / f"{key}_Topology_Lab_Reference"

# Predictor limits and alphabets, from each service's documentation (verified 2026-11-06):
#  Phobius  https://phobius.sbc.su.se/instructions : 20 aa + B,Z,X (treated as unknown); any other character is REMOVED by the server
#           (so such sequences are not submitted); <=100 sequences and <=50,000 residues per request; <=10,000 residues per sequence.
#  DeepTMHMM https://services.healthtech.dtu.dk/services/DeepTMHMM-1.0/ : allowed alphabet is the 20 standard amino acids.
#           BioLib documents no batch limit; we use <=500 sequences per BioLib job, submitted one at a time.
#  TOPCONS2 https://topcons.net/pred/ : each sequence 10-10,000 aa; https://topcons.net/pred/news/ : <=50,000 sequences per query;
#           official WSDL client: input file < 9 MB. We use <=1,000 sequences per job and at most 2 active jobs.
STD20 = set("ACDEFGHIKLMNPQRSTVWY")
METHOD_RULES = {
    "Phobius": {"alphabet": STD20 | set("BZX"), "min_len": 1, "max_len": 10000, "max_seqs": 100, "max_res": 50000},
    "DeepTMHMM": {"alphabet": STD20, "min_len": 1, "max_len": None, "max_seqs": 500, "max_res": None},
    "TOPCONS2": {"alphabet": STD20, "min_len": 10, "max_len": 10000, "max_seqs": 1000, "max_res": None},
}
TOPCONS_MAX_ACTIVE = 2

def eligibility(method, seq):
    r = METHOD_RULES[method]
    bad = sorted(set(seq) - r["alphabet"])
    if bad: return False, f"unsupported residue(s) {''.join(bad)} not in the {method} alphabet (sequence not altered)"
    if len(seq) < r["min_len"]: return False, f"too short ({len(seq)} aa < {r['min_len']} aa minimum)"
    if r["max_len"] and len(seq) > r["max_len"]: return False, f"too long ({len(seq)} aa > {r['max_len']} aa maximum)"
    return True, ""

# Curator-added conventional gene letters (not /gene qualifiers in RefSeq NC_001422.1; searchable aliases only).
CURATOR_ALIASES = {
    "phiX174|phiX174p01": "gene A", "phiX174|phiX174p02": "gene A*", "phiX174|phiX174p03": "gene B",
    "phiX174|phiX174p04": "gene K", "phiX174|phiX174p05": "gene C", "phiX174|phiX174p07": "gene D",
    "phiX174|phiX174p08": "gene E", "phiX174|phiX174p09": "gene J", "phiX174|phiX174p06": "gene F",
    "phiX174|phiX174p10": "gene G", "phiX174|phiX174p11": "gene H",
}
PHAGES = ORGANISMS  # backwards-compatible name used by older scripts

def selected(argv):
    """Organism keys from --org a,b (default: all)."""
    for i, a in enumerate(argv):
        if a == "--org" and i + 1 < len(argv): return [k for k in argv[i + 1].split(",") if k]
    return list(ORGANISMS)
