"""Normalize raw predictor outputs into data.json + topology_summary.csv, with strict validation.
Native label strings are preserved; normalized strings use the alphabet documented in STATE_DEFS."""
import csv, glob, html, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir
from jobrecord import sha, now, load

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
ALPHABET = {"Phobius": set("nhcCioOM"), "DeepTMHMM": set("IOMSBP"), "TOPCONS2": set("ioMS"),
            **{c: set("ioMS") for c in COMPONENTS}}

def segments(lbl):
    segs, i = [], 0
    while i < len(lbl):
        j = i
        while j + 1 < len(lbl) and lbl[j + 1] == lbl[i]: j += 1
        segs.append({"label": lbl[i], "start": i + 1, "stop": j + 1}); i = j + 1
    return segs

def normalize(method, native):
    if method == "Phobius":
        out = []
        for k, ch in enumerate(native):
            if ch in "nhc": out.append("S")
            elif ch == "C":  # cleavage-boundary marker = first mature residue; take following region's state
                nxt = next((c for c in native[k + 1:] if c != "C"), "o")
                out.append({"i": "I", "o": "O", "O": "O", "M": "M"}[nxt])
            else: out.append({"i": "I", "o": "O", "O": "O", "M": "M"}[ch])
        return "".join(out)
    if method == "DeepTMHMM": return native
    return native.translate(str.maketrans({"i": "I", "o": "O"}))

def check(method, native, seq, errors, pid):
    if len(native) != len(seq): errors.append(f"{pid} {method}: label length {len(native)} != sequence length {len(seq)}")
    bad = set(native) - ALPHABET[method]
    if bad: errors.append(f"{pid} {method}: unexpected states {sorted(bad)}")

def summarize(norm):
    segs = segments(norm)
    spans = [s for s in segs if s["label"] in "MB"]
    sp = [s for s in segs if s["label"] == "S"]
    first_side = next((s["label"] for s in segs if s["label"] in "IOP"), None)
    nterm = None
    if spans:
        before = [s for s in segs if s["stop"] < spans[0]["start"] and s["label"] in "IOP"]
        nterm = before[0]["label"] if before else None
    return {"n_alpha_spans": sum(s["label"] == "M" for s in spans), "n_beta_spans": sum(s["label"] == "B" for s in spans),
            "signal_peptide": bool(sp), "sp_range": [sp[0]["start"], sp[-1]["stop"]] if sp else None,
            "spans": [[s["start"], s["stop"], s["label"]] for s in spans], "n_side_before_first_span": nterm}

def parse_phobius(pd):
    rd = pd / "raw" / "Phobius"; out = {}
    if not (rd / "batch1_api.json").exists(): return out
    api = json.loads((rd / "batch1_api.json").read_text())
    short = {}
    for line in (rd / "batch1_api_short.txt").read_text().splitlines()[1:]:
        f = line.split()
        if len(f) >= 4: short[f[0]] = {"tm": int(f[1]), "sp": f[2], "prediction": f[3]}
    long_txt = (rd / "batch1_api_long.txt").read_text()
    longs = {m.group(1): m.group(2) for m in re.finditer(r"^ID\s+(\S+)\n(.*?)^//", long_txt, re.S | re.M)}
    for p in api["predictions"]:
        lbl, pos = [], 1
        for f in p["features"]:
            if f["start"] != pos: raise ValueError(f"Phobius {p['id']}: gap/overlap at {pos}")
            lbl.append(f["label"] * (f["stop"] - f["start"] + 1)); pos = f["stop"] + 1
        native = "".join(lbl)
        notes = []
        cs = p.get("cleavage_site")
        if p["signal_peptide"]:
            # verify: last signal-peptide residue == reported cleavage site; 'C' marker sits on cleavage_site+1
            last_c = max(i for i, ch in enumerate(native, 1) if ch in "nhc")
            if last_c != cs: notes.append(f"cleavage_site {cs} != last n/h/c residue {last_c}")
            if native[cs] != "C": notes.append("C marker not at cleavage_site+1")
        sh = short.get(p["id"], {})
        if p["transmembrane_count"] == 0 and sh.get("prediction") in ("i", "o"):
            longside = "NON CYTOPLASMIC" if "NON CYTOPLASMIC" in longs.get(p["id"], "") else ("CYTOPLASMIC" if "CYTOPLASMIC" in longs.get(p["id"], "") else None)
            if sh["prediction"] == "i" and longside == "NON CYTOPLASMIC" and not p["signal_peptide"]:
                notes.append("server output inconsistency: short format reports 'i' but long format/JSON report NON CYTOPLASMIC for this no-TM protein; no sidedness is interpreted")
        out[p["id"]] = {"native": native, "classification": f"TM={p['transmembrane_count']}; SP={'Y' if p['signal_peptide'] else '0'}; topology={p['topology']}",
                        "native_fields": {k: p[k] for k in ("transmembrane_count", "signal_peptide", "cleavage_site", "topology")},
                        "short_format": sh, "notes": notes, "source_output": "raw/Phobius/batch1_api.json",
                        "plot": f"raw/Phobius/plots/{p['id']}.svg" if (rd / "plots" / f"{p['id']}.svg").exists() else None}
    return out

