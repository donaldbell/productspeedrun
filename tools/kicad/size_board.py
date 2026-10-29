#!/usr/bin/env python3
"""How big does this board need to be? Run right after the schematic, before Stage 4 fixes the enclosure.

  "$KICAD_PY" tools/kicad/size_board.py <episode> <exported.net>     (build.sh schematic runs this)

Adds up the footprints' areas (courtyards, or the body for modules whose courtyard includes an
antenna clearance) and writes 5-electronics/SIZE.md: the part area, the biggest parts, and the
smallest board area Freerouting routes comfortably on 2 layers. The thresholds come from the
first episodes: 001 routed first time at about 35 % of one face; 002 failed every run at about
70 % across both faces (48 x 26) and routed at 54 x 31.
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import use_episode  # noqa: E402

HW = use_episode(sys.argv)
import pcbnew  # noqa: E402

import pcbkit as k  # noqa: E402
from sexpr import find, find_all, parse  # noqa: E402

ONE_FACE = 0.40     # parts area / board area, all parts on one face
TWO_FACES = 0.55    # parts area / board area (one face's worth), parts split across both faces
EDGE = 4.0          # mm from a part to the edge where mounting holes and posts go


def fab_box(fp):
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_Fab and isinstance(g, pcbnew.PCB_SHAPE):
            b = g.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]
            ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        return None
    return (pcbnew.ToMM(max(xs) - min(xs)) + 0.5, pcbnew.ToMM(max(ys) - min(ys)) + 0.5)


def main(netlist):
    net = parse(open(netlist).read())
    rows = []
    for c in find_all(find(net, "components"), "comp"):
        ref = str(find(c, "ref")[1])
        fpid = str(find(c, "footprint")[1])
        if not fpid or ref.startswith("H") and ref[1:].isdigit():
            continue        # mounting holes are counted in the edge margin
        fp = k.load_fp(fpid)
        x0, y0, x1, y1 = k.courtyard_rect(fp)
        w, h = x1 - x0, y1 - y0
        fab = fab_box(fp)
        note = ""
        if fab and w * h > 1.5 * fab[0] * fab[1]:
            w, h = fab
            note = "body only: its courtyard includes a clearance zone (use TRIM_COURTYARD)"
        tht = bool(fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE)
        rows.append((w * h, w, h, ref, fpid.split(":")[-1], tht, note))
    rows.sort(reverse=True)
    total = sum(r[0] for r in rows)
    tht_area = sum(r[0] for r in rows if r[5])
    one = total / ONE_FACE
    # On two faces, through-hole parts block both faces; SMD parts split between them.
    two = (tht_area + (total - tht_area) / 2) / TWO_FACES
    big_w = max((max(r[1], r[2]) for r in rows), default=0)

    def shape(area, aspect):
        h = math.sqrt(area / aspect)
        return "%.0f x %.0f" % (h * aspect, h)

    out = ["# Board size check", "",
           "From the schematic's footprints (written by `tools/kicad/size_board.py`; rerun with "
           "`tools/kicad/build.sh episodes/<slug> schematic`).", "",
           "| | mm² |", "|---|---|",
           "| Parts area (%d parts) | %.0f |" % (len(rows), total),
           "| Smallest comfortable board, **parts on one face** | **%.0f** (e.g. %s, or %s) |"
           % (one, shape(one, 1.0), shape(one, 1.6)),
           "| Smallest comfortable board, **parts on both faces** | **%.0f** (e.g. %s, or %s) |"
           % (two, shape(two, 1.0), shape(two, 1.6)), "",
           "Add about %.0f mm to each side for mounting holes and posts if they sit outside the parts area. "
           "No side can be shorter than the biggest part, %.1f mm, plus %.0f mm." % (EDGE, big_w, 2 * EDGE),
           "Corners cut by a large radius, cut-outs and keep-outs (antennas, under tall parts) need extra area on top.",
           "", "## Biggest parts", "", "| Ref | Footprint | W × H mm | Note |", "|---|---|---|---|"]
    for a, w, h, ref, fp, tht, note in rows[:8]:
        out.append("| %s | %s | %.1f × %.1f%s | %s |" % (ref, fp, w, h, " (through-hole)" if tht else "", note))
    text = "\n".join(out) + "\n"
    open(os.path.join(HW, "SIZE.md"), "w").write(text)
    print("parts %.0f mm2; board >= %.0f mm2 one face, >= %.0f mm2 both faces (SIZE.md)" % (total, one, two))


if __name__ == "__main__":
    main(sys.argv[2])
