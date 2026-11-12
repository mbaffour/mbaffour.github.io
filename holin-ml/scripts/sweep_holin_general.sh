#!/bin/bash
# General holin signal: does the holin model generalise better to UNSEEN families if it cannot lean on the few large
# families (family-balanced weights), or if it sees only biophysical features? Shipped holin recipe otherwise.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
CPT="--genbanks data/raw/cpt/genomes/*.gb --truth-file data/raw/cpt/truth.json --checkpoint .fitckpt_cpt"
VAL="--genbanks data/raw/validated/genomes/*.gb --truth-file data/raw/validated/truth.json --checkpoint .fitckpt_validated"
for spec in "cluster|--pos-weight cluster" "sqrt|--pos-weight sqrt" "hand|--features hand" "hand_cluster|--features hand --pos-weight cluster"; do
  IFS='|' read -r tag args <<< "$spec"
  for set in cpt validated; do
    out=reports/${set}_holin_${tag}.json; T=$([ $set = cpt ] && echo "$CPT" || echo "$VAL"); try=0
    while [ ! -f "$out" ] && [ $try -lt 5 ]; do
      try=$((try+1)); echo "=== $out attempt $try ==="
      python3 scripts/40_logo_benchmark.py --classes holin --early-stopping auto $args $T --out "$out" 2>&1 \
        | grep --line-buffered -E "^  family|^  sequence|Traceback"
    done
  done
done
echo HOLIN_DONE
