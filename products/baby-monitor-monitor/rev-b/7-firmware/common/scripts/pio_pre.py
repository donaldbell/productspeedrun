# PlatformIO pre-build script (both projects): regenerate include/pins.h from this board's design.py.
# The board key is the PlatformIO project's folder name (sensor / receiver = 5-electronics/<key>/).
import os
import subprocess
import sys

Import("env")  # noqa: F821  (provided by PlatformIO / SCons)

project = env.subst("$PROJECT_DIR")  # noqa: F821
script = os.path.join(project, "..", "common", "scripts", "gen_pins.py")
subprocess.check_call([sys.executable, script, os.path.basename(os.path.normpath(project))])
