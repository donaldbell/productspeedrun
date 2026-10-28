#!/usr/bin/env python3
"""Place the Backpack Defender board (70 x 45 mm, R9 corners, all parts on top).

Run with KiCad's bundled Python (it has the pcbnew module):
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 tools/gen_pcb.py

Reads the netlist exported from the schematic (tools/build.sh writes it). Writes
backpack-defender.kicad_pcb, overwriting it: stop using this once the board is edited by hand.

Coordinates: the enclosure's own XY (4-model/build_model.py): origin at the centre, mm,
+x to the button end, +y to the back (the front grille is at -y). KiCad's page is y-down; to_page() converts.
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import find, find_all, parse  # noqa: E402

import pcbnew  # noqa: E402

HW = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KICAD_FP = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
PROJECT = "backpack-defender"
PCB = os.path.join(HW, PROJECT + ".kicad_pcb")

CX, CY = 100.0, 100.0
BW, BH, BR = 70.0, 45.0, 9.0                     # board outline (Stage 4: 70 x 45, R9)
POSTS = [(sx * 31.0, sy * 17.0) for sx in (-1, 1) for sy in (-1, 1)]
POST_KEEPOUT = 3.0                               # M2 pan head / post top: no parts, no copper
PIR_AT, PIR_R = (-26.0, 13.0), 5.5               # AM312 body (Ø10) above the board: no parts under it
MODULE_AT = (-8.5, 9.0)                          # WROOM-02 pad-field centre; antenna end on the back edge
ANTENNA_KEEPOUT = (-19.5, 15.6, 2.5, 22.6)       # copper-free on both layers
BTN_AT = (18.0, 0.0)                             # big silence button centre (Stage 4 BTN_XY)
PIEZO_AT = (0.0, -14.5)                          # behind the front grille

# Fixed parts: ref -> (x, y, orientation). Footprint origin placed exactly here.
FIXED = {
    "U2": (MODULE_AT[0], MODULE_AT[1], 0),
    "SW1": (BTN_AT[0] - 6.25, BTN_AT[1] + 2.5, 0),       # SW_PUSH-12mm: origin at pad 1, body centre at (6.25, 2.5)
    "BZ1": (PIEZO_AT[0] - 2.5, PIEZO_AT[1], 0),          # PS1240: origin at pad 1, body centre at (2.5, 0)
    "FID1": (-32.0, -10.5, 0),
    "FID2": (27.0, 18.5, 0),
    "FID3": (25.0, -19.5, 0),
}
# Rows of through-hole pads: ref -> (pin-1 x, y, direction of pin 2 from pin 1).
ROWS = {
    "U4": (PIR_AT[0], PIR_AT[1] + 2.54, (0, -1)),        # AM312 legs, VCC / OUT / GND top to bottom
    "J1": (-31.0, -3.0, (0, -1)),                        # battery leads: + on top
    "J2": (30.0, 5.5, (0, -1)),                          # programming pogo pads down the right end
}
ROW_LABELS = {
    "U4": ("PIR", ["V", "O", "G"], "right", (PIR_AT[0] - 3.4, PIR_AT[1])),
    "J1": ("AAA", ["+", "-"], "left"),
    "J2": ("PROG", ["G", "3V3", "D-", "D+", "EN", "IO9"], "right"),
}
# Everything else: preferred spot (x, y, orientation); the auto-fitter moves a part to the nearest
# free spot if needed. Order matters: earlier parts get first pick.
PREFER = [
    # reverse-battery FET and the boost, front-left, over the battery holder's end
    ("Q1", -27.5, -3.4, 90), ("C1", -24.0, -4.5, 90), ("L1", -21.0, -11.5, 0), ("U1", -15.6, -11.0, 0),
    ("C2", -12.6, -9.0, 90), ("C3", -12.6, -13.0, 90), ("R1", -15.6, -14.2, 0), ("R2", -15.6, -16.0, 0),
    # battery sense, between the module and the piezo
    ("R3", -8.5, -3.0, 0), ("R4", -8.5, -4.8, 0), ("C4", -8.5, -6.6, 0),
    # module decoupling at pin 1 (top-left), EN RC and strap pull-ups along the module's left pins
    ("C6", -21.8, 20.0, 0), ("C5", -25.6, 20.0, 0), ("R5", -21.6, 4.0, 90), ("C7", -23.4, 4.0, 90),
    ("R7", -25.2, 4.0, 90), ("R8", -27.0, 4.0, 90), ("R6", 3.0, 12.0, 90), ("R9", 5.0, 5.0, 90),
    # PIR supply filter, left end under the PIR
    ("R10", -32.0, 3.0, 90), ("C8", -29.6, 3.0, 90),
    # amp beside the piezo, its decoupling on the VDD side, series resistors toward the piezo
    ("U3", 12.0, -12.5, 0), ("C10", 15.6, -9.6, 90), ("C9", 17.6, -9.6, 90), ("R11", 9.0, -9.0, 0),
    ("R12", 8.2, -14.2, 90), ("R13", 8.2, -17.4, 90),
    ("TP1", -27.5, -9.5, 0), ("TP3", -27.5, -13.5, 0), ("TP2", 5.0, -4.5, 0),
]


def mm(v):
    return pcbnew.FromMM(v)


def to_page(x, y):
    return pcbnew.VECTOR2I(mm(CX + x), mm(CY - y))


def from_page(p):
    return pcbnew.ToMM(p.x) - CX, CY - pcbnew.ToMM(p.y)


def rounded_rect_pts(w, h, r, n=12):
    """Counter-clockwise outline of a rounded rectangle centred at 0 (board frame)."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def inside_outline(x, y, inset):
    """True if (x, y) is at least `inset` inside the board outline."""
    hx, hy = BW / 2 - BR, BH / 2 - BR
    dx, dy = max(abs(x) - hx, 0), max(abs(y) - hy, 0)
    if dx > 0 and dy > 0:
        return math.hypot(dx, dy) <= BR - inset
    return abs(x) <= BW / 2 - inset and abs(y) <= BH / 2 - inset


