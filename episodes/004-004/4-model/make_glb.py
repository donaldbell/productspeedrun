"""model.glb for the web viewer: the visible bodies exported from model.solidcraft, coloured, in metres, Y-up.

  python3 make_glb.py        (needs solidcraft-cli and trimesh; run after build_model.py and the saved build)

Colours come from model_colors.json (written by build_model.py). Electronics stand-ins and the cells are left out:
they're hidden inside the bar.
"""
import json, math, os, struct, subprocess, tempfile
import numpy as np, trimesh
from trimesh.visual.material import PBRMaterial

here = os.path.dirname(os.path.abspath(__file__))
fit = json.load(open(os.path.join(here, "..", "fit.json")))
HIDDEN = set(fit["model"]["stand_ins"]) | {"Cell 1", "Cell 2"}
COLORS = {b: c for b, c in json.load(open(os.path.join(here, "model_colors.json"))).items() if b not in HIDDEN}


def srgb_to_linear(hexc):
    out = []
    for k in (1, 3, 5):
        c = int(hexc[k:k + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def look(name):
    """(metallic, roughness, emissive?) per body family: painted 'brass' reads as satin metal in the viewer."""
    if name in ("Deck", "Finial L", "Finial L (2)", "Dome Collar", "Port Boss", "Port Cap", "LED Bezel", "View Bezel",
                "USB Plug") or name.startswith(("Rivet", "Gear Hub")):
        return 0.75, 0.38, False
    if name == "Oval Bezel":
        return 0.9, 0.25, False
    if name.startswith(("Glow", "Lamp")):
        return 0.0, 0.5, True
    if name in ("View Glass", "Oval Lens"):
        return 0.0, 0.08, False
    if name == "Dome":
        return 0.0, 0.08, False
    return 0.0, 0.6, False


names = list(COLORS)
with tempfile.TemporaryDirectory() as tmp:
    cmds = [{"command": "file.export", "params": {"path": os.path.join(tmp, f"{i}.stl"), "bodies": [b]}}
            for i, b in enumerate(names)]
    script = os.path.join(tmp, "export.json")
    json.dump({"commands": cmds}, open(script, "w"))
    subprocess.run(["solidcraft-cli", "run", script, "--in", os.path.join(here, "model.solidcraft"), "--quiet"],
                   check=True, timeout=1800)
    # mm -> m, Z-up (CAD) -> Y-up (glTF)
    xf = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]) @ np.diag([0.001, 0.001, 0.001, 1])
    scene = trimesh.Scene()
    for i, name in enumerate(names):
        m = trimesh.load(os.path.join(tmp, f"{i}.stl"), force="mesh")
        m.apply_transform(xf)
        metal, rough, _ = look(name)
        m.visual = trimesh.visual.TextureVisuals(material=PBRMaterial(
            name=name, baseColorFactor=srgb_to_linear(COLORS[name]) + [1.0], metallicFactor=metal, roughnessFactor=rough))
        scene.add_geometry(m, node_name=name, geom_name=name)
    scene.export(os.path.join(here, "model.glb"))

# trimesh rounds the factors to 8 bits: write the exact linear floats (and the LED glow) back into the glTF JSON chunk
path = os.path.join(here, "model.glb")
b = open(path, "rb").read()
n = struct.unpack("<I", b[12:16])[0]
gltf = json.loads(b[20:20 + n])
for mat in gltf["materials"]:
    lin = [round(v, 6) for v in srgb_to_linear(COLORS[mat["name"]])]
    mat["pbrMetallicRoughness"]["baseColorFactor"] = lin + [1.0]
    if mat["name"] == "Dome":   # smoky amber, see-through (hosts' choice: the APDS-9960 needs a clear IR path)
        mat["pbrMetallicRoughness"]["baseColorFactor"][3] = 0.78
        mat["alphaMode"] = "BLEND"
    if look(mat["name"])[2]:
        mat["emissiveFactor"] = [round(v * 0.8, 6) for v in lin]
js = json.dumps(gltf, separators=(",", ":")).encode()
js += b" " * (-len(js) % 4)
rest = b[20 + n:]
out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + len(rest)) + struct.pack("<II", len(js), 0x4E4F534A) + js + rest
open(path, "wb").write(out)
g = trimesh.load(path)
print("model.glb:", os.path.getsize(path) // 1024, "KB,", len(g.geometry), "parts, extents (m):", np.round(g.extents, 4))
