#!/usr/bin/env python3
"""Route the episode's board: GND pours on both layers, then Freerouting.

Run with KiCad's bundled Python on a board fresh from gen_pcb.py (tools/kicad/build.sh does this):
  "$KICAD_PY" tools/kicad/route_pcb.py <episode>

1. layout.PREROUTE's fixed tracks, then GND vias around the big ground pads named in
   layout.GND_VIA_PADS (modules, QFNs).
2. GND pours on both layers (the bottom one comes from gen_pcb.py), a keep-out band along the edge.
3. Export Specctra DSN (GND plane stripped), run Freerouting headless (two passes), import the
   session, stitch GND vias.
Then: kicad-cli pcb drc --refill-zones --save-board to fill and check (build.sh), and fix_route.py.
ROUTE_PASSES (default 40) sets Freerouting's optimisation passes: lower is faster, higher is tidier.
ROUTE_TIMEOUT (default 300) stops a Freerouting run that hangs.
"""

import math
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import freerouting_jar, java, use_episode  # noqa: E402

HW = use_episode(sys.argv)
import pcbnew  # noqa: E402

import design  # noqa: E402,F401
import layout  # noqa: E402
import pcbkit as k  # noqa: E402
from pcbkit import from_page, inside_outline, to_page  # noqa: E402
from schkit import CFG  # noqa: E402

k.configure(layout)
PCB = os.path.join(HW, CFG["project"] + ".kicad_pcb")
OUT = os.path.join(HW, "output", "routing")
GND = getattr(layout, "GND_NET", "/GND")
# GND *is* autorouted: Freerouting links pour fragments the pours alone can't reach. Its
# board-wide planes are dropped so Freerouting doesn't treat both layers as blocked.
STRIP_PLANES = (GND,)


def mm(v):
    return pcbnew.FromMM(v)


