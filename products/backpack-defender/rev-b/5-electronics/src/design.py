"""Backpack Defender Rev B: the parts and nets for tools/kicad.

Ported from Rev A (episode 001, now tools/kicad/example/design.py), then changed for Rev B
(see ../../REV.md and ../../FIT.md):
  - SW2 power slide switch in series with battery + (hosts: "a physical on/off switch")
  - BZ1 piezo and its series resistors -> J3 wire pads for a 20 mm 8 ohm speaker
  - D1/D2 white eye LEDs, switched low-side by Q2 from IO10 (hosts: "white LEDs ... flash")
  - U4 AM312 is now off-board (it drops through the board cutout): J4 wire pads
  - SW1 is a 12 x 12 x 4.3 mm low-profile tact switch (thinner case)
  - J2 programming pads are a Tag-Connect TC2030 footprint (no header to hit the lid)
Sheet layout: one block per corner of an A3 sheet, at() in 2.54 mm grid units.
"""
from schkit import *  # noqa: F401,F403
from parts import max98357a, tps61023

setup("backpack-defender", lib="backpack", title="Backpack Defender", company="Product Speedrun 001",
      rev="B", date="2026-11-01",
      comments=["ESP32-C3 + 2xAAA boost + power switch + MAX98357A + speaker + AM312 PIR + eye LEDs"],
      ns="6a3f1c2e-0b7d-4e19-9a51-bacc9ac0de01")

BOOST, AMP = tps61023(), max98357a()
WIRE2 = "Connector_Wire:SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm"
WIRE3 = "Connector_Wire:SolderWire-0.25sqmm_1x03_P4.2mm_D0.65mm_OD1.7mm"

# --- Battery in, power switch, reverse-polarity guard, 3.3 V boost, battery sense (top-left)
part("J1", "Connector_Generic:Conn_01x02", "2xAAA leads", WIRE2, "", "", at(10, 20), {"1": "BAT_RAW", "2": "GND"},
     "Solder pads for the 2 x AAA cradle's contact wires (+ = pin 1)", dnp=True)
part("SW2", "Switch:SW_SPDT", "POWER", "Button_Switch_THT:SW_Slide_SPDT_Angled_CK_OS102011MA1Q", "", "OS102011MA1QN1",
     at(16, 12), {"1": "BAT_IN", "2": "BAT_RAW", "3": None},
     "Slide switch SPDT right-angle THT, 4 mm lever out through the case's right end: disconnects the cells")
part("Q1", "Transistor_FET:AO3401A", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "C15127", "AO3401A", at(22, 19),
     {"1": "GND", "2": "VBAT", "3": "BAT_IN"}, "P-MOSFET -30 V -4 A SOT-23: reverse-battery guard, drain to the cells, gate to GND")
cap("C1", "10uF", at(30, 25), "VBAT", "GND")
part("L1", "Device:L", "1uH", "Inductor_SMD:L_Changjiang_FXL0624", "C524602", "FXL0624-1R0-M", at(38, 16),
     {"1": "VBAT", "2": "BOOST_SW"}, "Inductor, power, 1 uH, 9 A sat, 7 x 6.6 mm")
part("U1", BOOST, "TPS61023DRLR", "Package_TO_SOT_SMD:SOT-563", "C919459", "TPS61023DRLR", at(44, 22),
     {"3": "VBAT", "2": "VBAT", "5": "BOOST_SW", "6": "3V3", "1": "BOOST_FB", "4": "GND"},
     "Synchronous boost converter 0.5-5.5 V in, 3.7 A switch, SOT-563")
cap("C2", "22uF", at(56, 27), "3V3", "GND")
cap("C3", "22uF", at(60, 27), "3V3", "GND")
res("R1", "1M", at(52, 31), "3V3", "BOOST_FB")          # 0.595 x (1 + 1M / 220k) = 3.30 V
res("R2", "220k", at(52, 40), "BOOST_FB", "GND")
res("R3", "1M", at(30, 35), "VBAT", "VBAT_SENSE")       # VBAT / 2, ~1.5 uA
res("R4", "1M", at(30, 44), "VBAT_SENSE", "GND")
cap("C4", "100nF", at(36, 40), "VBAT_SENSE", "GND")
part("TP1", "Connector:TestPoint", "VBAT", "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(66, 14), {"1": "VBAT"},
     "Test pad", dnp=True)
