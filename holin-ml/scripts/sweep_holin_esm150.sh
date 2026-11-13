#!/bin/bash
# Holin with ESM-2 150M embeddings in place of 35M; shipped recipe otherwise. CPT and experimental sets.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
M=facebook/esm2_t30_150M_UR50D
CPT="--genbanks data/raw/cpt/genomes/*.gb --truth-file data/raw/cpt/truth.json --checkpoint .fitckpt_cpt"
VAL="--genbanks data/raw/validated/genomes/*.gb --truth-file data/raw/validated/truth.json --checkpoint .fitckpt_validated"
for set in cpt validated; do
  out=reports/${set}_holin_esm150.json; T=$([ $set = cpt ] && echo "$CPT" || echo "$VAL"); try=0
  while [ ! -f "$out" ] && [ $try -lt 10 ]; do
    try=$((try+1)); echo "=== $out attempt $try ==="
    python3 scripts/40_logo_benchmark.py --classes holin --early-stopping auto --esm-model $M $T --out "$out" 2>&1 \
      | grep --line-buffered -E "genome features|features in|^  family|^  sequence|Traceback"
    [ -f "$out" ] && git add "$out" && git commit -q -m "holin with ESM-2 150M: $(basename $out)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MT5C9SSAZE7xus2TLcG1hW" && git push -q origin claude/holin-ml
  done
done
echo ESM150_DONE
