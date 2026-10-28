#!/usr/bin/env python3
"""Write bom.csv (Ref,Qty,Value,Description,Footprint,MPN) from the exported netlist.

Usage: python3 -I tools/make_bom.py output/backpack-defender.net > bom.csv
Lines are grouped by value + footprint + MPN. Parts marked DNP or excluded from the BOM
(pads, test points, holes, fiducials) are left out; off-board parts are added at the end.
"""

import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import find, find_all, parse  # noqa: E402

OFF_BOARD = [
    ("BT1", "2xAAA holder", "Battery holder, 2 x AAA side by side, wire leads (~52 x 25 x 12 mm), soldered to J1",
     "off-board", "generic 2xAAA holder with leads"),
]


def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def main(path):
    net = parse(open(path).read())
    groups = {}
    for c in find_all(find(net, "components"), "comp"):
        props = {str(find(p, "name")[1]) for p in find_all(c, "property")}
        if "dnp" in props or "exclude_from_bom" in props:
            continue
        fields = {str(find(f, "name")[1]): (str(f[2]) if len(f) > 2 else "")
                  for f in find_all(find(c, "fields"), "field")}
        desc = find(c, "description")
        key = (str(find(c, "value")[1]), str(find(c, "footprint")[1]).split(":")[-1], fields.get("MPN", ""))
        g = groups.setdefault(key, dict(refs=[], desc=str(desc[1]) if desc else fields.get("Description", "")))
        g["refs"].append(str(find(c, "ref")[1]))
    w = csv.writer(sys.stdout, lineterminator="\n")
    w.writerow(["Ref", "Qty", "Value", "Description", "Footprint", "MPN"])
    for (value, fp, mpn), g in sorted(groups.items(), key=lambda kv: natural(sorted(kv[1]["refs"], key=natural)[0])):
        refs = sorted(g["refs"], key=natural)
        w.writerow([" ".join(refs), len(refs), value, g["desc"], fp, mpn])
    for ref, value, desc, fp, mpn in OFF_BOARD:
        w.writerow([ref, 1, value, desc, fp, mpn])


if __name__ == "__main__":
    main(sys.argv[1])
