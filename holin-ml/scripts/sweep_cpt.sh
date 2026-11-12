#!/bin/bash
# Score the SHIPPED recipes on the CPT-curated benchmark (scripts/44): each class with its own shipped settings, truth
# from CPT's curated lysis vocabulary, rank of each curated gene in its genome under both protocols. Resumable.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
common="--genbanks data/raw/cpt/genomes/*.gb --truth-file data/raw/cpt/truth.json --checkpoint .fitckpt_cpt"
for spec in "endolysin|--endolysin-positives data/processed/endolysin_positives_v1.json --early-stopping False|reports/cpt_endolysin.json" \
            "holin spanin|--early-stopping auto|reports/cpt_holin_spanin.json"; do
  IFS='|' read -r cls args out <<< "$spec"
  try=0
  while [ ! -f "$out" ] && [ $try -lt 10 ]; do
    try=$((try+1)); echo "=== $cls attempt $try ==="
    python3 scripts/40_logo_benchmark.py --classes $cls $args $common --out "$out" 2>&1 \
      | grep --line-buffered -E "WARNING|training positives|^  family|^  sequence|Traceback"
    [ -f "$out" ] && git add "$out" && git commit -q -m "CPT benchmark: $cls results

Committed as it lands; read together once all classes are in.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MT5C9SSAZE7xus2TLcG1hW" && git push -q origin claude/holin-ml
  done
done
echo CPT_DONE
