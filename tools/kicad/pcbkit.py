"""Board geometry and placement helpers shared by gen_pcb, route_pcb, fix_route and tidy_silk.

Coordinates are the enclosure's own XY in mm: origin at the board centre, +y up (toward the
back of the product). KiCad's page is y-down around (100, 100); to_page() converts.
The board outline is a rounded rectangle from layout.BOARD = (width, height, corner radius):
a radius of half the shorter side gives a pill, equal sides and half radius give a disc.

Run with KiCad's bundled Python (it has the pcbnew module).
"""

import math
import os

import pcbnew

from env import kicad_share

CX, CY = 100.0, 100.0
BW = BH = BR = None
LAYOUT = None


def configure(layout):
    global BW, BH, BR, LAYOUT
    LAYOUT = layout
    BW, BH, BR = (float(v) for v in layout.BOARD)
    assert BR <= min(BW, BH) / 2 + 1e-9, "corner radius larger than half the board"


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


def board_pts(inset=0.0):
    """The board outline shrunk (or grown, if negative) by inset: for pours and keep-out bands."""
    return rounded_rect_pts(BW - 2 * inset, BH - 2 * inset, max(BR - inset, 0.01))


def inside_outline(x, y, inset):
    """True if (x, y) is at least `inset` inside the board outline."""
    hx, hy = BW / 2 - BR, BH / 2 - BR
    dx, dy = max(abs(x) - hx, 0), max(abs(y) - hy, 0)
    if dx > 0 and dy > 0:
        return math.hypot(dx, dy) <= BR - inset
    return abs(x) <= BW / 2 - inset and abs(y) <= BH / 2 - inset


