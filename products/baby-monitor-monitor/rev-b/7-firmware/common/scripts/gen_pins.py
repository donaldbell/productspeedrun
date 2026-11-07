#!/usr/bin/env python3
"""Generate <project>/include/pins.h from that board's design.py, so the firmware and the board can't disagree.

Runs ../5-electronics/<board>/src/design.py against a stub of tools/kicad's schkit (no KiCad needed), finds the
ESP32-C6-MINI-1, maps its pads to GPIO numbers and writes one PIN_<NET> per signal net. It also writes what the
board does to each pin (pull-ups / pull-downs, what else is on the net, strapping / LP-GPIO notes) and the
battery-sense divider ratio, so the firmware can check its assumptions with #if / _Static_assert.

The pad -> GPIO table is the ESP32-C6-MINI-1 datasheet's. When KiCad is installed, the script also reads the
module's symbol from KiCad's RF_Module library and stops if the two disagree.

Usage: python3 common/scripts/gen_pins.py <board> [--check]      board = sensor | receiver
       (run before every build by common/scripts/pio_pre.py, with the PlatformIO project's folder name as <board>)
"""
import glob
import os
import re
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.normpath(os.path.join(HERE, "..", ".."))          # 7-firmware/
REV = os.path.dirname(FW)                                       # the revision folder

MODULE = "RF_Module:ESP32-C6-MINI-1"
# ESP32-C6-MINI-1 pad -> GPIO (datasheet "Pin Definitions"; same as KiCad's symbol). Power / NC pads left out.
C6_MINI_GPIO = {"5": 2, "6": 3, "9": 4, "10": 5, "12": 0, "13": 1, "15": 6, "16": 7, "17": 12, "18": 13,
                "19": 14, "20": 15, "22": 8, "23": 9, "24": 18, "25": 19, "26": 20, "27": 21, "28": 22,
                "29": 23, "30": 17, "31": 16}
POWER_NETS = {"3V3", "GND", "EN"}
STRAPS = {4, 5, 8, 9, 15}             # ESP32-C6 strapping pins (MTMS, MTDI, GPIO8, GPIO9, GPIO15)
LP_GPIO = set(range(0, 8))            # LP GPIO0-7: the only pins that can wake the C6 from deep sleep
ADC1 = set(range(0, 7))               # ADC1 channels 0-6 = GPIO0-6
USB_PINS = {12: "USB D-", 13: "USB D+"}
KICAD_SYM_GLOBS = ["/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/RF_Module.kicad_sym",
                   "/usr/share/kicad/symbols/RF_Module.kicad_sym",
                   os.path.join(os.environ.get("KICAD_SYMBOL_DIR", "/nonexistent"), "RF_Module.kicad_sym"),
                   "C:/Program Files/KiCad/*/share/kicad/symbols/RF_Module.kicad_sym"]


def check_against_kicad():
    """If KiCad's library is here, compare our pad table with its ESP32-C6-MINI-1 symbol. Returns a note."""
    paths = [p for g in KICAD_SYM_GLOBS for p in glob.glob(g)]
    if not paths:
        return "KiCad library not found: pad table not cross-checked"
    text = open(paths[0], encoding="utf-8").read()
    i = text.find('(symbol "ESP32-C6-MINI-1"')
    if i < 0:
        return "ESP32-C6-MINI-1 not in KiCad's RF_Module library: pad table not cross-checked"
    j = text.find('\n\t(symbol "', i + 10)
    sym = text[i:j if j > 0 else None]
    pads = {m.group(2): m.group(1) for m in
            re.finditer(r'\(pin \w+ \w+.*?\(name "([^"]*)".*?\(number "([^"]*)"', sym, re.S)}
    named = {"RXD0": 17, "TXD0": 16}
    for pad, gpio in C6_MINI_GPIO.items():
        name = pads.get(pad, "?")
        got = named.get(name, int(name[2:]) if name.startswith("IO") and name[2:].isdigit() else None)
        if got != gpio:
            raise SystemExit("gen_pins: pad %s is %s in KiCad's symbol but GPIO%d in our table" % (pad, name, gpio))
    return "pad table cross-checked against KiCad's ESP32-C6-MINI-1 symbol"


def load_design(path):
    """Execute design.py with stub schkit / parts modules and return (PARTS dict, title)."""
    parts, meta = {}, {}

    def part(ref, lib_id, value, fp, lcsc, mpn, at, nets, desc="", **extra):
        parts[ref] = dict(lib_id=lib_id, value=value, nets=nets, desc=desc, **extra)

    def two_pin(lib_id):
        return lambda ref, value, at, a, b, *x, **k: part(ref, lib_id, value, "", "", "", at, {"1": a, "2": b})

    def setup(name, *a, title="", **k):
        meta.update(name=name, title=title or name)

    schkit = types.ModuleType("schkit")
    names = dict(setup=setup, part=part, cap=two_pin("Device:C"), res=two_pin("Device:R"),
                 at=lambda c, r: (c, r), box_symbol=lambda *a, **k: None, gnd_pins=lambda *n: {x: "GND" for x in n},
                 NOTES=[], OFF_BOARD=[], PARTS=parts, FP_0603C="", FP_0805C="", FP_0603R="", CAPS={}, RES={}, G=2.54)
    schkit.__dict__.update(names)
    schkit.__all__ = list(names)
    stub_parts = types.ModuleType("parts")
    stub_parts.__getattr__ = lambda name: (lambda *a, **k: "stub:" + name)
    saved = {k: sys.modules.get(k) for k in ("schkit", "parts")}
    sys.modules.update(schkit=schkit, parts=stub_parts)
    try:
        with open(path) as f:
            exec(compile(f.read(), path, "exec"), {"__name__": "design", "__file__": path})
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return parts, meta