def read_netlist(path):
    net = parse(open(path).read())
    comps = {}
    for c in find_all(find(net, "components"), "comp"):
        comps[str(find(c, "ref")[1])] = dict(
            value=str(find(c, "value")[1]),
            footprint=str(find(c, "footprint")[1]),
            uuid=str(find(c, "tstamps")[1]),
            fields={str(find(f, "name")[1]): str(f[2]) for f in find_all(find(c, "fields"), "field")
                    if len(f) > 2 and str(find(f, "name")[1]) in ("LCSC", "MPN", "Description")},
            dnp=any(str(find(p, "name")[1]) == "dnp" for p in find_all(c, "property")))
    nets = {}
    for n in find_all(find(net, "nets"), "net"):
        name = str(find(n, "name")[1])
        nets[name] = [(str(find(x, "ref")[1]), str(find(x, "pin")[1])) for x in find_all(n, "node")]
    return comps, nets


def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(os.path.join(KICAD_FP, lib + ".pretty"), name)
    if fp is None:
        raise RuntimeError("footprint not found: " + fpid)
    fp.SetFPIDAsString(fpid)
    return fp


def pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            return from_page(p.GetPosition())
    raise KeyError(num)


def courtyard_rect(fp):
    """Board-frame bounding box of a footprint's courtyard (pads + 0.3 mm if it has none)."""
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            bb = g.GetBoundingBox()
            xs += [bb.GetLeft(), bb.GetRight()]
            ys += [bb.GetTop(), bb.GetBottom()]
    if not xs:
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            xs += [bb.GetLeft() - mm(0.3), bb.GetRight() + mm(0.3)]
            ys += [bb.GetTop() - mm(0.3), bb.GetBottom() + mm(0.3)]
    (x0, y1), (x1, y0) = from_page(pcbnew.VECTOR2I(min(xs), min(ys))), from_page(pcbnew.VECTOR2I(max(xs), max(ys)))
    return (x0, y0, x1, y1)


