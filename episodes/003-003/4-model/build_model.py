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
# Sensor: 66.5 x 42.5 x 32.5 mouse-like bean (103450 cell) + SM58-style grille cage, grille on the -x end, USB-C + power switch on the +x end
# ======================================================================================
SX = FS.origin[0]
S_L, S_W, S_H = 63.0, 42.8, 32.6                   # body (the cage adds ~6.5 at the nose)
S_CR, S_TOP_R, S_WALL = 10.0, 5.0, 1.8
S_SPLIT_Z, S_SPLIT_TILT = 12.0, 0.25                # swoosh parting plane: z = 12 + 0.25 (x - SX)
S_GRILLE_R, S_GRILLE_Z = 8.0, 15.0
S_SW_H = 5.0                                       # XKB 1TS009 6 x 6 x 5.0 tact switch (Stage 5)
S_PCB_TOP = FS.origin[2]
S_PCB_Z = S_PCB_TOP - FS.thickness
sxy = lambda name: tuple(r4(v) for v in FS.to_enclosure(FS.feature(name))[:2])
S_MIC, S_LED, S_BTN, S_USB = sxy("mic"), sxy("status_led"), sxy("button"), sxy("usb")
S_PSW, S_CELL = sxy("power_switch"), sxy("cell")
S_CELL_WLH = (*FS.features["cell"]["size"], 10.0)     # 103450: 50 x 34 x 10
S_PSW_Z = S_PCB_TOP + 0.8                          # C&K PCM12SMTR lever centre (Stage 5)
S_LEVER_TIP = S_PSW[0] + 3.15                      # lever tip: footprint origin + 3.15 (Stage 5)
SL_Z0, SL_Z1 = S_PCB_TOP + 0.15, S_PCB_TOP + 2.85      # slider cap: clears the board, centred near the lever
SLIDER_W, SLIDER_TRAVEL = 5.2, 1.5                 # slider cap on the back: width (y), lever travel
SLIDER_Y = S_PSW[1] - SLIDER_TRAVEL / 2            # shown at one end of its travel, as KiCad's PCM12 model has its lever (Stage 5)
S_POSTS = [tuple(FS.to_enclosure(h)[:2]) for h in FS.holes + FS.rests]
S_USB_Z = S_PCB_TOP + 1.63
S_PIPE_BOT = S_PCB_TOP + 1.4

# ======================================================================================
# Receiver: 38 x 38 x 12.7 sealed watch: lens on top, no button, no port; pogo charge contacts on the back
# ======================================================================================
RX = FR.origin[0]
R_S, R_H, R_CR, R_TOP_R, R_WALL = 38.0, 12.7, 9.0, 3.5, 1.6
R_BACK = 1.4                                       # back plate
R_LENS, R_LENS_R = 20.0, 6.0
R_PCB_TOP = FR.origin[2]
R_PCB_Z = R_PCB_TOP - FR.thickness
rxy = lambda name: tuple(r4(v) for v in FR.to_enclosure(FR.feature(name))[:2])
R_GLOW, R_LINK = rxy("glow_led"), rxy("link_led")
R_POGO = [rxy("pogo_pos"), rxy("pogo_neg")]
R_MAGNETS = [tuple(r4(v) for v in FR.to_enclosure(xy)[:2]) for xy in ((-1, -13), (13, -13))]   # in the back plate only
R_LRA, R_BAT = rxy("lra"), rxy("battery")
R_POSTS = [tuple(FR.to_enclosure(h)[:2]) for h in FR.holes + FR.rests]
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

# ---- 1. sensor shell: a computer-mouse bean ------------------------------------------
# Plan: four three-point arcs (fuller on the right, a thumb dimple on the left), a crowned top that is
# tallest just behind the grille and sweeps down to the back, an SM58-style cage on the nose.
# All sensor numbers below are relative to SX (x forward = -x, the grille end).
def circ3(p1, p2, p3):
    (ax, ay), (bx_, by_), (cx_, cy_) = p1, p2, p3
    d = 2 * (ax * (by_ - cy_) + bx_ * (cy_ - ay) + cx_ * (ay - by_))
    ux = ((ax * ax + ay * ay) * (by_ - cy_) + (bx_ * bx_ + by_ * by_) * (cy_ - ay) + (cx_ * cx_ + cy_ * cy_) * (ay - by_)) / d
    uy = ((ax * ax + ay * ay) * (cx_ - bx_) + (bx_ * bx_ + by_ * by_) * (ax - cx_) + (cx_ * cx_ + cy_ * cy_) * (bx_ - ax)) / d
    return ux, uy, math.hypot(ax - ux, ay - uy)