part("TP2", "Connector:TestPoint", "3V3", "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(70, 14), {"1": "3V3"},
     "Test pad", dnp=True)
part("TP3", "Connector:TestPoint", "GND", "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(74, 14), {"1": "GND"},
     "Test pad", dnp=True)

# --- ESP32-C3 module, strapping, programming pads, big button (bottom-left)
part("U2", "RF_Module:ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02-N4", "RF_Module:ESP32-C3-WROOM-02", "C2934560",
     "ESP32-C3-WROOM-02-N4", at(26, 84),
     {"1": "3V3", "2": "EN", "18": "PIR_OUT", "17": "BTN", "16": "IO2", "15": "VBAT_SENSE",
      "3": "I2S_BCLK", "4": "I2S_LRCLK", "5": "I2S_DIN", "6": "AMP_SD", "7": "IO8", "8": "IO9", "10": "EYE_LED",
      "11": None, "12": None, "13": "USB_DN", "14": "USB_DP", "9": "GND", "19": "GND"},
     "ESP32-C3 Wi-Fi/BLE module, 4 MB flash, PCB antenna, 18 x 20 x 3.2 mm")
cap("C5", "10uF", at(6, 60), "3V3", "GND")
cap("C6", "100nF", at(10, 60), "3V3", "GND")
res("R5", "10k", at(6, 70), "3V3", "EN")
cap("C7", "1uF", at(10, 70), "EN", "GND")
res("R6", "10k", at(44, 60), "3V3", "IO2")              # strapping pins high at boot
res("R7", "10k", at(48, 60), "3V3", "IO8")
res("R8", "10k", at(52, 60), "3V3", "IO9")
part("J2", "Connector_Generic:Conn_02x03_Odd_Even", "PROG (TC2030)", "Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical",
     "", "TC2030-IDC-NL (cable)", at(48, 84), {"1": "GND", "2": "3V3", "3": "USB_DN", "4": "USB_DP", "5": "EN", "6": "IO9"},
     "Programming pads for a Tag-Connect cable: ESP32-C3 native USB + EN / IO9 (nothing to fit)", dnp=True)
part("SW1", "Switch:SW_Push", "SILENCE", "Button_Switch_THT:SW_PUSH-12mm", "", "TS-1212-4.3 (12x12x4.3 THT)", at(48, 98),
     {"1": "BTN", "2": "GND"}, "Tactile switch 12 x 12 x 4.3 mm THT (low profile), under the big silence button")
res("R9", "100k", at(42, 92), "3V3", "BTN")

# --- PIR (top-right): the AM312 drops through the board cutout and is wired to J4
part("J4", "Connector_Generic:Conn_01x03", "PIR leads", WIRE3, "", "", at(102, 20),
     {"1": "PIR_VCC", "2": "PIR_OUT", "3": "GND"}, "Solder pads for the AM312's three legs (VCC / OUT / GND) by short wires", dnp=True)
res("R10", "100", at(88, 16), "3V3", "PIR_VCC")         # RC filter: PIRs false-trigger on supply ripple
cap("C8", "10uF", at(92, 23), "PIR_VCC", "GND")

# --- Eye LEDs (top-right, lower): two white LEDs under the eye light pipes, one low-side FET
res("R14", "47", at(84, 34), "3V3", "LED_A_L")          # ~8 mA at Vf 2.9 V; both together ~16 mA from 3V3
res("R15", "47", at(96, 34), "3V3", "LED_A_R")
part("D1", "Device:LED", "White", "LED_SMD:LED_0603_1608Metric", "C2290", "KT-0603W", at(88, 38),
     {"1": "EYE_K", "2": "LED_A_L"}, "LED white 0603, under the left eye's light pipe")
part("D2", "Device:LED", "White", "LED_SMD:LED_0603_1608Metric", "C2290", "KT-0603W", at(100, 38),
     {"1": "EYE_K", "2": "LED_A_R"}, "LED white 0603, under the right eye's light pipe")
part("Q2", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23", "C20917", "AO3400A", at(94, 44),
     {"1": "EYE_LED", "2": "GND", "3": "EYE_K"}, "N-MOSFET 30 V 5.7 A SOT-23: switches both eye LEDs from IO10")
res("R16", "100k", at(86, 46), "EYE_LED", "GND")        # LEDs off while the module boots or sleeps

