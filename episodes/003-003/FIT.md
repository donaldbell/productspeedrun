# 003-003: fit between enclosure and board

The contract between Stage 4 (`4-model/`) and Stage 5 (`5-electronics/`). The numbers live in `fit.json`; this file holds the generated summary, the rules and the request log.

<!-- fit:start: generated from fit.json by tools/fit/fitmd.py. Edit fit.json, not this section -->
## Fit

This product has 2 boards, each with its own entry under `boards` in `fit.json`.

### Board: sensor (`5-electronics/sensor/`)

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/003-003` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 44 × 20 mm, R3, 1.6 thick, parts on both faces.
- **Where:** top face looks +z (up); its centre is at enclosure (−40, 0, 10.5). The board spans enclosure x −62 to −18, y −10 to 10, z 8.9 to 10.5. Its posts touch the bottom face.
- **Screw holes** (Ø2.2): H1 board (−19, −7.5) = enclosure (−59, −7.5, 10.5); H2 board (12, −7.5) = enclosure (−28, −7.5, 10.5).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| mic | (−19.5, 3.5) | top | (−59.5, 3.5, 10.5) | 3.5 × 2.65 mm. ICS-43434 I2S MEMS mic (bottom port: port hole through the board) facing the front grille chamber; foam gasket ring between board and grille |
| status_led | (−19.5, 7.5) | top | (−59.5, 7.5, 10.5) | 1.6 × 0.8 mm. green 0603 LED under the front light pipe (pipe ends 1.4 above the board); the pipe's window is the slit beside the grille |
| button | (6, 0) | top | (−34, 0, 10.5) | 6 × 6 mm. 6 x 6 x 4.3 tact switch under the Ø12 top cap: press = test / pair, hold 3 s = on / off |
| usb | (18.32, 0) | top | (−21.68, 0, 10.5) | 8.9 × 7.3 mm. GCT USB4105 USB-C 16P top-mount (footprint centre), mouth flush with the +x board edge, centre 1.6 above the top face; port opening in the back of the shell |
| module | (−9.45, −1.4) | top | (−49.45, −1.4, 10.5) | 13.2 × 16.6 mm. ESP32-C6-MINI-1 footprint origin (body x -16.05..-2.85, y -7..9.6, 2.4 tall), antenna end at the +y edge |

- **Keep-outs** (board x0, y0, x1, y1): antenna (−16.3, 4, −2.45, 10).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/003-003/5-electronics/sensor`): the real board in `4-model/model.solidcraft`, without Stage 4's stand-ins S PCB, S Mic, S Status LED, S Tact Switch, S USB-C.

### Board: receiver (`5-electronics/receiver/`)

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/003-003` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 30 × 30 mm, R8, 1.6 thick, parts on both faces.
- **Where:** top face looks +z (up); its centre is at enclosure (25, 0, 8.1). The board spans enclosure x 10 to 40, y −15 to 15, z 6.5 to 8.1. Its posts touch the top face.
- **Screw holes** (Ø2.2): H1 board (−10.5, 10.5) = enclosure (14.5, 10.5, 8.1); H2 board (10.5, −10.5) = enclosure (35.5, −10.5, 8.1).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| usb | (−11.3, 0) | top | (13.7, 0, 8.1) | 8.9 × 7.3 mm. GCT USB4105 USB-C 16P top-mount (footprint centre; mouth flush with the -x edge at -15), mouth at the -x edge (9 o'clock), centre 1.6 above the top face; washable band, so the port gets a silicone plug in the model |
| button | (12.25, 0) | top | (37.25, 0, 8.1) | 3.5 × 4.5 mm. Panasonic EVQ-PUJ right-angle side-push tact switch (footprint origin; plunger tip at the +x edge, x 15), plunger facing +x (3 o'clock), centre 1.5 above the top face: the 'I'm awake' button |
| glow_led | (0, −5) | top | (25, −5, 8.1) | 2.2 × 2.2 mm. WS2812B-2020 under the 20 x 20 frosted lens: intensity colour + wake pulse |
| link_led | (0, −11.6) | top | (25, −11.6, 8.1) | 1.6 × 0.8 mm. green 0603 LED under the Ø1.6 link light pipe at 6 o'clock (pipe ends 1.4 above the board: KiCad's 0603 LED model is 1.1 tall) |
| lra | (9, −3) | bottom | (34, −3, 6.5) | 10 × 10 mm. off-board: Ø10 x 2.7 ERM coin motor glued to the back plate (skin side), top 2.6 below the bottom face, 2 wires to pads (MOSFET drive) |
| battery | (−6.9, 0) | bottom | (18.1, 0, 6.5) | 20 × 25 mm. off-board: 402025 LiPo (~150 mAh) on the back plate, 1.0 below the bottom face; bottom-face parts <= 1.0 tall over it |
| module | (0.4, 3.6) | top | (25.4, 3.6, 8.1) | 13.2 × 16.6 mm. ESP32-C6-MINI-1 footprint origin (body x -6.2..7, y -2..14.6, 2.4 tall), antenna end at the +y edge |

- **Keep-outs** (board x0, y0, x1, y1): antenna (−6.6, 9.2, 7.4, 15).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/003-003/5-electronics/receiver`): the real board in `4-model/model.solidcraft`, without Stage 4's stand-ins R PCB, R USB-C, R Side Switch, R Glow LED, R Link LED.

