#!/bin/bash
# Spanin middle path: name-labelled TrEMBL spanins kept only where an independent sequence signal agrees (o-spanin
# lipobox in the first 35 aa, or a single N-terminal TM segment). Scored like the other candidates.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
SP=data/processed/spanin_positives_signal.json
for spec in "reports/cpt_spanin_signal.json|--genbanks data/raw/cpt/genomes/*.gb --truth-file data/raw/cpt/truth.json --checkpoint .fitckpt_cpt" \
            "reports/validated_spanin_signal.json|--genbanks data/raw/validated/genomes/*.gb --truth-file data/raw/validated/truth.json --checkpoint .fitckpt_validated"; do
  IFS='|' read -r out args <<< "$spec"; try=0
  while [ ! -f "$out" ] && [ $try -lt 10 ]; do
    try=$((try+1)); echo "=== $out attempt $try ==="
    python3 scripts/40_logo_benchmark.py --classes spanin --spanin-positives $SP --early-stopping auto $args --out "$out" 2>&1 \
      | grep --line-buffered -E "training positives|^  family|^  sequence|Traceback"
  done
done
echo SIGNAL_DONE