# --- I2S amp and speaker pads (bottom-right)
part("U3", AMP, "MAX98357AETE+T", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm_ThermalVias",
     "", "MAX98357AETE+T", at(94, 68),
     {"16": "I2S_BCLK", "14": "I2S_LRCLK", "1": "I2S_DIN", "4": "AMP_SD", "2": None,
      "7": "3V3", "8": "3V3", "9": "SPK_P", "10": "SPK_N", "5": None, "6": None, "12": None, "13": None,
      "3": "GND", "11": "GND", "15": "GND", "17": "GND"}, "I2S class-D mono amplifier, TQFN-16 3 x 3 mm")
cap("C9", "10uF", at(108, 56), "3V3", "GND")
cap("C10", "100nF", at(112, 56), "3V3", "GND")
res("R11", "100k", at(82, 78), "AMP_SD", "GND")         # amp off while the MCU boots or sleeps
part("J3", "Connector_Generic:Conn_01x02", "Speaker", WIRE2, "", "", at(118, 71), {"1": "SPK_P", "2": "SPK_N"},
     "Solder pads for the 20 mm 8 ohm speaker's leads", dnp=True)

# --- mechanical: M2 holes on the enclosure posts, fiducials (not placed by the assembler)
for i in range(4):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(90 + 4 * i, 104), {}, "Fiducial")

# --- power flags (nets fed only by connectors / passive pins)
for i, (net, xy) in enumerate((("BAT_RAW", at(4, 31)), ("GND", at(8, 31)), ("VBAT", at(12, 31)), ("PIR_VCC", at(16, 31)),
                               ("BAT_IN", at(20, 31))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)


NOTES += [
    (at(4, 3), "POWER: 2 x AAA (2.0-3.2 V) on J1 -> SW2 slide switch (off = cells disconnected) -> Q1 AO3401A\n"
               "reverse-battery guard (gate to GND) -> VBAT -> U1 TPS61023 boost, always on (EN tied to VIN).\n"
               "3V3 = 0.595 V x (1 + R1/R2) = 0.595 x (1 + 1M/220k) = 3.30 V. L1 1 uH.\n"
               "VBAT_SENSE = VBAT / 2 (R3/R4 1M, ~1.5 uA) -> IO3 (ADC1_CH3)."),
    (at(4, 52), "MCU: ESP32-C3-WROOM-02 on the board's BOTTOM face (frees the top for the eye LEDs), PCB antenna\n"
                "on the back edge, copper-free underneath. IO0 PIR_OUT and IO1 BTN wake it from deep sleep.\n"
                "IO4/IO5/IO6 = I2S BCLK/LRCLK/DIN, IO7 AMP_SD, IO10 EYE_LED. Straps IO2/IO8/IO9 pulled high.\n"
                "Native USB (IO18/IO19) on the J2 Tag-Connect pads."),
    (at(80, 3), "PIR: AM312 drops through a 10.8 mm board cutout onto a boss in the case; its legs reach J4 by wires.\n"
                "RC-filtered supply (R10/C8): PIRs false-trigger on boost / class-D / Wi-Fi ripple."),
    (at(80, 28), "EYES: D1/D2 white 0603 under the light pipes in the eye highlights, R14/R15 47R from 3V3, Q2 low side\n"
                 "on IO10 (R16 holds it off at boot). Flash them with the alarm (LEDC PWM for a soft pulse)."),
    (at(80, 50), "SOUND: MAX98357A (mono, left channel when SD_MODE is driven high; R11 keeps it off otherwise).\n"
                 "GAIN_SLOT open = 9 dB. Drives the 20 mm 8 ohm speaker on J3 directly (Rev A's piezo resistors gone)."),
]

OFF_BOARD += [
    ("BT1", "2xAAA cradle", "2 x AAA cells in a cradle in the bottom plate, spring contacts wired to J1",
     "off-board", "2 x Keystone-style AAA contact pairs"),
    ("U4", "AM312", "Mini PIR motion sensor, dome through the lid, wired to J4", "off-board", "AM312"),
    ("LS1", "Speaker 20 mm 8 ohm", "Micro speaker 20 x 4 mm, 8 ohm 1 W, faces the lid grille on a foam ring, wired to J3",
     "off-board", "generic 2004 micro speaker"),
]
