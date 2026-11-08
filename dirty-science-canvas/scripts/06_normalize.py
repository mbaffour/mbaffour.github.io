"""Normalize raw predictor outputs into data.json + topology_summary.csv for each organism, with strict validation.

Compact schema (dsc-topology-atlas/2): each prediction stores its normalized and native per-residue assignments as run-length
segment strings, e.g. "I1-37,M38-60,O61-75" (1-based inclusive; label, start, stop). Expanding the segments gives the full
per-residue label string; validation checks that the expansion has exactly one label per residue of the exact sequence.
When a protein has results from several runs (re-runs), the most recent complete result is used and earlier ones are listed
under "superseded". Usage: python3 scripts/06_normalize.py [--org k1,k2]"""
import csv, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import ORGANISMS, METHOD_RULES, project_dir, selected
from jobrecord import now, load
import predictors

STATE_DEFS = {
    "I": "inside / cytoplasmic side of the membrane (model-defined)",
    "O": "outside / non-cytoplasmic side (model-defined). In DeepTMHMM beta-barrel (BETA) predictions, O is the extracellular side of the outer membrane and P is the periplasm; alpha-helical models do not split periplasm from exterior",
    "M": "alpha-helical membrane span",
    "S": "signal peptide (precursor numbering; predicted, cleavage not demonstrated)",
    "B": "beta-strand membrane span (DeepTMHMM)",
    "P": "periplasm, in DeepTMHMM beta-barrel predictions",
}
MAIN = ["Phobius", "DeepTMHMM", "TOPCONS2"]
COMPONENTS = ["OCTOPUS", "Philius", "PolyPhobius", "SCAMPI", "SPOCTOPUS"]
ALPHABET = {"Phobius": set("nhcCioOM"), "DeepTMHMM": set("IOMSBP"), "TOPCONS2": set("ioMS"), **{c: set("ioMS") for c in COMPONENTS}}

def rle(lbl):
    out, i = [], 0
    while i < len(lbl):
        j = i
        while j + 1 < len(lbl) and lbl[j + 1] == lbl[i]: j += 1
        out.append(f"{lbl[i]}{i + 1}-{j + 1}"); i = j + 1
    return ",".join(out)

def expand(seg):
    s = ""
    for t in seg.split(","):
        m = re.fullmatch(r"([A-Za-z])(\d+)-(\d+)", t); s += m.group(1) * (int(m.group(3)) - int(m.group(2)) + 1)
    return s

def normalize(method, native):
    if method == "Phobius":
        out = []
        for k, ch in enumerate(native):
            if ch in "nhc": out.append("S")
            elif ch == "C":  # cleavage-boundary marker sits on the first mature residue: take the following region's state
                nxt = next((c for c in native[k + 1:] if c != "C"), "o"); out.append({"i": "I", "o": "O", "O": "O", "M": "M"}[nxt])
            else: out.append({"i": "I", "o": "O", "O": "O", "M": "M"}[ch])
        return "".join(out)
    if method == "DeepTMHMM": return native
    return native.translate(str.maketrans({"i": "I", "o": "O"}))

def summarize(norm):
    segs = [(m.group(1), int(m.group(2)), int(m.group(3))) for m in re.finditer(r"([A-Z])(\d+)-(\d+)", rle(norm))]
    spans = [s for s in segs if s[0] in "MB"]; sp = [s for s in segs if s[0] == "S"]
    nside = None
    if spans:
        before = [s for s in segs if s[2] < spans[0][1] and s[0] in "IOP"]
        nside = before[0][0] if before else None
    return {"spans": [[a, b, l] for l, a, b in spans], "sp_range": [sp[0][1], sp[-1][2]] if sp else None, "nside": nside}

