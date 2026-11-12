"""Aquarium Accent Light (episode 004): the parts and nets for tools/kicad.

A XIAO carrier (Rev A): one long, narrow board running the length of the light bar. Every part is on
the top face, the LED face that looks down at the water in use; the bottom face is bare, so the two
pouch cells lie flat against it. The XIAO ESP32-C6 brings the MCU, USB-C, LiPo charger and 3.3 V
LDO. It lies across the bar at the electronics end with its USB-C at the long side edge. The carrier
adds the cells' pads, a high-side switch for the LED chain, 12 WS2812B-2020s under the window squares,
an APDS-9960 (proximity / gesture / ambient) under the dome, an APDS-9251 RGB sensor under the chrome
oval, the porthole button, and battery / USB sense dividers.
"""
from schkit import *  # noqa: F401,F403
from parts import XIAO_C6_FP, apds9960, xiao_esp32c6

setup("aqua-accent", lib="aqua", title="Aquarium Accent Light", company="Product Speedrun 004",
      date="2026-11-11",
      comments=["XIAO ESP32C6 carrier: 12 x WS2812B-2020, APDS-9960 proximity, APDS-9251 colour, LED power switch"],
      ns="9b3e6c27-4d1a-4f85-a2c0-7e5d8b1f0004")

XIAO, APDS = xiao_esp32c6(), apds9960()
WIRE2 = "Connector_Wire:SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm"
LED_FP = "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm"
N_LEDS = 12

# --- Power: the two cells, VBAT bulk, battery and USB sense (top-left)
for i, ref in enumerate(("J1", "J2")):
    part(ref, "Connector_Generic:Conn_01x02", "LiPo %s" % "AB"[i], WIRE2, "", "", at(6 + 10 * i, 20),
         {"1": "VBAT", "2": "GND"},
         "Solder pads for a LiPo pouch's leads (+ = pin 1), the cell has its own protection PCB", dnp=True)
cap("C1", "22uF", at(28, 20), "VBAT", "GND")
res("R1", "200k", at(38, 16), "VBAT", "VBAT_SENSE")          # VBAT / 2 (Seeed's 200k 1:2), ~10 uA
res("R2", "200k", at(38, 30), "VBAT_SENSE", "GND")
cap("C2", "100nF", at(44, 30), "VBAT_SENSE", "GND")
res("R3", "100k", at(54, 16), "VBUS", "VBUS_SENSE")          # 5 V x 0.6 = 3.0 V when USB is in
res("R4", "150k", at(54, 30), "VBUS_SENSE", "GND")

# --- MCU: XIAO ESP32-C6, soldered flat (bottom-left)
part("U1", XIAO, "XIAO ESP32C6", XIAO_C6_FP, "", "113991254", at(24, 72),
     {"1": "VBAT_SENSE", "2": "VBUS_SENSE", "3": "BTN", "4": "LED_IO", "5": "SDA", "6": "SCL", "7": "LED_EN",
      "8": "RGB_INT", "9": "PROX_INT", "10": None, "11": None,
      "12": "3V3", "13": "GND", "14": "VBUS", "15": "VBAT", "16": "GND"},
     "Seeed XIAO ESP32C6 (USB-C, LiPo charger, 3.3 V LDO, ceramic antenna), castellations + BAT pads reflowed to the carrier")
res("R5", "4.7k", at(48, 60), "3V3", "SDA")
res("R6", "4.7k", at(52, 60), "3V3", "SCL")
res("R7", "10k", at(56, 60), "3V3", "BTN")
cap("C3", "10uF", at(48, 84), "3V3", "GND")                   # 3V3 bulk at the far (dome) end

# --- Sensors: APDS-9960 under the dome, APDS-9251 under the oval, porthole button (top-right)
part("U2", APDS, "APDS-9960", "Sensor:Avago_APDS-9960", "", "APDS-9960", at(96, 20),
     {"8": "3V3", "7": "SCL", "1": "SDA", "2": "PROX_INT", "5": "VBAT", "3": "LEDK", "4": "LEDK", "6": "GND"},
     "Proximity / gesture / ambient / RGBC sensor with IR LED, I2C 0x39: fish near the surface, room light")
cap("C4", "1uF", at(80, 14), "3V3", "GND")
cap("C5", "100nF", at(84, 14), "3V3", "GND")
cap("C6", "1uF", at(112, 14), "VBAT", "GND")                  # IR LED supply (LEDA), close to the sensor
res("R8", "10k", at(80, 28), "3V3", "PROX_INT")
part("U3", "Sensor_Optical:APDS-9251-001", "APDS-9251-001", "OptoDevice:Broadcom_LGA-8_2x2mm_P0.5mm", "",
     "APDS-9251-001", at(138, 20),
     {"1": None, "2": "3V3", "3": "GND", "4": None, "5": "SCL", "6": "SDA", "7": "RGB_INT", "8": None},
     "Digital RGB + IR light sensor, I2C 0x52: reads the tank's colour")
