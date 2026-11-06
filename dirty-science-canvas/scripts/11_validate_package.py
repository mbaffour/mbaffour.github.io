"""Validate each organism end to end; write verification.json + SHA256SUMS.txt; build zip packages for phages.
Checks report pass / fail / pending (pending = predictions still running; never counted as pass).
Requires logs/browser_check.json from scripts/09_browser_check.js run on the current combined atlas.
Usage: python3 scripts/11_validate_package.py [--org k1,k2]"""
import gzip, hashlib, json, re, sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import ORGANISMS, METHOD_RULES, project_dir, ROOT, selected
from jobrecord import now, load
import predictors
sha = lambda b: hashlib.sha256(b).hexdigest()
def expand(seg): return "".join(m.group(1) * (int(m.group(3)) - int(m.group(2)) + 1) for m in re.finditer(r"([A-Za-z])(\d+)-(\d+)", seg))
def contiguous(seg, L):
    runs = [(int(a), int(b)) for _, a, b in re.findall(r"([A-Za-z])(\d+)-(\d+)", seg)]
    return runs and runs[0][0] == 1 and runs[-1][1] == L and all(runs[i][1] + 1 == runs[i + 1][0] for i in range(len(runs) - 1)) and all(a <= b for a, b in runs)
LIT = {"M13|M13p06": (23, "pVIII precursor (procoat); mature coat begins at residue 24 (AEGDDP...), e.g. Kuhn & Wickner 1985 J Biol Chem 260:15914"),
       "M13|M13p07": (18, "pIII precursor; mature protein begins at residue 19 (AETVES...), e.g. van Wezenbeek et al. 1980 Gene 11:129")}
