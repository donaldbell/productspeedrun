"""Backpack Defender Rev B: board outline and placement for tools/kicad.

Coordinates: board mm (origin at the board's centre, +x right toward the button end, +y up toward
the back; the face's front is -y). The outline, holes and everything that lines up with the
enclosure come from ../../fit.json, which the Stage 4 model reads too: change them there.
Ported from Rev A (tools/kicad/example/layout.py). Rev B: speaker circle on top, eye LEDs over the
old module spot, module and power switch on the bottom face, cells under the front half of the
bottom face, PIR cutout. Every part in design.py goes in exactly one of HOLES, FIXED, ROWS or PREFER.
"""
import pcbnew

from fitlib import load_fit
from pcbkit import add_text, circle_rect, rect_pts, silk_circle, silk_rect  # noqa: F401

FIT = load_fit(__file__)
BOARD = FIT.board_tuple()                        # 70 x 45, R9
HOLES = [tuple(h) for h in FIT.holes]            # H1..H4 on the enclosure posts (H3 moved for the PIR)
HOLE_KEEPOUT = 3.0

f = FIT.feature
PIR_AT, PIR_CUT_R = f("pir"), FIT.features["pir"]["size"][0] / 2
SPK_AT, SPK_R = f("speaker"), FIT.features["speaker"]["size"][0] / 2
LED_L, LED_R = f("eye_led_l"), f("eye_led_r")
BTN_AT = f("button")
PSW_AT = f("power_switch")                       # body centre (bottom face)
MOD_AT = f("module")                             # body centre (bottom face); the pad field sits 3.1 mm toward -y
AMP_AT = f("amp")
BTN_LED = f("button_led")
cx, cy = f("cells")
cw, ch = FIT.features["cells"]["size"]
CELLS = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
ANTENNA_KEEPOUT = FIT.keepout("antenna")

CUTOUTS = [(PIR_AT[0], PIR_AT[1], PIR_CUT_R)]   # the AM312 drops through the board here
PIPE_BOSS = 2.6                                  # lid's light-pipe boss (r 2.2) comes down to 1.4 above the board

NO_PARTS = [
    circle_rect(PIR_AT, PIR_CUT_R + 0.8),
    ANTENNA_KEEPOUT,
    (circle_rect(SPK_AT, SPK_R), "F"),           # the speaker sits on the top face on a foam pad
    (CELLS, "B"),                                # the AAA cells are 0.9 mm under the bottom face
    (circle_rect(LED_L, PIPE_BOSS), "F"), (circle_rect(LED_R, PIPE_BOSS), "F"),
]
NO_COPPER = [
    ("Antenna keep-out", rect_pts(ANTENNA_KEEPOUT)),
    ("PIR cutout keep-out", rect_pts(circle_rect(PIR_AT, PIR_CUT_R + 0.6))),
]

BOTTOM = ["U2", "C5", "C6", "R5", "C7", "R6", "R7", "R8", "SW2"]

