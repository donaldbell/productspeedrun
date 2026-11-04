"""BMM Receiver (episode 003, Baby Monitor Monitor): the wearable's parts and nets for tools/kicad.

One small board in a sealed watch case (no button, no USB: the hosts' call, so it can be waterproof
and there's nothing to press by accident in bed). Two pogo pins on the bottom face press on gold
contacts in the back plate; a magnetic clip-on charger feeds them 5 V, through a Schottky into an
MCP73831. An AP2112K makes 3.3 V, an ESP32-C6-MINI-1 listens for the sensor over ESP-NOW and PWMs
an ERM coin motor through a low-side MOSFET. WS2812B glow under the face, green link LED under a
light pipe. The LiPo and motor sit under the board on wire leads. "I'm awake" is the sensor's button.
"""
from schkit import *  # noqa: F401,F403

setup("bmm-receiver", lib="bmm", title="Baby Monitor Monitor: Receiver", company="Product Speedrun 003",
      date="2026-11-04", comments=["ESP32-C6-MINI-1 + pogo-pin LiPo charger + LDO + ERM haptic driver + glow LED"],
      ns="3b1d7e52-9c0a-4f6e-8d21-a0c6b7e1f003")

C6 = "RF_Module:ESP32-C6-MINI-1"
WIRE2 = "Connector_Wire:SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm"

# --- Power: pogo charge contacts, reverse-blocking Schottky, LiPo charger, battery pads, 3.3 V LDO (top-left)
POGO = "TestPoint:TestPoint_Pad_D2.0mm"
part("P1", "Connector_Generic:Conn_01x01", "POGO +", POGO, "", "Mill-Max 0907 SMD spring pin (~5 mm)", at(6, 18),
     {"1": "VCHG_IN"}, "Spring (pogo) pin, SMD, bottom face: + charge contact on the back plate")
part("P2", "Connector_Generic:Conn_01x01", "POGO -", POGO, "", "Mill-Max 0907 SMD spring pin (~5 mm)", at(6, 26),
     {"1": "GND"}, "Spring (pogo) pin, SMD, bottom face: - charge contact on the back plate")
part("D2", "Diode:1N5819WS", "1N5819WS", "Diode_SMD:D_SOD-323", "C191023", "1N5819WS", at(18, 18),
     {"1": "VBUS", "2": "VCHG_IN"}, "Schottky 40 V 1 A SOD-323: blocks reverse polarity and keeps the cell off the exposed contacts")
cap("C1", "4.7uF", at(30, 22), "VBUS", "GND")
part("U1", "Battery_Management:MCP73831-2-OT", "MCP73831T-2ACI/OT", "Package_TO_SOT_SMD:SOT-23-5", "C424093",
     "MCP73831T-2ACI/OT", at(40, 18), {"4": "VBUS", "3": "VBAT", "1": "CHG_STAT", "5": "PROG", "2": "GND"},
     "Li-ion/LiPo linear charger 4.2 V, SOT-23-5")
res("R1", "10k", at(36, 30), "PROG", "GND")             # 1000 V / 10k = 100 mA (~0.6 C for a 150 mAh cell)
# CHG_STAT (open drain) and IO9 use the C6's internal pull-ups
cap("C2", "4.7uF", at(52, 22), "VBAT", "GND")
part("J2", "Connector_Generic:Conn_01x02", "LiPo", WIRE2, "", "", at(58, 30), {"1": "VBAT", "2": "GND"},
     "Solder pads for the LiPo's leads (+ = pin 1); cell has its own protection PCB", dnp=True)
part("U2", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3TRG1", "Package_TO_SOT_SMD:SOT-23-5", "C51118", "AP2112K-3.3TRG1",
     at(66, 18), {"1": "VBAT", "3": "VBAT", "2": "GND", "4": None, "5": "3V3"},
     "LDO 3.3 V 600 mA, SOT-23-5, EN tied to VIN (always on; the C6 deep-sleeps)")
cap("C3", "10uF", at(76, 22), "3V3", "GND")
res("R2", "1M", at(60, 40), "VBAT", "VBAT_SENSE")       # VBAT / 2, ~2 uA
res("R3", "1M", at(60, 49), "VBAT_SENSE", "GND")
cap("C4", "100nF", at(66, 45), "VBAT_SENSE", "GND")

# --- MCU: ESP32-C6-MINI-1 with EN RC and strap pull-ups (bottom-left)
part("U3", C6, "ESP32-C6-MINI-1-N4", "RF_Module:ESP32-C6-MINI-1", "", "ESP32-C6-MINI-1-N4", at(28, 80),
     {"3": "3V3", "8": "EN",
      "12": "VBAT_SENSE", "13": "CHG_STAT", "5": "MOT_PWM", "6": None, "9": None, "10": None,
      "15": "LED_IO", "16": "LINK_IO", "22": "IO8", "23": "IO9",
      "17": "USB_DN", "18": "USB_DP", "19": None, "20": None, "24": None, "25": None, "26": None,
      "27": None, "28": None, "29": None, "30": None, "31": None,
      "4": None, "7": None, "21": None, "32": None, "33": None, "34": None, "35": None,
      **gnd_pins("1", "2", "11", "14", *[str(n) for n in range(36, 54)])},
     "ESP32-C6 Wi-Fi 6 / BLE 5 / 802.15.4 module (ESP-NOW), 4 MB flash, PCB antenna, 13.2 x 16.6 x 2.4 mm")
