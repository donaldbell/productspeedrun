"""nRF52840 block: outline and placement. A 32 x 44 mm board, module antenna on the top edge with a
copper-free band across the board, USB-C on the bottom edge, LDO and USB parts between them.

MDBT50Q pads (module origin at MODULE, antenna at +y): outer left column x = -4.65, outer right
x = +4.65, outer bottom row y = -7.15 (relative to MODULE). VDD (28) and VDDH (30) are bottom-row
pads at x = 1.6 and 2.4, VBUS (32) at 4.0; D- / D+ (34 / 35) are the lowest right-hand pads.
"""
import pcbnew

from pcbkit import add_text, rect_pts

BOARD = (32.0, 44.0, 3.0)
HOLES = [(sx * 12.5, sy * 18.5) for sx in (-1, 1) for sy in (-1, 1)]
HOLE_KEEPOUT = 3.0

MODULE = (0.0, 12.0)
ANTENNA_KEEPOUT = (-16.0, MODULE[1] + 3.8, 16.0, 22.0)    # module's antenna end to the top edge, full width
NO_PARTS = [ANTENNA_KEEPOUT]
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA_KEEPOUT))]

FIXED = {
    "U2": (MODULE[0], MODULE[1], 0),
    "J1": (0.0, -18.0, 0),                 # USB-C, mouth on the bottom edge
    "J2": (10.5, 10.0, 90),                # TC2030 beside SWDIO / SWDCLK (pads 51 / 53)
    "FID1": (-13.5, 4.0, 0),
    "FID2": (13.5, -4.0, 0),
    "FID3": (-13.5, -12.0, 0),
}
ROWS = {}
ROW_LABELS = {}
PREFER = [
    # module decoupling at the bottom row's VDD / VDDH / VBUS pads
    ("C3", 2.0, 2.8, 90), ("C4", 4.2, 2.8, 90),
    # LDO between the USB-C and the module
    ("U1", -6.0, -6.0, 90), ("C1", -9.0, -8.0, 90), ("C2", -3.0, -6.0, 90),
    ("R1", -5.0, -12.0, 90), ("R2", 5.0, -12.0, 90),
    # reset and LED on the right
    ("SW1", 10.0, -3.5, 0), ("R3", 8.5, 4.5, 0), ("D1", 12.5, 4.5, 0),
]

MODEL_SUBST = {}
POWER_NETS = ()          # the module's pads are 0.8 mm apart: keep every net on 0.25 mm tracks
GND_VIA_PADS = ["U2"]
PREROUTE = []


def silk(board, placed):
    add_text(board, "ANTENNA", MODULE[0], MODULE[1] + 9.0, pcbnew.F_Fab, 1.0)
    add_text(board, "nRF52840 BLOCK", 0.0, -4.0, pcbnew.B_SilkS, 1.4, bold=True)
    add_text(board, "Product Speedrun kit  rev A", 0.0, -6.5, pcbnew.B_SilkS, 1.0)
