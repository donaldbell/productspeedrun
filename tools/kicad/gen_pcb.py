#!/usr/bin/env python3
"""Place the episode's board from its netlist and src/layout.py (parts on top unless layout.BOTTOM lists them).

Run with KiCad's bundled Python (it has the pcbnew module); tools/kicad/build.sh does this:
  "$KICAD_PY" tools/kicad/gen_pcb.py <episode> <exported.net>

Writes <project>.kicad_pcb, overwriting it: stop using this once the board is edited by hand.
Also writes output/placement.txt listing parts the auto-fitter had to move, so the layout can be
tuned (move their PREFER spot) without opening KiCad.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import use_episode  # noqa: E402

HW = use_episode(sys.argv)
import pcbnew  # noqa: E402

import design  # noqa: E402,F401
import layout  # noqa: E402
import pcbkit as k  # noqa: E402
from schkit import CFG  # noqa: E402
from sexpr import find, find_all, parse  # noqa: E402

k.configure(layout)
PROJECT = CFG["project"]
PCB = os.path.join(HW, PROJECT + ".kicad_pcb")
GND = getattr(layout, "GND_NET", "/GND")


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


def write_rules():
    """Board rules in the project file (JLCPCB 2-layer friendly) plus Power and GND net classes."""
    path = os.path.join(HW, PROJECT + ".kicad_pro")
    pro = json.load(open(path))
    pro.setdefault("board", {}).setdefault("design_settings", {}).setdefault("rules", {})
    rules = pro["board"]["design_settings"]["rules"]
    rules.update(min_resolved_spokes=1, min_clearance=0.15, min_track_width=0.15, min_copper_edge_clearance=0.3,
                 min_hole_clearance=0.25, min_through_hole_diameter=0.2, min_via_diameter=0.5)
    if getattr(layout, "TRIM_COURTYARD", ()):
        # trimmed module courtyards differ from the library copy on purpose
        pro["board"]["design_settings"].setdefault("rule_severities", {})["lib_footprint_mismatch"] = "ignore"
    ns = pro.setdefault("net_settings", {})
    classes = ns.get("classes") or [{"name": "Default"}]
    default = next((c for c in classes if c["name"] == "Default"), classes[0])
    default.update(clearance=0.15, track_width=0.25, via_diameter=0.6, via_drill=0.3)
    power = dict(default, name="Power", track_width=0.5, via_diameter=0.8, via_drill=0.4)
    gnd = dict(default, name="GND", track_width=0.4)
    ns["classes"] = [default, power, gnd]
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in getattr(layout, "POWER_NETS", ())] + \
                              [{"netclass": "GND", "pattern": GND}]
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)
        f.write("\n")


def row_labels(board, placed):
    """Silkscreen pin labels beside pad rows: ROW_LABELS = {ref: (title, [labels], "left"|"right"|"below", [title_at])}."""
    for ref, (title, labels, where, *title_at) in getattr(layout, "ROW_LABELS", {}).items():
        fp = placed[ref]
        pts = [k.pad_xy(fp, str(i + 1)) for i in range(len(labels))]
        for (x, y), text in zip(pts, labels):
            if where == "below":
                k.add_text(board, text, x, y - 1.9, pcbnew.F_SilkS, 0.8)
            else:
                dx = -2.4 - 0.35 * len(text) if where == "left" else 2.0 + 0.35 * len(text)
                k.add_text(board, text, x + dx, y, pcbnew.F_SilkS, 0.8)
        cx = sum(p[0] for p in pts) / len(pts)
        if title_at:
            k.add_text(board, title, *title_at[0], pcbnew.F_SilkS, 0.9)
        elif where == "below":
            k.add_text(board, title, cx, pts[0][1] - 3.4, pcbnew.F_SilkS, 0.9)
        else:
            k.add_text(board, title, cx, max(p[1] for p in pts) + 2.0, pcbnew.F_SilkS, 0.9)


def main(netlist):
    comps, nets = read_netlist(netlist)
    board = pcbnew.NewBoard(PCB)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = k.mm(0.15)
    ds.m_TrackMinWidth = k.mm(0.15)
    ds.m_MinThroughDrill = k.mm(0.2)          # stock module / QFN thermal vias are often 0.2 mm
    ds.m_HoleClearance = k.mm(0.25)
    ds.m_CopperEdgeClearance = k.mm(0.3)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(k.mm(0.15))
    nc.SetTrackWidth(k.mm(0.25))
    nc.SetViaDiameter(k.mm(0.6))
    nc.SetViaDrill(k.mm(0.3))

    netinfo = {}
    for name in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    pad_net = {node: name for name, nodes in nets.items() for node in nodes}

    subst = getattr(layout, "MODEL_SUBST", {})
    bottom = set(getattr(layout, "BOTTOM", ()))
    unknown = bottom - set(comps)
    if unknown:
        raise SystemExit("layout.BOTTOM names parts design.py doesn't have: " + ", ".join(sorted(unknown)))
    placed = {}
    for ref in sorted(comps):
        c = comps[ref]
        fp = k.load_fp(c["footprint"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + c["uuid"]))
        fp.SetSheetname("/")
        fp.SetSheetfile(PROJECT + ".kicad_sch")
        for key, v in c["fields"].items():
            fp.SetField(key, v)
            fp.GetField(key).SetVisible(False)
        if c["dnp"] or ref[0] in "HF" or ref.startswith("TP"):
            fp.SetDNP(c["dnp"])
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
        if ref in subst:
            fp.Models()[0].m_Filename = subst[ref]
        if ref[0] in "HF":
            fp.Reference().SetVisible(False)   # holes and fiducials need no label
        board.Add(fp)
        if ref in bottom:
            # mirrored onto the bottom face; positions and orientations in layout.py stay as seen from the top
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        for p in fp.Pads():
            name = pad_net.get((ref, p.GetNumber()))
            if name:
                p.SetNet(netinfo[name])
        placed[ref] = fp

    holes = list(getattr(layout, "HOLES", []))
    hole_refs = sorted((r for r in placed if r.startswith("H") and r[1:].isdigit()), key=lambda r: int(r[1:]))
    if len(hole_refs) != len(holes):
        raise SystemExit("design.py has %d mounting holes (H1..), layout.HOLES lists %d" % (len(hole_refs), len(holes)))
    for ref, (x, y) in zip(hole_refs, holes):
        placed[ref].SetPosition(k.to_page(x, y))
    for ref, (x, y, o) in getattr(layout, "FIXED", {}).items():
        fp = placed[ref]
        fp.SetPosition(k.to_page(x, y))
        k.set_orientation(fp, o)
    for ref in getattr(layout, "TRIM_COURTYARD", ()):
        k.trim_courtyard(placed[ref])
    for ref, (x, y, d) in getattr(layout, "ROWS", {}).items():
        k.place_row(placed[ref], (x, y), d)

    hk = getattr(layout, "HOLE_KEEPOUT", 3.0)
    keepouts = list(getattr(layout, "NO_PARTS", []))
    keepouts += [(x - hk, y - hk, x + hk, y + hk) for x, y in holes]
    prefer = list(getattr(layout, "PREFER", []))
    unplaced = set(placed) - set(hole_refs) - set(getattr(layout, "FIXED", {})) - \
        set(getattr(layout, "ROWS", {})) - {r for r, *_ in prefer}
    if unplaced:
        raise SystemExit("layout.py doesn't place: %s (add them to FIXED, ROWS or PREFER)" % ", ".join(sorted(unplaced)))
    moved = []
    k.autofit(placed, prefer, keepouts, moved)

    # Outline, keep-outs, GND pour on the bottom (the top one comes with routing).
    k.add_outline(board)
    both = [pcbnew.F_Cu, pcbnew.B_Cu]
    for name, pts, *layers in getattr(layout, "NO_COPPER", []):
        k.add_rule_area(board, name, pts, layers[0] if layers else both, pads=False, footprints=False)
    for i, p in enumerate(holes):
        k.add_rule_area(board, "Post %d keep-out" % (i + 1), k.circle_pts(p, hk), both, pads=False, footprints=False)
    for ref in sorted(r for r in placed if r.startswith("FID")):
        # Freerouting doesn't see a fiducial's 0.6 mm clearance
        c = k.from_page(placed[ref].GetPosition())
        k.add_rule_area(board, ref + " keep-out", k.circle_pts(c, 1.8, 16), [pcbnew.F_Cu], pads=False, footprints=False)
    gnd = pcbnew.ZONE(board)
    gnd.SetLayer(pcbnew.B_Cu)
    gnd.SetNet(netinfo[GND])
    gnd.SetZoneName("GND pour")
    gnd.SetLocalClearance(k.mm(0.3))
    gnd.SetPadConnection(pcbnew.ZONE_CONNECTION_THT_THERMAL)
    gnd.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = gnd.Outline()
    o.NewOutline()
    for x, y in k.board_pts(0.5):
        o.Append(k.to_page(x, y))
    board.Add(gnd)

    row_labels(board, placed)
    if hasattr(layout, "silk"):
        layout.silk(board, placed)

    title = board.GetTitleBlock()
    title.SetTitle(CFG["title"])
    title.SetRevision(CFG["rev"].split()[0])
    title.SetDate(CFG["date"])
    title.SetCompany(CFG["company"])
    board.SetTitleBlock(title)
    pcbnew.SaveBoard(PCB, board)
    write_rules()
    os.makedirs(os.path.join(HW, "output"), exist_ok=True)
    with open(os.path.join(HW, "output", "placement.txt"), "w") as f:
        for ref, d in moved:
            f.write("%s moved %.1f mm from its PREFER spot\n" % (ref, d))
    print("wrote", PCB)


if __name__ == "__main__":
    main(sys.argv[2] if len(sys.argv) > 2 else os.path.join(HW, "output", PROJECT + ".net"))
