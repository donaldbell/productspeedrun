"""Gamer Companion (episode 002): board outline and placement for tools/kicad.

The board stands upright behind the robot's face (enclosure XZ plane, front face at y = -15).
Board coordinates, as seen from the face (KiCad top = the side facing the visor):
    board x = enclosure x,   board y = enclosure z - 6   (board centre at enclosure z = +6).
Top (front): PIR, eye LEDs and their caps. Bottom (back, see BOTTOM): module and everything else.
Every part in design.py must appear in exactly one of HOLES, FIXED, ROWS or PREFER.
"""
import pcbnew

from pcbkit import add_text, circle_rect, rect_pts, silk_circle

BOARD = (54.0, 31.0, 5.0)                       # enclosure x -27..27, z -9.5..21.5
HOLES = [(-21.0, -13.25), (21.0, -13.25), (21.0, 12.5)]   # H1..H3: M2 into the face-cap posts
HOLE_KEEPOUT = 1.95                             # M2 pan head (Ø3.8) on the back

PIR_AT = (0.0, -2.0)                            # AM312 dome centre (enclosure z 4)
EYES = [(-11.0, 3.2), (11.0, 3.2)]              # under the visor's eye arcs (enclosure z 9.2), clear of U2's vias
MIC_PORT = (0.0, -12.0)                         # face mic port (enclosure z -6)
MODULE_AT = (-13.0, 1.9)                        # WROOM-1 body centre; antenna at the top edge
ANTENNA_KEEPOUT = (-22.6, 8.2, -3.4, 15.5)      # top 6.5 mm of the module: copper-free on both layers

NO_PARTS = [circle_rect(PIR_AT, 1.0), ANTENNA_KEEPOUT,
            (circle_rect(PIR_AT, 5.4), "F")]                     # the AM312 body stands on the front face
NO_PARTS += [(circle_rect(h, 3.0), "F") for h in HOLES]        # face-cap posts (Ø5.2) land on the front
NO_COPPER = [("Antenna keep-out", rect_pts(ANTENNA_KEEPOUT))]

BOTTOM = ["U1", "U2", "U3", "U4", "J1", "J2", "J3", "Q1", "D1",
          "C1", "C3", "C4", "C5", "C6", "C7", "C9", "C13", "C14",
          "R4", "R6", "R7", "R8"]
# On the front with the LEDs: the LED feed (D2, C10, R5), the PIR filter (R3, C8), the EN RC (R1, C7)
# and the test pads (probe them with the face cap off). They sit
# behind the smoked visor, which frees the back where the module's I2S lines cross to the amp.
TRIM_COURTYARD = ["U2"]     # the stock courtyard includes a 48 mm antenna clearance zone

