#!/bin/bash
# Topology descriptors for a general holin signal (queued after sweep_holin_general.sh).
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
until grep -q HOLIN_DONE /tmp/claude-0/-home-user-mbaffour-github-io/ae54e614-94be-5086-856f-f7da55d4495a/scratchpad/holin.log; do sleep 30; done
CPT="--genbanks data/raw/cpt/genomes/*.gb --truth-file data/raw/cpt/truth.json --checkpoint .fitckpt_cpt"
VAL="--genbanks data/raw/validated/genomes/*.gb --truth-file data/raw/validated/truth.json --checkpoint .fitckpt_validated"
for spec in "handtopo|--features hand+topo" "bothtopo|--features both+topo" "bothtopo_cluster|--features both+topo --pos-weight cluster"; do
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
echo TOPO_DONE
