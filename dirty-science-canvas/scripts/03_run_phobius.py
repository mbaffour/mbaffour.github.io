"""Run Phobius (JSON API) on all planned batches. Resumable. Usage: python3 scripts/03_run_phobius.py [--org k1,k2]"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).parent))
from config import selected; import predictors
for k in selected(sys.argv): predictors.run_phobius(k)
