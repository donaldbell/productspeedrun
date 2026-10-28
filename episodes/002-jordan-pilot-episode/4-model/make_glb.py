"""model.glb for the web viewer: each visible part exported from model.solidcraft, coloured, in metres, Y-up.

  python3 make_glb.py        (needs solidcraft-cli and trimesh; run after the build has saved model.solidcraft)
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
# name: (sRGB colour, metallic, roughness)
VISIBLE = {
    "Face Cap": ("#2a2d33", 0.0, 0.55), "Rear Shell": ("#2a2d33", 0.0, 0.55),
    "Visor Lens": ("#121418", 0.0, 0.08), "Eye L": ("#38d6ff", 0.0, 0.3), "Eye R": ("#38d6ff", 0.0, 0.3),
    "PIR Dome": ("#eef2f4", 0.0, 0.35),
    "Ring L": ("#5ff23a", 0.0, 0.35), "Ring R": ("#5ff23a", 0.0, 0.35),
    "Ear Accent L": ("#5ff23a", 0.0, 0.35), "Ear Accent R": ("#5ff23a", 0.0, 0.35),
    "Pad LF": ("#111111", 0.0, 0.9), "Pad RF": ("#111111", 0.0, 0.9), "Pad LB": ("#111111", 0.0, 0.9), "Pad RB": ("#111111", 0.0, 0.9),
    "Rear Clip": ("#3b3f46", 0.0, 0.6), "Blower Duct": ("#555a61", 0.0, 0.6),
}
# glow for the eyes so they read as lit in the viewer
EMISSIVE = {"Eye L": "#38d6ff", "Eye R": "#38d6ff"}

with tempfile.TemporaryDirectory() as tmp:
    cmds = [{"command": "file.export", "params": {"path": os.path.join(tmp, f"{i}.stl"), "bodies": [b]}}
            for i, b in enumerate(VISIBLE)]
    script = os.path.join(tmp, "export.json")
    json.dump({"commands": cmds}, open(script, "w"))
    subprocess.run(["solidcraft-cli", "run", script, "--in", os.path.join(here, "model.solidcraft"), "--quiet"],
                   check=True, timeout=900)

    # mm -> m, and Z-up (CAD) -> Y-up (glTF); CAD -y is the face, which becomes glTF +z (towards the default camera)
    xf = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]) @ np.diag([0.001, 0.001, 0.001, 1])
    scene = trimesh.Scene()
    for i, (name, (hexc, metal, rough)) in enumerate(VISIBLE.items()):
        m = trimesh.load(os.path.join(tmp, f"{i}.stl"), force="mesh")
        m.apply_transform(xf)
        m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
            name=name, baseColorFactor=srgb_to_linear(hexc) + [1.0], metallicFactor=metal, roughnessFactor=rough))
        scene.add_geometry(m, node_name=name, geom_name=name)
    scene.export(os.path.join(here, "model.glb"))

# trimesh stores the factor as 8-bit; write the exact linear floats (and the eye glow) back into the glTF JSON chunk
path = os.path.join(here, "model.glb")
b = open(path, "rb").read()
n = struct.unpack("<I", b[12:16])[0]
gltf = json.loads(b[20:20 + n])
for mat in gltf["materials"]:
    mat["pbrMetallicRoughness"]["baseColorFactor"] = [round(v, 6) for v in srgb_to_linear(VISIBLE[mat["name"]][0])] + [1.0]
    if mat["name"] in EMISSIVE:
        mat["emissiveFactor"] = [round(v, 6) for v in srgb_to_linear(EMISSIVE[mat["name"]])]
js = json.dumps(gltf, separators=(",", ":")).encode()
js += b" " * (-len(js) % 4)
rest = b[20 + n:]
out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + len(rest)) + struct.pack("<II", len(js), 0x4E4F534A) + js + rest
open(path, "wb").write(out)

g = trimesh.load(path)
print("model.glb:", os.path.getsize(path) // 1024, "KB,", len(g.geometry), "parts, extents (m):", np.round(g.extents, 4))
