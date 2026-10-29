#!/usr/bin/env python3
"""How big does this board need to be? Run right after the schematic, before Stage 4 fixes the enclosure.

  "$KICAD_PY" tools/kicad/size_board.py <episode> <exported.net>     (build.sh schematic runs this)

Adds up the footprints' areas (courtyards, or body plus pads for modules whose courtyard includes
an antenna clearance) and writes 5-electronics/SIZE.md: the part area, the biggest parts, and the
smallest board area Freerouting routes comfortably on 2 layers. Modules and other big parts (MCU
modules, 40-pin sockets) count once with a ring of fan-out room around them; everything else needs
2.5 times its own area. Checked against every board built so far: 001 (70 x 45 R9: routed first
time, estimate 2470 mm2), 002 (48 x 26 failed every run, 54 x 31 routed: estimate 1690 mm2) and
the Pico, nRF52840 and Pi HAT blocks (all well above their estimates, all routed first time).
002 had its parts on both faces and still needed the one-face area: plan on this number either way.
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

FILL = 0.40         # small parts' area / the board area they need
BIG = 250.0         # mm2: parts at least this big count once, with a RING mm fan-out ring round them
RING = 2.0
EDGE = 4.0          # mm from a part to the edge where mounting holes and posts go


def body_box(fp):
    """Fab outline plus pads (connector tabs and module pads stick out past the Fab body)."""
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_Fab and isinstance(g, pcbnew.PCB_SHAPE):
            b = g.GetBoundingBox()
            xs += [b.GetLeft(), b.GetRight()]
            ys += [b.GetTop(), b.GetBottom()]
    if not xs:
        return None
    for p in fp.Pads():
        b = p.GetBoundingBox()
        xs += [b.GetLeft(), b.GetRight()]
        ys += [b.GetTop(), b.GetBottom()]
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
        body = body_box(fp)
        note = ""
        if body and w * h > 1.5 * body[0] * body[1]:
            w, h = body
            note = "body and pads only: the courtyard includes a clearance zone (TRIM_COURTYARD on a tight board)"
        tht = bool(fp.GetAttributes() & pcbnew.FP_THROUGH_HOLE)
        rows.append((w * h, w, h, ref, fpid.split(":")[-1], tht, note))
    rows.sort(reverse=True)
    total = sum(r[0] for r in rows)
    big = [r for r in rows if r[0] >= BIG]
    big_area = sum((r[1] + 2 * RING) * (r[2] + 2 * RING) for r in big)
    need = big_area + (total - sum(r[0] for r in big)) / FILL
    big_w = max((max(r[1], r[2]) for r in rows), default=0)

    def shape(area, aspect):
        h = math.sqrt(area / aspect)
        return "%.0f x %.0f" % (h * aspect, h)

    out = ["# Board size check", "",
           "From the schematic's footprints (written by `tools/kicad/size_board.py`; rerun with "
           "`tools/kicad/build.sh episodes/<slug> schematic`).", "",
           "| | mm² |", "|---|---|",
           "| Parts area (%d parts) | %.0f |" % (len(rows), total),
           "| Big parts (%s), with a %.0f mm ring | %.0f |" % (", ".join(r[3] for r in big) or "none", RING, big_area),
           "| **Smallest comfortable board** | **%.0f** (e.g. %s, or %s) |"
           % (need, shape(need, 1.0), shape(need, 1.6)), "",
           "Parts on both faces don't make it smaller: episode 002 needed this area with parts on both faces.",
           "Add about %.0f mm to each side for mounting holes and posts if they sit outside the parts area. "
           "No side can be shorter than the biggest part, %.1f mm, plus %.0f mm." % (EDGE, big_w, 2 * EDGE),
           "Corners cut by a large radius, cut-outs and keep-outs (antennas, under tall parts) need extra area on top.",
           "", "## Biggest parts", "", "| Ref | Footprint | W × H mm | Note |", "|---|---|---|---|"]
    for a, w, h, ref, fp, tht, note in rows[:8]:
        out.append("| %s | %s | %.1f × %.1f%s | %s |" % (ref, fp, w, h, " (through-hole)" if tht else "", note))
    text = "\n".join(out) + "\n"
    open(os.path.join(HW, "SIZE.md"), "w").write(text)
    print("parts %.0f mm2; board >= %.0f mm2 (SIZE.md)" % (total, need))


if __name__ == "__main__":
    main(sys.argv[2])
