"""Build the self-contained offline HTML atlas for each phage (data + server plots embedded), plus a top-level index."""
import base64, json, sys, html
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir, ROOT
TPL = (Path(__file__).parent / "atlas_template.html").read_text()
def embed_json(o): return json.dumps(o, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")
rows = []
for key, cfg in PHAGES.items():
    pd = project_dir(key); data = json.loads((pd / "data.json").read_text())
    assets = {}
    for pr in data["proteins"]:
        a = {}; sid = pr["submitted_id"]
        ph = pr["predictions"].get("Phobius", {}).get("plot")
        if ph and (pd / ph).exists(): a["phobius_svg"] = base64.b64encode((pd / ph).read_bytes()).decode(); a["phobius_svg_src"] = ph
        tp = pr["predictions"].get("TOPCONS2", {}).get("provenance", {}).get("plot")
        if tp and (pd / tp).exists(): a["topcons_png"] = base64.b64encode((pd / tp).read_bytes()).decode(); a["topcons_png_src"] = tp
        assets[sid] = a
    out = TPL.replace("__TITLE__", html.escape(f"{key} Topology Atlas")).replace("__DATA__", embed_json(data)).replace("__ASSETS__", embed_json(assets))
    f = pd / f"{key}_Topology_Atlas.html"; f.write_text(out)
    cov = data["coverage"]
    rows.append((key, cfg, data, f.relative_to(ROOT), len(out)))
    print(key, f, f"{len(out)/1024:.0f} KB")
# index
items = "".join(f"""<a class="card" href="{html.escape(str(rel))}"><h2>{html.escape(cfg['name'])}</h2><p>{html.escape(cfg['accession'])} · {len(d['proteins'])} proteins · {sum(p['any_membrane_span'] for p in d['proteins'])} with ≥1 predicted membrane span (any main method) · {sum(p['any_signal_peptide'] for p in d['proteins'])} with a predicted signal peptide · {sum(bool(p['disagreements']) for p in d['proteins'])} with main-method disagreement</p><p class="cov">{' · '.join(f"{m} {d['coverage'][m]['complete']}/{d['coverage'][m]['inventory']}" for m in d['main_methods'])}</p></a>""" for key, cfg, d, rel, n in rows)
(ROOT / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>Dirty Science Canvas</title>
<style>body{{margin:0;background:#f6f5f1;color:#1b1f24;font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}main{{max-width:900px;margin:0 auto;padding:32px 16px}}h1{{margin:0 0 4px}}.card{{display:block;background:#fff;border:1px solid #d9dce1;border-radius:10px;padding:14px 18px;margin:14px 0;color:inherit;text-decoration:none}}.card:hover{{border-color:#1f4e79}}.card h2{{margin:0 0 4px;font-size:19px;color:#1f4e79}}.card p{{margin:2px 0}}.cov{{font-size:13px;color:#5b6470}}.note{{font-size:14px;color:#5b6470}}</style></head>
<body><main><h1>Dirty Science Canvas</h1><p class="note">Protein membrane-topology and charge atlases for small bacteriophage proteomes. Phobius, DeepTMHMM and TOPCONS2 (with its five components) were run on every annotated protein translation. All calls are computational predictions, not experimental evidence. Each atlas is a single offline HTML file.</p>{items}
<p class="note">Reproduce or extend: see <code>README.md</code> and <code>scripts/</code>.</p></main></body></html>""")
