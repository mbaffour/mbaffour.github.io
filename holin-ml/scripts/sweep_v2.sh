#!/bin/bash
# Run the three v2 capacity configs. Each python invocation is retried until its report exists;
# checkpointing (.fitckpt) makes a retry resume rather than restart, so a container restart or a
# killed process costs only the genome in flight. Each report is committed the moment it lands.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
V2=data/processed/endolysin_positives.json
run () {  # label es iter leaves lr
  local label=$1 es=$2 it=$3 lv=$4 lr=$5 out="reports/sweep_$label.json" try=0
  if [ -f "$out" ]; then echo "=== $label already done ==="; return; fi
  while [ ! -f "$out" ] && [ $try -lt 12 ]; do
    try=$((try+1)); echo "=== $label attempt $try ==="
    python3 scripts/40_logo_benchmark.py --classes endolysin --endolysin-positives "$V2" \
      --early-stopping "$es" --max-iter "$it" --max-leaf-nodes "$lv" --learning-rate "$lr" \
      --out "$out" 2>&1 | grep -E "^  family|^  sequence|^endolysin:|Traceback"
  done
  if [ -f "$out" ]; then
    git add "$out" && git commit -q -m "capacity sweep: $label ($es ES, $it iter, $lv leaves, lr $lr)

Committed as it lands. Interpretation waits until the v1/v2 pairs are all in.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MT5C9SSAZE7xus2TLcG1hW" && git push -q origin claude/holin-ml
    echo "--- committed $label ---"
  else
    echo "--- $label FAILED after $try attempts ---"
  fi
}
run v2_base_es     auto  400 31 0.06
run v2_noes_400_31 False 400 31 0.06
run v2_noes_800_63 False 800 63 0.04
echo V2_DONE
