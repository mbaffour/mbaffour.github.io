#!/bin/bash
# Evidence-only training: endolysin without the annotation-named "pool" tier; spanin without the name-labelled TrEMBL
# and pool tiers. Same recipes as shipped otherwise. Scored on the CPT-curated and experimental benchmarks.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
EV=data/processed/endolysin_positives_v1_evidence.json; SV=data/processed/spanin_positives_evidence.json
run () {  # out, args...
  local out=$1; shift; local try=0
  while [ ! -f "$out" ] && [ $try -lt 10 ]; do
    try=$((try+1)); echo "=== $out attempt $try ==="
    python3 scripts/40_logo_benchmark.py "$@" --out "$out" 2>&1 | grep --line-buffered -E "training positives|^  family|^  sequence|Traceback"
  done
  [ -f "$out" ] && git add "$out" && git commit -q -m "evidence-only training: $(basename $out .json)

Committed as it lands; compared with the shipped recipe once all runs are in.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01MT5C9SSAZE7xus2TLcG1hW" && git push -q origin claude/holin-ml
}
CPT="--genbanks data/raw/cpt/genomes/*.gb --truth-file data/raw/cpt/truth.json --checkpoint .fitckpt_cpt"
VAL="--genbanks data/raw/validated/genomes/*.gb --truth-file data/raw/validated/truth.json --checkpoint .fitckpt_validated"
run reports/cpt_endolysin_evidence.json   --classes endolysin --endolysin-positives $EV --early-stopping False $CPT
run reports/cpt_spanin_evidence.json      --classes spanin --spanin-positives $SV --early-stopping auto $CPT
run reports/validated_endolysin_evidence.json --classes endolysin --endolysin-positives $EV --early-stopping False $VAL
run reports/validated_spanin_evidence.json    --classes spanin --spanin-positives $SV --early-stopping auto $VAL
echo EVIDENCE_DONE
