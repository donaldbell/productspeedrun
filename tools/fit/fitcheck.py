#!/usr/bin/env python3
"""Check the routed board against the enclosure: the real board, not stand-in boxes.

  python3 tools/fit/fitcheck.py episodes/<slug>            (from the repo folder)

1. Exports the episode's .kicad_pcb as STEP (parts included) with its origin at the board centre.
2. Takes a copy of the Stage 4 design (fit.json: model.design), removes Stage 4's electronics
   stand-ins (model.stand_ins), inserts the board and moves it to where fit.json puts it.
3. Runs SolidCraft's clearance check of every enclosure body against every board body.
4. Writes 5-electronics/fitcheck.md (overlaps and near misses, in board and enclosure mm)
   and 5-electronics/fitcheck.png (the shell see-through, the board solid).

Exits 1 if anything overlaps: Stage 5 isn't finished until this passes, as well as DRC. It also
refreshes FIT.md's generated "Fit" section first. Scratch files go to
5-electronics/output/fit/. Takes a few minutes (most of it the clearance check).
"""
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fitlib import FitError, find_episode, load_fit  # noqa: E402
import fitmd  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KICAD_CLI = os.environ.get("KICAD_CLI", "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
SOLIDCRAFT = os.environ.get("SOLIDCRAFT_CLI", "solidcraft-cli")
NEAR = float(os.environ.get("FIT_NEAR", "0.3"))       # report gaps smaller than this (mm)
LIFT = float(os.environ.get("FIT_LIFT", "0.02"))      # check the board this far off its posts: touching
                                                       # faces can't be intersected, a 0.02 mm gap can


def kit_page_centre():
    """The page point tools/kicad puts the board centre on (pcbkit.CX, CY)."""
    src = open(os.path.join(REPO, "tools", "kicad", "pcbkit.py")).read()
    m = re.search(r"^CX, CY = ([\d.]+), ([\d.]+)", src, re.M)
    if not m:
        raise SystemExit("can't find CX, CY in tools/kicad/pcbkit.py")
    return float(m.group(1)), float(m.group(2))


def solidcraft(script, out, inp=None, save=None, label=""):
    path = out + ".json"
    json.dump({"commands": script}, open(path, "w"), indent=1)
    cmd = [SOLIDCRAFT, "run", path, "--results", "--quiet", "--json-out", out + ".out.json"]
    if inp:
        cmd += ["--in", inp]
    if save:
        cmd += ["--save", save]
    print("  solidcraft:", label, flush=True)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit("solidcraft-cli failed (%s):\n%s%s" % (label, p.stdout[-2000:], p.stderr[-2000:]))
    return json.load(open(out + ".out.json"))


def main(arg):
    ep = find_episode(arg)
    fit = load_fit(ep)
    fitmd.write(ep)
    hw = os.path.join(ep, "5-electronics")
    out = os.path.join(hw, "output", "fit")
    os.makedirs(out, exist_ok=True)
    pcbs = [p for p in glob.glob(os.path.join(hw, "*.kicad_pcb"))]
    if len(pcbs) != 1:
        raise SystemExit("expected one .kicad_pcb in %s, found %d" % (hw, len(pcbs)))
    pcb = pcbs[0]
    project = os.path.splitext(os.path.basename(pcb))[0]
    design = os.path.join(ep, fit.model.get("design", "4-model/model.solidcraft"))
    if not os.path.isfile(design):
        raise SystemExit("no Stage 4 design at " + design + " (fit.json: model.design)")
    stand_ins = list(fit.model.get("stand_ins", []))

    # 1. board -> STEP, origin at the board centre. The file's stem names the inserted component.
    step = os.path.join(out, "fitcheck_board.step")
    occurrence = "fitcheck_board:1"
    cx, cy = kit_page_centre()
    print("exporting", os.path.basename(pcb), "as STEP", flush=True)
    p = subprocess.run([KICAD_CLI, "pcb", "export", "step", "--user-origin", "%gx%gmm" % (cx, cy),
                        "--subst-models", "-f", "-o", step, pcb], capture_output=True, text=True)
    if p.returncode != 0 or not os.path.isfile(step):
        raise SystemExit("kicad-cli STEP export failed:\n" + p.stdout[-2000:] + p.stderr[-2000:])

    # 2a. quick look at the board on its own: its body names and where KiCad put its top face
    res = solidcraft([{"command": "file.new", "params": {}},
                      {"command": "file.insert_step", "params": {"path": step}},
                      {"command": "inspect.measure", "params": {"bodies": [project + "_PCB"]}}],
                     os.path.join(out, "probe"), label="read the board")
    board_bodies = sorted(set(res[1]["bodies"]))
    top_z = res[2]["bodies"][0]["bbox"]["max"][2]

    # 2b. one pass over the enclosure: drop the stand-ins, insert the board, move it into place, check
    mat = [round(v, 6) for v in fit.placement_matrix(top_z, LIFT)]
    script = []
    if stand_ins:
        script.append({"command": "solid.remove", "params": {"bodies": stand_ins}})
    script += [{"command": "inspect.measure", "params": {}},
               {"command": "file.insert_step", "params": {"path": step}},
               {"command": "occurrence.move", "params": {"occurrence": occurrence, "space": "world", "matrix": mat,
                                                         "move_grounded": True}},
               {"command": "inspect.measure", "params": {"bodies": [project + "_PCB"]}},
               {"command": "inspect.clearance", "params": {"against": board_bodies, "clearance": NEAR,
                                                           "skip_within": "component"}}]
    placed = os.path.join(out, "placed.solidcraft")
    res = solidcraft(script, os.path.join(out, "check"), inp=design, save=placed,
                     label="place it in the enclosure and check clearances (a few minutes)")
    k = 1 if stand_ins else 0
    enclosure = [b["name"] for b in res[k]["bodies"]]
    box = res[k + 3]["bodies"][0]["bbox"]
    clr = res[k + 4]

    # 3. picture: enclosure see-through, board solid
    png = os.path.join(hw, "fitcheck.png")
    snap = [SOLIDCRAFT, "snapshot", "--in", placed, "--out", png, "--view", "iso", "--width", "1400", "--height", "1000"]
    for b in enclosure:
        snap += ["--body", "%s:opacity=0.15" % b]
    subprocess.run(snap, capture_output=True, text=True)

    # 4. report
    def where(c):
        bx, by, h = fit.to_board(c)
        return "board (%.1f, %.1f), %+.1f mm from the top face; enclosure (%.1f, %.1f, %.1f)" % (bx, by, h, *c)

    def short(name):
        return (name or "?").split(" (fitcheck_board")[0]

    overlaps = clr.get("overlaps", [])
    near = clr.get("near", [])
    lines = ["# Fit check: %s in the enclosure" % project, "",
             "Real board (KiCad STEP export, parts included) placed in `%s` where `fit.json` puts it, with Stage 4's "
             "stand-ins removed (%s). Re-run with `python3 tools/fit/fitcheck.py episodes/%s`." % (
                 os.path.relpath(design, ep), ", ".join(stand_ins) or "none", os.path.basename(ep)), "",
             "**Result: %s**: %d overlaps, %d gaps under %.1f mm, %d pairs the checker couldn't measure." % (
                 ("PASS" if not clr.get("unchecked") else "PASS, with pairs not measured") if not overlaps else "FAIL", len(overlaps), len(near), NEAR, len(clr.get("unchecked", []))), "",
             "Board placed at enclosure x %.1f..%.1f, y %.1f..%.1f, z %.1f..%.1f." % (
                 box["min"][0], box["max"][0], box["min"][1], box["max"][1], box["min"][2], box["max"][2]), ""]
    if overlaps:
        lines += ["## Overlaps", ""]
        for o in sorted(overlaps, key=lambda o: -o["volume_mm3"]):
            lines.append("- **%s** into **%s**: %.2f mm³ at %s" % (short(o["b"]), short(o["a"]), o["volume_mm3"], where(o["center"])))
        lines.append("")
    if near:
        lines += ["## Close (under %.1f mm)" % NEAR, ""]
        for n in near:
            d = n.get("distance_mm")
            expected = " (posts: the board rests on them, lifted %.2f mm for the check)" % LIFT if d is not None and abs(d - LIFT) < 0.005 else ""
            lines.append("- %s to %s: %s mm%s" % (short(n.get("a")), short(n.get("b")), "%.2f" % d if d is not None else "?", expected))
        lines.append("")
    if clr.get("unchecked"):
        lines += ["## Not measured", "", "The checker couldn't intersect these pairs, so an overlap there would go unseen. Look at them in the picture.", ""] + \
            ["- %s / %s: %s" % (short(u["a"]), short(u["b"]), u["reason"]) for u in clr["unchecked"]] + [""]
    lines += ["![fit check](fitcheck.png)", ""]
    open(os.path.join(hw, "fitcheck.md"), "w").write("\n".join(lines))
    print("\n".join(lines[4:6]))
    return 1 if overlaps else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    try:
        sys.exit(main(sys.argv[1]))
    except FitError as e:
        raise SystemExit("fit.json: %s" % e)
