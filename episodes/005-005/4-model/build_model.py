"""Smart Bucket Hat (005): the LED band and its electronics pod, as a Solidcraft CLI script (headless).

  python3 build_model.py [--blockout] [--upto N]   writes model_build.json and model_colors.json
  python3 build_model.py --fit                      writes fit_build.json: the same without louvres and pixel tiles,
                                                    saved as fit_model.solidcraft for the fit check (fit.json model.design)
  solidcraft-cli run model_build.json --save model.solidcraft --out model.step --out model.stl

The product is the band a hat maker fuses into an ordinary bucket hat, not the hat (host's call): a tapered oval
pixel screen with fabric piping top and bottom, and a slim pod hidden inside at the back.

Model frame: Z up, the bottom of the band (the brim seam) on z 0. The hat's front is -Y (the sunset), the back
+Y (the pod). See DESIGN.md for the design read (signature features F1-F8, proportions, colours).
"""
import bisect, json, math, os, sys

here = os.path.dirname(os.path.abspath(__file__))
BLOCKOUT = "--blockout" in sys.argv
FIT_ONLY = "--fit" in sys.argv        # the fit check's design: no louvres or pixel tiles (500 bodies far from the board)
UPTO = int(sys.argv[sys.argv.index("--upto") + 1]) if "--upto" in sys.argv else 99

cmds, stage_marks, COLORS = [], [], {}
def c(command, **params):
    cmds.append({"command": command, "params": params})
