"""Generate per-organism README.md (all counts/dates pulled from data.json and job records) and the top-level README."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config import PHAGES, project_dir, ROOT
def fmt_spans(pr):
    if not pr: return "—"
    t = []
    if pr["sp_range"]: t.append(f"SP {pr['sp_range'][0]}–{pr['sp_range'][1]}")
    t += [f"{'β' if s[2]=='B' else 'TM'} {s[0]}–{s[1]}" for s in pr["spans"]]
    return ", ".join(t) or "none"
for key, cfg in PHAGES.items():
    pd = project_dir(key); d = json.loads((pd / "data.json").read_text()); v = json.loads((pd / "verification.json").read_text())
    ip = d["input_provenance"]; P = d["proteins"]; M = d["main_methods"]
    cache = {}
    for p in P:
        pr = p["predictions"].get("TOPCONS2")
        if pr: cache[pr["provenance"]["cache_status"]] = cache.get(pr["provenance"]["cache_status"], 0) + 1
    gens = sorted({p["predictions"]["TOPCONS2"]["provenance"]["generated"][:10] for p in P if "TOPCONS2" in p["predictions"]})
    jobs = d["jobs"]
    def jl(m): return "; ".join(f"batch {j.get('batch')}{' ('+j['format']+')' if j.get('format') else ''}: job `{j.get('jobid') or j.get('job_id') or 'n/a'}`, {j.get('status')}, submitted {j.get('submitted_utc')}" for j in jobs[m])
    dtm_ver = sorted({j.get("app_version") or "not recorded" for j in jobs["DeepTMHMM"]})
    rows = "\n".join(f"| {p['gene'] or p['curator_alias']} | `{p['locus_tag']}` | {p['protein_accession']} | {p['product']} | {p['length']} | " + " | ".join(fmt_spans(p['predictions'].get(m)) for m in M) + f" | {', '.join(p['disagreements']) or '—'} |" for p in P)
    lit = "\n".join(f"- `{x['protein_id']}`: experimentally the signal peptide ends at residue {x['experimental_signal_peptide_end']} ({x['reference']}). Predicted ends: " + ", ".join(f"{m} {e}" for m, e in x["predicted_signal_peptide_end"].items()) + "." for x in v.get("literature_comparison", []))
    beta = "\n".join(f"- `{pid}` — {m} class **{cls}**: periplasm (P), extracellular (O) and β-strand (B) segments, shown as a linear map rather than a helical cartoon." for pid, m, cls in v.get("beta_state_predictions", []))
    txt = f"""# {cfg['name']} — membrane topology & charge lab reference

Open **`{key}_Topology_Atlas.html`** in any modern browser. It is a single self-contained file that works offline: data, figure code and server plots are all embedded. Links to papers need internet access.

All topology calls here are **computational predictions**, not experimental evidence.

## Source
- RefSeq **{d['accession']}**, "{ip['ncbi_summary']['title']}", {ip['ncbi_summary']['slen']} nt, {ip['ncbi_summary']['topology']}. The NCBI record was last updated {ip['ncbi_summary']['updatedate']}, taxid {ip['ncbi_summary']['taxid']}.
- Downloaded from NCBI E-utilities on {ip['files'][0]['retrieved_utc'][:10]} (UTC). URLs and SHA-256 checksums are in `inputs/provenance.json`:
  - GenBank record: `inputs/{d['accession']}.gb`
  - NCBI CDS translations: `inputs/{d['accession']}.cds_aa.fasta`
  - Genome FASTA: `inputs/{d['accession']}.fna`
- Annotation preference: the current RefSeq annotation is used exactly as published. **Scope:** all {len(P)} CDS features with a `/translation` ({d['n_cds']} CDS features in total; {len(d['pseudogenes'])} pseudogenes or untranslated CDSs).
- Every translation was cross-checked in two ways:
  - Against NCBI's CDS FASTA.
  - Against an independent translation from the coordinates (strand, joins, `codon_start`, genetic code 11). Both agree for all proteins.
- Flags such as `joined_location_spans_circular_origin` mark CDSs that wrap the circular genome origin. They are informational. No sequence was trimmed, padded or edited.{' Curator gene letters (`curator_alias`) are added only as search aliases; RefSeq ' + d['accession'] + ' has no `/gene` qualifiers.' if any(p['curator_alias'] for p in P) else ''}
- Host context: {d['host_note']}

## Methods run (all {len(P)} proteins)
| Method | Coverage | Submission |
|---|---|---|
""" + "\n".join(f"| {m} | {d['coverage'][m]['complete']}/{d['coverage'][m]['inventory']} | {jl(m)} |" for m in M) + f"""

- **Phobius**: phobius.sbc.su.se JSON API (`/api/predict`, with `plot: true`). The plain-text long/short formats and the web-form outputs are kept in `raw/Phobius/` as cross-checks. Signal-peptide boundaries were verified against the reported cleavage site, and the `C` cleavage marker is never counted as a signal-peptide residue.
- **DeepTMHMM**: BioLib app DTU/DeepTMHMM, version(s): {', '.join(dtm_ver)}. Raw `predicted_topologies.3line`, `TMRs.gff3` and `deeptmhmm_results.md` are in `raw/DeepTMHMM/batch1/results/`.
- **TOPCONS2**: topcons.net WSDL API, with OCTOPUS, Philius, PolyPhobius, SCAMPI and SPOCTOPUS outputs retained.
  - TOPCONS2 served cached results for identical sequences: {', '.join(f'{k}: {n}' for k, n in sorted(cache.items()))}. The original computation dates are {', '.join(gens)}.
  - Per-protein generation dates and cache status are in `data.json`.
  - The original result zip and an extracted copy are in `raw/TOPCONS2/`.
  - The components feed the TOPCONS2 consensus; they are not independent votes in addition to it.

