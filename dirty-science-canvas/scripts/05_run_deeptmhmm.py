"""Run DeepTMHMM (BioLib DTU/DeepTMHMM) on all planned batches, one job at a time. Resumable. Usage: python3 scripts/05_run_deeptmhmm.py [--org k1,k2]"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).parent))
from config import selected; import predictors
for k in selected(sys.argv): predictors.run_deeptmhmm(k)
