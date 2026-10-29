"""Proven block: Raspberry Pi Pico (or Pico 2) soldered down as a castellated module.

Build it with `tools/kicad/selftest.sh all blocks/pico`. Copy the parts you need into an episode's
design.py. The Pico brings its own 3.3 V buck, USB and BOOTSEL button, so the carrier only adds:
an external 5 V input through a Schottky into VSYS (the Pico's own VBUS diode then keeps USB and
the external supply from fighting), 3V3 decoupling for whatever hangs off the Pico's 3V3 pin
(300 mA budget), a RUN (reset) button, the SWD pads brought out to a pad row, and one LED.
"""
from schkit import *  # noqa: F401,F403

setup("pico-block", lib="pico", title="Pico carrier block", company="Product Speedrun kit",
      date="2026-10-29", comments=["Raspberry Pi Pico castellated + 5 V in + RUN + SWD + LED"],
      ns="7d0f3b52-1c4e-4a8a-9e57-31b0c0de0a01")

# --- Power in: 5 V wire pads -> Schottky -> VSYS (top-left)
part("J1", "Connector_Generic:Conn_01x02", "5V IN", "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
     "C173752", "S2B-PH-K-S", at(8, 20), {"1": "5V_IN", "2": "GND"},
     "JST-PH 2-pin right-angle: external 5 V (+ = pin 1). Leave off when USB alone powers it")
part("D1", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123", "C8598", "B5819W SL", at(20, 19),
     {"1": "VSYS", "2": "5V_IN"}, "Schottky 40 V 1 A SOD-123: external 5 V into VSYS (Pico datasheet 4.5)")
cap("C1", "10uF", at(30, 25), "VSYS", "GND")
cap("C2", "10uF", at(38, 25), "3V3", "GND")
cap("C3", "100nF", at(42, 25), "3V3", "GND")
part("TP1", "Connector:TestPoint", "VBUS", "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(56, 14), {"1": "VBUS"},
     "Test pad: USB 5 V from the Pico's own connector", dnp=True)
part("TP2", "Connector:TestPoint", "3V3", "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(60, 14), {"1": "3V3"},
     "Test pad", dnp=True)
part("TP3", "Connector:TestPoint", "GND", "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(64, 14), {"1": "GND"},
     "Test pad", dnp=True)

# --- The Pico (bottom-left). GPIO picked for the layout: GP22 (pin 29) for the LED sits beside RUN.
pico = {str(n): None for n in range(1, 41)}
pico.update({str(n): "GND" for n in (3, 8, 13, 18, 23, 28, 38)})
pico.update({"33": "AGND", "39": "VSYS", "36": "3V3", "40": "VBUS", "30": "RUN", "29": "LED_IO",
             "35": None, "37": None, "D1": "SWCLK", "D2": "GND", "D3": "SWDIO"})
part("U1", "MCU_Module:RaspberryPi_Pico_Debug", "Raspberry Pi Pico", "Module:RaspberryPi_Pico_SMD", "",
     "SC0915 (Pico) / SC1631 (Pico 2)", at(26, 70), pico,
     "RP2040 / RP2350 module, castellated, 21 x 51 mm; USB and BOOTSEL on the module")
res("R2", "0", at(40, 84), "AGND", "GND")                # AGND and GND are both power outputs: ERC wants a part between
part("SW1", "Switch:SW_Push", "RUN", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "C318884", "TS-1187A-B-A-B",
     at(52, 66), {"1": "RUN", "2": "GND"}, "Tactile switch 5.1 x 5.1 mm SMD: RUN to GND resets (the Pico pulls RUN up)")
part("J2", "Connector_Generic:Conn_01x03", "SWD", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
     "", "", at(52, 82), {"1": "SWCLK", "2": "GND", "3": "SWDIO"},
     "SWD pads for a Debug Probe or picoprobe (unpopulated)", dnp=True)

# --- LED (right)
res("R1", "1k", at(80, 66), "LED_IO", "LED_A")
part("D2", "Device:LED", "Red", "LED_SMD:LED_0603_1608Metric", "C2286", "KT-0603R", at(90, 66),
     {"1": "GND", "2": "LED_A"}, "LED red 0603, ~1.3 mA from 3.3 V through 1k")

# --- mechanical
for i in range(3):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(90 + 4 * i, 104), {}, "Fiducial")

for i, (net, xy) in enumerate((("5V_IN", at(4, 31)), ("VSYS", at(8, 31))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)

NOTES += [
    (at(4, 3), "POWER: USB on the Pico, or 5 V on J1 -> D1 B5819W -> VSYS. The Pico's own diode stops J1 back-feeding\n"
               "USB. The Pico's buck makes 3V3 (up to ~300 mA for the board). VBUS (USB 5 V only) is on TP1."),
    (at(4, 46), "MCU: Pico soldered flat by its castellations (no headers). Flash over USB: hold BOOTSEL (on the\n"
                "module), tap SW1 RUN. SWD (D1-D3 under the module's end) on J2 for a Debug Probe.\n"
                "AGND to GND through R2 0R (swap for a ferrite if the ADC must be quiet). LED on GP22."),
]