cap("C7", "100nF", at(124, 14), "3V3", "GND")
res("R9", "10k", at(124, 28), "3V3", "RGB_INT")
part("SW1", "Switch:SW_Push", "PORTHOLE", "Button_Switch_SMD:SW_SPST_PTS810", "", "PTS810 SJM 250 SMTR LFS",
     at(150, 40), {"1": "BTN", "2": "GND"},
     "Tact switch 4.2 x 3.2 x 2.5 mm SMD under the porthole boss: wake, mode, hold = open the control panel")

# --- Outputs: LED power switch, 12 x WS2812B-2020 (bottom-right)
part("Q1", "Transistor_FET:AO3401A", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "C15127", "AO3401A", at(84, 52),
     {"1": "LED_PG", "2": "VBAT", "3": "VLED"}, "P-MOSFET -30 V -4 A SOT-23: high-side switch for the LED chain")
res("R10", "100k", at(74, 46), "VBAT", "LED_PG")              # Q1 off unless Q2 pulls its gate down
part("Q2", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23", "C20917", "AO3400A", at(74, 62),
     {"1": "LED_NG", "2": "GND", "3": "LED_PG"}, "N-MOSFET 30 V 5.7 A SOT-23: drives Q1's gate from the 3.3 V GPIO")
res("R11", "100", at(62, 62), "LED_EN", "LED_NG")
res("R12", "100k", at(66, 70), "LED_NG", "GND")              # LEDs off at boot and in deep sleep
cap("C8", "22uF", at(96, 52), "VLED", "GND")
res("R13", "100", at(60, 84), "LED_IO", "LED_DIN")
for i in range(N_LEDS):
    din = "LED_DIN" if i == 0 else "LED_D%d" % (i + 1)
    dout = None if i == N_LEDS - 1 else "LED_D%d" % (i + 2)
    part("LED%d" % (i + 1), "LED:WS2812B-2020", "WS2812B-2020", LED_FP, "C965555", "WS2812B-2020",
         at(70 + 14 * (i % 6), 74 + 14 * (i // 6)), {"1": dout, "2": "GND", "3": din, "4": "VLED"},
         "RGB LED 2 x 2 mm, one under each of the 12 window squares")
    cap("C%d" % (10 + i), "100nF", at(78 + 14 * (i % 6), 74 + 14 * (i // 6)), "VLED", "GND")

# --- Mechanical: holes on the enclosure posts (H1.. match fit.json holes), fiducials
for i in range(4):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(4 + 4 * i, 108), {}, "Mounting hole M2")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(24 + 4 * i, 108), {}, "Fiducial")

# --- power flags (nets fed only by connectors / passive pins)
for i, (net, xy) in enumerate((("VBAT", at(4, 32)), ("GND", at(8, 32)), ("VLED", at(12, 32))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)

NOTES += [
    (at(4, 3), "POWER: 2 x LiPo pouch (~4 x 20 x 80 mm, ~600 mAh each, own protection PCBs) in parallel on J1 / J2 -> VBAT.\n"
               "VBAT goes to the XIAO's underside BAT+ pad: the XIAO charges the cells from its USB-C and makes 3V3.\n"
               "VBAT_SENSE = VBAT / 2 (R1/R2) -> D0. VBUS_SENSE = 5V pin x 0.6 (R3/R4) -> D1: USB present (the 5V pin floats on battery)."),
    (at(4, 40), "MCU: XIAO ESP32C6, castellations + BAT pads reflowed flat (no sockets: the bar is ~11 mm thick).\n"
                "D0 VBAT_SENSE, D1 VBUS_SENSE, D2 BTN (LP GPIOs: ADC / deep-sleep wake), D3 LED data, D4/D5 I2C, D6 LED_EN\n"
                "(the XIAO sits on the bottom face, so this row faces the LEDs), D7 RGB_INT, D8 PROX_INT. D9/D10 spare. USB-C at the bar's side edge; antenna end copper-free."),
    (at(80, 3), "SENSORS (I2C, 4.7k pull-ups R5/R6): APDS-9960 0x39 under the dome: IR reflectance proximity for fish near the surface,\n"
                "plus ambient light for 'tank is dim -> lights on'. IR LED (LEDA) on VBAT, LDR tied to LEDK.\n"
                "APDS-9251 0x52 under the chrome oval: RGB + IR, reads the tank's colour while the LEDs flash white."),
    (at(80, 36), "LEDS: Q1 AO3401A high-side switch (R10 holds it off), driven by Q2 from LED_EN (R12 keeps it off at boot).\n"
                 "VLED = VBAT 3.0-4.2 V: 3.3 V data meets the WS2812's 0.7 x VDD. Firmware stops the lights below VBAT 3.5 V.\n"
                 "12 x WS2812B-2020, one per window square, 100 nF each. Keep LED data low while VLED is off."),
]

OFF_BOARD += [
    ("BT1", "LiPo ~600 mAh", "LiPo pouch 3.7 V ~600 mAh, ~4 x 20 x 80 mm, with protection PCB, leads soldered to J1",
     "off-board", "generic 402080"),
    ("BT2", "LiPo ~600 mAh", "Second, matching cell in parallel, leads soldered to J2 (charge both to the same voltage before joining)",
     "off-board", "generic 402080"),
]
