"""__TITLE__ (episode __EP__): the parts and nets for tools/kicad.

List every part with part(), cap() or res(). Every pin needs a net (None = no-connect), and the
netlist is exactly what's written here, so this file is the schematic review. Lay the sheet out
in blocks (power top-left, MCU bottom-left, sensors top-right, outputs bottom-right) using at()
in 2.54 mm grid units; if two different nets' labels land on one point the build stops: move a part.

Start by copying proven blocks from tools/kicad/example/design.py (2 x AAA boost, ESP32-C3
module with straps and USB pads, I2S amp, PIR, button, test pads, holes, fiducials) and
symbols from tools/kicad/parts.py. Stock KiCad symbols and footprints everywhere else.
"""
from schkit import *  # noqa: F401,F403

setup("__PROJECT__", lib="__LIB__", title="__TITLE__", company="Product Speedrun __EP__",
      comments=["__SUMMARY__"])

# --- Power (top-left)

# --- MCU (bottom-left)

# --- Inputs / sensors (top-right)

# --- Outputs (bottom-right)

# --- Mechanical: M2 holes on the enclosure posts (H1.. match layout.HOLES), fiducials
for i in range(4):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(90 + 4 * i, 104), {}, "Fiducial")

# --- Power flags for nets fed only by connectors or passive pins (ERC wants a driver), e.g.
# part("#FLG01", "power:PWR_FLAG", "PWR_FLAG", "", "", "", at(4, 31), {"1": "GND"}, power=True)

NOTES += [
    # (at(4, 3), "POWER: ..."),
]
OFF_BOARD += [
    # ("BT1", "LiPo 500mAh", "Battery, wire leads to J1", "off-board", "generic 503035"),
]
