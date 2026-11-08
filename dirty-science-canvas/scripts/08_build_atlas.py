"""Build the combined offline atlas (Dirty_Science_Canvas_Atlas.html), one atlas per organism, and index.html.

Usage: python3 scripts/08_build_atlas.py [--org k1,k2] [--only k1,k2]
  --org   rebuild these organisms' individual atlases (the combined atlas still spans every organism present)
  --only  restrict the WHOLE published site to these organisms: the combined atlas, the landing page and its
          counts. Organisms with a data.json that are left out are listed on the landing page as still running,
          so a partially finished run can be published honestly instead of shipping '(partial)' coverage rows.
"""
import datetime, html, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import ORGANISMS, project_dir, ROOT, REPO_SLUG, RERUN_WORKFLOW, selected
TPL = (Path(__file__).parent / "atlas_template.html").read_text()
def embed(o): return json.dumps(o, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")
KEEP = ("protein_id", "gene", "locus_tag", "product", "synonyms", "curator_alias", "note", "replicon", "start", "stop", "strand", "location", "protein_accession",
        "sequence", "length", "sequence_sha256", "annotation_flags", "identical_sequence_to", "status", "pred", "superseded", "topcons_meta", "ineligible",
        "disagreements", "any_membrane_span", "any_signal_peptide")
def load(key):
    d = json.loads((project_dir(key) / "data.json").read_text()); prots = []
    for p in d["proteins"]:
        q = {k: p[k] for k in KEEP if k in p and p[k] not in ({}, [], None, "") or k in ("annotation_flags", "disagreements", "status", "pred")}
        if p.get("transl_table", 11) != 11: q["transl_table"] = p["transl_table"]
        if "topcons_meta" in q: q["topcons_meta"] = {k: q["topcons_meta"].get(k) for k in ("generated", "cache", "jobid", "src")}
        # derivable fields are dropped from the embedded copy (data.json keeps everything): source path, spans/SP/nside summaries,
        # and native labels where they equal the normalized labels up to case (DeepTMHMM, TOPCONS2 family)
        q["pred"] = {m: {k: v for k, v in pr.items() if k not in ("src", "spans", "sp_range", "nside") and not (k == "nseg" and m != "Phobius") and v not in (None, [], "")}
                     for m, pr in p["pred"].items()}
        # compact status: omit 'complete' where a prediction exists, and component statuses equal to TOPCONS2's
        st = p["status"]; q["status"] = {m: v for m, v in st.items() if not (v == "complete" and m in p["pred"]) and not (m in d["component_methods"] and v == st.get("TOPCONS2"))}
        if len(d["accessions"]) == 1 and q.get("replicon") == d["accessions"][0]: q.pop("replicon", None)
        q["org"] = key; prots.append(q)
    beta = sum(any(c in "BP" for pr in p["pred"].values() for c in {s[0] for s in pr["seg"].split(",")}) for p in d["proteins"])
    meta = {"name": d["organism"], "kind": d["kind"], "accession": d["accession"], "host_note": d["host_note"], "n": len(prots), "n_cds": d["n_cds"],
            "n_pseudo": len(d["pseudogenes"]), "coverage": d["coverage"], "jobs": d["jobs"], "input_provenance": d["input_provenance"],
            "n_span": sum(p["any_membrane_span"] for p in d["proteins"]), "n_sp": sum(p["any_signal_peptide"] for p in d["proteins"]), "n_beta": beta}
    vers = sorted({j.get("app_version") for j in d["jobs"]["DeepTMHMM"] if j.get("app_version")})
    return d, meta, prots, vers
def build(keys, title, base_for, out):
    orgs, prots, vers, d0 = {}, [], set(), None
    for k in keys:
        d, meta, ps, v = load(k); d0 = d0 or d; meta["base"] = base_for(k); orgs[k] = meta; prots += ps; vers |= set(v)
    data = {"title": title, "organisms": orgs, "order": keys, "proteins": prots, "main_methods": d0["main_methods"], "component_methods": d0["component_methods"],
            "state_definitions": d0["state_definitions"], "segment_encoding": d0["segment_encoding"], "coordinate_convention": d0["coordinate_convention"],
            "repo": REPO_SLUG, "workflow": RERUN_WORKFLOW, "deeptmhmm_versions": ", ".join(sorted(vers)) or "version not recorded",
            "built_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    out.write_text(TPL.replace("__TITLE__", html.escape(title)).replace("__DATA__", embed(data)))
    print(out.relative_to(ROOT), f"{out.stat().st_size / 1e6:.1f} MB", len(prots), "proteins", flush=True)
    return orgs
def only(argv):
    for i, a in enumerate(argv):
        if a == "--only" and i + 1 < len(argv): return [k for k in argv[i + 1].split(",") if k]
    return None
present = [k for k in ORGANISMS if (project_dir(k) / "data.json").exists()]
_only = only(sys.argv)
avail = [k for k in present if k in _only] if _only else present
held_back = [k for k in present if k not in avail]
for k in [k for k in selected(sys.argv) if k in avail]:
    build([k], f"{ORGANISMS[k]['name']} — membrane topology & charge atlas", lambda _k: "", project_dir(k) / f"{k}_Topology_Atlas.html")
orgs = build(avail, "Dirty Science Canvas — membrane topology & charge atlas of model phages and hosts", lambda k: f"{project_dir(k).name}/", ROOT / "Dirty_Science_Canvas_Atlas.html")
def row(k, o):
    cov = " · ".join(f"{m} {o['coverage'][m]['complete']:,}/{o['coverage'][m]['eligible']:,}" for m in ("Phobius", "DeepTMHMM", "TOPCONS2"))
    done = all(o['coverage'][m]['complete'] == o['coverage'][m]['eligible'] for m in ("Phobius", "DeepTMHMM", "TOPCONS2"))
    return (f'<tr><td><a href="{project_dir(k).name}/{k}_Topology_Atlas.html">{html.escape(o["name"])}</a></td><td>{html.escape(o["accession"])}</td><td>{o["n"]:,}</td>'
            f'<td>{o["n_span"]:,}</td><td>{o["n_sp"]:,}</td><td>{o["n_beta"]:,}</td><td class="cov">{cov}{"" if done else " <b>(partial)</b>"}</td></tr>')
tbl = lambda kind: "".join(row(k, o) for k, o in orgs.items() if o["kind"] == kind)
combined_mb = (ROOT / "Dirty_Science_Canvas_Atlas.html").stat().st_size / 1e6
# Only warn about weight when it is actually heavy; a 3 MB page does not need a scare label.
combined_size = (f"{combined_mb:.0f}&nbsp;MB download, slow on mobile" if combined_mb >= 8
                 else f"{combined_mb:.1f}&nbsp;MB download")
hosts_block = (f"<h2>Model hosts</h2><div class=\"wrap\"><table>{head}{tbl('host')}</table></div>"
               if any(o["kind"] == "host" for o in orgs.values()) else "")
pending_block = ("<p class=\"note\"><b>Still running:</b> " + ", ".join(html.escape(ORGANISMS[k]["name"]) for k in held_back)
                 + ". Their predictions are not finished, so they are not published yet rather than shown as partial.</p>"
                 if held_back else "")
head = "<tr><th>Organism</th><th>RefSeq</th><th>Proteins</th><th>≥1 span</th><th>Signal peptide</th><th>β states</th><th>Complete / eligible</th></tr>"
(ROOT / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>Dirty Science Canvas</title>
<style>body{{margin:0;background:#f5f4f0;color:#17202a;font:16px/1.5 "Helvetica Neue",Helvetica,Arial,sans-serif}}main{{max-width:1100px;margin:0 auto;padding:32px 16px}}h1{{margin:0 0 4px}}h2{{margin:28px 0 8px;font-size:19px}}
.big{{display:block;background:#13263b;color:#fff;border-radius:10px;padding:16px 20px;text-decoration:none;margin:18px 0}}.big b{{font-size:19px}}.big span{{display:block;color:#c8d3df;font-size:14px}}
.wrap{{overflow-x:auto;background:#fff;border:1px solid #d9dce1;border-radius:10px}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:7px 10px;border-bottom:1px solid #eceef1;text-align:left;white-space:nowrap}}th{{background:#f3f4f6}}td.cov{{font-size:12.5px;color:#5b6470}}a{{color:#1f4e79}}.note{{font-size:14px;color:#5b6470}}</style></head>
<body><main><h1>Dirty Science Canvas</h1><p class="note">Membrane-topology and charge atlases for model bacteriophages and their hosts. Phobius, DeepTMHMM and TOPCONS2 (with its five components) were run on every annotated protein translation within each service's documented limits. All calls are computational predictions, not experimental evidence. Every atlas is a single offline HTML file.</p>
<h2>Atlases by organism</h2><p class="note">One self-contained file each — open the organism you need. Every phage atlas is under 1&nbsp;MB.</p>
<div class="wrap"><table>{head}{tbl('phage')}</table></div>{hosts_block}
<a class="big" href="Dirty_Science_Canvas_Atlas.html"><b>Or open the combined atlas →</b><span>{len(orgs)} organisms · {sum(o['n'] for o in orgs.values()):,} proteins in one file · search and filter across everything · <b>{combined_size}</b></span></a>{pending_block}
<p class="note">Each organism folder has its own atlas, README, inputs, untouched raw predictor outputs and job records, normalized data and validation report. Pipeline: <code>scripts/</code>; re-run: <code>scripts/rerun.py</code> or the GitHub Actions workflow <code>{RERUN_WORKFLOW}</code>.</p></main></body></html>""")
print("index.html")
