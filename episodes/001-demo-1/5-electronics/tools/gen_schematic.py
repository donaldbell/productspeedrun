#!/usr/bin/env python3
"""Generate the Backpack Defender KiCad project: custom symbols and the schematic.

  python3 -I tools/gen_schematic.py        (from 5-electronics/, or anywhere)

Adapted from the bollard ring v2 generator. Every component pin gets a short wire stub and a
net label, so the netlist is defined entirely by the part() calls below (one place to review).
Re-running overwrites the generated files; once the schematic is edited by hand, stop using it.
"""

import copy
import json
import math
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import Q, dump, find, find_all, load_symbol, pins  # noqa: E402

HW = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBDIR = os.path.join(HW, "lib")
LIB = "backpack"
KICAD = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
PROJECT = "backpack-defender"
NS = uuid.UUID("6a3f1c2e-0b7d-4e19-9a51-bacc9ac0de01")


def uid(*parts):
    return Q(str(uuid.uuid5(NS, "/".join(str(p) for p in parts))))


def font(size=1.27):
    return ["font", ["size", size, size]]


# ---------------------------------------------------------------- symbols ---

def pin_sx(typ, x, y, ang, name, num, length=2.54):
    return ["pin", typ, "line", ["at", x, y, ang], ["length", length],
            ["name", Q(name), ["effects", font()]],
            ["number", Q(num), ["effects", font()]]]


def prop(key, val, x=0, y=0, hide=False, ang=0):
    eff = ["effects", font()]
    if hide:
        eff.append(["hide", "yes"])
    return ["property", Q(key), Q(val), ["at", x, y, ang], eff]


SYMBOX = {}   # lib_id -> (top, bottom) of the body, for placing Reference / Value


def box_symbol(name, ref, value, fp, ds, desc, box, pin_list):
    x0, y0, x1, y1 = box
    SYMBOX[LIB + ":" + name] = (y0, y1)
    return ["symbol", Q(name), ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
            prop("Reference", ref, 0, y0 + 2.54), prop("Value", value, 0, y1 - 2.54),
            prop("Footprint", fp, hide=True), prop("Datasheet", ds, hide=True),
            prop("Description", desc, hide=True),
            ["symbol", Q(name + "_0_1"),
             ["rectangle", ["start", x0, y0], ["end", x1, y1],
              ["stroke", ["width", 0.254], ["type", "default"]], ["fill", ["type", "background"]]]],
            ["symbol", Q(name + "_1_1")] + [pin_sx(*p) for p in pin_list],
            ["embedded_fonts", "no"]]


TPS61023 = box_symbol(
    "TPS61023", "U", "TPS61023DRLR", "Package_TO_SOT_SMD:SOT-563",
    "https://www.ti.com/lit/ds/symlink/tps61023.pdf",
    "3.7 A switch, 0.5-5.5 V in, synchronous boost; VREF 0.595 V (pinout as bollard v2, proven)",
    (-7.62, 6.35, 7.62, -6.35),
    [("power_in", -10.16, 2.54, 0, "VIN", "3"), ("input", -10.16, -2.54, 0, "EN", "2"),
     ("passive", 10.16, 3.81, 180, "SW", "5"), ("power_out", 10.16, 0, 180, "VOUT", "6"),
     ("input", 10.16, -3.81, 180, "FB", "1"), ("power_in", 0, -8.89, 90, "GND", "4")])

