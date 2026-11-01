"""Backpack Defender Rev B enclosure -> SolidCraft CLI script (headless).

  python3 build_model.py [--upto N]   writes model_build.json (optionally only the first N stages)
  solidcraft-cli run model_build.json --save model.solidcraft --out model.step --out model.stl

Z up, device lying on its big flat side (as in a locker); origin at the bottom centre.
The board's place, outline, posts and everything that lines up with it come from ../fit.json
(tools/fit/fitlib.py), so a Stage 5 change there rebuilds into the model.

Rev B (see ../REV.md): 26 -> 22.5 mm thick, triangular carabiner loop, shadow-line reveal at the
parting line, speaker grille instead of piezo holes, white light pipes in the eye highlights,
power slide switch on the right end, white "PROPERTY OF:" name plate on the back.
"""
import json, math, os, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "..", "..", "..", "tools", "fit"))
from fitlib import load_fit  # noqa: E402
FIT = load_fit(here)

# --- Key dimensions (also written as named parameters) ----------------------------
L, W, H     = 76.0, 51.0, 22.5   # Rev A: 26 thick. Same plan view.
CORNER_R    = 12.0               # plan-view corner radius
TOP_R       = 7.5                # soft pebble top edge (a third of the height: rounder than Rev A)
BOT_R       = 1.0                # small bottom edge round, on the shell rim (must stay below WALL)
WALL        = 2.0
SPLIT_Z     = 14.0               # lid / base parting line (Rev A 12: the power switch slot now sits in the base)
REVEAL      = (0.6, 0.8)         # shadow-line groove at the bottom of the lid: depth, height

# --- From fit.json (board mm -> enclosure mm) ---------------------------------------
PCB_T       = FIT.thickness
Z_PCB_TOP   = FIT.origin[2]
PCB_Z       = Z_PCB_TOP - PCB_T                       # board underside = post tops
xy = lambda name: tuple(round(v, 4) for v in FIT.to_enclosure(FIT.feature(name))[:2])
BTN_XY      = xy("button")
PIR_XY      = xy("pir")
SPK_XY      = xy("speaker")
LED_XY      = [xy("eye_led_l"), xy("eye_led_r")]
PSW_XY      = xy("power_switch")
MOD_XY      = xy("module")
AMP_XY      = xy("amp")
POSTS       = [tuple(FIT.to_enclosure(h)[:2]) for h in FIT.holes + FIT.rests]
PIR_CUT_R   = FIT.features["pir"]["size"][0] / 2

BTN_R       = 12.0                    # big silence button
BTN_TOP     = H + 2.5
FLANGE_R    = BTN_R + 0.9             # captive flange: must clear the lid's inner top round (r TOP_R - WALL)
SW_H        = 4.3                     # SW1 12 x 12 x 4.3 low-profile (Rev A 7.3)
PIR_R       = 5.0                     # AM312 dome
PIR_LEN     = 14.4                    # AM312 base to lens apex
PIR_APEX    = H + 3.5                 # dome stands 3.5 proud of the lid
PIR_BASE    = PIR_APEX - PIR_LEN      # below the board: it passes through the board cutout
SPK_R, SPK_T, SPK_FOAM = 10.0, 4.0, 0.3   # Ø20 x 4 micro speaker on a foam pad
CELL_R, CELL_L = 5.25, 44.5               # AAA
CELL_Y      = [-15.25, -4.25]

FACE_DEPTH  = 0.6
EYES        = [(-19.0, 5.0), (-3.0, 5.0)]
EYE_R, HILITE_R = 4.0, 1.3            # the highlight dots are now light pipes over LED_XY
PIPE_R, PIPE_HOLE_R, PIPE_BOSS_R = 1.28, 1.35, 2.2
CHEEKS      = [(-24.5, -2.0), (2.5, -2.0)]
CHEEK_R     = 2.8
FONT        = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
INLAY       = 0.4                     # name plate inlay depth (pad print in production)

for (ex, ey), (lx, ly) in zip(EYES, LED_XY):   # the LEDs must sit under the highlight dots
    assert abs(ex + 1.4 - lx) < 0.01 and abs(ey + 1.4 - ly) < 0.01, "fit.json eye LED moved off the eye highlight"

cmds, stage_marks = [], []
def c(command, **params): cmds.append({"command": command, "params": params})
def stage(name): stage_marks.append((name, len(cmds)))
XY = lambda z: {"plane": "XY", "offset": z} if z else {"plane": "XY"}
z_top = H
z_in = H - WALL                       # lid inside, top

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

