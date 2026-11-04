"""Baby Monitor Monitor (003): sensor + wearable receiver -> SolidCraft CLI script (headless).

  python3 build_model.py [--upto N]   writes model_build.json (optionally only the first N stages)
  solidcraft-cli run model_build.json --save model.solidcraft --out model.step --out model.stl

Z up, both devices resting on z 0, side by side: the sensor centred at x SX (grille facing -x),
the receiver (watch, 12 o'clock = +y) centred at x RX. Each board's place, outline, posts and
everything that lines up with it come from ../fit.json (boards "sensor" and "receiver") through
tools/fit/fitlib.py, so a Stage 5 change there rebuilds into the model.
"""
import json, math, os, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "..", "..", "tools", "fit"))
from fitlib import load_fit  # noqa: E402
FS = load_fit(here, board="sensor")
FR = load_fit(here, board="receiver")

cmds, stage_marks = [], []
def c(command, **params): cmds.append({"command": command, "params": params})
def stage(name): stage_marks.append((name, len(cmds)))
def r4(v): return round(v, 4)
def P(*v): return [r4(a) for a in v]
XY = lambda z: {"plane": "XY", "offset": z} if z else {"plane": "XY"}
def yz_plane(x):   # sketch x = world y, sketch y = world z, normal +x
    return {"origin": [r4(x), 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}

# ======================================================================================
# Sensor: 52 x 34 x 24 bean, grille on the -x end, USB-C on the +x end
# ======================================================================================
SX = FS.origin[0]
S_L, S_W, S_H = 52.0, 34.0, 24.0
S_CR, S_TOP_R, S_WALL = 12.0, 9.0, 1.8
S_SPLIT_Z, S_SPLIT_TILT = 9.0, 0.2                  # swoosh parting plane: z = 9 + 0.2 (x - SX)
S_GRILLE_R, S_GRILLE_Z = 7.5, 12.0
S_PCB_TOP = FS.origin[2]
S_PCB_Z = S_PCB_TOP - FS.thickness
sxy = lambda name: tuple(r4(v) for v in FS.to_enclosure(FS.feature(name))[:2])
S_MIC, S_LED, S_BTN, S_USB = sxy("mic"), sxy("status_led"), sxy("button"), sxy("usb")
S_POSTS = [tuple(FS.to_enclosure(h)[:2]) for h in FS.holes + FS.rests]
S_USB_Z = S_PCB_TOP + 1.63
S_PIPE_BOT = S_PCB_TOP + 1.4

# ======================================================================================
# Receiver: 38 x 38 x 12.6 watch, lens on top, button at 3 o'clock (+x), USB-C at 9 (-x)
# ======================================================================================
RX = FR.origin[0]
R_S, R_H, R_CR, R_TOP_R, R_WALL = 38.0, 13.4, 9.0, 3.5, 1.6
R_BACK = 1.4                                       # back plate
R_LENS, R_LENS_R = 20.0, 6.0
R_PCB_TOP = FR.origin[2]
R_PCB_Z = R_PCB_TOP - FR.thickness
rxy = lambda name: tuple(r4(v) for v in FR.to_enclosure(FR.feature(name))[:2])
R_USB, R_BTN, R_GLOW, R_LINK = rxy("usb"), rxy("button"), rxy("glow_led"), rxy("link_led")
R_LRA, R_BAT = rxy("lra"), rxy("battery")
R_POSTS = [tuple(FR.to_enclosure(h)[:2]) for h in FR.holes + FR.rests]
R_USB_Z = R_PCB_TOP + 1.63
R_BTN_Z = R_PCB_TOP + 1.5
R_PIPE_BOT = R_PCB_TOP + 1.4
BAND_W, BAND_T, BAND_R = 20.0, 1.6, 30.0           # 20 mm band, loop for a ~60 mm wrist
LUG_Y, LUG_Z = 22.0, 5.0                           # spring-bar centre

for name, val, note in [("sensor_length", S_L, "sensor long side"), ("sensor_width", S_W, "sensor width (>31.7: not a small part)"),
                        ("sensor_height", S_H, "sensor height"), ("sensor_wall", S_WALL, "sensor shell wall"),
                        ("sensor_top_round", S_TOP_R, "sensor top edge round"),
                        ("watch_size", R_S, "receiver case, square"), ("watch_height", R_H, "receiver case height (no lens)"),
                        ("watch_wall", R_WALL, "receiver wall"), ("watch_top_round", R_TOP_R, "receiver top edge round"),
                        ("band_width", BAND_W, "quick-release band width")]:
    c("parameters.add", name=name, expression=f"{val} mm", comment=note)

def corner_pts(cx, cy, L, W, CR, z):
    """Points on a rounded-rect block's edge loop at height z (side mids + corner arc mids)."""
    ax, ay = L / 2 - CR, W / 2 - CR; d = CR / math.sqrt(2)
    pts = [[cx, cy + W / 2, z], [cx, cy - W / 2, z], [cx + L / 2, cy, z], [cx - L / 2, cy, z]]
    pts += [[cx + sx * (ax + d), cy + sy * (ay + d), z] for sx in (-1, 1) for sy in (-1, 1)]
    return [P(*p) for p in pts]

# ---- 1. sensor shell ---------------------------------------------------------------
stage("sensor shell")
c("sketch.create", **XY(0), name="Sensor Footprint")
c("sketch.rectangle.rounded", p0=[SX - S_L / 2, -S_W / 2], p1=[SX + S_L / 2, S_W / 2], radius=S_CR)
c("sketch.finish")
c("solid.extrude", distance="sensor_height", operation="new", name="Sensor Bean", body_name="Sensor Shell")
c("solid.fillet", edges=corner_pts(SX, 0, S_L, S_W, S_CR, S_H), radius="sensor_top_round", name="Sensor Top Round")
c("solid.shell", faces=[[SX, 0, 0]], thickness="sensor_wall", name="Sensor Hollow")
c("solid.fillet", edges=corner_pts(SX, 0, S_L, S_W, S_CR, 0), radius=1.0, name="Sensor Bottom Round")

# openings, cut before the split so each goes through cleanly
c("sketch.create", plane=yz_plane(SX - S_L / 2 - 4), name="Grille Opening")
c("sketch.circle.center", center=[0, S_GRILLE_Z], radius=S_GRILLE_R + 0.15)
c("sketch.finish")
c("solid.extrude", distance=7, operation="cut", targets=["Sensor Shell"], name="Grille Opening")

SLIT = (9.1, 10.9, S_PIPE_BOT + 0.4, 16.5)          # y0, y1, z0, z1 of the status slit
c("sketch.create", plane=yz_plane(SX - S_L / 2 - 4), name="Status Slit")
c("sketch.rectangle.rounded", p0=[SLIT[0] - 0.1, SLIT[2] - 0.1], p1=[SLIT[1] + 0.1, SLIT[3] + 0.1], radius=0.9)
c("sketch.finish")
c("solid.extrude", distance=8, operation="cut", targets=["Sensor Shell"], name="Status Slit")

c("sketch.create", plane=yz_plane(SX + S_L / 2 - 4), name="Sensor USB Opening")
c("sketch.rectangle.rounded", p0=[S_USB[1] - 4.8, S_USB_Z - 1.9], p1=[S_USB[1] + 4.8, S_USB_Z + 1.9], radius=1.8)
c("sketch.finish")
c("solid.extrude", distance=8, operation="cut", targets=["Sensor Shell"], name="Sensor USB Opening")

bx, by = S_BTN
c("sketch.create", **XY(S_H - 4), name="Sensor Button Hole")
c("sketch.circle.center", center=[bx, by], radius=6.3)
c("sketch.finish")
c("solid.extrude", distance=8, operation="cut", targets=["Sensor Shell"], name="Sensor Button Hole")

# Oakley swoosh: split along a tilted plane into a pearl upper shell and a lavender lower piece
nz = 1 / math.sqrt(1 + S_SPLIT_TILT ** 2)
c("solid.split_body", body="Sensor Shell", plane={"origin": [SX, 0, S_SPLIT_Z], "normal": P(-S_SPLIT_TILT * nz, 0, nz)})
c("body.rename", body="Sensor Shell", name="Sensor Upper")
c("body.rename", body="Sensor Shell (1)", name="Sensor Swoosh")

# ---- 2. sensor inside: bottom plate, posts, VHB, grille disc, button, light pipe ------------
stage("sensor parts")
ix, iy, ir = S_L / 2 - S_WALL - 0.15, S_W / 2 - S_WALL - 0.15, S_CR - S_WALL - 0.15
c("sketch.create", **XY(0), name="Sensor Bottom Plate")
c("sketch.rectangle.rounded", p0=[SX - ix, -iy], p1=[SX + ix, iy], radius=ir)
c("sketch.finish")
c("solid.extrude", distance="sensor_wall", operation="new", name="Sensor Bottom Plate", body_name="Sensor Base")
# board posts hang from the upper shell (posts_face "top"): the cell under the board leaves no room for floor
# posts. Each post ends on the board's top face; a pin through the hole is heat-staked under the board.
S_POST_TOP = S_H - S_WALL + 0.3                   # sunk into the top wall
c("sketch.create", **XY(S_POST_TOP), name="Sensor Posts")
for px, py in S_POSTS:
    c("sketch.circle.center", center=P(px, py), radius=1.8)
c("sketch.finish")
c("solid.extrude", distance=r4(S_POST_TOP - S_PCB_TOP), direction="negative", operation="join", targets=["Sensor Upper"], name="Sensor Posts", profiles="all")
c("sketch.create", **XY(S_PCB_TOP + 0.3), name="Sensor Stake Pins")
for px, py in S_POSTS:
    c("sketch.circle.center", center=P(px, py), radius=0.95)
c("sketch.finish")
c("solid.extrude", distance=r4(S_PCB_TOP + 0.3 - (S_PCB_Z - 0.5)), direction="negative", operation="join", targets=["Sensor Upper"], name="Sensor Stake Pins", profiles="all")
c("sketch.create", **XY(0), name="VHB Pad")
c("sketch.rectangle.rounded", p0=[SX - 18, -11], p1=[SX + 18, 11], radius=4)
c("sketch.finish")
c("solid.extrude", distance=0.8, direction="negative", operation="new", name="VHB Pad", body_name="VHB Pad")

# grille disc: dark, flat front 1.4 behind the bean's nose, hex pattern of Ø1.2 holes
gx0 = SX - S_L / 2 + 1.4
c("sketch.create", plane=yz_plane(gx0), name="Grille Disc")
c("sketch.circle.center", center=[0, S_GRILLE_Z], radius=S_GRILLE_R)
c("sketch.finish")
c("solid.extrude", distance=1.2, operation="new", name="Grille Disc", body_name="Sensor Grille")
holes = []
pitch = 2.0
for row in range(-4, 5):
    for col in range(-4, 5):
        hy = col * pitch + (pitch / 2 if row % 2 else 0)
        hz = row * pitch * math.sqrt(3) / 2
        if math.hypot(hy, hz) <= S_GRILLE_R - 1.4:
            holes.append((hy, S_GRILLE_Z + hz))
c("sketch.create", plane=yz_plane(gx0 - 1), name="Grille Holes")
for hy, hz in holes:
    c("sketch.circle.center", center=P(hy, hz), radius=0.6)
c("sketch.finish")
c("solid.extrude", distance=4, operation="cut", targets=["Sensor Grille"], name="Grille Holes", profiles="all")

# top button: revolved cap, flange under the shell, stem down to the 6x6 tact switch
z_in = S_H - S_WALL
sw_top = S_PCB_TOP + 4.3
c("sketch.create", plane={"origin": [bx, by, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Sensor Button Profile")
c("sketch.line", closed=True, points=[P(0, sw_top + 0.3), P(1.6, sw_top + 0.3), P(1.6, z_in - 0.8), P(7.2, z_in - 0.8),
                                      P(7.2, z_in - 0.1), P(6.0, z_in - 0.1), P(6.0, S_H + 1.4), P(0, S_H + 1.4)])
c("sketch.finish")
c("solid.revolve", axis="y", operation="new", name="Sensor Button", body_name="Sensor Button")
c("solid.fillet", body="Sensor Button", edges=[P(bx + 6.0, by, S_H + 1.4)], radius=1.6, name="Sensor Button Dome")

# status light pipe: a block over the LED plus a nose filling the slit (green, clear)
lx, ly = S_LED
c("solid.box", length=r4(lx + 1.6 - (SX - 22.0)), width=r4(SLIT[1] - 0.3 - (ly - 1.2)), height=r4(SLIT[3] - S_PIPE_BOT),
  center=P(((SX - 22.0) + lx + 1.6) / 2, ((ly - 1.2) + SLIT[1] - 0.3) / 2, (S_PIPE_BOT + SLIT[3]) / 2),
  operation="new", body_name="Sensor Light Pipe", name="Light Pipe Block")
c("solid.box", length=2.6, width=r4(SLIT[1] - SLIT[0]), height=r4(SLIT[3] - SLIT[2]),
  center=P(SX - 24.3 + 1.3, (SLIT[0] + SLIT[1]) / 2, (SLIT[2] + SLIT[3]) / 2),
  operation="join", targets=["Sensor Light Pipe"], name="Light Pipe Nose")

# ---- 3. receiver case ----------------------------------------------------------------
stage("receiver case")
c("sketch.create", **XY(0), name="Watch Footprint")
c("sketch.rectangle.rounded", p0=[RX - R_S / 2, -R_S / 2], p1=[RX + R_S / 2, R_S / 2], radius=R_CR)
c("sketch.finish")
c("solid.extrude", distance="watch_height", operation="new", name="Watch Block", body_name="Watch Case")
c("solid.fillet", edges=corner_pts(RX, 0, R_S, R_S, R_CR, R_H), radius="watch_top_round", name="Watch Top Round")
c("solid.shell", faces=[[RX, 0, 0]], thickness="watch_wall", name="Watch Hollow")
c("solid.fillet", edges=corner_pts(RX, 0, R_S, R_S, R_CR, 0), radius=0.8, name="Watch Bottom Round")

# lugs: four horns for 20 mm quick-release spring bars
LUG_T = 2.4
c("sketch.create", plane=yz_plane(RX - BAND_W / 2 - 0.2 - LUG_T), name="Lugs")
for s in (1, -1):
    y0, y1 = sorted([s * (R_S / 2 - 1.1), s * (LUG_Y + 2.6)])
    c("sketch.rectangle.rounded", p0=[y0, 1.4], p1=[y1, 8.6], radius=2.6)
c("sketch.finish")
c("solid.extrude", distance=LUG_T, operation="new", name="Lugs -x", body_name="Lugs A", profiles="all")
c("sketch.create", plane=yz_plane(RX + BAND_W / 2 + 0.2), name="Lugs B")
for s in (1, -1):
    y0, y1 = sorted([s * (R_S / 2 - 1.1), s * (LUG_Y + 2.6)])
    c("sketch.rectangle.rounded", p0=[y0, 1.4], p1=[y1, 8.6], radius=2.6)
c("sketch.finish")
c("solid.extrude", distance=LUG_T, operation="new", name="Lugs +x", body_name="Lugs B", profiles="all")
c("solid.combine", target="Watch Case", tools=["Lugs A", "Lugs A (2)", "Lugs B", "Lugs B (2)"], operation="join", name="Join Lugs")
c("sketch.create", plane=yz_plane(RX - BAND_W / 2 - LUG_T - 1), name="Spring Bar Holes")
for s in (1, -1):
    c("sketch.circle.center", center=[s * LUG_Y, LUG_Z], radius=0.6)
c("sketch.finish")
c("solid.extrude", distance=BAND_W + 2 * LUG_T + 2, operation="cut", targets=["Watch Case"], name="Spring Bar Holes", profiles="all")

# top: lens opening and link-LED pipe hole (+ a boss around the pipe)
r_in = R_H - R_WALL
c("sketch.create", **XY(R_H - 3), name="Lens Opening")
c("sketch.rectangle.rounded", p0=[RX - R_LENS / 2, -R_LENS / 2], p1=[RX + R_LENS / 2, R_LENS / 2], radius=R_LENS_R)
c("sketch.finish")
c("solid.extrude", distance=6, operation="cut", targets=["Watch Case"], name="Lens Opening")
c("sketch.create", **XY(r_in + 0.3), name="Link Pipe Boss")
c("sketch.circle.center", center=list(R_LINK), radius=1.5)
c("sketch.finish")
c("solid.extrude", distance=r4(r_in + 0.3 - (R_PIPE_BOT + 0.6)), direction="negative", operation="join", targets=["Watch Case"], name="Link Pipe Boss")
c("sketch.create", **XY(R_H + 0.5), name="Link Pipe Hole")
c("sketch.circle.center", center=list(R_LINK), radius=0.85)
c("sketch.finish")
c("solid.extrude", distance=r4(R_H + 0.5 - R_PIPE_BOT + 0.3), direction="negative", operation="cut", targets=["Watch Case"], name="Link Pipe Hole")

# sides: button slot at 3 o'clock, USB-C at 9 o'clock
c("sketch.create", plane=yz_plane(RX + R_S / 2 - 4), name="Awake Button Slot")
c("sketch.rectangle.rounded", p0=[R_BTN[1] - 3.6, R_BTN_Z - 1.9], p1=[R_BTN[1] + 3.6, R_BTN_Z + 1.9], radius=1.85)
c("sketch.finish")
c("solid.extrude", distance=6, operation="cut", targets=["Watch Case"], name="Awake Button Slot")
c("sketch.create", plane=yz_plane(RX - R_S / 2 - 2), name="Watch USB Opening")
c("sketch.rectangle.rounded", p0=[R_USB[1] - 4.8, R_USB_Z - 1.9], p1=[R_USB[1] + 4.8, R_USB_Z + 1.9], radius=1.8)
c("sketch.finish")
c("solid.extrude", distance=6, operation="cut", targets=["Watch Case"], name="Watch USB Opening")

# ---- 4. receiver parts: back plate + posts, lens, button, plug, link pipe, band ----------
stage("receiver parts")
q, qr = R_S / 2 - R_WALL - 0.15, R_CR - R_WALL - 0.15
c("sketch.create", **XY(0), name="Back Plate")
c("sketch.rectangle.rounded", p0=[RX - q, -q], p1=[RX + q, q], radius=qr)
c("sketch.finish")
c("solid.extrude", distance=R_BACK, operation="new", name="Back Plate", body_name="Watch Back")
# board posts hang from the lid (posts_face "top"): each post ends on the board's top face, and a pin
# goes through the hole and is heat-staked under the board
c("sketch.create", **XY(r_in + 0.3), name="Watch Posts")
for px, py in R_POSTS:
    c("sketch.circle.center", center=P(px, py), radius=1.8)
c("sketch.finish")
c("solid.extrude", distance=r4(r_in + 0.3 - R_PCB_TOP), direction="negative", operation="join", targets=["Watch Case"], name="Watch Posts", profiles="all")
c("sketch.create", **XY(R_PCB_TOP + 0.3), name="Stake Pins")
for px, py in R_POSTS:
    c("sketch.circle.center", center=P(px, py), radius=0.95)
c("sketch.finish")
c("solid.extrude", distance=r4(R_PCB_TOP + 0.3 - (R_PCB_Z - 0.5)), direction="negative", operation="join", targets=["Watch Case"], name="Stake Pins", profiles="all")

LENS_BOT = r_in - 0.1
c("sketch.create", **XY(LENS_BOT), name="Lens")
c("sketch.rectangle.rounded", p0=[RX - R_LENS / 2 + 0.1, -R_LENS / 2 + 0.1], p1=[RX + R_LENS / 2 - 0.1, R_LENS / 2 - 0.1], radius=R_LENS_R - 0.1)
c("sketch.finish")
c("solid.extrude", distance=r4(R_H + 0.7 - LENS_BOT), operation="new", name="Lens", body_name="Watch Lens")
c("solid.fillet", body="Watch Lens", edges=corner_pts(RX, 0, R_LENS - 0.2, R_LENS - 0.2, R_LENS_R - 0.1, R_H + 0.7), radius=1.2, name="Lens Pillow")

c("solid.cylinder", radius=0.8, height=r4(R_H - R_PIPE_BOT), base=[R_LINK[0], R_LINK[1], R_PIPE_BOT], operation="new", body_name="Link Pipe", name="Link Pipe")

# awake button: a pill pushed through the slot onto the side switch's plunger
bxx = RX + R_S / 2
btn_in = FR.to_enclosure((FR.size[0] / 2, 0))[0] + 0.1   # 0.1 off the board edge, where the plunger tip is
c("sketch.create", plane=yz_plane(btn_in), name="Awake Button")
c("sketch.rectangle.rounded", p0=[R_BTN[1] - 3.4, R_BTN_Z - 1.7], p1=[R_BTN[1] + 3.4, R_BTN_Z + 1.7], radius=1.65)
c("sketch.finish")
c("solid.extrude", distance=r4(bxx + 0.9 - btn_in), operation="new", name="Awake Button", body_name="Awake Button")

# silicone USB plug: a block in the opening with a thin grip tab
ux = RX - R_S / 2
c("sketch.create", plane=yz_plane(ux - 0.4), name="USB Plug")
c("sketch.rectangle.rounded", p0=[R_USB[1] - 4.6, R_USB_Z - 1.7], p1=[R_USB[1] + 4.6, R_USB_Z + 1.7], radius=1.65)
c("sketch.finish")
c("solid.extrude", distance=2.6, operation="new", name="USB Plug", body_name="USB Plug")

# elastic band: one loop through both spring bars, round a ~60 mm wrist
zc = LUG_Z - math.sqrt(BAND_R ** 2 - LUG_Y ** 2)
half = 180 - math.degrees(math.atan2(LUG_Z - zc, LUG_Y))        # from the bottom of the loop to a lug
c("sketch.create", plane={"origin": [0, 0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Band Section")
c("sketch.rectangle.two_point", p0=P(RX - BAND_W / 2, zc - BAND_R - BAND_T), p1=P(RX + BAND_W / 2, zc - BAND_R))
c("sketch.finish")
c("solid.revolve", axis={"origin": P(RX, 0, zc), "dir": [1, 0, 0]}, angle=f"{r4(2 * half)} deg", direction="symmetric",
  operation="new", name="Band", body_name="Band")

# ---- 5. electronics stand-ins (positions from fit.json) ----------------------------------
stage("electronics")
def pcb(F, name, z):
    w, h = F.size
    ox, oy = F.origin[0], F.origin[1]
    c("sketch.create", **XY(z), name=name)
    if F.corner_r * 2 >= min(w, h) - 1e-6 and abs(w - h) < 1e-6:
        c("sketch.circle.center", center=[ox, oy], radius=w / 2)
    else:
        c("sketch.rectangle.rounded", p0=[ox - w / 2, oy - h / 2], p1=[ox + w / 2, oy + h / 2], radius=F.corner_r)
    for hx, hy in F.holes:
        c("sketch.circle.center", center=P(ox + hx, oy + hy), radius=F.hole_d / 2)
    c("sketch.finish")
    c("solid.extrude", distance=F.thickness, operation="new", name=name, body_name=name, profiles=[{"point": [ox, oy]}])
pcb(FS, "S PCB", S_PCB_Z)
pcb(FR, "R PCB", R_PCB_Z)
box = lambda body, l, w, h, cx, cy, cz: c("solid.box", length=l, width=w, height=h, center=P(cx, cy, cz), operation="new", body_name=body, name=body)
# sensor
box("S Battery", 30, 25, 6, SX, 0, S_WALL + 0.1 + 3)
box("S Mic", 3.5, 2.65, 1.0, S_MIC[0], S_MIC[1], S_PCB_TOP + 0.5)
box("S Status LED", 1.6, 0.8, 1.1, S_LED[0], S_LED[1], S_PCB_TOP + 0.55)
box("S Tact Switch", 6, 6, 4.3, S_BTN[0], S_BTN[1], S_PCB_TOP + 2.15)
box("S USB-C", 7.3, 8.9, 3.26, S_USB[0], S_USB[1], S_PCB_TOP + 1.63)
# receiver
box("R Battery", 20, 25, 4, R_BAT[0], R_BAT[1], R_BACK + 0.1 + 2)
c("solid.cylinder", radius=5, height=2.7, base=[R_LRA[0], R_LRA[1], R_BACK], operation="new", body_name="R ERM Motor", name="R ERM Motor")
box("R USB-C", 7.3, 8.9, 3.26, R_USB[0], R_USB[1], R_PCB_TOP + 1.63)
box("R Side Switch", 3.5, 4.5, 3.0, R_BTN[0], R_BTN[1], R_PCB_TOP + 1.5)
box("R Glow LED", 2.2, 2.2, 0.9, R_GLOW[0], R_GLOW[1], R_PCB_TOP + 0.45)
box("R Link LED", 1.6, 0.8, 1.1, R_LINK[0], R_LINK[1], R_PCB_TOP + 0.55)

# ---- 6. colour ---------------------------------------------------------------------
stage("colour")
COLOURS = {
    "Sensor Upper": "#eef0f5", "Sensor Swoosh": "#b4acdc", "Sensor Base": "#8f93a6", "VHB Pad": "#d9d9d9",
    "Sensor Grille": "#2c2b35", "Sensor Button": "#d9dce6", "Sensor Light Pipe": "#7dff63",
    "Watch Case": "#e6e9f0", "Watch Back": "#b9b3d9", "Watch Lens": "#d86cff", "Link Pipe": "#7dff63",
    "Awake Button": "#9d8fe0", "USB Plug": "#9d8fe0", "Band": "#6e58a8",
    "S PCB": "#2e7d4f", "R PCB": "#2e7d4f", "S Battery": "#3a3a3a", "R Battery": "#3a3a3a", "R ERM Motor": "#c0c4c8",
    "S Mic": "#c0c4c8", "S Status LED": "#d8ffd0", "S Tact Switch": "#222222", "S USB-C": "#b0b4b8",
    "R USB-C": "#b0b4b8", "R Side Switch": "#222222", "R Glow LED": "#f4f4f4", "R Link LED": "#d8ffd0",
}
OPACITY = {"Watch Lens": 0.8, "Sensor Light Pipe": 0.85, "Link Pipe": 0.85}
for body, col in COLOURS.items():
    c("appearance.assign", bodies=[body], color=col, **({"opacity": OPACITY[body]} if body in OPACITY else {}))

if __name__ == "__main__":
    upto = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else len(stage_marks)
    end = stage_marks[upto][1] if upto < len(stage_marks) else len(cmds)
    json.dump({"commands": cmds[:end]}, open(os.path.join(here, "model_build.json"), "w"), indent=1)
    print("stages:", [s for s, _ in stage_marks[:upto]], f"({end} commands)")
