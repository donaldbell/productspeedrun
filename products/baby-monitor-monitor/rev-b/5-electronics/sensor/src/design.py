"""BMM Sensor (episode 003, Baby Monitor Monitor): the listening puck's parts and nets for tools/kicad.

One flat board in the bean, top face up. USB-C is the main power input (it usually lives plugged in
next to the baby monitor) and charges a 2000 mAh 103450 LiPo through an MCP73831, so it also runs
unplugged for a night or two (camping). A Schottky + P-FET power path runs the board from USB when
it's there and from the cell when it isn't. A slide switch on the back drives the AP2112K's enable:
off = no 3.3 V, but the cell still charges. The ESP32-C6-MINI-1 reads an ICS-43434 I2S mic, turns
the sound level into 0-3 and sends it to the watch over ESP-NOW. The top button is "I'm awake"
(tap = stop the watch buzzing, hold = test / pair); one green status LED.
"""
from schkit import *  # noqa: F401,F403

setup("bmm-sensor", lib="bmm", title="Baby Monitor Monitor: Sensor", company="Product Speedrun 003",
      date="2026-11-04", comments=["ESP32-C6-MINI-1 + ICS-43434 mic + USB-C power path + LiPo charger + LDO"],
      ns="5e2a9c14-7b3d-4c80-a1f6-d4b8e2c0f003")

C6 = "RF_Module:ESP32-C6-MINI-1"
WIRE2 = "Connector_Wire:SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm"

# --- Power: USB-C, charger, power path, LDO, battery sense (top-left)
part("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
     "", "USB4105-GF-A", at(8, 22),
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
      "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DN", "B7": "USB_DN",
      "A8": None, "B8": None, "SH": "GND"},
     "USB-C receptacle, USB 2.0, 16 pin, top mount: power, charging and flashing (ESP32-C6 native USB)")
res("R1", "5.1k", at(22, 30), "CC1", "GND")             # 5.1k pull-downs: a C-to-C charger gives 5 V
res("R2", "5.1k", at(26, 30), "CC2", "GND")
cap("C1", "4.7uF", at(30, 22), "VBUS", "GND")
part("U1", "Battery_Management:MCP73831-2-OT", "MCP73831T-2ACI/OT", "Package_TO_SOT_SMD:SOT-23-5", "C424093",
     "MCP73831T-2ACI/OT", at(40, 18), {"4": "VBUS", "3": "VBAT", "1": "CHG_STAT", "5": "PROG", "2": "GND"},
     "Li-ion/LiPo linear charger 4.2 V, SOT-23-5")
res("R3", "3.9k", at(36, 30), "PROG", "GND")            # 1000 V / 3.9k = 256 mA: ~8 h for 2000 mAh, kept low for the SOT-23-5's heat
cap("C2", "4.7uF", at(52, 26), "VBAT", "GND")
part("J2", "Connector_Generic:Conn_01x02", "LiPo", WIRE2, "", "", at(52, 36), {"1": "VBAT", "2": "GND"},
     "Solder pads for the LiPo's leads (+ = pin 1); cell has its own protection PCB", dnp=True)
# power path: USB present -> D1 feeds VSYS and Q1 is off (gate high); USB gone -> R4 pulls the gate low, Q1 on
part("D1", "Diode:1N5819WS", "1N5819WS", "Diode_SMD:D_SOD-323", "C191023", "1N5819WS", at(40, 6),
     {"1": "VSYS", "2": "VBUS"}, "Schottky 40 V 1 A SOD-323: USB into the system rail")
part("Q1", "Transistor_FET:AO3401A", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "C15127", "AO3401A", at(60, 12),
     {"1": "VBUS", "2": "VSYS", "3": "VBAT"}, "P-MOSFET -30 V -4 A SOT-23: battery into the system rail when USB is absent")
res("R4", "100k", at(52, 6), "VBUS", "GND")             # gate pull-down: Q1 on when USB is unplugged
part("U2", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3TRG1", "Package_TO_SOT_SMD:SOT-23-5", "C51118", "AP2112K-3.3TRG1",
     at(72, 18), {"1": "VSYS", "3": "LDO_EN", "2": "GND", "4": None, "5": "3V3"},
     "LDO 3.3 V 600 mA, SOT-23-5, enabled by the power switch")
part("SW2", "Switch:SW_SPDT", "POWER", "Button_Switch_SMD:SW_SPDT_PCM12", "", "PCM12SMTR", at(84, 10),
     {"1": "VSYS", "2": "LDO_EN", "3": "GND"}, "Slide switch SPDT right-angle SMD (C&K PCM12): on = LDO enabled, off = EN to GND")
cap("C3", "10uF", at(66, 26), "VSYS", "GND")
cap("C4", "10uF", at(82, 22), "3V3", "GND")
res("R5", "1M", at(60, 40), "VBAT", "VBAT_SENSE")       # VBAT / 2, ~2 uA
res("R6", "1M", at(60, 49), "VBAT_SENSE", "GND")
cap("C5", "100nF", at(66, 45), "VBAT_SENSE", "GND")

