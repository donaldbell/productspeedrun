# PlatformIO pre-build script: regenerate include/pins.h from the board's design.py before every build.
import os
import subprocess
import sys

Import("env")  # noqa: F821  (provided by PlatformIO / SCons)

script = os.path.join(env.subst("$PROJECT_DIR"), "scripts", "gen_pins.py")  # noqa: F821
subprocess.check_call([sys.executable, script])
