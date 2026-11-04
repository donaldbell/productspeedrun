"""BMM Receiver (episode 003): board outline and placement for tools/kicad.

Coordinates: board mm (origin at the board's centre, +x right, +y up as seen from the top face,
which looks up through the watch's lens). The outline, holes and everything that lines up with
the case come from fit.json's "receiver" entry (tools/fit/README.md): change them there.

Top face: module (antenna at the 12 o'clock edge), USB-C at 9 o'clock, side button at 3 o'clock,
glow LED under the lens, link LED at 6 o'clock, charger and LDO. Bottom face: 0603 passives
(<= 1.0 mm: the LiPo is 1.0 mm below the board on the left, x < 3.1) and the motor switch on the
right, where the ERM sits 2.6 mm below.
Module pads (ESP32-C6-MINI-1 at (0.4, 3.6)): left column x -5.5, 3V3 (pad 3) y 6.0, EN (pad 8) y 2.0,
IO2 4.4, IO3 3.6; bottom row y -1.3: IO0 x -4.4, IO1 -3.6, IO6 -2.0, IO7 -1.2, IO12 -0.4, IO13 0.4, IO8 3.6.
"""
import pcbnew

from fitlib import load_fit
from pcbkit import add_text, circle_rect, rect_pts  # noqa: F401

FIT = load_fit(__file__)                         # ../../../fit.json, board "receiver"
BOARD = FIT.board_tuple()                        # 30 x 30 R8
HOLES = [tuple(h) for h in FIT.holes]            # H1, H2: lid posts (Ø3.6) with heat-stake pins
HOLE_KEEPOUT = 2.2                               # Ø4 clear round each post, plus a little
HOLE_CLEARANCE = 0.18      # GCT USB4105's stock footprint has its GND pads 0.19 mm from the locating pegs (NPTH)

USB = FIT.feature("usb")
BUTTON = FIT.feature("button")
GLOW = FIT.feature("glow_led")
LINK = FIT.feature("link_led")
MODULE = FIT.feature("module")
ANTENNA = FIT.keepout("antenna")

NO_PARTS = [ANTENNA]
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA))]
TRIM_COURTYARD = ["U3"]      # the stock courtyard is a 43 x 20 mm antenna clearance zone

FIXED = {
    "U3": (MODULE[0], MODULE[1], 0),
    "J1": (USB[0], USB[1], 270),          # mouth (footprint +y) toward -x
    "SW1": (BUTTON[0], BUTTON[1], 270),   # plunger (footprint -y) toward +x
    "LED1": (GLOW[0], GLOW[1], 0),
    "LED2": (LINK[0], LINK[1], 90),
}
ROWS = {
    "J2": (-8.0, -12.6, (1, 0)),          # LiPo + / -, at the cell's tab end (cell y -12.5..12.5)
    "J3": (12.6, 5.6, (0, 1)),            # motor + / -, right side above the button
}
ROW_LABELS = {}       # "+" marks come from silk() below: the labels collided with U1/U2 and C8
BOTTOM = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9",
          "C2", "C4", "C6", "C7", "C9",
          "Q1", "D1"]                     # Q1, D1 over the motor (x > 3.1): room for SOT-23
PREFER = [
    # power on the top, lower half: charger beside the USB, LDO between it and the module
    ("U1", -9.0, -8.0, 0), ("C1", -12.0, -6.5, 90), ("R3", -9.0, -10.6, 0), ("R1", -9.5, -5.6, 0), ("R2", -12.5, -9.0, 90),
    ("C2", -6.0, -8.0, 90),
    ("U2", -4.0, -10.5, 0), ("C3", -4.0, -7.6, 0), ("C5", -7.0, 1.0, 90),
    # module decoupling at pad 3 (bottom, under the module's left column), EN RC at pad 8
    ("C6", -5.0, 6.6, 0), ("R6", -5.0, 1.0, 0), ("C7", -2.4, 1.0, 0),
    ("R7", 3.6, -3.4, 90),                                   # IO8 strap
    ("TP1", 6.5, -7.2, 0),
    ("R4", -2.0, -13.4, 0), ("R5", -6.0, -13.4, 0), ("C4", -2.0, -11.0, 0),    # VBAT sense
    # glow LED cap beside it, link LED resistor beside it
    ("C9", 2.2, -5.0, 90), ("R9", 2.2, -11.6, 90),
    # motor switch on the bottom, right half (over the ERM)
    ("Q1", 8.0, 8.0, 0), ("R8", 5.0, 8.0, 90), ("D1", 10.0, 11.0, 0),
    ("C8", 9.6, 9.0, 90),                                    # motor bulk (0805, top: too tall for over the cell)
]

MODEL_SUBST = {
    "U3": "${KIPRJMOD}/../../../../tools/kicad/models/ESP32-C6-MINI-1.step",
    "LED1": "${KICAD10_3DMODEL_DIR}/LED_SMD.3dshapes/LED_RGB_Wuerth-PLCC4_3.2x2.8mm_150141M173100.step",
}
POWER_NETS = ("/VBUS", "/VBAT")
GND_VIA_PADS = ["U3"]
PREROUTE = []


def silk(board, placed):
    add_text(board, "+", -9.3, -12.6, pcbnew.F_SilkS, 0.9)        # J2 pin 1: LiPo +
    add_text(board, "+", 11.2, 5.6, pcbnew.F_SilkS, 0.9)          # J3 pin 1: motor +
    add_text(board, "BABY MONITOR MONITOR", 0.0, 12.6, pcbnew.B_SilkS, 0.8, bold=True)   # under the antenna: no parts there
    add_text(board, "RECEIVER  PS 003  rev A", 0.0, 11.2, pcbnew.B_SilkS, 0.8)