def overlaps(a, b, gap=0.1):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def keepouts():
    px, py = PIR_AT
    out = [(px - PIR_R, py - PIR_R, px + PIR_R, py + PIR_R), ANTENNA_KEEPOUT]
    out += [(x - POST_KEEPOUT, y - POST_KEEPOUT, x + POST_KEEPOUT, y + POST_KEEPOUT) for x, y in POSTS]
    return out


def autofit(placed):
    """Put each PREFER part at its spot, or the nearest free spot in a widening spiral."""
    prefer_refs = {r for r, *_ in PREFER}
    occupied = [courtyard_rect(fp) for ref, fp in placed.items() if ref not in prefer_refs and not ref.startswith("H")]
    occupied += keepouts()

    def free(r):
        if not all(inside_outline(x, y, 0.5) for x in (r[0], r[2]) for y in (r[1], r[3])):
            return False
        return not any(overlaps(r, o) for o in occupied)

    for ref, x, y, o in PREFER:
        fp = placed[ref]
        fp.SetOrientationDegrees(o)
        best = None
        for step in range(0, 81):
            d = step * 0.2
            n = 1 if d == 0 else max(8, int(2 * math.pi * d / 0.2))
            for k in range(n):
                a = 2 * math.pi * k / n
                fp.SetPosition(to_page(x + d * math.cos(a), y + d * math.sin(a)))
                r = courtyard_rect(fp)
                if free(r):
                    best = r
                    break
            if best:
                break
        if best is None:
            raise SystemExit("autofit: no room for %s near (%.1f, %.1f)" % (ref, x, y))
        moved = math.hypot(*[a - b for a, b in zip(from_page(fp.GetPosition()), (x, y))])
        if moved > 0.05:
            print("  autofit: %-4s moved %.1f mm" % (ref, moved))
        occupied.append(best)


def place_row(fp, first, step_dir):
    """Rotate a 1xN pad footprint so pin 2 lies in step_dir from pin 1, then put pin 1 at first."""
    for o in (0, 90, 180, 270):
        fp.SetOrientationDegrees(o)
        (x1, y1), (x2, y2) = pad_xy(fp, "1"), pad_xy(fp, "2")
        d = math.hypot(x2 - x1, y2 - y1)
        if abs((x2 - x1) / d - step_dir[0]) < 0.01 and abs((y2 - y1) / d - step_dir[1]) < 0.01:
            break
    else:
        raise RuntimeError("no orientation for " + fp.GetReference())
    x1, y1 = pad_xy(fp, "1")
    px, py = from_page(fp.GetPosition())
    fp.SetPosition(to_page(px + first[0] - x1, py + first[1] - y1))


def add_rule_area(board, name, pts, layers, pads=True, footprints=True):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    ls = pcbnew.LSET()
    for layer in layers:
        ls.AddLayer(layer)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowPads(pads)
    z.SetDoNotAllowFootprints(footprints)
    o = z.Outline()
    o.NewOutline()
    for x, y in pts:
        o.Append(to_page(x, y))
    board.Add(z)


