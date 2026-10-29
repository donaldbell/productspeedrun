"""Schematic engine for an episode's src/design.py.

A design file calls setup(), defines any custom box symbols, then lists the parts:

    from schkit import *
    setup("plant-whisperer", lib="plant", title="Plant Whisperer", company="Product Speedrun 002")
    part("U1", "RF_Module:ESP32-C3-WROOM-02", "ESP32-C3-WROOM-02-N4", "RF_Module:ESP32-C3-WROOM-02",
         "C2934560", "ESP32-C3-WROOM-02-N4", at(26, 84), {"1": "3V3", "9": "GND", ...}, "desc")
    cap("C1", "10uF", at(30, 25), "3V3", "GND")
    res("R1", "10k", at(6, 70), "3V3", "EN")

Every pin gets a short wire stub and a net label, so the netlist is exactly the part() calls:
one place to review. Every pin must be listed (None = no-connect). Stock symbols ("Lib:Name")
are read from KiCad's own libraries; custom ones from box_symbol() go in src/lib/<lib>.kicad_sym.
Adapted from the bollard ring v2 and Backpack Defender (episode 001) generators.
"""

import copy
import datetime
import json
import math
import os
import uuid

from env import kicad_share
from sexpr import Q, dump, find, find_all, load_symbol, pins

CFG = {}
PARTS = {}
NOTES = []          # [((x, y), text)] free text on the sheet
OFF_BOARD = []      # [(ref, value, description, footprint, mpn)] extra BOM lines (cells, cables, speakers)
CUSTOM = {}         # lib_id -> custom symbol
SYMBOX = {}         # lib_id -> (top, bottom) of a custom body, for placing Reference / Value
_STOCK = {}

__all__ = ["setup", "part", "cap", "res", "at", "box_symbol", "gnd_pins", "NOTES", "OFF_BOARD", "PARTS",
           "FP_0603C", "FP_0805C", "FP_0603R", "CAPS", "RES", "G"]


def setup(project, lib=None, title=None, company="Product Speedrun", rev="A (first pass)", date=None,
          comments=(), paper="A3", ns=None):
    """project: file name stem (lowercase-hyphens). lib: custom symbol library name."""
    CFG.update(project=project, lib=lib or project.split("-")[0], title=title or project.replace("-", " ").title(),
               company=company, rev=rev, date=date or datetime.date.today().isoformat(),
               comments=list(comments), paper=paper,
               ns=uuid.UUID(ns) if isinstance(ns, str) else ns or uuid.uuid5(uuid.NAMESPACE_URL,
                                                                              "productspeedrun/" + project))


def _cfg(key):
    if not CFG:
        raise SystemExit("design.py must call setup(...) first")
    return CFG[key]


def uid(*parts):
    return Q(str(uuid.uuid5(_cfg("ns"), "/".join(str(p) for p in parts))))


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


def box_symbol(name, ref, value, fp, ds, desc, box, pin_list):
    """A rectangle symbol for a part KiCad doesn't ship. Returns its lib_id ("<lib>:<name>").

    box: (x0, y0, x1, y1) body corners. pin_list: (type, x, y, angle, name, number) per pin,
    on a 2.54 grid, pointing into the body (angle 0 = pin on the left, 180 = right,
    90 = bottom, 270 = top). Check the pinout against the datasheet: this is the risky bit.
    """
    lib_id = _cfg("lib") + ":" + name
    x0, y0, x1, y1 = box
    SYMBOX[lib_id] = (y0, y1)
    CUSTOM[lib_id] = ["symbol", Q(name), ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
                      prop("Reference", ref, 0, y0 + 2.54), prop("Value", value, 0, y1 - 2.54),
                      prop("Footprint", fp, hide=True), prop("Datasheet", ds, hide=True),
                      prop("Description", desc, hide=True),
                      ["symbol", Q(name + "_0_1"),
                       ["rectangle", ["start", x0, y0], ["end", x1, y1],
                        ["stroke", ["width", 0.254], ["type", "default"]], ["fill", ["type", "background"]]]],
                      ["symbol", Q(name + "_1_1")] + [pin_sx(*p) for p in pin_list],
                      ["embedded_fonts", "no"]]
    return lib_id


