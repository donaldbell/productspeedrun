#!/usr/bin/env python3
"""List the parts on a board that would be missing from its STEP export.

  python3 -I tools/kicad/check_models.py <board.kicad_pcb> [--quiet]

kicad-cli's STEP export silently leaves out any footprint with no 3D model, or whose model
file it can't find. The fit check would then pass with that part simply absent. This reads
the board and reports, for every placed part:
  - no model:  the footprint names no 3D model at all
  - not found: it names one, but the file isn't there (after expanding ${KICAD10_3DMODEL_DIR},
               ${KIPRJMOD}, and other environment variables; a .wrl counts if a .step or .stp sits
               beside it, as --subst-models uses that)
  - hidden:    the only model is switched off in the footprint
A footprint that names a model is always checked. One that names none is skipped if it looks like it
has no height: marked board-only, not marked SMD or through-hole (mounting holes, test and pogo pads,
logos), or with no paste and no through-hole pad (fiducials).

A DNP part with a missing model (for example the solder-wire pads, for which KiCad ships no model)
is reported as a warning only. Exits 1 if any other part is missing, so callers can stop. --quiet prints only problems.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import find, find_all, parse  # noqa: E402

KICAD_SHARE = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"


def expand(path, board_dir):
    env = dict(os.environ)
    env.setdefault("KIPRJMOD", board_dir)
    for v in ("KICAD10_3DMODEL_DIR", "KICAD9_3DMODEL_DIR", "KICAD8_3DMODEL_DIR", "KICAD_3DMODEL_DIR"):
        env.setdefault(v, os.path.join(KICAD_SHARE, "3dmodels"))
    out = re.sub(r"\$\{(\w+)\}", lambda m: env.get(m.group(1), m.group(0)), path)
    if not os.path.isabs(out):
        out = os.path.join(board_dir, out)
    return out


def found(path):
    if os.path.isfile(path):
        return True
    stem, ext = os.path.splitext(path)
    if ext.lower() == ".wrl":
        return any(os.path.isfile(stem + e) for e in (".step", ".stp", ".STEP", ".STP"))
    return False


def ref_of(fp):
    for prop in find_all(fp, "property"):
        if len(prop) > 2 and prop[1] == "Reference":
            return str(prop[2])
    return "?"


def flat(fp):
    """Pads only, nothing soldered on: no through-hole pad and no pad with solder paste (fiducials)."""
    for pad in find_all(fp, "pad"):
        if len(pad) > 2 and str(pad[2]) == "thru_hole":
            return False
        layers = find(pad, "layers")
        if layers and any("Paste" in str(x) for x in layers[1:]):
            return False
    return True


def check(pcb):
    board_dir = os.path.dirname(os.path.abspath(pcb))
    board = parse(open(pcb).read())
    if board and isinstance(board[0], list):
        board = board[0]
    problems, checked, skipped = [], 0, 0
    for fp in find_all(board, "footprint"):
        attr = find(fp, "attr")
        attrs = [str(a) for a in attr[1:]] if attr else []
        models = find_all(fp, "model")
        no_height = "board_only" in attrs or not ({"smd", "through_hole"} & set(attrs)) or flat(fp)
        if no_height and not models:
            skipped += 1
            continue
        checked += 1
        ref, name = ref_of(fp), str(fp[1])
        warn = "dnp" in attrs
        shown = [m for m in models if not any(isinstance(x, list) and x[:2] == ["hide", "yes"] for x in m)]
        if not models:
            problems.append((ref, name, "no model", "", warn))
        elif not shown:
            problems.append((ref, name, "hidden", str(models[0][1]), warn))
        else:
            paths = [str(m[1]) for m in shown]
            if not any(found(expand(p, board_dir)) for p in paths):
                problems.append((ref, name, "not found", paths[0], warn))
    return problems, checked, skipped


def report(problems):
    """Print the problems; return the ones that should fail (DNP parts only warn)."""
    for ref, name, why, path, warn in problems:
        print("  %-6s %-10s %s%s%s" % (ref, why, name, ("  (" + path + ")") if path else "",
                                       "  [DNP: warning only]" if warn else ""))
    return [p for p in problems if not p[4]]


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    problems, checked, skipped = check(args[0])
    failing = report(problems)
    if problems or "--quiet" not in argv:
        print("3D models: %d of %d parts missing from the STEP, %d of them DNP (warning only); "
              "%d with no model and no height skipped" % (len(problems), checked, len(problems) - len(failing), skipped))
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
