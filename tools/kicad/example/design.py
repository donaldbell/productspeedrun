"""Backpack Defender (episode 001): the parts and nets. Example for tools/kicad.

Copied from episodes/001-demo-1/5-electronics/tools/gen_schematic.py into the kit's format.
Sheet layout: one block per corner of an A3 sheet, at() in 2.54 mm grid units; the generator
refuses if two different nets' labels land on the same point, so just move a part if it complains.
"""
from schkit import *  # noqa: F401,F403
from parts import am312, max98357a, tps61023

setup("backpack-defender", lib="backpack", title="Backpack Defender", company="Product Speedrun 001",
      date="2026-10-28", comments=["ESP32-C3 + 2xAAA boost + MAX98357A + piezo + AM312 PIR"],
      ns="6a3f1c2e-0b7d-4e19-9a51-bacc9ac0de01")

BOOST, AMP, PIR = tps61023(), max98357a(), am312()

# --- Battery in, reverse-polarity guard, 3.3 V boost, battery sense (top-left)
part("J1", "Connector_Generic:Conn_01x02", "2xAAA leads", "Connector_Wire:SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm",
     "", "", at(10, 20), {"1": "BAT_IN", "2": "GND"}, "Solder pads for the 2 x AAA holder's wire leads (+ = pin 1)", dnp=True)
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
      "3": "I2S_BCLK", "4": "I2S_LRCLK", "5": "I2S_DIN", "6": "AMP_SD", "7": "IO8", "8": "IO9", "10": None,
      "11": None, "12": None, "13": "USB_DN", "14": "USB_DP", "9": "GND", "19": "GND"},
     "ESP32-C3 Wi-Fi/BLE module, 4 MB flash, PCB antenna, 18 x 20 x 3.2 mm")
cap("C5", "10uF", at(6, 60), "3V3", "GND")
cap("C6", "100nF", at(10, 60), "3V3", "GND")
res("R5", "10k", at(6, 70), "3V3", "EN")
cap("C7", "1uF", at(10, 70), "EN", "GND")
res("R6", "10k", at(44, 60), "3V3", "IO2")              # strapping pins high at boot
res("R7", "10k", at(48, 60), "3V3", "IO8")
res("R8", "10k", at(52, 60), "3V3", "IO9")
part("J2", "Connector_Generic:Conn_01x06", "PROG (pogo)", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
     "", "", at(48, 84), {"1": "GND", "2": "3V3", "3": "USB_DN", "4": "USB_DP", "5": "EN", "6": "IO9"},
     "Programming pads: ESP32-C3 native USB + EN / IO9 (unpopulated)", dnp=True)
part("SW1", "Switch:SW_Push", "SILENCE", "Button_Switch_THT:SW_PUSH-12mm", "", "TS-1212-7.3 (12x12x7.3 THT)", at(48, 98),
     {"1": "BTN", "2": "GND"}, "Tactile switch 12 x 12 x 7.3 mm THT, under the big silence button")
res("R9", "100k", at(42, 92), "3V3", "BTN")

# --- PIR (top-right)
part("U4", PIR, "AM312", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", "", "AM312",
     at(102, 20), {"1": "PIR_VCC", "2": "PIR_OUT", "3": "GND"}, "Mini PIR motion sensor, Fresnel dome through the lid")
res("R10", "100", at(88, 16), "3V3", "PIR_VCC")         # RC filter: PIRs false-trigger on supply ripple
cap("C8", "10uF", at(92, 23), "PIR_VCC", "GND")

# --- I2S amp and piezo (bottom-right)
part("U3", AMP, "MAX98357AETE+T", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm_ThermalVias",
     "", "MAX98357AETE+T", at(94, 68),
     {"16": "I2S_BCLK", "14": "I2S_LRCLK", "1": "I2S_DIN", "4": "AMP_SD", "2": None,
      "7": "3V3", "8": "3V3", "9": "SPK_P", "10": "SPK_N", "5": None, "6": None, "12": None, "13": None,
      "3": "GND", "11": "GND", "15": "GND", "17": "GND"}, "I2S class-D mono amplifier, TQFN-16 3 x 3 mm")
cap("C9", "10uF", at(108, 56), "3V3", "GND")
cap("C10", "100nF", at(112, 56), "3V3", "GND")
res("R11", "100k", at(82, 78), "AMP_SD", "GND")         # amp off while the MCU boots or sleeps
res("R12", "100", at(110, 66), "SPK_P", "BZ_P")         # series R: tames the piezo's capacitive load
res("R13", "100", at(110, 76), "SPK_N", "BZ_N")
part("BZ1", "Device:Buzzer", "PS1240P02BT", "Buzzer_Beeper:Buzzer_TDK_PS1240P02BT_D12.2mm_H6.5mm", "", "PS1240P02BT",
     at(120, 71), {"1": "BZ_P", "2": "BZ_N"}, "Piezo transducer (externally driven) 12.2 mm, ~4 kHz resonance")

# --- mechanical: M2 holes on the enclosure posts, fiducials (not placed by the assembler)
for i in range(4):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(70 + 4 * i, 104), {}, "Mounting hole M2")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(90 + 4 * i, 104), {}, "Fiducial")

# --- power flags (nets fed only by connectors / passive pins)
for i, (net, xy) in enumerate((("BAT_IN", at(4, 31)), ("GND", at(8, 31)), ("VBAT", at(12, 31)), ("PIR_VCC", at(16, 31))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)


NOTES += [
    (at(4, 3), "POWER: 2 x AAA (2.0-3.2 V) on J1 -> Q1 AO3401A reverse-battery guard (gate to GND: on when the cells\n"
               "are the right way round, body diode blocks when reversed) -> VBAT -> U1 TPS61023 boost, always on\n"
               "(EN tied to VIN). 3V3 = 0.595 V x (1 + R1/R2) = 0.595 x (1 + 1M/220k) = 3.30 V. L1 1 uH.\n"
               "VBAT_SENSE = VBAT / 2 (R3/R4 1M, ~1.5 uA) -> IO3 (ADC1_CH3)."),
    (at(4, 52), "MCU: ESP32-C3-WROOM-02 (PCB antenna on the board's back edge, copper-free underneath).\n"
                "IO0 PIR_OUT and IO1 BTN wake it from deep sleep (only IO0-IO5 can). IO4/IO5/IO6 = I2S BCLK/LRCLK/DIN,\n"
                "IO7 AMP_SD. Straps IO2/IO8/IO9 pulled high. Native USB (IO18/IO19) on J2 pogo pads."),
    (at(80, 3), "PIR: AM312 on an RC-filtered supply (R10/C8): PIRs false-trigger on boost / class-D / Wi-Fi ripple.\n"
                "OUT is high ~2 s after motion."),
    (at(80, 45), "SOUND: MAX98357A (mono, left channel when SD_MODE is driven high; R11 keeps it off otherwise).\n"
                 "GAIN_SLOT open = 9 dB. R12/R13 100R in series with the piezo limit the class-D edge current into\n"
                 "its capacitance (~100 kHz low-pass). For an 8 ohm speaker on BZ1's pads, fit 0R instead."),
]

OFF_BOARD += [
    ("BT1", "2xAAA holder", "Battery holder, 2 x AAA side by side, wire leads (~52 x 25 x 12 mm), soldered to J1",
     "off-board", "generic 2xAAA holder with leads"),
]
