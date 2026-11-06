"""Validate inventory, inputs, raw outputs, normalized predictions and atlas; write verification.json, SHA256SUMS.txt and a zip package.
Requires logs/browser_check.json from scripts/09_browser_check.js (run immediately before, on the same atlas build)."""
import hashlib, json, re, sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir, ROOT
from jobrecord import now
sha = lambda b: hashlib.sha256(b).hexdigest()
browser = json.loads((ROOT / "logs" / "browser_check.json").read_text())
STD = set("ACDEFGHIKLMNPQRSTVWY")
LIT = {  # literature comparison (experimental mature N-termini); informational only, not used by any prediction
    "M13|M13p06": {"signal_peptide_end": 23, "ref": "pVIII precursor (procoat) 73 aa; mature coat begins at residue 24 (AEGDDP...) — e.g. Kuhn & Wickner 1985 J Biol Chem 260:15914"},
    "M13|M13p07": {"signal_peptide_end": 18, "ref": "pIII precursor; mature protein begins at residue 19 (AETVES...) — e.g. van Wezenbeek et al. 1980 Gene 11:129"},
}
for key, cfg in PHAGES.items():
    pd = project_dir(key); res = {"checked_utc": now(), "organism": cfg["name"], "accession": cfg["accession"], "checks": [], "failures": []}
    def ok(name, cond, detail=""):
        res["checks"].append({"check": name, "pass": bool(cond), "detail": detail})
        if not cond: res["failures"].append(name + (": " + detail if detail else ""))
    inv = json.loads((pd / "inventory.json").read_text()); data = json.loads((pd / "data.json").read_text())
    prov = json.loads((pd / "inputs" / "provenance.json").read_text())
    for f in prov["files"]: ok(f"input checksum {f['file']}", sha((pd / f["file"]).read_bytes()) == f["sha256"])
    ok("CDS reconciliation", inv["n_cds_features"] == inv["n_proteins"] + inv["n_pseudogenes"], f"{inv['n_cds_features']} CDS = {inv['n_proteins']} proteins + {inv['n_pseudogenes']} pseudo/untranslated")
    ok("all CDS FASTA records matched", not inv["cds_fasta_unmatched"] and inv["cds_fasta_records"] == inv["n_proteins"])
    blocking = [f for p in inv["proteins"] for f in p["annotation_flags"] if f.startswith(("translation_differs", "cds_fasta_sequence_mismatch", "missing_in_cds_fasta", "internal_stop"))]
    ok("translations agree with CDS FASTA and coordinate derivation", not blocking, ";".join(blocking))
    nonstd = [p["protein_id"] for p in inv["proteins"] if set(p["sequence"]) - STD]
    res["nonstandard_residue_proteins"] = nonstd
    sub = (pd / "inputs" / "proteins_submitted.fasta").read_text(); subsha = sha(sub.encode())
    recs = dict(re.findall(r">(\S+)\n(\S+)", sub))
    ok("submitted FASTA == inventory (ids, exact sequences)", recs == {p["protein_id"].replace("|", "__"): p["sequence"] for p in inv["proteins"]})
    for m in ["Phobius", "DeepTMHMM", "TOPCONS2"]:
        for jp in sorted((pd / "raw" / m).glob("*.job.json")):
            j = json.loads(jp.read_text()); ok(f"{m} {jp.name}: batch FASTA identical to submitted FASTA", j.get("fasta_sha256") == subsha and sha((pd / j["fasta"]).read_bytes()) == subsha)
            outs = []
            if "output" in j: outs.append((j["output"], j["output_sha256"]))
            for v in (j.get("outputs") or {}).values() if isinstance(j.get("outputs"), dict) else []:
                for o in (v if isinstance(v, list) else [v]): outs.append((o["file"], o["sha256"]))
            if isinstance(j.get("outputs"), list): outs += [(o["file"], o["sha256"]) for o in j["outputs"]]
            if "result_zip" in j: outs.append((j["result_zip"], j["result_zip_sha256"]))
            bad = [f for f, h in outs if sha((pd / f).read_bytes()) != h]
            ok(f"{m} {jp.name}: raw output checksums ({len(outs)} files)", not bad, ";".join(bad))
            ok(f"{m} {jp.name}: status complete", j.get("status") == "complete", j.get("status", ""))
    invmap = {p["protein_id"]: p for p in inv["proteins"]}
    ok("data.json protein set == inventory", [p["protein_id"] for p in data["proteins"]] == list(invmap))
    nlab = 0
    for p in data["proteins"]:
        s = p["sequence"]; L = len(s)
        ok(f"{p['protein_id']} sequence/sha", s == invmap[p["protein_id"]]["sequence"] and sha(s.encode()) == p["sequence_sha256"] and L == p["length"])
        for m, pr in p["predictions"].items():
            nlab += 1
            lab = pr["labels"]; segs = pr["segments"]
            rebuilt = "".join(g["label"] * (g["stop"] - g["start"] + 1) for g in segs)
            contiguous = all(segs[i]["stop"] + 1 == segs[i + 1]["start"] for i in range(len(segs) - 1)) and segs[0]["start"] == 1 and segs[-1]["stop"] == L
            if not (len(lab) == L == len(pr["native_labels"]) and rebuilt == lab and contiguous and set(lab) <= set("IOMSBP")):
                ok(f"{p['protein_id']} {m} labels/segments", False)
            if pr.get("returned_sequence_matches") is False: ok(f"{p['protein_id']} {m} returned sequence", False)
            if m == "Phobius" and pr["native_fields"]["signal_peptide"]:
                cs = pr["native_fields"]["cleavage_site"]; nat = pr["native_labels"]
                ok(f"{p['protein_id']} Phobius SP boundary = cleavage site {cs}", pr["sp_range"] == [1, cs] and nat[cs] == "C" and lab[cs] != "S", f"SP {pr['sp_range']}, residue {cs+1} native '{nat[cs]}' -> '{lab[cs]}'")
        if p["protein_id"] in LIT:
            ref = LIT[p["protein_id"]]; calls = {m: (p["predictions"][m]["sp_range"] or [None, None])[1] for m in ("Phobius", "DeepTMHMM", "TOPCONS2") if m in p["predictions"]}
            res.setdefault("literature_comparison", []).append({"protein_id": p["protein_id"], "experimental_signal_peptide_end": ref["signal_peptide_end"], "reference": ref["ref"], "predicted_signal_peptide_end": calls})
    ok(f"all {nlab} label strings: length, contiguous coverage, segment rebuild, alphabet", not any("labels/segments" in f for f in res["failures"]))
    beta = [(p["protein_id"], m, pr.get("classification")) for p in data["proteins"] for m, pr in p["predictions"].items() if set(pr["labels"]) & set("BP")]
    res["beta_state_predictions"] = beta
    for pid, m, cls in beta:
        pr = next(p for p in data["proteins"] if p["protein_id"] == pid)["predictions"][m]
        gff = pd / Path(pr["source_output"]).parent / "TMRs.gff3"
        rows = [l.split("\t") for l in gff.read_text().splitlines() if l.startswith(pid.replace("|", "__") + "\t")]
        lab = {"signal": "S", "periplasm": "P", "Beta sheet": "B", "outside": "O", "inside": "I", "TMhelix": "M"}
        gseg = [[lab.get(r[1], "?"), int(r[2]), int(r[3])] for r in rows]
        ok(f"{pid} {m}: beta-state segments agree with model GFF (P=periplasm, O=outside, B=beta sheet)", gseg == [[g["label"], g["start"], g["stop"]] for g in pr["segments"]], json.dumps(gseg))
    ok("normalization validation errors empty", not data["validation_errors"], ";".join(data["validation_errors"]))
    for m in data["main_methods"]: ok(f"{m} coverage complete", data["coverage"][m]["complete"] == len(data["proteins"]), f"{data['coverage'][m]['complete']}/{len(data['proteins'])}")
    # atlas
    html = (pd / f"{key}_Topology_Atlas.html").read_text()
    emb = json.loads(re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>', html, re.S).group(1).replace("<\\/", "</").replace("<\\!--", "<!--"))
    ok("atlas embeds current data.json", emb == data)
    others = [c["name"] for k2, c in PHAGES.items() if k2 != key]
    ok("atlas contains no other organism names", not any(o in html for o in others))
    ok("atlas has no external script/style dependencies", not re.search(r'<(script|link)[^>]+(src|href)="https?:', html))
    b = browser["atlases"].get(key, {})
    ok("browser: no JS errors (file://, offline)", b and not b["js_errors"], str(b.get("js_errors")))
    ok("browser: every residue's identity, number and band state verified in full sequence map", b and all(x["residue_identity_and_numbering_ok"] and x["band_states_ok"] and x["seqmap_cells"] == x["length"] for x in b["proteins"]))
    ok("browser: bead cartoons account for every residue exactly once (drawn + explicitly omitted)", b and all(v["each_residue_once"] for x in b["proteins"] for v in x["beads"].values()))
    ok("browser: no bead overlaps (min centre distance >= bead diameter 20 px)", b and all(v["min_bead_centre_distance"] >= 20 for x in b["proteins"] for v in x["beads"].values() if v["residues_drawn"] > 1))
    ok("browser: SVG export is well-formed XML", b and b["exports"]["svg"]["xml_ok"])
    ok("browser: PNG exports produced", b and all(b["exports"][k2]["png_size"][0] > 0 for k2 in ("png2", "png4")), json.dumps({k2: b["exports"][k2].get("png_size") for k2 in ("png2", "png4")}))
    ok("browser: no horizontal page overflow at 390 px width", b and b.get("mobile_horizontal_overflow") is False)
    res["browser_check"] = {"source": "logs/browser_check.json (copied to verification_browser.json)", "checked_utc": browser["checked_utc"], "browser": browser["browser"], "ui": b.get("ui"), "exports": b.get("exports"),
                            "bead_abbreviations": {x["protein_id"]: {m: v["gaps"] for m, v in x["beads"].items() if v["gaps"]} for x in b["proteins"] if any(v["gaps"] for v in x["beads"].values())}}
    (pd / "verification_browser.json").write_text(json.dumps(b, indent=1))
    res["summary"] = {"checks": len(res["checks"]), "passed": sum(c["pass"] for c in res["checks"]), "failed": len(res["failures"])}
    (pd / "verification.json").write_text(json.dumps(res, indent=1))
    # checksums + package
    files = sorted(f for f in pd.rglob("*") if f.is_file() and f.name != "SHA256SUMS.txt")
    (pd / "SHA256SUMS.txt").write_text("".join(f"{sha(f.read_bytes())}  {f.relative_to(pd)}\n" for f in files))
    pk = ROOT / "packages"; pk.mkdir(exist_ok=True); zp = pk / f"{pd.name}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(pd.rglob("*")):
            if f.is_file(): z.write(f, f"{pd.name}/{f.relative_to(pd)}")
        for f in sorted((ROOT / "scripts").glob("*")):
            if f.is_file(): z.write(f, f"{pd.name}/scripts/{f.name}")
    print(key, res["summary"], res["failures"], f"package {zp.stat().st_size/1e6:.1f} MB")
