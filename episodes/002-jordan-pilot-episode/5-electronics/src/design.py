"""Gamer Companion (episode 002): the parts and nets for tools/kicad.

One vertical board behind the face. KiCad top = the face side (PIR, eye LEDs), bottom = the back
(module, power, audio, connectors): see layout.BOTTOM. 5 V comes in from a USB-C breakout on the
back wall over a 4-wire JST-SH harness (J1); the blower (J2) and speaker (J3) are off-board too.
"""
from schkit import *  # noqa: F401,F403
from parts import am312, max98357a

setup("gamer-companion", lib="gamer", title="Gamer Companion", company="Product Speedrun 002",
      date="2026-10-28", comments=["ESP32-S3 + LDO + MAX98357A + ICS-43434 + AM312 + 2xWS2812 + blower driver"],
      ns="2c7f9d1a-6e3b-4a58-b0c4-9e1d5a7b3f02")

AMP, PIR = max98357a(), am312()
SH2 = "Connector_JST:JST_SH_SM02B-SRSS-TB_1x02-1MP_P1.00mm_Horizontal"
SH4 = "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"

# --- Power: USB harness in, 5 V bulk, 3.3 V LDO (top-left)
part("J1", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", "USB harness", SH4, "C160390", "SM04B-SRSS-TB(LF)(SN)", at(8, 20),
     {"1": "VBUS", "2": "USB_DN", "3": "USB_DP", "4": "GND", "MP": "GND"},
     "JST-SH 4-pin: VBUS / D- / D+ / GND from the USB-C breakout on the back wall (it carries the 5.1k CC pull-downs)")
cap("C1", "22uF", at(20, 25), "VBUS", "GND")
part("U1", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3TRG1", "Package_TO_SOT_SMD:SOT-23-5", "C51118", "AP2112K-3.3TRG1",
     at(34, 22), {"1": "VBUS", "3": "VBUS", "2": "GND", "4": None, "5": "3V3"},
     "LDO 3.3 V 600 mA, SOT-23-5, EN tied to VIN (always on)")
cap("C3", "10uF", at(44, 27), "3V3", "GND")
cap("C4", "100nF", at(48, 27), "3V3", "GND")
# test pads for reset / download mode (probe VBUS, 3V3, GND on J1, C3 and C1)
for i, (net, col) in ((4, ("EN", 70)), (5, ("IO0", 74))):
    part("TP%d" % i, "Connector:TestPoint", net, "TestPoint:TestPoint_Pad_D1.5mm", "", "", at(col, 14), {"1": net},
         "Test pad", dnp=True)

# --- MCU: ESP32-S3-WROOM-1-N16R8 with EN RC and IO0 pull-up (bottom-left)
part("U2", "RF_Module:ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N16R8", "RF_Module:ESP32-S3-WROOM-1", "C2913202",
     "ESP32-S3-WROOM-1-N16R8", at(30, 76),
     {"1": "GND", "2": "3V3", "3": "EN", "4": "I2S_BCLK", "5": "I2S_LRCLK", "6": None, "7": None,
      "8": "PIR_OUT", "9": "LED_IO", "10": None, "11": "I2S_DIN", "12": "AMP_SD", "13": "USB_DN",
      "14": "USB_DP", "15": None, "16": None, "17": "MIC_SCK", "18": "MIC_WS", "19": "MIC_SD", "20": "FAN_PWM", "21": None,
      "22": None, "23": None, "24": None, "25": None, "26": None, "27": "IO0", "28": None, "29": None, "30": None,
      "31": None, "32": None, "33": None, "34": None, "35": None, "36": None, "37": None, "38": None, "39": None,
      "40": "GND", "41": "GND"},
     "ESP32-S3 Wi-Fi/BLE module, 16 MB flash + 8 MB octal PSRAM (runs ESP-SR on-device), PCB antenna, 18 x 25.5 x 3.1 mm")
