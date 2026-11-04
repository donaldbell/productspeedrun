# 003-003: fit between enclosure and board

The contract between Stage 4 (`4-model/`) and Stage 5 (`5-electronics/`). The numbers live in `fit.json`; this file holds the generated summary, the rules and the request log.

<!-- fit:start: generated from fit.json by tools/fit/fitmd.py. Edit fit.json, not this section -->
## Fit

This product has 2 boards, each with its own entry under `boards` in `fit.json`.

### Board: sensor (`5-electronics/sensor/`)

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/003-003` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 52 × 24 mm, R3, 1.6 thick, parts on both faces.
- **Where:** top face looks +z (up); its centre is at enclosure (−40, 0, 14.5). The board spans enclosure x −66 to −14, y −12 to 12, z 12.9 to 14.5. Its posts touch the top face.
- **Screw holes** (Ø2.2): H1 board (−23, −7.5) = enclosure (−63, −7.5, 14.5); H2 board (12, −7.5) = enclosure (−28, −7.5, 14.5).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| mic | (−23.5, 3.5) | top | (−63.5, 3.5, 14.5) | 3.5 × 2.65 mm. ICS-43434 I2S MEMS mic (bottom port: port hole through the board) facing the front grille chamber; foam gasket ring between board and grille |
| status_led | (−23.5, 7.5) | top | (−63.5, 7.5, 14.5) | 1.6 × 0.8 mm. green 0603 LED under the front light pipe (pipe ends 1.4 above the board); the pipe's window is the slit beside the grille |
| button | (6, 0) | top | (−34, 0, 14.5) | 6 × 6 mm. 6 x 6 x 5.0 tact switch (XKB 1TS009, plunger top 5.0 above the top face) under the Ø12 top cap: tap = "I'm awake" (stops the watch buzzing), hold 3 s = test / pair |
| usb | (22.32, −5.5) | top | (−17.68, −5.5, 14.5) | 8.9 × 7.3 mm. GCT USB4105 USB-C 16P top-mount (footprint centre), mouth flush with the +x board edge (x 26), centre 1.6 above the top face. Main power input (plugged in) and charges the 103450 cell |
| module | (−13.45, 0.6) | top | (−53.45, 0.6, 14.5) | 13.2 × 16.6 mm. ESP32-C6-MINI-1 footprint origin (body x -20.05..-6.85, y -5..11.6, 2.4 tall), antenna end at the +y edge |
| power_switch | (22.55, 6.5) | top | (−17.45, 6.5, 14.5) | 3.3 × 6.7 mm. C&K PCM12SMTR right-angle SMD SPDT slide (footprint origin; body x 21.55..24.15, y 3.15..9.85, 1.5 tall). Lever 1.3 wide x 1.55 long, centre ~0.8 above the top face, tip 0.3 inside the +x board edge (x 25.7), slides along y (travel ~1.5 mm, centre at y 6.5): the back wall needs a slider cap that engages the lever |
| cell | (0, 0) | bottom | (−40, 0, 12.9) | 50 × 34 mm. off-board: 103450 LiPo (10 x 34 x 50, ~2000 mAh) on the bottom plate, 1.0 below the bottom face |

- **Keep-outs** (board x0, y0, x1, y1): antenna (−20.3, 6, −6.6, 12).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/003-003/5-electronics/sensor`): the real board in `4-model/model.solidcraft`, without Stage 4's stand-ins S PCB, S Mic, S Status LED, S Tact Switch, S USB-C, S Power Switch, S Switch Lever.

