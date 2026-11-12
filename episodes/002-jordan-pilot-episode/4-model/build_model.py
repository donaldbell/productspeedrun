"""Gamer Companion enclosure -> SolidCraft CLI script (headless).

  python3 build_model.py [--upto N]   writes model_build.json (optionally only the first N stages)
  solidcraft-cli run model_build.json --save model.solidcraft --out model.step --out model.stl

Origin at the shell centre. x = robot's right (as you face it), y = face -> back (face at y = -25), z up.
"""
import json, math, os, sys

# --- Key dimensions (also written as named parameters) ----------------------------
W, D, H     = 68.0, 50.0, 50.0   # shell
CORNER_R    = 14.0               # front-view corners
EDGE_R      = 8.0                # front and back edge round
WALL        = 2.0
SPLIT_Y     = -12.0              # face cap / rear shell parting plane

LENS        = (44.0, 24.0, 8.0, 4.5)   # w, h, r, centre z
LENS_T      = 1.2
WINDOW      = (36.0, 18.0, 5.0)        # through-opening behind the lens
EYES        = [(-11.0, 6.0), (11.0, 6.0)]
PIR_XZ, PIR_HOLE_R = (0.0, 4.0), 5.2
MIC_XZ      = (0.0, -6.0)
SLOTS_Z     = (-14.0, -17.0, -20.0)

PCB_Y, PCB_T = -15.0, 1.6              # board front face, thickness
PCB         = (-27.0, -9.5, 27.0, 21.5, 5.0)   # rev 2: matched to the Stage 5 board (54 x 31 R5)
POSTS       = [(-21.0, -7.25), (21.0, -7.25), (21.0, 18.5), (-21.0, 18.5)]   # rev 2: H1..H3 + a rest under the antenna
SCREW_POSTS = POSTS[:3]

SPK_C, SPK_R, SPK_X = (5.0, 0.0), 14.0, (25.5, 30.5)   # (y, z) centre, radius, x span
RING_OR, RING_IR = 16.0, 13.0
BLOWER      = (-15.0, -7.0, -21.0, 15.0, 20.0, -11.0)  # x0 y0 z0 x1 y1 z1
FOOT_Z      = -33.0
USB_Z       = -6.2

cmds, stage_marks = [], []
def c(command, **params): cmds.append({"command": command, "params": params})
def stage(name): stage_marks.append((name, len(cmds)))
r4 = lambda v: round(v, 4)