FIXED = {
    "U2": (MODULE_AT[0], MODULE_AT[1], 0),
    "U4": (MIC_PORT[0], MIC_PORT[1] + 0.71, 0),          # footprint origin sits 0.71 mm above its port hole
    "LED1": (EYES[0][0], EYES[0][1], 0),
    "LED2": (EYES[1][0], EYES[1][1], 0),
    "FID1": (-19.0, -9.0, 0),
    "FID2": (19.0, 8.0, 0),
    "FID3": (8.0, -13.5, 0),
}
ROWS = {
    "U5": (PIR_AT[0], PIR_AT[1] + 2.54, (0, -1)),        # AM312 legs VCC / OUT / GND, top to bottom
}
ROW_LABELS = {
    "U5": ("PIR", ["V", "O", "G"], "right", (3.6, 2.6)),
}
# Bottom parts are given as seen from the top (through the board). The module's pin row 1-14
# faces the board centre (x = -4.25, pin n at y = 7.16 - 1.27 (n - 1)): 3V3 (pin 2) at 5.9, EN 4.6,
# PIR_OUT (pin 8) at -1.7 beside the PIR's OUT leg. Pins 6, 7, 10 face the PIR legs and stay unused.
PREFER = [
    # connectors first: they need the most room (bottom edge, right edge)
    ("J1", 15.0, -11.6, 0), ("J2", 6.2, -11.6, 0), ("J3", 23.0, 0.0, 90),
    # module decoupling at 3V3, EN RC, IO0 pull-up under the module's bottom-left
    ("C6", -1.95, 5.89, 180), ("C5", -2.3, 9.2, 90),     # C6 in line with 3V3 pin 2 (pad 1 nearest it)
    ("R1", -3.0, 11.2, 0), ("C7", -3.0, 13.2, 0),          # front, above the PIR: keeps the I2S exits clear
    ("TP4", -8.0, -12.6, 0), ("TP5", -12.0, -12.6, 0),                   # front, bottom edge
    # LDO and bulk caps top-middle (back), right of the antenna keep-out
    ("U1", 8.0, 11.0, 0), ("C3", 11.5, 12.6, 90), ("C4", 11.5, 9.4, 90), ("C1", 4.5, 11.0, 90),
    # front: LED feed above the PIR between the eyes, PIR filter to its upper right
    ("D2", 5.6, 9.6, 0), ("C10", 2.4, 7.4, 90), ("R5", -7.0, 6.2, 90),
    ("R3", 5.6, 4.0, 90), ("C8", 7.4, 4.0, 90),
    # back: mic decoupling and SD pull-down beside the mic
    ("C9", -3.0, -10.4, 90), ("R4", 3.0, -8.4, 90),
    # amp on the right with its 5 V decoupling, speaker connector at the right edge
    ("U3", 16.5, 2.0, 0), ("C14", 16.5, 5.5, 0), ("C13", 20.0, 5.5, 90), ("R6", 12.6, -0.6, 90),
    # blower switch and connectors along the bottom edge
    ("Q1", 14.0, -5.6, 0), ("R7", 10.4, -4.4, 90), ("R8", 10.4, -7.4, 90), ("D1", 18.5, -5.6, 0),
    # front side: LED decoupling right beside each eye
    ("C11", -8.6, 3.2, 90), ("C12", 13.4, 3.2, 90),
]

MODEL_SUBST = {
    "U3": "${KICAD10_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/TQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step",
    # no WS2812B-2020 model ships with KiCad: a slightly larger PLCC4 RGB stands in (renders only)
    "LED1": "${KICAD10_3DMODEL_DIR}/LED_SMD.3dshapes/LED_RGB_Wuerth-PLCC4_3.2x2.8mm_150141M173100.step",
    "LED2": "${KICAD10_3DMODEL_DIR}/LED_SMD.3dshapes/LED_RGB_Wuerth-PLCC4_3.2x2.8mm_150141M173100.step",
}
POWER_NETS = ("/VBUS",)       # 3V3 peaks ~0.5 A and must leave a 1.27 mm-pitch pin row: default 0.25 mm
GND_VIA_PADS = ["U2", "U3"]
# Two short links Freerouting kept leaving open (board mm, as seen from the front):
#   3V3: module pin 2 straight into C6.
#   PIR_OUT: module pin 8 (IO15) straight across to the PIR's middle leg, on the back.
#   3V3 to the mic: up the near-empty front from beside C9, back down just below C6.
#   3V3 to the front-side R1 (EN pull-up) and R3 (PIR filter), from C5 and from the LDO's C4.
PREROUTE = [
    ("U2.2", "C6.1"),                                    # module 3V3 straight into its decoupling
    ("U2.8", (-1.4, -2.0), "U5.2"),
    ("C9.1", 0.3, (-1.8, -8.9), "via", (-2.0, 4.6), "via", "C6.1"),
    ("C5.1", (-1.1, 10.15), "via", (-2.42, 10.15), "R1.1"),                     # 3V3 up to the EN pull-up (front)
    ("C5.1", (-3.2, 10.15), (-3.2, 6.6), "C6.1"),       # C5 to C6, between the module's pins and C5's GND pad
    ("C4.1", (13.0, 10.03), "via", (9.3, 6.6), (7.3, 6.6), (7.3, 2.2), (6.4, 2.2), "R3.1"),  # LDO out to the PIR filter (front), between R3 and C8
]


def silk(board, placed):
    """Antenna note on the fab layer and the PIR outline on the front (the back is full)."""
    silk_circle(board, PIR_AT, 4.9)
    add_text(board, "ANTENNA (BACK)", MODULE_AT[0], 12.0, pcbnew.F_Fab, 1.0)
