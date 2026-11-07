"""Rev B: model.glb for the web viewer: each visible part exported from model.solidcraft, coloured, in metres, Y-up.

  python3 make_glb.py                 (needs solidcraft-cli and trimesh; run after build_model.py)
  python3 make_glb.py --stl-dir DIR   (use "<body name>.stl" files already exported, e.g. from an MCP session that has
                                       the design open: re-opening the Rev B design to export takes ~30 min)
"""
import json, math, os, struct, subprocess, tempfile
import numpy as np, trimesh
from trimesh.visual.material import PBRMaterial

def srgb_to_linear(hexc):
    """glTF baseColorFactor is linear; the palette is sRGB hex."""
    out = []
    for k in (1, 3, 5):
        c = int(hexc[k:k + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out

here = os.path.dirname(os.path.abspath(__file__))
VISIBLE = {"Sensor Upper": "#eef0f5", "Sensor Swoosh": "#b4acdc", "Sensor Trim": "#c8ccd6", "Sensor Base": "#8f93a6", "VHB Pad": "#d9d9d9",
           "Sensor Grille": "#2c2b35", "Sensor Button": "#d9dce6", "Sensor Light Pipe": "#7dff63",
           "Watch Case": "#e6e9f0", "Watch Back": "#b9b3d9", "Watch Lens": "#d86cff", "Lens Face": "#f3cdfc", "Link Pipe": "#7dff63",
           "Band": "#6e58a8",
           "Charge Contact +": "#d8b04a", "Charge Contact -": "#d8b04a", "Magnet A": "#4a4a55", "Magnet B": "#4a4a55",
           "Switch Slider": "#9d8fe0", "Grille Collar": "#c8ccd6"}
# PBR tweaks: pearl/NCVM shells a little glossy, lens and pipes glowing, band matte fabric
ROUGH = {"Grille Collar": 0.2, "Sensor Trim": 0.2, "Lens Face": 0.3, "Sensor Upper": 0.3, "Watch Case": 0.25, "Watch Lens": 0.15, "Band": 0.9, "VHB Pad": 0.8, "Sensor Grille": 0.6}
METAL = {"Grille Collar": 0.9, "Sensor Trim": 0.8, "Watch Case": 0.35, "Sensor Upper": 0.15, "Charge Contact +": 1.0, "Charge Contact -": 1.0, "Magnet A": 0.8, "Magnet B": 0.8}
EMISSIVE = {"Watch Lens": "#8a2bb0", "Lens Face": "#6a3a80", "Sensor Light Pipe": "#3fbf2a", "Link Pipe": "#3fbf2a"}

import sys
stl_dir = sys.argv[sys.argv.index("--stl-dir") + 1] if "--stl-dir" in sys.argv else None
with tempfile.TemporaryDirectory() as tmp:
    if stl_dir:
        for i, b in enumerate(VISIBLE):
            os.symlink(os.path.join(os.path.abspath(stl_dir), b + ".stl"), os.path.join(tmp, f"{i}.stl"))
    else:
        cmds = [{"command": "file.export", "params": {"path": os.path.join(tmp, f"{i}.stl"), "bodies": [b]}}
                 for i, b in enumerate(VISIBLE)]
        script = os.path.join(tmp, "export.json")
        json.dump({"commands": cmds}, open(script, "w"))
        subprocess.run(["solidcraft-cli", "run", script, "--in", os.path.join(here, "model.solidcraft"), "--quiet"], check=True, timeout=7200)   # exports from the saved design

    # mm -> m, and Z-up (CAD) -> Y-up (glTF)
    xf = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]) @ np.diag([0.001, 0.001, 0.001, 1])
    scene = trimesh.Scene()
    for i, (name, hexc) in enumerate(VISIBLE.items()):
        m = trimesh.load(os.path.join(tmp, f"{i}.stl"), force="mesh")
        m.apply_transform(xf)
        m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
            name=name, baseColorFactor=srgb_to_linear(hexc) + [1.0], metallicFactor=METAL.get(name, 0.0),
            roughnessFactor=ROUGH.get(name, 0.5)))
        scene.add_geometry(m, node_name=name, geom_name=name)
    scene.export(os.path.join(here, "model.glb"))

# trimesh stores the factor as 8-bit; write the exact linear floats (and emissive glows) back into the glTF JSON chunk
path = os.path.join(here, "model.glb")
b = open(path, "rb").read()
n = struct.unpack("<I", b[12:16])[0]
gltf = json.loads(b[20:20 + n])
for mat in gltf["materials"]:
    mat["pbrMetallicRoughness"]["baseColorFactor"] = [round(v, 6) for v in srgb_to_linear(VISIBLE[mat["name"]])] + [1.0]
    if mat["name"] in EMISSIVE:
        mat["emissiveFactor"] = [round(v, 6) for v in srgb_to_linear(EMISSIVE[mat["name"]])]
js = json.dumps(gltf, separators=(",", ":")).encode()
js += b" " * (-len(js) % 4)
rest = b[20 + n:]
out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + len(rest)) + struct.pack("<II", len(js), 0x4E4F534A) + js + rest
open(path, "wb").write(out)

g = trimesh.load(path)
print("model.glb:", os.path.getsize(path) // 1024, "KB,", len(g.geometry), "parts, extents (m):", np.round(g.extents, 4))
