# PlatformIO pre-build script: regenerate include/pins.h (from the board's design.py) and src/sound_data.h
# (from sounds/*.mid) before every build.
import os
import subprocess
import sys

Import("env")  # noqa: F821  (provided by PlatformIO / SCons)

for script in ("gen_pins.py", "gen_sounds.py"):
    subprocess.check_call([sys.executable, os.path.join(env.subst("$PROJECT_DIR"), "scripts", script)])  # noqa: F821
