"""Run the lysis proteins through DeepTMHMM and SignalP 6.0 (DTU, via the BioLib cloud) for comparison with our own
transmembrane predictor (scripts/55).

Proteins: every protein scripts/55b classified (confident holin call and the second strong holin, confident endolysin
call, both members of the confident spanin pair) in the nine phage-group scans, deduplicated by sequence, plus the
110 Swiss-Prot phage lysis proteins (data/raw/tm/lysis.json) as a curated benchmark.
NOTE: the sequences (public phage proteins) are sent to BioLib's servers; DeepTMHMM is only available that way.

Steps (resumable; each chunk's results are saved as they arrive):
  build      reports/external/input.fasta + mapping.json (sequence id -> roles in genomes)
  deeptmhmm  chunks of 500 -> reports/external/deeptmhmm/chunk_NNN/{predicted_topologies.3line, TMRs.gff3}
  signalp    chunks of 500 -> reports/external/signalp/chunk_NNN/output/prediction_results.txt (organism other, fast
             mode; the BioLib wrapper requires --output_dir output)
Usage: python3 scripts/56_external_predictors.py build|deeptmhmm|signalp [--chunk 500]
"""
import argparse, hashlib, importlib, json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
B = Path(__file__).resolve().parent.parent
OUT = B / "reports/external"
SETS = ["n4", "lambda", "t7", "p2", "drexler", "t5", "herelle", "t4", "jumbo"]


def sid(seq): return "s" + hashlib.sha256(seq.encode()).hexdigest()[:15]


def build():
    import genecall as G
    from Bio import SeqIO
    roles, seqs = {}, {}
    def add(seq, role):
        if not seq: return
        k = sid(seq); seqs[k] = seq; roles.setdefault(k, []).append(role)
    for p in json.load(open(B / "data/raw/tm/lysis.json")):
        add(p["seq"], {"swissprot": p["acc"], "name": p["name"], "curated_tm": p["tm"]})
    for s in SETS:
        for acc in json.load(open(B / f"data/raw/{s}/selection.json"))["accessions"]:
            L = (B / f"reports/{s}/pred/{acc}.tsv").read_text().splitlines(); hd = L[0].split("\t")
            R = [dict(zip(hd, l.split("\t"))) for l in L[1:] if l.strip()]
            calls = {}
            for i, r in enumerate(R):
                for x in r["lysis_call"].split(","):
                    if x: c, t = x.split(":"); calls[c] = (i, t)
            if not any(t == "confident" for _, t in calls.values()): continue
            rec = next(SeqIO.parse(B / f"data/raw/{s}/fna/{acc}.fna", "fasta"))
            prot = {p["id"]: p["sequence"] for p in G.denovo([(rec.id, str(rec.seq))], nested=True)}
            g = lambda j: prot.get(R[j]["id"], "")
            if calls.get("holin", (0, ""))[1] == "confident":
                i = calls["holin"][0]; add(g(i), {"set": s, "genome": acc, "role": "holin"})
                strong = sorted([j for j, r in enumerate(R) if float(r["P_holin"]) >= 0.9 and j != i], key=lambda j: -float(R[j]["P_holin"]))
                if strong: add(g(strong[0]), {"set": s, "genome": acc, "role": "holin2"})
            if calls.get("endolysin", (0, ""))[1] == "confident":
                add(g(calls["endolysin"][0]), {"set": s, "genome": acc, "role": "endolysin"})
            if calls.get("spanin", (0, ""))[1] == "confident":
                i = calls["spanin"][0]; r = R[i]; s0, e0 = int(r["start"]), int(r["stop"]); cand = []
                for j, q in enumerate(R):
                    if j == i or float(q["P_spanin"]) < 0.5: continue
                    ov = min(e0, int(q["stop"])) - max(s0, int(q["start"]))
                    if ov > 0 or abs(j - i) <= 2: cand.append((ov > 0, float(q["P_spanin"]), j))
                add(g(i), {"set": s, "genome": acc, "role": "spanin"})
                if cand: add(g(max(cand)[2]), {"set": s, "genome": acc, "role": "spanin_partner"})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "input.fasta").write_text("".join(f">{k}\n{v}\n" for k, v in seqs.items()))
    (OUT / "mapping.json").write_text(json.dumps(roles))
    print(f"{len(seqs)} distinct proteins ({sum(len(v) for v in roles.values())} roles)")


def chunks(n):
    ids, seqs, cur = [], [], None
    for ln in (OUT / "input.fasta").read_text().splitlines():
        if ln.startswith(">"): ids.append(ln[1:])
        else: seqs.append(ln)
    return [list(zip(ids[i:i + n], seqs[i:i + n])) for i in range(0, len(ids), n)]


def run(tool, n):
    import biolib
    app = biolib.load({"deeptmhmm": "DTU/DeepTMHMM", "signalp": "DTU/SignalP-6"}[tool])
    for k, ch in enumerate(chunks(n)):
        d = OUT / tool / f"chunk_{k:03d}"
        if (d / "DONE").exists(): continue
        d.mkdir(parents=True, exist_ok=True)
        (d / "in.fasta").write_text("".join(f">{i}\n{s}\n" for i, s in ch))
        cwd = os.getcwd(); os.chdir(d); t = time.time()
        try:
            if tool == "deeptmhmm":
                job = app.cli(args="--fasta in.fasta")
            else:
                job = app.cli(args="--fastafile in.fasta --output_dir output --format txt --organism other --mode fast")
            job.save_files(".")
        finally:
            os.chdir(cwd)
        (d / "DONE").write_text(f"{time.time()-t:.0f}s")
        print(f"{tool} chunk {k}: {len(ch)} proteins in {time.time()-t:.0f}s", flush=True)
    print(f"{tool}: all chunks done", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("step", choices=["build", "deeptmhmm", "signalp"])
    ap.add_argument("--chunk", type=int, default=500); a = ap.parse_args()
    build() if a.step == "build" else run(a.step, a.chunk)
