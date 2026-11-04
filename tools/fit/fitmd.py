#!/usr/bin/env python3
"""Write FIT.md's "Fit" section from fit.json, so the two can't drift.

  python3 tools/fit/fitmd.py episodes/<slug>

Only the text between the `<!-- fit:start -->` and `<!-- fit:end -->` markers is rewritten; the
request log and the rules around it are left alone. If FIT.md doesn't exist yet it is created
with the rules and an empty request log. tools/kicad/build.sh and fitcheck.py run this too.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fitlib import FitError, board_names, find_episode, load_fit  # noqa: E402

START = "<!-- fit:start: generated from fit.json by tools/fit/fitmd.py. Edit fit.json, not this section -->"
END = "<!-- fit:end -->"

RULES = """## Rules

What each stage may change without asking (the full version is in CLAUDE.md, "Stages 4 and 5 work together"):

- **Stage 5** may change the board's size, shape, posts and the inside positions of parts and connectors. It edits `fit.json` and adds a request below so Stage 4 follows.
- **Stage 4** may move posts, ribs and internal features, and may grow the enclosure by up to about 10 % in any direction to make room, keeping the concept's look.
- **Ask the hosts first** before anything visible changes: the outer size beyond 10 %, the shape, or where buttons, windows, eyes, ports or speakers sit on the outside.
"""

REQUESTS = """## Requests

One line each, newest last: `- [open] 5→4: …`. The other stage marks it `[done]` once it's in its model or board, or `[asked hosts]`.

- (none yet)
"""

AXES = {(1, 0, 0): "+x", (-1, 0, 0): "−x", (0, 1, 0): "+y", (0, -1, 0): "−y", (0, 0, 1): "+z (up)", (0, 0, -1): "−z (down)"}


def f1(v):
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s.replace("-", "−")


def pt(p):
    return "(" + ", ".join(f1(v) for v in p) + ")"


def section(fit, slug, head="## Fit"):
    w, h = fit.size
    corners = [fit.to_enclosure((sx * w / 2, sy * h / 2)) for sx in (-1, 1) for sy in (-1, 1)]
    corners += [fit.to_enclosure((sx * w / 2, sy * h / 2), -fit.thickness) for sx in (-1, 1) for sy in (-1, 1)]
    span = ", ".join("%s %s to %s" % (a, f1(min(c[i] for c in corners)), f1(max(c[i] for c in corners)))
                     for i, a in enumerate("xyz"))
    faces = {"top": "parts on the top face", "both": "parts on both faces"}.get(fit.board.get("faces", "top"), fit.board.get("faces"))
    look = AXES.get(tuple(int(round(v)) for v in fit.normal), pt(fit.normal))
    lines = [START, head, "",
             "Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/%s` "
             "(the kit's build and the fit check also do it). Board positions are board mm (origin at the board "
             "centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm "
             "(origin at its centre)." % slug, "",
             "- **Board:** %s × %s mm, R%s, %s thick, %s%s." % (
                 f1(w), f1(h), f1(fit.corner_r), f1(fit.thickness), faces,
                 " **(provisional: Stage 5's SIZE.md decides)**" if fit.board.get("provisional") else ""),
             "- **Where:** top face looks %s; its centre is at enclosure %s. The board spans enclosure %s. Its posts touch the %s face." % (
                 look, pt(fit.origin), span, fit.posts_face)]
    if fit.holes:
        lines.append("- **Screw holes** (Ø%s): " % f1(fit.hole_d) + "; ".join(
            "H%d board %s = enclosure %s" % (i + 1, pt(hp), pt(fit.to_enclosure(hp))) for i, hp in enumerate(fit.holes)) + ".")
    if fit.rests:
        lines.append("- **Rest posts** (no hole): " + "; ".join(
            "board %s = enclosure %s" % (pt(r), pt(fit.to_enclosure(r))) for r in fit.rests) + ".")
    if fit.features:
        lines += ["", "| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |", "|---|---|---|---|---|"]
        for name, f in fit.features.items():
            face = f.get("face", "top")
            e = fit.to_enclosure(f["at"], 0.0 if face == "top" else -fit.thickness)
            note = f.get("note", "")
            if "size" in f:
                note = ("%s × %s mm. " % (f1(f["size"][0]), f1(f["size"][1])) + note).strip()
            lines.append("| %s | %s | %s | %s | %s |" % (name, pt(f["at"]), face, pt(e), note))
    if fit.keepouts:
        lines += ["", "- **Keep-outs** (board x0, y0, x1, y1): " + "; ".join(
            "%s %s" % (k, pt(v)) for k, v in fit.keepouts.items()) + "."]
    m = fit.model
    if m:
        lines.append("- **Fit check** (`python3 tools/fit/fitcheck.py episodes/%s%s`): the real board in `%s`, without Stage 4's stand-ins %s." % (
            slug, "/5-electronics/" + fit.name if fit.name else "", m.get("design", "4-model/model.solidcraft"), ", ".join(m.get("stand_ins", [])) or "(none listed)"))
    lines += ["", END]
    return "\n".join(lines)


def write(episode):
    ep = find_episode(episode)
    slug = os.path.basename(ep)
    if os.path.basename(os.path.dirname(ep)) == "units":  # a unit of a multi-unit product
        slug = "%s/units/%s" % (os.path.basename(os.path.dirname(os.path.dirname(ep))), slug)   # so "episodes/<slug>" commands still work
    path = os.path.join(ep, "FIT.md")
    names = board_names(ep)
    if names:
        parts = [section(load_fit(ep, board=n), slug, "### Board: %s (`5-electronics/%s/`)" % (n, n)) for n in names]
        sec = "\n".join([START, "## Fit", "", "This product has %d boards, each with its own entry under `boards` in `fit.json`." % len(names), ""]
                        + [p[len(START) + 1:-len(END) - 1] for p in parts] + [END])
    else:
        sec = section(load_fit(ep), slug)
    if not os.path.isfile(path):
        title = "# %s: fit between enclosure and board\n\nThe contract between Stage 4 (`4-model/`) and Stage 5 (`5-electronics/`). The numbers live in `fit.json`; this file holds the generated summary, the rules and the request log.\n" % slug
        text = "\n".join([title, sec, "", RULES, REQUESTS])
    else:
        text = open(path).read()
        if START.split(":")[0] in text and END in text:
            a = text.index(START.split(":")[0])
            b = text.index(END) + len(END)
            text = text[:a] + sec + text[b:]
        else:
            # first run on a hand-written FIT.md: swap its "## Fit" section, or put the block on top
            i = text.find("\n## Fit")
            if i >= 0:
                j = text.find("\n## ", i + 1)
                text = text[:i + 1] + sec + "\n" + (text[j:] if j >= 0 else "")
            else:
                k = text.find("\n## ")
                text = (text[:k + 1] + sec + "\n" + text[k:]) if k >= 0 else (text.rstrip() + "\n\n" + sec + "\n")
    tmp = "%s.%d.tmp" % (path, os.getpid())     # per process: two boards may be checked at once
    open(tmp, "w").write(text)
    os.replace(tmp, path)
    return path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    try:
        print("wrote", write(sys.argv[1]))
    except FitError as e:
        raise SystemExit(str(e))
