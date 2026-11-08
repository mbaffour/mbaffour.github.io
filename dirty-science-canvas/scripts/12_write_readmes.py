"""Generate per-organism README.md (all counts/dates/jobs pulled from data.json, job records and verification.json) and the top-level README."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import ORGANISMS, project_dir, ROOT, REPO_SLUG, RERUN_WORKFLOW
def spans(pr):
    if not pr: return "—"
    t = ([f"SP {pr['sp_range'][0]}–{pr['sp_range'][1]}"] if pr["sp_range"] else []) + [f"{'β' if s[2] == 'B' else 'TM'} {s[0]}–{s[1]}" for s in pr["spans"]]
    return ", ".join(t) or "none"
REBUILD = """```
python3 scripts/01_fetch_inputs.py --org {k}     # skips files already present
python3 scripts/02_inventory.py --org {k}
python3 scripts/03_run_phobius.py --org {k}      # resumable; plans batches within documented limits
python3 scripts/05_run_deeptmhmm.py --org {k}    # resumable
python3 scripts/04_run_topcons.py --org {k}      # submit/poll/collect; never resubmits a batch with a job ID
python3 scripts/06_normalize.py --org {k} && python3 scripts/08_build_atlas.py --org {k}
node scripts/09_browser_check.js logs/browser_check.json && python3 scripts/11_validate_package.py --org {k}
python3 scripts/rerun.py --org {k} [--proteins "ID1,ID2"]   # re-run: new batches, earlier results kept as superseded
```"""
rows_top = []
for k, o in ORGANISMS.items():
    pd = project_dir(k)
    if not (pd / "data.json").exists(): continue
    d = json.loads((pd / "data.json").read_text()); v = json.loads((pd / "verification.json").read_text()) if (pd / "verification.json").exists() else None
    P = d["proteins"]; M = d["main_methods"]; ip = d["input_provenance"]
    cov = {m: d["coverage"][m] for m in M}
    # 'no_topology_produced' means the method ran and declined on that sequence, which is terminal: not partial.
    dec = {m: c["status_counts"].get("no_topology_produced", 0) for m, c in cov.items()}
    partial = any(c["complete"] + dec[m] < c["eligible"] for m, c in cov.items())
    cache = {}
    for p in P:
        tm = p.get("topcons_meta")
        if tm: cache[tm.get("cache")] = cache.get(tm.get("cache"), 0) + 1
    vers = sorted({j.get("app_version") for j in d["jobs"]["DeepTMHMM"] if j.get("app_version")}) or ["not recorded"]
    inel = {m: [(p["protein_id"], p["ineligible"][m]) for p in P if p.get("ineligible", {}).get(m)] for m in M}
    n_span = sum(p["any_membrane_span"] for p in P); n_sp = sum(p["any_signal_peptide"] for p in P); n_dis = sum(bool(p["disagreements"]) for p in P)
    beta = v.get("beta_state_predictions", []) if v else []
    rows_top.append(f"| [{o['name']}]({pd.name}/{k}_Topology_Atlas.html) | {o['kind']} | {', '.join(o['accessions'])} | {len(P):,} | {n_span:,} | {n_sp:,} | {len(beta):,} | " + " · ".join(f"{m} {cov[m]['complete']:,}/{cov[m]['eligible']:,}" + (f" (+{dec[m]} declined)" if dec[m] else "") for m in M) + (" **(partial)**" if partial else "") + " |")
    lines = [f"# {o['name']} — membrane topology & charge lab reference", "",
             f"Open **`{k}_Topology_Atlas.html`** (one offline file), or the combined atlas `../Dirty_Science_Canvas_Atlas.html`. All topology calls are **computational predictions**, not experimental evidence.", ""]
    if any(dec.values()):
        lines += ["> **Declined predictions:** " + "; ".join(f"{m}: {dec[m]}" for m in M if dec[m]) +
                  ". TOPCONS2 reports `***No topology could be produced with this method***` for some sequences "
                  "(here, soluble proteins where every component returns an all-outside topology). Those are "
                  "recorded as `no_topology_produced`: a result from the method, not a missing job, and resubmitting "
                  "reproduces it.", ""]
    if partial: lines += ["> **Partial:** at least one predictor has not yet finished every eligible protein (see coverage). Missing results are shown as pending, never substituted. Resume with the commands below.", ""]
    lines += ["## Source", *[f"- RefSeq **{s['accessionversion']}**: \"{s['title']}\", {s['slen']:,} nt, {s['topology']}; NCBI record updated {s['updatedate']}; taxid {s['taxid']}." for s in ip["ncbi_summaries"]],
              f"- Downloaded from NCBI E-utilities on {ip['files'][0]['retrieved_utc'][:10]} (UTC); URLs and SHA-256 in `inputs/provenance.json`" + (" (GenBank stored gzip-compressed; checksums of both forms recorded)." if o["kind"] == "host" else "."),
              f"- Scope: all **{len(P):,}** CDS features with a `/translation` ({d['n_cds']:,} CDS features; {len(d['pseudogenes'])} pseudogenes/untranslated CDSs listed in `pseudogene_inventory.json`). The RefSeq annotation is used exactly; translations were cross-checked against NCBI's CDS FASTA and re-derived from coordinates (strand, joins, `codon_start`, genetic code, `transl_except`). No sequence was trimmed, padded or edited.",
              f"- Context: {d['host_note']}", "",
              "## Coverage", "| Method | Complete / eligible | Not eligible (reason) |", "|---|---|---|"]
    for m in M:
        c = cov[m]; ie = inel[m]
        lines.append(f"| {m} | {c['complete']:,} / {c['eligible']:,} ({c['status_counts']}) | " + ("; ".join(f"`{pid}`: {why}" for pid, why in ie[:8]) + (f"; … {len(ie) - 8} more" if len(ie) > 8 else "") if ie else "—") + " |")
    lines += ["", f"- **Phobius**: phobius.sbc.su.se JSON API; batches ≤100 sequences and ≤50,000 residues. {'Per-protein posterior plots (SVG) in `raw/Phobius/plots/`.' if o['kind'] == 'phage' else 'Plots not requested at proteome scale.'}",
              f"- **DeepTMHMM**: BioLib app DTU/DeepTMHMM ({', '.join(vers)}); ≤500 sequences per job, one job at a time.",
              f"- **TOPCONS2**: topcons.net WSDL API; ≤1,000 sequences per job, ≤2 active jobs. Cache status reported by the server: {', '.join(f'{a}: {b:,}' for a, b in sorted(cache.items(), key=str)) or '—'}. Components (OCTOPUS, Philius, PolyPhobius, SCAMPI, SPOCTOPUS) feed the consensus; they are not extra votes.",
              f"- Job records (exact batch FASTA checksum, job ID, times, status, output checksums) are in `raw/<Method>/*.job.json`; {sum(len(j) for j in d['jobs'].values())} records.", "",
              "## Summary", f"- {n_span:,} proteins with ≥1 predicted membrane span (any main method); {n_sp:,} with a predicted signal peptide; {len(beta):,} with DeepTMHMM β-type states; {n_dis:,} with main-method disagreement.",
              "- Per-protein calls for every method: `topology_summary.csv` (segments use `LABELstart-stop` runs, 1-based inclusive) and `data.json`.", ""]
    if v and v.get("literature_comparison"):
        lines += ["### Comparison with experimentally known signal-peptide ends (informational)"] + [f"- `{x['protein_id']}`: experimental end {x['experimental_signal_peptide_end']} ({x['reference']}). Predicted: " + ", ".join(f"{m} {e}" for m, e in x["predicted_signal_peptide_end"].items()) + "." for x in v["literature_comparison"]] + [""]
    if o["kind"] == "phage" and len(P) <= 300:
        lines += ["### Per-protein calls (main methods)", "| Gene | Locus tag | Product | aa | " + " | ".join(M) + " | Disagreement |", "|---|---|---|---|" + "---|" * len(M) + "---|"]
        for p in P:
            pr = {m: p["pred"].get(m) for m in M}
            lines.append(f"| {p['gene'] or p['curator_alias'] or '—'} | `{p['locus_tag']}` | {p['product']} | {p['length']} | " + " | ".join(spans(pr[m]) if pr[m] else p['status'].get(m, '').replace('_', ' ') for m in M) + f" | {', '.join(p['disagreements']) or '—'} |")
        lines.append("")
    lines += ["## Conventions & cautions", f"- {d['coordinate_convention']}; signal peptides keep precursor numbering. {d['segment_encoding']}.",
              "- Normalized states: " + "; ".join(f"**{a}** {b}" for a, b in d["state_definitions"].items()) + ". Native labels are kept (`nseg`).",
              "- Inside/outside on proteins without a predicted span does not establish localization. Charge classes are approximate side-chain categories near neutral pH, not measured charges.",
              "- Disagreements are flagged, never resolved into a consensus.", "",
              "## Figures", "The atlas renders four views per protein — A presentation orientation (residue-proportional scale), B full-length sequence & charge map, C residue-bead cartoon, D method-comparison tracks — with SVG / PNG 2×·4× / copy-image / copy-caption. Every figure is laid out by a collision-free label engine and audited in a real browser (no overlapping text, no clipped text, no line crossing a label, no crossing leaders or bonds). A figure library for this organism can be regenerated with `node scripts/10_export_figures.js --org " + k + " [--png]`.", "",
              "## Re-run", f"- In the atlas: per-protein **Phobius ↗** and **DeepTMHMM ↗** buttons submit the exact sequence to the official servers in one click; **TOPCONS2 ↗** copies the FASTA and opens its form (it requires a session token).",
              f"- Pipeline: GitHub → Actions → *Topology atlas re-run* (`.github/workflows/{RERUN_WORKFLOW}`, https://github.com/{REPO_SLUG}/actions/workflows/{RERUN_WORKFLOW}) with organism `{k}`; or locally `python3 scripts/rerun.py --org {k}`.", ""]
    if v:
        s = v["summary"]
        lines += ["## Validation", f"`verification.json`: {s['passed']} pass, {s['failed']} fail, {s['pending']} pending of {s['checks']} checks. " + (f"Pending: {'; '.join(v['pending'][:4])}." if v["pending"] else "") + (f" Failures: {'; '.join(v['failures'][:4])}." if v["failures"] else ""),
                  "Checks cover input checksums, CDS reconciliation, batch-FASTA identity, raw-output checksums, segment expansion/contiguity/alphabet for every prediction, Phobius signal-peptide boundaries, DeepTMHMM β segments against its GFF, atlas embedding, and the headless-browser audit.", ""]
    lines += ["## Rebuild / resume (from `dirty-science-canvas/`; Python 3 with `biopython requests suds pybiolib`, Node with Playwright)", REBUILD.format(k=k),
              "Web-job links expire; the raw outputs and job records here are the durable record." + (" Large TOPCONS2 result zips (mostly per-sequence images) are not stored; their checksums/URLs are recorded and every text output needed to reproduce the predictions is archived unmodified in `raw/TOPCONS2/*.text.tar.xz`." if any(j.get("result_text_archive") for j in d["jobs"]["TOPCONS2"]) or o["kind"] == "host" else "")]
    (pd / "README.md").write_text("\n".join(lines) + "\n")
(ROOT / "README.md").write_text(f"""# Dirty Science Canvas

