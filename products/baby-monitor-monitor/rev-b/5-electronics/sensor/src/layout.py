"""BMM Sensor (episode 003): board outline and placement for tools/kicad.

Coordinates: board mm (origin at the board's centre, +x right toward the back of the bean where the
USB-C and power switch are, +y up as seen from the top face). The outline, holes and everything that
lines up with the shell come from fit.json's "sensor" entry (tools/fit/README.md): change them there.

Top face: mic and status LED at the front (-x) end behind the grille, module front-left with its
antenna on the +y edge, two 6 x 6 tacts (SW3 front, SW1 back) under the Rev B snooze bar with its RGB LED
(LED2) between them, power parts, USB-C and the power slide switch at the back. Bottom face: 0603 passives only (<= 1.0 mm: the 103450 cell is
1.0 mm below the board). The board hangs from two upper-shell posts (Ø4 kept clear round H1, H2).
Module pads (ESP32-C6-MINI-1 at (-13.45, 0.6)): left column x -19.35: 3V3 (pad 3) y 3.0, IO2 MIC_SD
1.4, IO3 LED 0.6, EN -1.0, IO4 MIC_SCK -1.8, IO5 MIC_WS -2.6; bottom row y -4.3: IO0 x -18.25,
IO7 BTN -15.05, IO12 -14.25, IO13 -13.45, IO8 -10.25; right column x -7.55: IO21 CHG_STAT y -1.8.
"""
import pcbnew

from fitlib import load_fit
from pcbkit import add_text, circle_rect, rect_pts  # noqa: F401

FIT = load_fit(__file__)                         # ../../../fit.json, board "sensor"
BOARD = FIT.board_tuple()                        # 52 x 24 R3
HOLES = [tuple(h) for h in FIT.holes]            # H1, H2: upper-shell posts (Ø3.6) with heat-stake pins
HOLE_KEEPOUT = 2.2                               # Ø4 clear round each post, plus a little
HOLE_CLEARANCE = 0.18      # GCT USB4105's stock footprint has its GND pads 0.19 mm from the locating pegs (NPTH)

MIC = FIT.feature("mic")
LED = FIT.feature("status_led")
BUTTON = FIT.feature("button")
BUTTON_2 = FIT.feature("button_2")
BAR_LED = FIT.feature("bar_led")
USB = FIT.feature("usb")
SWITCH = FIT.feature("power_switch")
MODULE = FIT.feature("module")
ANTENNA = FIT.keepout("antenna")

NO_PARTS = [ANTENNA]
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA))]
TRIM_COURTYARD = ["U3"]
HIDE_TEXT = {("SW1", "REF**"), ("SW3", "REF**")}   # the 1TS009 footprint carries a second reference text

FIXED = {
    "U3": (MODULE[0], MODULE[1], 0),
    "U4": (MIC[0], MIC[1] + 0.71, 0),     # footprint origin sits 0.71 mm above its port hole
    "LED1": (LED[0], LED[1], 0),
    "SW1": (BUTTON[0], BUTTON[1], 0),     # snooze bar, back switch (pad 1 BTN at -x)
    "SW3": (BUTTON_2[0], BUTTON_2[1], 0), # snooze bar, front switch
    "LED2": (BAR_LED[0], BAR_LED[1], 0),  # under the bar's light leg
    "J1": (USB[0], USB[1], 90),           # mouth (footprint +y) toward +x
    "SW2": (SWITCH[0], SWITCH[1], 90),    # lever (footprint +y) toward +x
}
ROWS = {
    "J2": (3.4, -9.6, (1, 0)),            # LiPo + / -, below the button
}
ROW_LABELS = {
    "J2": ("BAT", ["+", "-"], "above"),
}
BOTTOM = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R9",
          "C1", "C2", "C5", "C7", "C8", "C9", "C10"]