def ohms(value):
    v = value.strip().upper().replace("Ω", "").replace("R", "")
    mult = {"K": 1e3, "M": 1e6}.get(v[-1:], 1)
    return float(v[:-1] if mult != 1 else v) * mult


def generate(board):
    design = os.path.join(REV, "5-electronics", board, "src", "design.py")
    if not os.path.exists(design):
        raise SystemExit("gen_pins: no design.py for board %r at %s" % (board, design))
    parts, meta = load_design(design)
    mods = [r for r, p in parts.items() if p["lib_id"] == MODULE]
    if len(mods) != 1:
        raise SystemExit("gen_pins: expected one %s in %s, found %r" % (MODULE, design, mods))
    mcu = mods[0]
    kicad_note = check_against_kicad()

    pins = sorted(((net, C6_MINI_GPIO[pad]) for pad, net in parts[mcu]["nets"].items()
                   if net and net not in POWER_NETS and pad in C6_MINI_GPIO), key=lambda t: t[1])

    def on_net(net):
        return [(r, pn, p) for r, p in sorted(parts.items()) if r != mcu for pn, n in p["nets"].items() if n == net]

    rel = os.path.relpath(design, os.path.join(FW, board))
    out = ["// GENERATED by ../common/scripts/gen_pins.py from %s. Do not edit: change the board, then rebuild." % rel,
           "// %s (%s, %s)." % (kicad_note, mcu, MODULE),
           "// Every PIN_* can be overridden with a build flag (the devkit envs in platformio.ini do).",
           "#pragma once", "",
           "#define BOARD_NAME \"%s\"" % meta.get("title", board),
           "#define BOARD_KEY \"%s\"" % board, ""]
    for net, gpio in pins:
        pull_up = pull_dn = None
        others = []
        for ref, pn, p in on_net(net):
            if p["lib_id"] == "Device:R":
                other = [n for k, n in p["nets"].items() if k != pn][0]
                if other == "3V3":
                    pull_up = (ref, p["value"])
                    continue
                if other == "GND":
                    pull_dn = (ref, p["value"])
                    continue
            others.append("%s.%s" % (ref, pn))
        notes = []
        if pull_up:
            notes.append("pull-up %s %s" % pull_up)
        if pull_dn:
            notes.append("pull-down %s %s" % pull_dn)
        if others:
            notes.append("to " + ", ".join(others))
        if gpio in STRAPS:
            notes.append("strapping pin")
        if gpio in LP_GPIO:
            notes.append("LP GPIO (can wake from deep sleep)")
        if gpio in ADC1:
            notes.append("ADC1 ch%d" % gpio)
        if gpio in USB_PINS:
            notes.append("native " + USB_PINS[gpio])
        name = "PIN_" + re.sub(r"\W", "_", net)
        out += ["// %s: %s" % (net, "; ".join(notes) or "no other connections"),
                "#ifndef %s" % name, "#define %s %d" % (name, gpio), "#endif",
                "#define %s_PULLUP %d" % (name, 1 if pull_up else 0),
                "#define %s_PULLDOWN %d" % (name, 1 if pull_dn else 0), ""]

    top = [p for p in parts.values() if p["lib_id"] == "Device:R" and set(p["nets"].values()) == {"VBAT", "VBAT_SENSE"}]
    bot = [p for p in parts.values() if p["lib_id"] == "Device:R" and set(p["nets"].values()) == {"VBAT_SENSE", "GND"}]
    if len(top) == 1 and len(bot) == 1:
        rt, rb = ohms(top[0]["value"]), ohms(bot[0]["value"])
        out += ["// VBAT_SENSE = VBAT x %g / (%g + %g): multiply the pin voltage by this to get VBAT" % (rb, rt, rb),
                "#define VBAT_SENSE_RATIO %.4ff" % ((rt + rb) / rb), ""]
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    board = args[0]
    out_path = os.path.join(FW, board, "include", "pins.h")
    text = generate(board)
    old = open(out_path).read() if os.path.exists(out_path) else None
    if "--check" in sys.argv:
        sys.exit(0 if old == text else "%s/include/pins.h is out of date: run common/scripts/gen_pins.py %s" % (board, board))
    if old != text:            # only touch the file when it changes, so builds stay incremental
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(text)
        print("gen_pins: wrote %s/include/pins.h" % board)


if __name__ == "__main__":
    main()
