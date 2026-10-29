"""Proven block: Raspberry Pi HAT (65 x 56.5 mm, 40-pin socket, ID EEPROM).

Build it with `tools/kicad/selftest.sh all blocks/pi-hat`. Copy the parts you need into an
episode's design.py. The Pi powers the HAT: 5 V (pins 2 / 4) and 3V3 (pins 1 / 17, budget ~50 mA
for HAT parts) come in through the 2 x 20 socket, which sits on the HAT's underside. The ID EEPROM on
ID_SD / ID_SC (pins 27 / 28) at address 0x50 is what makes it a HAT: the Pi reads it at boot to
load the overlay. Flash it from the Pi with the raspberrypi/utils eepromutils, after bridging TP1
(WP) to GND. Check it against the current HAT+ specification before ordering.
"""
from schkit import *  # noqa: F401,F403

setup("pi-hat-block", lib="pihat", title="Pi HAT block", company="Product Speedrun kit",
      date="2026-10-29", comments=["Raspberry Pi HAT outline + 40-pin socket + ID EEPROM + LED"],
      ns="7d0f3b52-1c4e-4a8a-9e57-31b0c0de0a03")

# --- 40-pin socket (left). GPIO17 (pin 11) drives the LED.
gpio = {str(n): None for n in range(1, 41)}
gpio.update({str(n): "GND" for n in (6, 9, 14, 20, 25, 30, 34, 39)})
gpio.update({"1": "3V3", "17": "3V3", "2": "5V", "4": "5V", "27": "ID_SD", "28": "ID_SC", "11": "LED_IO"})
part("J1", "Connector:Raspberry_Pi_2_3", "GPIO", "Connector_PinSocket_2.54mm:PinSocket_2x20_P2.54mm_Vertical",
     "", "2x20 female header 2.54 mm, 8.5 mm body", at(26, 50), gpio,
     "2 x 20 socket on the underside, onto the Pi's GPIO header (stacking header for a pass-through HAT)")
cap("C1", "10uF", at(8, 20), "5V", "GND")
cap("C2", "10uF", at(14, 20), "3V3", "GND")

# --- ID EEPROM (top-right): A0-A2 low = 0x50, WP high = write-protected until TP1 is bridged to GND
part("U1", "Memory_EEPROM:24LC32", "CAT24C32", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "", "CAT24C32WI-GT3",
     at(84, 24), {"1": "GND", "2": "GND", "3": "GND", "4": "GND", "5": "ID_SD", "6": "ID_SC", "7": "WP", "8": "3V3"},
     "32 kbit I2C EEPROM, SOIC-8: HAT ID")
cap("C3", "100nF", at(96, 16), "3V3", "GND")
res("R1", "3.9k", at(72, 14), "3V3", "ID_SD")
res("R2", "3.9k", at(76, 14), "3V3", "ID_SC")
res("R3", "10k", at(100, 26), "3V3", "WP")
part("TP1", "Connector:TestPoint", "WP", "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(104, 32), {"1": "WP"},
     "Test pad: bridge to GND to write the EEPROM", dnp=True)
part("TP2", "Connector:TestPoint", "GND", "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(108, 32), {"1": "GND"},
     "Test pad", dnp=True)

# --- LED (bottom-right)
res("R4", "1k", at(80, 66), "LED_IO", "LED_A")
part("D1", "Device:LED", "Green", "LED_SMD:LED_0603_1608Metric", "C72043", "KT-0603G", at(90, 66),
     {"1": "GND", "2": "LED_A"}, "LED green 0603")

# --- mechanical: M2.5 holes on the Pi's standoff pattern (58 x 49 mm)
for i in range(4):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2.5", "MountingHole:MountingHole_2.7mm_M2.5", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2.5")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(90 + 4 * i, 104), {}, "Fiducial")

for i, (net, xy) in enumerate((("5V", at(4, 31)), ("3V3", at(8, 31)), ("GND", at(12, 31))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)

NOTES += [
    (at(4, 3), "POWER: from the Pi through J1: 5V (pins 2/4) and 3V3 (pins 1/17). No back-powering: a HAT that\n"
               "feeds 5 V into the Pi needs an ideal-diode / fuse per the HAT+ spec."),
    (at(60, 3), "ID EEPROM: CAT24C32 / 24LC32 at 0x50 on ID_SD / ID_SC with 3.9k pull-ups. WP pulled high (R3):\n"
                "bridge TP1 to GND while writing it from the Pi (eepromutils), then leave it open."),
    (at(60, 52), "LED on GPIO17 (pin 11)."),
]