# Lofted through cross-sections (x, right half-width, left half-width, height, crown corner radius). The crown is
# rounder on the right and steeper on the left (thumb) side; the nose rounds over in four quick sections; the back
# is lower. (A plan extrude with a filleted crown was tried first: the fillet took 5 min and then failed.)
S_SECTIONS = [(-34.0, 13.0, -12.5, 24.0, 9.0), (-33.3, 17.0, -16.5, 27.5, 11.0), (-32.0, 19.3, -18.8, 29.6, 12.0),
              (-29.5, 20.6, -20.1, 31.0, 13.0), (-22.0, 21.4, -20.7, 32.2, 14.0), (-10.0, 21.9, -20.9, 32.6, 14.0),
              (4.0, 21.9, -20.8, 31.6, 14.0), (16.0, 21.3, -20.3, 29.4, 13.0), (24.0, 20.5, -19.7, 27.0, 12.0),
              (26.5, 19.6, -18.9, 25.6, 11.0), (28.2, 17.8, -17.2, 23.8, 9.0), (29.0, 15.0, -14.5, 22.0, 7.0)]
S_THUMB = 4.0                                            # the left crown radius is this much tighter
S_RB = 2.0                                               # bottom edge radius (the base slab takes most of it)
S_SWOOSH_Z0, S_SWOOSH_SLOPE = 11.0, (0.25, 0.08)        # swoosh plane: z = 11 + 0.25 x - 0.08 y (front ~2.5, back ~18.3)
GZ, COLLAR_R, CAGE_R = 13.5, 9.0, 10.2                  # grille axis height, collar, cage ball radius
SLIT = (10.4, 11.6, 14.0, 18.8)                         # y0, y1, z0, z1 of the status slit (beside the grille)
NOSE_X, BACK_X = S_SECTIONS[0][0], S_SECTIONS[-1][0]
def sec_interp(x, k):
    for a, b in zip(S_SECTIONS, S_SECTIONS[1:]):
        if a[0] <= x <= b[0]:
            t = (x - a[0]) / (b[0] - a[0]); return a[k] + t * (b[k] - a[k])
    raise ValueError(x)
def top_z(x, inset=0.0): return sec_interp(x, 3) - inset
cw, cl, ch = S_CELL_WLH
for xx in (-cw / 2, cw / 2):                             # the 103450 cell must clear the side walls
    assert sec_interp(xx, 1) - S_WALL > cl / 2 + 0.3 and -sec_interp(xx, 2) - S_WALL > cl / 2 + 0.3, "cell hits the sensor's side wall"

def in_nose_face(y, z):
    x, yr, yl, h, rt = S_SECTIONS[0]; rl = rt - S_THUMB
    if not (yl < y < yr and S_RB < z < h): return False
    if y > yr - rt and z > h - rt: return math.hypot(y - (yr - rt), z - (h - rt)) < rt
    if y < yl + rl and z > h - rl: return math.hypot(y - (yl + rl), z - (h - rl)) < rl
    return True
for ang in range(0, 360, 10):
    assert in_nose_face((COLLAR_R + 0.4) * math.cos(math.radians(ang)), GZ + (COLLAR_R + 0.4) * math.sin(math.radians(ang))), "grille leaves the nose face"
for yy, zz in [(SLIT[1] + 0.2, SLIT[3] + 0.2), (SLIT[1] + 0.2, SLIT[2] - 0.2)]:
    assert in_nose_face(yy, zz), "status slit leaves the nose face"

