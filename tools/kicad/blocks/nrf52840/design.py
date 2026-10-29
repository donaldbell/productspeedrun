"""Proven block: nRF52840 as a Raytac MDBT50Q-1MV2 module, USB-C powered, native USB + SWD.

Build it with `tools/kicad/selftest.sh all blocks/nrf52840`. Copy the parts you need into an
episode's design.py. Power is the nRF52840's "normal voltage" mode: an AP2112K makes 3.3 V from
USB, and VDD and VDDH both take it (DCCH unused). VBUS also goes to the module's USB PHY. A blank
module is flashed first over SWD (Tag-Connect TC2030 footprint, no connector to buy); after a USB
bootloader (Adafruit nRF52 / Zephyr MCUboot) it updates over USB-C.

Only pins on the module's outer pad rows are used, except P0.18 (nRESET), which has no outer
alternative: the 0.8 mm outer-row pitch leaves no room for a track to reach the inner row, so its
track goes inward under the module and drops through a via there.
"""
from schkit import *  # noqa: F401,F403

setup("nrf52840-block", lib="nrf", title="nRF52840 block", company="Product Speedrun kit",
      date="2026-10-29", comments=["MDBT50Q nRF52840 + USB-C + AP2112K + TC2030 SWD + reset + LED"],
      ns="7d0f3b52-1c4e-4a8a-9e57-31b0c0de0a02")

# --- USB-C in, 3.3 V LDO (top-left)
part("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
     "C165948", "TYPE-C-31-M-12", at(10, 30),
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
      "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN",
      "A8": None, "B8": None, "SH": "GND"},
     "USB-C receptacle, USB 2.0, 16-pin SMD + through-hole shell")
res("R1", "5.1k", at(26, 38), "CC1", "GND")             # 5.1k CC pull-downs: a C-to-C cable then gives 5 V
res("R2", "5.1k", at(30, 38), "CC2", "GND")
cap("C1", "10uF", at(36, 25), "VBUS", "GND")
part("U1", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3TRG1", "Package_TO_SOT_SMD:SOT-23-5", "C51118", "AP2112K-3.3TRG1",
     at(46, 22), {"1": "VBUS", "3": "VBUS", "2": "GND", "4": None, "5": "3V3"},
     "LDO 3.3 V 600 mA, SOT-23-5, EN tied to VIN (always on)")
cap("C2", "10uF", at(56, 27), "3V3", "GND")

# --- nRF52840 module (bottom-left). LED on P0.15, both on the right-hand outer row.
nrf = {str(n): None for n in range(1, 62)}
nrf.update({str(n): "GND" for n in (1, 2, 15, 33, 55)})
nrf.update({"28": "3V3", "30": "3V3", "31": None, "32": "VBUS", "34": "USB_DN", "35": "USB_DP",
            "51": "SWDIO", "53": "SWDCLK", "40": "NRST", "39": "LED_IO"})
part("U2", "RF_Module:MDBT50Q-1MV2", "MDBT50Q-1MV2", "RF_Module:Raytac_MDBT50Q", "", "MDBT50Q-1MV2", at(26, 80), nrf,
     "nRF52840 module (BLE 5 / 802.15.4 / USB), 1 MB flash, chip antenna, 10 x 15.5 mm")
cap("C3", "100nF", at(4, 62), "3V3", "GND")              # at VDD / VDDH
cap("C4", "4.7uF", at(8, 62), "VBUS", "GND")             # VBUS pin needs 4.7 uF (nRF52840 PS, USB)
part("J2", "Connector_Generic:Conn_02x03_Odd_Even", "SWD", "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
     "", "TC2030-IDC-NL (cable)", at(52, 64), {"1": "3V3", "2": "SWDIO", "3": "NRST", "4": "SWDCLK", "5": "GND", "6": None},
     "Tag-Connect TC2030 pads: SWD for J-Link / Debug Probe (pin 6 SWO unused)", dnp=True)
part("SW1", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "C318884", "TS-1187A-B-A-B",
     at(52, 82), {"1": "NRST", "2": "GND"}, "Tactile switch 5.1 x 5.1 mm SMD: P0.18 nRESET to GND")

# --- LED (right)
res("R3", "1k", at(80, 66), "LED_IO", "LED_A")
part("D1", "Device:LED", "Green", "LED_SMD:LED_0603_1608Metric", "C72043", "KT-0603G", at(90, 66),
     {"1": "GND", "2": "LED_A"}, "LED green 0603")

# --- mechanical
for i in range(4):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(90 + 4 * i, 104), {}, "Fiducial")

for i, (net, xy) in enumerate((("VBUS", at(4, 46)), ("GND", at(8, 46))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)

NOTES += [
    (at(4, 3), "POWER: USB-C (5.1k CC pull-downs) -> VBUS -> U1 AP2112K-3.3 -> 3V3 on VDD and VDDH (normal voltage\n"
               "mode, DCCH open). VBUS also to the module's USB regulator (C4 4.7 uF). Add ESD (e.g. USBLC6-2) on a product."),
    (at(4, 50), "MCU: MDBT50Q-1MV2 with its antenna on the board's top edge, copper-free around it.\n"
                "SWD on J2 (TC2030 pads) for the first flash; then USB DFU. P0.18 is nRESET once UICR.PSELRESET is\n"
                "set (bootloaders do it): SW1 resets. LED on P0.15. Free outer-row GPIO for the product: P1.10-P1.15,\n"
                "P0.29-P0.31, P0.02-P0.08, P0.13, P0.17, P0.20-P0.24, P1.09."),
]