cap("C5", "10uF", at(6, 58), "3V3", "GND")
cap("C6", "100nF", at(10, 58), "3V3", "GND")
res("R1", "10k", at(6, 68), "3V3", "EN")
cap("C7", "1uF", at(10, 68), "EN", "GND")
# IO0: the S3's internal pull-up holds it high at reset (normal boot); TP5 can force it low.

# --- Sensors: PIR with filtered supply, I2S mic (top-right)
part("U5", PIR, "AM312", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", "", "AM312",
     at(102, 20), {"1": "PIR_VCC", "2": "PIR_OUT", "3": "GND"}, "Mini PIR motion sensor; dome through the visor")
res("R3", "100", at(88, 16), "3V3", "PIR_VCC")          # RC filter: PIRs false-trigger on supply ripple
cap("C8", "10uF", at(92, 23), "PIR_VCC", "GND")
part("U4", "Sensor_Audio:ICS-43434", "ICS-43434", "Sensor_Audio:InvenSense_ICS-43434-6_3.5x2.65mm", "", "ICS-43434",
     at(130, 24), {"1": "MIC_WS", "2": "GND", "3": "GND", "4": "MIC_SCK", "5": "3V3", "6": "MIC_SD"},
     "I2S MEMS microphone, bottom port (over a 1 mm hole in the board), L/R low = left slot")
cap("C9", "100nF", at(142, 18), "3V3", "GND")
res("R4", "100k", at(142, 30), "MIC_SD", "GND")         # SD is tri-stated between slots

# --- Outputs: eye LEDs, I2S amp + speaker, blower switch (bottom-right)
part("D2", "Diode:1N4148W", "1N4148W", "Diode_SMD:D_SOD-123", "C81598", "1N4148W", at(86, 44),
     {"1": "VLED", "2": "VBUS"}, "Signal diode, SOD-123: drops VBUS to ~4.3 V so 3.3 V data reads as high")
cap("C10", "10uF", at(94, 50), "VLED", "GND")
res("R5", "100", at(86, 54), "LED_IO", "LED_DIN")
part("LED1", "LED:WS2812B-2020", "WS2812B-2020", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm", "C965555", "WS2812B-2020",
     at(104, 52), {"1": "LED_D2", "2": "GND", "3": "LED_DIN", "4": "VLED"}, "RGB LED 2 x 2 mm, left eye")
part("LED2", "LED:WS2812B-2020", "WS2812B-2020", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm", "C965555", "WS2812B-2020",
     at(124, 52), {"1": None, "2": "GND", "3": "LED_D2", "4": "VLED"}, "RGB LED 2 x 2 mm, right eye")
cap("C11", "100nF", at(112, 44), "VLED", "GND")
cap("C12", "100nF", at(132, 44), "VLED", "GND")

part("U3", AMP, "MAX98357AETE+T", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm_ThermalVias",
     "", "MAX98357AETE+T", at(94, 80),
     {"16": "I2S_BCLK", "14": "I2S_LRCLK", "1": "I2S_DIN", "4": "AMP_SD", "2": None,
      "7": "VBUS", "8": "VBUS", "9": "SPK_P", "10": "SPK_N", "5": None, "6": None, "12": None, "13": None,
      "3": "GND", "11": "GND", "15": "GND", "17": "GND"}, "I2S class-D mono amplifier on 5 V, TQFN-16 3 x 3 mm")
cap("C13", "10uF", at(108, 68), "VBUS", "GND")
cap("C14", "100nF", at(112, 68), "VBUS", "GND")
res("R6", "100k", at(82, 90), "AMP_SD", "GND")          # amp off while the MCU boots
part("J3", "Connector_Generic_MountingPin:Conn_01x02_MountingPin", "SPEAKER", SH2, "C160402", "SM02B-SRSS-TB(LF)(SN)", at(118, 82),
     {"1": "SPK_P", "2": "SPK_N", "MP": "GND"}, "JST-SH 2-pin to the 28 mm 8 ohm speaker on the right wall")

part("Q1", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23", "C20917", "AO3400A", at(138, 92),
     {"1": "FAN_G", "2": "GND", "3": "FAN_N"}, "N-MOSFET 30 V 5.7 A SOT-23: low-side PWM switch for the blower")