stage("sensor shell")
q = math.sqrt(0.5)
def section(name, x, yr, yl, h, rt, rb, z0=0.0, thumb=S_THUMB):
    rl = rt - thumb
    c("sketch.create", plane=yz_plane(SX + x), name=name)
    c("sketch.line", points=[P(yl + rb, z0), P(yr - rb, z0)])
    c("sketch.arc.three_point", start=P(yr - rb, z0), through=P(yr - rb + rb * q, z0 + rb - rb * q), end=P(yr, z0 + rb))
    c("sketch.line", points=[P(yr, z0 + rb), P(yr, h - rt)])
    c("sketch.arc.three_point", start=P(yr, h - rt), through=P(yr - rt + rt * q, h - rt + rt * q), end=P(yr - rt, h))
    c("sketch.line", points=[P(yr - rt, h), P(yl + rl, h)])
    c("sketch.arc.three_point", start=P(yl + rl, h), through=P(yl + rl - rl * q, h - rl + rl * q), end=P(yl, h - rl))
    c("sketch.line", points=[P(yl, h - rl), P(yl, z0 + rb)])
    c("sketch.arc.three_point", start=P(yl, z0 + rb), through=P(yl + rb - rb * q, z0 + rb - rb * q), end=P(yl + rb, z0))
    c("sketch.finish")
for k, (x, yr, yl, h, rt) in enumerate(S_SECTIONS):
    section(f"Sensor Section {k}", x, yr, yl, h, rt, S_RB)
c("solid.loft", sections=[{"sketch": f"Sensor Section {k}"} for k in range(len(S_SECTIONS))], operation="new",
  name="Sensor Body", body_name="Sensor Shell")
DIMPLE_C, DIMPLE_R = P(SX + 6, sec_interp(6, 2) - 46.0, 17), 48.0      # thumb dimple, 2 mm deep, on the left side
# (a spherical thumb dimple was tried: the cavity cut then failed where its sphere met the swoosh face)
# a 1.8 mm base slab (dark foot); the rest is hollowed by an inset loft (SolidCraft's shell can't offset lofted faces)
c("solid.split_body", body="Sensor Shell", plane={"origin": [SX, 0, S_WALL], "normal": [0, 0, 1]})
c("body.rename", body="Sensor Shell (1)", name="Sensor Base")
w = S_WALL
inner = []
for xe, sgn in ((NOSE_X + w, 1), (BACK_X - w, -1)):            # end sections: inset, shrunk a little more to follow the round-over
    inner.append((xe, sec_interp(xe, 1) - w - 1.0, sec_interp(xe, 2) + w + 1.0, sec_interp(xe, 3) - w - 1.0, max(sec_interp(xe, 4) - w - 1.0, 3.0)))
mid = [(x, yr - w, yl + w, h - w, rt - w) for x, yr, yl, h, rt in S_SECTIONS if NOSE_X + w + 0.8 < x < BACK_X - w - 0.8]
inner = [inner[0]] + mid + [inner[1]]
for k, (x, yr, yl, h, rt) in enumerate(inner):
    section(f"Sensor Cavity {k}", x, yr, yl, h, rt, 0.5, z0=-1.0, thumb=S_THUMB)
c("solid.loft", sections=[{"sketch": f"Sensor Cavity {k}"} for k in range(len(inner))], operation="new",
  name="Sensor Cavity", body_name="Sensor Cavity")
c("solid.combine", target="Sensor Shell", tools=["Sensor Cavity"], operation="cut", name="Sensor Hollow")

# openings, cut before the swoosh split. The grille and slit sit inside the nose's flat face, so their cuts
# meet only flat faces (a cut through the lofted nose took ~3 min)
c("sketch.create", plane=yz_plane(SX - 42), name="Grille Opening")
c("sketch.circle.center", center=[0, GZ], radius=COLLAR_R + 0.2)
c("sketch.finish")
c("solid.extrude", distance=14, operation="cut", targets=["Sensor Shell"], name="Grille Opening")

