"""Pico carrier block: outline and placement. A 46 x 60 mm board with the Pico flat along its left
side, the Pico's micro-USB flush with the top edge, and the carrier parts in the right-hand strip.

Pico pin positions on this board (module origin at PICO): left column x = PICO.x - 8.89, right
column x = PICO.x + 8.89; pin n of 21..40 at y = PICO.y + 24.13 - (40 - n) * 2.54 (pin 40 VBUS at
the USB end); the SWD pads D1..D3 sit at y = PICO.y - 23.9, x = PICO.x - 2.54 / 0 / + 2.54.
"""
import pcbnew

from pcbkit import add_text, silk_rect

BOARD = (46.0, 60.0, 3.0)
HOLES = [(19.0, 26.0), (19.0, -26.0), (-19.5, -26.5)]
HOLE_KEEPOUT = 3.0

PICO = (-10.0, 3.0)               # module origin = its centre; the USB end is at +y
NO_PARTS = []
NO_COPPER = []

FIXED = {
    "U1": (PICO[0], PICO[1], 0),
    "FID1": (21.0, 10.0, 0),
    "FID2": (12.0, -27.0, 0),
    "FID3": (-2.0, -27.0, 0),
}
ROWS = {
    "J1": (13.5, 19.0, (0, 1)),                      # 5 V in, opening to the right edge: + at the bottom
    "J2": (PICO[0] - 2.5, -26.5, (1, 0)),            # SWD pads straight below the Pico's D1..D3
}
ROW_LABELS = {
    "J1": ("5V", ["+", "-"], "left", (13.5, 24.4)),
    "J2": ("SWD", ["C", "G", "D"], "above", (PICO[0] - 6.0, -26.5)),
}
PREFER = [
    # 5 V in -> Schottky -> VSYS (pin 39), its bulk cap; 3V3 (pin 36) decoupling; AGND (pin 33) link
    ("D1", 6.0, 24.6, 0), ("C1", 4.0, 21.5, 0), ("C2", 4.5, 17.5, 0), ("C3", 4.5, 15.5, 0),
    ("R2", 3.5, 9.4, 0),
    # RUN (pin 30) button and the LED on GP22 (pin 29)
    ("SW1", 12.0, 2.0, 0), ("R1", 4.0, -1.0, 0), ("D2", 4.0, -4.0, 0),
    ("TP1", 4.0, 27.0, 0), ("TP2", 10.0, 14.0, 0), ("TP3", 14.0, 14.0, 0),
]

MODEL_SUBST = {}
POWER_NETS = ("/5V_IN", "/VSYS")    # Pico pads are 2.54 mm apart: 0.5 mm tracks still pass between them
GND_VIA_PADS = []
PREROUTE = []


def silk(board, placed):
    add_text(board, "PICO CARRIER", 10.0, -12.0, pcbnew.B_SilkS, 1.6, bold=True)
    add_text(board, "Product Speedrun kit  rev A", 10.0, -15.0, pcbnew.B_SilkS, 1.0)
    add_text(board, "BOOTSEL on the Pico", PICO[0], -16.0, pcbnew.F_Fab, 1.0)
    silk_rect(board, (PICO[0] - 10.5, PICO[1] - 25.5), (PICO[0] + 10.5, PICO[1] + 25.5), pcbnew.F_Fab)
