"""Backpack Defender enclosure -> SolidCraft CLI script (headless).

  python3 build_model.py [--upto N]   writes model_build.json (optionally only the first N stages)
  solidcraft-cli run model_build.json --save model.solidcraft --out model.step --out model.stl

Z up, device lying on its big flat side (as in a locker); origin at the bottom centre.
"""
import json, math, os, sys

# --- Key dimensions (also written as named parameters) ----------------------------
L, W, H     = 76.0, 51.0, 26.0   # 3 x 2 x 1 in, "deck of cards"
CORNER_R    = 12.0               # plan-view corner radius
TOP_R       = 7.0                # soft pebble top edge
BOT_R       = 1.0                # small bottom edge round, on the shell rim (must stay below WALL)
WALL        = 2.0
SPLIT_Z     = 12.0               # lid / base parting line

BTN_XY, BTN_R = (18.0, 0.0), 12.0     # big silence button
BTN_TOP     = 28.5
FLANGE_NOTE = "flange r = BTN_R + 1.5: clears the lid's inner top round"
PIR_XY, PIR_R = (-26.0, 13.0), 5.0    # AM312 dome
PCB_Z       = 14.5                    # PCB underside
PIEZO_XY    = (0.0, -14.5)            # BZ1 (KiCad), sound port on top
PCB_T       = 1.6

FACE_DEPTH  = 0.6
EYES        = [(-19.0, 5.0), (-3.0, 5.0)]
EYE_R, HILITE_R = 4.0, 1.3
CHEEKS      = [(-24.5, -2.0), (2.5, -2.0)]
CHEEK_R     = 2.8

cmds, stage_marks = [], []
def c(command, **params): cmds.append({"command": command, "params": params})
def stage(name): stage_marks.append((name, len(cmds)))
XY = lambda z: {"plane": "XY", "offset": z} if z else {"plane": "XY"}
z_top = H

for name, val, note in [("length", L, "long side"), ("width", W, "short side"), ("height", H, "thickness"),
                        ("wall", WALL, "shell wall"), ("top_round", TOP_R, "top edge round"), ("split_z", SPLIT_Z, "lid/base parting line")]:
    c("parameters.add", name=name, expression=f"{val} mm", comment=note)

# 1. Pebble block -> rounded edges -> hollow shell open at the bottom -> split into lid and base
stage("shell")
c("sketch.create", **XY(0), name="Footprint")
c("sketch.rectangle.rounded", p0=[-L / 2, -W / 2], p1=[L / 2, W / 2], radius=CORNER_R)
c("sketch.finish")
c("solid.extrude", distance="height", operation="new", name="Pebble", body_name="Housing")
def loop(z):
    cx, cy = L / 2 - CORNER_R, W / 2 - CORNER_R; d = CORNER_R / math.sqrt(2)
    pts = [[0, W / 2, z], [0, -W / 2, z], [L / 2, 0, z], [-L / 2, 0, z]]
    pts += [[sx * (cx + d), sy * (cy + d), z] for sx in (-1, 1) for sy in (-1, 1)]
    return [[round(v, 4) for v in p] for p in pts]
c("solid.fillet", edges=loop(H), radius="top_round", name="Top Round")
c("solid.shell", faces=[[0, 0, 0]], thickness="wall", name="Shell")
c("solid.fillet", edges=loop(0), radius=BOT_R, name="Bottom Round")   # after the shell: only the outer rim edge
c("solid.split_body", body="Housing", plane={"origin": [0, 0, SPLIT_Z], "normal": [0, 0, 1]})
c("body.rename", body="Housing", name="Lid")          # the split keeps the upper half as "Housing"
c("body.rename", body="Housing (1)", name="Base")

# 2. Lid details: button and PIR openings, kawaii face pockets, speaker grille
stage("lid")
c("sketch.create", **XY(z_top - 4), name="Lid Openings")
c("sketch.circle.center", center=list(BTN_XY), radius=BTN_R + 0.3)
c("sketch.circle.center", center=list(PIR_XY), radius=PIR_R + 0.2)
c("sketch.finish")
c("solid.extrude", distance=8, operation="cut", targets=["Lid"], name="Lid Openings", profiles="all")

def face_sketch(name):
    c("sketch.create", **XY(z_top), name=name)
    for ex, ey in EYES:
        c("sketch.circle.center", center=[ex, ey], radius=EYE_R)
        c("sketch.circle.center", center=[ex + 1.4, ey + 1.4], radius=HILITE_R)
    c("sketch.slot.arc_three_point", start=[-15.5, -4.0], through=[-11.0, -7.6], end=[-6.5, -4.0], width=1.4)
    for cx_, cy_ in CHEEKS:
        c("sketch.circle.center", center=[cx_, cy_], radius=CHEEK_R)
    c("sketch.finish")
