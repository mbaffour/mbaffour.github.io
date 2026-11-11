#!/bin/bash
# Resumable capacity sweep. Two changes from sweep.sh after a container restart killed it
# mid-config-4 and lost ~2h of fitting:
#   1. skip any config whose report already exists, so a restart costs only the running config;
#   2. commit+push each report the moment it lands, so a restart cannot lose a finished config.
# Order is also changed: the v2 configs that answer the actual question (does more data help)
# run BEFORE the two expensive 1500/127 runs, so a restart loses the least valuable config.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
run () {  # label, positives, es, iter, leaves, lr
  if [ -f "reports/sweep_$1.json" ]; then echo "=== $1 (already done, skipped) ==="; return; fi
  echo "=== $1 ==="
  python3 scripts/40_logo_benchmark.py --classes endolysin \
    --endolysin-positives "$2" --early-stopping "$3" --max-iter "$4" \
    --max-leaf-nodes "$5" --learning-rate "$6" \
    --out "reports/sweep_$1.json" 2>&1 | grep -E "^estimator|^  family|^  sequence|Traceback"
  if [ -f "reports/sweep_$1.json" ]; then
    git add "reports/sweep_$1.json"
    git commit -q -m "capacity sweep: $1 ($3 ES, $4 iter, $5 leaves, lr $6)

Committed as the config lands so a container restart cannot lose it. Numbers are
read and interpreted together once the sweep completes, not per config.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MT5C9SSAZE7xus2TLcG1hW" \
      && git push -q origin claude/holin-ml 2>&1 | tail -1
    echo "--- committed $1 ---"
  else
    echo "--- $1 produced no report ---"
  fi
}
V1=data/processed/endolysin_positives_v1.json
V2=data/processed/endolysin_positives.json
run v1_base_es        "$V1" auto  400  31  0.06
run v1_noes_400_31    "$V1" False 400  31  0.06
run v1_noes_800_63    "$V1" False 800  63  0.04
run v2_base_es        "$V2" auto  400  31  0.06
run v2_noes_400_31    "$V2" False 400  31  0.06
run v2_noes_800_63    "$V2" False 800  63  0.04
run v1_noes_1500_127  "$V1" False 1500 127 0.03
run v2_noes_1500_127  "$V2" False 1500 127 0.03
echo SWEEP_DONE
