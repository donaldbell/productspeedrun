"""Move reference labels off pads and off each other; hide any that can't fit.

Run with KiCad's bundled Python on the routed board (tools/build.sh does this):
  "$KICAD_PY" tools/kicad/tidy_silk.py <episode>

For each reference that touches a pad, another label or another part's outline
on its silkscreen layer, tries spots around its own part (above, below, left,
right, then the corners, a little further out each round), upright, inside the
board edge. The first clear spot wins. If none is clear, the label is hidden;
the part's position is still in the assembly files.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import use_episode  # noqa: E402

ROOT = use_episode(sys.argv)
import pcbnew  # noqa: E402

import design  # noqa: E402,F401
import layout  # noqa: E402
import pcbkit  # noqa: E402
from pcbkit import CX, CY, inside_outline  # noqa: E402
from schkit import CFG  # noqa: E402

pcbkit.configure(layout)
PCB = os.path.join(ROOT, CFG["project"] + ".kicad_pcb")
EDGE_INSET = 0.5     # keep labels this far inside the board edge (mm)
PAD_GAP = 0.15       # silk-to-pad clearance (mm)
GAPS = (0.2, 0.5, 0.9, 1.4)
# Labels to hide outright (none so far).
HIDE_TEXT = set(getattr(layout, "HIDE_TEXT", ()))   # {(ref, text)}: footprint texts to take off the silk

mm = pcbnew.FromMM


def box(cx, cy, w, h, grow=0.0):
    b = pcbnew.BOX2I(pcbnew.VECTOR2I(int(cx - w / 2 - grow), int(cy - h / 2 - grow)),
                     pcbnew.VECTOR2I(int(w + 2 * grow), int(h + 2 * grow)))
    return b


def inside_board(b, centre):
    for x, y in ((b.GetLeft(), b.GetTop()), (b.GetRight(), b.GetTop()),
                 (b.GetLeft(), b.GetBottom()), (b.GetRight(), b.GetBottom())):
        if not inside_outline(pcbnew.ToMM(x) - CX, CY - pcbnew.ToMM(y), EDGE_INSET):
            return False
    return True


def obstacles(board, layer, skip_field):
    """Everything on this silk layer (except the field itself), plus exposed pads on this side."""
    copper = pcbnew.F_Cu if layer == pcbnew.F_SilkS else pcbnew.B_Cu
    out = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(copper):
                out.append((p, mm(PAD_GAP)))
        for g in fp.GraphicalItems():
            if g.GetLayer() == layer and (not hasattr(g, "IsVisible") or g.IsVisible()):
                out.append((g, mm(0.1)))
        for f in fp.GetFields():
            if f.GetLayer() == layer and f.IsVisible() and f is not skip_field and f.GetText():
                out.append((f, mm(0.1)))
    for d in board.GetDrawings():
        if d.GetLayer() == layer:
            out.append((d, mm(0.1)))
    return out


def clashes(rect, obs, skip_fp):
    for item, grow in obs:
        parent = item.GetParentFootprint() if hasattr(item, "GetParentFootprint") else None
        if parent is not None and parent.m_Uuid.AsString() == skip_fp.m_Uuid.AsString() and \
                not isinstance(item, pcbnew.PAD):
            continue    # the part's own outline may touch its own label
        r = pcbnew.BOX2I(rect.GetOrigin(), pcbnew.VECTOR2I(rect.GetWidth(), rect.GetHeight()))
        r.Inflate(grow)
        if item.HitTest(r, False):
            return True
    return False


def main():
    board = pcbnew.LoadBoard(PCB)
    centre = board.GetBoardEdgesBoundingBox().GetCenter()
    moved, hidden = [], []
    for fp in board.GetFootprints():
        for t in fp.GraphicalItems():
            if isinstance(t, pcbnew.PCB_TEXT) and (fp.GetReference(), t.GetText()) in HIDE_TEXT \
                    and t.GetLayer() == pcbnew.F_SilkS:
                t.SetLayer(pcbnew.F_Fab)    # off the silkscreen (plain text has no hide flag that sticks)
                hidden.append("%s pin-1 mark" % fp.GetReference())
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.Reference()
        if not ref.IsVisible() or ref.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        obs = obstacles(board, ref.GetLayer(), ref)
        if not clashes(ref.GetBoundingBox(), obs, fp):
            continue
        ref.SetTextAngleDegrees(0)      # upright (and mirrored text on the bottom stays readable)
        tb = ref.GetBoundingBox()
        w, h = tb.GetWidth(), tb.GetHeight()
        cb = fp.GetCourtyard(pcbnew.F_CrtYd if not fp.IsFlipped() else pcbnew.B_CrtYd).BBox()
        if cb.GetWidth() == 0:
            cb = fp.GetBoundingBox(False)
        cx, cy = cb.GetCenter().x, cb.GetCenter().y
        spot = None
        for gap in GAPS:
            g = mm(gap)
            cands = [(cx, cb.GetTop() - g - h / 2), (cx, cb.GetBottom() + g + h / 2),
                     (cb.GetLeft() - g - w / 2, cy), (cb.GetRight() + g + w / 2, cy),
                     (cb.GetLeft() - g - w / 2, cb.GetTop() - g - h / 2),
                     (cb.GetRight() + g + w / 2, cb.GetTop() - g - h / 2),
                     (cb.GetLeft() - g - w / 2, cb.GetBottom() + g + h / 2),
                     (cb.GetRight() + g + w / 2, cb.GetBottom() + g + h / 2)]
            for x, y in cands:
                r = box(x, y, w, h)
                if inside_board(r, centre) and not clashes(r, obs, fp):
                    spot = (x, y)
                    break
            if spot:
                break
        if spot:
            off = ref.GetBoundingBox().GetCenter() - ref.GetPosition()
            ref.SetPosition(pcbnew.VECTOR2I(int(spot[0] - off.x), int(spot[1] - off.y)))
            moved.append(fp.GetReference())
        else:
            ref.SetVisible(False)
            hidden.append(fp.GetReference())
    board.Save(PCB)
    print("labels moved:", " ".join(moved) or "none")
    print("hidden:", ", ".join(hidden) or "none")


if __name__ == "__main__":
    main()
