"""The numbers Stages 4 and 5 share: the episode's fit.json.

fit.json is the single source of truth for how the board sits in the enclosure. Stage 4's
build_model.py and Stage 5's layout.py both read it, so a change is made once and both follow.
FIT.md (next to it) keeps the request log and the permission rules, and its "Fit" section is
generated from fit.json by tools/fit/fitmd.py, so the two can't drift.

Everything on the board is in **board coordinates** (mm, origin at the board's centre, +x right
and +y up as seen from the board's top face, which is how tools/kicad's layout.py works). The
board's place in the enclosure is given once, in `board.origin` / `x_axis` / `y_axis`, and
`to_enclosure()` converts.

    from fitlib import load_fit
    fit = load_fit(__file__)          # any path inside the episode folder
    w, h = fit.size
    x, y, z = fit.to_enclosure(fit.feature("pir"), height=13.0)   # 13 mm above the top face

Keys (tools/fit/README.md has a full example):
    board     size [w, h], corner_r, thickness, faces ("top" | "both"), provisional (bool),
              posts_face ("bottom" default: the board sits on its posts; "top": posts press on the top face),
              origin [x, y, z]  enclosure point at the board's centre, on its top face,
              x_axis, y_axis    enclosure directions of the board's +x and +y
    holes     [[x, y], ...]     screw holes (H1, H2, ... in this order), hole_d (default 2.2)
    rests     [[x, y], ...]     posts that only support the board (no hole)
    features  {name: {"at": [x, y], "face": "top" | "bottom", "note": ...}}  what the two sides line up
    keepouts  {name: [x0, y0, x1, y1]}
    model     {"design": "4-model/model.solidcraft", "stand_ins": [body names]}  for fitcheck.py
"""
import json
import math
import os


class FitError(Exception):
    pass


def find_episode(path):
    """The episode folder (holding fit.json, FIT.md or episode.json) at or above path."""
    p = os.path.abspath(path)
    if os.path.isfile(p):
        p = os.path.dirname(p)
    while True:
        if any(os.path.isfile(os.path.join(p, f)) for f in ("fit.json", "FIT.md", "episode.json")):
            return p
        parent = os.path.dirname(p)
        if parent == p:
            raise FitError("no episode folder (with fit.json, FIT.md or episode.json) above " + path)
        p = parent


def _vec(v, n=3):
    v = [float(a) for a in v]
    if len(v) != n:
        raise FitError("expected %d numbers, got %r" % (n, v))
    return v


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


class Fit:
    def __init__(self, data, path):
        self.data, self.path = data, path
        self.episode = os.path.dirname(path)
        b = data.get("board")
        if not b:
            raise FitError("fit.json has no 'board'")
        self.board = b
        self.size = _vec(b["size"], 2)
        self.corner_r = float(b.get("corner_r", 0))
        self.thickness = float(b.get("thickness", 1.6))
        self.origin = _vec(b["origin"])
        self.x_axis = _vec(b.get("x_axis", [1, 0, 0]))
        self.y_axis = _vec(b.get("y_axis", [0, 1, 0]))
        for v in (self.x_axis, self.y_axis):
            if abs(math.sqrt(_dot(v, v)) - 1) > 1e-6:
                raise FitError("board axes must be unit vectors: %r" % v)
        if abs(_dot(self.x_axis, self.y_axis)) > 1e-6:
            raise FitError("board x_axis and y_axis must be at right angles")
        self.normal = _cross(self.x_axis, self.y_axis)      # the direction the top face looks
        self.posts_face = b.get("posts_face", "bottom")       # the face the posts / rests touch
        if self.posts_face not in ("top", "bottom"):
            raise FitError("board.posts_face must be \"top\" or \"bottom\"")
        self.holes = [_vec(h, 2) for h in data.get("holes", [])]
        self.hole_d = float(data.get("hole_d", 2.2))
        self.rests = [_vec(h, 2) for h in data.get("rests", [])]
        self.features = data.get("features", {})
        self.keepouts = data.get("keepouts", {})
        self.model = data.get("model", {})

    # --- board side -------------------------------------------------------------
    def feature(self, name):
        """A feature's board (x, y)."""
        if name not in self.features:
            raise FitError("fit.json has no feature %r (it has: %s)" % (name, ", ".join(sorted(self.features))))
        return tuple(_vec(self.features[name]["at"], 2))

    def keepout(self, name):
        return tuple(_vec(self.keepouts[name], 4))

    def board_tuple(self):
        """(width, height, corner_radius), as tools/kicad's layout.BOARD wants it."""
        return (self.size[0], self.size[1], self.corner_r)

    # --- enclosure side ---------------------------------------------------------
    def to_enclosure(self, xy, height=0.0):
        """Board (x, y) and a height above the top face (negative: below it; the bottom face is at
        -thickness) to an enclosure point."""
        x, y = xy
        return tuple(o + x * a + y * b + height * n
                     for o, a, b, n in zip(self.origin, self.x_axis, self.y_axis, self.normal))

    def to_board(self, p):
        """Enclosure point to (board x, board y, height above the top face)."""
        d = [a - o for a, o in zip(p, self.origin)]
        return _dot(d, self.x_axis), _dot(d, self.y_axis), _dot(d, self.normal)

    def placement_matrix(self, step_top_z, lift=0.0):
        """Row-major 3 x 4 rigid move taking a KiCad STEP export of the board (exported with its
        origin at the board centre: x, y as in layout.py, top face at z = step_top_z) into place.
        lift moves it that far off its posts (away from posts_face), so contact can be measured."""
        R = [[self.x_axis[i], self.y_axis[i], self.normal[i]] for i in range(3)]
        away = -1.0 if self.posts_face == "top" else 1.0
        t = [self.origin[i] + (away * lift - step_top_z) * self.normal[i] for i in range(3)]
        return [R[0][0], R[0][1], R[0][2], t[0], R[1][0], R[1][1], R[1][2], t[1], R[2][0], R[2][1], R[2][2], t[2]]


def fit_path(anywhere):
    return os.path.join(find_episode(anywhere), "fit.json")


def load_fit(anywhere):
    """Read the episode's fit.json. `anywhere` is any file or folder inside the episode."""
    path = fit_path(anywhere)
    if not os.path.isfile(path):
        raise FitError("no fit.json in %s: Stage 4 starts it (see tools/fit/README.md)" % os.path.dirname(path))
    try:
        data = json.load(open(path))
    except json.JSONDecodeError as e:
        raise FitError("%s isn't valid JSON: %s" % (path, e))
    return Fit(data, path)