def parse_topcons(pd):
    out = {}
    for d in sorted(glob.glob(str(pd / "raw" / "TOPCONS2" / "extracted" / "*" / "seq_*"))):
        d = Path(d); rel = d.relative_to(pd)
        hdr, *sq = (d / "seq.fa").read_text().split("\n"); sid = hdr[1:].strip(); seq_ret = "".join(sq).strip()
        txt = (d / "query.result.txt").read_text()
        gen = re.search(r"Generated from (\S+) at (.+)", txt)
        name = re.search(r"Sequence name: (.+)", txt)
        seq_in_result = re.search(r"Sequence:\n(\S+)", txt)
        fin = {}
        ff = d.parent / "finished_seqs.txt"
        if ff.exists():
            for line in ff.read_text().splitlines():
                f = line.split("\t")
                if f[0] == d.name: fin = {"length": f[1], "n_tm": f[2], "sp": f[3], "run": f[4], "runtime_s": f[5], "id": f[6], "finished": f[7]}
        meth = {}
        for m, label in [("TOPCONS2", "TOPCONS"), *[(c, c) for c in COMPONENTS]]:
            mm = re.search(rf"^{label} predicted topology:\n(\S*)", txt, re.M)
            val = mm.group(1).strip() if mm else ""
            meth[m] = val if val and not val.startswith("***") else None
            if mm is None or not val: meth[m] = None
        out[sid] = {"returned_sequence": seq_ret, "result_sequence": seq_in_result.group(1) if seq_in_result else None,
                    "generated": gen.group(2) if gen else None, "backend": gen.group(1) if gen else None,
                    "cache_original_name": name.group(1) if name else None, "finished": fin, "dir": str(rel), "methods": meth,
                    "reliability": str(rel / "Topcons" / "reliability.final"), "plot": str(rel / "Topcons" / "total_image.png")}
    return out

def parse_deeptmhmm(pd):
    out = {}
    for f in sorted(glob.glob(str(pd / "raw" / "DeepTMHMM" / "batch*" / "results" / "predicted_topologies.3line"))):
        rel = Path(f).relative_to(pd); lines = Path(f).read_text().splitlines()
        for k in range(0, len(lines) - 2, 3):
            m = re.match(r">(\S+)\s*\|\s*(\S+)", lines[k])
            out[m.group(1)] = {"returned_sequence": lines[k + 1].strip(), "native": lines[k + 2].strip(), "classification": m.group(2), "source_output": str(rel)}
    return out