def rect_pts(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle_pts(c, r, n=32):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def add_text(board, text, x, y, layer, size=1.0, angle=0, bold=False):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetLayer(layer)
    t.SetPosition(to_page(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm((0.2 if bold else 0.15) * size))
    t.SetTextAngleDegrees(angle)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


def add_shape(board, layer, width, shape, **kw):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(shape)
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    if shape == pcbnew.SHAPE_T_CIRCLE:
        s.SetCenter(to_page(*kw["c"]))
        s.SetEnd(to_page(kw["c"][0] + kw["r"], kw["c"][1]))
    elif shape == pcbnew.SHAPE_T_ARC:
        s.SetArcGeometry(to_page(*kw["a"]), to_page(*kw["m"]), to_page(*kw["b"]))
    else:
        s.SetStart(to_page(*kw["a"]))
        s.SetEnd(to_page(*kw["b"]))
    board.Add(s)


def add_outline(board):
    """70 x 45 with R9 corners: four lines and four arcs on Edge.Cuts."""
    hx, hy = BW / 2, BH / 2
    L = pcbnew.Edge_Cuts
    for a, b in (((-hx + BR, hy), (hx - BR, hy)), ((-hx + BR, -hy), (hx - BR, -hy)),
                 ((hx, -hy + BR), (hx, hy - BR)), ((-hx, -hy + BR), (-hx, hy - BR))):
        add_shape(board, L, 0.1, pcbnew.SHAPE_T_SEGMENT, a=a, b=b)
    k = BR * (1 - math.sqrt(0.5))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_shape(board, L, 0.1, pcbnew.SHAPE_T_ARC, a=(sx * (hx - BR), sy * hy),
                      m=(sx * (hx - k), sy * (hy - k)), b=(sx * hx, sy * (hy - BR)))


# Stock footprints whose own 3D model isn't shipped: same-geometry stand-ins (renders / GLB only).
MODEL_SUBST = {
    "SW1": "${KICAD10_3DMODEL_DIR}/Button_Switch_THT.3dshapes/SW_PUSH-12mm_Wuerth-430476085716.step",
    "U3": "${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step",
}

# Nets carrying battery / boost current get wider tracks.
POWER_NETS = ("/BAT_IN", "/VBAT", "/BOOST_SW", "/3V3")


def write_rules():
    path = os.path.join(HW, PROJECT + ".kicad_pro")
    pro = json.load(open(path))
    rules = pro["board"]["design_settings"]["rules"]
    rules.update(min_resolved_spokes=1, min_clearance=0.15, min_track_width=0.15, min_copper_edge_clearance=0.3,
                 min_hole_clearance=0.25, min_through_hole_diameter=0.2, min_via_diameter=0.5)
    ns = pro["net_settings"]
    default = next(c for c in ns["classes"] if c["name"] == "Default")
    default.update(clearance=0.15, track_width=0.25, via_diameter=0.6, via_drill=0.3)
    power = dict(default, name="Power", track_width=0.5, via_diameter=0.8, via_drill=0.4)
    gnd = dict(default, name="GND", track_width=0.4)
    ns["classes"] = [default, power, gnd]
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER_NETS] + \
                              [{"netclass": "GND", "pattern": "/GND"}]
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)
        f.write("\n")


