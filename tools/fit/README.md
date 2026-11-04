# Fit kit

How the board sits in the enclosure, kept in one place that both stages read, and a check of the real routed board inside the real model.

```
episodes/<slug>/
  fit.json        the shared numbers (single source of truth): Stage 4's build_model.py and
                  Stage 5's layout.py both read it through fitlib
  FIT.md          the request log and the rules between the stages; its "Fit" section is
                  generated from fit.json, so the two can't drift
  5-electronics/fitcheck.md, fitcheck.png     the fit check's report and picture
```

## Commands

Run from the repo folder.

| Command | What it does | Time |
|---|---|---|
| `python3 tools/fit/fitmd.py episodes/<slug>` | Rewrites FIT.md's "Fit" section from fit.json (creates FIT.md with the rules and an empty request log if it isn't there). The kit's `build.sh` and `fitcheck.py` also run it. | instant |
| `python3 tools/fit/fitcheck.py episodes/<slug>` | Exports the routed board as STEP, places it in a copy of the Stage 4 design where fit.json says, without Stage 4's electronics stand-ins, and checks every enclosure body against every board body. Writes `5-electronics/fitcheck.md` and `fitcheck.png`. Exits 1 on any overlap. | a few minutes |

Scratch files go to `5-electronics/output/fit/` (not committed).

## fit.json

Board positions are **board mm**: origin at the board's centre, +x right and +y up as seen from the board's top face (KiCad top). That's what `layout.py` uses already. The board's place in the enclosure is given once, so nobody converts by hand:

- `origin`: the enclosure point at the board's centre, on its top face.
- `x_axis`, `y_axis`: the enclosure directions of the board's +x and +y. The top face looks along `x_axis × y_axis`.

A flat board lying in the base, top face up, 14.5 mm above the floor (episode 001's layout):

```json
{
  "board": {"size": [70, 45], "corner_r": 9, "thickness": 1.6, "faces": "top",
            "origin": [0, 0, 16.1], "x_axis": [1, 0, 0], "y_axis": [0, 1, 0]},
  "holes": [[-31, -17], [31, -17], [-31, 17], [31, 17]],
  "features": {"button": {"at": [18, 0], "face": "top", "note": "big silence button, 12 x 12 tact switch"},
               "pir":    {"at": [-26, 13], "face": "top"}},
  "model": {"design": "4-model/model.solidcraft", "stand_ins": ["PCB", "ESP32-C3-WROOM-02"]}
}
```

A board standing upright behind a face, top face looking out through the front (−y), centre 6 mm above the shell's centre (episode 002's layout):

```json
{
  "board": {"size": [54, 31], "corner_r": 5, "thickness": 1.6, "faces": "both",
            "origin": [0, -15, 6], "x_axis": [1, 0, 0], "y_axis": [0, 0, 1], "posts_face": "top"},
  "holes": [[-21, -13.25], [21, -13.25], [21, 12.5]],
  "rests": [[-21, 12.5]],
  "features": {"pir":      {"at": [0, -2],    "face": "top", "note": "dome through the visor"},
               "eye_l":    {"at": [-11, 3.2], "face": "top"},
               "eye_r":    {"at": [11, 3.2],  "face": "top"},
               "mic_port": {"at": [0, -12],   "face": "bottom", "note": "port hole through the board"},
               "module":   {"at": [-13, 1.9], "face": "bottom", "size": [18, 25.5]}},
  "keepouts": {"antenna": [-22.6, 8.2, -3.4, 15.5]},
  "model": {"design": "4-model/model.solidcraft",
            "stand_ins": ["Main Board", "ESP32-S3-WROOM-1", "LED L", "LED R", "Mic", "PIR Dome"]}
}
```

Several boards (separate devices, episode 003): `{"boards": {"sensor": {...}, "receiver": {...}}}`, each entry with the keys below and its origin in its own `model.design` (two entries may share one design). Electronics live in `5-electronics/<board>/`; `load_fit(path)` picks the board from such a path, otherwise pass `board=`. `fitmd.py` writes one subsection per board, and `fitcheck.py` checks one board (`episodes/<slug>/5-electronics/<board>`) or all of them (the episode folder).