def rect_pts(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle_pts(c, r, n=32):
    return [(c[0] + r * math.cos(2 * math.pi * k / n), c[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def circle_rect(c, r):
    return (c[0] - r, c[1] - r, c[0] + r, c[1] + r)


def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(os.path.join(kicad_share(), "footprints", lib + ".pretty"), name)
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
    """Board-frame bounding box of a footprint's courtyard (pads + 0.3 mm if it has none), on its own side."""
    xs, ys = [], []
    crtyd = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    for g in fp.GraphicalItems():
        if g.GetLayer() == crtyd:
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


def side(fp):
    """Which faces of the board a footprint takes up: "F", "B", or "FB" for a through-hole part.

    Goes by the footprint's own THT attribute, not its pads: an SMD module's plated thermal vias
    don't make it block the other face."""
    if fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE:
        return "FB"
    return "B" if fp.IsFlipped() else "F"


def pth_rects(fp, margin=0.3):
    """Board-frame boxes of an SMD footprint's plated-hole pads (thermal vias): copper on both faces."""
    if fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE:
        return []          # its whole courtyard already blocks both faces
    out = []
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            bb = p.GetBoundingBox()
            (x0, y1), (x1, y0) = from_page(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())), \
                from_page(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
            out.append((x0 - margin, y0 - margin, x1 + margin, y1 + margin))
    return out


def set_orientation(fp, deg):
    """Orientation as seen from the top. A left-right flip leaves a bottom footprint at 180 degrees
    with its geometry mirrored in x only, so bottom parts add that 180 back."""
    fp.SetOrientationDegrees((deg + 180) % 360 if fp.IsFlipped() else deg)


def trim_courtyard(fp, margin=0.25):
    """Replace a footprint's courtyard with its Fab-layer body outline plus margin.

    For modules whose stock courtyard includes an antenna clearance zone wider than the board:
    the auto-fitter and DRC then see the body only. Its built-in keep-out zone goes too, so keep
    copper off the antenna with layout.NO_COPPER. DRC's footprint-vs-library check is turned off
    for the board (gen_pcb.write_rules), since the edit is deliberate."""
    fab = pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab
    crt = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    bb = None
    for g in list(fp.GraphicalItems()):
        if g.GetLayer() == fab and isinstance(g, pcbnew.PCB_SHAPE):
            b = g.GetBoundingBox()
            if bb is None:
                bb = b
            else:
                bb.Merge(b)
    if bb is None:
        raise RuntimeError("trim_courtyard: %s has no Fab outline" % fp.GetReference())
    for g in list(fp.GraphicalItems()):
        if g.GetLayer() == crt:
            fp.Remove(g)
    for z in list(fp.Zones()):      # the footprint's own antenna keep-out spans the same oversized zone
        fp.Remove(z)
    r = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_RECT)
    r.SetLayer(crt)
    r.SetWidth(mm(0.05))
    r.SetStart(pcbnew.VECTOR2I(bb.GetLeft() - mm(margin), bb.GetTop() - mm(margin)))
    r.SetEnd(pcbnew.VECTOR2I(bb.GetRight() + mm(margin), bb.GetBottom() + mm(margin)))
    fp.Add(r)


def autofit(placed, prefer, keepouts, report=None):
    """Put each preferred part at its spot, or the nearest free spot in a widening spiral (up to 16 mm).

    report: list that collects (ref, mm moved) for parts that didn't fit where asked.
    """
    prefer_refs = {r for r, *_ in prefer}
    # (rect, sides): SMD parts on opposite faces may share board area; keep-outs and THT parts block both
    occupied = [(courtyard_rect(fp), side(fp)) for ref, fp in placed.items()
                if ref not in prefer_refs and not ref.startswith("H")]
    occupied += [(r, "FB") for ref, fp in placed.items() if ref not in prefer_refs for r in pth_rects(fp)]
    # keep-outs: a rect blocks both faces; (rect, "F") or (rect, "B") blocks one
    occupied += [(r, "FB") if len(r) == 4 else (r[0], r[1]) for r in keepouts]

    def free(r, s):
        if not all(inside_outline(x, y, 0.5) for x in (r[0], r[2]) for y in (r[1], r[3])):
            return False
        return not any(overlaps(r, o) and set(s) & set(os_) for o, os_ in occupied)

    for ref, x, y, o in prefer:
        fp = placed[ref]
        set_orientation(fp, o)
        best = None
        for step in range(0, 81):
            d = step * 0.2
            n = 1 if d == 0 else max(8, int(2 * math.pi * d / 0.2))
            for k in range(n):
                a = 2 * math.pi * k / n
                fp.SetPosition(to_page(x + d * math.cos(a), y + d * math.sin(a)))
                r = courtyard_rect(fp)
                if free(r, side(fp)):
                    best = r
                    break
            if best:
                break
        if best is None:
            raise SystemExit("autofit: no room for %s near (%.1f, %.1f): free some space or move its PREFER spot"
                             % (ref, x, y))
        moved = math.hypot(*[a - b for a, b in zip(from_page(fp.GetPosition()), (x, y))])
        if moved > 0.05:
            print("  autofit: %-4s moved %.1f mm" % (ref, moved))
            if report is not None:
                report.append((ref, moved))
        occupied.append((best, side(fp)))
        occupied += [(r, "FB") for r in pth_rects(fp)]


def place_row(fp, first, step_dir):
    """Rotate a 1xN pad footprint so pin 2 lies in step_dir from pin 1, then put pin 1 at first."""
    for o in (0, 90, 180, 270):
        set_orientation(fp, o)
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


def silk_circle(board, c, r, layer=None, width=0.12):
    add_shape(board, pcbnew.F_SilkS if layer is None else layer, width, pcbnew.SHAPE_T_CIRCLE, c=c, r=r)


def silk_rect(board, a, b, layer=None, width=0.12):
    add_shape(board, pcbnew.F_SilkS if layer is None else layer, width, pcbnew.SHAPE_T_RECTANGLE, a=a, b=b)


def add_outline(board):
    """The rounded-rectangle outline on Edge.Cuts: up to four lines and four arcs (a disc is just arcs)."""
    hx, hy = BW / 2, BH / 2
    L = pcbnew.Edge_Cuts
    if BR <= 0:
        for a, b in (((-hx, hy), (hx, hy)), ((hx, hy), (hx, -hy)), ((hx, -hy), (-hx, -hy)), ((-hx, -hy), (-hx, hy))):
            add_shape(board, L, 0.1, pcbnew.SHAPE_T_SEGMENT, a=a, b=b)
        return
    for a, b in (((-hx + BR, hy), (hx - BR, hy)), ((-hx + BR, -hy), (hx - BR, -hy)),
                 ((hx, -hy + BR), (hx, hy - BR)), ((-hx, -hy + BR), (-hx, hy - BR))):
        if math.hypot(b[0] - a[0], b[1] - a[1]) > 1e-6:
            add_shape(board, L, 0.1, pcbnew.SHAPE_T_SEGMENT, a=a, b=b)
    k = BR * (1 - math.sqrt(0.5))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_shape(board, L, 0.1, pcbnew.SHAPE_T_ARC, a=(sx * (hx - BR), sy * hy),
                      m=(sx * (hx - k), sy * (hy - k)), b=(sx * hx, sy * (hy - BR)))
