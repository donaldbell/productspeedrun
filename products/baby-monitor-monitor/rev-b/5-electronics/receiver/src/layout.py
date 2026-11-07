"""BMM Receiver (episode 003): board outline and placement for tools/kicad.

Coordinates: board mm (origin at the board's centre, +x right, +y up as seen from the top face,
which looks up through the watch's lens). The outline, holes and everything that lines up with
the case come from fit.json's "receiver" entry (tools/fit/README.md): change them there.

Sealed watch: no USB, no button. Top face (parts <= 2.6 mm under the lens): module (antenna at the
12 o'clock edge), glow LED under the lens, link LED at 6 o'clock, charger, LDO, flashing pads.
Bottom face: the two pogo pins onto the back plate's charge contacts, the motor switch over the ERM
(2.6 mm below), 0603 passives over the LiPo (1.0 mm below the board, x < 3.1).
Module pads (ESP32-C6-MINI-1 at (0.4, 3.6)): left column x -5.5, 3V3 (pad 3) y 6.0, EN (pad 8) y 2.0,
IO2 MOT_PWM 4.4; bottom row y -1.3: IO0 x -4.4, IO1 -3.6, IO6 -2.0, IO7 -1.2, IO12 -0.4, IO13 0.4, IO8 3.6.
"""
import pcbnew

from fitlib import load_fit
from pcbkit import add_text, circle_rect, rect_pts  # noqa: F401

FIT = load_fit(__file__)                         # ../../../fit.json, board "receiver"
BOARD = FIT.board_tuple()                        # 30 x 30 R8
HOLES = [tuple(h) for h in FIT.holes]            # H1, H2: lid posts (Ø3.6) with heat-stake pins
HOLE_KEEPOUT = 2.2                               # Ø4 clear round each post, plus a little

GLOW = FIT.feature("glow_led")
LINK = FIT.feature("link_led")
MODULE = FIT.feature("module")
POGO_POS = FIT.feature("pogo_pos")
POGO_NEG = FIT.feature("pogo_neg")
ANTENNA = FIT.keepout("antenna")

NO_PARTS = [ANTENNA]
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA))]
TRIM_COURTYARD = ["U3"]      # the stock courtyard is a 43 x 20 mm antenna clearance zone

FIXED = {
    "U3": (MODULE[0], MODULE[1], 0),
    "LED1": (GLOW[0], GLOW[1], 0),
    "LED2": (LINK[0], LINK[1], 90),
    "P1": (POGO_POS[0], POGO_POS[1], 0),  # bottom face (BOTTOM), pressing on the back plate's contacts
    "P2": (POGO_NEG[0], POGO_NEG[1], 0),
}
ROWS = {
    "J2": (-8.0, -12.6, (1, 0)),          # LiPo + / -, at the cell's tab end (cell y -12.5..12.5)
    "J3": (12.6, 5.6, (0, 1)),            # motor + / -, right side
}
ROW_LABELS = {}       # "+" marks come from silk() below
BOTTOM = ["P1", "P2", "D2",
          "R1", "R2", "R3", "R4", "R5", "R7",
          "C2", "C4", "C6", "C7", "C9",
          "Q1", "R6", "D1"]               # Q1, R6, D1 over the motor (x > 3.1): room for SOT-23
PREFER = [
    # charge input on the bottom beside the + pogo pin, charger and LDO on the top where the USB-C was
    ("D2", 5.5, -7.2, 0),
    ("U1", -10.0, -3.0, 90), ("C1", -12.6, -3.0, 90), ("R1", -10.0, -7.0, 0),
    ("C2", -7.0, -6.0, 90),
    ("U2", -10.0, 3.5, 90), ("C3", -12.6, 3.5, 90), ("C5", -7.6, 7.0, 90),
    ("TP2", -12.5, 7.5, 0), ("TP3", -12.5, -7.5, 0), ("TP1", 6.5, -7.2, 0),
    # module decoupling at pad 3 (bottom, under the module's left column), EN RC at pad 8
    ("C6", -5.0, 6.6, 0), ("R4", -5.0, 1.0, 0), ("C7", -2.4, 1.0, 0),
    ("R5", 3.6, -3.4, 90),                                   # IO8 strap
    ("R2", -2.0, -13.4, 0), ("R3", -6.0, -13.4, 0), ("C4", -2.0, -11.0, 0),    # VBAT sense
    # glow LED cap beside it, link LED resistor beside it
    ("C9", 2.2, -5.0, 90), ("R7", 2.2, -11.6, 90),
    # motor switch on the bottom over the ERM, bulk cap on the top
    ("Q1", 8.0, 8.0, 0), ("R6", 5.0, 8.0, 90), ("D1", 10.0, 11.0, 0),
    ("C8", 9.6, 9.0, 90),
]

MODEL_SUBST = {
    "U3": "${KIPRJMOD}/../../../../../tools/kicad/models/ESP32-C6-MINI-1.step",
    "LED1": "${KICAD10_3DMODEL_DIR}/LED_SMD.3dshapes/LED_RGB_Wuerth-PLCC4_3.2x2.8mm_150141M173100.step",
    "P1": "${KIPRJMOD}/../../../../../tools/kicad/models/PogoPin_D1.8mm_H5.0mm.step",
    "P2": "${KIPRJMOD}/../../../../../tools/kicad/models/PogoPin_D1.8mm_H5.0mm.step",
}
POWER_NETS = ("/VCHG_IN", "/VBUS", "/VBAT")
GND_VIA_PADS = ["U3"]
PREROUTE = []


def silk(board, placed):
    add_text(board, "+", -9.3, -12.6, pcbnew.F_SilkS, 0.9)        # J2 pin 1: LiPo +
    add_text(board, "+", 11.2, 5.6, pcbnew.F_SilkS, 0.9)          # J3 pin 1: motor +
    add_text(board, "BABY MONITOR MONITOR", 0.0, 12.6, pcbnew.B_SilkS, 0.8, bold=True)   # under the antenna: no parts there
    add_text(board, "RECEIVER  PS 003  rev B", 0.0, 11.2, pcbnew.B_SilkS, 0.8)