Keys:

| Key | Meaning |
|---|---|
| `board.size`, `corner_r`, `thickness` | Outline in mm. `layout.BOARD = fit.board_tuple()`. |
| `board.faces` | `"top"` or `"both"`. Which faces carry parts. |
| `board.provisional` | `true` until Stage 5's `SIZE.md` has confirmed the area. |
| `board.posts_face` | The face the posts touch: `"bottom"` (default: the board sits on its posts) or `"top"` (posts press on the top face, like 002's face-cap posts). The fit check lifts the board 0.02 mm off them, because touching faces can't be intersected. |
| `holes`, `hole_d` | Screw holes, H1, H2… in this order (default Ø2.2 for M2 self-tappers). Stage 4 puts its posts here. |
| `rests` | Posts that only support the board (no hole). |
| `features` | Anything the two sides line up: sensors, LEDs, buttons, ports, windows, a module's antenna end. `at` is board (x, y), `face` is `top` or `bottom`, plus optional `size` and `note`. Name them in lower case (`pir`, `eye_l`, `usb`). |
| `keepouts` | Board rectangles `[x0, y0, x1, y1]` (an antenna's copper keep-out). |
| `model.design` | The Stage 4 design the fit check uses (default `4-model/model.solidcraft`). |
| `model.stand_ins` | Stage 4 body names that stand in for parts that are on the board (the board itself, the module, LEDs). The fit check removes them, because the real board takes their place. Off-board parts (speaker, battery, fan) stay in, so the board is checked against them. |

## Reading it

Both sides use `fitlib` (`tools/fit/fitlib.py`). The kit puts it on the import path for `layout.py`. A Stage 4 script adds it itself:

```python
# 5-electronics/src/layout.py
from fitlib import load_fit
FIT = load_fit(__file__)
BOARD = FIT.board_tuple()
HOLES = [tuple(h) for h in FIT.holes]
PIR_AT = FIT.feature("pir")

# 4-model/build_model.py
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "fit"))
from fitlib import load_fit
FIT = load_fit(__file__)
posts = [FIT.to_enclosure(h) for h in FIT.holes + FIT.rests]              # where posts meet the top face
pir_apex = FIT.to_enclosure(FIT.feature("pir"), height=13.0)               # 13 mm above the top face
module = FIT.to_enclosure(FIT.feature("module"), -FIT.thickness - 1.55)    # middle of a 3.1 mm module on the bottom
```

`to_enclosure(xy, height)` takes a height above the top face (the bottom face is at `-thickness`). `to_board(p)` goes the other way.

## The fit check

The routed board comes from `kicad-cli pcb export step`, with the kit's board centre as origin and parts included. KiCad's STEP puts board x, y as in `layout.py`, with the board's bottom face at z 0. `fitcheck.py` measures the top face, builds the rigid move from fit.json (`Fit.placement_matrix`), lifts the board 0.02 mm off its posts (`FIT_LIFT`), and runs SolidCraft's `inspect.clearance` of every enclosure body against the board's bodies (pairs within the board are skipped). Gaps under 0.3 mm (`FIT_NEAR`) are listed, and the posts show up there at the lift distance. That catches what stand-in boxes miss: real connector bodies, tall parts, THT leads through the back, parts sitting under a post.

A part's real 3D model comes from KiCad's library. A footprint with the wrong or a missing model (a pin header standing in for a PIR, say) is checked as that model, so fix the model or note it in the report.

## Multi-unit products

A product made of separate devices (a transmitter and a receiver, say) has one fit folder per unit: `episodes/<slug>/units/<unit>/` holds that unit's `fit.json`, `FIT.md`, `4-model/` and `5-electronics/`. Pass the unit folder wherever these tools take an episode folder (`python3 tools/fit/fitcheck.py episodes/<slug>/units/rx`). `fitlib.find_episode` stops at a unit folder, so a unit never reads the episode's or another unit's numbers. See "Multi-unit products" in CLAUDE.md.