# 2. Lid details: button and PIR openings, eye light-pipe bosses, face pockets, speaker grille, reveal
stage("lid")
c("sketch.create", **XY(z_top - 4), name="Lid Openings")
c("sketch.circle.center", center=list(BTN_XY), radius=BTN_R + 0.3)
c("sketch.circle.center", center=list(PIR_XY), radius=PIR_R + 0.2)
c("sketch.finish")
c("solid.extrude", distance=8, operation="cut", targets=["Lid"], name="Lid Openings", profiles="all")

PIPE_BOT = Z_PCB_TOP + 1.0            # light pipe ends 1 mm above the board (0603 LED is 0.8 tall)
c("sketch.create", **XY(z_in + 0.3), name="Light Pipe Bosses")   # start 0.3 inside the lid so the join overlaps
for p in LED_XY:
    c("sketch.circle.center", center=list(p), radius=PIPE_BOSS_R)
c("sketch.finish")
c("solid.extrude", distance=round(z_in + 0.3 - (PIPE_BOT + 0.4), 4), direction="negative", operation="join", targets=["Lid"],
  name="Light Pipe Bosses", profiles="all")

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

c("sketch.create", **XY(z_top + 0.1), name="Light Pipe Holes")   # straight through the highlight islands and the bosses
for p in LED_XY:
    c("sketch.circle.center", center=list(p), radius=PIPE_HOLE_R)
c("sketch.finish")
c("solid.extrude", distance=round(z_top + 0.1 - PIPE_BOT + 0.2, 4), direction="negative", operation="cut", targets=["Lid"],
  name="Light Pipe Holes", profiles="all")

# speaker grille: a little flower of holes (1 + 6 + 12) right over the speaker
GRILLE = [(0.0, 0.0)] + [(2.5 * math.cos(math.radians(60 * k)), 2.5 * math.sin(math.radians(60 * k))) for k in range(6)] \
       + [(4.9 * math.cos(math.radians(30 * k + 15)), 4.9 * math.sin(math.radians(30 * k + 15))) for k in range(12)]
c("sketch.create", **XY(z_top), name="Speaker Grille")
for gx, gy in GRILLE:
    c("sketch.circle.center", center=[round(SPK_XY[0] + gx, 4), round(SPK_XY[1] + gy, 4)], radius=0.65)
c("sketch.finish")
c("solid.extrude", distance=3, direction="negative", operation="cut", targets=["Lid"], name="Speaker Grille", profiles="all")

# shadow-line reveal: the lid's bottom edge steps in, so the parting line reads as a deliberate groove
rd, rh = REVEAL
c("sketch.create", **XY(SPLIT_Z), name="Reveal")
c("sketch.rectangle.rounded", p0=[-L / 2 - 3, -W / 2 - 3], p1=[L / 2 + 3, W / 2 + 3], radius=CORNER_R + 3)
c("sketch.rectangle.rounded", p0=[-L / 2 + rd, -W / 2 + rd], p1=[L / 2 - rd, W / 2 - rd], radius=CORNER_R - rd)
c("sketch.finish")
c("solid.extrude", distance=rh, operation="cut", targets=["Lid"], name="Reveal", profiles=[{"point": [0, W / 2 + 1.5]}])

# 3. Base details: triangular carabiner loop on the left end, power-switch slot on the right end
stage("base")
LOOP_IN_R, LOOP_WEB, LOOP_T = 6.0, 4.5, 6.0     # Ø12 circle fits in the hole; 4.5 webs; 6 thick
hx = -L / 2 - 2.5                                # hole's flat side, 2.5 off the end wall
inc = (hx - LOOP_IN_R, 0.0)                      # in-centre of the (equilateral) hole
def tri(r):                                      # equilateral triangle, apex to -x, in-radius r about inc
    return [[inc[0] + r, inc[1] + r * math.sqrt(3)], [inc[0] - 2 * r, inc[1]], [inc[0] + r, inc[1] - r * math.sqrt(3)]]
