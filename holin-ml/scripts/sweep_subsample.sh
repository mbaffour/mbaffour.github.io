#!/bin/bash
# Count-vs-composition test for the v2 endolysin regression. v2's training positives are cut to v1's
# exact count (1,337) with v2's source mix preserved, at the configuration where the v1-v2 gap
# resolved (early stopping off, 400 iter, 31 leaves, lr 0.06). Three seeds, because a single draw
# can be lucky or unlucky. Resumable through .fitckpt; each report is committed as it lands.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
V2=data/processed/endolysin_positives.json
for seed in 0 1 2; do
  out="reports/subsample_v2_n1337_s$seed.json"
  try=0
  while [ ! -f "$out" ] && [ $try -lt 10 ]; do
    try=$((try+1)); echo "=== seed $seed attempt $try ==="
    python3 scripts/40_logo_benchmark.py --classes endolysin --endolysin-positives "$V2" \
      --early-stopping False --max-iter 400 --max-leaf-nodes 31 --learning-rate 0.06 \
      --pos-subsample 1337 --pos-subsample-seed "$seed" --pos-subsample-strata source \
      --out "$out" 2>&1 | grep -E "^checkpoints|subsampled|^  family|^  sequence|Traceback"
  done
  if [ -f "$out" ]; then
    git add "$out" && git commit -q -m "subsample test: v2 cut to 1337 positives, seed $seed

Committed as it lands; read together with the other seeds and the paired tests.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MT5C9SSAZE7xus2TLcG1hW" && git push -q origin claude/holin-ml
    echo "--- committed seed $seed ---"
  else
    echo "--- seed $seed FAILED ---"
  fi
done
echo SUBSAMPLE_DONE
