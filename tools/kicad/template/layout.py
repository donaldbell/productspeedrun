"""__TITLE__ (episode __EP__): board outline and placement for tools/kicad.

Coordinates: the Stage 4 enclosure's XY (origin at the centre, mm, +y toward the back), so the
board drops onto the model's posts. Every part in design.py goes in exactly one of HOLES (H1..),
FIXED, ROWS or PREFER; gen_pcb.py names any that are missing. See tools/kicad/example/layout.py.
"""
import pcbnew

from pcbkit import add_text, circle_rect, rect_pts, silk_circle, silk_rect  # noqa: F401

BOARD = (60.0, 40.0, 4.0)                        # width, height, corner radius: from 4-model/NOTES.md
HOLES = [(sx * 26.0, sy * 16.0) for sx in (-1, 1) for sy in (-1, 1)]   # H1..H4 on the enclosure posts
HOLE_KEEPOUT = 3.0

NO_PARTS = []         # extra rectangles (x0, y0, x1, y1) the auto-fitter avoids: tall parts above, antenna
NO_COPPER = []        # (name, points[, layers]) copper keep-outs, e.g. a module's antenna on both layers

FIXED = {             # ref -> (x, y, orientation): parts the enclosure dictates (module, buttons, sensors, LEDs)
    "FID1": (-25.0, -10.0, 0),
    "FID2": (25.0, 13.0, 0),
    "FID3": (22.0, -15.0, 0),
}
ROWS = {}             # ref -> (pin-1 x, y, (dx, dy) toward pin 2): headers, wire pads, THT sensors
ROW_LABELS = {}       # ref -> (title, [pin labels], "left" | "right" | "below")
PREFER = [            # (ref, x, y, orientation): everything else, each IC first, then its decoupling
]

MODEL_SUBST = {}      # ref -> stand-in 3D model path, for footprints KiCad ships without one
POWER_NETS = ()       # e.g. ("/VBAT", "/3V3"): 0.5 mm tracks
GND_VIA_PADS = []     # parts with a big ground pad (modules, QFNs): GND vias around their centre
PREROUTE = []         # fixed tracks before Freerouting, e.g. ("U1.5", (x, y), "via", (x, y), "via", "L1.2"); see the README


def silk(board, placed):
    add_text(board, "__TITLE_UPPER__", 0.0, 0.0, pcbnew.B_SilkS, 1.6, bold=True)
    add_text(board, "Product Speedrun __EP__  rev A", 0.0, -3.0, pcbnew.B_SilkS, 1.0)
