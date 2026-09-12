"""Run the NOVA AI conversation evaluation suite."""
import sys
sys.path.insert(0, ".")
from backend.evaluation.runner import run_all
run_all()
