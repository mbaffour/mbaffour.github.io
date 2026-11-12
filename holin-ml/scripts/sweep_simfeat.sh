#!/bin/bash
# Similarity-feature test: the shipped endolysin configuration (v1 positives, current spanin negatives, early
# stopping off, 400/31) plus one feature -- max identity to the kept training positives. Resumable via .fitckpt.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
out=reports/sim_features_endolysin.json; try=0
while [ ! -f "$out" ] && [ $try -lt 10 ]; do
  try=$((try+1)); echo "=== attempt $try ==="
  python3 scripts/40_logo_benchmark.py --classes endolysin \
    --endolysin-positives data/processed/endolysin_positives_v1.json \
    --early-stopping False --max-iter 400 --max-leaf-nodes 31 --learning-rate 0.06 \
    --sim-features --out "$out" 2>&1 | grep -E "^checkpoints|similarity|^endolysin:|^  family|^  sequence|Traceback|Error"
done
echo SIM_DONE
