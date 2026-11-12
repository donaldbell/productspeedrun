"""Aquarium Accent Light (episode 004): board outline and placement for tools/kicad.

Coordinates: board mm (origin at the board's centre, +x toward the electronics end of the bar, +y up
as seen from the top face). The top face is the LED face; in use it hangs under the lid looking down
at the water. The outline, holes and everything that lines up with the enclosure come from fit.json
(tools/fit/README.md): change them there, not here.

Along the bar, from -x: APDS-9960 under the dome, porthole button, the 12 LEDs under the window
squares (LED1 nearest the XIAO, so the data runs out from it), the LED power switch, the XIAO across
the bar (USB-C at the -y edge, its antenna end at +y, copper-free under it), then the APDS-9251 under
the chrome oval. Every part is on the top face; the bottom is a bare GND pour the cells lie on.
XIAO on the BOTTOM face, pads seen from the top (USB-C toward -y), relative to its centre: D0..D6 (pins 1-7) at
x -8.06, y -7.62..+7.62 (facing the LEDs); D7..D10, 3V3, GND, 5V (pins 8-14) at x +8.1, y +7.62..-7.62;
BAT+ (-1.79, +5.53), BAT- (+0.75, +5.53).
"""
import pcbnew

from fitlib import load_fit
import math

from pcbkit import add_shape, add_text, circle_rect, rect_pts, silk_circle  # noqa: F401

FIT = load_fit(__file__)                         # ../../fit.json
BOARD = FIT.board_tuple()
HOLES = [tuple(h) for h in FIT.holes]
HOLE_KEEPOUT = 2.2

MODULE = FIT.feature("module")                   # XIAO centre
DOME = FIT.feature("dome")                       # APDS-9960
COLOR = FIT.feature("color")                     # APDS-9251
BUTTON = FIT.feature("button")
LEDS = sorted((FIT.feature(n) for n in FIT.features if n.startswith("led") and n[3:].isdigit()),
              key=lambda p: -p[0])               # LED1 nearest the XIAO (+x)
ANTENNA = FIT.keepout("antenna")
VIEW = FIT.feature("view")                       # smoked window in the deck above the XIAO
VW, VH = FIT.features["view"]["size"]
CELLS = [FIT.feature(n) for n in ("cell1", "cell2")]
W2 = BOARD[1] / 2.0
mx, my = MODULE

# the XIAO's own underside test pads (Seeed footprint pads 15-22) sit on the carrier's mask: no vias under them
XIAO_TEST_PADS = (mx - 2.3, my - 9.7, mx + 2.3, my - 0.1)

VIEW_RECT = (VIEW[0] - VW / 2, VIEW[1] - VH / 2, VIEW[0] + VW / 2, VIEW[1] + VH / 2)
CELL_RECTS = [(x - 40.5, y - 10.5, x + 40.5, y + 10.5) for x, y in CELLS]     # 4 x 20 x 80 cells, 0.3 mm below
NO_PARTS = [ANTENNA, (circle_rect(DOME, 3.2), "F"), (VIEW_RECT, "F")]          # the window shows the top: art only
NO_PARTS += [(r, "B") for r in CELL_RECTS] + [(circle_rect(r, 2.6), "B") for r in FIT.rests]
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA)), ("XIAO test pads", rect_pts(XIAO_TEST_PADS))]

FIXED = {
    "U1": (mx, my, 180),                         # bottom face (BOTTOM), USB-C toward -y, out through the side wall
    "U2": (DOME[0], DOME[1], 0),
    "U3": (COLOR[0], COLOR[1], 0),
    "SW1": (BUTTON[0], BUTTON[1], 0),
    "FID1": (BUTTON[0] - 9.0, W2 - 2.8, 0),      # clear of the end holes H1..H4
    "FID2": (COLOR[0] - 5.0, -W2 + 2.8, 0),
    "FID3": (0.0, -W2 + 3.0, 0),
}
for i, (x, y) in enumerate(LEDS):
    FIXED["LED%d" % (i + 1)] = (x, y, 0)

# bottom face: the XIAO, and the sense dividers / pull-ups between cell B's end and the XIAO's D0-D6 row
BOTTOM = ["U1", "R1", "R2", "C2", "R3", "R4", "R7", "R5", "R6", "C1"]

# cell pads (THT, leads up from the bottom) just past each cell's outer end: cell1's tabs at -x, cell2's at +x
J1_X = CELL_RECTS[0][0] - 3.5
J2_X = CELL_RECTS[1][2] + 3.0
ROWS = {
    "J1": (J1_X, 5.5, (0, -1)),
    "J2": (J2_X, 5.5, (0, -1)),
}
ROW_LABELS = {
    "J1": ("A", ["+", "-"], "left"),
    "J2": ("B", ["+", "-"], "left"),
}

