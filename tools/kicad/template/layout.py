"""__TITLE__ (episode __EP__): board outline and placement for tools/kicad.

Coordinates: board mm (origin at the board's centre, +x right, +y up as seen from the top face).
The outline, holes and everything that lines up with the enclosure come from the episode's
fit.json, which Stage 4's model reads too (tools/fit/README.md): change them there, not here.
Every part in design.py goes in exactly one of HOLES (H1..), FIXED, ROWS or PREFER; gen_pcb.py
names any that are missing. See tools/kicad/example/layout.py.
"""
import pcbnew

from fitlib import load_fit
from pcbkit import add_text, circle_rect, rect_pts, silk_circle, silk_rect  # noqa: F401

FIT = load_fit(__file__)                         # ../../fit.json
BOARD = FIT.board_tuple()                        # width, height, corner radius
HOLES = [tuple(h) for h in FIT.holes]            # H1.. on the enclosure posts
HOLE_KEEPOUT = 3.0
# Line parts up with FIT.feature("<name>"), e.g. PIR_AT = FIT.feature("pir"); keep-outs with FIT.keepout("<name>").

NO_PARTS = []         # extra rectangles (x0, y0, x1, y1) the auto-fitter avoids: tall parts above, antenna
NO_COPPER = []        # (name, points[, layers]) copper keep-outs, e.g. a module's antenna on both layers

FIXED = {             # ref -> (x, y, orientation): parts the enclosure dictates (module, buttons, sensors, LEDs)
    "FID1": (-25.0, -10.0, 0),
    "FID2": (25.0, 13.0, 0),
    "FID3": (22.0, -15.0, 0),
}
ROWS = {}             # ref -> (pin-1 x, y, (dx, dy) toward pin 2): headers, wire pads, THT sensors
ROW_LABELS = {}       # ref -> (title, [pin labels], "left" | "right" | "below" | "above"[, title (x, y)])
PREFER = [            # (ref, x, y, orientation): everything else, each IC first, then its decoupling
]

MODEL_SUBST = {}      # ref -> stand-in 3D model path, for footprints KiCad ships without one
POWER_NETS = ()       # e.g. ("/VBAT", "/3V3"): 0.5 mm tracks
GND_VIA_PADS = []     # parts with a big ground pad (modules, QFNs): GND vias around their centre
PREROUTE = []         # fixed tracks before Freerouting, e.g. ("U1.5", (x, y), "via", (x, y), "via", "L1.2"); see the README


def silk(board, placed):
    add_text(board, "__TITLE_UPPER__", 0.0, 0.0, pcbnew.B_SilkS, 1.6, bold=True)
    add_text(board, "Product Speedrun __EP__  rev A", 0.0, -3.0, pcbnew.B_SilkS, 1.0)
