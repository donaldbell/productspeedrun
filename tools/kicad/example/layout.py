"""Backpack Defender (episode 001): board outline and placement. Example for tools/kicad.

Coordinates: the enclosure's own XY from Stage 4 (origin at the centre, mm, +x to the button end,
+y to the back; the front grille is at -y). Every part in design.py must appear in exactly one of
HOLES (mounting holes H1..), FIXED, ROWS or PREFER, or gen_pcb.py stops and names it.
"""
import pcbnew

from pcbkit import add_text, circle_rect, rect_pts, silk_circle, silk_rect

BOARD = (70.0, 45.0, 9.0)                        # width, height, corner radius (Stage 4: 70 x 45, R9)
HOLES = [(sx * 31.0, sy * 17.0) for sx in (-1, 1) for sy in (-1, 1)]   # H1..H4 on the enclosure posts
HOLE_KEEPOUT = 3.0                               # M2 pan head / post top: no parts, no copper

PIR_AT, PIR_R = (-26.0, 13.0), 5.5               # AM312 body (D10) above the board: no parts under it
MODULE_AT = (-8.5, 9.0)                          # WROOM-02 pad-field centre; antenna end on the back edge
ANTENNA_KEEPOUT = (-19.5, 15.6, 2.5, 22.6)       # copper-free on both layers
BTN_AT = (18.0, 0.0)                             # big silence button centre (Stage 4 BTN_XY)
PIEZO_AT = (0.0, -14.5)                          # behind the front grille

NO_PARTS = [circle_rect(PIR_AT, PIR_R), ANTENNA_KEEPOUT]          # areas the auto-fitter avoids
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA_KEEPOUT))]     # (name, points[, layers]): both layers by default

# Parts that must sit exactly where the enclosure needs them: ref -> (x, y, orientation).
# The footprint's origin goes here, which for THT parts is often pin 1, not the body centre.
FIXED = {
    "U2": (MODULE_AT[0], MODULE_AT[1], 0),
    "SW1": (BTN_AT[0] - 6.25, BTN_AT[1] + 2.5, 0),       # SW_PUSH-12mm: origin at pad 1, body centre at (6.25, 2.5)
    "BZ1": (PIEZO_AT[0] - 2.5, PIEZO_AT[1], 0),          # PS1240: origin at pad 1, body centre at (2.5, 0)
    "FID1": (-32.0, -10.5, 0),
    "FID2": (27.0, 18.5, 0),
    "FID3": (25.0, -19.5, 0),
}
# Rows of through-hole pads: ref -> (pin-1 x, y, direction of pin 2 from pin 1).
ROWS = {
    "U4": (PIR_AT[0], PIR_AT[1] + 2.54, (0, -1)),        # AM312 legs, VCC / OUT / GND top to bottom
    "J1": (-31.0, -3.0, (0, -1)),                        # battery leads: + on top
    "J2": (30.0, 5.5, (0, -1)),                          # programming pogo pads down the right end
}
# Silkscreen pin labels for those rows: ref -> (title, labels, "left" | "right" | "below"[, title (x, y)]).
ROW_LABELS = {
    "U4": ("PIR", ["V", "O", "G"], "right", (PIR_AT[0] - 3.4, PIR_AT[1])),
    "J1": ("AAA", ["+", "-"], "left"),
    "J2": ("PROG", ["G", "3V3", "D-", "D+", "EN", "IO9"], "right"),
}
# Everything else: (ref, x, y, orientation). The auto-fitter moves a part to the nearest free spot
# if needed and lists it in output/placement.txt. Earlier parts get first pick, so put each IC's
# decoupling right after it, next to its power pin.
PREFER = [
    # reverse-battery FET and the boost, front-left, over the battery holder's end
    ("Q1", -27.5, -3.4, 90), ("C1", -24.0, -4.5, 90), ("L1", -21.0, -11.5, 0), ("U1", -15.6, -11.0, 0),
    ("C2", -12.6, -9.0, 90), ("C3", -12.6, -13.0, 90), ("R1", -15.6, -14.2, 0), ("R2", -15.6, -16.0, 0),
    # battery sense, between the module and the piezo
    ("R3", -8.5, -3.0, 0), ("R4", -8.5, -4.8, 0), ("C4", -8.5, -6.6, 0),
    # module decoupling at pin 1 (top-left), EN RC and strap pull-ups along the module's left pins
    ("C6", -21.8, 20.0, 0), ("C5", -25.6, 20.0, 0), ("R5", -21.6, 4.0, 90), ("C7", -23.4, 4.0, 90),
    ("R7", -25.2, 4.0, 90), ("R8", -27.0, 4.0, 90), ("R6", 3.0, 12.0, 90), ("R9", 5.0, 5.0, 90),
    # PIR supply filter, left end under the PIR
    ("R10", -32.0, 3.0, 90), ("C8", -29.6, 3.0, 90),
    # amp beside the piezo, its decoupling on the VDD side, series resistors toward the piezo
    ("U3", 12.0, -12.5, 0), ("C10", 15.6, -9.6, 90), ("C9", 17.6, -9.6, 90), ("R11", 9.0, -9.0, 0),
    ("R12", 8.2, -14.2, 90), ("R13", 8.2, -17.4, 90),
    ("TP1", -27.5, -9.5, 0), ("TP3", -27.5, -13.5, 0), ("TP2", 5.0, -4.5, 0),
]

# Stock footprints whose own 3D model isn't shipped: same-geometry stand-ins (renders / GLB only).
MODEL_SUBST = {
    "SW1": "${KICAD10_3DMODEL_DIR}/Button_Switch_THT.3dshapes/SW_PUSH-12mm_Wuerth-430476085716.step",
    "U3": "${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step",
}
POWER_NETS = ("/BAT_IN", "/VBAT", "/BOOST_SW", "/3V3")   # wider tracks (0.5 mm)
# Fixed tracks laid before Freerouting: "REF.PAD", (x, y) points, a width in mm from there on,
# "via" to change layer, then "REF.PAD". The boost's switch pin faces away from L1 and C2/C3
# leave only 0.65 mm beside it, which Freerouting often fails to get through: so neck down to
# 0.3 mm between the caps, drop to the bottom, and come back up beside L1.
PREROUTE = [
    ("U1.5", 0.3, (-11.6, -11.0), "via", 0.5, (-13.6, -13.0), (-16.3, -13.0), "via", "L1.2"),
]
GND_VIA_PADS = ["U2"]       # parts with a big ground pad: route_pcb drops GND vias around their centre


def silk(board, placed):
    """Extra silkscreen: outlines of what sits above / below, the name and face on the back."""
    silk_circle(board, PIR_AT, 5.0)
    add_text(board, "ANTENNA", MODULE_AT[0], 19.2, pcbnew.F_Fab, 1.0)
    add_text(board, "BACKPACK DEFENDER", -4.0, -6.0, pcbnew.B_SilkS, 1.6, bold=True)
    add_text(board, "^_^  rev A  2026", -4.0, -9.0, pcbnew.B_SilkS, 1.2)
    silk_rect(board, (-26.0, 0.0), (26.0, -22.0), pcbnew.B_SilkS)
    add_text(board, "2 x AAA holder (approx.)", -4.0, -19.5, pcbnew.B_SilkS, 1.0)