hole = tri(LOOP_IN_R)
outer = tri(LOOP_IN_R + LOOP_WEB)
xe = -L / 2 + 1.0                                # outer triangle is cut off 1 mm into the end wall
ye = (xe - outer[1][0]) / (outer[0][0] - outer[1][0]) * outer[0][1]
c("sketch.create", **XY(0), name="Carabiner Loop")
c("sketch.line", closed=True, points=[[round(xe, 4), round(ye, 4)], [round(v, 4) for v in outer[1]], [round(xe, 4), round(-ye, 4)]])
c("sketch.line", closed=True, points=[[round(v, 4) for v in p] for p in hole])
c("sketch.finish")
c("solid.extrude", distance=LOOP_T, operation="new", name="Carabiner Loop", body_name="Loop",
  profiles=[{"point": [round(outer[1][0] + 3, 4), 0]}])
c("solid.fillet", body="Loop", edges=[[round(outer[1][0], 4), 0, LOOP_T / 2]], radius=6, name="Loop Tip Round")
c("solid.fillet", body="Loop", edges=[[round(p[0], 4), round(p[1], 4), LOOP_T / 2] for p in hole], radius=2.5, name="Loop Hole Rounds")
# soften the loop's top and bottom edges (outer outline and hole), so it reads as a moulded part, not a plate
lo_mid = [[(outer[1][0] + xe) / 2, s * ye / 2] for s in (1, -1)] + [[outer[1][0] + 6.0, 0]]
ho_mid = [[(hole[i][0] + hole[(i + 1) % 3][0]) / 2, (hole[i][1] + hole[(i + 1) % 3][1]) / 2] for i in range(3)]
c("solid.fillet", body="Loop", edges=[[round(x, 4), round(y, 4), z] for x, y in lo_mid + ho_mid for z in (LOOP_T, 0.0)], radius=1.2, name="Loop Edge Rounds")
c("solid.combine", target="Base", tools=["Loop"], operation="join", name="Join Loop")

