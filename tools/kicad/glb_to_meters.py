#!/usr/bin/env python3
"""Rescale a KiCad GLB to metres if it came out in millimetres (the web viewer expects metres).

Usage: python3 tools/kicad/glb_to_meters.py in.glb out.glb
"""
import sys

import trimesh

scene = trimesh.load(sys.argv[1])
size = max(scene.extents)
if size > 1.0:            # a 70 mm board in mm units: extents ~70
    scene.apply_scale(0.001)
print("board.glb extents (m):", [round(v, 4) for v in scene.extents])
scene.export(sys.argv[2])