Membrane-topology and charge atlases for **model bacteriophages and their hosts**. Every annotated protein translation was run through **Phobius**, **DeepTMHMM** and **TOPCONS2** (with OCTOPUS, Philius, PolyPhobius, SCAMPI and SPOCTOPUS) within each service's documented limits; results are normalized with full provenance, validated, and rendered into self-contained offline HTML atlases. All calls are computational predictions, not experimental evidence.

**Start here:** `index.html` → `Dirty_Science_Canvas_Atlas.html` (the combined atlas: every organism in one searchable file). Each organism folder also has its own atlas, README, inputs, untouched raw outputs with job records, normalized `data.json`/CSV and `verification.json`.

| Organism | Kind | RefSeq | Proteins | ≥1 span | Signal peptide | β states | Complete / eligible |
|---|---|---|---|---|---|---|---|
{chr(10).join(rows_top)}

**Figures** are publication-ready SVG/PNG produced by a collision-free label engine and audited in a real browser for overlapping or clipped text and crossing lines. **Re-run:** one-click Phobius and DeepTMHMM submissions per protein from the atlas; pipeline re-runs via the GitHub Actions workflow `{RERUN_WORKFLOW}` or `python3 scripts/rerun.py`. **Pipeline:** `scripts/` (fetch → inventory → predictors → normalize → atlas → browser audit → validation). Add an organism by adding an entry to `scripts/config.py`.
""")
print("ok")