<!-- fit:end -->

## Rules

What each stage may change without asking (the full version is in CLAUDE.md, "Stages 4 and 5 work together"):

- **Stage 5** may change the board's size, shape, posts and the inside positions of parts and connectors. It edits `fit.json` and adds a request below so Stage 4 follows.
- **Stage 4** may move posts, ribs and internal features, and may grow the enclosure by up to about 10 % in any direction to make room, keeping the concept's look.
- **Ask the hosts first** before anything visible changes: the outer size beyond 10 %, the shape, or where buttons, windows, eyes, ports or speakers sit on the outside.

## Requests

One line each, newest last: `- [open] 5→4: …`. The other stage marks it `[done]` once it's in its model or board, or `[asked hosts]`.

- [done] 5→4 (receiver): board 26 Ø → **30 × 30 R8, parts on both faces** (SIZE.md asks ~1410 mm²; 900 is the most a ~32 mm watch can hold, so 0603 passives go on the bottom too). Holes moved to (−10.5, 10.5) and (10.5, −10.5). USB to (−12.5, 0), button to (13, 0): same 9 and 3 o'clock spots on the outside, case grows to ~35 mm (≤ 10 %). Bottom-face parts are ≤ 1.0 mm tall: please drop the cell and motor to ~1.0 mm below the bottom face (about +0.7 mm case thickness).
- [done] 5→4 (receiver): haptic is an **ERM coin motor Ø10 × 2.7** (not the Ø10 × 3.6 LRA): the ERM needs only a MOSFET, an LRA needs a driver IC. Feature `lra` moved to (8, −3), name kept.
- [done] 5→4 (sensor): board 40 × 18 → **44 × 20 R3, parts on both faces** (SIZE.md asks ~1420 mm²). Holes to (±19.5, −7), USB to (18.5, 0), mic to (−19.5, 5), status LED to (−20, 8). New antenna keep-out (−15.5, 3.5) to (−2.5, 10): the module sits at the front-left with its antenna along the +y edge. Bottom parts ≤ 1.0 mm: the cell needs ~1 mm clearance under the board.
- [done] 4→5 (receiver): case is still **38 × 38** (it already had room for 30 × 30 R8), now 13.4 tall (+0.8). Board `origin` z 7.4 → **8.1**: cell and motor are 1.0 below the bottom face. **posts_face → "top"**: a back-plate post at (−10.5, 10.5) would sit in the cell, so the board now hangs from two lid posts (Ø3.6) at the same holes. Each post has a Ø1.9 pin through the hole, heat-staked under the board (the stake head is ≤ 0.6 below the bottom face), so keep top-face parts out of a Ø4 circle round each hole. `battery` → (−6.9, 0) and `lra` → (9, −3) so the cell clears the ERM (internal only).
- [done] 4→5 (sensor): board `origin` z 9.8 → **10.5**, so the cell is 1.0 below the bottom face. Nothing visible changes.
- [open] 5→4 (receiver): exact footprint spots: `usb` (−12.5, 0) → **(−11.3, 0)** (mouth still flush with the −x edge), `button` (13, 0) → **(12.25, 0)** (plunger tip at the +x edge), antenna keep-out now (−6.6, 9.2) to (7.4, 15), new feature `module` (0.4, 3.6) for reference. Nothing visible moves.
- [open] 5→4 (sensor): exact footprint spots: `mic` → **(−19.5, 3.5)** (port hole), `status_led` → **(−19.5, 7.5)** (both 1.5 / 0.5 mm from my last numbers, to clear each other), `usb` → **(18.325, 0)** (mouth flush with the +x edge), antenna keep-out now (−17.5, 4) to (−3.7, 10), new feature `module` (−10.7, −1.4) for reference.
- [open] 5→4 (sensor): **posts move**: H1 (−19.5, −7) → **(−19, −7.5)**, H2 (19.5, −7) → **(12, −7.5)** (between the button and the USB-C: at 19.5 the hole hit the USB-C's shell pegs). Module 1.25 mm right to (−9.45, −1.4), antenna keep-out (−16.3, 4) to (−2.45, 10). Nothing visible moves.
