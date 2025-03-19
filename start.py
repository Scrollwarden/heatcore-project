import os
import sys
import subprocess

SCRIPT = "intel_arti.cube_v2.cube_ui"

base_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(base_dir)
subprocess.run([sys.executable, "-m", SCRIPT])