# ---------------- parsers (each yields {submitted_id: dict}) ----------------
def parse_phobius(pd, rec):
    out = {}
    api = json.loads((pd / rec["outputs"]["json"]["file"]).read_text())
    short, longs = {}, {}
    o = rec.get("outputs", {})
    if "short" in o:
        for line in (pd / o["short"]["file"]).read_text().splitlines()[1:]:
            f = line.split()
            if len(f) >= 4: short[f[0]] = f[3]
    if "long" in o:
        longs = {m.group(1): m.group(2) for m in re.finditer(r"^ID\s+(\S+)\n(.*?)^//", (pd / o["long"]["file"]).read_text(), re.S | re.M)}
    for p in api["predictions"]:
        lbl, pos = [], 1
        for f in p["features"]:
            if f["start"] != pos: raise ValueError(f"Phobius {p['id']}: gap/overlap at {pos}")
            lbl.append(f["label"] * (f["stop"] - f["start"] + 1)); pos = f["stop"] + 1
        native = "".join(lbl); notes = []
        cs = p.get("cleavage_site")
        if p["signal_peptide"]:
            last = max(i for i, ch in enumerate(native, 1) if ch in "nhc")
            if last != cs: notes.append(f"cleavage_site {cs} != last n/h/c residue {last}")
            if native[cs] != "C": notes.append("C marker not at cleavage_site+1")
        if p["transmembrane_count"] == 0 and not p["signal_peptide"] and short.get(p["id"]) == "i" and "NON CYTOPLASMIC" in longs.get(p["id"], ""):
            notes.append("server output inconsistency: short format 'i' vs long format/JSON NON CYTOPLASMIC for this no-TM protein; no sidedness is interpreted")
        plot = f"raw/Phobius/plots/{p['id']}.svg"
        out[p["id"]] = {"native": native, "cls": f"TM={p['transmembrane_count']}; SP={'Y' if p['signal_peptide'] else '0'}; {p['topology']}",
                        "cleavage_site": cs, "notes": notes, "src": rec["outputs"]["json"]["file"], "plot": plot if (pd / plot).exists() else None}
    return out

def parse_deeptmhmm(pd, rec):
    out = {}
    files = [o["file"] for o in rec.get("outputs", []) if o["file"].endswith("predicted_topologies.3line")]
    for f in files:
        lines = (pd / f).read_text().splitlines()
        for k in range(0, len(lines) - 2, 3):
            m = re.match(r">(\S+)\s*\|\s*(\S+)", lines[k])
            out[m.group(1)] = {"returned_sequence": lines[k + 1].strip(), "native": lines[k + 2].strip(), "cls": m.group(2), "src": f}
    return out

def parse_topcons(pd, rec):
    files = predictors.topcons_members(pd, rec); out = {}
    fin = {}
    for name, b in files.items():
        if name.endswith("finished_seqs.txt"):
            for line in b.decode().splitlines():
                f = line.split("\t")
                if len(f) >= 8: fin[f[0]] = {"run": f[4], "id": f[6], "finished": f[7]}
    dirs = sorted({re.match(r"(.*seq_\d+)/", n).group(1) for n in files if re.search(r"seq_\d+/", n)})
    src = rec.get("result_zip") or rec.get("result_text_archive")
    for d in dirs:
        fa = files.get(f"{d}/seq.fa"); txt = files.get(f"{d}/query.result.txt")
        if fa is None or txt is None: continue
        hdr, *sq = fa.decode().split("\n"); sid = hdr[1:].strip(); seq_ret = "".join(sq).strip(); txt = txt.decode()
        gen = re.search(r"Generated from (\S+) at (.+)", txt); name = re.search(r"Sequence name: (.+)", txt); sres = re.search(r"Sequence:\n(\S+)", txt)
        meth = {}
        for m, label in [("TOPCONS2", "TOPCONS"), *[(c, c) for c in COMPONENTS]]:
            mm = re.search(rf"^{label} predicted topology:\n(\S*)", txt, re.M)
            v = mm.group(1).strip() if mm else ""
            meth[m] = v if v and not v.startswith("***") else None
        rel = []
        rb = files.get(f"{d}/Topcons/reliability.final")
        if rb:
            for line in rb.decode().split("\n"):
                f = line.split()
                if len(f) == 2: rel.append([int(f[0]), float(f[1])])
        dn = d.split("/")[-1]
        out[sid] = {"returned_sequence": seq_ret, "result_sequence": sres.group(1) if sres else None, "methods": meth, "reliability": rel,
                    "meta": {"generated": gen.group(2) if gen else None, "backend": gen.group(1) if gen else None, "cache": fin.get(dn, {}).get("run"),
                             "cache_original_name": name.group(1) if name else None, "src": f"{src}::{d}", "jobid": rec.get("jobid")}}
    return out

PARSERS = {"Phobius": parse_phobius, "DeepTMHMM": parse_deeptmhmm, "TOPCONS2": parse_topcons}

