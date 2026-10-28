#!/usr/bin/env python3
"""Write the episode's KiCad project files from 5-electronics/src/design.py.

  python3 -I tools/kicad/gen_schematic.py <episode>          writes <project>.kicad_sch, .kicad_pro, lib/
  python3 -I tools/kicad/gen_schematic.py <episode> --name   prints the project name only

Overwrites the generated files: once the schematic is edited by hand in KiCad, stop using this.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import use_episode  # noqa: E402

HW = use_episode(sys.argv)
import design  # noqa: E402,F401  (runs the part() calls)
import schkit  # noqa: E402

if "--name" in sys.argv:
    print(schkit.CFG["project"])
else:
    schkit.build(HW)