MAX98357A = box_symbol(
    "MAX98357A", "U", "MAX98357AETE+T", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm_ThermalVias",
    "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf",
    "I2S input class-D mono amplifier, 2.5-5.5 V, filterless; GAIN open = 9 dB; SD_MODE high = left channel",
    (-7.62, 10.16, 7.62, -10.16),
    [("input", -10.16, 7.62, 0, "BCLK", "16"), ("input", -10.16, 5.08, 0, "LRCLK", "14"),
     ("input", -10.16, 2.54, 0, "DIN", "1"), ("input", -10.16, -2.54, 0, "~{SD_MODE}", "4"),
     ("input", -10.16, -5.08, 0, "GAIN_SLOT", "2"),
     ("power_in", 10.16, 7.62, 180, "VDD", "7"), ("power_in", 10.16, 5.08, 180, "VDD", "8"),
     ("output", 10.16, 0, 180, "OUTP", "9"), ("output", 10.16, -2.54, 180, "OUTN", "10"),
     ("no_connect", 10.16, -5.08, 180, "NC", "5"), ("no_connect", 10.16, -7.62, 180, "NC", "6"),
     ("no_connect", 7.62, -12.7, 90, "NC", "12"), ("no_connect", 5.08, -12.7, 90, "NC", "13"),
     ("power_in", -5.08, -12.7, 90, "GND", "3"), ("power_in", -2.54, -12.7, 90, "GND", "11"),
     ("power_in", 0, -12.7, 90, "GND", "15"), ("power_in", 2.54, -12.7, 90, "EP", "17")])

AM312 = box_symbol(
    "AM312", "U", "AM312", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
    "https://www.lcsc.com/search?q=AM312",
    "Mini PIR motion sensor module, 2.7-12 V, ~15 uA, digital output (high ~2 s on motion). "
    "Pin order VCC/OUT/GND and 2.54 mm pitch: verify against the supplier's drawing",
    (-5.08, 3.81, 5.08, -3.81),
    [("power_in", -7.62, 2.54, 0, "VCC", "1"), ("output", 7.62, 0, 180, "OUT", "2"),
     ("power_in", -7.62, -2.54, 0, "GND", "3")])


def write_symbol_lib():
    lib = ["kicad_symbol_lib", ["version", 20251024], ["generator", Q("backpack_gen")],
           ["generator_version", Q("10.0")], TPS61023, MAX98357A, AM312]
    with open(os.path.join(LIBDIR, LIB + ".kicad_sym"), "w") as f:
        f.write(dump(lib) + "\n")


# ------------------------------------------------------- symbol sources ---

def stock(lib, name):
    """A stock symbol, with `extends` resolved (e.g. AO3401A extends TP0610T)."""
    path = os.path.join(KICAD, "symbols", lib + ".kicad_sym")
    sym = load_symbol(path, name)
    ext = find(sym, "extends")
    if ext is None:
        return sym
    parent = copy.deepcopy(load_symbol(path, str(ext[1])))
    pname = str(ext[1])
    out = [parent[0], Q(name)]
    child_props = {str(p[1]): p for p in find_all(sym, "property")}
    for item in parent[2:]:
        if isinstance(item, list) and item and item[0] == "property" and str(item[1]) in child_props:
            out.append(child_props.pop(str(item[1])))
        elif isinstance(item, list) and item and item[0] == "symbol":
            sub = list(item)
            sub[1] = Q(str(item[1]).replace(pname, name, 1))
            out.append(sub)
        else:
            out.append(item)
    out[2:2] = list(child_props.values())
    return out


LIBSYMS = {
    "Device:R": lambda: stock("Device", "R"),
    "Device:C": lambda: stock("Device", "C"),
    "Device:L": lambda: stock("Device", "L"),
    "Device:Buzzer": lambda: stock("Device", "Buzzer"),
    "Transistor_FET:AO3401A": lambda: stock("Transistor_FET", "AO3401A"),
    "RF_Module:ESP32-C3-WROOM-02": lambda: stock("RF_Module", "ESP32-C3-WROOM-02"),
    "Switch:SW_Push": lambda: stock("Switch", "SW_Push"),
    "Connector_Generic:Conn_01x02": lambda: stock("Connector_Generic", "Conn_01x02"),
    "Connector_Generic:Conn_01x06": lambda: stock("Connector_Generic", "Conn_01x06"),
    "Connector:TestPoint": lambda: stock("Connector", "TestPoint"),
    "Mechanical:MountingHole": lambda: stock("Mechanical", "MountingHole"),
    "Mechanical:Fiducial": lambda: stock("Mechanical", "Fiducial"),
    "power:PWR_FLAG": lambda: stock("power", "PWR_FLAG"),
    LIB + ":TPS61023": lambda: TPS61023,
    LIB + ":MAX98357A": lambda: MAX98357A,
    LIB + ":AM312": lambda: AM312,
}