# power switch: a slot through the right end, inside a shallow thumb pocket
PSW_Z = PCB_Z - 1.8                               # actuator centre: middle of a 3.6 mm switch body hung under the board
py0 = PSW_XY[1]
c("sketch.create", plane={"origin": [L / 2 - 0.6, 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="Switch Pocket")
c("sketch.rectangle.rounded", p0=[py0 - 5.0, PSW_Z - 1.9], p1=[py0 + 5.0, PSW_Z + 1.9], radius=1.8)
c("sketch.finish")
c("solid.extrude", distance=2, operation="cut", targets=["Base"], name="Switch Pocket")
c("sketch.create", plane={"origin": [L / 2 - 3.5, 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="Switch Slot")
c("sketch.rectangle.rounded", p0=[py0 - 3.5, PSW_Z - 1.2], p1=[py0 + 3.5, PSW_Z + 1.2], radius=1.1)
c("sketch.finish")
c("solid.extrude", distance=5, operation="cut", targets=["Base"], name="Switch Slot")

# 4. Bottom plate (PCB posts, PIR boss, battery opening), battery door, name plate on the back
stage("plate")
ix, iy, ir = L / 2 - WALL - 0.15, W / 2 - WALL - 0.15, CORNER_R - WALL - 0.15
DOOR = (54.0, 27.0, 3.0, (0.0, -9.5))     # w, h, corner r, centre
dw, dh, dr, (dx, dy) = DOOR
c("sketch.create", **XY(0), name="Bottom Plate")
c("sketch.rectangle.rounded", p0=[-ix, -iy], p1=[ix, iy], radius=ir)
c("sketch.rectangle.rounded", p0=[dx - dw / 2, dy - dh / 2], p1=[dx + dw / 2, dy + dh / 2], radius=dr)
c("sketch.finish")
c("solid.extrude", distance="wall", operation="new", name="Bottom Plate", body_name="Bottom Plate", profiles=[{"point": [0, iy - 3]}])
c("sketch.create", **XY(WALL), name="PCB Posts")
for px, py in POSTS:
    c("sketch.circle.center", center=[px, py], radius=2.5)
c("sketch.finish")
c("solid.extrude", distance=round(PCB_Z - WALL, 4), operation="join", targets=["Bottom Plate"], name="PCB Posts", profiles="all")
c("sketch.create", **XY(WALL), name="PIR Boss")             # a tube the AM312 sits on; its legs drop inside it
c("sketch.circle.center", center=list(PIR_XY), radius=4.6)
c("sketch.circle.center", center=list(PIR_XY), radius=3.4)
c("sketch.finish")
c("solid.extrude", distance=round(PIR_BASE - WALL, 4), operation="join", targets=["Bottom Plate"], name="PIR Boss",
  profiles=[{"point": [PIR_XY[0] + 4.0, PIR_XY[1]]}])
c("sketch.create", **XY(PCB_Z), name="Post Pilot Holes")      # M2 self-tapping screws through the board's H1-H4
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

# name plate: drawn looking at the back (sketch x = world -x), so it reads when the pebble is turned over like a page.
# "PROPERTY OF:" on the plate, a big white write-on panel on the battery door for a dark marker.
FIELD = (46.0, 16.5, 3.0, 0.0, -7.0)      # w, h, r, centre (sketch x, y = world y)
fw, fh, fr, fx, fy = FIELD
def name_sketch(name, text=True, field=True):
    c("sketch.create", plane={"origin": [0, 0, 0], "x_dir": [-1, 0, 0], "y_dir": [0, 1, 0]}, name=name)
    if text:
        c("sketch.text", text="PROPERTY OF:", at=[0, 8.6], height=4.2, align="center", font=FONT, letter_spacing=0.3)
    if field:
        c("sketch.rectangle.rounded", p0=[fx - fw / 2, fy - fh / 2], p1=[fx + fw / 2, fy + fh / 2], radius=fr)
    c("sketch.finish")
name_sketch("Name Plate")
c("solid.extrude", distance=INLAY, direction="negative", operation="cut", targets=["Bottom Plate", "Battery Door"], name="Name Plate Pockets", profiles="all")
name_sketch("Name Field Inlay", text=False)      # separate sketches: the extrude has no "all but this one" profile choice
c("solid.extrude", distance=INLAY, direction="negative", operation="new", name="Name Field", body_name="Name Field", profiles="all")
name_sketch("Name Text Inlay", field=False)
c("solid.extrude", distance=INLAY, direction="negative", operation="new", name="Name Text", body_name="Name Text", profiles="all")

# 5. Big silence button: captive flange under the lid, pill-dome top, sits 0.3 above SW1's plunger
stage("button")
bx, by = BTN_XY
fl_top = z_in - 0.1
fl_bot = fl_top - 0.7
c("sketch.create", plane={"origin": [bx, by, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Button Profile")
c("sketch.line", closed=True, points=[[0, fl_bot], [FLANGE_R, fl_bot], [FLANGE_R, fl_top], [BTN_R, fl_top], [BTN_R, BTN_TOP], [0, BTN_TOP]])
c("sketch.finish")
c("solid.revolve", axis="y", operation="new", name="Silence Button", body_name="Silence Button")
c("solid.fillet", edges=[[bx + BTN_R, by, BTN_TOP]], radius=4, name="Button Dome")

# 6. Face inlays (second colour, flush in the pockets) and the eye light pipes (white, translucent)
stage("face")
face_sketch("Face Inlays")
for i, p in enumerate(face_pts):
    nm = ["Eye L", "Eye R", "Smile", "Cheek L", "Cheek R"][i]
    c("solid.extrude", sketch="Face Inlays", distance=FACE_DEPTH, direction="negative", operation="new", name=nm, body_name=nm, profiles=[p])
for nm, p in zip(["Eye Light L", "Eye Light R"], LED_XY):
    c("solid.cylinder", radius=PIPE_R, height=round(z_top - PIPE_BOT, 4), base=[p[0], p[1], PIPE_BOT], operation="new", body_name=nm, name=nm)

# 7. Power slider cap on the switch actuator (sits 0.6 below the wall surface, in the thumb pocket)
c("solid.box", length=2.3, width=4.0, height=2.0, center=[L / 2 - 1.85, py0 - 0.8, PSW_Z], operation="new", body_name="Power Slider", name="Power Slider")

# 8. Electronics stand-ins, positions from fit.json (fit check only; not in the GLB)
stage("electronics")
zt = Z_PCB_TOP
bw, bh = FIT.size
c("sketch.create", **XY(PCB_Z), name="PCB")
c("sketch.rectangle.rounded", p0=[-bw / 2, -bh / 2], p1=[bw / 2, bh / 2], radius=FIT.corner_r)
c("sketch.circle.center", center=list(PIR_XY), radius=PIR_CUT_R)
c("sketch.finish")
c("solid.extrude", distance=PCB_T, operation="new", name="PCB", body_name="PCB", profiles=[{"point": [0, 0]}])
c("sketch.create", plane={"origin": [-CELL_L / 2, 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="AAA Cells")
for cy in CELL_Y:
    c("sketch.circle.center", center=[cy, WALL + 0.1 + CELL_R], radius=CELL_R)
c("sketch.finish")
c("solid.extrude", distance=CELL_L, operation="new", name="AAA Cells", body_name="AAA Cells", profiles="all")
mx, my = MOD_XY
c("solid.box", length=18, width=20, height=3.2, center=[mx, my, PCB_Z - 1.6], operation="new", body_name="ESP32-C3-WROOM-02", name="U2 ESP32-C3-WROOM-02 (bottom)")
c("solid.box", length=12, width=12, height=SW_H - 1.0, center=[bx, by, zt + (SW_H - 1.0) / 2], operation="new", body_name="Tact Switch", name="SW1 body")
c("solid.cylinder", radius=3.5, height=1.0, base=[bx, by, zt + SW_H - 1.0], operation="new", body_name="Switch Plunger", name="SW1 plunger")
c("solid.cylinder", radius=SPK_R, height=SPK_T, base=[SPK_XY[0], SPK_XY[1], zt + SPK_FOAM], operation="new", body_name="Speaker", name="Speaker 20x4")
c("solid.box", length=3, width=3, height=0.8, center=[AMP_XY[0], AMP_XY[1], zt + 0.4], operation="new", body_name="MAX98357A", name="U3 MAX98357A")
for nm, p in zip(["Eye LED L", "Eye LED R"], LED_XY):
    c("solid.box", length=1.6, width=0.8, height=0.8, center=[p[0], p[1], zt + 0.4], operation="new", body_name=nm, name=nm)
c("solid.box", length=4.4, width=8.6, height=3.6, center=[PSW_XY[0], PSW_XY[1], PCB_Z - 1.8], operation="new", body_name="Power Switch", name="Power Switch (bottom)")
# AM312: Ø10 body with a domed lens, one revolved profile, standing on the PIR boss through the board cutout
zd = PIR_APEX - PIR_R
c("sketch.create", plane={"origin": [PIR_XY[0], PIR_XY[1], 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="PIR Profile")
c("sketch.line", points=[[0, PIR_APEX], [0, PIR_BASE], [PIR_R, PIR_BASE], [PIR_R, zd]])
c("sketch.arc.three_point", start=[PIR_R, zd], through=[round(PIR_R * math.cos(math.pi / 4), 4), round(zd + PIR_R * math.sin(math.pi / 4), 4)], end=[0, PIR_APEX])
c("sketch.finish")
c("solid.revolve", axis="y", operation="new", name="AM312 PIR", body_name="PIR Dome")

# 9. Kawaii pastel finish (enclosure) and readable colours for the stand-ins
stage("colour")
COLOURS = {"Lid": "#8fe0c9", "Base": "#ffe08a", "Bottom Plate": "#cdbdf2", "Battery Door": "#cdbdf2",
           "Silence Button": "#ff8f87", "Eye L": "#3b3552", "Eye R": "#3b3552", "Smile": "#3b3552",
           "Cheek L": "#ffadc4", "Cheek R": "#ffadc4", "PIR Dome": "#b39ddb",
           "Eye Light L": "#ffffff", "Eye Light R": "#ffffff", "Name Field": "#ffffff", "Name Text": "#ffffff",
           "Power Slider": "#ff8f87",
           "PCB": "#2e7d4f", "AAA Cells": "#3a3a3a", "ESP32-C3-WROOM-02": "#c0c4c8", "Tact Switch": "#222222", "Switch Plunger": "#555555",
           "Speaker": "#c9a227", "MAX98357A": "#111111", "Eye LED L": "#fff8d0", "Eye LED R": "#fff8d0", "Power Switch": "#222222"}
TEXT_BODIES = ["Name Text"] + [f"Name Text ({i})" for i in range(2, 13)]   # the text extrude makes one body per glyph piece: 12 for "PROPERTY OF:"
for t in TEXT_BODIES[1:]:
    COLOURS[t] = COLOURS["Name Text"]
for body, col in COLOURS.items():
    c("appearance.assign", bodies=[body], color=col)

if __name__ == "__main__":
    upto = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else len(stage_marks)
    end = stage_marks[upto][1] if upto < len(stage_marks) else len(cmds)
    json.dump({"commands": cmds[:end]}, open(os.path.join(here, "model_build.json"), "w"), indent=1)
    print("stages:", [s for s, _ in stage_marks[:upto]], f"({end} commands)")
