#!/bin/bash
# Score the SHIPPED recipes on the experimentally validated benchmark (scripts/43). Each class with its own shipped
# settings; a checkpoint directory of its own, because which genes count as truth changes what is removed from training.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
common="--genbanks data/raw/validated/genomes/*.gb --truth-file data/raw/validated/truth.json --checkpoint .fitckpt_validated"
for spec in "endolysin|--endolysin-positives data/processed/endolysin_positives_v1.json --early-stopping False|reports/validated_endolysin.json" \
            "holin spanin|--early-stopping auto|reports/validated_holin_spanin.json"; do
  IFS='|' read -r cls args out <<< "$spec"
  try=0
  while [ ! -f "$out" ] && [ $try -lt 10 ]; do
    try=$((try+1)); echo "=== $cls attempt $try ==="
    python3 scripts/40_logo_benchmark.py --classes $cls $args $common --out "$out" 2>&1 \
      | grep --line-buffered -E "WARNING|^[a-z]+: [0-9]+ training|^  family|^  sequence|Traceback"
  done
done
echo VALIDATED_DONE