# ------------------------------------------------------------- the design ---

FP_0603C = "Capacitor_SMD:C_0603_1608Metric"
FP_0805C = "Capacitor_SMD:C_0805_2012Metric"
FP_0603R = "Resistor_SMD:R_0603_1608Metric"

PARTS = {}


def part(ref, lib_id, value, fp, lcsc, mpn, at, nets, desc="", **extra):
    assert ref not in PARTS, ref
    PARTS[ref] = dict(lib_id=lib_id, value=value, fp=fp, lcsc=lcsc, mpn=mpn, at=at, nets=nets, desc=desc, **extra)


def cap(ref, value, at, a, b):
    lcsc, mpn, fp, desc = {
        "100nF": ("C14663", "CC0603KRX7R9BB104", FP_0603C, "Capacitor, ceramic, 100 nF 50 V X7R 0603"),
        "1uF": ("C15849", "CL10A105KB8NNNC", FP_0603C, "Capacitor, ceramic, 1 uF 50 V X5R 0603"),
        "10uF": ("C15850", "CL21A106KAYNNNE", FP_0805C, "Capacitor, ceramic, 10 uF 25 V X5R 0805"),
        "22uF": ("C45783", "CL21A226MAQNNNE", FP_0805C, "Capacitor, ceramic, 22 uF 25 V X5R 0805"),
    }[value]
    part(ref, "Device:C", value, fp, lcsc, mpn, at, {"1": a, "2": b}, desc)


RES = {"100": ("C22775", "0603WAF1000T5E"), "10k": ("C25804", "0603WAF1002T5E"),
       "100k": ("C25803", "0603WAF1003T5E"), "220k": ("", "0603WAF2203T5E"), "1M": ("C22935", "0603WAF1004T5E")}


def res(ref, value, at, a, b):
    lcsc, mpn = RES[value]
    part(ref, "Device:R", value, FP_0603R, lcsc, mpn, at, {"1": a, "2": b}, "Resistor, 1 %%, 0603, %s" % value)


def gnd_pins(*nums):
    return {n: "GND" for n in nums}


G = 2.54
def at(col, row):
    """Schematic grid helper: (col, row) in 2.54 mm units."""
    return (round(col * G, 2), round(row * G, 2))


# --- Battery in, reverse-polarity guard, 3.3 V boost, battery sense (top-left)
part("J1", "Connector_Generic:Conn_01x02", "2xAAA leads", "Connector_Wire:SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm",
     "", "", at(10, 20), {"1": "BAT_IN", "2": "GND"}, "Solder pads for the 2 x AAA holder's wire leads (+ = pin 1)", dnp=True)
part("Q1", "Transistor_FET:AO3401A", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "C15127", "AO3401A", at(22, 19),
     {"1": "GND", "2": "VBAT", "3": "BAT_IN"}, "P-MOSFET -30 V -4 A SOT-23: reverse-battery guard, drain to the cells, gate to GND")
cap("C1", "10uF", at(30, 25), "VBAT", "GND")
part("L1", "Device:L", "1uH", "Inductor_SMD:L_Changjiang_FXL0624", "C524602", "FXL0624-1R0-M", at(38, 16),
     {"1": "VBAT", "2": "BOOST_SW"}, "Inductor, power, 1 uH, 9 A sat, 7 x 6.6 mm")
