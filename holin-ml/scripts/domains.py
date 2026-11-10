"""Lysis Pfam domain evidence, shared by the predictor (scripts/32) and the verifier (scripts/33).

Extracted from scripts/33 so the deployable predictor does not have to import the verification script. This is
the model-INDEPENDENT half of the pipeline, and on an out-of-distribution genome it is the half that works: on
Bacteroides phage DAC15 the real endolysin candidate (gp039, PF01832 Glucosaminidase, E=8.7e-17) scored 0.0059
and ranked 25th of 118 by model probability, and was found only here.

Domain hits are graded, because they are not equal evidence:

  CATALYTIC   an enzymatic domain that actually cleaves peptidoglycan (GH24/25/73/108, SLT, amidases, CHAP,
              NlpC/P60, M15, M23, ...). A hit is strong evidence that the protein is a cell-wall hydrolase.
  BINDING     a cell-wall-BINDING domain only (LysM, PG_binding_1/3, choline-binding, CW_7, PSA CBD). These sit
              on lysins but also on tail, baseplate and surface proteins, so a binding-only hit is weak evidence
              and must not promote a protein to a confirmed call. This is the distinction that keeps a tail
              protein carrying PG_binding out of the top of a domain-ranked list.
  NOT_EXIT    an endolysin-like fold whose owner is not an exit lysin: PF16754 pesticin is a bacteriocin, and
              PF18013 phage tail lysozyme is virion-associated (entry). Reported, never promoting.

A domain hit still does not establish that a protein is an EXIT lysin -- virion-associated lysins share these
folds (T4 gp5, T7 gp16). Genomic context and topology have to do that part, which is why scripts/33 reports
neighbours and Phobius alongside.
"""
import gzip, json, re, time, urllib.request
from pathlib import Path

B = Path(__file__).resolve().parent.parent
HMMDIR = B / "data/raw/pfam_hmm"
IPR_HMM = "https://www.ebi.ac.uk/interpro/api/entry/pfam/{}?annotation=hmm"

CATALYTIC = {
    "PF00959": "Phage_lysozyme (GH24)", "PF01183": "Glyco_hydro_25 lysozyme", "PF01510": "Amidase_2",
    "PF01520": "Amidase_3", "PF05257": "CHAP", "PF00877": "NLPC_P60", "PF01464": "SLT transglycosylase",
    "PF01551": "Peptidase_M23", "PF02557": "VanY (M15)", "PF08291": "Peptidase_M15_3", "PF13539": "Peptidase_M15_4",
    "PF01832": "Glucosaminidase (GH73)", "PF05838": "Glyco_hydro_108", "PF13702": "Lysozyme_like",
    "PF07486": "Hydrolase_2 (cell wall)", "PF31186": "Endolysin", "PF25309": "Endolysin-like domain",
    "PF31067": "Endolysin A", "PF13406": "SLT_2 transglycosylase", "PF06737": "Transglycosylase",
    "PF05382": "Amidase_5 (phage PG hydrolase)", "PF11860": "Muramidase"}
BINDING = {
    "PF01471": "PG_binding_1", "PF01476": "LysM", "PF18341": "PSA endolysin CBD",
    "PF01473": "CW_binding_1 (choline-binding)", "PF08230": "CW_7 cell-wall binding", "PF09374": "PG_binding_3"}
NOT_EXIT = {"PF16754": "Pesticin (bacteriocin, not a phage endolysin)",
            "PF18013": "Phage tail lysozyme (virion-associated, entry not exit)"}
ENDOLYSIN_PFAM = {**CATALYTIC, **BINDING, **NOT_EXIT}

SPANIN_PFAM = {"PF17531": "Spanin outer lipoprotein (T7-like)", "PF26831": "Phage spanin outer lipoprotein",
               "PF03245": "Phage_lysis (Rz, i-spanin)", "PF06085": "Rz1 lipoprotein (o-spanin)",
               "PF23793": "LysC (Rz1-like)", "PF28595": "RzoQ (o-spanin-like)"}
NOT_HOLIN = re.compile(r"choline|cholinesterase|carnitine|betaine|sulfatase|kinase|acyltransferase|"
                       r"cell wall binding", re.I)
STRUCT = re.compile(r"virion|structural|head|capsid|tail|fib(er|re)|baseplate|portal|terminase|tape.?measure|neck",
                    re.I)


def holin_pfam():
    """The Pfam families InterPro names as holins, minus the false name matches (choline, kinase, ...)."""
    d = json.load(open(B / "data/raw/interpro_pfam_holin.json"))
    return {r["metadata"]["accession"]: r["metadata"]["name"]
            for r in d["results"] if not NOT_HOLIN.search(r["metadata"]["name"])}