def main():
    allsum = []
    for key, cfg in PHAGES.items():
        pd = project_dir(key); inv = json.loads((pd / "inventory.json").read_text()); errors = []
        ph, tc, dt = parse_phobius(pd), parse_topcons(pd), parse_deeptmhmm(pd)
        jobs = {m: [load(p) for p in sorted((pd / "raw" / m).glob("*.job.json"))] for m in MAIN}
        recs = []
        for pr in inv["proteins"]:
            sid = pr["protein_id"].replace("|", "__"); seq = pr["sequence"]
            r = {k: pr[k] for k in ("protein_id", "gene", "locus_tag", "product", "synonyms", "curator_alias", "note", "replicon", "start", "stop", "strand", "location",
                                    "protein_accession", "sequence", "length", "sequence_sha256", "annotation_flags", "transl_table")}
            r["submitted_id"] = sid; r["identical_sequence_to"] = pr.get("identical_sequence_to", [])
            r["method_status"], r["predictions"] = {}, {}
            elig = all(c in "ACDEFGHIKLMNPQRSTVWY" for c in seq)
            def add(m, native, extra):
                check(m, native, seq, errors, sid)
                norm = normalize(m, native)
                r["predictions"][m] = {"native_labels": native, "labels": norm, "segments": segments(norm), "native_segments": segments(native), **summarize(norm), **extra}
                r["method_status"][m] = "complete"
            # Phobius
            if sid in ph: add("Phobius", ph[sid]["native"], {k: v for k, v in ph[sid].items() if k != "native"})
            else: r["method_status"]["Phobius"] = "pending" if elig else "unsupported"
            # DeepTMHMM
            if sid in dt:
                if dt[sid]["returned_sequence"] != seq: errors.append(f"{sid} DeepTMHMM returned sequence differs")
                add("DeepTMHMM", dt[sid]["native"], {k: v for k, v in dt[sid].items() if k not in ("native", "returned_sequence")} | {"returned_sequence_matches": dt[sid]["returned_sequence"] == seq})
            else:
                st = [j.get("status") for j in jobs["DeepTMHMM"]]
                r["method_status"]["DeepTMHMM"] = "failed" if st and all(s == "failed" for s in st) else "pending"
            # TOPCONS2 + components
            if sid in tc:
                t = tc[sid]
                if t["returned_sequence"] != seq: errors.append(f"{sid} TOPCONS2 returned seq.fa differs")
                if t["result_sequence"] and t["result_sequence"] != seq: errors.append(f"{sid} TOPCONS2 result-file sequence differs")
                prov = {"generated": t["generated"], "backend": t["backend"], "cache_status": t["finished"].get("run"), "cache_original_name": t["cache_original_name"],
                        "source_output": t["dir"] + "/query.result.txt", "reliability_file": t["reliability"], "plot": t["plot"],
                        "returned_sequence_matches": t["returned_sequence"] == seq and (t["result_sequence"] in (None, seq))}
                rel = []
                rf = pd / t["reliability"]
                if rf.exists():
                    for line in rf.read_text().split("\n"):
                        f = line.split()
                        if len(f) == 2: rel.append([int(f[0]), float(f[1])])
                for m in ["TOPCONS2"] + COMPONENTS:
                    if t["methods"][m]: add(m, t["methods"][m], {"provenance": prov, "classification": None, **({"reliability": rel} if m == "TOPCONS2" else {})})
                    else: r["method_status"][m] = "no_output_returned"
            else:
                st = [j.get("status") for j in jobs["TOPCONS2"]]
                for m in ["TOPCONS2"] + COMPONENTS: r["method_status"][m] = "failed" if st and all(s == "failed" for s in st) else "pending"
            # disagreements among main methods
            done = [m for m in MAIN if r["method_status"].get(m) == "complete"]
            dis = []
            if len(done) >= 2:
                P = {m: r["predictions"][m] for m in done}
                if len({P[m]["n_alpha_spans"] + P[m]["n_beta_spans"] for m in done}) > 1: dis.append("span_count")
                if len({P[m]["signal_peptide"] for m in done}) > 1: dis.append("signal_peptide")
                with_spans = [m for m in done if P[m]["spans"]]
                if len({P[m]["n_side_before_first_span"] for m in with_spans}) > 1: dis.append("n_terminal_side")
                if not dis and with_spans:
                    mx = max(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for m1 in with_spans for m2 in with_spans for a, b in zip(P[m1]["spans"], P[m2]["spans"]))
                    if mx > 3: dis.append(f"span_boundaries(max_shift={mx})")
                sps = [tuple(P[m]["sp_range"]) for m in done if P[m]["sp_range"]]
                if len(set(sps)) > 1: dis.append("signal_peptide_boundary")
            r["disagreements"] = dis
            r["any_membrane_span"] = any(r["predictions"][m]["spans"] for m in done)
            r["any_signal_peptide"] = any(r["predictions"][m]["signal_peptide"] for m in done)
            r["complete_main_methods"] = len(done)
            recs.append(r)
        cov = {}
        for m in MAIN + COMPONENTS:
            sts = [r["method_status"].get(m) for r in recs]
            cov[m] = {"complete": sts.count("complete"), "eligible": sum(all(c in "ACDEFGHIKLMNPQRSTVWY" for c in r["sequence"]) for r in recs), "inventory": len(recs),
                      "status_counts": {s: sts.count(s) for s in set(sts)}}
        prov = json.loads((pd / "inputs" / "provenance.json").read_text())
        data = {"schema": "dsc-topology-atlas/1", "generated_utc": now(), "organism": cfg["name"], "key": key, "accession": cfg["accession"], "host_note": cfg["host_note"],
                "input_provenance": prov, "coordinate_convention": "1-based inclusive amino-acid positions in the annotated precursor translation",
                "state_definitions": STATE_DEFS, "main_methods": MAIN, "component_methods": COMPONENTS, "coverage": cov,
                "jobs": {m: j for m, j in jobs.items()}, "n_cds": inv["n_cds_features"], "pseudogenes": json.loads((pd / "pseudogene_inventory.json").read_text()),
                "validation_errors": errors, "proteins": recs}
        (pd / "data.json").write_text(json.dumps(data, indent=1))
        with open(pd / "topology_summary.csv", "w", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["protein_id", "gene", "curator_alias", "product", "length"] + [f"{m}_{x}" for m in MAIN + COMPONENTS for x in ("status", "spans", "signal_peptide", "topology")] + ["disagreements"])
            for r in recs:
                row = [r["protein_id"], r["gene"], r["curator_alias"], r["product"], r["length"]]
                for m in MAIN + COMPONENTS:
                    p = r["predictions"].get(m)
                    row += [r["method_status"].get(m), ";".join(f"{a}-{b}{'' if t == 'M' else '(beta)'}" for a, b, t in p["spans"]) if p else "",
                            (f"{p['sp_range'][0]}-{p['sp_range'][1]}" if p and p["sp_range"] else ("none" if p else "")),
                            ";".join(f"{s['label']}{s['start']}-{s['stop']}" for s in p["segments"]) if p else ""]
                w.writerow(row + [";".join(r["disagreements"])])
        print(key, "errors:", errors, {m: cov[m]["complete"] for m in MAIN})
if __name__ == "__main__": main()