def front_plane(y):   # sketch u = x, v = z; normal -y (towards the viewer)
    return {"origin": [0, y, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}
def back_plane(y):    # u = -x, v = z; normal +y
    return {"origin": [0, y, 0], "x_dir": [-1, 0, 0], "y_dir": [0, 0, 1]}
def side_plane(x, s):  # s = +1 right (u = y), -1 left (u = -y); normal = s * x
    return {"origin": [x, 0, 0], "x_dir": [0, s, 0], "y_dir": [0, 0, 1]}

for name, val, note in [("width", W, "shell x"), ("depth", D, "shell y"), ("height", H, "shell z"),
                        ("corner_r", CORNER_R, "front-view corner radius"), ("edge_r", EDGE_R, "front/back edge round"),
                        ("wall", WALL, "shell wall"), ("split_y", SPLIT_Y, "face cap / rear shell parting plane")]:
    c("parameters.add", name=name, expression=f"{val} mm", comment=note)

def edge_loop(y, w, h, r):
    cx, cz = w / 2 - r, h / 2 - r
    d = r / math.sqrt(2)
    pts = [[0, y, h / 2], [0, y, -h / 2], [w / 2, y, 0], [-w / 2, y, 0]]
    pts += [[sx * (cx + d), y, sz * (cz + d)] for sx in (-1, 1) for sz in (-1, 1)]
    return [[r4(v) for v in p] for p in pts]

# 1. Rounded block, hollowed by a smaller rounded cavity, split into face cap and rear shell
stage("shell")
c("sketch.create", plane=front_plane(D / 2), name="Shell Profile")
c("sketch.rectangle.rounded", p0=[-W / 2, -H / 2], p1=[W / 2, H / 2], radius="corner_r")
c("sketch.finish")
c("solid.extrude", distance="depth", operation="new", name="Shell Block", body_name="Rear Shell")
c("solid.fillet", edges=edge_loop(-D / 2, W, H, CORNER_R) + edge_loop(D / 2, W, H, CORNER_R), radius="edge_r", name="Edge Round")
iw, idp, ih = W - 2 * WALL, D - 2 * WALL, H - 2 * WALL
c("sketch.create", plane=front_plane(idp / 2), name="Cavity Profile")
c("sketch.rectangle.rounded", p0=[-iw / 2, -ih / 2], p1=[iw / 2, ih / 2], radius=f"corner_r - wall")
c("sketch.finish")
c("solid.extrude", distance=idp, operation="new", name="Cavity Block", body_name="Cavity")
c("solid.fillet", edges=edge_loop(-idp / 2, iw, ih, CORNER_R - WALL) + edge_loop(idp / 2, iw, ih, CORNER_R - WALL),
  radius=f"edge_r - wall", name="Cavity Round")
c("solid.combine", target="Rear Shell", tools=["Cavity"], operation="cut", name="Hollow")

# 2. Face: window, mic port, breeze slots ("mouth"), board posts; visor lens with eye inlays
stage("face")
lw, lh, lr, lz = LENS
ww, wh, wr = WINDOW
wz = 5.0
c("sketch.create", plane=front_plane(-D / 2 - 1), name="Face Openings")
c("sketch.rectangle.rounded", p0=[-ww / 2, wz - wh / 2], p1=[ww / 2, wz + wh / 2], radius=wr)
c("sketch.circle.center", center=list(MIC_XZ), radius=0.6)
for z in SLOTS_Z:
    c("sketch.slot.overall", p0=[-11, z], p1=[11, z], width=1.8)
c("sketch.finish")
c("solid.extrude", distance=7, direction="negative", operation="cut", targets=["Rear Shell"], name="Face Openings", profiles="all")
y_in = -(D / 2 - WALL) - 0.5                     # posts start 0.5 inside the front wall
c("sketch.create", plane=front_plane(y_in), name="Board Posts")
for px, pz in POSTS:
    c("sketch.circle.center", center=[px, pz], radius=2.6)
c("sketch.finish")
c("solid.extrude", distance=PCB_Y - y_in, direction="negative", operation="join", targets=["Rear Shell"], name="Board Posts", profiles="all")
c("sketch.create", plane=front_plane(PCB_Y), name="Post Pilot Holes")     # M2 self-tapping, Ø1.7 x 6
for px, pz in SCREW_POSTS:
    c("sketch.circle.center", center=[px, pz], radius=0.85)
c("sketch.finish")
c("solid.extrude", distance=6, operation="cut", targets=["Rear Shell"], name="Post Pilot Holes", profiles="all")

c("sketch.create", plane=front_plane(-D / 2), name="Visor Lens")
c("sketch.rectangle.rounded", p0=[-lw / 2, lz - lh / 2], p1=[lw / 2, lz + lh / 2], radius=lr)
c("sketch.circle.center", center=list(PIR_XZ), radius=PIR_HOLE_R)
c("sketch.finish")
c("solid.extrude", distance=LENS_T, operation="new", name="Visor Lens", body_name="Visor Lens", profiles=[{"point": [-lw / 2 + 3, lz]}])
yl = -D / 2 - LENS_T
def eye_sketch(name):
    c("sketch.create", plane=front_plane(yl), name=name)
    for ex, ez in EYES:
        c("sketch.slot.arc_three_point", start=[ex - 4, ez], through=[ex, ez + 4], end=[ex + 4, ez], width=2.0)
    c("sketch.finish")
eye_sketch("Eyes")
eye_pts = [{"point": [ex, ez + 4]} for ex, ez in EYES]
c("solid.extrude", distance=0.4, direction="negative", operation="cut", targets=["Visor Lens"], name="Eye Pockets", profiles=eye_pts)
eye_sketch("Eye Inlays")
for nm, p in zip(("Eye L", "Eye R"), eye_pts):
    c("solid.extrude", sketch="Eye Inlays", distance=0.4, direction="negative", operation="new", name=nm, body_name=nm, profiles=[p])

# PIR stand-in (AM312 class): Ø9.8 body from the board, domed lens through the visor hole
pr, py0, pyd = 4.9, -PCB_Y, -PCB_Y + 8.2      # u = -y
c("sketch.create", plane={"origin": [PIR_XZ[0], 0, PIR_XZ[1]], "x_dir": [0, -1, 0], "y_dir": [1, 0, 0]}, name="PIR Profile")
c("sketch.line", points=[[pyd + pr, 0], [py0, 0], [py0, pr], [pyd, pr]])
c("sketch.arc.three_point", start=[pyd, pr], through=[r4(pyd + pr * math.cos(math.pi / 4)), r4(pr * math.sin(math.pi / 4))], end=[pyd + pr, 0])
c("sketch.finish")
c("solid.revolve", axis="x", operation="new", name="AM312 PIR", body_name="PIR Dome")

EAR_ROOT = float(os.environ.get("EAR_ROOT", 20.0))   # roots run into the cavity so the join crosses the wall steeply
# 3. Ears: angular fins on the top, with green accent inlays on their fronts
stage("ears")
c("sketch.create", plane=front_plane(-3), name="Ears")
for s in (-1, 1):
    c("sketch.line", closed=True, points=[[s * 9, EAR_ROOT], [s * 25, EAR_ROOT], [s * 25, 23.3], [s * 24, 40], [s * 9, 23.3]])
c("sketch.finish")
c("solid.extrude", distance=10, direction="negative", operation="join", targets=["Rear Shell"], name="Ears", profiles="all")
c("sketch.create", plane=front_plane(-3), name="Ear Accents")
for s in (-1, 1):
    c("sketch.line", closed=True, points=[[s * 12.5, 25.5], [s * 22, 25.5], [s * 22.8, 35]])
c("sketch.finish")
for nm, s in (("Ear Accent L", -1), ("Ear Accent R", 1)):
    c("solid.extrude", sketch="Ear Accents", distance=0.6, operation="new", name=nm, body_name=nm, profiles=[{"point": [s * 19, 28]}])

# 4. Sides: speaker grille + retaining ring (right), vent holes (left), green accent rings in 1 mm grooves
stage("sides")
sy, sz = SPK_C
holes = []
for row in range(-4, 5):
    for col in range(-4, 5):
        u = col * 3.2 + (row % 2) * 1.6
        v = row * 3.2 * 0.866
        if u * u + v * v <= 10.5 ** 2:
            holes.append((u, v))
for s in (1, -1):
    c("sketch.create", plane=side_plane(s * (W / 2 + 2), s), name=f"Grille {'R' if s > 0 else 'L'}")
    for u, v in holes:
        c("sketch.circle.center", center=[r4(s * sy + u), r4(sz + v)], radius=0.8)
    c("sketch.finish")
    c("solid.extrude", distance=4, direction="negative", operation="cut", targets=["Rear Shell"], name=f"Grille {'R' if s > 0 else 'L'}", profiles="all")
c("sketch.create", plane=side_plane(SPK_X[1] - 1.0, 1), name="Speaker Ring")
c("sketch.circle.center", center=[sy, sz], radius=15.5)
c("sketch.circle.center", center=[sy, sz], radius=14.3)
c("sketch.finish")
c("solid.extrude", distance=3.0, operation="join", targets=["Rear Shell"], name="Speaker Ring", profiles=[{"point": [sy + 14.9, sz]}])
for nm, s in (("Ring R", 1), ("Ring L", -1)):
    c("sketch.create", plane=side_plane(s * (W / 2 - 1.0), s), name=nm)
    c("sketch.circle.center", center=[s * sy, sz], radius=RING_OR)
    c("sketch.circle.center", center=[s * sy, sz], radius=RING_IR)
    c("sketch.finish")
    c("solid.extrude", distance=2.5, operation="new", name=nm, body_name=nm, profiles=[{"point": [s * sy + (RING_OR + RING_IR) / 2, sz]}])
    c("solid.combine", target="Rear Shell", tools=[nm], operation="cut", keep_tools=True, name=f"{nm} Groove")

# 5. Underside: intake slots under the blower, blower stand-offs, feet with a front lip, clip knuckle
stage("underside")
c("sketch.create", plane="XY", offset=-H / 2 - 2, name="Intake Slots")
for x in (-8, -4, 0, 4, 8):
    c("sketch.slot.overall", p0=[x, -4], p1=[x, 16], width=2.2)
c("sketch.finish")
c("solid.extrude", distance=4.5, operation="cut", targets=["Rear Shell"], name="Intake Slots", profiles="all")
for x in (-12, 12):
    for y in (-4, 17):
        c("solid.cylinder", radius=2.0, height=2.5, base=[x, y, -H / 2 + WALL - 0.5], operation="join", targets=["Rear Shell"], name=f"Blower Standoff {x:+d},{y:+d}")
FOOT_TOP = -23.6
for s in (-1, 1):
    x0, x1 = sorted((s * 12, s * 21))
    for y0, y1 in ((-20, -13), (13, 20)):
        c("solid.box", length=x1 - x0, width=y1 - y0, height=FOOT_TOP - FOOT_Z, center=[(x0 + x1) / 2, (y0 + y1) / 2, (FOOT_TOP + FOOT_Z) / 2],
          operation="join", targets=["Rear Shell"], name=f"Foot {'L' if s < 0 else 'R'}{'F' if y0 < 0 else 'B'}")
    c("solid.box", length=x1 - x0, width=2.5, height=10, center=[(x0 + x1) / 2, -20.75, FOOT_Z - 5 + 5.0],
      operation="join", targets=["Rear Shell"], name=f"Bezel Lip {'L' if s < 0 else 'R'}")
c("solid.box", length=20, width=8, height=FOOT_TOP - (-29), center=[0, 17, (FOOT_TOP - 29) / 2], operation="join", targets=["Rear Shell"], name="Clip Knuckle")
for nm, s, y in (("Pad LF", -1, -16.5), ("Pad RF", 1, -16.5), ("Pad LB", -1, 16.5), ("Pad RB", 1, 16.5)):
    c("solid.box", length=8, width=6, height=1.0, center=[s * 16.5, y, FOOT_Z - 0.5], operation="new", name=nm, body_name=nm)

# 6. Back: USB-C opening, vent slots, ribs for the USB-C breakout
stage("back")
c("sketch.create", plane=back_plane(D / 2 + 1), name="Back Openings")
c("sketch.slot.overall", p0=[-3.0, USB_Z], p1=[3.0, USB_Z], width=3.8)
for z in (6, 10, 14):
    c("sketch.slot.overall", p0=[-10, z], p1=[10, z], width=1.8)
c("sketch.finish")
c("solid.extrude", distance=5, direction="negative", operation="cut", targets=["Rear Shell"], name="Back Openings", profiles="all")
for x in (-8, 8):
    c("solid.box", length=2, width=5.5, height=1.4, center=[x, 20.75 + 0.5, -10.1], operation="join", targets=["Rear Shell"], name=f"USB Rib {x:+d}")

# 7. Split into face cap and rear shell
stage("split")
c("solid.split_body", body="Rear Shell", plane={"origin": [0, SPLIT_Y, 0], "normal": [0, 1, 0]})
c("body.rename", body="Rear Shell (1)", name="Face Cap")   # the split keeps the +y side under the original name

# 8. Blower duct and rear clip (deployed)
stage("duct-clip")
c("solid.box", length=20, width=14.5, height=8, center=[0, -14.25, -16], operation="new", name="Blower Duct", body_name="Blower Duct")
c("solid.box", length=18, width=16, height=6, center=[0, -14.25, -16], operation="cut", targets=["Blower Duct"], name="Duct Channel")
c("solid.box", length=18, width=3, height=36, center=[0, 0, -18], operation="new", name="Rear Clip", body_name="Rear Clip")
c("solid.cylinder", radius=3, height=18, base=[-9, 0, 0], axis="X", operation="join", targets=["Rear Clip"], name="Clip Knuckle Barrel")
c("solid.box", length=16, width=1.7, height=5, center=[0, -2.2, -33.5], operation="join", targets=["Rear Clip"], name="Clip Pad")
c("solid.move", bodies=["Rear Clip"], axis=[1, 0, 0], angle="-10 deg", name="Clip Angle")
c("solid.move", bodies=["Rear Clip"], translate=[0, 24.2, -29], name="Clip Pivot")

# 9. Electronics stand-ins (fit check only; not in the GLB)
stage("electronics")
x0, z0, x1, z1, pr_ = PCB
c("sketch.create", plane=front_plane(PCB_Y), name="Main Board")
c("sketch.rectangle.rounded", p0=[x0, z0], p1=[x1, z1], radius=pr_)
c("sketch.finish")
c("solid.extrude", distance=PCB_T, direction="negative", operation="new", name="Main Board", body_name="Main Board")
yb = PCB_Y + PCB_T
c("solid.box", length=18, width=3.1, height=25.5, center=[-13, yb + 1.55, 7.9], operation="new", name="ESP32-S3-WROOM-1", body_name="ESP32-S3-WROOM-1")
for nm, (ex, ez) in zip(("LED L", "LED R"), EYES):
    c("solid.box", length=2, width=0.8, height=2, center=[ex, PCB_Y - 0.4, ez + 3.2], operation="new", name=nm, body_name=nm)
c("solid.box", length=3.5, width=1.0, height=2.65, center=[MIC_XZ[0], yb + 0.5, MIC_XZ[1]], operation="new", name="Mic", body_name="Mic")
c("solid.box", length=3, width=0.9, height=3, center=[16.5, yb + 0.45, 8], operation="new", name="MAX98357A", body_name="MAX98357A")
bx0, by0, bz0, bx1, by1, bz1 = BLOWER
c("solid.box", length=bx1 - bx0, width=by1 - by0, height=bz1 - bz0, center=[(bx0 + bx1) / 2, (by0 + by1) / 2, (bz0 + bz1) / 2],
  operation="new", name="Blower 3010", body_name="Blower")
c("solid.cylinder", radius=SPK_R, height=SPK_X[1] - SPK_X[0], base=[SPK_X[0], sy, sz], axis="X", operation="new", name="Speaker 28mm", body_name="Speaker")
c("solid.box", length=12, width=14, height=1.6, center=[0, 16, -8.6], operation="new", name="USB-C Breakout", body_name="USB-C Breakout")
c("solid.box", length=8.94, width=7.35, height=3.26, center=[0, 23 - 7.35 / 2, USB_Z + 0.05], operation="new", name="USB-C Receptacle", body_name="USB-C Receptacle")

# 10. Finish: charcoal shell, smoked visor, cyan eyes, neon-green accents
stage("colour")
COLOURS = {"Face Cap": "#2a2d33", "Rear Shell": "#2a2d33", "Visor Lens": "#121418", "Eye L": "#38d6ff", "Eye R": "#38d6ff",
           "PIR Dome": "#eef2f4", "Ring L": "#5ff23a", "Ring R": "#5ff23a", "Ear Accent L": "#5ff23a", "Ear Accent R": "#5ff23a",
           "Pad LF": "#111111", "Pad RF": "#111111", "Pad LB": "#111111", "Pad RB": "#111111", "Rear Clip": "#3b3f46",
           "Blower Duct": "#555a61",
           "Main Board": "#1d6b45", "ESP32-S3-WROOM-1": "#c0c4c8", "LED L": "#f4f4f4", "LED R": "#f4f4f4", "Mic": "#9aa0a6",
           "MAX98357A": "#111111", "Blower": "#1b1b1b", "Speaker": "#8a8f96", "USB-C Breakout": "#1a4fa0", "USB-C Receptacle": "#c0c4c8"}
for body, col in COLOURS.items():
    c("appearance.assign", bodies=[body], color=col)

upto = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else len(stage_marks)
end = stage_marks[upto][1] if upto < len(stage_marks) else len(cmds)
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"commands": cmds[:end]}, open(os.path.join(here, "model_build.json"), "w"), indent=1)
print("stages:", [s for s, _ in stage_marks[:upto]], f"({end} commands)")