### Board: receiver (`5-electronics/receiver/`)

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/003-003` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 30 × 30 mm, R8, 1.6 thick, parts on both faces.
- **Where:** top face looks +z (up); its centre is at enclosure (25, 0, 8.1). The board spans enclosure x 10 to 40, y −15 to 15, z 6.5 to 8.1. Its posts touch the top face.
- **Screw holes** (Ø2.2): H1 board (−10.5, 10.5) = enclosure (14.5, 10.5, 8.1); H2 board (10.5, −10.5) = enclosure (35.5, −10.5, 8.1).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| glow_led | (0, −5) | top | (25, −5, 8.1) | 2.2 × 2.2 mm. WS2812B-2020 under the 20 x 20 frosted lens: intensity colour + wake pulse |
| link_led | (0, −11.6) | top | (25, −11.6, 8.1) | 1.6 × 0.8 mm. green 0603 LED under the Ø1.6 link light pipe at 6 o'clock (pipe ends 1.4 above the board: KiCad's 0603 LED model is 1.1 tall) |
| lra | (9, 3) | bottom | (34, 3, 6.5) | 10 × 10 mm. off-board: Ø10 x 2.7 ERM coin motor glued to the back plate (skin side), top 2.6 below the bottom face, 2 wires to pads (MOSFET drive) |
| battery | (−6.9, 0) | bottom | (18.1, 0, 6.5) | 20 × 25 mm. off-board: 402025 LiPo (~150 mAh) on the back plate, 1.0 below the bottom face; bottom-face parts <= 1.0 tall over it |
| module | (0.4, 3.6) | top | (25.4, 3.6, 8.1) | 13.2 × 16.6 mm. ESP32-C6-MINI-1 footprint origin (body x -6.2..7, y -2..14.6, 2.4 tall), antenna end at the +y edge |
| pogo_pos | (5.5, −10) | bottom | (30.5, −10, 6.5) | 2 × 2 mm. spring pogo pin (bottom face, ~5 mm) pressing on a gold contact moulded into the back plate; the magnetic USB charger clips onto the back |
| pogo_neg | (13, −5) | bottom | (38, −5, 6.5) | 2 × 2 mm. second pogo pin; two Ø3 x 1 magnets in the back plate at board (-1, -13) and (13, -13) align the charger |

- **Keep-outs** (board x0, y0, x1, y1): antenna (−6.6, 9.2, 7.4, 15).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/003-003/5-electronics/receiver`): the real board in `4-model/model.solidcraft`, without Stage 4's stand-ins R PCB, R Glow LED, R Link LED, R Pogo +, R Pogo -.

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
- [done] 5→4 (receiver): exact footprint spots: `usb` (−12.5, 0) → **(−11.3, 0)** (mouth still flush with the −x edge), `button` (13, 0) → **(12.25, 0)** (plunger tip at the +x edge), antenna keep-out now (−6.6, 9.2) to (7.4, 15), new feature `module` (0.4, 3.6) for reference. Nothing visible moves.
- [done] 5→4 (sensor): exact footprint spots: `mic` → **(−19.5, 3.5)** (port hole), `status_led` → **(−19.5, 7.5)** (both 1.5 / 0.5 mm from my last numbers, to clear each other), `usb` → **(18.325, 0)** (mouth flush with the +x edge), antenna keep-out now (−17.5, 4) to (−3.7, 10), new feature `module` (−10.7, −1.4) for reference.
- [done] 5→4 (sensor): **posts move**: H1 (−19.5, −7) → **(−19, −7.5)**, H2 (19.5, −7) → **(12, −7.5)** (between the button and the USB-C: at 19.5 the hole hit the USB-C's shell pegs). Module 1.25 mm right to (−9.45, −1.4), antenna keep-out (−16.3, 4) to (−2.45, 10). Nothing visible moves.
- [done] 5→4 (receiver, by message): the awake button cap went into the EVQ-PUJ switch. Its inner face now sits 0.1 off the board's +x edge (enclosure x 40.1).
- [done] 4→5 (sensor): **posts_face → "top"**: with H2 at (12, −7.5) a floor post would go through the cell (602530, x ±15), so the sensor board also hangs from two Ø3.6 posts in the upper shell. Each has a Ø1.9 heat-stake pin through the hole (stake head ≤ 0.6 below the bottom face). Keep top-face parts out of a Ø4 circle round each hole. H2's post clears the button cap's flange by 0.6.
- [done] 5→4 (sensor): fit check FAIL, 1 overlap: the tact switch is **6 × 6 × 5.0** (1TS009, plunger top 5.0 above the board's top face), not 4.3, so its plunger runs 3.7 mm³ into the Sensor Button's stem at board (6, 0). Please raise the button's underside to ~5.05 above the top face (enclosure z ≥ 15.55). Inside only, nothing visible changes. Everything else clears.
- [done] 4→5 (both, **hosts' decisions**). (1) The sensor runs on a 103450 LiPo (2000 mAh, so it works unplugged for camping), and USB-C is the main power input and charges it. (2) The sensor gets a power slide switch. Its top button is now the "I'm awake" button: tap = ack, hold = test/pair. (3) **The watch has no button and no USB** (waterproof; nothing to press by accident in bed). It charges through two pogo pins onto contacts in the back plate, with a magnetic clip-on charger.
  - sensor: the bean grows to 60 × 42 × 28. I've grown the board to **52 × 24** so it fills the length: front parts −4, back parts +4, and module and keep-out −4 in x. Origin z is **14.5** (cell 10 thick + 1.0). H1 → (−23, −7.5); H2 stays at (12, −7.5). `usb` → (22.325, −5.5) and new `power_switch` (23.8, 6.5) sit side by side in the back. Please confirm the switch part and its lever height. The new size is provisional, so resize as you need (the cavity holds up to ~54 × 34).
  - receiver: `usb` and `button` removed. New `pogo_pos` (5.5, −10) and `pogo_neg` (14, −5) on the bottom face (spring pins ~5 mm down to the back plate). `lra` → (9, 3) to make room. The case is 0.7 mm thinner (12.7), so **top-face parts ≤ 2.6 mm**. The firmware has no power switch: it sleeps when the sensor goes quiet.
- [done] 5→4 (receiver): `pogo_neg` (14, −5) → **(13, −5)**: at 14 the Ø2 pad is 0 mm from the board edge and inside the R8 corner's copper clearance. Its back-plate contact moves 1 mm toward the centre; please move that contact (and the magnet if it's keyed to it). Pogo pins are a Ø1.8 × 5.0 stand-in (`tools/kicad/models/PogoPin_D1.8mm_H5.0mm.step`, e.g. Mill-Max 0907 SMD), standing on the bottom face.
- [done] 5→4 (sensor): power switch is a **C&K PCM12SMTR** (right-angle SMD SPDT; KiCad has its footprint and model), not the OS102011. Footprint origin `power_switch` (22.55, 6.5): body x 21.55..24.15, y 3.15..9.85, 1.5 tall; lever 1.3 wide × 1.55 long, centre ~0.8 above the top face, tip 0.3 inside the board edge (x 25.7), slides along y (~1.5 mm travel). The back wall needs a slider cap that reaches in 4 mm to the lever. Module moved up 2 mm to (−13.45, 0.6) so its antenna is on the +y edge; keep-out (−20.3, 6) to (−6.6, 12).
- [done] 5→4 (sensor): fit check FAIL, 1 overlap (0.22 mm³): the PCM12's lever runs into the Switch Slider at board (25.3, 5.5), 0.9 above the top face. The KiCad model has the lever at one end of its travel: **lever y 5.1..6.4 (centre 5.75), not centred on the switch (6.5)**. Please centre the slider's notch on y 5.75 (1.7 wide → y 4.9..6.6), keeping x and z as they are. Inside only. The receiver passes.