PREFER = [
    # charger, power path and LDO in the back half, between the button and the USB-C / switch
    ("U1", 15.4, -5.6, 0), ("D1", 16.3, -1.6, 0), ("Q1", 16.2, 2.6, 0),   # Rev B: D1, Q1 back ~1.5 mm for SW1; U1 landscape between SW1, J1 and H2's keep-out
    ("U2", 15.0, 7.5, 0), ("C3", 15.0, 10.3, 0), ("C4", 11.5, 7.5, 90),
    # module bulk cap at the front, between the mic and H1; small decoupling under pad 3
    ("C6", -23.8, -1.5, 90), ("C7", -17.8, 3.0, 0), ("R7", -17.8, -1.0, 0), ("C8", -17.8, -2.8, 0),
    ("R8", -10.25, -6.6, 0),                                # IO8 strap, top, straight below its pad
    ("TP1", -3.0, -7.0, 0),                                 # Rev B: out from under SW3
    # Rev B bar light: data resistor, decoupling, diode and bulk cap all between the tacts round LED2
    ("R10", 4.0, -2.4, 0), ("C11", 4.0, 2.4, 0), ("D2", 4.0, 5.2, 0), ("C10", 4.0, 5.2, 0),   # D2 top, C10 under it (bottom): out of the crowded power corner
    # bottom: USB CC, PROG, charger caps, gate pull-down, battery sense
    ("R1", 18.0, -3.0, 90), ("R2", 18.0, -8.0, 90), ("C1", 13.0, -4.0, 90), ("R3", 10.0, -6.5, 90),   # Rev B: R3 out of H2's new keep-out
    ("C2", 11.0, -4.0, 90), ("R4", 12.5, 2.6, 90),
    ("R5", -2.0, -8.0, 90), ("R6", -0.5, -8.0, 90), ("C5", -2.0, -10.6, 0),
    ("C9", -23.5, 1.0, 0),                                  # mic decoupling, under it
    ("R9", -21.0, 8.6, 90),                                 # status LED resistor
]

MODEL_SUBST = {
    "U3": "${KIPRJMOD}/../../../../../tools/kicad/models/ESP32-C6-MINI-1.step",   # rev-b sits one level deeper than an episode
    # no WS2812B-2020 model ships with KiCad: the kit's 2.0 x 2.0 x 0.84 stand-in (the Wuerth PLCC4 used before is
    # 2.05 tall and ran into the snooze bar's light leg in the fit check)
    "LED2": "${KIPRJMOD}/../../../../../tools/kicad/models/WS2812B-2020.step",
}
POWER_NETS = ("/VBUS", "/VSYS", "/VBAT")
GND_VIA_PADS = ["U3"]
# BTN runs from the module's bottom-left pin (IO7, an LP GPIO so it can wake the C6) to the button,
# half the board's length; Freerouting kept leaving it open, so lay it by hand: a via just below the
# pad, along the bottom just under the module's pin row (the top-side escapes cross over it), then
# up beside the button.
# Rev B: two tacts in parallel under the snooze bar. Module -> SW3 along the bottom at y -5.3, then SW3 -> SW1
# along the bottom at y -3.6, so the top under the bar stays clear for LED2 and its parts.
PREROUTE = [
    ("U3.16", (-15.05, -5.3), "via", (-5.0, -5.3), "via", "SW3.1"),
    ("SW1.1", (7.0, -3.6), "via", (-3.7, -3.6), "via", (-5.0, -1.0), "SW3.1"),
    # Rev B: status LED anode, R9 (bottom) to LED1 (top): a via right beside both pads. Every Rev B routing try left it open.
    ("R9.2", (-22.0, 7.775), "via", "LED1.2"),
    # mic SD: up and round its own VDD pad, then down to IO2 (Freerouting left it open once)
    ("U4.6", (-23.5, 6.5), (-21.0, 6.5), (-21.0, 1.4), "U3.5"),
]


def silk(board, placed):
    add_text(board, "BABY MONITOR MONITOR", -13.0, 9.6, pcbnew.B_SilkS, 0.8, bold=True)   # under the antenna: no parts there
    add_text(board, "SENSOR  PS 003  rev B", -13.0, 8.2, pcbnew.B_SilkS, 0.8)
