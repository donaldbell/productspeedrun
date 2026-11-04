# 003-003: fit between enclosure and board

The contract between Stage 4 (`4-model/`) and Stage 5 (`5-electronics/`). The numbers live in `fit.json`; this file holds the generated summary, the rules and the request log.

<!-- fit:start: generated from fit.json by tools/fit/fitmd.py. Edit fit.json, not this section -->
## Fit

This product has 2 boards, each with its own entry under `boards` in `fit.json`.

### Board: sensor (`5-electronics/sensor/`)

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/003-003` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 44 × 20 mm, R3, 1.6 thick, parts on both faces.
- **Where:** top face looks +z (up); its centre is at enclosure (−40, 0, 9.8). The board spans enclosure x −62 to −18, y −10 to 10, z 8.2 to 9.8. Its posts touch the bottom face.
- **Screw holes** (Ø2.2): H1 board (−19.5, −7) = enclosure (−59.5, −7, 9.8); H2 board (19.5, −7) = enclosure (−20.5, −7, 9.8).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| mic | (−19.5, 5) | top | (−59.5, 5, 9.8) | 3.5 × 2.65 mm. ICS-43434 I2S MEMS mic (bottom port: port hole through the board) facing the front grille chamber; foam gasket ring between board and grille |
| status_led | (−20, 8) | top | (−60, 8, 9.8) | 1.6 × 0.8 mm. green 0603 LED under the front light pipe (pipe ends 1.4 above the board); the pipe's window is the slit beside the grille |
| button | (6, 0) | top | (−34, 0, 9.8) | 6 × 6 mm. 6 x 6 x 4.3 tact switch under the Ø12 top cap: press = test / pair, hold 3 s = on / off |
| usb | (18.5, 0) | top | (−21.5, 0, 9.8) | 8.9 × 7.3 mm. USB-C 16P top-mount receptacle, mouth flush with the +x board edge, centre 1.6 above the top face; port opening in the back of the shell |

- **Keep-outs** (board x0, y0, x1, y1): antenna (−15.5, 3.5, −2.5, 10).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/003-003/5-electronics/sensor`): the real board in `4-model/model.solidcraft`, without Stage 4's stand-ins S PCB, S Mic, S Status LED, S Tact Switch, S USB-C.

### Board: receiver (`5-electronics/receiver/`)

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/003-003` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 30 × 30 mm, R8, 1.6 thick, parts on both faces.
- **Where:** top face looks +z (up); its centre is at enclosure (25, 0, 7.4). The board spans enclosure x 10 to 40, y −15 to 15, z 5.8 to 7.4. Its posts touch the bottom face.
- **Screw holes** (Ø2.2): H1 board (−10.5, 10.5) = enclosure (14.5, 10.5, 7.4); H2 board (10.5, −10.5) = enclosure (35.5, −10.5, 7.4).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| usb | (−12.5, 0) | top | (12.5, 0, 7.4) | 8.9 × 7.3 mm. USB-C 16P top-mount, mouth at the -x edge (9 o'clock), centre 1.6 above the top face; washable band, so the port gets a silicone plug in the model |
| button | (13, 0) | top | (38, 0, 7.4) | 3.5 × 4.5 mm. right-angle side-push tact switch, plunger facing +x (3 o'clock), centre 1.5 above the top face: the 'I'm awake' button |
| glow_led | (0, −5) | top | (25, −5, 7.4) | 2.2 × 2.2 mm. WS2812B-2020 under the 20 x 20 frosted lens: intensity colour + wake pulse |
| link_led | (0, −11.6) | top | (25, −11.6, 7.4) | 1.6 × 0.8 mm. green 0603 LED under the Ø1.6 link light pipe at 6 o'clock (pipe ends 1.4 above the board: KiCad's 0603 LED model is 1.1 tall) |
| lra | (8, −3) | bottom | (33, −3, 5.8) | 10 × 10 mm. off-board: Ø10 x 2.7 ERM coin motor (was LRA: the ERM needs only a MOSFET, no LRA driver IC) glued to the back plate (skin side), top 0.7 below the bottom face, 2 wires to pads; no bottom-face parts over it |
| battery | (−4.5, 0) | bottom | (20.5, 0, 5.8) | 20 × 25 mm. off-board: 402025 LiPo (~150 mAh) on the back plate, 0.3 below the bottom face (foam pad: it also supports the board's left half); no bottom-face parts; Stage 5 wants 0603 passives on the bottom face too, so the cell needs ~1.0 mm below the bottom face, not 0.3 |

- **Keep-outs** (board x0, y0, x1, y1): antenna (−6.8, 9.4, 6.8, 15).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/003-003/5-electronics/receiver`): the real board in `4-model/model.solidcraft`, without Stage 4's stand-ins R PCB, R USB-C, R Side Switch, R Glow LED, R Link LED.

<!-- fit:end -->

## Rules

What each stage may change without asking (the full version is in CLAUDE.md, "Stages 4 and 5 work together"):

- **Stage 5** may change the board's size, shape, posts and the inside positions of parts and connectors. It edits `fit.json` and adds a request below so Stage 4 follows.
- **Stage 4** may move posts, ribs and internal features, and may grow the enclosure by up to about 10 % in any direction to make room, keeping the concept's look.
- **Ask the hosts first** before anything visible changes: the outer size beyond 10 %, the shape, or where buttons, windows, eyes, ports or speakers sit on the outside.

## Requests

One line each, newest last: `- [open] 5→4: …`. The other stage marks it `[done]` once it's in its model or board, or `[asked hosts]`.

- [open] 5→4 (receiver): board 26 Ø → **30 × 30 R8, parts on both faces** (SIZE.md asks ~1410 mm²; 900 is the most a ~32 mm watch can hold, so 0603 passives go on the bottom too). Holes moved to (−10.5, 10.5) and (10.5, −10.5). USB to (−12.5, 0), button to (13, 0): same 9 and 3 o'clock spots on the outside, case grows to ~35 mm (≤ 10 %). Bottom-face parts are ≤ 1.0 mm tall: please drop the cell and motor to ~1.0 mm below the bottom face (about +0.7 mm case thickness).
- [open] 5→4 (receiver): haptic is an **ERM coin motor Ø10 × 2.7** (not the Ø10 × 3.6 LRA): the ERM needs only a MOSFET, an LRA needs a driver IC. Feature `lra` moved to (8, −3), name kept.
- [open] 5→4 (sensor): board 40 × 18 → **44 × 20 R3, parts on both faces** (SIZE.md asks ~1420 mm²). Holes to (±19.5, −7), USB to (18.5, 0), mic to (−19.5, 5), status LED to (−20, 8). New antenna keep-out (−15.5, 3.5) to (−2.5, 10): the module sits at the front-left with its antenna along the +y edge. Bottom parts ≤ 1.0 mm: the cell needs ~1 mm clearance under the board.
