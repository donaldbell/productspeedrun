"""BMM Sensor (episode 003): board outline and placement for tools/kicad.

Coordinates: board mm (origin at the board's centre, +x right toward the back of the puck where the
USB-C is, +y up as seen from the top face). The outline, holes and everything that lines up with
the shell come from fit.json's "sensor" entry (tools/fit/README.md): change them there.

Top face: mic and status LED at the front (-x) end behind the grille, module front-left with its
antenna along the +y edge, the 6 x 6 tact under the top cap, power parts and USB-C at the back.
Bottom face: 0603 passives only (<= 1.0 mm: the LiPo is 1.0 mm below the board).
Module pads (ESP32-C6-MINI-1 at (-9.45, -1.4)): left column x -15.35: 3V3 (pad 3) y 1.0, IO2 MIC_SD
-0.6, IO3 LED -1.4, EN -3.0, IO4 MIC_SCK -3.8, IO5 MIC_WS -4.6; bottom row y -6.3: IO0 x -14.25,
IO1 -13.45, IO7 BTN -11.05, IO12 -10.25, IO13 -9.45, IO8 -6.25.
"""
import pcbnew

from fitlib import load_fit
from pcbkit import add_text, circle_rect, rect_pts  # noqa: F401

FIT = load_fit(__file__)                         # ../../../fit.json, board "sensor"
BOARD = FIT.board_tuple()                        # 44 x 20 R3
HOLES = [tuple(h) for h in FIT.holes]            # H1, H2 on the base posts
HOLE_KEEPOUT = 2.2
HOLE_CLEARANCE = 0.18      # GCT USB4105's stock footprint has its GND pads 0.19 mm from the locating pegs (NPTH)

MIC = FIT.feature("mic")
LED = FIT.feature("status_led")
BUTTON = FIT.feature("button")
USB = FIT.feature("usb")
MODULE = FIT.feature("module")
ANTENNA = FIT.keepout("antenna")

NO_PARTS = [ANTENNA]
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA))]
TRIM_COURTYARD = ["U3"]
HIDE_TEXT = {("SW1", "REF**")}           # the 1TS009 footprint carries a second reference text

FIXED = {
    "U3": (MODULE[0], MODULE[1], 0),
    "U4": (MIC[0], MIC[1] + 0.71, 0),     # footprint origin sits 0.71 mm above its port hole
    "LED1": (LED[0], LED[1], 0),
    "SW1": (BUTTON[0], BUTTON[1], 0),
    "J1": (USB[0], USB[1], 90),           # mouth (footprint +y) toward +x
}
ROWS = {
    "J2": (4.4, -7.8, (1, 0)),            # LiPo + / -, below the button, clear of the BTN track
}
ROW_LABELS = {
    "J2": ("BAT", ["+", "-"], "above"),
}
BOTTOM = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R9",
          "C1", "C2", "C5", "C7", "C8", "C9"]
PREFER = [
    # charger and power path above and below the USB-C (top)
    ("U1", 12.0, 6.4, 0), ("D1", 16.2, 7.0, 0), ("Q1", 16.5, -7.4, 0),
    # LDO beside the button, its VSYS input cap and 3V3 output cap right at its pins
    ("U2", 1.5, 6.8, 0), ("C3", 5.2, 7.6, 90), ("C4", -0.5, 3.4, 0),
    # module bulk cap at the front, between the mic and H1; small decoupling under pad 3
    ("C6", -20.0, -2.0, 90), ("C7", -13.8, 1.0, 0), ("R7", -13.8, -3.0, 0), ("C8", -13.8, -4.8, 0),
    ("R8", -6.25, -8.4, 0),                                 # IO8 strap, top, straight below its pad
    ("TP1", -2.8, -2.0, 0),
    # bottom: USB CC, PROG, charger caps, gate pull-down, battery sense
    ("R1", 13.5, 2.0, 90), ("R2", 13.5, -2.0, 90), ("C1", 11.0, 4.0, 0), ("R3", 9.5, 7.5, 90),
    ("C2", 8.0, 4.5, 0), ("R4", 9.5, -7.5, 90),
    ("R5", 1.0, -3.0, 90), ("R6", 2.5, -3.0, 90), ("C5", 1.0, -6.0, 0),
    ("C9", -19.5, 1.0, 0),                                 # mic decoupling, under it
    ("R9", -17.0, 8.6, 0),                                  # status LED resistor
]

MODEL_SUBST = {
    "U3": "${KIPRJMOD}/../../../../tools/kicad/models/ESP32-C6-MINI-1.step",
}
POWER_NETS = ("/VBUS", "/VSYS", "/VBAT")
GND_VIA_PADS = ["U3"]
# BTN runs from the module's bottom-left pin (IO7, the nearest LP GPIO: it has to wake the C6) to the
# button, the length of the board. Freerouting kept leaving it open, so lay it by hand: a via just
# below the pad, along the bottom just under the module's pin row (the top-side escapes cross over
# it), then up beside the button.
PREROUTE = [
    ("U3.16", (-11.05, -7.3), "via", (2.8, -7.3), "via", (2.8, -1.2), "SW1.1"),
]


def silk(board, placed):
    add_text(board, "BABY MONITOR MONITOR", -9.0, 7.6, pcbnew.B_SilkS, 0.8, bold=True)   # under the antenna: no parts there
    add_text(board, "SENSOR  PS 003  rev A", -9.5, 6.0, pcbnew.B_SilkS, 0.8)
