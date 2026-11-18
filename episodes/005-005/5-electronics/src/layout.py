"""Smart Bucket Hat (episode 005): board outline and placement for tools/kicad.

Coordinates: board mm (origin at the board's centre, +x right, +y up as seen from the top face).
The outline, holes and everything that lines up with the enclosure come from the episode's
fit.json, which Stage 4's model reads too (tools/fit/README.md): change them there, not here.

The pod board: the XIAO nRF52840 Sense in the middle with its USB-C on the lower edge and its antenna
end up (copper-free above it), band half A's switch, buffer and plug on the left, half B's on the right,
each SMD plug at a top corner, mouth on the side edge, so the leads run straight into the band. The charger sits by the XIAO's
5V pin; the cells' pads sit low on each side, toward the cells.
XIAO at orientation 180 (USB-C toward -y), pads relative to its centre: D0..D6 (pins 1-7) on the
right at x +8.07, y -7.62..+7.62 (D0 at the USB end); D7..D10, 3V3, GND, 5V (pins 8-14) on the left at
x -8.1, y +7.62..-7.62 (5V at the USB end); BAT+ (+4.46, -0.31), BAT- (+4.46, -2.22).
"""
import pcbnew

from fitlib import load_fit
from pcbkit import add_text, circle_rect, rect_pts, silk_circle, silk_rect  # noqa: F401

FIT = load_fit(__file__)                         # ../../fit.json
BOARD = FIT.board_tuple()                        # width, height, corner radius
HOLES = [tuple(h) for h in FIT.holes]            # H1.. on the pod's posts
HOLE_KEEPOUT = 2.4
W2, H2 = BOARD[0] / 2.0, BOARD[1] / 2.0

MODULE = FIT.feature("module")                   # XIAO centre
BUTTON = FIT.feature("button")
PLUG_A, PLUG_B = FIT.feature("plug_a"), FIT.feature("plug_b")    # the plugs' mouths, on the side edges
mx, my = MODULE

# the XIAO's antenna end (away from the USB-C): no copper between its pad rows or beyond its end
ANTENNA = FIT.keepout("antenna") if "antenna" in FIT.keepouts else (mx - 6.4, my + 7.0, mx + 6.4, H2)
# its own underside test pads sit on the carrier's mask: no copper under them
XIAO_SWD = (mx - 2.3, my - 9.7, mx + 2.3, my - 4.9)
XIAO_NFC = (mx - 7.0, my + 8.0, mx - 2.6, my + 10.4)

NO_PARTS = [ANTENNA]
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA)), ("XIAO SWD pads", rect_pts(XIAO_SWD)),
             ("XIAO NFC pads", rect_pts(XIAO_NFC))]

# JST PH SMD side entry (S3B-PH-SM4-TB): footprint origin between the signal pads, the mouth 4.4 mm in
# front of it and the mounting tabs to 4.6. Orientation 270 opens toward -x (pin 1 on top), 90 toward +x.
PH_SET = 5.2                                     # origin to the side edge: mouth 0.8 inside, tabs 0.6 clear
FIXED = {
    "U1": (mx, my, 180),
    "SW1": (BUTTON[0], BUTTON[1], 0),
    "J3": (PLUG_A[0] + PH_SET, PLUG_A[1], 270),
    "J4": (PLUG_B[0] - PH_SET, PLUG_B[1], 90),
    "FID1": (-10.5, H2 - 2.0, 0),               # between the antenna keep-out and the plugs
    "FID2": (10.5, H2 - 2.0, 0),
    "FID3": (mx - 12.5, -H2 + 2.0, 0),
}
CELL_PADS_Y = FIT.feature("cells")[1] if "cells" in FIT.features else my
ROWS = {              # cell leads: + on top
    "J1": (-W2 + 2.6, CELL_PADS_Y + 1.8, (0, -1)),
    "J2": (W2 - 2.6, CELL_PADS_Y + 1.8, (0, -1)),
}
ROW_LABELS = {
    "J1": ("A", ["+", "-"], "right"),
    "J2": ("B", ["+", "-"], "left"),
}
lx, rx = mx - 14.0, mx + 14.0                    # the middle of each side
PREFER = [
    # charger beside the XIAO's 5V pin (bottom-left), its caps either side
    ("U2", lx, my - 7.0, 0), ("C2", lx + 1.5, my - 10.2, 0), ("C3", lx - 3.5, my - 9.5, 90),
    ("R1", lx - 3.5, my - 5.0, 90), ("R2", lx + 1.5, my - 3.8, 0), ("C1", lx - 1.0, my - 0.5, 90),
    # half A (left): switch, bulk, buffer, series R toward J3
    ("Q1", lx, my + 3.6, 90), ("C4", lx - 3.6, my + 3.0, 90), ("C5", lx + 3.0, my + 3.0, 90),
    ("U3", lx + 0.5, my + 10.0, 0), ("C8", lx + 0.5, my + 13.0, 0), ("R6", lx - 3.2, my + 12.5, 90),
    # half B (right): the same, mirrored
    ("Q2", rx, my + 3.6, 90), ("C6", rx + 3.6, my + 3.0, 90), ("C7", rx - 3.0, my + 3.0, 90),
    ("U4", rx - 0.5, my + 10.0, 0), ("C9", rx - 0.5, my + 13.0, 0), ("R7", rx + 3.2, my + 12.5, 90),
    # the gate driver for both switches, beside D2 (LED_EN)
    ("Q3", rx, my - 1.5, 0), ("R3", rx + 3.4, my - 1.0, 90), ("R4", rx - 2.6, my - 4.2, 0),
    ("R5", rx + 1.0, my - 4.2, 0),
]

MODELS = "${KIPRJMOD}/../../../tools/kicad/models/"
MODEL_SUBST = {"U1": MODELS + "Seeed_XIAO_nRF52840.step", "J3": MODELS + "JST_PH_S3B-PH-SM4-TB.step",
               "J4": MODELS + "JST_PH_S3B-PH-SM4-TB.step"}
POWER_NETS = ("/VBAT", "/VLED_A", "/VLED_B", "/VBUS")
GND_VIA_PADS = []
PREROUTE = []


def silk(board, placed):
    add_text(board, "SMART BUCKET HAT", 0.0, 2.5, pcbnew.B_SilkS, 1.6, bold=True)
    add_text(board, "Product Speedrun 005  rev A", 0.0, 0.0, pcbnew.B_SilkS, 1.0)
    add_text(board, "XIAO nRF52840 Sense carrier", 0.0, -2.0, pcbnew.B_SilkS, 1.0)
    add_text(board, "A", PLUG_A[0] + PH_SET + 4.2, PLUG_A[1] - 4.0, pcbnew.F_SilkS, 1.2, bold=True)
    add_text(board, "B", PLUG_B[0] - PH_SET - 4.2, PLUG_B[1] - 4.0, pcbnew.F_SilkS, 1.2, bold=True)
