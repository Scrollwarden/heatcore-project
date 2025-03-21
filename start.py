import os
import sys
import subprocess

SCRIPT = "new_engine.main"

base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)
subprocess.run([sys.executable, "-m", SCRIPT])
