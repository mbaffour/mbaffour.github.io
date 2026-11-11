#!/bin/bash
# Restore-127 test: v2 with the 127 curated v1 positives that v2's holdout redraw swept up returned to
# training, then three count-matched controls returning 127 held-out Pfam-mined records instead.
# Early stopping off, 400/31 -- the configuration where the v1-v2 gap resolved. Resumable; each
# report is committed as it lands.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
for arm in restore127 ctrl127_s0 ctrl127_s1 ctrl127_s2; do
  pf="data/processed/endolysin_positives_v2_$arm.json"
  out="reports/restore_v2_$arm.json"
  try=0
  while [ ! -f "$out" ] && [ $try -lt 10 ]; do
    try=$((try+1)); echo "=== $arm attempt $try ==="
    python3 scripts/40_logo_benchmark.py --classes endolysin --endolysin-positives "$pf" \
      --early-stopping False --max-iter 400 --max-leaf-nodes 31 --learning-rate 0.06 \
      --out "$out" 2>&1 | grep -E "^endolysin:|^  family|^  sequence|Traceback"
  done
  if [ -f "$out" ]; then
    git add "$out" && git commit -q -m "restore test: $arm

Committed as it lands; read with the other arms and the paired tests.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MT5C9SSAZE7xus2TLcG1hW" && git push -q origin claude/holin-ml
    echo "--- committed $arm ---"
  else
    echo "--- $arm FAILED ---"
  fi
done
echo RESTORE_DONE