## Per-protein summary (main methods)
| Gene | Locus tag | Accession | Product | aa | {' | '.join(M)} | Disagreement |
|---|---|---|---|---|{'---|' * len(M)}---|
{rows}

{('### β-type predictions' + chr(10) + beta + chr(10)) if beta else ''}
{('### Comparison with experimentally known signal-peptide ends (informational)' + chr(10) + lit + chr(10)) if lit else ''}
## Conventions & cautions
- {d['coordinate_convention']}. Signal peptides keep precursor numbering.
- Normalized states: {'; '.join(f'**{k}** {v}' for k, v in d['state_definitions'].items())}. Each method's native label strings are kept alongside (`native_labels`).
- Inside/outside labels on proteins with no predicted span do not establish localization.
- For phage proteins, no specific host membrane is assigned, and none of this predicts a viral envelope.
- Charge classes (K/R, D/E, variable H, declared hydrophobic/aromatic group) are approximate side-chain categories near neutral pH. They are not measured charges, net charge, pI or electrostatics.
- Disagreements between methods are flagged, never resolved into a consensus.

## Figures
The atlas draws four views for each protein:
- **A**: presentation orientation, with residue-proportional horizontal scale.
- **B**: full-length sequence and charge map. It shows every residue by default; an optional window is available.
- **C**: switchable residue-bead cartoon. Long loops are abbreviated with explicit omitted ranges.
- **D**: method-comparison tracks.

Every figure has buttons for SVG, PNG (2×/4×; PNG is automatically down-scaled when it would exceed browser canvas limits), copy-image (falls back to download) and copy-caption. A pre-rendered SVG library is in `figures/`, with 2× PNGs of view A for proteins with a predicted span or signal peptide.

## Files
`data.json` (normalized, complete) · `protein_inventory.csv` · `topology_summary.csv` · `inventory.json` · `pseudogene_inventory.json` · `inputs/` · `raw/` · `figures/` · `verification.json` + `verification_browser.json` · `SHA256SUMS.txt`. The zip package in `../packages/` also contains `scripts/`.

## Validation
`verification.json` records {v['summary']['passed']}/{v['summary']['checks']} passing checks (run time recorded in the file). They cover:
- input checksums and CDS reconciliation;
- submitted-FASTA identity per batch and raw-output checksums;
- label length, contiguity and alphabet for every prediction;
- Phobius signal-peptide boundaries, and β segments against DeepTMHMM's GFF;
- that the atlas embeds the current data and contains no other organism's names;
- a headless Chromium pass ({v['browser_check']['browser']}, file://, offline) over every protein. It confirms that each residue's identity, number and band state is correct and that bead cartoons account for every residue exactly once. It also checks bead overlap, search, filters, component toggles, windowing, SVG/PNG export, and the absence of horizontal overflow at phone width.

Clipboard copy was not exercised headlessly.

## Rebuild / resume
From the project root (`dirty-science-canvas/`), with Python 3 + `biopython requests suds pybiolib` and Node + Playwright:
```
python3 scripts/01_fetch_inputs.py        # skips files already present
python3 scripts/02_inventory.py
python3 scripts/03b_run_phobius_api.py    # resumable; skips complete batches
python3 scripts/04_topcons_submit.py      # never resubmits a batch that has a job ID
python3 scripts/05_topcons_collect.py     # poll + download; exit code 2 while pending
python3 scripts/07_run_deeptmhmm.py       # resumable
python3 scripts/06_normalize.py && python3 scripts/08_build_atlas.py
node scripts/10_export_figures.js && node scripts/09_browser_check.js logs/browser_check.json
python3 scripts/11_validate_package.py && python3 scripts/12_write_readmes.py
```
Web-job links (TOPCONS2 result URLs, BioLib job IDs) may expire; the raw outputs here are the durable record.
"""
    (pd / "README.md").write_text(txt)
# top-level
lines = []
for key, cfg in PHAGES.items():
    d = json.loads((project_dir(key) / "data.json").read_text()); P = d["proteins"]
    lines.append(f"| [{cfg['name']}]({key}_Topology_Lab_Reference/{key}_Topology_Atlas.html) | {d['accession']} | {len(P)} | {sum(p['any_membrane_span'] for p in P)} | {sum(p['any_signal_peptide'] for p in P)} | {sum(bool(p['disagreements']) for p in P)} | " + " · ".join(f"{m} {d['coverage'][m]['complete']}/{len(P)}" for m in d['main_methods']) + f" | [zip](packages/{key}_Topology_Lab_Reference.zip) |")
(ROOT / "README.md").write_text(f"""# Dirty Science Canvas

Protein membrane-topology and charge atlases for small bacteriophage proteomes. Every annotated protein translation was run through **Phobius**, **DeepTMHMM** and **TOPCONS2** (including its OCTOPUS, Philius, PolyPhobius, SCAMPI and SPOCTOPUS components). The results were normalized with provenance, validated, and rendered into self-contained offline HTML atlases.

All calls are computational predictions, not experimental evidence.

| Phage | RefSeq | Proteins | ≥1 span (any main method) | Signal peptide (any main method) | Main-method disagreement | Coverage | Package |
|---|---|---|---|---|---|---|---|
{chr(10).join(lines)}

Start at `index.html`, or open a phage's `*_Topology_Atlas.html` directly; each works offline. Each phage folder's `README.md` documents its sources, jobs, coverage, conventions, validation and how to rebuild it.

`scripts/` holds the whole pipeline (fetch → inventory → predictors → normalize → atlas → figures → browser check → validation/package). `scripts/config.py` lists the phages, so adding a phage means adding an entry there and rerunning the pipeline.
""")
print("ok")