def stock(lib, name):
    """A stock symbol, with `extends` resolved (e.g. AO3401A extends TP0610T)."""
    path = os.path.join(kicad_share(), "symbols", lib + ".kicad_sym")
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


def libsym(lib_id):
    if lib_id in CUSTOM:
        return CUSTOM[lib_id]
    if lib_id not in _STOCK:
        lib, name = lib_id.split(":", 1)
        _STOCK[lib_id] = stock(lib, name)
    return _STOCK[lib_id]


# ------------------------------------------------------------ part helpers ---

FP_0603C = "Capacitor_SMD:C_0603_1608Metric"
FP_0805C = "Capacitor_SMD:C_0805_2012Metric"
FP_0603R = "Resistor_SMD:R_0603_1608Metric"

# JLCPCB basic parts where possible. Add values here as episodes need them.
CAPS = {
    "100nF": ("C14663", "CC0603KRX7R9BB104", FP_0603C, "Capacitor, ceramic, 100 nF 50 V X7R 0603"),
    "1uF": ("C15849", "CL10A105KB8NNNC", FP_0603C, "Capacitor, ceramic, 1 uF 50 V X5R 0603"),
    "4.7uF": ("C19666", "CL10A475KO8NNNC", FP_0603C, "Capacitor, ceramic, 4.7 uF 16 V X5R 0603"),
    "10uF": ("C15850", "CL21A106KAYNNNE", FP_0805C, "Capacitor, ceramic, 10 uF 25 V X5R 0805"),
    "22uF": ("C45783", "CL21A226MAQNNNE", FP_0805C, "Capacitor, ceramic, 22 uF 25 V X5R 0805"),
}
RES = {"0": ("C21189", "0603WAF0000T5E"), "100": ("C22775", "0603WAF1000T5E"), "1k": ("C21190", "0603WAF1001T5E"),
       "3.9k": ("C23018", "0603WAF3901T5E"),
       "4.7k": ("C23162", "0603WAF4701T5E"), "5.1k": ("C23186", "0603WAF5101T5E"),
       "10k": ("C25804", "0603WAF1002T5E"), "100k": ("C25803", "0603WAF1003T5E"),
       "220k": ("", "0603WAF2203T5E"), "1M": ("C22935", "0603WAF1004T5E")}


def part(ref, lib_id, value, fp, lcsc, mpn, at, nets, desc="", **extra):
    """nets: {pin number: net name or None for no-connect}. extra: dnp=True, power=True."""
    assert ref not in PARTS, ref
    PARTS[ref] = dict(lib_id=lib_id, value=value, fp=fp, lcsc=lcsc, mpn=mpn, at=at, nets=nets, desc=desc, **extra)


def cap(ref, value, at, a, b):
    lcsc, mpn, fp, desc = CAPS[value]
    part(ref, "Device:C", value, fp, lcsc, mpn, at, {"1": a, "2": b}, desc)


def res(ref, value, at, a, b):
    lcsc, mpn = RES[value]
    part(ref, "Device:R", value, FP_0603R, lcsc, mpn, at, {"1": a, "2": b}, "Resistor, 1 %%, 0603, %s" % value)


def gnd_pins(*nums):
    return {n: "GND" for n in nums}


G = 2.54


def at(col, row):
    """Schematic grid helper: (col, row) in 2.54 mm units. An A3 sheet is about 160 x 110."""
    return (round(col * G, 2), round(row * G, 2))


# ------------------------------------------------------------- emit sch ---

def pin_geometry(lib_id):
    return {p[0]: p for p in pins(libsym(lib_id))}


def label_node(net, x, y, ang, key):
    just = {0: ["justify", "left", "bottom"], 180: ["justify", "right", "bottom"],
            90: ["justify", "left", "bottom"], 270: ["justify", "right", "bottom"]}[ang]
    return ["label", Q(net), ["at", x, y, ang], ["effects", font(), just], ["uuid", uid("label", key)]]


