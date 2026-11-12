#!/bin/bash
# Fill in context scores: every class scored in every genome (CPT and experimental sets), current models' recipes.
# Genomes that already have checkpoints (those with a curated gene of the class) are resumed, not recomputed.
cd /home/user/mbaffour.github.io/.worktrees/holin-ml/holin-ml || exit 1
EV=data/processed/endolysin_positives_v1_evidence.json; SP=data/processed/spanin_positives_signal.json
for set in cpt validated; do
  if [ $set = cpt ]; then T="--genbanks data/raw/cpt/genomes/*.gb --truth-file data/raw/cpt/truth.json --checkpoint .fitckpt_cpt"
  else T="--genbanks data/raw/validated/genomes/*.gb --truth-file data/raw/validated/truth.json --checkpoint .fitckpt_validated"; fi
  python3 scripts/40_logo_benchmark.py --classes endolysin --endolysin-positives $EV --early-stopping False --score-all $T --out /tmp/claude-0/-home-user-mbaffour-github-io/ae54e614-94be-5086-856f-f7da55d4495a/scratchpad/sa_${set}_e.json 2>&1 | grep -E "context scores|Traceback"
  python3 scripts/40_logo_benchmark.py --classes holin --early-stopping auto --score-all $T --out /tmp/claude-0/-home-user-mbaffour-github-io/ae54e614-94be-5086-856f-f7da55d4495a/scratchpad/sa_${set}_h.json 2>&1 | grep -E "context scores|Traceback"
  python3 scripts/40_logo_benchmark.py --classes spanin --spanin-positives $SP --early-stopping auto --score-all $T --out /tmp/claude-0/-home-user-mbaffour-github-io/ae54e614-94be-5086-856f-f7da55d4495a/scratchpad/sa_${set}_s.json 2>&1 | grep -E "context scores|Traceback"
done
echo SCOREALL_DONE
