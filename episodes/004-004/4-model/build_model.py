"""Color-Sensing Aquarium Accent Light (004): Solidcraft CLI script (headless).

  python3 build_model.py [--blockout] [--upto N]   writes model_build.json
  solidcraft-cli run model_build.json --save model.solidcraft --out model.step --out model.stl

Model frame: LED face UP (+Z), back (the side that clips to the lid rail) on z 0. X along the bar, the dome end at -X,
the electronics end at +X. The USB-C side is -Y. In use the bar hangs upside down under the aquarium lid.
See DESIGN.md for the design read (signature features F1-F9, proportions, silhouettes, colours).
"""
import json, math, os, sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "..", "..", "tools", "fit"))
from fitlib import load_fit  # noqa: E402
FIT = load_fit(here)
def fxy(name): return tuple(round(v, 4) for v in FIT.to_enclosure(FIT.feature(name))[:2])
BLOCKOUT = "--blockout" in sys.argv
UPTO = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else 99

cmds, stage_marks = [], []
NEW_OPS = ("solid.extrude", "solid.sphere", "solid.cylinder", "solid.box")
def c(command, **params):
    if command in NEW_OPS and "body_name" in params and "operation" not in params:
        params["operation"] = "new"
    cmds.append({"command": command, "params": params})
def stage(name): stage_marks.append((name, len(cmds)))
def r4(v): return round(v, 4)
def P(*v): return [r4(a) for a in v]
def XY(z): return {"plane": "XY", "offset": r4(z)} if z else {"plane": "XY"}
SIDE = {"origin": [0, 0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}          # sketch (x, y) = world (x, z), normal -Y
def FRONT(x=0.0): return {"origin": [r4(x), 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}   # (y, z), normal +X

# ---- main numbers (DESIGN.md "Proportions") ---------------------------------------------------------------
L_TIP = 150.0          # finial tip at +-150: 300 overall
X_END = 139.4          # body end (plan) at +-X_END
W, T = 26.0, 11.0      # body width, thickness
Z_SPLIT = 6.3          # gunmetal base 0..6.3, brass deck 6.3..11 (concept side view: 57 / 43 %)
DECK_IN = 0.8          # deck inset from the base's sides (the visible parting step)
HW, DHW = W / 2, W / 2 - DECK_IN
Z_AX = T / 2           # finial axis

DOME_X, DOME_A, DOME_H = fxy("dome")[0], 10.4, 9.0       # faceted dome: centre x, base radius, height above its collar
RISER_Z0, RISER_Z1, RISER_R, RISER_TAPER = 9.6, 12.4, 12.4, 20.0   # top r 11.4 > the dome's 10-gon corners
PORT_X = fxy("button")[0]                                  # porthole button (F6)
SLOT_C = (-81.5, 76.5)                           # LED window arc centres (F4)
SLOT_WO, SLOT_WI = 17.0, 13.4                    # bezel outer / diffuser width
N_LED = 12
VIEW_X, VIEW_L, VIEW_W, VIEW_R = fxy("view")[0], 19.0, 16.0, 2.5     # viewing window (F7)
OVAL_X, OVAL_HL, OVAL_W = fxy("color")[0], 3.0, 7.4                    # colour-sensor oval: centre, half centre distance, width
USB_X, USB_Z = fxy("usb")[0], 3.2   # receptacle centre (Stage 5 fit check: z 1.6 .. 4.8)                                   # side USB-C (F9), -Y face

COLORS = {
    "Base": "#3b3d40", "Deck": "#b8863b", "Finial L": "#b8863b",
    "Dome Collar": "#a87a34", "Dome": "#7f4a1c", "Port Boss": "#b8863b", "Port Cap": "#c9a25a", "Port Eye": "#2a2420",
    "LED Bezel": "#c39042", "Diffuser": "#f3eef8", "View Bezel": "#c39042", "View Glass": "#23272b", "View Chip": "#c9c4b8",
    "Oval Bezel": "#c8cbcf", "Oval Lens": "#15181b", "USB Plug": "#b8863b",
}
def pastel(h, k=0.5):
    rgb = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(v + (255 - v) * k):02x}" for v in rgb)
LED_COLORS = ["#ff4fd8", "#c25cff", "#7a6bff", "#4f8dff", "#33c6ff", "#2fe0d0",
              "#3fe08a", "#a6e43c", "#ffe14a", "#ffb23e", "#ff8a3d", "#ff5f7a"]

# ======================================================================================================
stage("1 base: plan x side x front section (F1, F3)")
# Plan: straight long sides + fit-point spline ends (DESIGN.md top plan, half-widths from the left end)
# pass 3: the end is blunt (a cone into the finial collar, ~0.7 of the width), not a point
PLAN = [(0.075, 1.00), (0.064, 0.985), (0.056, 0.95), (0.050, 0.90), (0.045, 0.84), (0.041, 0.785),
        (0.0385, 0.74)]
def plan_end(hw, x_in, sgn):
    """One end of the plan as a spline through (x, +y) ... (x_end, 0) ... (x, -y); sgn -1 = left end.
    The straight sides sit 0.6 outside hw: the front section sets the real width (coincident faces fail booleans)."""
    pts = [(-118.0, hw + 0.6), (-122.0, hw + 0.45)]
    for f, h in PLAN:
        pts.append((f * 300 - 150 + x_in, h * hw))
    pts += [(-X_END + 0.12 + x_in, 0.62 * hw), (-X_END + 0.02 + x_in, 0.35 * hw), (-X_END + x_in, 0.0)]
    full = pts + [(x, -y) for x, y in reversed(pts[:-1])]
    return [P(sgn * -x if sgn > 0 else x, y) for x, y in full] if sgn > 0 else [P(x, y) for x, y in full]

def plan_sketch(name, z, hw, x_in):
    c("sketch.create", **XY(z), name=name)
    left, right = plan_end(hw, x_in, -1), plan_end(hw, x_in, +1)
    c("sketch.spline.fit_point", points=left)
    c("sketch.spline.fit_point", points=right)
    c("sketch.line", points=[left[0], right[0]])
    c("sketch.line", points=[left[-1], right[-1]])
    c("sketch.finish")

def side_sketch(name, top, bot, ends):
    """Side outline: lines along top/bottom, fit-point splines at the ends (ends: left-end points, top to bottom)."""
    c("sketch.create", plane=SIDE, name=name)
    left = [P(x, z) for x, z in ends]
    right = [P(-x, z) for x, z in ends]
    c("sketch.spline.fit_point", points=left)
    c("sketch.spline.fit_point", points=right)
    c("sketch.line", points=[left[0], right[0]])
    c("sketch.line", points=[left[-1], right[-1]])
    c("sketch.finish")

plan_sketch("base plan", -1.0, HW, 0.0)
c("solid.extrude", sketch="base plan", distance=T + 2, name="base plan body", body_name="Base")
BASE_END = [(-120.0, Z_SPLIT), (-130.0, Z_SPLIT), (-134.5, 6.0), (-137.5, 5.0), (-139.2, 3.5), (-139.9, 1.8),
            (-140.3, -0.6)]   # bottom below z 0: the front section sets the underside
side_sketch("base side", Z_SPLIT, 0, BASE_END)
c("solid.extrude", sketch="base side", distance=W + 6, direction="symmetric", operation="intersect",
  targets=["Base"], name="base side cut")
c("sketch.create", plane=FRONT(-160), name="base section")
c("sketch.rectangle.rounded", p0=P(-HW, 0), p1=P(HW, Z_SPLIT + 2.5), radius=1.4)
c("sketch.finish")
c("solid.extrude", sketch="base section", distance=320, operation="intersect", targets=["Base"], name="base section cut")

# ======================================================================================================
stage("2 deck: brass top plate with ramped ends (F3)")
plan_sketch("deck plan", Z_SPLIT - 1, DHW, 0.8)
c("solid.extrude", sketch="deck plan", distance=T - Z_SPLIT + 2, name="deck plan body", body_name="Deck")
# the ramp crosses the section's top (z = T) at ~18 deg: a shallower crossing made the intersect fail (near tangent)
DECK_END = [(-118.0, T + 0.8), (-121.5, T + 0.75), (-123.6, T + 0.5), (-125.4, T), (-127.6, 10.2), (-130.2, 9.15),
            (-133.0, 7.9), (-135.0, 6.95), (-136.6, Z_SPLIT)]   # running it out to -138.2 broke the section intersect
c("sketch.create", plane=SIDE, name="deck side")
left = [P(x, z) for x, z in DECK_END]; right = [P(-x, z) for x, z in DECK_END]
c("sketch.spline.fit_point", points=left); c("sketch.spline.fit_point", points=right)
c("sketch.line", points=[left[0], right[0]]); c("sketch.line", points=[left[-1], right[-1]])
c("sketch.finish")
c("solid.extrude", sketch="deck side", distance=W + 6, direction="symmetric", operation="intersect",
  targets=["Deck"], name="deck side cut")
c("sketch.create", plane=FRONT(-160), name="deck section")
c("sketch.rectangle.rounded", p0=P(-DHW, 1.9), p1=P(DHW, T), radius=2.2)
c("sketch.finish")
c("solid.extrude", sketch="deck section", distance=320, operation="intersect", targets=["Deck"], name="deck section cut")

# ======================================================================================================
stage("3 finials (F2)")
# Turned finial, flattened to an ellipse (the bar is wider than thick): two lofts through elliptical sections.
# (Fillets on elliptical edges aren't supported: "only straight edges can be blended".)
# pass 2: a thin wide flange + base ring (collar), then a narrow neck into a rounded bulb (nub): reads as turned
COLLAR_ST = [(-142.6, 8.2, 4.2), (-142.1, 10.0, 5.0), (-140.9, 10.0, 5.0), (-140.3, 8.6, 4.4), (-138.8, 8.2, 4.2)]
NUB_ST = [(-150.0, 2.6, 1.4), (-149.6, 4.6, 2.5), (-148.7, 5.9, 3.2), (-147.4, 6.2, 3.35), (-146.0, 5.6, 3.0),
          (-144.8, 4.5, 2.45), (-142.3, 4.5, 2.45)]
def ell_loft(tag, stations, body):
    names = []
    for i, (x, a, b) in enumerate(stations):
        n = f"{tag} {i}"
        c("sketch.create", plane=FRONT(x), name=n)
        c("sketch.ellipse", center=P(0, Z_AX), major=P(a, Z_AX), minor_radius=b)
        c("sketch.finish")
        names.append({"sketch": n})
    c("solid.loft", sections=names, operation="new", name=tag + " loft", body_name=body)
ell_loft("finial collar", COLLAR_ST, "Finial L")
ell_loft("finial nub", NUB_ST, "fin nub")
c("solid.combine", target="Finial L", tools=["fin nub"], operation="join")
c("solid.mirror", bodies=["Finial L"], plane="YZ")

# ======================================================================================================
stage("4 dome on its collar (F5) + porthole (F6)")
# pass 2: the concept seats the dome and porthole on a dark gunmetal panel framed by the brass deck
PANEL_L = (-124.5, -93.0, 10.6, 4.0)             # x0, x1, half-width, corner r
c("sketch.create", **XY(T - 0.5), name="panel l")
c("sketch.rectangle.rounded", p0=P(PANEL_L[0], -PANEL_L[2]), p1=P(PANEL_L[1], PANEL_L[2]), radius=PANEL_L[3])
c("sketch.finish")
c("solid.extrude", sketch="panel l", distance=2, operation="cut", targets=["Deck"], name="panel l cut")
c("solid.extrude", sketch="panel l", distance=0.12, operation="new", name="panel l ext", body_name="Panel L")
COLORS["Panel L"] = "#2e3134"
c("sketch.create", **XY(RISER_Z0), name="riser")
c("sketch.circle.center", center=P(DOME_X, 0), radius=RISER_R)
c("sketch.finish")
c("solid.extrude", sketch="riser", distance=RISER_Z1 - RISER_Z0, taper=f"-{RISER_TAPER} deg",
  name="riser ext", body_name="Dome Collar")
R = (DOME_A ** 2 + DOME_H ** 2) / (2 * DOME_H)
ZC = RISER_Z1 + DOME_H - R
# Faceted lens as a polyhedron: rings of planes tangent to the dome's sphere (tapered polygon prisms, intersected)
# plus a small flat crown. Planes only: cutting a real sphere with planes failed (shallow-angle crossing, curved faces).
def facet_ring(name, n, elev_deg, rot, first=False):
    e = math.radians(elev_deg)
    zb = RISER_Z1 - 0.15
    r_in = (R - (zb - ZC) * math.sin(e)) / math.cos(e)
    r_v = r_in / math.cos(math.pi / n)
    dist = min(DOME_H + 2, (r_in - 0.3) / math.tan(e))
    c("sketch.create", **XY(zb), name=name)
    c("sketch.polygon.inscribed", center=P(DOME_X, 0), radius=r4(r_v), sides=n, angle=rot)
    c("sketch.finish")
    if first:
        c("solid.extrude", sketch=name, distance=r4(dist), taper=f"-{elev_deg} deg", operation="new",
          name=name + " ext", body_name="Dome")
    else:
        c("solid.extrude", sketch=name, distance=r4(dist), taper=f"-{elev_deg} deg", operation="intersect",
          targets=["Dome"], name=name + " cut")
facet_ring("facets low", 10, 12, 0, first=True)
facet_ring("facets mid", 10, 38, 18)
facet_ring("facets high", 5, 63, 0)
c("sketch.create", **XY(ZC + 0.975 * R), name="dome crown")
c("sketch.circle.center", center=P(DOME_X, 0), radius=R)
c("sketch.finish")
c("solid.extrude", sketch="dome crown", distance=5, operation="cut", targets=["Dome"], name="crown flat")
# porthole button: boss, cap, dark eye
c("solid.cylinder", diameter=7.6, height=1.5, base=P(PORT_X, 0, T - 0.3), name="port boss", body_name="Port Boss")
c("solid.cylinder", diameter=5.0, height=0.7, base=P(PORT_X, 0, T + 1.1), name="port cap", body_name="Port Cap")
c("solid.cylinder", diameter=2.4, height=0.3, base=P(PORT_X, 0, T + 1.7), name="port eye", body_name="Port Eye")

# ======================================================================================================
stage("5 LED window: bezel, diffuser, 12 rainbow LEDs (F4)")
c("sketch.create", **XY(T - 0.6), name="led window")
c("sketch.slot.center_to_center", p0=P(SLOT_C[0], 0), p1=P(SLOT_C[1], 0), width=SLOT_WI)
c("sketch.finish")
c("solid.extrude", sketch="led window", distance=2, operation="cut", targets=["Deck"], name="led window cut")
c("solid.extrude", sketch="led window", distance=0.5, name="diffuser ext", body_name="Diffuser")
c("sketch.create", **XY(T - 0.2), name="led bezel")
c("sketch.slot.center_to_center", p0=P(SLOT_C[0], 0), p1=P(SLOT_C[1], 0), width=SLOT_WO)
c("sketch.slot.center_to_center", p0=P(SLOT_C[0], 0), p1=P(SLOT_C[1], 0), width=SLOT_WI)
c("sketch.finish")
c("solid.extrude", sketch="led bezel", distance=0.75, operation="new", name="bezel ext", body_name="LED Bezel")
x0, x1 = SLOT_C[0] - 0.5, SLOT_C[1] + 0.5
for i in range(N_LED):
    x = x0 + (x1 - x0) * i / (N_LED - 1)
    pitch = (x1 - x0) / (N_LED - 1)
    ln, dx = (pitch - 0.3, 0.0) if 0 < i < N_LED - 1 else (9.0, 2.5 if i == 0 else -2.5)
    c("solid.box", length=r4(ln), width=10.0, height=0.05, center=P(x + dx, 0, T - 0.1 + 0.025), name=f"glow {i+1}",
      body_name=f"Glow {i+1}")
    c("solid.box", length=4.0, width=4.0, height=0.1, center=P(x, 0, T - 0.05 + 0.05), name=f"lamp {i+1}",
      body_name=f"Lamp {i+1}")
    COLORS[f"Lamp {i+1}"] = LED_COLORS[i]
    COLORS[f"Glow {i+1}"] = pastel(LED_COLORS[i])

# ======================================================================================================
stage("6 electronics end: viewing window + colour-sensor oval (F7), rivets (F8)")
c("sketch.create", **XY(T - 0.8), name="view window")
c("sketch.rectangle.rounded", p0=P(VIEW_X - VIEW_L / 2, -VIEW_W / 2), p1=P(VIEW_X + VIEW_L / 2, VIEW_W / 2), radius=VIEW_R)
c("sketch.finish")
c("solid.extrude", sketch="view window", distance=2, operation="cut", targets=["Deck"], name="view window cut")
c("solid.extrude", sketch="view window", distance=0.5, operation="new", name="view glass ext", body_name="View Glass")
c("solid.box", length=6.5, width=6.5, height=0.1, center=P(VIEW_X + 1.5, 0, T - 0.25), name="view chip",
  body_name="View Chip")
c("sketch.create", **XY(T - 0.2), name="view bezel")
c("sketch.rectangle.rounded", p0=P(VIEW_X - VIEW_L / 2 - 1.4, -VIEW_W / 2 - 1.4),
  p1=P(VIEW_X + VIEW_L / 2 + 1.4, VIEW_W / 2 + 1.4), radius=VIEW_R + 1.4)
c("sketch.rectangle.rounded", p0=P(VIEW_X - VIEW_L / 2, -VIEW_W / 2), p1=P(VIEW_X + VIEW_L / 2, VIEW_W / 2), radius=VIEW_R)
c("sketch.finish")
c("solid.extrude", sketch="view bezel", distance=0.7, operation="new", name="view bezel ext", body_name="View Bezel")
c("sketch.create", **XY(T - 0.6), name="oval")
c("sketch.slot.center_to_center", p0=P(OVAL_X - OVAL_HL, 0), p1=P(OVAL_X + OVAL_HL, 0), width=OVAL_W)
c("sketch.finish")
c("solid.extrude", sketch="oval", distance=2, operation="cut", targets=["Deck"], name="oval cut")
c("solid.extrude", sketch="oval", distance=0.4, operation="new", name="oval lens ext", body_name="Oval Lens")
c("sketch.create", **XY(T - 0.2), name="oval bezel")
c("sketch.slot.center_to_center", p0=P(OVAL_X - OVAL_HL, 0), p1=P(OVAL_X + OVAL_HL, 0), width=OVAL_W + 2.6)
c("sketch.slot.center_to_center", p0=P(OVAL_X - OVAL_HL, 0), p1=P(OVAL_X + OVAL_HL, 0), width=OVAL_W)
c("sketch.finish")
c("solid.extrude", sketch="oval bezel", distance=1.1, operation="new", name="oval bezel ext", body_name="Oval Bezel")
RIVETS = [(87.6, 9.6), (87.6, -9.6)]       # the others gave way to the scrolls (stage 7b)
for i, (x, y) in enumerate(RIVETS):
    c("solid.sphere", radius=1.0, center=P(x, y, T - 0.1), name=f"rivet {i+1}", body_name=f"Rivet {i+1}")
    COLORS[f"Rivet {i+1}"] = "#c9a25a"

# filigree (pass 2): a gear cut-out on each end ramp shows the dark base through the brass, with a brass hub pin,
# flanked by two round holes (the concept's scrollwork, simplified)
GEAR_X, GEAR_RO, GEAR_RI, GEAR_N = 131.6, 4.3, 3.3, 8
c("sketch.create", **XY(Z_SPLIT - 0.3), name="filigree")
for sx in (-1, 1):
    pts = []
    for k in range(GEAR_N * 4):
        a = 2 * math.pi * k / (GEAR_N * 4) + math.pi / (GEAR_N * 4)
        r = GEAR_RO if (k % 4) in (0, 1) else GEAR_RI
        pts.append(P(sx * GEAR_X + r * math.cos(a), r * math.sin(a)))
    c("sketch.line", points=pts, closed=True)
    for sy in (-1, 1):   # hexagons, not circles: a round-hole cut on the ramp failed (curved faces, shallow crossing)
        c("sketch.polygon.inscribed", center=P(sx * (GEAR_X - 1.0), sy * 7.6), radius=1.4, sides=6)
c("sketch.finish")
c("solid.extrude", sketch="filigree", distance=8, operation="cut", targets=["Deck"], name="filigree cut")
for sx, tag in ((-1, "L"), (1, "R")):
    c("solid.cylinder", diameter=2.6, height=2.6, base=P(sx * GEAR_X, 0, Z_SPLIT - 0.2), name=f"gear hub {tag}",
      body_name=f"Gear Hub {tag}")
    COLORS[f"Gear Hub {tag}"] = "#c9a25a"

# ======================================================================================================
stage("7 side: USB-C brass plug (F9)")
c("sketch.create", plane={"origin": [0, -HW - 0.7, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="usb plug")
c("sketch.slot.center_to_center", p0=P(USB_X - 3.6, USB_Z), p1=P(USB_X + 3.6, USB_Z), width=4.6)
c("sketch.finish")
c("solid.extrude", sketch="usb plug", distance=1.2, direction="negative", operation="new", name="usb plug ext",
  body_name="USB Plug")

# ======================================================================================================
stage("7b filigree: art nouveau brasswork (F8, hosts' request)")
# All raised relief or thin dark inlay as their own bodies on flat faces: no booleans into the spline surfaces.
def spiral(cx, cy, r0, r1, a0_deg, turns, sense=-1, n=16):
    a0 = math.radians(a0_deg)
    return [(cx + (r0 + (r1 - r0) * t) * math.cos(a0 + sense * 2 * math.pi * turns * t),
             cy + (r0 + (r1 - r0) * t) * math.sin(a0 + sense * 2 * math.pi * turns * t))
            for t in (k / (n - 1) for k in range(n))]
def wave(x0, x1, yc, amp, lam, step=1.5, phase=0.0):
    n = max(3, int((x1 - x0) / step) + 1)
    return [(x0 + (x1 - x0) * k / (n - 1),
             yc + amp * math.sin(2 * math.pi * ((x1 - x0) * k / (n - 1)) / lam + phase)) for k in range(n)]
def named(body, n, start=1):
    """Names Solidcraft gives n bodies made by one feature: body, body (2), body (3) ..."""
    return [body if k == 1 else f"{body} ({k})" for k in range(start, start + n)]
def thin(name, plane, curves, thickness, height, body, color, n_bodies=None):
    c("sketch.create", **(plane if "plane" in plane else {"plane": plane}), name=name)
    for pts in curves:
        c("sketch.spline.fit_point", points=[P(*p) for p in pts])
    c("sketch.finish")
    c("solid.extrude", sketch=name, thin=True, thickness=thickness, distance=height, operation="new",
      name=name + " ext", body_name=body)
    for b in named(body, n_bodies or 1):
        COLORS[b] = color
BRASS_HI, ETCH = "#c9974a", "#2e2a24"

# (1) the vine on the gunmetal side (-Y face, z 3.2 .. 5.6, above the rail's clip lips): two whiplash waves braided
# (half a wave apart, so they cross and make a chain of eyes) with a brass bead in each eye. Mirrored to +Y below.
SIDE_M = {"origin": [0, -HW + 0.05, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}     # normal -Y: relief grows outward
VZ, VA, VL = 4.4, 0.85, 16.0
RUNS = [(-126.0, -126.0 + VL * 13.25), (112.0, 112.0 + VL * 0.875)]                 # left of the escutcheon, right of it
braid = [wave(x0, x1, VZ, VA, VL, step=1.0, phase=ph) for x0, x1 in RUNS for ph in (0.0, math.pi)]
beads = [x0 + VL * (0.25 + 0.5 * k) for x0, x1 in RUNS for k in range(40) if x0 + VL * (0.25 + 0.5 * k) < x1 - 1.0]
thin("vine wave", SIDE_M, braid, 0.55, 0.4, "Vine", BRASS_HI, n_bodies=2)
c("sketch.create", plane=SIDE_M, name="vine beads")
for x in beads:
    c("sketch.circle.center", center=P(x, VZ), diameter=1.1)
c("sketch.finish")
c("solid.extrude", sketch="vine beads", distance=0.45, operation="new", name="vine curls ext", body_name="Bead")
for bname in named("Bead", len(beads)):
    COLORS[bname] = BRASS_HI
c1, c2 = beads, []
# (2) escutcheon: a horseshoe-arch brass plate round the USB plug (open at the bottom, where the plug runs to the edge)
ESC = [(89.5, 2.4), (90.6, 3.9), (92.3, 4.9), (94.6, 5.6), (97.4, 5.9), (100, 6.1), (102.6, 5.9), (105.4, 5.6),
       (107.7, 4.9), (109.4, 3.9), (110.5, 2.4), (109.6, 1.75), (106.0, 1.6), (100.0, 1.6), (94.0, 1.6), (90.4, 1.75)]
c("sketch.create", plane=SIDE_M, name="escutcheon")
c("sketch.spline.fit_point", points=[P(x - 100 + USB_X, z) for x, z in ESC], periodic=True)
c("sketch.slot.center_to_center", p0=P(USB_X - 3.6, USB_Z), p1=P(USB_X + 3.6, USB_Z), width=4.9)
c("sketch.finish")
c("solid.extrude", sketch="escutcheon", distance=0.4, profiles=[{"point": P(USB_X - 9.0, 3.0)}], operation="new",
  name="escutcheon ext", body_name="Escutcheon")
COLORS["Escutcheon"] = "#b8863b"
# the +Y side gets the same vine and a blank cartouche in the same place
c("solid.mirror", features=["vine wave ext", "vine curls ext", "escutcheon ext"], plane="XZ")
for k in range(2 + len(beads) + 1):    # a feature mirror names its copies Body1, Body2, ... (all brass)
    COLORS[f"Body{k + 1}"] = BRASS_HI

# (3) brass scrolls on the dark panel round the dome and porthole (both sides of the bar's centre line)
ZP = T - 0.5 + 0.12                                   # Panel L's top face
scrolls_l = []
for sy in (1, -1):
    main = [(-106.6, 8.9), (-104.5, 9.5), (-101.5, 9.75), (-98.9, 9.45)] + spiral(-96.4, 7.3, 1.75, 0.5, 150, 1.3)[1:]
    curl = [(-104.5, 9.45)] + spiral(-103.6, 7.6, 1.3, 0.5, 115, 1.1)[1:]
    scrolls_l += [[(x, sy * y) for x, y in main], [(x, sy * y) for x, y in curl]]
# the -Y copies are traced in the same sense as +Y mirrored, which flips the curl's handedness: as drawn in the art
thin("scrolls l", XY(ZP - 0.02), scrolls_l, 0.75, 0.4, "Scrolls L", BRASS_HI, n_bodies=2)
# (4) a matching dark panel round the colour-sensor oval, with scrolls on it
PANEL_R = (109.2, 124.8, 9.8, 3.0)
c("sketch.create", **XY(T - 0.5), name="panel r")
c("sketch.rectangle.rounded", p0=P(PANEL_R[0], -PANEL_R[2]), p1=P(PANEL_R[1], PANEL_R[2]), radius=PANEL_R[3])
c("sketch.finish")
c("solid.extrude", sketch="panel r", distance=2, operation="cut", targets=["Deck"], name="panel r cut")
c("solid.extrude", sketch="panel r", distance=0.12, operation="new", name="panel r ext", body_name="Panel R")
COLORS["Panel R"] = "#2e3134"
scrolls_r = []
for sy in (1, -1):
    main = [(109.9, 6.0), (111.6, 8.3), (114.5, 9.25), (118.0, 9.2), (120.0, 8.75)] + spiral(121.6, 7.3, 1.45, 0.6, 115, 1.2)[1:]
    curl = [(112.4, 8.75)] + spiral(113.1, 7.25, 1.1, 0.6, 120, 1.0, sense=1)[1:]
    scrolls_r += [[(x, sy * y) for x, y in main], [(x, sy * y) for x, y in curl]]
thin("scrolls r", XY(ZP - 0.02), scrolls_r, 0.65, 0.4, "Scrolls R", BRASS_HI, n_bodies=2)
# (5) etched (blackened) wave lines along both long edges of the LED window
etch = [wave(-86.0, 81.0, sy * 9.25, 0.3, 8.35, step=0.8) for sy in (1, -1)]
thin("window etch", XY(T - 0.01), etch, 0.42, 0.05, "Etch", ETCH, n_bodies=2)

# ======================================================================================================
# Engineering inside the form (not in --blockout). Board, posts and features come from ../fit.json.
# ======================================================================================================
FLOOR, WALL, CEIL = 1.2, 1.4, 1.2                # base floor, base side wall, deck top wall
PCB_TOP = FIT.origin[2]; PCB_BOT = PCB_TOP - FIT.thickness
BASE_CAV = (126.0, HW - WALL, 3.0)               # half-length, half-width, corner r
DECK_CAV = (124.6, DHW - WALL, 3.0)
Z_CEIL = T - CEIL
GLASS_Z = Z_CEIL - 0.8                           # windows' flanges sit under the ceiling, 9.0 .. 9.8

def rrect(name, z, hx, hy, r, cx=0.0, cy=0.0, holes=()):
    c("sketch.create", **XY(z), name=name)
    c("sketch.rectangle.rounded", p0=P(cx - hx, cy - hy), p1=P(cx + hx, cy + hy), radius=r)
    for (hx_, hy_), d in holes:
        c("sketch.circle.center", center=P(hx_, hy_), diameter=d)
    c("sketch.finish")
def slot(name, z, cx, hl, w):
    c("sketch.create", **XY(z), name=name)
    c("sketch.slot.center_to_center", p0=P(cx - hl, 0), p1=P(cx + hl, 0), width=w)
    c("sketch.finish")
def circ(name, z, x, y, d):
    c("sketch.create", **XY(z), name=name)
    c("sketch.circle.center", center=P(x, y), diameter=d)
    c("sketch.finish")

if not BLOCKOUT:
    stage("8 hollow: cavities in base and deck, sealing tongue on the deck")
    for name, val, note in [("floor_t", FLOOR, "base floor"), ("wall", WALL, "side walls"), ("ceiling", CEIL, "deck top wall"),
                            ("z_split", Z_SPLIT, "parting line height"), ("bar_thickness", T, "body thickness"),
                            ("bar_width", W, "body width")]:
        c("parameters.add", name=name, expression=f"{val} mm", comment=note)
    rrect("base cavity", FLOOR, BASE_CAV[0], BASE_CAV[1], BASE_CAV[2])
    c("solid.extrude", sketch="base cavity", distance="z_split - floor_t + 1 mm", operation="cut", targets=["Base"],
      name="base cavity cut")
    rrect("deck cavity", Z_SPLIT - 1, DECK_CAV[0], DECK_CAV[1], DECK_CAV[2])
    c("solid.extrude", sketch="deck cavity", distance="bar_thickness - ceiling - z_split + 1 mm", operation="cut",
      targets=["Deck"], name="deck cavity cut")
    # tongue: a 0.75 mm lip under the deck that drops 1 mm into the base (a gasket cord runs round it: NOTES.md)
    c("sketch.create", **XY(Z_SPLIT - 1.0), name="tongue")
    c("sketch.rectangle.rounded", p0=P(-BASE_CAV[0] + 0.05, -BASE_CAV[1] + 0.05), p1=P(BASE_CAV[0] - 0.05, BASE_CAV[1] - 0.05),
      radius=BASE_CAV[2] - 0.05)
    c("sketch.rectangle.rounded", p0=P(-DECK_CAV[0], -DECK_CAV[1]), p1=P(DECK_CAV[0], DECK_CAV[1]), radius=DECK_CAV[2])
    c("sketch.finish")
    c("solid.extrude", sketch="tongue", distance=1.05, operation="join", targets=["Deck"], name="tongue ext")

    stage("9 openings: windows through the deck, sensor hole, porthole plunger, USB-C")
    slot("led thru", GLASS_Z + 0.3, (SLOT_C[0] + SLOT_C[1]) / 2, (SLOT_C[1] - SLOT_C[0]) / 2, SLOT_WI)
    c("solid.extrude", sketch="led thru", distance=1.4, operation="cut", targets=["Deck"], name="led thru cut")
    slot("diffuser body", GLASS_Z, (SLOT_C[0] + SLOT_C[1]) / 2, (SLOT_C[1] - SLOT_C[0]) / 2, SLOT_WI)
    c("solid.extrude", sketch="diffuser body", distance=T - 0.6 - GLASS_Z + 0.01, operation="join", targets=["Diffuser"],
      name="diffuser body ext")
    slot("diffuser flange", GLASS_Z, (SLOT_C[0] + SLOT_C[1]) / 2, (SLOT_C[1] - SLOT_C[0]) / 2, SLOT_WI + 2.4)
    c("solid.extrude", sketch="diffuser flange", distance=0.75, operation="join", targets=["Diffuser"], name="diffuser flange ext")
    rrect("view thru", GLASS_Z + 0.3, VIEW_L / 2, VIEW_W / 2, VIEW_R, cx=VIEW_X)
    c("solid.extrude", sketch="view thru", distance=1.4, operation="cut", targets=["Deck"], name="view thru cut")
    rrect("view glass body", GLASS_Z, VIEW_L / 2, VIEW_W / 2, VIEW_R, cx=VIEW_X)
    c("solid.extrude", sketch="view glass body", distance=T - 0.8 - GLASS_Z + 0.01, operation="join", targets=["View Glass"],
      name="view glass body ext")
    rrect("view flange", GLASS_Z, VIEW_L / 2 + 1.0, VIEW_W / 2 + 1.0, VIEW_R + 1.0, cx=VIEW_X)
    c("solid.extrude", sketch="view flange", distance=0.75, operation="join", targets=["View Glass"], name="view flange ext")
    slot("oval thru", GLASS_Z + 0.3, OVAL_X, OVAL_HL, OVAL_W)
    c("solid.extrude", sketch="oval thru", distance=1.4, operation="cut", targets=["Deck"], name="oval thru cut")
    slot("oval lens body", GLASS_Z, OVAL_X, OVAL_HL, OVAL_W)
    c("solid.extrude", sketch="oval lens body", distance=T - 0.6 - GLASS_Z + 0.01, operation="join", targets=["Oval Lens"],
      name="oval lens body ext")
    slot("oval flange", GLASS_Z, OVAL_X, OVAL_HL, OVAL_W + 1.8)
    c("solid.extrude", sketch="oval flange", distance=0.75, operation="join", targets=["Oval Lens"], name="oval flange ext")
    # dome: a d7 light path from the APDS-9960 up into the lens
    circ("dome hole", GLASS_Z + 0.3, DOME_X, 0, 7.0)
    c("solid.extrude", sketch="dome hole", distance=RISER_Z1 - GLASS_Z - 0.3 - 0.05, operation="cut",
      targets=["Deck", "Panel L", "Dome Collar"], name="dome hole cut")
    # light barrier (Stage 5): a 0.6 rib across the light path, splitting the APDS-9960's IR LED half (-x) from its
    # receiver half (+x), from the deck top down to 0.3 above the sensor. The dome's underside stays flat and clear.
    APDS_TOP = PCB_TOP + 1.35
    RIB_X, RIB_GAP = DOME_X + 0.13, 0.3     # Stage 5: centre of the gap between its windows; 0.3 clear of the package
    c("solid.box", length=0.6, width=7.2, height=T - (APDS_TOP + RIB_GAP), center=P(RIB_X, 0, (T + APDS_TOP + RIB_GAP) / 2),
      operation="join", targets=["Deck"], name="light barrier")
    # porthole: the cap becomes a plunger (stem through the boss, a stop flange under the ceiling)
    circ("port hole", GLASS_Z + 0.3, PORT_X, 0, 5.4)
    c("solid.extrude", sketch="port hole", distance=4.0, operation="cut", targets=["Deck", "Panel L", "Port Boss"],
      name="port hole cut")
    c("solid.cylinder", diameter=4.8, height=T + 1.2 - (PCB_TOP + 2.7), base=P(PORT_X, 0, PCB_TOP + 2.7),
      operation="join", targets=["Port Cap"], name="plunger stem")
    c("solid.cylinder", diameter=7.0, height=0.4, base=P(PORT_X, 0, PCB_TOP + 2.7), operation="join",
      targets=["Port Cap"], name="plunger stop")
    # USB-C: opening through the -Y wall of the base; the brass plug gets a stem that seals in it
    UO = (9.6, 4.0)                              # 0.33 round the 8.94 x 3.2 receptacle; bottom level with the floor
    c("sketch.create", plane={"origin": [0, -HW - 1.0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="usb hole")
    c("sketch.slot.center_to_center", p0=P(USB_X - (UO[0] - UO[1]) / 2, USB_Z), p1=P(USB_X + (UO[0] - UO[1]) / 2, USB_Z),
      width=UO[1])
    c("sketch.finish")
    c("solid.extrude", sketch="usb hole", distance=WALL + 1.6, direction="negative", operation="cut", targets=["Base"],
      name="usb hole cut")
    c("sketch.create", plane={"origin": [0, -HW + 0.4, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="plug stem")
    c("sketch.slot.center_to_center", p0=P(USB_X - (UO[0] - UO[1]) / 2, USB_Z), p1=P(USB_X + (UO[0] - UO[1]) / 2, USB_Z),
      width=UO[1] - 0.3)
    c("sketch.finish")
    c("solid.extrude", sketch="plug stem", distance=0.55, direction="negative", operation="join", targets=["USB Plug"], name="plug stem ext")

    stage("10 board mounting: base posts (M2 from the back), deck bosses, rest post, rail grooves")
    for i, (hx, hy) in enumerate(FIT.holes):
        x, y = FIT.to_enclosure((hx, hy))[:2]
        c("solid.cylinder", diameter=6.0, height=PCB_BOT - FLOOR + 0.3, base=P(x, y, FLOOR - 0.3), operation="join",
          targets=["Base"], name=f"post {i+1}")
        c("solid.cylinder", diameter=4.6, height=Z_CEIL + 0.1 - (PCB_TOP + 0.05), base=P(x, y, PCB_TOP + 0.05),
          operation="join", targets=["Deck"], name=f"boss {i+1}")
    holes = [tuple(FIT.to_enclosure(h)[:2]) for h in FIT.holes]
    c("sketch.create", **XY(-0.5), name="screw clearance")
    for x, y in holes: c("sketch.circle.center", center=P(x, y), diameter=2.4)
    c("sketch.finish")
    c("solid.extrude", sketch="screw clearance", distance=PCB_BOT + 0.5, operation="cut", targets=["Base"], name="screw holes")
    c("sketch.create", **XY(-0.5), name="counterbores")
    for x, y in holes: c("sketch.circle.center", center=P(x, y), diameter=4.2)
    c("sketch.finish")
    c("solid.extrude", sketch="counterbores", distance=2.3, operation="cut", targets=["Base"], name="counterbores cut")
    c("sketch.create", **XY(PCB_TOP + 0.5), name="pilots")
    for x, y in holes: c("sketch.circle.center", center=P(x, y), diameter=1.6)
    c("sketch.finish")
    c("solid.extrude", sketch="pilots", distance=Z_CEIL - PCB_TOP - 0.9, operation="cut", targets=["Deck"], name="pilot holes")
    for i, (rx, ry) in enumerate(FIT.rests):
        x, y = FIT.to_enclosure((rx, ry))[:2]
        c("solid.cylinder", diameter=3.5, height=PCB_BOT - FLOOR + 0.3, base=P(x, y, FLOOR - 0.3), operation="join",
          targets=["Base"], name=f"rest {i+1}")
    RAIL_HX = 82.0
    c("sketch.create", **XY(1.5), name="rail grooves")
    for sy in (-1, 1):
        c("sketch.rectangle.two_point", p0=P(-RAIL_HX, sy * (HW - 0.7)), p1=P(RAIL_HX, sy * (HW + 0.6)))
    c("sketch.finish")
    c("solid.extrude", sketch="rail grooves", distance=1.0, operation="cut", targets=["Base"], name="rail grooves cut")

    stage("11 mounting rail (sticks under the lid) + electronics stand-ins from fit.json")
    RL = RAIL_HX - 2
    rail = [(-14.2, -1.6), (14.2, -1.6), (14.2, 2.4), (12.4, 2.4), (12.4, 1.6), (13.1, 1.6), (13.1, -0.05),
            (-13.1, -0.05), (-13.1, 1.6), (-12.4, 1.6), (-12.4, 2.4), (-14.2, 2.4)]
    c("sketch.create", plane=FRONT(-RL), name="rail section")
    c("sketch.line", points=[P(*p) for p in rail], closed=True)
    c("sketch.finish")
    c("solid.extrude", sketch="rail section", distance=2 * RL, operation="new", name="rail ext", body_name="Mount Rail")
    c("solid.box", length=2 * RL - 4, width=24.0, height=0.8, center=P(0, 0, -2.0), operation="new", name="vhb",
      body_name="VHB Tape")
    COLORS.update({"Mount Rail": "#2b2d30", "VHB Tape": "#d9d4c7"})
    bw, bh = FIT.size
    c("sketch.create", **XY(PCB_BOT), name="pcb")
    c("sketch.rectangle.rounded", p0=P(-bw / 2, -bh / 2), p1=P(bw / 2, bh / 2), radius=FIT.corner_r)
    for x, y in holes: c("sketch.circle.center", center=P(x, y), diameter=FIT.data.get("hole_d", 2.2))
    c("sketch.finish")
    c("solid.extrude", sketch="pcb", distance=FIT.thickness, operation="new", name="pcb ext", body_name="PCB")
    mx, my = fxy("module"); msz = FIT.features["module"]["size"]
    c("solid.box", length=msz[0], width=msz[1], height=1.0, center=P(mx, my, PCB_BOT - 0.5), operation="new",
      name="xiao", body_name="XIAO")
    ux, uy = fxy("usb")
    c("solid.box", length=8.94, width=7.35, height=3.2, center=P(ux, uy - 1.2 + 7.35 / 2, USB_Z),   # mouth 1.2 past the edge
      operation="new", name="xiao usb", body_name="XIAO USB-C")
    for nm, body, (lx, ly, lz) in [("dome", "APDS-9960", (3.94, 2.36, 1.35)), ("color", "APDS-9251", (2.0, 2.0, 0.65)),
                                   ("button", "Button SW", (4.2, 3.2, 2.5))]:
        x, y = fxy(nm)
        c("solid.box", length=lx, width=ly, height=lz, center=P(x, y, PCB_TOP + lz / 2), operation="new",
          name=body.lower(), body_name=body)
    for i in range(12):
        x, y = fxy(f"led{i+1}")
        c("solid.box", length=2.0, width=2.0, height=0.84, center=P(x, y, PCB_TOP + 0.42), operation="new",
          name=f"led {i+1}", body_name=f"LED {i+1}")
        COLORS[f"LED {i+1}"] = "#f2f2f2"
    for i, nm in enumerate(("cell1", "cell2")):
        x, y = fxy(nm); sz = FIT.features[nm]["size"]
        c("solid.box", length=sz[0], width=sz[1], height=4.0, center=P(x, y, FLOOR + 0.1 + 2.0), operation="new",
          name=f"cell {i+1}", body_name=f"Cell {i+1}")
        COLORS[f"Cell {i+1}"] = "#b9c2cc"
        # tab end (FIT.md 5→4): cell1's tabs at its -x end, cell2's at its +x end, under the board's through-hole pads
        sx = -1 if i == 0 else 1
        for ty in (5.5, 1.9):
            c("solid.box", length=3.5, width=2.6, height=0.2, center=P(x + sx * (sz[0] / 2 + 1.5), ty, FLOOR + 0.1 + 2.0),
              operation="join", targets=[f"Cell {i+1}"], name=f"cell {i+1} tab {ty}")
    COLORS.update({"PCB": "#16181b", "XIAO": "#1f2a36", "XIAO USB-C": "#c0c4c8", "APDS-9960": "#141414",
                   "APDS-9251": "#141414", "Button SW": "#4a4a4a"})

# ---- colours, output -----------------------------------------------------------------------------------
n_stage = len(stage_marks)
cut = stage_marks[UPTO][1] if UPTO < n_stage else len(cmds)
out = cmds[:cut]
present = set()
for cm in out:
    bn = cm["params"].get("body_name")
    if bn: present.add(bn)
if any(cm["command"] == "solid.mirror" for cm in out):
    present.add("Finial L (2)"); COLORS["Finial L (2)"] = COLORS["Finial L"]   # the mirror's copy (Solidcraft names it)
out.append({"command": "browser.visibility", "params": {"visible": False, "folder": "sketches"}})
present |= {b for b in COLORS if "(" in b and b.split(" (")[0] in present}
present |= {b for b in COLORS if b.startswith("Body") and any(cm["command"] == "solid.mirror" and "features" in cm["params"] for cm in out)}
for body, col in COLORS.items():
    if body in present:
        out.append({"command": "appearance.assign", "params": {"bodies": [body], "color": col}})
json.dump({"commands": out}, open(os.path.join(here, "model_build.json"), "w"), indent=1)
json.dump({b: COLORS[b] for b in COLORS if b in present}, open(os.path.join(here, "model_colors.json"), "w"), indent=1)
print(f"{len(out)} commands, stages: " + ", ".join(f"{n}@{i}" for n, i in stage_marks))