res("R7", "100", at(126, 92), "FAN_PWM", "FAN_G")
res("R8", "100k", at(130, 100), "FAN_G", "GND")         # fan off at boot
part("D1", "Diode:1N5819WS", "1N5819WS", "Diode_SMD:D_SOD-323", "C191023", "1N5819WS", at(146, 80),
     {"1": "VBUS", "2": "FAN_N"}, "Schottky 40 V 1 A SOD-323: flyback across the blower")
part("J2", "Connector_Generic_MountingPin:Conn_01x02_MountingPin", "BLOWER", SH2, "C160402", "SM02B-SRSS-TB(LF)(SN)", at(154, 86),
     {"1": "VBUS", "2": "FAN_N", "MP": "GND"}, "JST-SH 2-pin to the 5 V 3010 blower (+ on pin 1)")

# --- Mechanical: M2 holes on the enclosure posts (H1.. match layout.HOLES), fiducials
for i in range(3):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(90 + 4 * i, 104), {}, "Fiducial")

# --- power flags (nets fed only by connectors / passive pins)
for i, (net, xy) in enumerate((("VBUS", at(4, 31)), ("GND", at(8, 31)), ("PIR_VCC", at(12, 31)), ("VLED", at(16, 31))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)


NOTES += [
    (at(4, 3), "POWER: USB-C breakout on the back wall (5.1k CC pull-downs on it) -> J1 JST-SH: VBUS / D- / D+ / GND.\n"
               "VBUS 5 V feeds the amp, the blower and (through D2) the LEDs. U1 AP2112K-3.3 LDO -> 3V3 for the\n"
               "module, mic and PIR. Budget ~150-250 mA typical, ~870 mA if everything peaks: firmware staggers\n"
               "speech, Wi-Fi and fan. No battery."),
    (at(4, 46), "MCU: ESP32-S3-WROOM-1-N16R8 on the board's back, antenna on the top edge (copper-free).\n"
                "Native USB on IO19/IO20 for flashing (no buttons needed). Pins picked for the layout: IO15 PIR\n"
                "(level with the PIR's OUT leg), IO16 LEDs, IO4/5/18 amp BCLK/LRCLK/DIN, IO8 amp SD,\n"
                "IO9/10/11 mic SCK/WS/SD, IO12 fan PWM. IO35-37 belong to the octal PSRAM."),
    (at(80, 3), "SENSORS: AM312 PIR on an RC-filtered supply (R3/C8). ICS-43434 mic on the back, port over a\n"
                "1 mm hole through the board, rubber boot to the face's mic port. L/R low = left slot."),
    (at(80, 36), "EYES: 2 x WS2812B-2020 on VLED = VBUS - one diode (~4.3 V), so their 0.7 x VDD input high\n"
                 "(~3.0 V) accepts 3.3 V data with no level shifter. Lit only when a reminder needs attention."),
    (at(80, 62), "SOUND + BREEZE: MAX98357A on 5 V (~1 W into 8 ohm), SD high = on / left, R6 keeps it off at boot.\n"
                 "Blower: Q1 AO3400A low side at ~25 kHz PWM, D1 flyback, R8 keeps it off at boot."),
]

OFF_BOARD += [
    ("BLOWER", "3010 blower 5 V", "Radial blower 30 x 30 x 10 mm, 5 V ~150 mA, lead re-terminated to JST-SH (J2)",
     "off-board", "generic 3010 5 V blower"),
    ("LS1", "8 ohm 1 W", "Speaker 28 mm round, 8 ohm 1 W, ~5 mm thick, on the right wall behind the grille (J3)",
     "off-board", "generic 28 mm 8 ohm 1 W"),
    ("USB-C", "USB-C breakout", "USB-C receptacle breakout with VBUS/D+/D-/GND and 5.1k CC pull-downs, on the back wall (J1)",
     "off-board", "generic 4-wire USB-C breakout"),
]