# Parts that must sit exactly where the enclosure needs them: ref -> (x, y, orientation).
# Footprint origins: SW_PUSH-12mm at pad 1 (body centre +6.25, -2.5); OS102011MA1Q at pad 1, pads
# along -y and the lever toward +x at 90 deg on the bottom face (the flip mirrors the pad row); LEDs at their centre.
FIXED = {
    "U2": (MOD_AT[0], MOD_AT[1] - 3.1, 0),
    "SW1": (BTN_AT[0] - 6.25, BTN_AT[1] + 2.5, 0),
    "SW2": (PSW_AT[0], PSW_AT[1] + 2.0, 90),
    "D1": (LED_L[0], LED_L[1], 0),
    "D2": (LED_R[0], LED_R[1], 0),
    "LED1": (BTN_LED[0], BTN_LED[1], 0),
    "FID1": (-24.0, -20.5, 0),
    "FID2": (27.0, 18.5, 0),
    "FID3": (24.0, -20.0, 0),
}
# Rows of through-hole pads: ref -> (pin-1 x, y, direction of pin 2 from pin 1).
ROWS = {
    "J4": (-31.0, -1.0, (0, -1)),                # PIR leads, VCC / OUT / GND, left end (outside the cells)
    "J1": (26.8, -19.0, (0, 1)),                 # battery contact wires: + at the front, beside the cells' + end
    "J3": (13.5, -18.5, (1, 0)),                 # speaker leads, beside the speaker circle
}
ROW_LABELS = {
    "J4": ("PIR", ["V", "O", "G"], "right"),
    "J1": ("AAA", ["+", "-"], "left"),
    "J3": ("SPK", ["+", "-"], "above"),
}
# Everything else: (ref, x, y, orientation). Earlier parts get first pick.
PREFER = [
    # power path: reverse-battery FET and the boost, front-left, over the cells (top face)
    ("Q1", -26.0, -9.0, 90), ("C1", -23.0, -10.0, 90), ("L1", -20.5, -15.5, 0), ("U1", -15.0, -14.0, 0),
    ("C2", -12.6, -17.0, 90), ("C3", -15.0, -19.5, 0), ("R1", -15.0, -10.8, 0), ("R2", -15.0, -12.4, 0),
    ("R3", -22.0, -4.0, 0), ("R4", -22.0, -5.8, 0), ("C4", -18.5, -4.9, 90),
    # module decoupling at pin 1 and EN RC / straps, bottom face: mirrored there, so pin 1 is on the module's +x side
    ("C6", 4.0, 20.0, 0), ("C5", 4.0, 17.8, 0), ("R5", 6.6, 15.0, 90), ("C7", 8.4, 15.0, 90),
    ("R6", 5.0, 9.0, 90), ("R7", 6.8, 9.0, 90), ("R8", 8.6, 9.0, 90),
    # button pull-up, programming pads (top face, back right)
    ("R9", 10.0, 6.0, 90), ("J2", 18.0, 15.0, 0),
    # eye LED driver between the eyes
    ("Q2", -9.6, 3.6, 0), ("R14", -14.2, 6.4, 90), ("R15", -5.0, 6.4, 90), ("R16", -9.6, 0.8, 0),
    # button glow: LED1's supply switch, gate pull-up, data resistor and decoupling, beside it
    ("C11", 21.0, 9.2, 90), ("Q3", 13.5, 10.5, 0), ("R17", 13.5, 13.4, 0), ("R18", 15.0, 8.4, 90),
    # PIR supply filter beside J4
    ("R10", -27.5, -3.0, 90), ("C8", -27.5, 1.0, 90),
    # amp beside the speaker, its decoupling on the VDD side
    ("U3", AMP_AT[0], AMP_AT[1], 0), ("C10", 15.8, -10.0, 90), ("C9", 17.8, -10.0, 90), ("R11", 11.8, -8.5, 0),
    ("TP1", 23.5, 10.0, 0), ("TP2", 26.5, 10.0, 0), ("TP3", 29.5, 10.0, 0),
]

# Stock footprints whose own 3D model isn't shipped or is the wrong height: same-geometry stand-ins.
MODEL_SUBST = {
    "SW1": "${KIPRJMOD}/lib/3d/SW_PUSH-12mm_H4.3.step",      # 12 x 12 x 4.3 (KiCad ships only an 8.5 mm one)
    "U3": "${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step",
    # no WS2812B-2020 model ships with KiCad: a slightly larger PLCC4 RGB stands in (as in episode 002)
    "LED1": "${KICAD10_3DMODEL_DIR}/LED_SMD.3dshapes/LED_RGB_Wuerth-PLCC4_3.2x2.8mm_150141M173100.step",
}
POWER_NETS = ("/BAT_RAW", "/BAT_IN", "/VBAT", "/BOOST_SW", "/3V3")   # wider tracks (0.5 mm)
# The boost's switch pin (U1.5) faces away from L1 and Freerouting keeps missing it (Rev A had the same
# problem): leave east, drop to the bottom (only the GND pour there, over the cells), run west under U1 and
# come up through a via inside L1's big pad 2. Absolute points: re-check if U1 or L1 move.
PREROUTE = [
    ("U1.5", 0.3, (-12.9, -14.0), "via", 0.5, (-17.47, -14.0), (-17.47, -14.6), "via", "L1.2"),
]
GND_VIA_PADS = ["U2"]


def silk(board, placed):
    """Extra silkscreen: outlines of what sits above / below, the name on the back."""
    silk_circle(board, SPK_AT, SPK_R - 0.3)
    add_text(board, "SPEAKER", SPK_AT[0], SPK_AT[1], pcbnew.F_Fab, 1.0)
    add_text(board, "BACKPACK DEFENDER", 2.0, -6.0, pcbnew.B_SilkS, 1.6, bold=True)
    add_text(board, "^_^  rev B  2026", 2.0, -9.0, pcbnew.B_SilkS, 1.2)
    silk_rect(board, (-22.25, -20.5), (22.25, 1.0), pcbnew.B_SilkS)     # the cells themselves (2 x AAA, 44.5 long), clear of SW1 pads
    add_text(board, "2 x AAA cradle", 2.0, -19.0, pcbnew.B_SilkS, 1.0)