slit_in = -29.4                                                # inside the nose, behind the collar's inner end
c("sketch.create", plane=yz_plane(SX - 42), name="Status Slit")
c("sketch.rectangle.rounded", p0=[SLIT[0] - 0.1, SLIT[2] - 0.1], p1=[SLIT[1] + 0.1, SLIT[3] + 0.1], radius=0.69)
c("sketch.finish")
c("solid.extrude", distance=r4(42 + slit_in), operation="cut", targets=["Sensor Shell"], name="Status Slit")

c("sketch.create", plane=yz_plane(SX + 26), name="Sensor USB Opening")
c("sketch.rectangle.rounded", p0=[S_USB[1] - 4.8, S_USB_Z - 1.9], p1=[S_USB[1] + 4.8, S_USB_Z + 1.9], radius=1.8)
c("sketch.finish")
c("solid.extrude", distance=12, operation="cut", targets=["Sensor Shell"], name="Sensor USB Opening")
c("sketch.create", plane=yz_plane(SX + 26), name="Power Switch Slot")
sl = SLIDER_W / 2 + SLIDER_TRAVEL / 2 + 0.15
c("sketch.rectangle.rounded", p0=[S_PSW[1] - sl, SL_Z0 - 0.15], p1=[S_PSW[1] + sl, SL_Z1 + 0.15], radius=1.3)
c("sketch.finish")
c("solid.extrude", distance=12, operation="cut", targets=["Sensor Shell"], name="Power Switch Slot")

bx, by = S_BTN
zt_b = top_z(bx - SX)                                       # (S_BTN sits on a section station)
c("sketch.create", **XY(zt_b - 5), name="Sensor Button Hole")
c("sketch.circle.center", center=[bx, by], radius=6.3)
c("sketch.finish")
c("solid.extrude", distance=10, operation="cut", targets=["Sensor Shell"], name="Sensor Button Hole")

# the swoosh: split along a plane tilted front-to-back and a little side-to-side, so the lavender lower piece sweeps up
# toward the back and sits higher on the left than the right (a split along a big curved surface would not close on the loft)
nrm_ = [-S_SWOOSH_SLOPE[0], S_SWOOSH_SLOPE[1], 1.0]
ln_ = math.sqrt(sum(v * v for v in nrm_))
c("solid.split_body", body="Sensor Shell", plane={"origin": [SX, 0, S_SWOOSH_Z0], "normal": P(*[v / ln_ for v in nrm_])})
c("body.rename", body="Sensor Shell", name="Sensor Upper")
c("body.rename", body="Sensor Shell (1)", name="Sensor Swoosh")
# ---- 2. sensor inside: posts, VHB, grille collar + cage, button, light pipe -----------------
stage("sensor parts")
# board posts hang from the upper shell (posts_face "top"): the cell under the board leaves no room for floor
# posts. Each post ends on the board's top face; a pin through the hole is heat-staked under the board.
for k, (px, py) in enumerate(S_POSTS):
    ptop = top_z(px - SX, S_WALL) + 0.8                         # sunk into the top wall (the loft is near-linear between stations)
    c("sketch.create", **XY(r4(ptop)), name=f"Sensor Post {k + 1}")
    c("sketch.circle.center", center=P(px, py), radius=1.8)
    c("sketch.finish")
    c("solid.extrude", distance=r4(ptop - S_PCB_TOP), direction="negative", operation="join", targets=["Sensor Upper"], name=f"Sensor Post {k + 1}")
c("sketch.create", **XY(S_PCB_TOP + 0.3), name="Sensor Stake Pins")
for px, py in S_POSTS:
    c("sketch.circle.center", center=P(px, py), radius=0.95)
c("sketch.finish")
c("solid.extrude", distance=r4(S_PCB_TOP + 0.3 - (S_PCB_Z - 0.5)), direction="negative", operation="join", targets=["Sensor Upper"], name="Sensor Stake Pins", profiles="all")
c("sketch.create", **XY(0), name="VHB Pad")
c("sketch.rectangle.rounded", p0=[SX - 22, -14], p1=[SX + 22, 14], radius=5)
c("sketch.finish")
c("solid.extrude", distance=0.8, direction="negative", operation="new", name="VHB Pad", body_name="VHB Pad")