x_sw = (J2_X + VIEW_RECT[0]) / 2.0 + 0.5        # the gap between cell B's pads and the XIAO window
PREFER = [
    # LED power switch and VLED bulk, between LED1 and the XIAO
    ("Q1", x_sw, -4.5, 90), ("R10", x_sw - 2.6, -7.5, 0), ("Q2", x_sw, 1.5, 90),
    ("R11", x_sw + 1.0, 5.0, 0), ("R12", x_sw - 2.6, 4.0, 90), ("C8", x_sw - 3.6, -3.0, 90),
    ("R13", x_sw + 1.0, 7.5, 0), ("C1", J2_X, -6.0, 90),
    # bottom: battery and USB sense, I2C and button pull-ups, beside the XIAO's D0-D6 row (x = mx - 8.06)
    ("R1", mx - 12.0, my - 8.6, 0), ("R2", mx - 12.0, my - 6.8, 0), ("C2", mx - 15.0, my - 7.7, 90),
    ("R3", mx - 12.0, my - 5.0, 0), ("R4", mx - 12.0, my - 3.2, 0),
    ("R7", mx - 12.0, my - 1.4, 0), ("R5", mx - 12.0, my + 2.2, 0), ("R6", mx - 12.0, my + 4.0, 0),
    # colour sensor decoupling and INT pull-up
    ("C7", COLOR[0], COLOR[1] + 2.6, 0), ("R9", COLOR[0], COLOR[1] - 2.6, 0),
    # proximity sensor decoupling, IR LED supply cap, INT pull-up, 3V3 bulk at the far end
    ("C4", DOME[0] - 3.6, DOME[1] + 1.0, 90), ("C5", DOME[0] - 3.6, DOME[1] - 2.0, 90),
    ("C6", DOME[0] + 3.6, DOME[1] + 1.0, 90), ("R8", DOME[0] + 3.6, DOME[1] - 2.2, 90),
    ("C3", DOME[0] + 6.5, DOME[1] - 5.0, 0),
]
for i, (x, y) in enumerate(LEDS):
    PREFER.append(("C%d" % (10 + i), x + 2.6, y + 2.6, 0))      # 100 nF by each LED's VDD

MODELS = "${KIPRJMOD}/../../../tools/kicad/models/"
MODEL_SUBST = {"U1": MODELS + "Seeed_XIAO_ESP32C6.step", "U2": MODELS + "APDS-9960.step",
               "U3": MODELS + "Broadcom_LGA-8_2x2mm.step"}
MODEL_SUBST.update({"LED%d" % (i + 1): MODELS + "WS2812B-2020.step" for i in range(len(LEDS))})
POWER_NETS = ("/VBAT", "/VLED")
GND_VIA_PADS = []
PREROUTE = []


def gear(board, c, r_out, r_root, teeth, width=0.2):
    """A spur-gear outline in silkscreen: square teeth between r_root and r_out."""
    pts = []
    for k in range(teeth):
        a0 = 2 * math.pi * k / teeth
        for da, r in ((0.0, r_root), (0.12, r_root), (0.17, r_out), (0.33, r_out), (0.38, r_root)):
            a = a0 + da * 2 * math.pi / teeth * 2
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    for p, q in zip(pts, pts[1:] + pts[:1]):
        add_shape(board, pcbnew.F_SilkS, width, pcbnew.SHAPE_T_SEGMENT, a=p, b=q)


def silk(board, placed):
    # the smoked viewing window shows this patch of the top face: brass-coloured "machinery" (Stage 4's ask)
    gear(board, (VIEW[0] - 2.5, VIEW[1] + 0.5), 5.6, 4.6, 14)
    silk_circle(board, (VIEW[0] - 2.5, VIEW[1] + 0.5), 1.6, width=0.25)
    silk_circle(board, (VIEW[0] - 2.5, VIEW[1] + 0.5), 3.4, width=0.15)
    gear(board, (VIEW[0] + 5.6, VIEW[1] - 3.6), 3.1, 2.4, 9)
    silk_circle(board, (VIEW[0] + 5.6, VIEW[1] - 3.6), 0.9, width=0.2)
    add_text(board, "N\u00b0 004", VIEW[0] + 5.6, VIEW[1] + 3.8, pcbnew.F_SilkS, 1.0, bold=True)
    add_text(board, "AQUARIUM ACCENT LIGHT", -40.0, 2.0, pcbnew.B_SilkS, 1.6, bold=True)
    add_text(board, "Product Speedrun 004  rev A  -  XIAO ESP32C6 carrier", -40.0, -1.5, pcbnew.B_SilkS, 1.0)