face_pts = [{"point": [ex - 2.0, ey - 1.5]} for ex, ey in EYES] + [{"point": [-11.0, -6.9]}] + [{"point": [cx_, cy_]} for cx_, cy_ in CHEEKS]
face_sketch("Face")
c("solid.extrude", distance=FACE_DEPTH, direction="negative", operation="cut", targets=["Lid"], name="Face Pockets", profiles=face_pts)

c("sketch.create", **XY(z_top), name="Sound Holes")         # PS1240's port faces up: 7 holes right above it
c("sketch.circle.center", center=list(PIEZO_XY), radius=0.8)
for k in range(6):
    a = math.radians(60 * k + 30)
    c("sketch.circle.center", center=[round(PIEZO_XY[0] + 3.0 * math.cos(a), 4), round(PIEZO_XY[1] + 3.0 * math.sin(a), 4)], radius=0.8)
c("sketch.finish")
c("solid.extrude", distance=3, direction="negative", operation="cut", targets=["Lid"], name="Sound Holes", profiles="all")

c("sketch.create", plane={"origin": [0, -W / 2, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Speaker Grille")
for x in (-4.0, 0.0, 4.0):
    c("sketch.slot.overall", p0=[x, 14.8], p1=[x, 18.6], width=2.0)
c("sketch.finish")
c("solid.extrude", distance=4, direction="negative", operation="cut", targets=["Lid"], name="Speaker Grille", profiles="all")

# 3. Base details: charm loop on the left end for a keyring / carabiner / zip tie
stage("base")
c("sketch.create", **XY(0), name="Charm Loop")
c("sketch.slot.overall", p0=[-L / 2 - 10.0, 0], p1=[-L / 2 + 2.0, 0], width=11)   # sticks out 10 mm, runs 2 mm into the wall
c("sketch.circle.center", center=[-L / 2 - 4.5, 0], radius=2.2)
c("sketch.finish")
c("solid.extrude", distance=5, operation="join", targets=["Base"], name="Charm Loop", profiles=[{"point": [-L / 2 - 8.5, 0]}])

# 4. Bottom plate (PCB posts, battery opening) and battery door
stage("plate")
ix, iy, ir = L / 2 - WALL - 0.15, W / 2 - WALL - 0.15, CORNER_R - WALL - 0.15
DOOR = (54.0, 27.0, 3.0, (0.0, -9.5))     # w, h, corner r, centre
dw, dh, dr, (dx, dy) = DOOR
c("sketch.create", **XY(0), name="Bottom Plate")
c("sketch.rectangle.rounded", p0=[-ix, -iy], p1=[ix, iy], radius=ir)
c("sketch.rectangle.rounded", p0=[dx - dw / 2, dy - dh / 2], p1=[dx + dw / 2, dy + dh / 2], radius=dr)
c("sketch.finish")
c("solid.extrude", distance="wall", operation="new", name="Bottom Plate", body_name="Bottom Plate", profiles=[{"point": [0, iy - 3]}])
POSTS = [(sx * 31.0, sy * 17.0) for sx in (-1, 1) for sy in (-1, 1)]
c("sketch.create", **XY(WALL), name="PCB Posts")
for px, py in POSTS:
    c("sketch.circle.center", center=[px, py], radius=2.5)
c("sketch.finish")
c("solid.extrude", distance=PCB_Z - WALL, operation="join", targets=["Bottom Plate"], name="PCB Posts", profiles="all")
c("sketch.create", **XY(PCB_Z), name="Post Pilot Holes")      # M2 self-tapping screws through the board's H1-H4 (Ø2.2)
for px, py in POSTS:
    c("sketch.circle.center", center=[px, py], radius=0.85)
c("sketch.finish")
c("solid.extrude", distance=6, direction="negative", operation="cut", targets=["Bottom Plate"], name="Post Pilot Holes", profiles="all")
c("sketch.create", **XY(0), name="Battery Door")
g = 0.2
c("sketch.rectangle.rounded", p0=[dx - dw / 2 + g, dy - dh / 2 + g], p1=[dx + dw / 2 - g, dy + dh / 2 - g], radius=dr - g)
c("sketch.finish")
c("solid.extrude", distance="wall", operation="new", name="Battery Door", body_name="Battery Door")
c("solid.box", length=12, width=3, height=1.2, center=[dx, dy - dh / 2 + 3.0, 0.6], operation="cut", targets=["Battery Door"], name="Door Thumb Notch")

# 5. Big silence button: captive flange under the lid, pill-dome top, presses a 12x12x7 tact switch
stage("button")
bx, by = BTN_XY
c("sketch.create", plane={"origin": [bx, by, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Button Profile")
c("sketch.line", closed=True, points=[[0, 23.2], [BTN_R + 1.5, 23.2], [BTN_R + 1.5, 23.9], [BTN_R, 23.9], [BTN_R, BTN_TOP], [0, BTN_TOP]])
c("sketch.finish")
c("solid.revolve", axis="y", operation="new", name="Silence Button", body_name="Silence Button")
c("solid.fillet", edges=[[bx + BTN_R, by, BTN_TOP]], radius=4, name="Button Dome")
c("solid.cylinder", radius=4, height=0.5, base=[bx, by, 23.1], operation="cut", targets=["Silence Button"], name="Plunger Pocket")  # 0.2 clear of SW1

# 6. Face inlays (second colour, flush in the pockets)
stage("face")
face_sketch("Face Inlays")
for i, p in enumerate(face_pts):
    nm = ["Eye L", "Eye R", "Smile", "Cheek L", "Cheek R"][i]
    c("solid.extrude", sketch="Face Inlays", distance=FACE_DEPTH, direction="negative", operation="new", name=nm, body_name=nm, profiles=[p])

# 7. Electronics stand-ins, positions from 5-electronics/backpack-defender.kicad_pcb (fit check only; not in the GLB)
stage("electronics")
z_pcb_top = PCB_Z + PCB_T
c("sketch.create", **XY(PCB_Z), name="PCB")
c("sketch.rectangle.rounded", p0=[-35, -22.5], p1=[35, 22.5], radius=9)
c("sketch.finish")
c("solid.extrude", distance=PCB_T, operation="new", name="PCB", body_name="PCB")
c("solid.box", length=52, width=25, height=12, center=[0, -10, WALL + 6], operation="new", body_name="2xAAA Holder", name="2xAAA Holder")
c("solid.box", length=18, width=20, height=3.2, center=[-8.5, 12.1, z_pcb_top + 1.6], operation="new", body_name="ESP32-C3-WROOM-02", name="U2 ESP32-C3-WROOM-02")
# SW1 12x12x7.3: a 3.8 mm body with a Ø7 round plunger to 7.3 (two bodies: a stand-in needs no join)
c("solid.box", length=12, width=12, height=3.8, center=[bx, by, z_pcb_top + 1.9], operation="new", body_name="Tact Switch", name="SW1 body")
c("solid.cylinder", radius=3.5, height=3.5, base=[bx, by, z_pcb_top + 3.8], operation="new", body_name="Switch Plunger", name="SW1 plunger")
c("solid.cylinder", radius=6.1, height=6.5, base=[PIEZO_XY[0], PIEZO_XY[1], z_pcb_top], operation="new", body_name="Piezo", name="BZ1 PS1240")
c("solid.box", length=3, width=3, height=0.8, center=[12, -12.5, z_pcb_top + 0.4], operation="new", body_name="MAX98357A", name="U3 MAX98357A")
# AM312: Ø10 body with a domed lens, one revolved profile (a sphere joined to a same-radius cylinder only touches it)
zd = z_top - 0.5
c("sketch.create", plane={"origin": [PIR_XY[0], PIR_XY[1], 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="PIR Profile")
c("sketch.line", points=[[0, zd + PIR_R], [0, z_pcb_top], [PIR_R, z_pcb_top], [PIR_R, zd]])
c("sketch.arc.three_point", start=[PIR_R, zd], through=[round(PIR_R * math.cos(math.pi / 4), 4), round(zd + PIR_R * math.sin(math.pi / 4), 4)], end=[0, zd + PIR_R])
c("sketch.finish")
c("solid.revolve", axis="y", operation="new", name="AM312 PIR", body_name="PIR Dome")

# 8. Kawaii pastel finish (enclosure) and readable colours for the stand-ins
stage("colour")
COLOURS = {"Lid": "#8fe0c9", "Base": "#ffe08a", "Bottom Plate": "#cdbdf2", "Battery Door": "#cdbdf2",
           "Silence Button": "#ff8f87", "Eye L": "#3b3552", "Eye R": "#3b3552", "Smile": "#3b3552",
           "Cheek L": "#ffadc4", "Cheek R": "#ffadc4", "PIR Dome": "#b39ddb",
           "PCB": "#2e7d4f", "2xAAA Holder": "#3a3a3a", "ESP32-C3-WROOM-02": "#c0c4c8", "Tact Switch": "#222222", "Switch Plunger": "#555555",
           "Piezo": "#c9a227", "MAX98357A": "#111111"}
for body, col in COLOURS.items():
    c("appearance.assign", bodies=[body], color=col)

upto = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else len(stage_marks)
end = stage_marks[upto][1] if upto < len(stage_marks) else len(cmds)
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"commands": cmds[:end]}, open(os.path.join(here, "model_build.json"), "w"), indent=1)
print("stages:", [s for s, _ in stage_marks[:upto]], f"({end} commands)")