def symbol_instance(ref, p, items, root_uuid):
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
    sym.append(["instances", ["project", Q(_cfg("project")),
                              ["path", Q("/" + root_uuid), ["reference", Q(ref)], ["unit", 1]]]])
    items.append(sym)

    extra = set(p["nets"]) - set(geo)
    assert not extra, "%s has no pins %s" % (ref, sorted(extra))
    missing = set(geo) - set(p["nets"])
    assert not missing, "%s pins not assigned (use None for no-connect): %s" % (ref, sorted(missing))
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
                    raise SystemExit("label/pin collision at %s: %s.%s (%s) vs %s: move one part on the sheet"
                                     % (pt, ref, num, net, other))
                seen[pt] = (net, "%s.%s" % (ref, num))


def write_symbol_lib(hw):
    custom = [s for lib_id, s in CUSTOM.items()]
    if not custom:
        return
    os.makedirs(os.path.join(hw, "lib"), exist_ok=True)
    lib = ["kicad_symbol_lib", ["version", 20251024], ["generator", Q(_cfg("lib") + "_gen")],
           ["generator_version", Q("10.0")]] + custom
    with open(os.path.join(hw, "lib", _cfg("lib") + ".kicad_sym"), "w") as f:
        f.write(dump(lib) + "\n")


def write_schematic(hw):
    root = uid("root")
    lib_symbols = ["lib_symbols"]
    for lib_id in sorted({p["lib_id"] for p in PARTS.values()}):
        s = list(libsym(lib_id))
        s[1] = Q(lib_id)
        lib_symbols.append(s)

    items = []
    for ref, p in PARTS.items():
        symbol_instance(ref, p, items, root)
    for i, ((x, y), text) in enumerate(NOTES):
        items.append(["text", Q(text), ["exclude_from_sim", "no"], ["at", x, y, 0],
                      ["effects", font(), ["justify", "left", "top"]], ["uuid", uid("note", i)]])

    comments = ["Generated by tools/kicad from 5-electronics/src/design.py"] + _cfg("comments")
    tb = ["title_block", ["title", Q(_cfg("title"))], ["date", Q(_cfg("date"))], ["rev", Q(_cfg("rev"))],
          ["company", Q(_cfg("company"))]] + [["comment", i + 1, Q(c)] for i, c in enumerate(comments)]
    sch = ["kicad_sch", ["version", 20250114], ["generator", Q("eeschema")], ["generator_version", Q("9.0")],
           ["uuid", root], ["paper", Q(_cfg("paper"))], tb,
           lib_symbols] + items + [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]],
                                   ["embedded_fonts", "no"]]
    with open(os.path.join(hw, _cfg("project") + ".kicad_sch"), "w") as f:
        f.write(dump(sch) + "\n")


def write_project_files(hw):
    project = _cfg("project")
    pro_path = os.path.join(hw, project + ".kicad_pro")
    if not os.path.exists(pro_path):
        with open(pro_path, "w") as f:
            json.dump({"meta": {"filename": project + ".kicad_pro", "version": 3},
                       "sheets": [[str(uid("root")), "Root"]]}, f, indent=2)
            f.write("\n")
    if CUSTOM:
        with open(os.path.join(hw, "sym-lib-table"), "w") as f:
            f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "%s") (type "KiCad") '
                    '(uri "${KIPRJMOD}/lib/%s.kicad_sym") (options "") (descr "%s parts"))\n)\n'
                    % (_cfg("lib"), _cfg("lib"), _cfg("title")))


def build(hw):
    write_symbol_lib(hw)
    write_project_files(hw)
    check_label_collisions()
    write_schematic(hw)
    nets = {}
    for ref, p in PARTS.items():
        for num, net in p["nets"].items():
            if net:
                nets.setdefault(net, []).append("%s.%s" % (ref, num))
    for net in sorted(nets):
        if len(nets[net]) < 2:
            print("WARNING single-pin net", net, nets[net])
    print("wrote %d symbols, %d nets" % (len(PARTS), len(nets)))