part("U1", LIB + ":TPS61023", "TPS61023DRLR", "Package_TO_SOT_SMD:SOT-563", "C919459", "TPS61023DRLR", at(44, 22),
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
part("U4", LIB + ":AM312", "AM312", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical", "", "AM312",
     at(102, 20), {"1": "PIR_VCC", "2": "PIR_OUT", "3": "GND"}, "Mini PIR motion sensor, Fresnel dome through the lid")
res("R10", "100", at(88, 16), "3V3", "PIR_VCC")         # RC filter: PIRs false-trigger on supply ripple
cap("C8", "10uF", at(92, 23), "PIR_VCC", "GND")

# --- I2S amp and piezo (bottom-right)
part("U3", LIB + ":MAX98357A", "MAX98357AETE+T", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm_ThermalVias",
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


NOTES = [
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


# ------------------------------------------------------------- emit sch ---

ROOT_UUID = uid("root")


def pin_geometry(lib_id):
    return {p[0]: p for p in pins(LIBSYMS[lib_id]())}


def label_node(net, x, y, ang, key):
    just = {0: ["justify", "left", "bottom"], 180: ["justify", "right", "bottom"],
            90: ["justify", "left", "bottom"], 270: ["justify", "right", "bottom"]}[ang]
    return ["label", Q(net), ["at", x, y, ang], ["effects", font(), just], ["uuid", uid("label", key)]]


def symbol_instance(ref, p, items):
    x, y = p["at"]
    lib_id = p["lib_id"]
    geo = pin_geometry(lib_id)
    is_power = p.get("power", False)
    dnp = p.get("dnp", False)
    mech = lib_id.startswith("Mechanical:")
    in_bom = not (dnp or is_power or mech)
    if lib_id in SYMBOX:
        top, bottom = SYMBOX[lib_id]
        ref_at, val_at, just = (x, y - top - 1.27), (x, y - bottom + 1.27), []
    else:
        ref_at, val_at, just = (x + 2.54, y - 1.27), (x + 2.54, y + 1.27), [["justify", "left"]]

    def vprop(key, val, at_, hide=False):
        eff = ["effects", font()] + (just if not hide else [])
        if hide:
            eff.append(["hide", "yes"])
        return ["property", Q(key), Q(val), ["at", at_[0], at_[1], 0], eff]

    sym = ["symbol", ["lib_id", Q(lib_id)], ["at", x, y, 0], ["unit", 1],
           ["exclude_from_sim", "no"], ["in_bom", "yes" if in_bom else "no"], ["on_board", "no" if is_power else "yes"],
           ["dnp", "yes" if dnp else "no"], ["uuid", uid("sym", ref)],
           vprop("Reference", ref, ref_at, hide=is_power),
           vprop("Value", p["value"], val_at, hide=is_power),
           vprop("Footprint", p["fp"], (x, y), hide=True),
           vprop("Datasheet", "~", (x, y), hide=True)]
    if p["desc"]:
        sym.append(vprop("Description", p["desc"], (x, y), hide=True))
    if p["lcsc"]:
        sym.append(vprop("LCSC", p["lcsc"], (x, y), hide=True))
    if p["mpn"]:
        sym.append(vprop("MPN", p["mpn"], (x, y), hide=True))
    for num in sorted(geo, key=lambda s: (len(s), s)):
        sym.append(["pin", Q(num), ["uuid", uid("pin", ref, num)]])
    sym.append(["instances", ["project", Q(PROJECT),
                              ["path", Q("/" + ROOT_UUID), ["reference", Q(ref)], ["unit", 1]]]])
    items.append(sym)

    assert set(p["nets"]) <= set(geo), (ref, set(p["nets"]) - set(geo))
    missing = set(geo) - set(p["nets"])
    assert not missing, "%s pins not assigned: %s" % (ref, missing)
    for num, net in p["nets"].items():
        _, _, _, px, py, ang = geo[num]
        cx, cy = round(x + px, 4), round(y - py, 4)
        if net is None:
            items.append(["no_connect", ["at", cx, cy], ["uuid", uid("nc", ref, num)]])
            continue
        ox = -round(math.cos(math.radians(ang)))
        oy = round(math.sin(math.radians(ang)))
        ex, ey = round(cx + 2.54 * ox, 4), round(cy + 2.54 * oy, 4)
        items.append(["wire", ["pts", ["xy", cx, cy], ["xy", ex, ey]],
                      ["stroke", ["width", 0], ["type", "default"]], ["uuid", uid("wire", ref, num)]])
        lang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[(ox, oy)]
        items.append(label_node(net, ex, ey, lang, "%s.%s" % (ref, num)))


def check_label_collisions():
    """Two different nets' labels or pins at the same point would silently merge them: refuse."""
    seen = {}
    for ref, p in PARTS.items():
        geo = pin_geometry(p["lib_id"])
        x, y = p["at"]
        for num, net in p["nets"].items():
            _, _, _, px, py, ang = geo[num]
            cx, cy = round(x + px, 3), round(y - py, 3)
            ex = round(cx - 2.54 * round(math.cos(math.radians(ang))), 3)
            ey = round(cy + 2.54 * round(math.sin(math.radians(ang))), 3)
            for pt in ((cx, cy), (ex, ey)):
                other = seen.get(pt)
                if other and other[0] != net:
                    raise SystemExit("label/pin collision at %s: %s.%s (%s) vs %s" % (pt, ref, num, net, other))
                seen[pt] = (net, "%s.%s" % (ref, num))


def write_schematic():
    lib_symbols = ["lib_symbols"]
    for lib_id in sorted({p["lib_id"] for p in PARTS.values()}):
        s = list(LIBSYMS[lib_id]())
        s[1] = Q(lib_id)
        lib_symbols.append(s)

    items = []
    for ref, p in PARTS.items():
        symbol_instance(ref, p, items)
    for i, ((x, y), text) in enumerate(NOTES):
        items.append(["text", Q(text), ["exclude_from_sim", "no"], ["at", x, y, 0],
                      ["effects", font(), ["justify", "left", "top"]], ["uuid", uid("note", i)]])

    sch = ["kicad_sch", ["version", 20250114], ["generator", Q("eeschema")], ["generator_version", Q("9.0")],
           ["uuid", ROOT_UUID], ["paper", Q("A3")],
           ["title_block", ["title", Q("Backpack Defender")], ["date", Q("2026-10-28")], ["rev", Q("A (first pass)")],
            ["company", Q("Product Speedrun 001")],
            ["comment", 1, Q("Generated by 5-electronics/tools/gen_schematic.py")],
            ["comment", 2, Q("ESP32-C3 + 2xAAA boost + MAX98357A + piezo + AM312 PIR")]],
           lib_symbols] + items + [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]],
                                   ["embedded_fonts", "no"]]
    with open(os.path.join(HW, PROJECT + ".kicad_sch"), "w") as f:
        f.write(dump(sch) + "\n")


def write_project_files():
    pro_path = os.path.join(HW, PROJECT + ".kicad_pro")
    if not os.path.exists(pro_path):
        with open(pro_path, "w") as f:
            json.dump({"meta": {"filename": PROJECT + ".kicad_pro", "version": 3},
                       "sheets": [[str(ROOT_UUID), "Root"]]}, f, indent=2)
            f.write("\n")
    with open(os.path.join(HW, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") '
                '(uri "${KIPRJMOD}/lib/%s.kicad_sym") (options "") (descr "Backpack Defender parts"))\n)\n' % (LIB, LIB))


def main():
    os.makedirs(LIBDIR, exist_ok=True)
    write_symbol_lib()
    write_project_files()
    check_label_collisions()
    write_schematic()
    nets = {}
    for ref, p in PARTS.items():
        for num, net in p["nets"].items():
            if net:
                nets.setdefault(net, []).append("%s.%s" % (ref, num))
    for net in sorted(nets):
        if len(nets[net]) < 2:
            print("WARNING single-pin net", net, nets[net])
    print("wrote %d symbols, %d nets" % (len(PARTS), len(nets)))


if __name__ == "__main__":
    main()
