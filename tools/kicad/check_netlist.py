#!/usr/bin/env python3
"""Compare the KiCad-exported netlist with the nets intended in src/design.py.

Usage: python3 -I tools/kicad/check_netlist.py <episode> <exported.net>
Catches stubs/labels that KiCad did not actually connect to the pin.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env import use_episode  # noqa: E402

use_episode(sys.argv)
from sexpr import find, find_all, parse  # noqa: E402
import design  # noqa: E402,F401
from schkit import PARTS  # noqa: E402


def main(path):
    net = parse(open(path).read())
    comps = find_all(find(net, "components"), "comp")
    got = {}
    for n in find_all(find(net, "nets"), "net"):
        name = str(find(n, "name")[1]).lstrip("/")
        for node in find_all(n, "node"):
            got[(str(find(node, "ref")[1]), str(find(node, "pin")[1]))] = name
    want = {}
    for ref, p in PARTS.items():
        if p.get("power"):
            continue
        for num, nm in p["nets"].items():
            want[(ref, num)] = nm
    errors = 0
    for key, nm in sorted(want.items()):
        actual = got.get(key)
        if nm is None:
            if actual and not actual.startswith("unconnected-"):
                print("NC pin %s.%s is on net %s" % (key + (actual,)))
                errors += 1
        elif actual != nm:
            print("%s.%s: want %s, got %s" % (key + (nm, actual)))
            errors += 1
    expected_refs = {r for r, p in PARTS.items() if not p.get("power")}
    refs = {str(find(c, "ref")[1]) for c in comps}
    if refs != expected_refs:
        print("component mismatch:", sorted(refs ^ expected_refs))
        errors += 1
    print("%d components, %d pins checked, %d errors" % (len(refs), len(want), errors))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[2]))
