"""Gene calling from bare DNA, with the lysis-specific gap of standard gene finders filled.

Pyrodigal (like Prodigal, GeneMark and Glimmer) does not call a gene that lies INSIDE another gene in a different
reading frame. Embedded o-spanins are exactly that: lambda Rz1 lies inside Rz in the +1 frame, T7 gp18.7 inside gp18.5,
and so on. On the experimental benchmark this made three of seven proven spanins invisible from bare DNA before any
model ran (reports/validated_benchmark.md).

nested_lipoprotein_orfs() adds those back, narrowly, by the o-spanin's own defining signal rather than by length:
  host       any called gene of 60-300 aa (the i-spanin size range), on either strand. An earlier version also
             required a hydropathy-detected N-terminal TM segment; the heuristic misses real i-spanins (T7 gp18.5),
             and dropping it recovered more o-spanins at a similar cost in extra ORFs (below)
  ORF        an alternative-frame open reading frame on the same strand whose start codon (ATG/GTG/TTG) lies inside
             the host, 40-200 codons, not already called
  signal     a lipoprotein signal: lipobox [LVI][ASTVI][GAS]C with the cysteine at residue 15-35 and a hydrophobic
             h-region (mean Kyte-Doolittle >= 1.5 over the 11 residues ending 3 before the cysteine). Of the possible
             starts, the most upstream one that puts the lipobox in that window is used.
Measured on the 162 curated spanins of the 90 CPT genomes that have one: from bare DNA Pyrodigal misses 48 (30%);
this finder recovers 24 of them while adding 45 ORFs in total (0.5 per genome), so about half of what it adds is a
curated spanin. On the experimental set it recovers all three missed o-spanins (lambda Rz1, T7 gp18.7, Mu) and adds
nothing else. Settings were chosen on those gene-finding counts only, never on model scores; the broader lipobox
consensus and a later cysteine window (to residue 55) found 1-6 more spanins for 8-19 more ORFs.
The extra ORFs are scored like any other protein; nothing is promoted. They are marked caller="nested-lipoprotein"
so a user can see where they came from.

denovo() is the one entry point: Pyrodigal (meta mode) genes plus, optionally, the nested ORFs.
"""
import re
from Bio.Seq import Seq

LIPO = re.compile(r"[LVI][ASTVI][GAS]C")
KD = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5, "G": -0.4, "H": -3.2, "I": 4.5,
      "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2}
STARTS, STOPS = {"ATG", "GTG", "TTG"}, {"TAA", "TAG", "TGA"}


def lipo_signal(prot):
    """True if the protein starts with a lipoprotein signal peptide (lipobox Cys at residue 15-35, hydrophobic h-region)"""
    for m in LIPO.finditer(prot[:36]):
        c = m.end() - 1                                   # 0-based index of the cysteine
        if not 14 <= c <= 34: continue
        h = prot[max(0, c - 14):c - 3]
        if h and sum(KD.get(a, 0) for a in h) / len(h) >= 1.5: return True
    return False


def _host_like(prot):
    return 60 <= len(prot) <= 300


def nested_lipoprotein_orfs(dna, genes, rec_id="seq", min_aa=40, max_aa=200):
    """genes: Pyrodigal-style dicts with 1-based inclusive start/stop, strand '+'/'-' and sequence.
    Returns new protein dicts in the same shape for nested lipoprotein ORFs (see module docstring)."""
    dna = dna.upper(); L = len(dna)
    rc = str(Seq(dna).reverse_complement())
    called = {(g["strand"], g["stop"] if g["strand"] == "+" else g["start"]) for g in genes}   # 3' ends already called
    out, seen = [], set()
    for g in genes:
        if not _host_like(g["sequence"]): continue
        S = dna if g["strand"] == "+" else rc
        hs, he = (g["start"] - 1, g["stop"]) if g["strand"] == "+" else (L - g["stop"], L - g["start"] + 1)
        for f in (1, 2):                                  # the two other frames
            p = hs + f
            best = {}                                     # stop position -> most upstream valid start
            while p + 3 <= he:
                if S[p:p + 3] in STARTS:
                    q = p
                    while q + 3 <= L and S[q:q + 3] not in STOPS: q += 3
                    if q + 3 <= L:
                        n = (q - p) // 3
                        if min_aa <= n <= max_aa and q not in best:
                            prot = str(Seq(S[p:q]).translate())
                            prot = "M" + prot[1:]          # alternative start codons are read as Met
                            if lipo_signal(prot): best[q] = (p, prot)
                p += 3
            for q, (p, prot) in best.items():
                if g["strand"] == "+": start, stop = p + 1, q + 3
                else: start, stop = L - (q + 3) + 1, L - p
                key = (g["strand"], stop if g["strand"] == "+" else start)
                if key in called or key in seen: continue
                seen.add(key)
                out.append({"id": f"{rec_id}_nested{len(out) + 1:03d}", "product": "", "gene": "", "start": start,
                            "stop": stop, "strand": g["strand"], "sequence": prot, "caller": "nested-lipoprotein",
                            "host": g["id"]})
    return out


def denovo(records, nested=False):
    """records: iterable of (id, DNA string). Pyrodigal meta-mode genes, plus nested lipoprotein ORFs if asked,
    sorted by position within each record."""
    import pyrodigal
    finder = pyrodigal.GeneFinder(meta=True)
    out = []
    for rid, dna in records:
        gs = []
        for i, g in enumerate(finder.find_genes(dna.encode() if isinstance(dna, str) else dna), 1):
            gs.append({"id": f"{rid}_orf{i:04d}", "product": "", "gene": "", "start": g.begin, "stop": g.end,
                       "strand": "+" if g.strand == 1 else "-", "sequence": g.translate().rstrip("*"),
                       "caller": f"Pyrodigal {pyrodigal.__version__} (meta)"})
        if nested:
            gs += nested_lipoprotein_orfs(dna if isinstance(dna, str) else dna.decode(), gs, rid)
        out += sorted(gs, key=lambda x: x["start"])
    return out
