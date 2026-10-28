#!/usr/bin/env python3
"""Clean up after autorouting, driven by a KiCad DRC JSON report.

Run with KiCad's bundled Python:
  "$KICAD_PY" tools/kicad/fix_route.py <episode> output/drc.json

- Widens autorouter neck-downs below the 0.15 mm minimum.
- Gives every GND pad the pours didn't reach a short track and via to the pours.
- Removes vias that are connected on one layer only, and dangling track spurs (autorouter leftovers).
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
from route_pcb import GND, PCB, Router, from_page, seg_dist  # noqa: E402  (also loads the episode)


def in_own_pad(board, via):
    """True if the via's centre lies on a pad of the same net (e.g. an exposed-pad thermal via)."""
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == via.GetNetname() and pad.HitTest(via.GetPosition()):
                return True
    return False


def dangling_stubs(board, tracks, d, gone):
    """Unlocked track segments with a free end, on the nets DRC flags as track_dangling.

    Freerouting sometimes leaves a short spur; removing its free segment can leave the next one
    free, so this repeats until the spur is gone back to where it branches off. An end counts as
    connected if it lands on a same-net pad, via, zone fill or another same-net track on its layer."""
    nets = set()
    for v in d["violations"]:
        if v["type"] == "track_dangling":
            m = re.search(r"\[([^\]]+)\]", v["items"][0]["description"])
            if m:
                nets.add(m.group(1))
    if not nets:
        return []
    pads = [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() in nets]
    zones = [z for z in board.Zones() if z.GetNetname() in nets and not z.GetIsRuleArea()]
    live = [t for t in tracks if t.GetNetname() in nets and id(t) not in gone]

    def xy(p):
        return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)

    def connected(t, end):
        layer, net, q = t.GetLayer(), t.GetNetname(), xy(end)
        if any(p.IsOnLayer(layer) and p.HitTest(end) for p in pads if p.GetNetname() == net):
            return True
        if any(z.IsOnLayer(layer) and z.HitTestFilledArea(layer, end) for z in zones if z.GetNetname() == net):
            return True
        for o in live:
            if o is t or o.GetNetname() != net:
                continue
            if o.GetClass() == "PCB_VIA":
                if math.dist(q, xy(o.GetPosition())) <= pcbnew.ToMM(o.GetWidth()) / 2:
                    return True
            elif o.GetLayer() == layer and seg_dist(q, xy(o.GetStart()), xy(o.GetEnd())) <= pcbnew.ToMM(o.GetWidth()) / 2:
                return True
        return False

    removed = []
    while True:
        free = [t for t in live if t.GetClass() == "PCB_TRACK" and not t.IsLocked()
                and not (connected(t, t.GetStart()) and connected(t, t.GetEnd()))]
        if not free:
            return removed
        for t in free:
            live.remove(t)
        removed += free


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
    print("removed dangling vias:", len(doomed))
    stubs = dangling_stubs(board, tracks, d, {id(t) for t in doomed})
    print("removed dangling track stubs:", len(stubs))
    for t in doomed + stubs:
        board.Remove(t)
    pcbnew.SaveBoard(PCB, board)


if __name__ == "__main__":
    main(sys.argv[2])
