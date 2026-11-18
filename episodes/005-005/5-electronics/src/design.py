"""Smart Bucket Hat (episode 005): the parts and nets for tools/kicad.

A XIAO carrier (Rev A) in the hat's electronics pod at the back of the crown. The XIAO nRF52840 Sense
brings the nRF52840 (BLE: phone app + friend-finder beacon), USB-C, a 3.3 V LDO, a slow LiPo charger,
the battery ADC, a PDM mic ("reacts to music") and an IMU. The carrier adds what the hat needs on top:
a 500 mA charger so the pack fills in an afternoon, a high-side switch for each half of the LED band
(WS2812s draw current even when dark), a 3.3 V -> VLED data buffer per half, two JST-PH plugs so the
pod unplugs from the band for washing, the cells' pads and one button.
"""
from schkit import *  # noqa: F401,F403
from parts import XIAO_NRF_FP, xiao_nrf52840

setup("bucket-hat", lib="bucket", title="Smart Bucket Hat", company="Product Speedrun 005",
      date="2026-11-18",
      comments=["XIAO nRF52840 Sense carrier: 2 x WS2812 band halves on switched VBAT, 500 mA charger, button"],
      ns="5b7d1e40-8c2a-4f63-9e15-2a6c0d8b0005")

XIAO = xiao_nrf52840(sense=True)
WIRE2 = "Connector_Wire:SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm"
PH3 = "Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SOT235 = "Package_TO_SOT_SMD:SOT-23-5"

# --- Power: the cells, the 500 mA charger (top-left)
for i, ref in enumerate(("J1", "J2")):
    part(ref, "Connector_Generic:Conn_01x02", "LiPo %s" % "AB"[i], WIRE2, "", "", at(6 + 8 * i, 20),
         {"1": "VBAT", "2": "GND"},
         "Solder pads for a LiPo pouch's leads (+ = pin 1), the cell has its own protection PCB", dnp=True)
cap("C1", "47uF", at(24, 22), "VBAT", "GND")
part("U2", "Battery_Management:MCP73831-2-OT", "MCP73831T-2ACI/OT", SOT235, "C424093", "MCP73831T-2ACI/OT",
     at(44, 18), {"4": "VBUS", "3": "VBAT", "1": "CHG_STAT", "5": "PROG", "2": "GND"},
     "Li-ion/LiPo linear charger 4.2 V, 500 mA (R1 2k), SOT-23-5: fills the pack ~5x faster than the XIAO's own")
cap("C2", "4.7uF", at(34, 24), "VBUS", "GND")
cap("C3", "4.7uF", at(56, 24), "VBAT", "GND")
res("R1", "2k", at(44, 30), "PROG", "GND")                    # 1000 V / 2k = 500 mA
res("R2", "10k", at(56, 12), "3V3", "CHG_STAT")              # STAT is open drain: low while charging

# --- MCU: XIAO nRF52840 Sense, soldered flat (bottom-left)
part("U1", XIAO, "XIAO nRF52840 Sense", XIAO_NRF_FP, "", "102010448", at(24, 72),
     {"1": None, "2": "BTN", "3": "LED_EN", "4": "LED_IO_B", "5": None, "6": None, "7": None,
      "8": None, "9": "LED_IO_A", "10": "CHG_STAT", "11": None,
      "12": "3V3", "13": "GND", "14": "VBUS", "15": "VBAT", "16": "GND"},
     "Seeed XIAO nRF52840 Sense (BLE 5, USB-C, LiPo charger, 3.3 V LDO, PDM mic, IMU), castellations + BAT pads reflowed to the carrier")
part("SW1", "Switch:SW_Push", "MODE", "Button_Switch_SMD:SW_SPST_PTS810", "", "PTS810 SJM 250 SMTR LFS",
     at(52, 66), {"1": "BTN", "2": "GND"},
     "Tact switch 4.2 x 3.2 x 2.5 mm SMD, pressed through the pod's inner face: wake, next show, hold = beacon / off")

# --- LED band power: one P-FET per half, gates driven together (top-right)
part("Q1", "Transistor_FET:AO3401A", "AO3401A", SOT23, "C15127", "AO3401A", at(84, 18),
     {"1": "LED_PG", "2": "VBAT", "3": "VLED_A"}, "P-MOSFET -30 V -4 A SOT-23: high-side switch, band half A")
part("Q2", "Transistor_FET:AO3401A", "AO3401A", SOT23, "C15127", "AO3401A", at(84, 34),
     {"1": "LED_PG", "2": "VBAT", "3": "VLED_B"}, "P-MOSFET -30 V -4 A SOT-23: high-side switch, band half B")
res("R3", "100k", at(74, 14), "VBAT", "LED_PG")              # both P-FETs off unless Q3 pulls the gates down
part("Q3", "Transistor_FET:AO3400A", "AO3400A", SOT23, "C20917", "AO3400A", at(74, 30),
     {"1": "LED_NG", "2": "GND", "3": "LED_PG"}, "N-MOSFET 30 V 5.7 A SOT-23: drives Q1/Q2's gates from the 3.3 V GPIO")