bc_path = ROOT / "logs" / "browser_check.json"; browser = json.loads(bc_path.read_text()) if bc_path.exists() else None
for key in selected(sys.argv):
    o = ORGANISMS[key]; pd = project_dir(key)
    if not (pd / "data.json").exists(): continue
    res = {"checked_utc": now(), "organism": o["name"], "accessions": o["accessions"], "checks": [], "failures": [], "pending": []}
    def ck(name, cond, detail="", pending=False):
        st = "pending" if pending else ("pass" if cond else "fail")
        res["checks"].append({"check": name, "status": st, "detail": detail})
        if st == "fail": res["failures"].append(name + (": " + detail if detail else ""))
        if st == "pending": res["pending"].append(name + (": " + detail if detail else ""))
    inv = json.loads((pd / "inventory.json").read_text()); data = json.loads((pd / "data.json").read_text()); prov = json.loads((pd / "inputs" / "provenance.json").read_text())
    for f in prov["files"]:
        b = (pd / f["file"]).read_bytes()
        if f["file"].endswith(".gz"): ck(f"input checksums {f['file']}", sha(b) == f["sha256_gz"] and sha(gzip.decompress(b)) == f["sha256"])
        else: ck(f"input checksum {f['file']}", sha(b) == f["sha256"])
    ck("CDS reconciliation", inv["n_cds_features"] == inv["n_proteins"] + inv["n_pseudogenes"], f"{inv['n_cds_features']} CDS = {inv['n_proteins']} translated + {inv['n_pseudogenes']} pseudo/untranslated")
    ck("every NCBI CDS-FASTA record matched", not inv["cds_fasta_unmatched"] and inv["cds_fasta_records"] == inv["n_proteins"])
    blocking = [f"{p['protein_id']}:{f}" for p in inv["proteins"] for f in p["annotation_flags"] if f.startswith(("translation_differs", "cds_fasta_sequence_mismatch", "missing_in_cds_fasta", "internal_stop"))]
    ck("translations agree with CDS FASTA and coordinate re-derivation (incl. transl_except)", not blocking, ";".join(blocking[:10]))
    seqs = {p["protein_id"].replace("|", "__"): p["sequence"] for p in inv["proteins"]}
    nb = nout = 0; bad_fa, bad_out, not_done = [], [], []
    for m in METHOD_RULES:
        for jp in sorted((pd / "raw" / m).glob("*.job.json")):
            j = load(jp); nb += 1
            if j.get("fasta"):
                txt = (pd / j["fasta"]).read_text(); recs = dict(re.findall(r">(\S+)\n(\S+)", txt))
                if sha(txt.encode()) != j.get("fasta_sha256") or any(seqs.get(i) != s for i, s in recs.items()): bad_fa.append(jp.name)
                for i in recs:
                    if i not in seqs: bad_fa.append(f"{jp.name}:{i}")
            outs = []
            o_ = j.get("outputs")
            if isinstance(o_, dict):
                for v in o_.values():
                    for x in (v if isinstance(v, list) else [v]):
                        if isinstance(x, dict) and "file" in x: outs.append((x["file"], x["sha256"]))
            elif isinstance(o_, list): outs += [(x["file"], x["sha256"]) for x in o_]
            if "output" in j: outs.append((j["output"], j["output_sha256"]))
            if j.get("result_zip"): outs.append((j["result_zip"], j["result_zip_sha256"]))
            if j.get("result_text_archive"): outs.append((j["result_text_archive"], j["result_text_archive_sha256"]))
            nout += len(outs); bad_out += [f for f, h in outs if not (pd / f).exists() or sha((pd / f).read_bytes()) != h]
            if j.get("status") != "complete": not_done.append(f"{m}/{jp.name}:{j.get('status')}")
    ck(f"submitted batch FASTAs are exact inventory sequences ({nb} job records)", not bad_fa, ";".join(bad_fa[:10]))
    ck(f"raw output checksums ({nout} files)", not bad_out, ";".join(bad_out[:10]))
    failed = [x for x in not_done if x.endswith(("failed", "rejected", "submit_error"))]
    ck("no failed batches", not failed, ";".join(failed[:10]))
    if [x for x in not_done if x not in failed]: ck("all batches complete", False, ";".join([x for x in not_done if x not in failed][:10]), pending=True)
    # predictions
    invmap = {p["protein_id"]: p for p in inv["proteins"]}
    ck("data.json protein set == inventory (order preserved)", [p["protein_id"] for p in data["proteins"]] == list(invmap))
    errs, nl, sp_checked = [], 0, 0
    for p in data["proteins"]:
        L = len(p["sequence"])
        if p["sequence"] != invmap[p["protein_id"]]["sequence"] or sha(p["sequence"].encode()) != p["sequence_sha256"] or L != p["length"]: errs.append(f"{p['protein_id']} sequence")
        for m, pr in p["pred"].items():
            nl += 1
            for fld in ("seg", "nseg"):
                if len(expand(pr[fld])) != L or not contiguous(pr[fld], L): errs.append(f"{p['protein_id']} {m} {fld}")
            if not set(expand(pr["seg"])) <= set("IOMSBP"): errs.append(f"{p['protein_id']} {m} alphabet")
            if m == "Phobius" and pr.get("cleavage_site"):
                cs = pr["cleavage_site"]; nat = expand(pr["nseg"]); lab = expand(pr["seg"]); sp_checked += 1
                if not (pr["sp_range"] == [1, cs] and nat[cs] == "C" and lab[cs] != "S"): errs.append(f"{p['protein_id']} Phobius SP boundary")
    ck(f"{nl} predictions: segment strings expand to exactly one label per residue, contiguous 1..L, allowed alphabet", not [e for e in errs if "SP boundary" not in e], ";".join(errs[:10]))
    ck(f"Phobius signal-peptide ends = reported cleavage site; 'C' marker not counted as SP ({sp_checked} proteins)", not [e for e in errs if "SP boundary" in e])
    ck("normalizer: returned sequences match and no label/alphabet errors", not data["validation_errors"], ";".join(data["validation_errors"][:10]))
    # beta segments vs DeepTMHMM GFF
    beta = [(p["protein_id"], p["pred"]["DeepTMHMM"]) for p in data["proteins"] if "DeepTMHMM" in p["pred"] and re.search(r"(^|,)[BP]\d", p["pred"]["DeepTMHMM"]["seg"])]
    lab = {"signal": "S", "periplasm": "P", "Beta sheet": "B", "outside": "O", "inside": "I", "TMhelix": "M"}; gffs = {}; bmis = []
    for pid, pr in beta:
        gf = pd / Path(pr["src"]).parent / "TMRs.gff3"
        if gf not in gffs: gffs[gf] = [l.split("\t") for l in gf.read_text().splitlines() if l and not l.startswith("#")]
        sid = pid.replace("|", "__"); gseg = ",".join(f"{lab.get(r[1], '?')}{r[2]}-{r[3]}" for r in gffs[gf] if r[0] == sid)
        if gseg != pr["seg"]: bmis.append(pid)
    ck(f"DeepTMHMM β-type predictions agree with its GFF (P=periplasm, O=outside, B=beta sheet; {len(beta)} proteins)", not bmis, ";".join(bmis[:10]))
    res["beta_state_predictions"] = [pid for pid, _ in beta]
    for m in data["main_methods"]:
        c = data["coverage"][m]; done = c["complete"] == c["eligible"]
        ck(f"{m} coverage of eligible proteins", done, f"{c['complete']}/{c['eligible']} eligible ({c['inventory']} in inventory); {c['status_counts']}", pending=not done and not failed)
    for pid, (end, ref) in LIT.items():
        if pid in invmap:
            p = next(x for x in data["proteins"] if x["protein_id"] == pid)
            res.setdefault("literature_comparison", []).append({"protein_id": pid, "experimental_signal_peptide_end": end, "reference": ref,
                "predicted_signal_peptide_end": {m: (p["pred"][m]["sp_range"] or [None, None])[1] for m in data["main_methods"] if m in p["pred"]}})
    # atlas
    html = (pd / f"{key}_Topology_Atlas.html").read_text()
    emb = json.loads(re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>', html, re.S).group(1).replace("<\\/", "</").replace("<\\!--", "<!--"))
    E = {p["protein_id"]: p for p in emb["proteins"]}
    mism = [p["protein_id"] for p in data["proteins"] if p["protein_id"] not in E or E[p["protein_id"]]["sequence"] != p["sequence"] or {m: v["seg"] for m, v in E[p["protein_id"]]["pred"].items()} != {m: v["seg"] for m, v in p["pred"].items()}]
    ck("organism atlas embeds the current sequences and predictions", not mism and len(E) == len(data["proteins"]), ";".join(mism[:5]))
    others = [c["name"] for k2, c in ORGANISMS.items() if k2 != key]
    ck("organism atlas contains no other organism's name", not [n for n in others if n in html], ";".join(n for n in others if n in html))
    ck("atlas loads no external scripts or styles", not re.search(r'<(script|link)[^>]+(src|href)="https?:', html))
    comb = (ROOT / "Dirty_Science_Canvas_Atlas.html").read_text()
    cemb = json.loads(re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>', comb, re.S).group(1).replace("<\\/", "</").replace("<\\!--", "<!--"))
    CE = {p["protein_id"]: p for p in cemb["proteins"] if p["org"] == key}
    cm = [p["protein_id"] for p in data["proteins"] if p["protein_id"] not in CE or CE[p["protein_id"]]["sequence"] != p["sequence"] or {m: v["seg"] for m, v in CE[p["protein_id"]]["pred"].items()} != {m: v["seg"] for m, v in p["pred"].items()}]
    ck("combined atlas embeds the current sequences and predictions for this organism", not cm and len(CE) == len(data["proteins"]), ";".join(cm[:5]))
    if browser:
        mine = [r for r in browser["problems"] if r["org"] == key]
        ck("browser (file://, offline): no JavaScript errors", not browser["js_errors"], str(browser["js_errors"][:3]))
        ck(f"browser layout audit: no text overlaps, no clipped text, no line crossing a label, no crossing leaders/bonds (all figures of every checked protein; {browser['proteins_checked']} proteins checked atlas-wide, all phage proteins + host sample)",
           not [r for r in mine if r["issues"]], json.dumps([(r["protein_id"], r["issues"]) for r in mine if r["issues"]][:3]))
        ck("browser: every residue's identity, number and band state verified in the full sequence map; bead cartoons account for every residue exactly once",
           not [r for r in mine if not r["seq_ok"] or any(not b["exact"] for b in r["beads"].values())])
        ck("browser: SVG export well-formed; PNG 2x/4x produced; no horizontal overflow at 390 px", browser["exports"]["svg"]["xml_ok"] and all(browser["exports"][x]["png_size"][0] > 0 for x in ("png2", "png4")) and browser["mobile_horizontal_overflow"] is False)
        res["browser_check"] = {k: browser[k] for k in ("checked_utc", "browser", "proteins_checked", "phage_proteins", "host_sample", "ui", "exports")}
    else: ck("browser check present", False, "logs/browser_check.json missing", pending=True)
    res["summary"] = {"checks": len(res["checks"]), "passed": sum(c["status"] == "pass" for c in res["checks"]), "failed": len(res["failures"]), "pending": len(res["pending"])}
    (pd / "verification.json").write_text(json.dumps(res, indent=1))
    files = sorted(f for f in pd.rglob("*") if f.is_file() and f.name != "SHA256SUMS.txt")
    (pd / "SHA256SUMS.txt").write_text("".join(f"{sha(f.read_bytes())}  {f.relative_to(pd)}\n" for f in files))
    pk = ROOT / "packages"; pk.mkdir(exist_ok=True); zp = pk / f"{pd.name}.zip"
    if o["kind"] == "phage":
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(pd.rglob("*")):
                if f.is_file(): z.write(f, f"{pd.name}/{f.relative_to(pd)}")
            for f in sorted((ROOT / "scripts").rglob("*")):
                if f.is_file() and "__pycache__" not in f.parts: z.write(f, f"{pd.name}/scripts/{f.relative_to(ROOT / 'scripts')}")
    elif zp.exists(): zp.unlink()
    print(key, res["summary"], res["failures"][:3], flush=True)