cap("C5", "10uF", at(6, 62), "3V3", "GND")
cap("C6", "100nF", at(10, 62), "3V3", "GND")
res("R4", "10k", at(6, 72), "3V3", "EN")
cap("C7", "1uF", at(10, 72), "EN", "GND")
res("R5", "10k", at(48, 62), "3V3", "IO8")              # strap: IO8 high for serial / USB download
part("TP1", "Connector:TestPoint", "IO9", "TestPoint:TestPoint_Pad_D1.0mm", "", "", at(56, 70), {"1": "IO9"},
     "Test pad: short to GND at reset for download mode (recovery only)", dnp=True)

# --- Factory flashing: native USB on test pads (the case is sealed; later updates go over the air)
part("TP2", "Connector:TestPoint", "USB D+", "TestPoint:TestPoint_Pad_D1.0mm", "", "", at(96, 18), {"1": "USB_DP"},
     "Test pad: USB D+ for the flashing jig", dnp=True)
part("TP3", "Connector:TestPoint", "USB D-", "TestPoint:TestPoint_Pad_D1.0mm", "", "", at(100, 18), {"1": "USB_DN"},
     "Test pad: USB D- for the flashing jig", dnp=True)

# --- Outputs: haptic ERM driver, glow LED, link LED (bottom-right)
part("Q1", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23", "C20917", "AO3400A", at(108, 80),
     {"1": "MOT_PWM", "2": "GND", "3": "MOT_N"}, "N-MOSFET 30 V 5.7 A SOT-23: low-side PWM switch for the ERM motor")
res("R6", "100k", at(100, 88), "MOT_PWM", "GND")       # motor off while the C6 boots or sleeps
part("D1", "Diode:1N5819WS", "1N5819WS", "Diode_SMD:D_SOD-323", "C191023", "1N5819WS", at(116, 70),
     {"1": "VBAT", "2": "MOT_N"}, "Schottky 40 V 1 A SOD-323: flyback across the motor")
cap("C8", "10uF", at(124, 64), "VBAT", "GND")           # bulk for the motor's start current
part("J3", "Connector_Generic:Conn_01x02", "ERM motor", WIRE2, "", "", at(126, 76),
     {"1": "VBAT", "2": "MOT_N"}, "Solder pads for the coin motor's leads (red = pin 1)", dnp=True)

part("LED1", "LED:WS2812B-2020", "WS2812B-2020", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm", "C965555", "WS2812B-2020",
     at(100, 52), {"1": None, "2": "GND", "3": "LED_IO", "4": "VBAT"}, "RGB LED 2 x 2 mm: the face's glow")
cap("C9", "100nF", at(110, 46), "VBAT", "GND")
res("R7", "1k", at(118, 34), "LINK_IO", "LINK_A")
part("LED2", "Device:LED", "green", "LED_SMD:LED_0603_1608Metric", "C72043", "KT-0603G", at(126, 38),
     {"2": "LINK_A", "1": "GND"}, "LED green 0603: link indicator under the front light pipe")

# --- Mechanical: M2 holes on the lid posts (H1.. match fit.json holes)
for i in range(2):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2")

# --- power flags (nets fed only by connectors / passive pins)
for i, (net, xy) in enumerate((("VCHG_IN", at(4, 34)), ("GND", at(8, 34)), ("VBUS", at(12, 34))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)

NOTES += [
    (at(4, 3), "POWER: pogo pins P1 / P2 (magnetic clip-on charger, 5 V) -> D2 -> U1 MCP73831 charges the LiPo at 100 mA (R1 10k).\n"
               "VBAT (3.0-4.2 V) feeds U2 AP2112K-3.3 (always on), the motor and the glow LED.\n"
               "VBAT_SENSE = VBAT / 2 -> IO0 (ADC). CHG_STAT -> IO1 (low while charging)."),
    (at(4, 54), "MCU: ESP32-C6-MINI-1, antenna on a board edge with copper kept clear. Native USB on IO12/IO13\n"
                "to test pads TP2/TP3 (flashed before the case is sealed; then OTA). IO2 MOT_PWM,\n"
                "IO6 glow LED, IO7 link LED. IO8 pulled high (R5); IO9 internal pull-up, TP1 pulls it low for recovery."),
    (at(80, 60), "HAPTIC: ERM coin motor (10 x 2.7 mm, 3 V) on VBAT, Q1 low side, PWM ~20 kHz from IO2.\n"
                 "Three levels = 3 duty cycles; firmware caps duty at ~70 % at full battery (motor is 3 V rated).\n"
                 "GLOW: WS2812B-2020 on VBAT (works to ~3.5 V); link LED green 0603 on IO7."),
]

OFF_BOARD += [
    ("BT1", "LiPo 150 mAh", "LiPo 3.7 V ~150 mAh with protection PCB, 402025 (4 x 20 x 25 mm), leads soldered to J2",
     "off-board", "generic 402025"),
    ("M1", "ERM coin motor", "Coin vibration motor 10 x 2.7 mm, 3 V ~80 mA, adhesive back, leads soldered to J3",
     "off-board", "generic 1027 coin ERM"),
]
