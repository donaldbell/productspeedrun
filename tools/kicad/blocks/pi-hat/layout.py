"""Pi HAT block: the HAT outline (65 x 56.5 mm, R3, M2.5 holes on a 58 x 49 mm pattern) with the
40-pin socket along the top edge, on the underside, in the place the Pi's GPIO header expects.

Origin at the board centre, +y toward the GPIO edge. Socket pins: odd pins on the inner row at
y = 22.98, even pins on the outer row at y = 25.52; pin n at x = -24.13 + ((n - 1) // 2) * 2.54.
That puts the header centred on the top holes' line, 29 mm from the left-hand holes, as on the Pi.
"""
import pcbnew

from pcbkit import add_text

BOARD = (65.0, 56.5, 3.0)
HOLES = [(sx * 29.0, sy * 24.5) for sx in (-1, 1) for sy in (1, -1)]
HOLE_KEEPOUT = 3.1                 # 6.2 mm keep-out round each M2.5 standoff (HAT spec)

NO_PARTS = []
NO_COPPER = []

FIXED = {
    "FID1": (28.0, 0.0, 0),
    "FID2": (-28.0, -14.0, 0),
    "FID3": (0.0, -24.0, 0),
}
ROWS = {
    "J1": (-24.13, 22.98, (0, 1)),          # pin 1 (3V3) inner row, pin 2 (5V) beside it on the edge row
}
ROW_LABELS = {}
BOTTOM = ["J1"]                             # the socket's body is under the HAT, onto the Pi
PREFER = [
    # supply decoupling at the 5V (2 / 4) and 3V3 (1) pins
    ("C1", -21.0, 18.5, 0), ("C2", -26.0, 18.0, 90),
    # ID EEPROM beside ID_SD / ID_SC (27 / 28), its pull-ups between it and the socket
    ("U1", 9.0, 13.5, 0), ("C3", 15.0, 13.5, 90), ("R1", 6.5, 19.0, 0), ("R2", 11.5, 19.0, 0),
    ("R3", 14.5, 10.0, 0), ("TP1", 18.5, 10.0, 0), ("TP2", 22.0, 10.0, 0),
    # LED on GPIO17 (pin 11)
    ("R4", -11.4, 19.0, 0), ("D1", -11.4, 16.5, 0),
]

MODEL_SUBST = {}
POWER_NETS = ("/5V",)
GND_VIA_PADS = []
PREROUTE = []


def silk(board, placed):
    add_text(board, "PI HAT BLOCK", 0.0, -5.0, pcbnew.F_SilkS, 1.6, bold=True)
    add_text(board, "Product Speedrun kit  rev A", 0.0, -8.0, pcbnew.F_SilkS, 1.0)