def main(netlist):
    comps, nets = read_netlist(netlist)
    board = pcbnew.NewBoard(PCB)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = mm(0.15)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_MinThroughDrill = mm(0.2)          # the stock WROOM-02 / TQFN thermal vias are 0.2 mm
    ds.m_HoleClearance = mm(0.25)
    ds.m_CopperEdgeClearance = mm(0.3)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(0.15))
    nc.SetTrackWidth(mm(0.25))
    nc.SetViaDiameter(mm(0.6))
    nc.SetViaDrill(mm(0.3))

    netinfo = {}
    for name in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    pad_net = {node: name for name, nodes in nets.items() for node in nodes}

    placed = {}
    for ref in sorted(comps):
        c = comps[ref]
        fp = load_fp(c["footprint"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        fp.SetSheetname("/")
        fp.SetSheetfile(PROJECT + ".kicad_sch")
        for k, v in c["fields"].items():
            fp.SetField(k, v)
            fp.GetField(k).SetVisible(False)
        if c["dnp"] or ref[0] in "HF" or ref.startswith("TP"):
            fp.SetDNP(c["dnp"])
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
        if ref in MODEL_SUBST:
            fp.Models()[0].m_Filename = MODEL_SUBST[ref]
        if ref[0] in "HF":
            fp.Reference().SetVisible(False)   # holes and fiducials need no label
        board.Add(fp)
        for p in fp.Pads():
            name = pad_net.get((ref, p.GetNumber()))
            if name:
                p.SetNet(netinfo[name])
        placed[ref] = fp

    for i, (x, y) in enumerate(POSTS):
        placed["H%d" % (i + 1)].SetPosition(to_page(x, y))
    for ref, (x, y, o) in FIXED.items():
        fp = placed[ref]
        fp.SetPosition(to_page(x, y))
        fp.SetOrientationDegrees(o)
    for ref, (x, y, d) in ROWS.items():
        place_row(placed[ref], (x, y), d)
    autofit(placed)

    # Outline, keep-outs, GND pour on the bottom (the top one comes with routing).
    add_outline(board)
    add_rule_area(board, "Antenna keep-out", rect_pts(ANTENNA_KEEPOUT), [pcbnew.F_Cu, pcbnew.B_Cu],
                  pads=False, footprints=False)
    for i, p in enumerate(POSTS):
        add_rule_area(board, "Post %d keep-out" % (i + 1), circle_pts(p, POST_KEEPOUT), [pcbnew.F_Cu, pcbnew.B_Cu],
                      pads=False, footprints=False)
    for ref in ("FID1", "FID2", "FID3"):        # Freerouting doesn't see a fiducial's 0.6 mm clearance
        add_rule_area(board, ref + " keep-out", circle_pts(FIXED[ref][:2], 1.8, 16), [pcbnew.F_Cu],
                      pads=False, footprints=False)
    gnd = pcbnew.ZONE(board)
    gnd.SetLayer(pcbnew.B_Cu)
    gnd.SetNet(netinfo["/GND"])
    gnd.SetZoneName("GND pour")
    gnd.SetLocalClearance(mm(0.3))
    gnd.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    gnd.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = gnd.Outline()
    o.NewOutline()
    for x, y in rounded_rect_pts(BW - 1.0, BH - 1.0, BR - 0.5):
        o.Append(to_page(x, y))
    board.Add(gnd)

    # Silkscreen: pad-row labels, outlines of what sits above / below, name and face.
    for ref, (title, labels, where, *title_at) in ROW_LABELS.items():
        fp = placed[ref]
        pts = [pad_xy(fp, str(i + 1)) for i in range(len(labels))]
        for (x, y), text in zip(pts, labels):
            if where == "below":
                add_text(board, text, x, y - 1.9, pcbnew.F_SilkS, 0.8)
            else:
                dx = -2.4 - 0.35 * len(text) if where == "left" else 2.0 + 0.35 * len(text)
                add_text(board, text, x + dx, y, pcbnew.F_SilkS, 0.8)
        cx = sum(p[0] for p in pts) / len(pts)
        if title_at:
            add_text(board, title, *title_at[0], pcbnew.F_SilkS, 0.9)
        elif where == "below":
            add_text(board, title, cx, pts[0][1] - 3.4, pcbnew.F_SilkS, 0.9)
        else:
            add_text(board, title, cx, max(p[1] for p in pts) + 2.0, pcbnew.F_SilkS, 0.9)
    add_shape(board, pcbnew.F_SilkS, 0.12, pcbnew.SHAPE_T_CIRCLE, c=PIR_AT, r=5.0)
    add_text(board, "ANTENNA", MODULE_AT[0], 19.2, pcbnew.F_Fab, 1.0)
    add_text(board, "BACKPACK DEFENDER", -4.0, -6.0, pcbnew.B_SilkS, 1.6, bold=True)
    add_text(board, "^_^  rev A  2026", -4.0, -9.0, pcbnew.B_SilkS, 1.2)
    add_shape(board, pcbnew.B_SilkS, 0.12, pcbnew.SHAPE_T_RECTANGLE, a=(-26.0, 0.0), b=(26.0, -22.0))
    add_text(board, "2 x AAA holder (approx.)", -4.0, -19.5, pcbnew.B_SilkS, 1.0)

    title = board.GetTitleBlock()
    title.SetTitle("Backpack Defender")
    title.SetRevision("A")
    title.SetDate("2026-10-28")
    title.SetCompany("Product Speedrun 001")
    board.SetTitleBlock(title)
    pcbnew.SaveBoard(PCB, board)
    write_rules()
    print("wrote", PCB)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HW, "output", PROJECT + ".net"))
