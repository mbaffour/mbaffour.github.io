# Galaxy wrapper: Phage lysis gene caller

Wraps `scripts/32_predict_lysis.py` (holin / endolysin / spanin caller) as a Galaxy tool
(`predict_lysis.xml`, id `phage_lysis_caller`). Intended for a Center for Phage Technology (CPT) Galaxy instance.
Inputs are protein FASTA, nucleotide FASTA (Pyrodigal gene calling) or GenBank; the NCBI `--acc` mode is deliberately
not exposed (Galaxy tools take uploaded files, not network fetches).

## Admin install

1. **Check out holin-ml** on the Galaxy server (and cluster nodes) at a path readable by the job user.
2. **Set `LYSIS_CALLER_HOME`** to that checkout path (the directory containing `scripts/` and `models/`). The tool
   command calls `python3 "${LYSIS_CALLER_HOME}/scripts/32_predict_lysis.py"`. Set it in `job_conf` for the
   destination, e.g. `<env id="LYSIS_CALLER_HOME">/opt/holin-ml</env>`.
3. **Model files must exist** in `$LYSIS_CALLER_HOME/models/`: `holin_model_curated.pkl`, `endolysin_model.pkl`,
   `spanin_model.pkl`. They are not conda packages.
4. **Conda dependencies** are resolved from the `<requirements>` block. **scikit-learn must be exactly 1.9.1**: the models
   are pickled estimators and will fail or misbehave under another version. Other pins follow DEPLOY.md
   (python 3.13, numpy 2.5, pytorch 2.15 CPU, transformers 5.22, pyrodigal 3.7, biopython). Verify those builds exist
   on your channels (conda-forge/bioconda) before installing; adjust the pins only if the models still load.
5. **ESM-2 weights** `facebook/esm2_t12_35M_UR50D` (~130 MB) are not conda-installable.
   - Online instances: allow outbound HTTPS to `huggingface.co` on first run (cached afterwards under
     `$LYSIS_CALLER_HOME/models/esm_cache`, which must be writable by the job user, or set `HF_HOME`).
   - Offline instances: pre-populate the cache by running the script once on a networked machine, then copy it to
     `models/esm_cache` (or point `HF_HOME` at a populated cache) and set `HF_HUB_OFFLINE=1` in the job environment.
6. CPU is sufficient (35M-parameter model).

## Tests

`test-data/sample_proteins.faa` holds five N4 (NC_008720.1) proteins: holin (gp62), endolysin (gp61), Rz-like spanin
(gp60), portal protein (gp59) and gp63. The test checks the TSV header, 12 columns and 6 lines. Run with
`planemo test galaxy/predict_lysis.xml` once the environment above is configured. The tool has not been run through
Galaxy yet.

## Citation

Manuscript in preparation; add the citation to `predict_lysis.xml` when available.
