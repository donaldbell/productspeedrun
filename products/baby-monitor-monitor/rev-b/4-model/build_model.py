"""Baby Monitor Monitor (003) Rev B: sensor + wearable receiver -> SolidCraft CLI script (headless).

  python3 build_model.py [--upto N] [--blockout]   writes model_build.json (optionally only the first N stages;
                                                   --blockout: the outer forms and visible details only)
  solidcraft-cli run model_build.json --save model.solidcraft --out model.step --out model.stl

Z up, both devices resting on z 0, side by side: the sensor centred at x SX (grille facing -x),
the receiver (watch, 12 o'clock = +y) centred at x RX. Each board's place, outline, posts and
everything that lines up with it come from ../fit.json (boards "sensor" and "receiver") through
tools/fit/fitlib.py, so a Stage 5 change there rebuilds into the model.
"""
import json, math, os, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "..", "..", "..", "tools", "fit"))   # rev-b sits one level deeper than an episode
from fitlib import load_fit  # noqa: E402
FS = load_fit(here, board="sensor")
FR = load_fit(here, board="receiver")

BLOCKOUT = "--blockout" in sys.argv
cmds, stage_marks = [], []
def c(command, **params): cmds.append({"command": command, "params": params})
def stage(name): stage_marks.append((name, len(cmds)))
def r4(v): return round(v, 4)
def P(*v): return [r4(a) for a in v]
XY = lambda z: {"plane": "XY", "offset": z} if z else {"plane": "XY"}
def yz_plane(x):   # sketch x = world y, sketch y = world z, normal +x
    return {"origin": [r4(x), 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}

# ======================================================================================
# Sensor: 64 x 44.3 x 29.8 low teardrop pebble (103450 cell), bezel + dome grille on the -x end, USB-C + power switch
# in an inset back panel on the +x end (Rev B; the stations are in section 1)
# ======================================================================================
SX = FS.origin[0]
S_L, S_W, S_H = 64.0, 44.3, 29.8                   # body (the bezel and dome add ~3.8 at the nose)
S_WALL = 1.8
S_SW_H = 5.0                                       # XKB 1TS009 6 x 6 x 5.0 tact switch (Stage 5)
S_PCB_TOP = FS.origin[2]
S_PCB_Z = S_PCB_TOP - FS.thickness
sxy = lambda name: tuple(r4(v) for v in FS.to_enclosure(FS.feature(name))[:2])
S_MIC, S_LED, S_BTN, S_USB = sxy("mic"), sxy("status_led"), sxy("button"), sxy("usb")
S_BTN2, S_BARLED = sxy("button_2"), sxy("bar_led")   # Rev B snooze bar: front tact and the RGB LED under the bar
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
R_LENS, R_LENS_R = 18.4, 5.6                       # lens window
R_STEP = (20.4, 6.6, 0.6)                          # bezel step round the lens: size, corner radius, depth
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
LUG_Y, LUG_Z = 21.4, 4.6                           # spring-bar centre (Rev A: 22, 5)

for name, val, note in [("sensor_length", S_L, "sensor long side"), ("sensor_width", S_W, "sensor width (>31.7: not a small part)"),
                        ("sensor_height", S_H, "sensor height"), ("sensor_wall", S_WALL, "sensor shell wall"),
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

# ---- 1. sensor shell: a low teardrop pebble (Rev B) ------------------------------------
# Rev B: the outer form is lofted through 14 superellipse cross-sections, each a fit-point spline over a flat base
# line (Rev A used lines and arcs, which read as a rounded box). Stations follow DESIGN.md's side profile, plan and
# front section. The -y side is the side the concept shows (nose to the left in iso.png): it's the fuller one
# and carries the status light and the main swoosh.
# All sensor numbers below are relative to SX (x forward = -x, the grille end).
# (x, height, half-width +y, half-width -y, z of the widest point, exponent +y, exponent -y, lower exponent, lower stretch)
S_STATIONS = [
    (-35.00, 27.8, 13.6, 13.8, 14.0, 2.2, 2.2, 2.3, 1.04),
    (-34.36, 28.6, 15.9, 16.3, 13.4, 2.2, 2.3, 2.5, 1.07),
    (-33.08, 29.2, 17.8, 18.6, 12.8, 2.2, 2.4, 2.8, 1.10),
    (-31.16, 29.5, 19.1, 20.0, 12.1, 2.2, 2.5, 3.2, 1.15),
    (-27.32, 29.7, 20.4, 21.3, 11.3, 2.2, 2.6, 3.6, 1.20),
    (-20.92, 29.8, 21.0, 22.2, 10.7, 2.2, 2.7, 4.0, 1.25),
    (-11.96, 29.6, 21.1, 22.6, 10.3, 2.2, 2.7, 4.0, 1.25),
    (-1.72, 29.0, 21.2, 22.7, 10.0, 2.2, 2.7, 4.0, 1.25),
    (7.88, 27.8, 21.2, 22.6, 10.0, 2.2, 2.7, 4.0, 1.25),
    (16.20, 26.1, 21.0, 22.4, 10.0, 2.2, 2.7, 4.0, 1.25),
    (21.96, 24.8, 20.7, 22.1, 9.8, 2.2, 2.7, 4.0, 1.25),
    (25.80, 23.8, 20.1, 21.4, 9.6, 2.3, 2.6, 3.8, 1.25),
    (27.72, 23.1, 18.7, 19.8, 9.4, 2.3, 2.5, 3.4, 1.22),
    (29.00, 22.6, 16.8, 17.6, 9.2, 2.3, 2.4, 3.0, 1.18),
]
NOSE_X, BACK_X = S_STATIONS[0][0], S_STATIONS[-1][0]
GZ, COLLAR_R, COLLAR_RI = 14.2, 12.0, 10.8              # grille axis height, chrome bezel ring outer / inner radius
DOME_H = 2.8                                            # how far the honeycomb dome bulges past the bezel
S_K = 5                                                 # spline points per quarter section (more = heavier surfaces, slower booleans)
S_RECESS = (2.2, 0.6)                                   # back panel: inset from the back cap's outline, depth


def se_pt(a, b, n, t):
    co, si = math.cos(t), math.sin(t)
    return a * math.copysign(abs(co) ** (2 / n), co), b * math.copysign(abs(si) ** (2 / n), si)


def st_at(x):
    """Station parameters at x, interpolated linearly between the table's stations."""
    for a, b in zip(S_STATIONS, S_STATIONS[1:]):
        if a[0] <= x <= b[0]:
            t = (x - a[0]) / (b[0] - a[0])
            return tuple(a[k] + t * (b[k] - a[k]) for k in range(len(a)))
    raise ValueError(x)


def s_outline(st, inset=0.0, z_bot=0.0, k=S_K):
    """A section's outline (y, z): from the +y base over the crown to the -y base (the base line closes it).
    inset shrinks the half-widths and the top: an approximate wall offset (solid.shell can't offset a loft)."""
    _, h, wp, wn, zc, n_p, n_n, nlow, flow = st
    bt, bl = h - zc - inset, zc * flow

    def side(a, n):
        tb = -math.asin(min(1.0, ((zc - z_bot) / bl) ** (nlow / 2)))
        low = [se_pt(a, bl, nlow, tb * (1 - i / k)) for i in range(k)]
        up = [se_pt(a, bt, n, (math.pi / 2) * i / k) for i in range(k + 1)]
        return [(y, zc + z) for y, z in low + up]
    p = side(wp - inset, n_p)
    m = [(-y, z) for y, z in side(wn - inset, n_n)]
    pts = p + m[::-1][1:]
    pts[0], pts[-1] = (pts[0][0], z_bot), (pts[-1][0], z_bot)
    return pts


def half_width(pts, z, sgn):
    """Half-width of an outline at height z on the +y (sgn 1) or -y (sgn -1) side."""
    best = 0.0
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        if z0 != z1 and (z0 - z) * (z1 - z) <= 0:
            y = y0 + (y1 - y0) * (z - z0) / (z1 - z0)
            if y * sgn > 0:
                best = max(best, abs(y))
    return best


def inside(pts, y, z):
    """Point-in-polygon for a closed outline (the base line closes it)."""
    n, c = len(pts), False
    for i in range(n):
        (y0, z0), (y1, z1) = pts[i], pts[(i + 1) % n]
        if (z0 > z) != (z1 > z) and y < y0 + (y1 - y0) * (z - z0) / (z1 - z0):
            c = not c
    return c


def top_z(x, inset=0.0): return st_at(x)[1] - inset


# cavity sections: the outer ones inset by the wall; the end ones shrink a little more to follow the round-over
w = S_WALL
S_CAVITY = [(NOSE_X + w, 1.0)] + [(st[0], 0.0) for st in S_STATIONS if NOSE_X + w + 0.8 < st[0] < BACK_X - w - 0.8] + [(BACK_X - w, 1.0)]
cav = [(x, s_outline(st_at(x), inset=w + extra, z_bot=-1.0)) for x, extra in S_CAVITY]
# checks: the 103450 cell, the board and its tallest parts clear the cavity; walls are thick enough; the grille,
# USB-C and slider openings sit inside the faces they're cut in
cw, cl, ch = S_CELL_WLH
for xx in (S_CELL[0] - SX - cw / 2, S_CELL[0] - SX, S_CELL[0] - SX + cw / 2):
    o = s_outline(st_at(xx), inset=w, z_bot=-1.0)
    for zz in (S_WALL + 0.1, S_WALL + 0.1 + ch):
        for sg in (1, -1):
            assert half_width(o, zz, sg) > cl / 2 + 0.3, f"cell hits the sensor's side wall at x {xx}, z {zz}"
for xx in (-26.0, 0.0, 26.0):
    o = s_outline(st_at(xx), inset=w, z_bot=-1.0)
    for zz in (S_PCB_Z, S_PCB_TOP + 3.3):
        for sg in (1, -1):
            assert half_width(o, zz, sg) > FS.size[1] / 2 + 0.3, f"board hits the side wall at x {xx}"
for st in [st for st in S_STATIONS if any(abs(st[0] - x) < 1e-9 for x, _ in S_CAVITY)]:
    o, i_ = s_outline(st, k=40), s_outline(st, inset=w, z_bot=-1.0)
    for y, z in i_:
        if z > S_WALL:
            assert min(math.hypot(y - oy, z - oz) for oy, oz in o) > 1.15, f"sensor wall under 1.15 mm at x {st[0]}"   # (1.8 nominal; ~1.2 where the side tucks under, just above the base)
nose = s_outline(S_STATIONS[0])
for ang in range(0, 360, 10):
    assert inside(nose, (COLLAR_R + 0.5) * math.cos(math.radians(ang)), GZ + (COLLAR_R + 0.5) * math.sin(math.radians(ang))), "bezel leaves the nose face"
assert GZ - COLLAR_R > S_WALL + 0.2, "bezel runs into the base"
back = s_outline(S_STATIONS[-1])
for y, z in [(S_USB[1] - 4.8 - 1.0, S_USB_Z + 1.9 + 1.0), (S_USB[1] + 4.8 + 1.0, S_USB_Z + 1.9 + 1.0),
             (S_PSW[1] + 4.0, SL_Z1 + 1.0), (S_PSW[1] - 4.0, SL_Z1 + 1.0)]:
    assert inside(back, y, z), "USB-C / slider opening leaves the back face"

stage("sensor shell")
def s_section(name, x, pts):
    c("sketch.create", plane=yz_plane(SX + x), name=name)
    c("sketch.spline.fit_point", points=[P(y, z) for y, z in pts])
    c("sketch.line", points=[P(*pts[-1]), P(*pts[0])])
    c("sketch.finish")
for k, st in enumerate(S_STATIONS):
    s_section(f"Sensor Section {k}", st[0], s_outline(st))
c("solid.loft", sections=[{"sketch": f"Sensor Section {k}"} for k in range(len(S_STATIONS))], operation="new",
  name="Sensor Body", body_name="Sensor Upper")
# a 1.8 mm base slab (the dark foot). Bodies get their final names when they're made: renaming one after the heavy
# booleans took ~3 min per rename (it re-evaluates the features that name it)
c("solid.split_body", body="Sensor Upper", plane={"origin": [SX, 0, S_WALL], "normal": [0, 0, 1]})
c("body.rename", body="Sensor Upper (1)", name="Sensor Base")

# status light: a kidney bean on the -y cheek just behind the bezel (the concept's green bean). The pipe is the bean
# pushed through the wall and clipped to the outer skin, so it sits flush; a bar under the top wall carries the light
# across from the board's LED (on the +y half of the board).
BEAN = [(-26.9, 10.8), (-27.8, 14.6), (-26.9, 18.4)]           # bean centreline (x rel SX, z), bowed toward the nose
BEAN_HW = 1.15
def bean_pts(k=8):
    (x0, z0), (x1, z1), (x2, z2) = BEAN
    cen = lambda t: ((1 - t) ** 2 * x0 + 2 * t * (1 - t) * x1 + t * t * x2, (1 - t) ** 2 * z0 + 2 * t * (1 - t) * z1 + t * t * z2)
    def nrm(t):
        dx = 2 * (1 - t) * (x1 - x0) + 2 * t * (x2 - x1); dz = 2 * (1 - t) * (z1 - z0) + 2 * t * (z2 - z1)
        L = math.hypot(dx, dz); return dz / L, -dx / L, dx / L, dz / L
    side_a, side_b = [], []
    for i in range(k + 1):
        t = i / k; (cx, cz), (nx, nz, tx, tz) = cen(t), nrm(t)
        side_a.append((cx + nx * BEAN_HW, cz + nz * BEAN_HW)); side_b.append((cx - nx * BEAN_HW, cz - nz * BEAN_HW))
    caps = []
    for t, s in ((1.0, 1), (0.0, -1)):
        (cx, cz), (nx, nz, tx, tz) = cen(t), nrm(t)
        caps.append((cx + s * tx * BEAN_HW, cz + s * tz * BEAN_HW))
    return side_a + [caps[0]] + side_b[::-1] + [caps[1]]
BEAN_Y0 = -(FS.size[1] / 2 + 0.5)                               # the pipe starts 0.5 outside the board's -y edge
XZ_AT = lambda y: {"origin": [0, r4(y), 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}   # normal -y
c("sketch.create", plane=XZ_AT(BEAN_Y0), name="Status Bean")
c("sketch.spline.fit_point", points=[P(SX + x, z) for x, z in bean_pts()], periodic=True)
c("sketch.finish")
c("solid.extrude", distance=30, operation="new", name="Status Bean", body_name="Sensor Light Pipe")
c("solid.combine", target="Sensor Light Pipe", tools=["Sensor Upper"], operation="intersect", keep_tools=True, name="Bean To Skin")

if not BLOCKOUT:
    # hollow: an inset loft, with the board posts (and their heat-stake pins) taken out of it first, so they stay
    # behind in the shell, running exactly from the inside of the top wall down to the board
    for k, (x, pts) in enumerate(cav):
        s_section(f"Sensor Cavity {k}", x, pts)
    c("solid.loft", sections=[{"sketch": f"Sensor Cavity {k}"} for k in range(len(cav))], operation="new",
      name="Sensor Cavity", body_name="Sensor Cavity")
    c("sketch.create", **XY(S_PCB_TOP), name="Sensor Posts")
    for px, py in S_POSTS:
        c("sketch.circle.center", center=P(px, py), radius=1.8)
    c("sketch.finish")
    c("solid.extrude", distance=r4(40 - S_PCB_TOP), operation="cut", targets=["Sensor Cavity"], name="Sensor Posts", profiles="all")
    c("sketch.create", **XY(S_PCB_Z - 0.5), name="Sensor Stake Pins")
    for px, py in S_POSTS:
        c("sketch.circle.center", center=P(px, py), radius=0.95)
    c("sketch.finish")
    c("solid.extrude", distance=r4(40 - S_PCB_Z + 0.5), operation="cut", targets=["Sensor Cavity"], name="Sensor Stake Pins", profiles="all")
    c("solid.combine", target="Sensor Upper", tools=["Sensor Cavity"], operation="cut", name="Sensor Hollow")
# the window: a second, unclipped bean prism (cutting with the clipped pipe fails: its face is the shell's own skin)
c("solid.extrude", sketch="Status Bean", distance=30, operation="new", name="Status Window Cutter", body_name="Status Cutter")
c("solid.combine", target="Sensor Upper", tools=["Status Cutter"], operation="cut", name="Status Window")

# back panel: a shallow recess in the flat back cap, inset from its outline (the concept's inset back face)
rec = s_outline(S_STATIONS[-1], inset=S_RECESS[0], z_bot=S_WALL + S_RECESS[0])
c("sketch.create", plane=yz_plane(SX + BACK_X + 1), name="Back Panel")
c("sketch.spline.fit_point", points=[P(y, z) for y, z in rec])
c("sketch.line", points=[P(*rec[-1]), P(*rec[0])])
c("sketch.finish")
c("solid.extrude", distance=r4(1 + S_RECESS[1]), direction="negative", operation="cut", targets=["Sensor Upper"], name="Back Panel")

# openings in flat faces: the bezel in the nose, USB-C and the slider in the back panel, the button on the crown
c("sketch.create", plane=yz_plane(SX + NOSE_X - 7), name="Grille Opening")
c("sketch.circle.center", center=[0, GZ], radius=COLLAR_R + 0.2)
c("sketch.finish")
c("solid.extrude", distance=12, operation="cut", targets=["Sensor Upper"], name="Grille Opening")
if not BLOCKOUT:
    c("sketch.create", plane=yz_plane(SX + 26), name="Sensor USB Opening")
    c("sketch.rectangle.rounded", p0=[S_USB[1] - 4.8, S_USB_Z - 1.9], p1=[S_USB[1] + 4.8, S_USB_Z + 1.9], radius=1.8)
    c("sketch.finish")
    c("solid.extrude", distance=12, operation="cut", targets=["Sensor Upper"], name="Sensor USB Opening")
    c("sketch.create", plane=yz_plane(SX + 26), name="Power Switch Slot")
    sl = SLIDER_W / 2 + SLIDER_TRAVEL / 2 + 0.55          # room for the slider at either end of its travel
    c("sketch.rectangle.rounded", p0=[S_PSW[1] - sl, SL_Z0 - 0.15], p1=[S_PSW[1] + sl, SL_Z1 + 0.15], radius=0.5)
    c("sketch.finish")
    c("solid.extrude", distance=12, operation="cut", targets=["Sensor Upper"], name="Power Switch Slot")
else:   # blockout: the openings drawn as dark insets
    c("sketch.create", plane=yz_plane(SX + BACK_X - S_RECESS[1] - 1.0), name="Sensor USB Opening")
    c("sketch.rectangle.rounded", p0=[S_USB[1] - 4.8, S_USB_Z - 1.9], p1=[S_USB[1] + 4.8, S_USB_Z + 1.9], radius=1.8)
    c("sketch.finish")
    c("solid.extrude", distance=3, operation="cut", targets=["Sensor Upper"], name="Sensor USB Opening")

# Rev B snooze bar: a 30 x 12 clear acrylic bar along the crown, over two tacts in parallel (fit.json button and
# button_2) with an RGB LED under its middle (bar_led), so a sleepy parent can find it in the dark and press it anywhere
BAR_L, BAR_W, BAR_PROUD, BAR_GAP = 30.0, 12.0, 1.0, 0.3
BAR_X = (S_BTN[0] + S_BTN2[0]) / 2                           # centred between the tacts (absolute x)
assert abs(BAR_X - S_BARLED[0]) < 0.5 and abs(S_BTN[1]) < 0.5 and abs(S_BTN2[1]) < 0.5, "bar LED / tacts off the bar's axis"
bar_x0, bar_x1 = BAR_X - BAR_L / 2, BAR_X + BAR_L / 2
assert bar_x0 - SX > NOSE_X + 18 and bar_x1 - SX < BACK_X - 8, "snooze bar runs off the crown"
sw_top = S_PCB_TOP + S_SW_H
c("sketch.create", **XY(sw_top + 1.0), name="Snooze Bar Slot")
c("sketch.slot.overall", p0=P(bar_x0 - BAR_GAP, 0), p1=P(bar_x1 + BAR_GAP, 0), width=BAR_W + 2 * BAR_GAP)
c("sketch.finish")
c("solid.extrude", distance=20, operation="cut", targets=["Sensor Upper"], name="Snooze Bar Slot")

# the swoosh: lavender side panels below an S-curve (one per side, the -y one sweeping higher), with a bright trim
# band 1.5 mm wide along its top edge. Each is the shell intersected with a tool extruded from the curve in the
# side view, kept to |y| > 12 so only the side walls and the back corners change colour. The curves start steeply under the nose: one that
# runs nearly tangent to the base split plane made the cut unreliable. (Posts and the back panel stay in the upper shell.)
S_LEN, S_CROWN = BACK_X - NOSE_X, max(st[1] for st in S_STATIONS)
SWOOSH = {
    -1: [(0.10, -0.14), (0.20, 0.04), (0.35, 0.13), (0.48, 0.25), (0.58, 0.40), (0.67, 0.53), (0.76, 0.60), (0.86, 0.62), (0.95, 0.60), (1.05, 0.55)],
    1: [(0.11, -0.14), (0.22, 0.03), (0.38, 0.11), (0.52, 0.22), (0.62, 0.35), (0.71, 0.47), (0.80, 0.53), (0.90, 0.55), (1.05, 0.52)],
}
TRIM = 1.5
SW_Y0 = 12.0                     # the panels start this far out (at 15 the cutter's flat face ran nearly tangent to the nose's round-over and the cut was refused)
def swoosh_prism(sgn, body, kind):
    """kind 'below': under the swoosh curve; 'band': between it and the curve TRIM higher; 'cutter': under the higher curve."""
    base = [(SX + NOSE_X + xn * S_LEN, zn * S_CROWN) for xn, zn in SWOOSH[sgn]]
    hi = [(x, z + TRIM) for x, z in base]
    c("sketch.create", plane=XZ_AT(sgn * SW_Y0), name=body)
    if kind == "band":
        c("sketch.spline.fit_point", points=[P(*p) for p in hi])
        c("sketch.line", points=[P(*hi[-1]), P(*base[-1])])
        c("sketch.spline.fit_point", points=[P(*p) for p in base[::-1]])
        c("sketch.line", points=[P(*base[0]), P(*hi[0])])
    else:
        pts = base if kind == "below" else hi
        c("sketch.spline.fit_point", points=[P(*p) for p in pts])
        c("sketch.line", points=[P(*pts[-1]), P(pts[-1][0], -5), P(pts[0][0], -5), P(*pts[0])])
    c("sketch.finish")
    c("solid.extrude", distance=30, direction="positive" if sgn < 0 else "negative", operation="new", name=body, body_name=body)
# each piece is cut from the original shell by its own prism, so no boolean meets a face two bodies share (cutting the
# trim with the lavender piece failed for that reason), and each side is done on its own (a two-lump tool body gave
# an empty intersection)
for sgn, suf in ((-1, ""), (1, " R")):
    for body, kind in (("Sensor Swoosh" + suf, "below"), ("Sensor Trim" + suf, "band"), ("Upper Cutter" + suf, "cutter")):
        swoosh_prism(sgn, body, kind)
    for body in ("Sensor Swoosh" + suf, "Sensor Trim" + suf):
        c("solid.combine", target=body, tools=["Sensor Upper"], operation="intersect", keep_tools=True, name=body + " Panel")
c("solid.combine", target="Sensor Upper", tools=["Upper Cutter", "Upper Cutter R"], operation="cut", name="Upper Shell")
for nm in ("Sensor Swoosh", "Sensor Trim"):
    c("solid.combine", target=nm, tools=[nm + " R"], operation="join", name=nm + " Join")

# ---- 2. sensor inside: VHB, bezel + dome grille, button, slider, light pipe ------------------
stage("sensor parts")
c("sketch.create", **XY(0), name="VHB Pad")
c("sketch.rectangle.rounded", p0=[SX - 22, -14], p1=[SX + 22, 14], radius=5)
c("sketch.finish")
c("solid.extrude", distance=0.8, direction="negative", operation="new", name="VHB Pad", body_name="VHB Pad")

# grille: a chrome bezel ring standing 1 mm proud of the nose, filled by a shallow honeycomb dome
XZ0 = {"origin": [0, 0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}
AXIS = {"origin": [SX, 0, GZ], "dir": [1, 0, 0]}
c_in, c_out = SX - 30.0, SX + NOSE_X - 1.0                          # collar: from inside the nose to 1 mm proud of it
c("sketch.create", plane=XZ0, name="Grille Collar Profile")
c("sketch.rectangle.two_point", p0=P(c_out, GZ + COLLAR_RI), p1=P(c_in, GZ + COLLAR_R))
c("sketch.finish")
c("solid.revolve", axis=AXIS, operation="new", name="Grille Collar", body_name="Grille Collar")
c("solid.fillet", body="Grille Collar", edges=[P(c_out, 0, GZ + COLLAR_R), P(c_out, 0, GZ + COLLAR_RI)], radius=0.45, name="Collar Round")
rb_ = COLLAR_RI - 0.1                                               # dome: a spherical cap on the collar's front face
ro = (rb_ ** 2 + DOME_H ** 2) / (2 * DOME_H); ri = ro - 1.0
cc = c_out + (ro - DOME_H)                                          # sphere centre, behind the face
h_i = math.sqrt(ri ** 2 - (cc - c_out) ** 2)
mid = lambda R: (cc - R * math.cos(0.5 * math.asin(rb_ / ro)), GZ + R * math.sin(0.5 * math.asin(rb_ / ro)))
c("sketch.create", plane=XZ0, name="Grille Dome Profile")
c("sketch.arc.three_point", start=P(c_out, GZ + rb_), through=P(*mid(ro)), end=P(cc - ro, GZ))
c("sketch.line", points=[P(cc - ro, GZ), P(cc - ri, GZ)])
c("sketch.arc.three_point", start=P(cc - ri, GZ), through=P(*mid(ri)), end=P(c_out, GZ + h_i))
c("sketch.line", points=[P(c_out, GZ + h_i), P(c_out, GZ + rb_)])
c("sketch.finish")
c("solid.revolve", axis=AXIS, operation="new", name="Grille Dome", body_name="Sensor Grille")
holes, pitch = [], 2.3                                              # honeycomb: hex-packed round holes
for row in range(-6, 7):
    for col in range(-6, 7):
        hy = col * pitch + (pitch / 2 if row % 2 else 0)
        hz = row * pitch * math.sqrt(3) / 2
        if math.hypot(hy, hz) <= min(h_i, rb_) - 1.2:
            holes.append((hy, GZ + hz))
c("sketch.create", plane=yz_plane(cc - ro - 2), name="Grille Holes")
for hy, hz in holes:
    c("sketch.circle.center", center=P(hy, hz), radius=0.8)
c("sketch.finish")
c("solid.extrude", distance=r4(ro + 2 - (cc - c_out) + 0.5), operation="cut", targets=["Sensor Grille"], name="Grille Holes", profiles="all")

# snooze bar ("I'm awake": tap = stop the buzz, hold = test / pair). One clear acrylic part: a cap whose top follows
# the crown (an arc through the crown 1 mm up at its ends and middle) with rounded edges, a flange under the shell
# that follows the same arc lower down, two plunger legs onto the tacts and a light leg down to the RGB LED.
def arc3(pa, pm, pb):
    ux, uy, rr = circ3(pa, pm, pb)
    return lambda x: uy + math.sqrt(rr * rr - (x - ux) ** 2) if uy < pm[1] else uy - math.sqrt(rr * rr - (x - ux) ** 2)
def circ3(p1, p2, p3):
    (ax, ay), (bx_, by_), (cx_, cy_) = p1, p2, p3
    d = 2 * (ax * (by_ - cy_) + bx_ * (cy_ - ay) + cx_ * (ay - by_))
    ux = ((ax * ax + ay * ay) * (by_ - cy_) + (bx_ * bx_ + by_ * by_) * (cy_ - ay) + (cx_ * cx_ + cy_ * cy_) * (ay - by_)) / d
    uy = ((ax * ax + ay * ay) * (cx_ - bx_) + (bx_ * bx_ + by_ * by_) * (ax - cx_) + (cx_ * cx_ + cy_ * cy_) * (bx_ - ax)) / d
    return ux, uy, math.hypot(ax - ux, ay - uy)
crown_pts = [(x, top_z(x - SX) + BAR_PROUD) for x in (bar_x0 - 2, BAR_X, bar_x1 + 2)]
bar_top = arc3(*crown_pts)
FL_TOP = BAR_PROUD + S_WALL + 0.6 + 0.5          # flange top below the bar top: proud + wall + the crown falling sideways + clearance
FL_T, FL_OVER = 0.8, 1.0                         # flange thickness and overhang round the slot
def arc_band(name, off_top, off_bot, body):
    """A body between the bar-top arc lowered by off_top and by off_bot, extruded across y."""
    xs = [bar_x0 - 2, BAR_X, bar_x1 + 2]
    top = [(x, bar_top(x) - off_top) for x in xs]
    c("sketch.create", plane=XZ_AT(15), name=name)
    c("sketch.arc.three_point", start=P(*top[0]), through=P(*top[1]), end=P(*top[2]))
    if off_bot is None:
        c("sketch.line", points=[P(*top[2]), P(xs[2], sw_top), P(xs[0], sw_top), P(*top[0])])
    else:
        bot = [(x, bar_top(x) - off_bot) for x in xs]
        c("sketch.line", points=[P(*top[2]), P(*bot[2])])
        c("sketch.arc.three_point", start=P(*bot[2]), through=P(*bot[1]), end=P(*bot[0]))
        c("sketch.line", points=[P(*bot[0]), P(*top[0])])
    c("sketch.finish")
    c("solid.extrude", distance=30, operation="new", name=name, body_name=body)
def slot_prism(name, grow, body):
    c("sketch.create", **XY(sw_top), name=name)
    c("sketch.slot.overall", p0=P(bar_x0 - grow, 0), p1=P(bar_x1 + grow, 0), width=BAR_W + 2 * grow)
    c("sketch.finish")
    c("solid.extrude", distance=25, operation="new", name=name, body_name=body)
slot_prism("Snooze Bar Cap", 0.0, "Snooze Bar")
arc_band("Snooze Bar Top", 0.0, FL_TOP + FL_T, "Bar Top Tool")    # the cap runs from the crown down to the flange's underside
c("solid.combine", target="Snooze Bar", tools=["Bar Top Tool"], operation="intersect", name="Snooze Bar Crown")
c("solid.fillet", body="Snooze Bar", edges=[P(BAR_X, s_ * BAR_W / 2, bar_top(BAR_X)) for s_ in (1, -1)]
  + [P(x_, 0, bar_top(x_)) for x_ in (bar_x0, bar_x1)], radius=1.8, fit="reduce", name="Snooze Bar Round")
slot_prism("Snooze Bar Flange", BAR_GAP + FL_OVER, "Bar Flange")
arc_band("Snooze Bar Flange Band", FL_TOP, FL_TOP + FL_T, "Bar Flange Tool")
c("solid.combine", target="Bar Flange", tools=["Bar Flange Tool"], operation="intersect", name="Snooze Bar Flange Cut")
c("solid.combine", target="Snooze Bar", tools=["Bar Flange"], operation="join", name="Snooze Bar Flange Join")
for nm, (lx_, ly_), z0, rr in (("Bar Leg Front", S_BTN2, sw_top + BAR_GAP, 1.6), ("Bar Leg Back", S_BTN, sw_top + BAR_GAP, 1.6),
                               ("Bar Light Leg", S_BARLED, S_PCB_TOP + 0.9 + 1.0, 1.5)):   # light leg 1.0 above the LED: more than the travel
    h_ = bar_top(lx_) - FL_TOP - FL_T + 0.3 - z0
    c("solid.cylinder", radius=rr, height=r4(h_), base=P(lx_, ly_, z0), operation="join", targets=["Snooze Bar"], name=nm)
for (px, py) in S_POSTS:                                     # the flange clears the posts (H2 moved to y -9.5 for it)
    assert not (bar_x0 - BAR_GAP - FL_OVER - 1.8 - 0.3 < px < bar_x1 + BAR_GAP + FL_OVER + 1.8 + 0.3
                and abs(py) - 1.8 < BAR_W / 2 + BAR_GAP + FL_OVER + 0.3), "snooze bar flange hits a post"

if not BLOCKOUT:
    # power slider: a cap in the back slot that reaches in over the PCM12's short lever; a notch takes the lever
    sx_in = S_LEVER_TIP - 0.8
    sx_out = SX + BACK_X - S_RECESS[1] + 0.6                    # 0.6 proud of the recessed back panel
    zc_ = (SL_Z0 + SL_Z1) / 2
    c("solid.box", length=r4(sx_out - sx_in), width=SLIDER_W, height=r4(SL_Z1 - SL_Z0), center=P((sx_in + sx_out) / 2, SLIDER_Y, zc_),
      operation="new", body_name="Switch Slider", name="Switch Slider")
    c("solid.box", length=1.0, width=1.7, height=r4(S_PSW_Z + 0.85 - SL_Z0 + 0.5), center=P(sx_in + 0.5, SLIDER_Y, (SL_Z0 - 0.5 + S_PSW_Z + 0.85) / 2),
      operation="cut", targets=["Switch Slider"], name="Slider Lever Notch")
    c("solid.fillet", body="Switch Slider", edges=[P(sx_out, SLIDER_Y + s_ * SLIDER_W / 2, zc_) for s_ in (1, -1)]
      + [P(sx_out, SLIDER_Y + 1.5, zc_ + s_ * (SL_Z1 - SL_Z0) / 2) for s_ in (1, -1)], radius=0.8, name="Slider Round")

    # light pipe, inside: a cap over the board LED and a bar under the top wall across to the bean (x clear of
    # post H1, the mic and the module; z clear of the mic)
    lx, ly = S_LED
    bar_x0, bar_x1 = SX - 29.0, SX - 25.2
    bar_z0, bar_z1 = S_PIPE_BOT, S_PIPE_BOT + 3.0
    c("solid.box", length=r4(lx + 0.9 - bar_x0), width=2.4, height=r4(bar_z1 - bar_z0), center=P((bar_x0 + lx + 0.9) / 2, ly, (bar_z0 + bar_z1) / 2),
      operation="join", targets=["Sensor Light Pipe"], name="Light Pipe Cap")
    c("solid.box", length=r4(bar_x1 - bar_x0), width=r4(ly + 1.2 - BEAN_Y0 + 0.6), height=r4(bar_z1 - bar_z0),
      center=P((bar_x0 + bar_x1) / 2, (ly + 1.2 + BEAN_Y0 - 0.6) / 2, (bar_z0 + bar_z1) / 2),
      operation="join", targets=["Sensor Light Pipe"], name="Light Pipe Bar")
    for (px, py) in S_POSTS:                                     # keep the bar clear of the posts
        assert not (bar_x0 - 1.8 - 0.2 < px < bar_x1 + 1.8 + 0.2 and BEAN_Y0 - 0.6 - 2.0 < py < ly + 1.2 + 2.0), "light pipe hits a post"


# ---- 3. receiver case ----------------------------------------------------------------
stage("receiver case")
# Rev B: a pillow case lofted through rounded-rect sections, so the sides bulge (widest a third of the way up) and
# the top edge rolls over into a flat bezel (Rev A: an extrusion with a 3.5 fillet). Hollowed by an inset loft,
# open at the back for the back plate. The plan stays a 38 mm rounded square with R9 corners at the back plate,
# so the cell, board and back plate fit as in Rev A.
r_in = R_H - R_WALL
R_SECTIONS = [(0.0, 37.6, 8.8), (1.5, 38.0, 9.0), (5.0, 38.6, 9.3), (8.5, 38.4, 9.2), (10.8, 37.0, 8.5),
              (12.0, 35.0, 7.8), (R_H, 32.6, 6.6)]                      # (z, size, corner radius)
R_CAVITY = [(-1.0, 34.8, 7.4), (1.5, 34.8, 7.4), (5.0, 35.4, 7.7), (8.5, 35.2, 7.6), (10.2, 33.6, 7.0), (r_in, 31.0, 6.0)]
assert R_CAVITY[1][1] >= R_S - 2 * R_WALL and R_CAVITY[1][2] >= R_CR - R_WALL - 1e-9, "the back plate no longer fits"
for nm, secs in (("Watch Section", R_SECTIONS), ("Watch Cavity", R_CAVITY)):
    for k, (z, size, cr) in enumerate(secs):
        c("sketch.create", **XY(z), name=f"{nm} {k}")
        c("sketch.rectangle.rounded", p0=P(RX - size / 2, -size / 2), p1=P(RX + size / 2, size / 2), radius=cr)
        c("sketch.finish")
    c("solid.loft", sections=[{"sketch": f"{nm} {k}"} for k in range(len(secs))], operation="new", name=nm, body_name=nm.replace("Section", "Case"))
if not BLOCKOUT:
    c("solid.combine", target="Watch Case", tools=["Watch Cavity"], operation="cut", name="Watch Hollow")
else:
    c("solid.remove", bodies=["Watch Cavity"])

# lugs: four small horns for 20 mm quick-release spring bars, low and tucked close to the case (Rev A's stood out
# 5.6 mm and read as separate horns)
LUG_T = 2.4
for nm, x0 in (("Lugs A", RX - BAND_W / 2 - 0.2 - LUG_T), ("Lugs B", RX + BAND_W / 2 + 0.2)):
    c("sketch.create", plane=yz_plane(x0), name=nm)
    for s in (1, -1):
        y0, y1 = sorted([s * (R_S / 2 - 1.1), s * (LUG_Y + 2.3)])
        c("sketch.rectangle.rounded", p0=P(y0, LUG_Z - 3.0), p1=P(y1, LUG_Z + 3.0), radius=2.5)
    c("sketch.finish")
    c("solid.extrude", distance=LUG_T, operation="new", name=nm, body_name=nm, profiles="all")
c("solid.combine", target="Watch Case", tools=["Lugs A", "Lugs A (2)", "Lugs B", "Lugs B (2)"], operation="join", name="Join Lugs")
c("sketch.create", plane=yz_plane(RX - BAND_W / 2 - LUG_T - 1), name="Spring Bar Holes")
for s in (1, -1):
    c("sketch.circle.center", center=[s * LUG_Y, LUG_Z], radius=0.6)
c("sketch.finish")
c("solid.extrude", distance=BAND_W + 2 * LUG_T + 2, operation="cut", targets=["Watch Case"], name="Spring Bar Holes", profiles="all")

# top: a stepped bezel round the lens (the concept's recessed window), the lens opening, and the link-LED pipe hole
# (+ a boss around the pipe)
c("sketch.create", **XY(R_H - R_STEP[2]), name="Lens Step")
c("sketch.rectangle.rounded", p0=[RX - R_STEP[0] / 2, -R_STEP[0] / 2], p1=[RX + R_STEP[0] / 2, R_STEP[0] / 2], radius=R_STEP[1])
c("sketch.finish")
c("solid.extrude", distance=2, operation="cut", targets=["Watch Case"], name="Lens Step")
assert -R_STEP[0] / 2 - (R_LINK[1] + 0.85) > 0.4, "link LED hole runs into the lens step"
c("sketch.create", **XY(R_H - 3), name="Lens Opening")
c("sketch.rectangle.rounded", p0=[RX - R_LENS / 2, -R_LENS / 2], p1=[RX + R_LENS / 2, R_LENS / 2], radius=R_LENS_R)
c("sketch.finish")
c("solid.extrude", distance=6, operation="cut", targets=["Watch Case"], name="Lens Opening")
if not BLOCKOUT:
    c("sketch.create", **XY(r_in + 0.3), name="Link Pipe Boss")
    c("sketch.circle.center", center=list(R_LINK), radius=1.5)
    c("sketch.finish")
    c("solid.extrude", distance=r4(r_in + 0.3 - (R_PIPE_BOT + 0.6)), direction="negative", operation="join", targets=["Watch Case"], name="Link Pipe Boss")
c("sketch.create", **XY(R_H + 0.5), name="Link Pipe Hole")
c("sketch.circle.center", center=list(R_LINK), radius=0.85)
c("sketch.finish")
c("solid.extrude", distance=r4(R_H + 0.5 - R_PIPE_BOT + 0.3), direction="negative", operation="cut", targets=["Watch Case"], name="Link Pipe Hole")

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

# lens: recessed 0.25 below the bezel, pillowed, with a lighter centre face in a pocket, so its edge reads as the
# concept's glowing magenta ring
LENS_BOT, LENS_TOP = r_in - 0.1, R_H - 0.25
c("sketch.create", **XY(LENS_BOT), name="Lens")
c("sketch.rectangle.rounded", p0=[RX - R_LENS / 2 + 0.1, -R_LENS / 2 + 0.1], p1=[RX + R_LENS / 2 - 0.1, R_LENS / 2 - 0.1], radius=R_LENS_R - 0.1)
c("sketch.finish")
c("solid.extrude", distance=r4(LENS_TOP - LENS_BOT), operation="new", name="Lens", body_name="Watch Lens")
c("solid.fillet", body="Watch Lens", edges=corner_pts(RX, 0, R_LENS - 0.2, R_LENS - 0.2, R_LENS_R - 0.1, LENS_TOP), radius=0.9, name="Lens Pillow")
LF, LF_R = R_LENS - 4.4, R_LENS_R - 1.4                               # lens face: 14 x 14
c("sketch.create", **XY(LENS_TOP - 0.5), name="Lens Face Pocket")
c("sketch.rectangle.rounded", p0=P(RX - LF / 2 - 0.2, -LF / 2 - 0.2), p1=P(RX + LF / 2 + 0.2, LF / 2 + 0.2), radius=LF_R + 0.2)
c("sketch.finish")
c("solid.extrude", distance=1, operation="cut", targets=["Watch Lens"], name="Lens Face Pocket")
c("sketch.create", **XY(LENS_TOP - 0.5), name="Lens Face")
c("sketch.rectangle.rounded", p0=P(RX - LF / 2, -LF / 2), p1=P(RX + LF / 2, LF / 2), radius=LF_R)
c("sketch.finish")
c("solid.extrude", distance=0.35, operation="new", name="Lens Face", body_name="Lens Face")

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
box("S Tact Switch 2", 6, 6, S_SW_H, S_BTN2[0], S_BTN2[1], S_PCB_TOP + S_SW_H / 2)
box("S Bar LED", 2.2, 2.2, 0.9, S_BARLED[0], S_BARLED[1], S_PCB_TOP + 0.45)
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
    "Sensor Upper": "#eef0f5", "Sensor Swoosh": "#b4acdc", "Sensor Trim": "#c8ccd6", "Lens Face": "#f3cdfc", "Sensor Base": "#8f93a6", "VHB Pad": "#d9d9d9",
    "Sensor Grille": "#2c2b35", "Grille Collar": "#c8ccd6", "Snooze Bar": "#e6f2ff", "S Bar LED": "#f4f4f4", "S Tact Switch 2": "#222222", "Sensor Light Pipe": "#7dff63",
    "Watch Case": "#e6e9f0", "Watch Back": "#b9b3d9", "Watch Lens": "#d86cff", "Link Pipe": "#7dff63",
    "Band": "#6e58a8", "Charge Contact +": "#d8b04a", "Charge Contact -": "#d8b04a", "Magnet A": "#4a4a55", "Magnet B": "#4a4a55",
    "S PCB": "#2e7d4f", "R PCB": "#2e7d4f", "S Battery": "#3a3a3a", "R Battery": "#3a3a3a", "R ERM Motor": "#c0c4c8",
    "S Mic": "#c0c4c8", "S Status LED": "#d8ffd0", "S Tact Switch": "#222222", "S USB-C": "#b0b4b8",
    "R Pogo +": "#d8b04a", "R Pogo -": "#d8b04a", "S Power Switch": "#222222", "S Switch Lever": "#222222", "Switch Slider": "#9d8fe0", "R Glow LED": "#f4f4f4", "R Link LED": "#d8ffd0",
}
OPACITY = {"Snooze Bar": 0.55, "Watch Lens": 0.85, "Lens Face": 0.9, "Sensor Light Pipe": 0.85, "Link Pipe": 0.85}
for body, col in COLOURS.items():
    c("appearance.assign", bodies=[body], color=col, **({"opacity": OPACITY[body]} if body in OPACITY else {}))

if __name__ == "__main__":
    upto = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else len(stage_marks)
    end = stage_marks[upto][1] if upto < len(stage_marks) else len(cmds)
    json.dump({"commands": cmds[:end]}, open(os.path.join(here, "model_build.json"), "w"), indent=1)
    print("stages:", [s for s, _ in stage_marks[:upto]], f"({end} commands)")
