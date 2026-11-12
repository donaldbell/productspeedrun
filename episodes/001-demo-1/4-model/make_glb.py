"""model.glb for the web viewer: each visible part exported from model_build.json, coloured, in metres, Y-up.

  python3 make_glb.py        (needs solidcraft-cli and trimesh; run after build_model.py)
"""
import json, math, os, subprocess, tempfile
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
VISIBLE = {"Lid": "#8fe0c9", "Base": "#ffe08a", "Bottom Plate": "#cdbdf2", "Battery Door": "#cdbdf2",
           "Silence Button": "#ff8f87", "Eye L": "#3b3552", "Eye R": "#3b3552", "Smile": "#3b3552",
           "Cheek L": "#ffadc4", "Cheek R": "#ffadc4", "PIR Dome": "#b39ddb"}

with tempfile.TemporaryDirectory() as tmp:
    cmds = json.load(open(os.path.join(here, "model_build.json")))["commands"]
    cmds += [{"command": "file.export", "params": {"path": os.path.join(tmp, f"{i}.stl"), "bodies": [b]}}
             for i, b in enumerate(VISIBLE)]
    script = os.path.join(tmp, "export.json")
    json.dump({"commands": cmds}, open(script, "w"))
    subprocess.run(["solidcraft-cli", "run", script, "--quiet"], check=True, timeout=900)

    # mm -> m, and Z-up (CAD) -> Y-up (glTF)
    xf = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]) @ np.diag([0.001, 0.001, 0.001, 1])
    scene = trimesh.Scene()
    for i, (name, hexc) in enumerate(VISIBLE.items()):
        m = trimesh.load(os.path.join(tmp, f"{i}.stl"), force="mesh")
        m.apply_transform(xf)
        m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
            name=name, baseColorFactor=srgb_to_linear(hexc) + [1.0], metallicFactor=0.0, roughnessFactor=0.25 if name == "PIR Dome" else 0.5))
        scene.add_geometry(m, node_name=name, geom_name=name)
    scene.export(os.path.join(here, "model.glb"))

# trimesh stores the factor as 8-bit; write the exact linear floats back into the glTF JSON chunk
import struct
path = os.path.join(here, "model.glb")
b = open(path, "rb").read()
n = struct.unpack("<I", b[12:16])[0]
gltf = json.loads(b[20:20 + n])
for mat in gltf["materials"]:
    mat["pbrMetallicRoughness"]["baseColorFactor"] = [round(v, 6) for v in srgb_to_linear(VISIBLE[mat["name"]])] + [1.0]
js = json.dumps(gltf, separators=(",", ":")).encode()
js += b" " * (-len(js) % 4)
rest = b[20 + n:]
out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + len(rest)) + struct.pack("<II", len(js), 0x4E4F534A) + js + rest
open(path, "wb").write(out)

g = trimesh.load(os.path.join(here, "model.glb"))
print("model.glb:", os.path.getsize(os.path.join(here, "model.glb")) // 1024, "KB,", len(g.geometry), "parts, extents (m):", np.round(g.extents, 4))
