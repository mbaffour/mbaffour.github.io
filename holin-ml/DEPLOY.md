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
python3 scripts/32_predict_lysis.py --genbank phage.gb --show-cassettes --domains    # high_conf column = confident calls
python3 scripts/32_predict_lysis.py --acc NC_008720.1
```
Output is TSV:
`id, gene, product, start, stop, strand, length, P_holin, P_endolysin, P_spanin, rank_holin, rank_endolysin,
rank_spanin, call, high_conf, lysis_call, cassette` — plus `pfam_lysis`, `dom_tier_*` and `ev_rank_*` with `--domains`.

**The call.** For genome and GenBank input the tool names one gene per class in `lysis_call` and in a `LYSIS GENE CALLS`
summary: the top-ranked protein once its neighbours are taken into account (a candidate beside a strong holin,
endolysin or spanin is lifted; `models/context_params.json`). It is **confident** when its score clears that class's
measured cut-off or, with `--domains`, when it carries a catalytic lysis domain; otherwise **candidate**. On 130
CPT-curated phages, cross-validated with related phages kept out of each other's training folds, confident calls were
correct 95% (endolysin), 93% (holin) and 98% (spanin) of the time for known families, and 85%, 90% and 98% for novel
ones. Holins and endolysins are called by the context rule; spanins by a learned second-stage caller
(`models/spanin_caller.pkl`) that uses lipobox and membrane-topology features. See `reports/integrated_caller.md`. Ranks are context-aware; `--no-context` turns that off.

`high_conf` lists the classes whose probability clears that class's **own** high-confidence cut-off, stored in each
model file: 0.95 for holin and spanin, 0.9995 for endolysin. Use it instead of a single `--threshold 0.95`, which no
longer means the same thing for every class (see "How well it works").

`rank_*` is the protein's rank within this run for that class (1 = highest). Ranks are there because a
probability is not safe to read as a verdict out of distribution: the ranked shortlist per class is what the
leave-one-genome-out numbers actually measure. The summary prints the top `--top N` per class with coordinates,
length, score and rank **whatever the threshold**, since a novel-family gene can rank well while scoring below
any threshold.

`--domains` additionally scans every protein with the lysis Pfam HMMs (pyhmmer; HMMs cached in
`data/raw/pfam_hmm`, fetched once from InterPro) and ends with the line that matters most:

```
# 1 protein(s) carry a lysis Pfam domain but were NOT called -- inspect these first:
#   KNU90_gp039 (PF01832:endolysin, rank_e=25)
```

That is evidence independent of the model, and on *Bacteroides* phage DAC15 it is the **only** thing that finds
the real endolysin candidate: gp039 scores 0.0002 and ranks **12th of 118** with the current endolysin model (0.0059,
25th, with the previous one), so neither the threshold nor the ranking would have surfaced it. Use `--domains` on anything out of distribution.

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
  The endolysin model is trained only on evidence-backed labels (no positives labelled from genome product names); the
  spanin model keeps name-labelled spanins only where a lipobox or i-spanin topology agrees. Previous spanin model:
  `spanin_model_v2_retired.pkl`.
  Earlier endolysin models are kept as `endolysin_model_v1_pool_retired.pkl` (the previous one) and
  `endolysin_model_v1_es_retired.pkl`; rename one to `endolysin_model.pkl` to roll back.

## How well it works, and how to read the score
Honest leave-one-genome-out estimates over 66 genomes and 180 annotated lysis genes (`scripts/40_logo_benchmark.py`,
`reports/logo_benchmark.json`, `reports/capacity_sweep.md`). Genome-scan AP with 95 % CI:

| gene | realistic (known family, new phage) | strict (never-seen family) | true gene in top 5 (real./strict) |
|---|---|---|---|
| holin | 0.754 (0.66–0.84) | 0.613 (0.49–0.74) | 98 % / 93 % |
| endolysin | 0.809 (0.73–0.88) | 0.614 (0.51–0.73) | 93 % / 87 % |
| spanin | 0.800 (0.67–0.94) | 0.568 (0.43–0.80) | 100 % / 97 % |

These replace earlier figures (holin 0.965 / 0.785, endolysin 0.843 / 0.729, spanin 0.834 / 0.729) measured on
13–19 genes per class; the larger panel puts every class lower.

- **Treat the output as a ranked shortlist.** The true gene is in the top five nearly always, but top-ranked only
  50–70 % of the time.
- **High confidence: read `high_conf`.** Cut-offs are per class because the endolysin model (trained without early
  stopping) gives more extreme probabilities. At its 0.9995 cut-off: precision 0.98 / recall 0.42 for known
  families, 0.91 / 0.22 for novel ones; at 0.95 its precision would be only 0.78. Holin and spanin keep 0.95.
- A **known-family** gene in a newly sequenced phage is usually in the top few; a **genuinely novel family** gets a
  shortlist, not a verdict. Triangulate with `--domains`, membrane topology (TMHMM/DeepTMHMM) and genomic context.
- Some real lysis genes carry **no recognisable domain anywhere** (the phage Serwaa endolysin matches nothing in 23
  InterPro databases), so a missing domain hit is not evidence against a call.
- Differences between models below about 0.05 AP are not measurable on this panel.
- The caller frequently flags a **second holin-fold gene** next to the annotated one — this is real dual-holin /
  holin-antiholin biology (see `reports/dual_holin_analysis.json`), not an error, but treat the second gene as a
  candidate to verify.

## Scaling / institutional deployment
- **Batch:** `scripts/30_scan_many.py --accessions list.txt` fetches and scans many genomes, aggregating recovery.
- **Galaxy (CPT):** `scripts/32_predict_lysis.py` is a clean single-command tool with FASTA in / TSV out, so it
  wraps directly as a Galaxy tool; ask and I will scaffold the `.xml` wrapper.
- **Reproducibility:** every data source has provenance (URL + SHA-256); `PROTOCOL.md` documents the full pipeline.