# grille: a chrome collar ring in the nose opening and a domed honeycomb cage on it (SM58 style)
XZ0 = {"origin": [0, 0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}
AXIS = {"origin": [SX, 0, GZ], "dir": [1, 0, 0]}
c_in, c_out = SX - 29.5, SX + NOSE_X - 1.2                              # collar: from inside the nose to 2-3 mm proud of it
c("sketch.create", plane=XZ0, name="Grille Collar Profile")
c("sketch.rectangle.two_point", p0=P(c_out, GZ + COLLAR_R - 1.3), p1=P(c_in, GZ + COLLAR_R))
c("sketch.finish")
c("solid.revolve", axis=AXIS, operation="new", name="Grille Collar", body_name="Grille Collar")
cc = c_out + 4.4                                                  # cage ball centre, behind the collar's face
ro, ri = CAGE_R, CAGE_R - 1.0
h_o, h_i = math.sqrt(ro ** 2 - (c_out - cc) ** 2), math.sqrt(ri ** 2 - (c_out - cc) ** 2)
q = math.sqrt(0.5)
c("sketch.create", plane=XZ0, name="Grille Cage Profile")
c("sketch.arc.three_point", start=P(c_out, GZ + h_o), through=P(cc - ro * q, GZ + ro * q), end=P(cc - ro, GZ))
c("sketch.line", points=[P(cc - ro, GZ), P(cc - ri, GZ)])
c("sketch.arc.three_point", start=P(cc - ri, GZ), through=P(cc - ri * q, GZ + ri * q), end=P(c_out, GZ + h_i))
c("sketch.line", points=[P(c_out, GZ + h_i), P(c_out, GZ + h_o)])
c("sketch.finish")
c("solid.revolve", axis=AXIS, operation="new", name="Grille Cage", body_name="Sensor Grille")
holes = []
pitch = 2.2
for row in range(-5, 6):
    for col in range(-5, 6):
        hy = col * pitch + (pitch / 2 if row % 2 else 0)
        hz = row * pitch * math.sqrt(3) / 2
        if math.hypot(hy, hz) <= h_i - 1.3:
            holes.append((hy, GZ + hz))
c("sketch.create", plane=yz_plane(cc - ro - 2), name="Grille Holes")
for hy, hz in holes:
    c("sketch.circle.center", center=P(hy, hz), radius=0.65)
c("sketch.finish")
c("solid.extrude", distance=r4(ro + 2 - (cc - c_out) + 0.5), operation="cut", targets=["Sensor Grille"], name="Grille Holes", profiles="all")

# top button ("I'm awake"): revolved cap, flange under the sloping crown, stem down to the 6x6 tact switch
slope_b = (top_z(bx - SX + 3) - top_z(bx - SX - 3)) / 6
z_in = zt_b - S_WALL - abs(slope_b) * 7.2 - 0.3              # flange clears the sloping inside of the crown
sw_top = S_PCB_TOP + S_SW_H
cap_top = zt_b + 1.4
c("sketch.create", plane={"origin": [bx, by, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Sensor Button Profile")
c("sketch.line", closed=True, points=[P(0, sw_top + 0.3), P(1.6, sw_top + 0.3), P(1.6, z_in - 0.7), P(7.2, z_in - 0.7),
                                      P(7.2, z_in), P(6.0, z_in), P(6.0, cap_top), P(0, cap_top)])
c("sketch.finish")
c("solid.revolve", axis="y", operation="new", name="Sensor Button", body_name="Sensor Button")
c("solid.fillet", body="Sensor Button", edges=[P(bx + 6.0, by, cap_top)], radius=1.6, name="Sensor Button Dome")

# power slider: a cap in the back slot that reaches in over the PCM12's short lever; a notch takes the lever
sx_in = S_LEVER_TIP - 0.8
sx_out = SX + BACK_X + 0.6                           # 0.6 proud of the flat back
zc_ = (SL_Z0 + SL_Z1) / 2
c("solid.box", length=r4(sx_out - sx_in), width=SLIDER_W, height=r4(SL_Z1 - SL_Z0), center=P((sx_in + sx_out) / 2, SLIDER_Y, zc_),
  operation="new", body_name="Switch Slider", name="Switch Slider")
c("solid.box", length=1.0, width=1.7, height=r4(S_PSW_Z + 0.85 - SL_Z0 + 0.5), center=P(sx_in + 0.5, SLIDER_Y, (SL_Z0 - 0.5 + S_PSW_Z + 0.85) / 2),
  operation="cut", targets=["Switch Slider"], name="Slider Lever Notch")
c("solid.fillet", body="Switch Slider", edges=[P(sx_out, SLIDER_Y + s_ * SLIDER_W / 2, zc_) for s_ in (1, -1)]
  + [P(sx_out, SLIDER_Y + 1.5, zc_ + s_ * (SL_Z1 - SL_Z0) / 2) for s_ in (1, -1)], radius=0.8, name="Slider Round")

# status light pipe: a block over the LED plus a nose filling the slit on the right cheek (green, clear)
lx, ly = S_LED
px0 = SX + slit_in                                              # clear of the grille collar
c("solid.box", length=r4(lx + 1.6 - px0), width=r4(SLIT[1] - 0.3 - (ly - 1.2)), height=r4(SLIT[3] - S_PIPE_BOT),
  center=P((px0 + lx + 1.6) / 2, ((ly - 1.2) + SLIT[1] - 0.3) / 2, (S_PIPE_BOT + SLIT[3]) / 2),
  operation="new", body_name="Sensor Light Pipe", name="Light Pipe Block")
n0 = SX + NOSE_X + 0.6                                          # nose face just inside the outer skin
c("solid.box", length=r4(px0 + 0.4 - n0), width=r4(SLIT[1] - SLIT[0]), height=r4(SLIT[3] - SLIT[2]),
  center=P((n0 + px0 + 0.4) / 2, (SLIT[0] + SLIT[1]) / 2, (SLIT[2] + SLIT[3]) / 2),
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

# charging: two gold contacts through the back plate (pogo pins on the board press on them) and two magnets
c("sketch.create", **XY(-0.5), name="Contact Holes")
for p in R_POGO:
    c("sketch.circle.center", center=list(p), radius=1.3)
c("sketch.finish")
c("solid.extrude", distance=R_BACK + 1, operation="cut", targets=["Watch Back"], name="Contact Holes", profiles="all")
c("sketch.create", **XY(-0.5), name="Magnet Pockets")
for p in R_MAGNETS:
    c("sketch.circle.center", center=list(p), radius=1.6)
c("sketch.finish")
c("solid.extrude", distance=1.5, operation="cut", targets=["Watch Back"], name="Magnet Pockets", profiles="all")
for nm, p in zip(["Charge Contact +", "Charge Contact -"], R_POGO):
    c("solid.cylinder", radius=1.25, height=R_BACK, base=[p[0], p[1], 0], operation="new", body_name=nm, name=nm)
for nm, p in zip(["Magnet A", "Magnet B"], R_MAGNETS):
    c("solid.cylinder", radius=1.5, height=1.0, base=[p[0], p[1], 0], operation="new", body_name=nm, name=nm)

LENS_BOT = r_in - 0.1
c("sketch.create", **XY(LENS_BOT), name="Lens")
c("sketch.rectangle.rounded", p0=[RX - R_LENS / 2 + 0.1, -R_LENS / 2 + 0.1], p1=[RX + R_LENS / 2 - 0.1, R_LENS / 2 - 0.1], radius=R_LENS_R - 0.1)
c("sketch.finish")
c("solid.extrude", distance=r4(R_H + 0.7 - LENS_BOT), operation="new", name="Lens", body_name="Watch Lens")
c("solid.fillet", body="Watch Lens", edges=corner_pts(RX, 0, R_LENS - 0.2, R_LENS - 0.2, R_LENS_R - 0.1, R_H + 0.7), radius=1.2, name="Lens Pillow")

c("solid.cylinder", radius=0.8, height=r4(R_H - R_PIPE_BOT), base=[R_LINK[0], R_LINK[1], R_PIPE_BOT], operation="new", body_name="Link Pipe", name="Link Pipe")

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
box("S Battery", S_CELL_WLH[0], S_CELL_WLH[1], S_CELL_WLH[2], S_CELL[0], S_CELL[1], S_WALL + 0.1 + S_CELL_WLH[2] / 2)
box("S Mic", 3.5, 2.65, 1.0, S_MIC[0], S_MIC[1], S_PCB_TOP + 0.5)
box("S Status LED", 1.6, 0.8, 1.1, S_LED[0], S_LED[1], S_PCB_TOP + 0.55)
box("S Tact Switch", 6, 6, S_SW_H, S_BTN[0], S_BTN[1], S_PCB_TOP + S_SW_H / 2)
box("S USB-C", 7.3, 8.9, 3.26, S_USB[0], S_USB[1], S_PCB_TOP + 1.63)
box("S Power Switch", 2.6, 6.7, 1.5, S_PSW[0] + 0.3, S_PSW[1], S_PCB_TOP + 0.75)   # body x origin -1.0 .. +1.6
box("S Switch Lever", 1.55, 1.3, 1.0, S_LEVER_TIP - 0.775, SLIDER_Y, S_PSW_Z)
# receiver
box("R Battery", 20, 25, 4, R_BAT[0], R_BAT[1], R_BACK + 0.1 + 2)
c("solid.cylinder", radius=5, height=2.7, base=[R_LRA[0], R_LRA[1], R_BACK], operation="new", body_name="R ERM Motor", name="R ERM Motor")
for nm, p in zip(["R Pogo +", "R Pogo -"], R_POGO):
    c("solid.cylinder", radius=0.75, height=r4(R_PCB_Z - R_BACK), base=[p[0], p[1], R_BACK], operation="new", body_name=nm, name=nm)
box("R Glow LED", 2.2, 2.2, 0.9, R_GLOW[0], R_GLOW[1], R_PCB_TOP + 0.45)
box("R Link LED", 1.6, 0.8, 1.1, R_LINK[0], R_LINK[1], R_PCB_TOP + 0.55)

# ---- 6. colour ---------------------------------------------------------------------
stage("colour")
COLOURS = {
    "Sensor Upper": "#eef0f5", "Sensor Swoosh": "#b4acdc", "Sensor Base": "#8f93a6", "VHB Pad": "#d9d9d9",
    "Sensor Grille": "#2c2b35", "Grille Collar": "#c8ccd6", "Sensor Button": "#d9dce6", "Sensor Light Pipe": "#7dff63",
    "Watch Case": "#e6e9f0", "Watch Back": "#b9b3d9", "Watch Lens": "#d86cff", "Link Pipe": "#7dff63",
    "Band": "#6e58a8", "Charge Contact +": "#d8b04a", "Charge Contact -": "#d8b04a", "Magnet A": "#4a4a55", "Magnet B": "#4a4a55",
    "S PCB": "#2e7d4f", "R PCB": "#2e7d4f", "S Battery": "#3a3a3a", "R Battery": "#3a3a3a", "R ERM Motor": "#c0c4c8",
    "S Mic": "#c0c4c8", "S Status LED": "#d8ffd0", "S Tact Switch": "#222222", "S USB-C": "#b0b4b8",
    "R Pogo +": "#d8b04a", "R Pogo -": "#d8b04a", "S Power Switch": "#222222", "S Switch Lever": "#222222", "Switch Slider": "#9d8fe0", "R Glow LED": "#f4f4f4", "R Link LED": "#d8ffd0",
}
OPACITY = {"Watch Lens": 0.8, "Sensor Light Pipe": 0.85, "Link Pipe": 0.85}
for body, col in COLOURS.items():
    c("appearance.assign", bodies=[body], color=col, **({"opacity": OPACITY[body]} if body in OPACITY else {}))

if __name__ == "__main__":
    upto = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else len(stage_marks)
    end = stage_marks[upto][1] if upto < len(stage_marks) else len(cmds)
    json.dump({"commands": cmds[:end]}, open(os.path.join(here, "model_build.json"), "w"), indent=1)
    print("stages:", [s for s, _ in stage_marks[:upto]], f"({end} commands)")
