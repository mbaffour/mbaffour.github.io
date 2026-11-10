# Deploying the lysis-gene caller

Find phage **holins, endolysins and spanins** in protein or nucleotide sequence. The three genes are called
**independently**, wherever they sit in a genome; co-located holin+endolysin+spanin sets are additionally flagged
as cassettes. One command, four input modes.

## Does it work on protein *and* nucleotide?
Yes — the classifiers operate on **protein** sequence (36 hand-crafted features + a 480-d ESM-2 embedding).

| input | how it is handled |
|---|---|
| **protein FASTA** (`--proteins`) | scored directly, one row per sequence (no positions → no cassette calls) |
| **nucleotide FASTA** (`--genome`) | genes called **de novo with Pyrodigal**, translated, then scored — works on a raw assembly, contig or MAG bin with no annotation |
| **GenBank** (`--genbank`) | annotated CDS translations scored in genome order |
| **NCBI accession** (`--acc`) | record fetched, then treated as GenBank |

Verified identical on phage N4: the de-novo nucleotide path recovers the same gp60 spanin / gp61 endolysin /
gp63 holin cassette as the annotated GenBank, from the bare genome sequence.

## Run it
```
python3 scripts/32_predict_lysis.py --genome my_phage.fna                 # raw assembly
python3 scripts/32_predict_lysis.py --proteins proteins.faa --out hits.tsv
python3 scripts/32_predict_lysis.py --genbank phage.gb --show-cassettes --threshold 0.95
python3 scripts/32_predict_lysis.py --acc NC_008720.1
```
Output is TSV: `id, gene, product, start, stop, strand, length, P_holin, P_endolysin, P_spanin, call, cassette`.
For many genomes at once use `scripts/30_scan_many.py`.

## What you need (pinned to the versions the models were built with)
- `pip install -r requirements.txt` — the single source of truth for dependencies. Step-by-step local install
  (tested on a clean machine) is in `README.md` under "Run it on your computer".
- **scikit-learn 1.9.1** is the one pin that matters: the pickled models must load under a matching scikit-learn.
  Python 3.11+ (3.13 tested); torch CPU build is fine (ESM-2 t12_35M is only 35 M params). On Linux install the CPU
  torch wheel first (`--index-url https://download.pytorch.org/whl/cpu`) to avoid multi-GB GPU builds.
- pyopal is NOT needed to predict (only to re-run the training pipeline: `requirements-pipeline.txt`).
- The ESM-2 weights `facebook/esm2_t12_35M_UR50D` (~130 MB) download from HuggingFace on first run. For offline/HPC
  use, pre-cache them (set `HF_HOME` to a populated cache) or run once online to warm `models/esm_cache`.
- The three model files in `models/`: `holin_model_curated.pkl`, `endolysin_model.pkl`, `spanin_model.pkl`.

## How well it works, and how to read the score
Honest leave-one-genome-out estimates (not the in-sample recovery), from `reports/*_eval.json`:

| gene | realistic (known family, new phage) | strict (never-seen family) |
|---|---|---|
| holin | genome AP 0.965 | 0.785 |
| endolysin | 0.843 | 0.729 |
| spanin | 0.834 | 0.729 |

- Precision is ~0.75 at `P>=0.9`; for high-confidence calls use `--threshold 0.95`.
- A **known-family** gene in a newly sequenced phage is called reliably; a **genuinely novel family** gets a
  ranked shortlist, not a verdict — triangulate with membrane topology (TMHMM/DeepTMHMM) and genomic context.
- Endolysin is limited by enzymatic-family diversity, not count; spanin's strong recovery rests partly on
  in-sample data, so its honest number is the 0.73 strict figure.
- The caller frequently flags a **second holin-fold gene** next to the annotated one — this is real dual-holin /
  holin-antiholin biology (see `reports/dual_holin_analysis.json`), not an error, but treat the second gene as a
  candidate to verify.

## Scaling / institutional deployment
- **Batch:** `scripts/30_scan_many.py --accessions list.txt` fetches and scans many genomes, aggregating recovery.
- **Galaxy (CPT):** `scripts/32_predict_lysis.py` is a clean single-command tool with FASTA in / TSV out, so it
  wraps directly as a Galaxy tool; ask and I will scaffold the `.xml` wrapper.
- **Reproducibility:** every data source has provenance (URL + SHA-256); `PROTOCOL.md` documents the full pipeline.