res("R4", "100", at(64, 30), "LED_EN", "LED_NG")
res("R5", "100k", at(66, 38), "LED_NG", "GND")              # band off at boot and in System OFF
for i, (ref_a, ref_b) in enumerate((("C4", "C5"), ("C6", "C7"))):
    rail = "VLED_%s" % "AB"[i]
    cap(ref_a, "47uF", at(96, 16 + 16 * i), rail, "GND")
    cap(ref_b, "47uF", at(102, 16 + 16 * i), rail, "GND")

# --- LED band data: 3.3 V -> VLED buffer, series resistor, JST-PH plug per half (bottom-right)
for i, half in enumerate("AB"):
    y = 62 + 20 * i
    u, c, r, j = ("U3", "C8", "R6", "J3") if half == "A" else ("U4", "C9", "R7", "J4")
    part(u, "74xGxx:74LVC1G34", "SN74LV1T34DBVR", SOT235, "C100024", "SN74LV1T34DBVR", at(76, y),
         {"1": None, "2": "LED_IO_%s" % half, "3": "GND", "4": "LED_Y_%s" % half, "5": "VLED_%s" % half},
         "Single buffer with 3.3 V-compatible inputs, powered from VLED: full-swing data for band half %s" % half)
    cap(c, "100nF", at(64, y - 10), "VLED_%s" % half, "GND")
    res(r, "100", at(88, y), "LED_Y_%s" % half, "LED_DIN_%s" % half)
    part(j, "Connector_Generic_MountingPin:Conn_01x03_MountingPin", "BAND %s" % half, PH3, "",
         "S3B-PH-SM4-TB(LF)(SN)", at(100, y),
         {"1": "VLED_%s" % half, "2": "LED_DIN_%s" % half, "3": "GND", "MP": "GND"},
         "JST PH 3-pin SMD side entry: LED band half %s (VLED, DIN, GND); the pod unplugs for washing" % half)

# --- Mechanical: M2 holes on the pod's posts (H1.. match fit.json holes), fiducials
for i in range(2):
    part("H%d" % (i + 1), "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", "", "",
         at(4 + 4 * i, 108), {}, "Mounting hole M2")
for i in range(3):
    part("FID%d" % (i + 1), "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", "", "",
         at(16 + 4 * i, 108), {}, "Fiducial")

# --- power flags (nets fed only by connectors / passive pins)
# (VBAT needs none: U2's VBAT pin is a power output)
for i, (net, xy) in enumerate((("GND", at(8, 32)), ("VLED_A", at(12, 32)), ("VLED_B", at(16, 32))), 1):
    part("#FLG%02d" % i, "power:PWR_FLAG", "PWR_FLAG", "", "", "", xy, {"1": net}, power=True)

NOTES += [
    (at(4, 3), "POWER: 2 x LiPo pouch (~1200 mAh each, own protection PCBs) in parallel on J1 / J2 -> VBAT.\n"
               "VBAT goes to the XIAO's underside BAT+ pad (XIAO makes 3V3, reads VBAT on P0.31, charges at 50 mA).\n"
               "U2 MCP73831 adds 500 mA from the XIAO's 5V pin (USB VBUS; floats on battery). CHG_STAT -> D9 (low = charging)."),
    (at(4, 40), "MCU: XIAO nRF52840 Sense, castellations + BAT pads reflowed flat (the pod is thin; no sockets).\n"
                "D8 / D3 LED data A / B (left / right pin row, toward each half's buffer), D2 LED_EN, D1 BTN (any pin wakes\n"
                "System OFF; internal pull-up), D9 CHG_STAT. D0, D4-D7, D10 spare (D4/D5 = I2C). On the XIAO: PDM mic (music), IMU (tap / nod), USB-C at the pod's lower edge."),
    (at(64, 3), "LED BAND: 12 x 208 px at 2.8 mm (2,496 addressable LEDs), two flex halves of 12 x 104, one per side,\n"
                "both starting at the back seam. Q1 / Q2 AO3401A switch VBAT to each half (R3 holds them off),\n"
                "Q3 drives the gates from LED_EN (R5 keeps it off at boot). VLED = VBAT 3.0-4.2 V.\n"
                "Firmware caps the band at 2.4 A total (1.2 A per plug; ~0.6 A of each is the LEDs' idle) and stops below VBAT 3.5 V."),
    (at(64, 50), "DATA: U3 / U4 SN74LV1T34 on VLED take the 3.3 V GPIO (VIH 2.0 V) to a full VLED swing, 100R series.\n"
                 "Keep LED data low before LED_EN goes low (the buffers' Ioff inputs tolerate it either way)."),
]

OFF_BOARD += [
    ("BT1", "LiPo ~1200 mAh", "LiPo pouch 3.7 V ~1200 mAh, ~6 x 34 x 50 mm (603450), with protection PCB, leads soldered to J1",
     "off-board", "generic 603450"),
    ("BT2", "LiPo ~1200 mAh", "Second, matching cell in parallel, leads soldered to J2 (charge both to the same voltage before joining)",
     "off-board", "generic 603450"),
    ("LB1", "LED band half A", "Flex matrix 12 x 104 addressable RGB LEDs (1515 / 1010 size, 2.8 mm pitch, ~34 x 292 mm), JST PH 3-pin lead (VLED, DIN, GND)",
     "off-board", "custom flex"),
    ("LB2", "LED band half B", "Second band half, mirrored, same JST PH 3-pin lead", "off-board", "custom flex"),
]