def stage(name): stage_marks.append((name, len(cmds)))
def r4(v): return round(v, 4)
def P(*v): return [r4(a) for a in v]
def XY(z): return {"plane": "XY", "offset": r4(z)}
SIDE = {"origin": [0, 0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}   # sketch (x, y) = world (x, z), normal -Y

# ---- main numbers (DESIGN.md "Proportions") ---------------------------------------------------------------
A0, B0 = 89.0, 102.0          # screen surface at the brim seam: semi-axes across (X) and front to back (Y)
LEAN = 7.0                    # inward lean of the band (deg)
TN = math.tan(math.radians(LEAN))
CORE = 3.0                    # band thickness behind the screen surface (back skin + flex + LEDs + diffuser)
NR, PITCH = 12, 2.8           # pixel rows, pitch
CORD = 3.0                    # piping cord height
Z_S0 = CORD                   # screen bottom
Z_S1 = CORD + NR * PITCH      # screen top (36.6)
H = Z_S1 + CORD               # band height (39.6)
LOUV, LOUV_W = 0.5, 0.5       # louvre height above the screen surface, louvre width
TILE = (-0.05, 0.2)           # lit tile layer (offset from the screen surface)

def semi(z, d):
    """Semi-axes (across, front-back) of the band's oval at height z, offset d outward from the screen surface."""
    return A0 - z * TN + d, B0 - z * TN + d

def ellipse_sketch(name, z, d):
    a, b = semi(z, d)
    c("sketch.create", **XY(z), name=name)
    c("sketch.ellipse", center=[0, 0], major=P(0, b), minor_radius=r4(a))
    c("sketch.finish")

def ring(body, sections, d_in, z_in, tag, color):
    """A ring: loft through ellipse sections [(z, d), ...], minus the inner loft at offset d_in over z_in."""
    names = []
    for i, (z, d) in enumerate(sections):
        ellipse_sketch(f"{tag} o{i}", z, d)
        names.append({"sketch": f"{tag} o{i}"})
    c("solid.loft", sections=names, operation="new", name=f"{tag} loft", body_name=body)
    ellipse_sketch(f"{tag} i0", z_in[0], d_in)
    ellipse_sketch(f"{tag} i1", z_in[1], d_in)
    c("solid.loft", sections=[{"sketch": f"{tag} i0"}, {"sketch": f"{tag} i1"}], operation="cut", targets=[body],
      name=f"{tag} hollow")
    COLORS[body] = color

# ---- walking round the oval -----------------------------------------------------------------------------
# t = 0 at the front (-Y), increasing towards +X (the wearer's left, the viewer's right from the front).
def at(t, z, d):
    """Point on the oval at angle parameter t, height z, offset d along the oval's normal; and the normal."""
    a, b = semi(z, 0)
    x, y = a * math.sin(t), -b * math.cos(t)
    nx, ny = math.sin(t) / a, -math.cos(t) / b
    n = math.hypot(nx, ny)
    nx, ny = nx / n, ny / n
    return (x + d * nx, y + d * ny), (nx, ny)

class Arc:
    """Arc-length table round the screen surface at height z (s = 0 at the front centre)."""
    def __init__(self, z, n=4000):
        self.z, self.ts, self.s = z, [2 * math.pi * i / n for i in range(n + 1)], [0.0]
        for i in range(n):
            (x0, y0), _ = at(self.ts[i], z, 0)
            (x1, y1), _ = at(self.ts[i + 1], z, 0)
            self.s.append(self.s[-1] + math.hypot(x1 - x0, y1 - y0))
        self.L = self.s[-1]
    def t(self, s):
        s %= self.L
        i = min(bisect.bisect(self.s, s) - 1, len(self.s) - 2)
        f = (s - self.s[i]) / (self.s[i + 1] - self.s[i])
        return self.ts[i] + f * (self.ts[i + 1] - self.ts[i])
    def pt(self, s, d):
        return at(self.t(s), self.z, d)[0]

Z_MID = (Z_S0 + Z_S1) / 2
MID = Arc(Z_MID)
NC = 208                      # columns: 584.6 mm round at mid-height / 208 = 2.81 mm, square with the rows
CP = MID.L / NC               # column pitch along the screen at mid-height
def col_s(k): return k * CP   # column k's centre (k = 0 at the front centre)
def row_z(r): return Z_S1 - (r + 1) * PITCH, Z_S1 - r * PITCH   # row r (0 = top): z range

# ---- the pixel art (DESIGN.md F6, F7): 12 rows x 208 columns, k = 0 at the front centre --------------------
ART_COLORS = {"O": "#ff7a1a", "Y": "#ffc23a", "R": "#ff3b1f", "G": "#39e64a", "M": "#ff3fd2", "V": "#b44dff",
              "B": "#3b7bff", "C": "#29d3ff", "W": "#fff1c9"}
ART_NAMES = {"O": "Sunset Orange", "Y": "Amber", "R": "Sunset Red", "G": "Palm Green", "M": "Hibiscus", "V": "Violet",
             "B": "Blue", "C": "Cyan", "W": "Warm White"}
SUNSET = ["....YYYYY....",       # front centre: the sun setting over the sea, its reflection in the waves
          "..YYYYYYYYY..",
          ".YYYYYYYYYYY.",
          ".OOOOOOOOOOO.",
          "OOOOOOOOOOOOO",
          "RRRRRRRRRRRRR",
          ".............",
          "CCC.COOOC.CCC",
          ".............",
          ".BBB.BOB.BBB.",
          ".............",
          "BB..BBBBB..BB"]
PALM = ["..GGG.GGG..",
        ".GGGGGGGGG.",
        "GG..GYG..GG",
        "G..GGYGG..G",
        "..G..Y..G..",
        ".....Y.....",
        ".....Y.....",
        "....Y......",
        "....Y......",
        "....Y......",
        "...YY......",
        "..YYYY....."]
HIBISCUS = ["...MMM...",
            ".MMMMMMM.",
            "MMMVVVMMM",
            "MMVVYVVMM",
            "MMMVVVMMM",
            ".MMMMMMM.",
            "...M.M...",
            "..G...G.."]
STAR = [".B.", "BBB", ".B."]
FISH = ["....WWWWW....",          # head at the left (facing -k), tail at the right
        "..WWWWWWWWW.W",
        ".W.WWWWWWWWWW",
        "WWWWWWWWWW..W",
        "..WWWWWWW...."]
FONT = {"A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
        "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
        "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
        "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"]}

ART = [["."] * NC for _ in range(NR)]
def put(sprite, k0, r0, mirror=False, color=None):
    for r, line in enumerate(sprite):
        if mirror:
            line = line[::-1]
        for j, ch in enumerate(line):
            if ch not in ".":
                ART[r0 + r][(k0 + j) % NC] = color or ch
