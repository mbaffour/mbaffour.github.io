#!/bin/bash
# The validated benchmark again, as for a newly sequenced phage: GenBank annotation ignored, genes called from bare DNA
# with Pyrodigal, proven genes placed by sequence. Waits for the annotated-CDS run to finish so the two do not compete.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
until grep -q VALIDATED_DONE /tmp/claude-0/-home-user-mbaffour-github-io/ae54e614-94be-5086-856f-f7da55d4495a/scratchpad/validated.log 2>/dev/null; do sleep 20; done
common="--genbanks data/raw/validated/genomes/*.gb --truth-file data/raw/validated/truth.json --de-novo --checkpoint .fitckpt_validated_denovo"
for spec in "endolysin|--endolysin-positives data/processed/endolysin_positives_v1.json --early-stopping False|reports/validated_denovo_endolysin.json" \
            "holin spanin|--early-stopping auto|reports/validated_denovo_holin_spanin.json"; do
  IFS='|' read -r cls args out <<< "$spec"
  try=0
  while [ ! -f "$out" ] && [ $try -lt 10 ]; do
    try=$((try+1)); echo "=== $cls attempt $try ==="
    python3 scripts/40_logo_benchmark.py --classes $cls $args $common --out "$out" 2>&1 \
      | grep --line-buffered -E "WARNING|^[a-z]+: [0-9]+ training|^  family|^  sequence|Traceback"
  done
done
echo DENOVO_DONE