def fetch_hmms(accs, hmmdir=None):
    """Local HMM files for these accessions, downloading any that are missing from the InterPro API.

    Cached, so this is a one-off cost. For an offline or HPC run, pre-populate the directory and pass hmmdir --
    nothing is fetched for a family whose .hmm is already there.
    """
    d = Path(hmmdir) if hmmdir else HMMDIR
    d.mkdir(parents=True, exist_ok=True)
    prov_p = d / "provenance.json"
    prov = json.loads(prov_p.read_text()) if prov_p.exists() else {}
    fetched = 0
    for acc in accs:
        f = d / f"{acc}.hmm"
        if f.exists(): continue
        url = IPR_HMM.format(acc)
        try:
            raw = urllib.request.urlopen(url, timeout=120).read()
            txt = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
            if not txt.startswith(b"HMMER"): raise ValueError("not an HMM")
            f.write_bytes(txt); fetched += 1
            prov[acc] = {"url": url, "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        except Exception as e:
            prov[acc] = {"url": url, "error": f"{type(e).__name__}: {str(e)[:80]}"}
        time.sleep(0.3)
    if fetched: prov_p.write_text(json.dumps(prov, indent=1))
    return [d / f"{a}.hmm" for a in accs if (d / f"{a}.hmm").exists()]


def lysis_hmms(hmmdir=None):
    """(hmm_files, class_of_accession) for every lysis family: the one call a caller needs."""
    hol = holin_pfam()
    cls_of = {**{a: "endolysin" for a in ENDOLYSIN_PFAM}, **{a: "holin" for a in hol},
              **{a: "spanin" for a in SPANIN_PFAM}}
    return fetch_hmms(list(ENDOLYSIN_PFAM) + list(hol) + list(SPANIN_PFAM), hmmdir), cls_of


def scan(seqs, hmm_files, cls_of, E=1e-3):
    """{id: [domain hit, ...]} by pyhmmer hmmscan. Each hit carries pfam, name, class, from, to, ievalue, grade."""
    import pyhmmer
    alpha = pyhmmer.easel.Alphabet.amino()
    hmms = []
    for f in hmm_files:
        with pyhmmer.plan7.HMMFile(str(f)) as h: hmms.extend(list(h))
    digital = [pyhmmer.easel.TextSequence(name=k.encode(), sequence=v).digitize(alpha) for k, v in seqs.items()]
    out = {k: [] for k in seqs}
    for hits in pyhmmer.hmmer.hmmscan(digital, hmms, E=E, domE=E):
        q = hits.query.name.decode() if isinstance(hits.query.name, bytes) else hits.query.name
        for h in hits:
            if not h.included: continue
            for d in h.domains.included:
                raw = h.accession or h.name
                acc = (raw.decode() if isinstance(raw, bytes) else str(raw)).split(".")[0]
                name = h.name.decode() if isinstance(h.name, bytes) else h.name
                out[q].append({"pfam": acc, "name": name, "class": cls_of.get(acc, "?"),
                               "grade": grade(acc), "from": d.env_from, "to": d.env_to,
                               "ievalue": float(f"{d.i_evalue:.2e}")})
    return out


def grade(acc):
    """How much a hit on this family is worth: catalytic > binding > not_exit."""
    if acc in NOT_EXIT: return "not_exit"
    if acc in BINDING: return "binding"
    if acc in CATALYTIC: return "catalytic"
    return "family"          # a holin/spanin family: membership IS the evidence, there is no catalytic domain


def tier(hits, cls, max_evalue=1e-5):
    """Domain-evidence tier for one protein and one class. Higher is stronger.

    2  a CATALYTIC domain of this class, or membership of a holin/spanin family, at or below max_evalue
    1  a BINDING-only domain of this class -- real but weak: these sit on tail and surface proteins too
    0  nothing, or only a NOT_EXIT fold (pesticin, tail lysozyme), which never promotes
    """
    best = 0
    for h in hits or []:
        if h.get("class") != cls or h.get("ievalue", 1) > max_evalue: continue
        g = h.get("grade")
        if g in ("catalytic", "family"): best = max(best, 2)
        elif g == "binding": best = max(best, 1)
    return best


def summarise(hits, max_evalue=1e-5):
    """Short human-readable evidence string, e.g. 'PF01832:endolysin/catalytic(8.7e-17)'."""
    keep = [h for h in hits or [] if h.get("ievalue", 1) <= max_evalue]
    return ";".join(f"{h['pfam']}:{h['class']}/{h['grade']}({h['ievalue']:.1e})" for h in keep)