# --- MCU: ESP32-C6-MINI-1 with EN RC and IO8 pull-up (bottom-left)
part("U3", C6, "ESP32-C6-MINI-1-N4", "RF_Module:ESP32-C6-MINI-1", "", "ESP32-C6-MINI-1-N4", at(28, 80),
     {"3": "3V3", "8": "EN",
      "12": "VBAT_SENSE", "13": None, "5": "MIC_SD", "6": "LED_IO", "9": "MIC_SCK", "10": "MIC_WS",
      "15": None, "16": "BTN", "22": "IO8", "23": "IO9",
      "17": "USB_DN", "18": "USB_DP", "19": None, "20": None,
      "24": None, "25": None, "26": None,
      "27": "CHG_STAT", "28": None, "29": None, "30": None, "31": None,
      "4": None, "7": None, "21": None, "32": None, "33": None, "34": None, "35": None,
      **gnd_pins("1", "2", "11", "14", *[str(n) for n in range(36, 54)])},
     "ESP32-C6 Wi-Fi 6 / BLE 5 / 802.15.4 module (ESP-NOW), 4 MB flash, PCB antenna, 13.2 x 16.6 x 2.4 mm")
cap("C6", "10uF", at(6, 62), "3V3", "GND")
cap("C7", "100nF", at(10, 62), "3V3", "GND")
res("R7", "10k", at(6, 72), "3V3", "EN")
cap("C8", "1uF", at(10, 72), "EN", "GND")
res("R8", "10k", at(48, 62), "3V3", "IO8")              # strap: IO8 high for serial / USB download
part("TP1", "Connector:TestPoint", "IO9", "TestPoint:TestPoint_Pad_D1.0mm", "", "", at(56, 70), {"1": "IO9"},
     "Test pad: short to GND at reset for download mode (recovery only)", dnp=True)

# --- Input: I2S MEMS mic, top button (top-right)
part("U4", "Sensor_Audio:ICS-43434", "ICS-43434", "Sensor_Audio:InvenSense_ICS-43434-6_3.5x2.65mm", "", "ICS-43434",
     at(110, 24), {"1": "MIC_WS", "2": "GND", "3": "GND", "4": "MIC_SCK", "5": "3V3", "6": "MIC_SD"},
     "I2S MEMS microphone, bottom port over a 1 mm hole through the board, L/R low = left slot")
cap("C9", "100nF", at(122, 18), "3V3", "GND")
# SD is tri-stated between slots: the C6 holds IO2 with its internal pull-down (no resistor)
part("SW1", "Switch:SW_Push", "I'M AWAKE", "Button_Switch_SMD:SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm", "", "1TS009A-1800-5000-CT",
     at(100, 50), {"1": "BTN", "2": "GND"}, "Tact switch 6 x 6 x 5 mm SMD under the top cap: tap = I'm awake, hold = test / pair")

# --- Output: green status LED (bottom-right)
res("R9", "1k", at(100, 72), "LED_IO", "LED_A")
part("LED1", "Device:LED", "green", "LED_SMD:LED_0603_1608Metric", "C72043", "KT-0603G", at(110, 76),
     {"2": "LED_A", "1": "GND"}, "LED green 0603: status under the front light pipe")

# --- Mechanical: M2 holes on the base posts (H1.. match fit.json holes)
for i in range(2):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2")

# --- power flags (nets fed only by connectors / passive pins)
for i, (net, xy) in enumerate((("VBUS", at(4, 34)), ("GND", at(8, 34)), ("VSYS", at(12, 34))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)

NOTES += [
    (at(4, 3), "POWER: USB-C (5.1k CC) -> U1 MCP73831 charges the 2000 mAh LiPo at 256 mA (R3 3.9k).\n"
               "Power path: USB -> D1 -> VSYS; USB unplugged -> R4 pulls Q1's gate low -> VBAT -> VSYS.\n"
               "U2 AP2112K-3.3 from VSYS, EN from SW2 (off = EN to GND). VBAT_SENSE = VBAT / 2 -> IO0, CHG_STAT -> IO21 (internal pull-up; the module side facing the charger)."),
    (at(80, 3), "MIC: ICS-43434 on IO4 / IO5 / IO2 (SCK / WS / SD: the module's side facing the mic), bottom port through the board to the front grille.\n"
                "Firmware: 16 kHz I2S, RMS over 250 ms, three thresholds -> level 0-3 sent over ESP-NOW."),
    (at(80, 60), "I'M AWAKE button on IO7 (LP GPIO, internal pull-up). STATUS LED green on IO3.\n"
                 "IO8 pulled high (R8); IO9 internal pull-up, TP1 pulls it low for recovery. USB on IO12/IO13."),
]

OFF_BOARD += [
    ("BT1", "LiPo 2000 mAh", "LiPo 3.7 V ~2000 mAh with protection PCB, 103450 (10 x 34 x 50 mm), leads soldered to J2",
     "off-board", "generic 103450"),
]