def seg_dist(p, a, b):
    """Distance from point p to segment ab."""
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class Router:
    def __init__(self, board):
        self.b = board

    def net(self, name):
        n = self.b.FindNet(name)
        assert n is not None, name
        return n

    def track(self, net, a, b, w, layer=pcbnew.F_Cu):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(to_page(*a))
        t.SetEnd(to_page(*b))
        t.SetWidth(mm(w))
        t.SetLayer(layer)
        t.SetNet(self.net(net))
        t.SetLocked(True)
        self.b.Add(t)

    def via(self, net, p, d=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(to_page(*p))
        v.SetWidth(mm(d))
        v.SetDrill(mm(drill))
        v.SetNet(self.net(net))
        v.SetLocked(True)
        self.b.Add(v)

    def via_ok(self, net, p, d=0.6, margin=0.3):
        """True if a via at p clears other nets' pads, tracks, vias, keep-outs, holes and the edge."""
        x, y = p
        if not inside_outline(x, y, d / 2 + 0.5):
            return False
        reach = d / 2 + margin
        for fp in self.b.GetFootprints():
            for pad in fp.Pads():
                if pad.HasHole() or pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    px, py = from_page(pad.GetPosition())
                    hole = pcbnew.ToMM(max(pad.GetDrillSize().x, pad.GetDrillSize().y, pad.GetSize().x))
                    if math.hypot(px - x, py - y) < d / 2 + hole / 2 + 0.35:
                        return False
                    continue
                if pad.GetNetname() == net:
                    continue
                bb = pad.GetBoundingBox()
                x0, y1 = from_page(bb.GetOrigin())
                x1, y0 = from_page(bb.GetEnd())
                if x0 - reach < x < x1 + reach and y0 - reach < y < y1 + reach:
                    return False
        for t in self.b.GetTracks():
            if t.GetClass() == "PCB_VIA":
                vx, vy = from_page(t.GetPosition())
                if math.hypot(vx - x, vy - y) < d / 2 + 0.3 + (0 if t.GetNetname() == net else 0.3):
                    return False
            elif t.GetNetname() != net:
                a, b = from_page(t.GetStart()), from_page(t.GetEnd())
                if seg_dist((x, y), a, b) < d / 2 + pcbnew.ToMM(t.GetWidth()) / 2 + margin:
                    return False
        ring = [(x, y)] + [(x + (d / 2 + 0.2) * math.cos(i * math.pi / 4),
                             y + (d / 2 + 0.2) * math.sin(i * math.pi / 4)) for i in range(8)]
        zones = list(self.b.Zones()) + [z for fp in self.b.GetFootprints() for z in fp.Zones()]
        for z in zones:
            if z.GetIsRuleArea() and z.GetDoNotAllowVias():
                if any(z.Outline().Contains(to_page(*q)) for q in ring):
                    return False
        return True

    def track_ok(self, net, a, b, w, margin=0.2):
        """True if a track a-b of width w clears other nets' tracks, vias and pads."""
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.2))
        samples = [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
        for t in self.b.GetTracks():
            if t.GetNetname() == net:
                continue
            if t.GetClass() == "PCB_VIA":
                if seg_dist(from_page(t.GetPosition()), a, b) < w / 2 + 0.3 + margin:
                    return False
            else:
                p0, p1 = from_page(t.GetStart()), from_page(t.GetEnd())
                tw = pcbnew.ToMM(t.GetWidth())
                if any(seg_dist(q, p0, p1) < w / 2 + tw / 2 + margin for q in samples):
                    return False
        for fp in self.b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == net:
                    continue
                bb = pad.GetBoundingBox()
                x0, y1 = from_page(bb.GetOrigin())
                x1, y0 = from_page(bb.GetEnd())
                r = w / 2 + margin
                if any(x0 - r < q[0] < x1 + r and y0 - r < q[1] < y1 + r for q in samples):
                    return False
        return True

    def via_near(self, net, origin, candidates, w):
        """Via at the first clear candidate, tracked back to origin; None if none fits."""
        for c in candidates:
            if self.via_ok(net, c) and self.track_ok(net, origin, c, w):
                self.track(net, origin, c, w)
                self.via(net, c)
                return c
        return None

    def zone(self, net, pts, layer, name, priority, min_w=0.2):
        z = pcbnew.ZONE(self.b)
        z.SetLayer(layer)
        z.SetNet(self.net(net))
        z.SetZoneName(name)
        z.SetAssignedPriority(priority)
        z.SetMinThickness(mm(min_w))
        z.SetLocalClearance(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            o.Append(to_page(x, y))
        self.b.Add(z)


def clear_previous(board):
    for t in list(board.GetTracks()):
        board.Remove(t)
    for z in list(board.Zones()):
        if z.GetZoneName().startswith("route:"):
            board.Remove(z)


def big_pad_gnd_vias(r):
    """GND vias around each listed part's centre, so its ground pad reaches the bottom pour directly."""
    for ref in getattr(layout, "GND_VIA_PADS", []):
        x, y = from_page(r.b.FindFootprintByReference(ref).GetPosition())
        for p in ((x - 3.0, y), (x + 3.0, y), (x, y - 3.0), (x, y + 3.0)):
            if r.via_ok(GND, p):
                r.via(GND, p)


def edge_band(r):
    """Keep-out band just inside the outline: Freerouting only keeps its own 0.15 mm from the
    edge, but the board rule is 0.3 mm to copper."""
    z = pcbnew.ZONE(r.b)
    z.SetIsRuleArea(True)
    z.SetZoneName("route:edge band")
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in k.board_pts(-0.2):
        o.Append(to_page(x, y))
    o.NewHole()
    for x, y in reversed(k.board_pts(0.45)):
        o.Append(to_page(x, y))
    r.b.Add(z)


def top_gnd_pour(r):
    r.zone(GND, k.board_pts(0.5), pcbnew.F_Cu, "route:GND top", 0, min_w=0.25)


def stitch(r, pitch=3.0):
    """GND vias on a grid wherever they fit, tying the top and bottom pours together."""
    n = 0
    for i in range(-int(k.BW / pitch), int(k.BW / pitch) + 1):
        for j in range(-int(k.BH / pitch), int(k.BH / pitch) + 1):
            p = (i * pitch + (j % 2) * pitch / 2, j * pitch)
            if inside_outline(*p, 1.5) and r.via_ok(GND, p, margin=0.35):
                r.via(GND, p)
                n += 1
    print("stitching vias:", n)


def stitch_islands(r):
    """Give every GND pour fragment with no via or through-hole GND pad a via of its own."""
    anchors = [from_page(t.GetPosition()) for t in r.b.GetTracks()
               if t.GetClass() == "PCB_VIA" and t.GetNetname() == GND]
    anchors += [from_page(p.GetPosition()) for fp in r.b.GetFootprints() for p in fp.Pads()
                if p.GetNetname() == GND and p.HasHole()]
    added = 0
    for z in r.b.Zones():
        if z.GetNetname() != GND or z.GetIsRuleArea():
            continue
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(layer):
                continue
            polys = z.GetFilledPolysList(layer)
            for i in range(polys.OutlineCount()):
                one = pcbnew.SHAPE_POLY_SET()
                one.AddOutline(polys.Outline(i))
                if any(one.Contains(to_page(*a)) for a in anchors):
                    continue
                bb = one.BBox()
                x0, y1 = from_page(bb.GetOrigin())
                x1, y0 = from_page(bb.GetEnd())
                placed = False
                for a in range(13):
                    for b in range(13):
                        q = (x0 + (x1 - x0) * a / 12, y0 + (y1 - y0) * b / 12)
                        ring = [q] + [(q[0] + 0.45 * math.cos(n * math.pi / 4), q[1] + 0.45 * math.sin(n * math.pi / 4))
                                      for n in range(8)]
                        if all(one.Contains(to_page(*c)) for c in ring) and r.via_ok(GND, q, margin=0.3):
                            r.via(GND, q)
                            anchors.append(q)
                            added += 1
                            placed = True
                            break
                    if placed:
                        break
    print("island vias:", added)


def strip_planes_from_dsn(path):
    text = open(path).read()
    for name in STRIP_PLANES:
        text = re.sub(r"\(plane %s \(polygon[^)]*\)\s*\)" % re.escape(name), "", text)
    open(path, "w").write(text)


def prerouted(r):
    """Lay layout.PREROUTE's fixed tracks before Freerouting (it routes around them; they're locked).

    Each entry is a path: "REF.PAD", then any of (x, y) points in board mm, a number (track width
    from there on, else 0.5 mm on POWER_NETS and 0.25 mm otherwise), "via" (via here, carry on
    on the other layer), ending with "REF.PAD". The net comes from the first pad."""
    for path in getattr(layout, "PREROUTE", []):
        def pad(s):
            ref, num = s.split(".")
            fp = r.b.FindFootprintByReference(ref)
            assert fp is not None, "PREROUTE: no part " + ref
            p = fp.FindPadByNumber(num)
            assert p is not None, "PREROUTE: no pad %s on %s" % (num, ref)
            return p
        first, last = pad(path[0]), pad(path[-1])
        net = first.GetNetname()
        assert last.GetNetname() == net, "PREROUTE: %s and %s are on different nets" % (path[0], path[-1])
        w = 0.5 if net in getattr(layout, "POWER_NETS", ()) else 0.25
        layer, at = pcbnew.F_Cu, from_page(first.GetPosition())
        for step in list(path[1:-1]) + [from_page(last.GetPosition())]:
            if isinstance(step, (int, float)):
                w = step
            elif step == "via":
                r.via(net, at)
                layer = pcbnew.B_Cu if layer == pcbnew.F_Cu else pcbnew.F_Cu
            else:
                r.track(net, at, step, w, layer)
                at = step
        assert layer == pcbnew.F_Cu, "PREROUTE %s: ends on the bottom layer (odd number of vias)" % path[0]
        print("prerouted", net, path[0], "->", path[-1])


def freerouting(dsn, ses, logname):
    """One headless Freerouting run on dsn. Returns True if it saved a session.
    Freerouting has no time limit of its own and now and then never finishes (a normal run is
    well under a minute), so ROUTE_TIMEOUT (default 300 s) stops it."""
    if os.path.exists(ses):
        os.remove(ses)
    cmd = [java(), "-Djava.awt.headless=true", "-jar", freerouting_jar(), "-de", dsn, "-do", ses,
           "-mp", os.environ.get("ROUTE_PASSES", "40"), "-mt", "6", "--gui.enabled=false"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=int(os.environ.get("ROUTE_TIMEOUT", "300")))
        log = p.stdout + p.stderr
    except subprocess.TimeoutExpired as e:
        log = "%s%s\nTIMED OUT\n" % (e.stdout or "", e.stderr or "")
        log = log.decode(errors="replace") if isinstance(log, bytes) else log
        print("  timed out")
    open(os.path.join(OUT, logname), "w").write(log)
    return os.path.exists(ses) and "TIMED OUT" not in log


def main():
    os.makedirs(OUT, exist_ok=True)
    board = pcbnew.LoadBoard(PCB)
    clear_previous(board)
    r = Router(board)
    prerouted(r)
    big_pad_gnd_vias(r)
    top_gnd_pour(r)
    edge_band(r)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    dsn = os.path.join(OUT, "board.dsn")
    ses = os.path.join(OUT, "board.ses")
    # Two runs: the second starts from the first run's routing and finishes what it left.
    # If the second one hangs or fails, the first run's routing stands.
    for n in (1, 2):
        assert pcbnew.ExportSpecctraDSN(board, dsn), "DSN export failed"
        strip_planes_from_dsn(dsn)
        print("freerouting run", n)
        if freerouting(dsn, ses, "freerouting%d.log" % n):
            assert pcbnew.ImportSpecctraSES(board, ses), "SES import failed"
        else:
            assert n == 2, "Freerouting produced no session; see output/routing/freerouting1.log"
            print("  run 2 failed; keeping run 1's routing")
    stitch(Router(board))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    stitch_islands(Router(board))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("routed:", len(board.GetTracks()), "tracks/vias")


if __name__ == "__main__":
    main()
