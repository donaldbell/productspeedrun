"""model.glb for the web viewer: the visible bodies of model.solidcraft, one mesh per colour, in metres, Y-up.

  python3 make_glb.py        (needs solidcraft-cli and trimesh; run after build_model.py and the saved build)

Colours come from model_colors.json (written by build_model.py). The board stand-ins and the cells are left out:
they're inside the closed pod. The ~570 bodies are grouped by colour (louvres, each pixel colour, ...) so the viewer
loads ~16 meshes, not hundreds. Pixel tiles glow (emissive).
"""
import json, math, os, struct, subprocess, sys, tempfile
from collections import defaultdict
import numpy as np, trimesh
from trimesh.visual.material import PBRMaterial

here = os.path.dirname(os.path.abspath(__file__))
design = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "model.solidcraft")
fit = json.load(open(os.path.join(here, "..", "fit.json")))
HIDDEN = set(fit["model"]["stand_ins"]) | {"Cell A", "Cell B"}
COLORS = {b: c for b, c in json.load(open(os.path.join(here, "model_colors.json"))).items() if b not in HIDDEN}
NAMES = {"#0d1220": "Screen", "#040406": "Louvres", "#7d735c": "Piping", "#26282d": "Pod", "#2e3035": "Pod Lid",
         "#ff7a1a": "Tiki Orange", "#ffc23a": "Amber", "#ff3b1f": "Tiki Red", "#39e64a": "Palm Green",
         "#ff3fd2": "Hibiscus", "#b44dff": "Violet", "#3b7bff": "Blue", "#29d3ff": "Cyan", "#fff1c9": "Warm White"}
GLOW = {"#ff7a1a", "#ffc23a", "#ff3b1f", "#39e64a", "#ff3fd2", "#b44dff", "#3b7bff", "#29d3ff", "#fff1c9"}

def srgb_to_linear(hexc):
    out = []
    for k in (1, 3, 5):
        c = int(hexc[k:k + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out

def look(col):
    """(metallic, roughness) per family."""
    if col in GLOW:
        return 0.0, 0.35
    if col == "#0d1220":
        return 0.0, 0.25          # glossy screen
    if col == "#040406":
        return 0.0, 0.7
    return 0.0, 0.85              # fabric, soft-touch TPU

groups = defaultdict(list)
for body, col in COLORS.items():
    groups[col].append(body)
cols = list(groups)
with tempfile.TemporaryDirectory() as tmp:
    cmds = [{"command": "file.export", "params": {"path": os.path.join(tmp, f"{i}.stl"), "bodies": groups[col]}}
            for i, col in enumerate(cols)]
    script = os.path.join(tmp, "export.json")
    json.dump({"commands": cmds}, open(script, "w"))
    subprocess.run(["solidcraft-cli", "run", script, "--in", design, "--quiet"], check=True, timeout=3600)
    # mm -> m, Z-up (CAD) -> Y-up (glTF)
    xf = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]) @ np.diag([0.001, 0.001, 0.001, 1])
    scene = trimesh.Scene()
    for i, col in enumerate(cols):
        name = NAMES.get(col, col)
        m = trimesh.load(os.path.join(tmp, f"{i}.stl"), force="mesh")
        m.apply_transform(xf)
        metal, rough = look(col)
        m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
            name=col, baseColorFactor=srgb_to_linear(col) + [1.0], metallicFactor=metal, roughnessFactor=rough))
        scene.add_geometry(m, node_name=name, geom_name=name)
    scene.export(os.path.join(here, "model.glb"))

# trimesh rounds the factors to 8 bits: write the exact linear floats (and the pixel glow) back into the glTF JSON
path = os.path.join(here, "model.glb")
b = open(path, "rb").read()
n = struct.unpack("<I", b[12:16])[0]
gltf = json.loads(b[20:20 + n])
for mat in gltf["materials"]:
    col = mat["name"]
    lin = [round(v, 6) for v in srgb_to_linear(col)]
    mat["pbrMetallicRoughness"]["baseColorFactor"] = lin + [1.0]
    if col in GLOW:
        mat["emissiveFactor"] = [round(v * 0.9, 6) for v in lin]
    mat["name"] = NAMES.get(col, col)
js = json.dumps(gltf, separators=(",", ":")).encode()
js += b" " * (-len(js) % 4)
rest = b[20 + n:]
out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + len(rest)) + struct.pack("<II", len(js), 0x4E4F534A) + js + rest
open(path, "wb").write(out)
g = trimesh.load(path)
print(f"model.glb: {len(g.geometry)} meshes, {os.path.getsize(path) / 1e6:.1f} MB, extents (m) {np.round(g.extents, 3)}")
