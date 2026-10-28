#!/usr/bin/env python3
"""Clean up after autorouting, driven by a KiCad DRC JSON report.

Run with KiCad's bundled Python:
  "$KICAD_PY" tools/kicad/fix_route.py <episode> output/drc.json

- Widens autorouter neck-downs below the 0.15 mm minimum.
- Gives every GND pad the pours didn't reach a short track and via to the pours.
- Removes vias that are connected on one layer only (autorouter leftovers).
Removals come last: after board.Remove() the pcbnew wrapper can't iterate the
board's tracks again in the same session.
Then re-run DRC with --refill-zones; repeat if it still reports GND items.
"""

import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew  # noqa: E402
from route_pcb import GND, PCB, Router, from_page  # noqa: E402  (also loads the episode)


def in_own_pad(board, via):
    """True if the via's centre lies on a pad of the same net (e.g. an exposed-pad thermal via)."""
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == via.GetNetname() and pad.HitTest(via.GetPosition()):
                return True
    return False


def main(report):
    d = json.load(open(report))
    board = pcbnew.LoadBoard(PCB)
    r = Router(board)
    tracks = list(board.GetTracks())

    narrow = 0
    for t in tracks:
        if t.GetClass() == "PCB_TRACK" and t.GetWidth() < pcbnew.FromMM(0.15):
            t.SetWidth(pcbnew.FromMM(0.15))  # autorouter neck-downs below the 0.15 mm minimum
            narrow += 1
    print("widened narrow tracks:", narrow)

    fixed = set()
    for u in d.get("unconnected_items", []):
        for item in u["items"]:
            m = re.match(r"(?:PTH )?[Pp]ad (\S+) \[%s\] of (\S+)" % re.escape(GND), item["description"])
            if not m or (m.group(2), m.group(1)) in fixed:
                continue
            num, ref = m.group(1), m.group(2)
            fixed.add((ref, num))
            fp = board.FindFootprintByReference(ref)
            pad = fp.FindPadByNumber(num)
            x, y = from_page(pad.GetPosition())
            cands = [(x + rr * math.cos(math.radians(a)), y + rr * math.sin(math.radians(a)))
                     for rr in (1.2, 1.6, 2.0, 2.5) for a in range(0, 360, 30)]
            if r.via_near(GND, (x, y), cands, 0.4) is not None:
                print("GND via added for %s pad %s" % (ref, num))
            else:
                print("NO ROOM for a GND via at %s pad %s" % (ref, num))

    doomed = []
    for v in d["violations"]:
        if v["type"] != "via_dangling":
            continue
        pos = v["items"][0]["pos"]
        for t in tracks:
            # Locked vias are hand-placed; keep them (a dangling one means a hand-route
            # mistake to see), except GND stitching vias, which are spares by design.
            # Never remove a via sitting in a pad of its own net (thermal / via-in-pad):
            # it carries heat even where the far-side pour doesn't reach it.
            if t.GetClass() == "PCB_VIA" and in_own_pad(board, t):
                continue
            if t.GetClass() == "PCB_VIA" and (not t.IsLocked() or t.GetNetname() == GND):
                x, y = pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y)
                if abs(x - pos["x"]) < 0.01 and abs(y - pos["y"]) < 0.01:
                    doomed.append(t)
    for t in doomed:
        board.Remove(t)
    print("removed dangling vias:", len(doomed))
    pcbnew.SaveBoard(PCB, board)


if __name__ == "__main__":
    main(sys.argv[2])
