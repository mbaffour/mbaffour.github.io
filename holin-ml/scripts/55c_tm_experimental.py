"""Validate the transmembrane predictor against EXPERIMENTALLY determined membrane topology.

Swiss-Prot's transmembrane features for bacterial proteins are mostly predictions themselves (evidence ECO:0000255,
sequence analysis), so agreement with them partly measures agreement with older predictors. Here only proteins whose
every TRANSMEM feature carries experimental evidence (ECO:0000269) are used, from UniProtKB/Swiss-Prot:
  primary    bacteria and viruses (the predictor's domain)
  secondary  all organisms
Proteins in the predictor's training set (data/raw/tm/{tm,soluble,signal}.json) are excluded. Scored: exact helix count,
helix precision and recall (a predicted and an annotated helix match when they overlap by half the shorter), and the
N-terminus side where an experimentally supported first topological domain is given; for our predictor, the hydropathy
heuristic and DeepTMHMM (run on BioLib, scripts/56; the public sequences are sent there).
Output: data/raw/tm/experimental.json, reports/tm_experimental.json
Usage: python3 scripts/55c_tm_experimental.py fetch | deeptmhmm | score
"""
import importlib, json, os, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
OUT = B / "data/raw/tm/experimental.json"
Q = {"bacteria_viruses": "(reviewed:true) AND (ft_transmem_exp:*) AND (taxonomy_id:2 OR taxonomy_id:10239) AND (length:[30 TO 1000])",
     "all_organisms": "(reviewed:true) AND (ft_transmem_exp:*) AND (length:[30 TO 1000])"}


def fetch():
    train = {p["acc"] for k in ("tm", "soluble", "signal") for p in json.load(open(B / f"data/raw/tm/{k}.json"))}
    recs = {}
    for name, q in Q.items():
        url = ("https://rest.uniprot.org/uniprotkb/search?format=tsv&size=500&fields=accession,organism_name,sequence,"
               "ft_transmem,ft_topo_dom&query=" + urllib.parse.quote(q))
        n = 0
        while url and n < 2000:
            with urllib.request.urlopen(url, timeout=120) as r:
                txt = r.read().decode(); link = r.headers.get("Link", "")
            L = txt.splitlines(); hd = L[0].split("\t")
            for l in L[1:]:
                d = dict(zip(hd, l.split("\t"))); tm = d.get("Transmembrane", "")
                feats = re.findall(r'TRANSMEM (\d+)\.\.(\d+);([^T]*?)(?=TRANSMEM|$)', tm)
                if not feats or "Beta stranded" in tm: continue
                if not all("ECO:0000269" in f[2] for f in feats): continue      # every helix experimentally supported
                if d["Entry"] in train or re.search(r"[^ACDEFGHIKLMNPQRSTVWY]", d["Sequence"]): continue
                m = re.search(r'TOPO_DOM 1\.\.\d+; /note="([^"]+)";[^T]*?ECO:0000269', d.get("Topological domain", ""))
                side = None
                if m: side = "in" if "Cytoplasmic" in m.group(1) else "out" if re.search("Periplasmic|Extracellular|Lumenal", m.group(1)) else None
                r_ = recs.setdefault(d["Entry"], {"acc": d["Entry"], "organism": d.get("Organism", ""), "seq": d["Sequence"],
                                                  "tm": [[int(a), int(b)] for a, b, _ in feats], "nterm": side, "sets": []})
                r_["sets"].append(name); n += 1
            m = re.search(r'<([^>]+)>; rel="next"', link); url = m.group(1) if m else None
            time.sleep(0.3)
        print(f"{name}: {sum(name in r['sets'] for r in recs.values())} proteins with all helices experimentally supported "
              f"(training proteins excluded)", flush=True)
    OUT.write_text(json.dumps(list(recs.values())))


def deeptmhmm():
    import biolib
    recs = json.load(open(OUT)); d = B / "reports/external/tm_experimental"; d.mkdir(parents=True, exist_ok=True)
    (d / "in.fasta").write_text("".join(f">{r['acc']}\n{r['seq']}\n" for r in recs))
    cwd = os.getcwd(); os.chdir(d)
    try:
        job = biolib.load("DTU/DeepTMHMM").cli(args="--fasta in.fasta"); job.save_files(".")
    finally:
        os.chdir(cwd)
    print("DeepTMHMM done")


def read_deep():
    out = {}
    f = next((B / "reports/external/tm_experimental").rglob("predicted_topologies.3line"), None)
    if not f: return out
    L = f.read_text().splitlines()
    for i in range(0, len(L) - 2, 3):
        if not L[i].startswith(">"): continue
        acc = L[i][1:].split(" | ")[0].strip(); topo = L[i + 2].strip()
        segs = [(m.start() + 1, m.end()) for m in re.finditer(r"M+", topo)]
        first = topo.lstrip("S")[:1]
        out[acc] = {"helices": segs, "nterm": {"I": "in", "O": "out", "P": "out"}.get(first)}
    return out


def score():
    TM = importlib.import_module("55_tm_predictor"); import features as F
    recs = json.load(open(OUT)); deep = read_deep()
    def evaluate(rs, pred):
        ex = mp = mt = mm = 0; on = ok = 0
        for r in rs:
            p = pred(r)
            if p is None: continue
            h, side = p; ex += len(h) == len(r["tm"]); mp += len(h); mt += len(r["tm"]); mm += TM.seg_match(h, r["tm"])
            if r["nterm"] and side: on += 1; ok += side == r["nterm"]
        n = sum(pred(r) is not None for r in rs)
        return {"proteins": n, "helix_count_exact": round(ex / max(n, 1), 3), "helix_precision": round(mm / max(mp, 1), 3),
                "helix_recall": round(mm / max(mt, 1), 3), "n_terminus_correct": [ok, on]}
    ours_cache = {}
    def ours(r):
        if r["acc"] not in ours_cache:
            p = TM.predict([r["seq"]])[0]; ours_cache[r["acc"]] = (p["helices"], p["n_terminus"])
        return ours_cache[r["acc"]]
    heur = lambda r: ([(i + 1, j + 1) for i, j in F.tm_segments(r["seq"])], None)
    dtm = lambda r: (deep[r["acc"]]["helices"], deep[r["acc"]]["nterm"]) if r["acc"] in deep else None
    res = {}
    for name in Q:
        rs = [r for r in recs if name in r["sets"]]
        res[name] = {"ours": evaluate(rs, ours), "DeepTMHMM": evaluate(rs, dtm), "hydropathy heuristic": evaluate(rs, heur)}
        for k, v in res[name].items(): print(f"{name:17s} {k:21s} {v}", flush=True)
    (B / "reports/tm_experimental.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"fetch": fetch, "deeptmhmm": deeptmhmm, "score": score}[sys.argv[1]]()