def collect(pd, method):
    """All complete result sets for a method, oldest first. Returns (list of (completed, batch, results), batch status by protein)."""
    recs = []
    for jp in (pd / "raw" / method).glob("*.job.json"):
        r = load(jp)
        if r.get("format"): continue  # legacy web-form cross-check outputs (not a separate prediction source)
        recs.append((r.get("completed_utc") or r.get("submitted_utc") or "", jp.name.replace(".job.json", ""), r))
    recs.sort(key=lambda x: x[0])
    results, status = [], {}
    for t, name, r in recs:
        ids = set(re.findall(r">(\S+)", (pd / r["fasta"]).read_text())) if r.get("fasta") and (pd / r["fasta"]).exists() else set()
        for i in ids:
            if r.get("status") == "complete": status[i] = "complete"
            elif status.get(i) != "complete": status[i] = {"submitted": "pending", "running": "pending"}.get(r.get("status"), "failed")
        if r.get("status") == "complete": results.append((t, name, PARSERS[method](pd, r)))
    return results, status

def main():
    for key in selected(sys.argv):
        o = ORGANISMS[key]; pd = project_dir(key); inv = json.loads((pd / "inventory.json").read_text()); errors = []
        res = {m: collect(pd, m) for m in MAIN}
        planned = {m: set() for m in MAIN}
        for m in MAIN:
            pl = load(pd / "raw" / m / "plan.json") or {"batches": []}
            for b in pl["batches"]: planned[m] |= set(re.findall(r">(\S+)", (pd / b["fasta"]).read_text()))
        recs = []
        for pr in inv["proteins"]:
            sid = pr["protein_id"].replace("|", "__"); seq = pr["sequence"]; L = len(seq)
            r = {k: pr[k] for k in ("protein_id", "gene", "locus_tag", "product", "synonyms", "curator_alias", "note", "replicon", "start", "stop", "strand", "location",
                                    "protein_accession", "sequence", "length", "sequence_sha256", "annotation_flags", "transl_table")}
            r["identical_sequence_to"] = pr.get("identical_sequence_to", []); r["status"], r["pred"], r["superseded"] = {}, {}, {}
            def add(m, native, extra, batch):
                bad = set(native) - ALPHABET[m]
                if len(native) != L: errors.append(f"{sid} {m}: label length {len(native)} != {L}")
                if bad: errors.append(f"{sid} {m}: unexpected states {sorted(bad)}")
                norm = normalize(m, native)
                r["pred"][m] = {"seg": rle(norm), "nseg": rle(native), "batch": batch, **summarize(norm), **extra}; r["status"][m] = "complete"
            for m in MAIN:
                ok, why = pr["eligibility"][m]
                hits = [(t, b, rs[sid]) for t, b, rs in res[m][0] if sid in rs]
                if not ok:
                    r["status"][m] = "too_short" if why.startswith("too short") else ("too_long" if why.startswith("too long") else "unsupported"); r.setdefault("ineligible", {})[m] = why
                    if m == "TOPCONS2":
                        for c in COMPONENTS: r["status"][c] = r["status"][m]
                    continue
                if not hits:
                    st = res[m][1].get(sid) or ("pending" if sid in planned[m] else "not_submitted")
                    if st == "complete": st = "not_returned"
                    r["status"][m] = st
                    if m == "TOPCONS2":
                        for c in COMPONENTS: r["status"][c] = st
                    continue
                t, b, h = hits[-1]
                if len(hits) > 1: r["superseded"][m] = [{"batch": bb, "completed": tt} for tt, bb, _ in hits[:-1]]
                if m == "Phobius": add(m, h["native"], {k: h[k] for k in ("cls", "cleavage_site", "notes", "src", "plot")}, b)
                elif m == "DeepTMHMM":
                    if h["returned_sequence"] != seq: errors.append(f"{sid} DeepTMHMM returned sequence differs")
                    add(m, h["native"], {"cls": h["cls"], "src": h["src"]}, b)
                else:
                    if h["returned_sequence"] != seq or (h["result_sequence"] and h["result_sequence"] != seq): errors.append(f"{sid} TOPCONS2 returned sequence differs")
                    r["topcons_meta"] = h["meta"]
                    for mm in ["TOPCONS2"] + COMPONENTS:
                        if h["methods"][mm]: add(mm, h["methods"][mm], {"src": h["meta"]["src"]}, b)
                        else: r["status"][mm] = "no_output_returned"
                    if o["kind"] == "phage" and h["reliability"] and "TOPCONS2" in r["pred"]: r["pred"]["TOPCONS2"]["rel"] = h["reliability"]
            done = [m for m in MAIN if r["status"].get(m) == "complete"]; P = r["pred"]; dis = []
            if len(done) >= 2:
                if len({len(P[m]["spans"]) for m in done}) > 1: dis.append("span_count")
                if len({bool(P[m]["sp_range"]) for m in done}) > 1: dis.append("signal_peptide")
                ws = [m for m in done if P[m]["spans"]]
                if len({P[m]["nside"] for m in ws}) > 1: dis.append("n_terminal_side")
                if not dis and ws:
                    mx = max(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for m1 in ws for m2 in ws for a, b in zip(P[m1]["spans"], P[m2]["spans"]))
                    if mx > 3: dis.append(f"span_boundaries(max_shift={mx})")
                sps = {tuple(P[m]["sp_range"]) for m in done if P[m]["sp_range"]}
                if len(sps) > 1: dis.append("signal_peptide_boundary")
            r["disagreements"] = dis
            r["any_membrane_span"] = any(P[m]["spans"] for m in done); r["any_signal_peptide"] = any(P[m]["sp_range"] for m in done)
            r["complete_main_methods"] = len(done)
            # validation: expansion of every stored segment string reproduces a full-length label string
            for m, p in P.items():
                for fld in ("seg", "nseg"):
                    if len(expand(p[fld])) != L: errors.append(f"{sid} {m} {fld} expansion length")
            recs.append(r)
        cov = {}
        for m in MAIN + COMPONENTS:
            base = "TOPCONS2" if m in COMPONENTS else m
            sts = [r["status"].get(m) for r in recs]
            cov[m] = {"complete": sts.count("complete"), "eligible": sum(p["eligibility"][base][0] for p in inv["proteins"]), "inventory": len(recs),
                      "status_counts": {s: sts.count(s) for s in sorted(set(map(str, sts)))}}
        jobs = {}
        for m in MAIN:
            jobs[m] = []
            for jp in sorted((pd / "raw" / m).glob("*.job.json")):
                j = load(jp)
                jobs[m].append({k: j.get(k) for k in ("batch", "format", "jobid", "job_id", "status", "submitted_utc", "completed_utc", "n_sequences", "fasta", "fasta_sha256", "app_version", "result_url", "result_zip_url", "rerun") if j.get(k) is not None} | {"record": f"raw/{m}/{jp.name}"})
        prov = json.loads((pd / "inputs" / "provenance.json").read_text())
        data = {"schema": "dsc-topology-atlas/2", "generated_utc": now(), "organism": o["name"], "key": key, "kind": o["kind"], "accessions": o["accessions"],
                "accession": ", ".join(o["accessions"]), "host_note": o["host_note"], "input_provenance": prov,
                "coordinate_convention": "1-based inclusive amino-acid positions in the annotated precursor translation",
                "segment_encoding": "comma-separated LABELstart-stop runs (1-based inclusive) covering every residue exactly once; expand to obtain the per-residue label string",
                "state_definitions": STATE_DEFS, "main_methods": MAIN, "component_methods": COMPONENTS, "eligibility_rules": {m: {k: (sorted(v) if isinstance(v, set) else v) for k, v in r_.items()} for m, r_ in METHOD_RULES.items()},
                "coverage": cov, "jobs": jobs, "n_cds": inv["n_cds_features"], "pseudogenes": json.loads((pd / "pseudogene_inventory.json").read_text()),
                "validation_errors": errors, "proteins": recs}
        (pd / "data.json").write_text(json.dumps(data, separators=(",", ":")))
        with open(pd / "topology_summary.csv", "w", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["protein_id", "gene", "curator_alias", "locus_tag", "product", "length"] + [f"{m}_{x}" for m in MAIN + COMPONENTS for x in ("status", "spans", "signal_peptide", "segments")] + ["disagreements"])
            for r in recs:
                row = [r["protein_id"], r["gene"], r["curator_alias"], r["locus_tag"], r["product"], r["length"]]
                for m in MAIN + COMPONENTS:
                    p = r["pred"].get(m)
                    row += [r["status"].get(m), ";".join(f"{a}-{b}{'' if t == 'M' else '(beta)'}" for a, b, t in p["spans"]) if p else "",
                            (f"{p['sp_range'][0]}-{p['sp_range'][1]}" if p and p["sp_range"] else ("none" if p else "")), p["seg"] if p else ""]
                w.writerow(row + [";".join(r["disagreements"])])
        print(key, "errors:", len(errors), errors[:3], {m: f"{cov[m]['complete']}/{cov[m]['inventory']}" for m in MAIN}, flush=True)

if __name__ == "__main__": main()