def both(sprite, k0, r0):
    """Put a sprite at columns k0.. on the right of the front and its mirror image on the left."""
    w = len(sprite[0])
    put(sprite, k0, r0)
    put(sprite, -k0 - w + 1, r0, mirror=True)

for k in range(42, NC - 41):                  # waves all the way round the sides and back (under the sprites)
    crest = 10 + round(math.sin(2 * math.pi * (k - 42) / 13))
    ART[crest][k] = "C"
    for r in range(crest + 1, NR):
        ART[r][k] = "B"
put(SUNSET, -6, 0)                            # front centre: the sunset, with palms and hibiscus round it
both(STAR, 8, 5)
both(PALM, 13, 0)
both(STAR, 25, 2)
both(HIBISCUS, 29, 2)
both(STAR, 39, 0)
both(FISH, 46, 3)                             # the angler's side: a fish over the waves
both(STAR, 61, 1)
both(PALM, 66, 0)
both(STAR, 80, 4)
text, k = "ALOHA", NC // 2 - 14                # across the back, 29 columns wide
for ch in text:
    put(FONT[ch], k, 1, color="W")
    k += 6
for k in (84, NC - 84 - 1):                   # sparkles either side of the text
    ART[2][k] = "C"
    ART[5][k + (2 if k < NC // 2 else -2)] = "C"

# ======================================================================================================
stage("1 band: screen core and piping cords (F1, F2, F3, F5)")
CORD_C = "#7d735c"                    # the festival hat's weathered fabric
ring("Screen", [(0.0, 0.0), (H, 0.0)], -CORE, (-1.0, H + 1.0), "screen", "#0d1220")
CORD_PROFILE = [(0.0, 0.4), (0.4, 1.5), (0.9, 2.05), (1.5, 2.25), (2.1, 2.05), (2.6, 1.5), (3.0, 0.4)]
ring("Cord Bottom", [(z, d) for z, d in CORD_PROFILE], -0.5, (-1.0, CORD + 1.0), "cord b", CORD_C)
ring("Cord Top", [(Z_S1 + z, d) for z, d in CORD_PROFILE], -0.5, (Z_S1 - 1.0, H + 1.0), "cord t", CORD_C)

# ======================================================================================================
stage("2 louvres: the black pixel grid (F4)")
# Vertical ribs: a comb outline (one closed polygon: a tooth per column boundary, joined by a base inside the
# screen core, which the louvre shell doesn't reach) extruded and intersected with the louvre shell.
ring("Louvre V", [(Z_S0 - 0.4, LOUV), (Z_S1 + 0.4, LOUV)], -0.1, (Z_S0 - 1.4, Z_S1 + 1.4), "louv v", "#040406")
ring("Louvre H", [(Z_S0 - 0.4, LOUV), (Z_S1 + 0.4, LOUV)], -0.1, (Z_S0 - 1.4, Z_S1 + 1.4), "louv h", "#040406")
def comb(name, z, runs, d_in=-3.0, d_out=3.4):
    """XY sketch at z: one polygon with a tooth over each run (s0, s1) of the screen, plus a hole inside the base,
    so the whole comb is a single profile. Teeth follow the curve (a point every half column)."""
    runs = sorted(runs)
    outer, inner = [], []
    s_end = runs[0][0] + MID.L
    for i, (s0, s1) in enumerate(runs):
        n = max(1, int((s1 - s0) / (CP / 2)))
        outer.append(MID.pt(s0, d_in))
        outer += [MID.pt(s0 + (s1 - s0) * j / n, d_out) for j in range(n + 1)]
        outer.append(MID.pt(s1, d_in))
        nxt = runs[i + 1][0] if i + 1 < len(runs) else s_end
        m = int((nxt - s1) / (CP / 2))
        outer += [MID.pt(s1 + (nxt - s1) * j / (m + 1), d_in) for j in range(1, m + 1)]
    inner = [MID.pt(MID.L * j / 400, d_in - 0.4) for j in range(400)]
    pts = []
    for p in (P(*q) for q in outer):           # drop repeats (runs one cell apart, rounding)
        if not pts or math.dist(p, pts[-1]) > 0.02:
            pts.append(p)
    if math.dist(pts[0], pts[-1]) <= 0.02:
        pts.pop()
    c("sketch.create", **XY(z), name=name)
    c("sketch.line", points=pts, closed=True)
    c("sketch.line", points=[P(*p) for p in inner], closed=True)
    c("sketch.finish")
# (the oval leans 7 deg, so a tooth drawn at mid-height still crosses the shell from top to bottom: the shell moves
#  2.1 mm in and out over the screen, so the teeth run from d -3.0 to +3.4 about mid-height)
comb("rib comb", Z_S0 - 0.6, [(col_s(k + 0.5) - LOUV_W / 2, col_s(k + 0.5) + LOUV_W / 2) for k in range(NC)])
c("solid.extrude", sketch="rib comb", distance=r4(Z_S1 - Z_S0 + 1.2), operation="intersect", targets=["Louvre V"],
  name="ribs")
# Horizontal louvres: a comb in the side plane (slabs at the row boundaries, joined by a spine past the band)
zs = [Z_S0 + i * PITCH for i in range(1, NR)]
X_OUT, X_SPINE = A0 + 8, A0 + 12
outline = [[X_SPINE, zs[0] - LOUV_W / 2], [X_SPINE, zs[-1] + LOUV_W / 2]]
for i, z in enumerate(reversed(zs)):
    outline += [[-X_OUT, z + LOUV_W / 2], [-X_OUT, z - LOUV_W / 2]]
    if i + 1 < len(zs):
        outline += [[X_OUT, z - LOUV_W / 2], [X_OUT, list(reversed(zs))[i + 1] + LOUV_W / 2]]
c("sketch.create", plane=SIDE, name="row comb")
c("sketch.line", points=[P(*p) for p in outline], closed=True)
c("sketch.finish")
c("solid.extrude", sketch="row comb", distance=2 * B0 + 20, direction="symmetric", operation="intersect",
  targets=["Louvre H"], name="rows")

# ======================================================================================================
stage("3 pixel art: lit tiles (F6, F7)")
# A tile shell per colour and row would be slow; instead one master shell, and for each (row, colour) a comb prism
# over that row's lit runs, intersected with the master (kept). Runs of lit cells are one tooth: the ribs split them.
ring("Tile Master", [(Z_S0 - 0.4, TILE[1]), (Z_S1 + 0.4, TILE[1])], TILE[0], (Z_S0 - 1.4, Z_S1 + 1.4), "tiles", "#151b2c")
del COLORS["Tile Master"]
TILE_BODIES = {}
K0 = next(k for k in range(NC) if all(ART[r][k] == "." for r in range(NR)))   # scan runs from an empty column,
ORDER = [(K0 + j) % NC for j in range(NC)]                                     # so no run is split at the wrap
def lump_names(name, n):
    """Solidcraft names the n disconnected pieces of a cut or intersect <name>, <name> (1), <name> (2) ..."""
    return [name] + [f"{name} ({i})" for i in range(1, n)]
for r in range(NR):
    z0, z1 = row_z(r)
    for ch in ART_COLORS:
        ks = [K0 + j for j, k in enumerate(ORDER) if ART[r][k] == ch]
        if not ks:
            continue
        runs, start = [], ks[0]
        for a, b in zip(ks, ks[1:] + [None]):
            if b != a + 1:
                runs.append((col_s(start - 0.5), col_s(a + 0.5)))
                start = b
        name = f"{ART_NAMES[ch]} r{r + 1}"
        comb(f"{name} comb", z0 + LOUV_W / 2, runs)
        c("solid.extrude", sketch=f"{name} comb", distance=r4(PITCH - LOUV_W), operation="new", name=f"{name} prism",
          body_name=name)
        c("solid.combine", target=name, tools=["Tile Master"], operation="intersect", keep_tools=True)
        lumps = lump_names(name, len(runs))   # each run comes out as its own body
        c("appearance.assign", bodies=lumps, color=ART_COLORS[ch])
        for b in lumps:
            TILE_BODIES[b] = ART_COLORS[ch]
c("solid.remove", bodies=["Tile Master"])

# ======================================================================================================
stage("4 pod: the hidden brains at the back (F8)")
# A band of the oval inside the screen ring: d -3.8 (0.8 for the crown fabric) to POD_D1, POD_HALF of arc either side
# of the back centre, with round ends. Two sections only (bottom and top, leaning with the band): more sections twisted
# or bulged, and fillets on its curved edges aren't supported, so its edges stay square (it's hidden in the hat).
# Tub z 1.6 -> 37.6 and a 1.2 lid on top (the board and cells drop in from the top).
POD_D0, POD_D1 = -CORE - 0.8, -17.4
POD_HALF = 102.0
POD_Z0, POD_LID, POD_Z1 = 1.2, 37.6, 38.8
POD_WALL = 1.2
def pod_section(name, z, d0, d1, half):
    arc = Arc(z, 2000)
    sb = arc.L / 2                       # the back centre
    rr = (d0 - d1) / 2
    n = 16
    outer = [arc.pt(sb - half + rr + (2 * half - 2 * rr) * j / n, d0) for j in range(n + 1)]
    inner = [arc.pt(sb + half - rr - (2 * half - 2 * rr) * j / n, d1) for j in range(n + 1)]
    c("sketch.create", **XY(z), name=name)
    c("sketch.spline.fit_point", points=[P(*q) for q in outer])
    c("sketch.arc.three_point", start=P(*outer[-1]), through=P(*arc.pt(sb + half, (d0 + d1) / 2)), end=P(*inner[0]))
    c("sketch.spline.fit_point", points=[P(*q) for q in inner])
    c("sketch.arc.three_point", start=P(*inner[-1]), through=P(*arc.pt(sb - half, (d0 + d1) / 2)), end=P(*outer[0]))
    c("sketch.finish")
def pod_loft(tag, z0, z1, d0, d1, half, body=None, op="new", targets=None):
    pod_section(f"{tag} s0", z0, d0, d1, half)
    pod_section(f"{tag} s1", z1, d0, d1, half)
    kw = {"body_name": body} if body else {"targets": targets}
    c("solid.loft", sections=[{"sketch": f"{tag} s0"}, {"sketch": f"{tag} s1"}], operation=op, name=f"{tag} loft", **kw)
pod_loft("pod", POD_Z0, POD_LID, POD_D0, POD_D1, POD_HALF, body="Pod")
pod_loft("pod lid", POD_LID, POD_Z1, POD_D0, POD_D1, POD_HALF, body="Pod Lid")
COLORS["Pod"] = "#26282d"
COLORS["Pod Lid"] = "#2e3035"

# ======================================================================================================
# Engineering inside the form (not in --blockout). Board, posts and features come from ../fit.json.
# ======================================================================================================
sys.path.insert(0, os.path.join(here, "..", "..", "..", "tools", "fit"))
from fitlib import load_fit  # noqa: E402
FIT = load_fit(here)
BX, BY = FIT.x_axis, FIT.y_axis
BN = [BX[1] * BY[2] - BX[2] * BY[1], BX[2] * BY[0] - BX[0] * BY[2], BX[0] * BY[1] - BX[1] * BY[0]]   # top normal
def E(xy, h=0.0): return [r4(v) for v in FIT.to_enclosure(xy, h)]
def bplane(xy=(0, 0), h=0.0, xd=None, yd=None):
    """A sketch plane in the board frame: sketch (x, y) = board (x, y) about xy, normal = the top normal (or as given)."""
    return {"origin": E(xy, h), "x_dir": [r4(v) for v in (xd or BX)], "y_dir": [r4(v) for v in (yd or BY)]}
def offset_d(p):
    """Signed offset of a world point from the screen surface at its height (negative = inside)."""
    z = p[2]
    best = None
    for k in range(2001):
        t = math.pi + (k - 1000) / 1000 * 1.6
        q, nrm = at(t, z, 0)
        dd = math.dist(q, p[:2])
        if best is None or dd < best[0]:
            best = (dd, (p[0] - q[0]) * nrm[0] + (p[1] - q[1]) * nrm[1])
    return best[1]
CAV_D0, CAV_D1 = POD_D0 - POD_WALL, POD_D1 + POD_WALL      # cavity: d -5.0 .. -15.8
STAND_INS = FIT.data["model"]["stand_ins"]

if not BLOCKOUT:
    stage("5 hollow the pod; board stand-ins from fit.json")
    for name, val, note in [("pod_wall", POD_WALL, "pod wall"), ("band_core", CORE, "band thickness behind the screen"),
                            ("pixel_pitch", PITCH, "LED pitch"), ("lean", LEAN, "band lean (deg)")]:
        c("parameters.add", name=name, expression=f"{val} mm" if name != "lean" else f"{val} deg", comment=note)
    pod_loft("pod cavity", POD_Z0 + POD_WALL, POD_LID + 0.5, CAV_D0, CAV_D1, POD_HALF - POD_WALL, op="cut",
             targets=["Pod"])
    TH = FIT.thickness
    W, Hb = FIT.data["board"]["size"]
    CR = FIT.data["board"].get("corner_r", 3)
    c("sketch.create", plane=bplane(h=-TH), name="pcb")
    c("sketch.rectangle.rounded", p0=P(-W / 2, -Hb / 2), p1=P(W / 2, Hb / 2), radius=CR)
    for hx, hy in FIT.holes:
        c("sketch.circle.center", center=P(hx, hy), diameter=FIT.data.get("hole_d", 2.2))
    c("sketch.finish")
    c("solid.extrude", sketch="pcb", distance=TH, operation="new", name="pcb ext", body_name="PCB")
    COLORS["PCB"] = "#1f5a3a"
    mx, my = FIT.feature("module")
    c("sketch.create", plane=bplane(), name="xiao")
    c("sketch.rectangle.rounded", p0=P(mx - 8.9, my - 10.5), p1=P(mx + 8.9, my + 10.5), radius=1.0)
    c("sketch.finish")
    c("solid.extrude", sketch="xiao", distance=0.8, operation="new", name="xiao ext", body_name="XIAO")
    c("sketch.create", plane=bplane(h=0.8), name="xiao shield")
    c("sketch.rectangle.rounded", p0=P(mx - 6, my + 10.5 - 15.5), p1=P(mx + 6, my + 10.5 - 3.5), radius=0.5)
    c("sketch.finish")
    c("solid.extrude", sketch="xiao shield", distance=1.6, operation="join", targets=["XIAO"], name="xiao shield ext")
    COLORS["XIAO"] = "#22324f"
    # USB-C shell: 8.94 x 3.2 stadium, 7.35 deep, overhanging the board's bottom edge by 1.2 (as the kit's stand-in)
    ux, uy = FIT.feature("usb")
    USB_PLANE = lambda y, h=0.0: {"origin": E((ux, y), h), "x_dir": [r4(v) for v in BN], "y_dir": [r4(v) for v in BX]}
    c("sketch.create", plane=USB_PLANE(uy - 1.2), name="usb shell")
    c("sketch.slot.center_to_center", p0=P(2.4, -2.87), p1=P(2.4, 2.87), width=3.2)
    c("sketch.finish")
    c("solid.extrude", sketch="usb shell", distance=7.35, operation="new", name="usb shell ext", body_name="XIAO USB-C")
    COLORS["XIAO USB-C"] = "#c8cbcf"
    # JST PH side-entry plugs (S3B-PH-SM4-TB, ~7.6 deep x 9.9 x 4.8), mouths flush with the board's side edges
    for key, body, sx in (("plug_a", "Plug A", -1), ("plug_b", "Plug B", 1)):
        px, py = FIT.feature(key)
        c("sketch.create", plane=bplane(), name=body.lower())
        c("sketch.rectangle.two_point", p0=P(px, py - 4.95), p1=P(px - sx * 7.6, py + 4.95))
        c("sketch.finish")
        c("solid.extrude", sketch=body.lower(), distance=4.8, operation="new", name=body.lower() + " ext", body_name=body)
        COLORS[body] = "#f2efe6"
    bx_, by_ = FIT.feature("button")
    c("sketch.create", plane=bplane(), name="button sw")
    c("sketch.rectangle.two_point", p0=P(bx_ - 2.9, by_ - 1.9), p1=P(bx_ + 2.9, by_ + 1.9))
    c("sketch.finish")
    c("solid.extrude", sketch="button sw", distance=2.5, operation="new", name="button sw ext", body_name="Button SW")
    COLORS["Button SW"] = "#3a3a3a"

    stage("6 cells, posts, openings, button")
    # Cells: 6 x 34 x 50 LiPo pouches, flat chords in the wings, ends 0.4 off the cavity's outer face, centred
    # CELL_S of arc either side of the back centre, leaning with the band
    CELL_S, CELL = 68.0, (50.0, 34.0, 6.0)      # near ends clear of the plugs' mating housings and leads
    zc = FIT.origin[2]
    arc = Arc(zc, 4000)
    for sgn, body in ((-1, "Cell A"), (1, "Cell B")):
        s = arc.L / 2 + sgn * CELL_S
        t = arc.t(s)
        (x, y), (nx, ny) = at(t, zc, 0)
        tx, ty = -ny, nx
        def worst(D):
            return max(offset_d((x - nx * D + tx * e, y - ny * D + ty * e, zc)) for e in (-CELL[0] / 2, CELL[0] / 2))
        lo, hi = 0.0, 20.0
        for _ in range(40):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if worst(m) > CAV_D0 - 0.8 else (lo, m)
        D = hi
        up = [-TN * nx / math.hypot(1, TN), -TN * ny / math.hypot(1, TN), 1 / math.hypot(1, TN)]   # up the lean
        org = [x - nx * D, y - ny * D, zc]
        c("sketch.create", plane={"origin": P(*org), "x_dir": P(tx, ty, 0), "y_dir": P(*up)}, name=body.lower())
        c("sketch.rectangle.rounded", p0=P(-CELL[0] / 2, -CELL[1] / 2), p1=P(CELL[0] / 2, CELL[1] / 2), radius=1.5)
        c("sketch.finish")
        nrm = (ty * up[2] - 0, 0 - tx * up[2], tx * up[1] - ty * up[0])          # x_dir x y_dir
        inward = nrm[0] * -nx + nrm[1] * -ny > 0
        c("solid.extrude", sketch=body.lower(), distance=CELL[2], direction="positive" if inward else "negative",
          operation="new", name=body.lower() + " ext", body_name=body)
        COLORS[body] = "#b9bcc2"
        CELL_INNER = -D - CELL[2]
    # Posts from the cavity's outer face to the board's bottom face (the board sits on them), heat-stake pins
    # through the screw holes. Each post runs along the board normal into the outer wall.
    for i, (hx, hy) in enumerate(FIT.holes + FIT.rests):
        p0 = FIT.to_enclosure((hx, hy), -TH)
        reach = -offset_d(p0) + CAV_D0 + 0.8          # to 0.8 inside the outer wall (along the normal ~ along d)
        base = [r4(p0[k] - BN[k] * reach) for k in range(3)]
        c("solid.cylinder", diameter=4.2, height=r4(reach), base=base, axis=[r4(v) for v in BN], operation="join",
          targets=["Pod"], name=f"post {i + 1}")
        if i < len(FIT.holes):
            c("solid.cylinder", diameter=1.9, height=r4(TH + 0.6), base=[r4(v) for v in p0], axis=[r4(v) for v in BN],
              operation="join", targets=["Pod"], name=f"stake {i + 1}")
    # USB-C opening through the bottom wall, along the receptacle's axis: 9.6 x 4.0 stadium
    c("sketch.create", plane=USB_PLANE(uy - 6.0), name="usb opening")
    c("sketch.slot.center_to_center", p0=P(2.4, -2.8), p1=P(2.4, 2.8), width=4.0)
    c("sketch.finish")
    c("solid.extrude", sketch="usb opening", distance=7.0, operation="cut", targets=["Pod"], name="usb opening cut")
    # Mic: seven hex holes in the inner face over the XIAO (felt on the inside); hexagons, not circles (curved wall)
    c("sketch.create", plane=bplane(h=4.4), name="mic holes")
    for ddx, ddy in [(0, 0)] + [(1.9 * math.cos(math.radians(a)), 1.9 * math.sin(math.radians(a))) for a in range(30, 390, 60)]:
        c("sketch.polygon.inscribed", center=P(mx + ddx, my + ddy), radius=0.6, sides=6)
    c("sketch.finish")
    c("solid.extrude", sketch="mic holes", distance=6, operation="cut", targets=["Pod"], name="mic cut")
    # MODE button: an octagonal TPU key through the inner face, with a flange inside, 0.2 above the PTS810
    face_h = offset_d(FIT.to_enclosure((bx_, by_), 0)) - POD_D1           # height of the pod's inner face above the top face
    c("sketch.create", plane=bplane(h=3.6), name="button hole")
    c("sketch.polygon.inscribed", center=P(bx_, by_), radius=3.3, sides=8, angle=22.5)
    c("sketch.finish")
    c("solid.extrude", sketch="button hole", distance=r4(face_h), operation="cut", targets=["Pod"], name="button hole cut")
    c("sketch.create", plane=bplane(h=2.7), name="button flange")
    c("sketch.polygon.inscribed", center=P(bx_, by_), radius=4.4, sides=8, angle=22.5)
    c("sketch.finish")
    c("solid.extrude", sketch="button flange", distance=0.7, operation="new", name="button flange ext", body_name="Mode Key")
    c("sketch.create", plane=bplane(h=3.3), name="button key")
    c("sketch.polygon.inscribed", center=P(bx_, by_), radius=2.95, sides=8, angle=22.5)
    c("sketch.finish")
    c("solid.extrude", sketch="button key", distance=r4(face_h - 3.3 + 0.5), operation="join", targets=["Mode Key"],
      name="button key ext")
    COLORS["Mode Key"] = "#ff7a1a"
    # Lead exits: the band halves' leads leave the plugs sideways, then go out through the outer wall into the band
    for key, sx in (("plug_a", -1), ("plug_b", 1)):
        px, py = FIT.feature(key)
        c("sketch.create", plane=bplane((px + sx * 4.5, py), -TH - 1.5), name=f"{key} exit")
        c("sketch.polygon.inscribed", center=[0, 0], radius=2.3, sides=8, angle=22.5)
        c("sketch.finish")
        c("solid.extrude", sketch=f"{key} exit", distance=8, direction="negative", operation="cut", targets=["Pod"],
          name=f"{key} exit cut")
    FACE_H, CELL_IN = face_h, CELL_INNER

COLORS.update(TILE_BODIES)
n_stage = len(stage_marks)
cut = stage_marks[UPTO][1] if UPTO < n_stage else len(cmds)
out = cmds[:cut]
if FIT_ONLY:
    out = cmds[:stage_marks[1][1]] + cmds[stage_marks[3][1]:cut]
for body in ("Screen", "Cord Bottom", "Cord Top", "Louvre V", "Louvre H", "Pod", "Pod Lid", "PCB", "XIAO",
             "XIAO USB-C", "Plug A", "Plug B", "Button SW", "Cell A", "Cell B", "Mode Key"):
    if body in COLORS and any(x["params"].get("body_name") == body for x in out):
        n = {"Louvre V": NC, "Louvre H": NR - 1}.get(body, 1)
        out.append({"command": "appearance.assign", "params": {"bodies": lump_names(body, n), "color": COLORS[body]}})
json.dump({"commands": out}, open(os.path.join(here, "fit_build.json" if FIT_ONLY else "model_build.json"), "w"), indent=1)
json.dump(COLORS, open(os.path.join(here, "model_colors.json"), "w"), indent=1)
print(f"{len(out)} commands, {len(TILE_BODIES)} tile bodies, stages: " + ", ".join(f"{n}@{i}" for n, i in stage_marks))
print("\n".join("".join(row[k] for k in list(range(NC // 2, NC)) + list(range(NC // 2))) for row in ART))
