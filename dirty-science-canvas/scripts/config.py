"""Project configuration: phages analysed in this canvas."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PHAGES = {
    "phiX174": {"accession": "NC_001422.1", "name": "Escherichia phage phiX174", "host_note": "Escherichia coli (host); membrane predictions refer to a generic membrane context, not a specific host membrane."},
    "M13": {"accession": "NC_003287.2", "name": "Enterobacteria phage M13", "host_note": "Escherichia coli F+ strains (host); membrane predictions refer to a generic membrane context, not a specific host membrane."},
    "MS2": {"accession": "NC_001417.2", "name": "Escherichia phage MS2", "host_note": "Escherichia coli F+ strains (host); membrane predictions refer to a generic membrane context, not a specific host membrane."},
}
def project_dir(key):
    return ROOT / f"{key}_Topology_Lab_Reference"

# Curator-added conventional gene letters. NOT present as /gene qualifiers in RefSeq NC_001422.1; added only as searchable aliases.
# Mapping follows the standard phiX174 gene map (genes A, A*, B, K, C, D, E, J, F, G, H; e.g. Sanger et al. 1977 Nature 265:687;
# reviewed in Fane et al. in "The Bacteriophages" 2006), matched here by RefSeq product name, protein length and genome position.
CURATOR_ALIASES = {
    "phiX174|phiX174p01": "gene A", "phiX174|phiX174p02": "gene A*", "phiX174|phiX174p03": "gene B",
    "phiX174|phiX174p04": "gene K", "phiX174|phiX174p05": "gene C", "phiX174|phiX174p07": "gene D",
    "phiX174|phiX174p08": "gene E", "phiX174|phiX174p09": "gene J", "phiX174|phiX174p06": "gene F",
    "phiX174|phiX174p10": "gene G", "phiX174|phiX174p11": "gene H",
}
