# 005-005: fit between enclosure and board

The contract between Stage 4 (`4-model/`) and Stage 5 (`5-electronics/`). The numbers live in `fit.json`; this file holds the generated summary, the rules and the request log.

<!-- fit:start: generated from fit.json by tools/fit/fitmd.py. Edit fit.json, not this section -->
## Fit

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/005-005` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 50 × 34 mm, R3, 1 thick, parts on the top face.
- **Where:** top face looks −y; its centre is at enclosure (0, 88.34, 20.35). The board spans enclosure x −25 to 25, y 86.27 to 91.41, z 3.48 to 37.35. Its posts touch the bottom face.
- **Screw holes** (Ø2.2): H1 board (−21, −13) = enclosure (−21, 89.93, 7.45); H2 board (21, −13) = enclosure (21, 89.93, 7.45).
- **Rest posts** (no hole): board (−21, 13) = enclosure (−21, 86.76, 33.25); board (21, 13) = enclosure (21, 86.76, 33.25).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| module | (0, −6.5) | top | (0, 89.14, 13.9) | 17.8 × 21 mm. XIAO nRF52840 Sense soldered flat on the top face (toward the head), USB-C down; its shell overhangs the bottom edge 1.2 |
| usb | (0, −17) | top | (0, 90.42, 3.48) | XIAO USB-C mouth at the board's bottom edge, through the pod's bottom face (reached under the sweatband) |
| mic | (0, −6.5) | top | (0, 89.14, 13.9) | the Sense's PDM mic on the XIAO's top face: felt-covered acoustic opening in the pod's inner face over the module |
| button | (14.5, −12) | top | (14.5, 89.81, 8.44) | PTS810 MODE button: a flexure key in the pod's inner face presses it (under the sweatband) |
| plug_a | (−25, 9.5) | top | (−25, 87.19, 29.78) | JST PH side-entry SMD (S3B-PH-SM4-TB), mouth flush with the -x edge: band half A (wearer's right) |
| plug_b | (25, 9.5) | top | (25, 87.19, 29.78) | JST PH side-entry SMD, mouth flush with the +x edge: band half B (wearer's left) |
| cells | (0, −4) | top | (0, 88.83, 16.38) | cell lead pads at x +-22.4; the two 6 x 34 x 50 LiPo pouches sit off-board in the pod's wings, centred 68 mm of arc either side of the back centre (near ends ~31 mm from the centre, clear of the plugs' mating housings) |

- **Keep-outs** (board x0, y0, x1, y1): antenna (−6.4, 0.5, 6.4, 17).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/005-005`): the real board in `4-model/fit_model.solidcraft`, without Stage 4's stand-ins PCB, XIAO, XIAO USB-C, Plug A, Plug B, Button SW.

<!-- fit:end -->

## Rules

What each stage may change without asking (the full version is in CLAUDE.md, "Stages 4 and 5 work together"):

- **Stage 5** may change the board's size, shape, posts and the inside positions of parts and connectors. It edits `fit.json` and adds a request below so Stage 4 follows.
- **Stage 4** may move posts, ribs and internal features, and may grow the enclosure by up to about 10 % in any direction to make room, keeping the concept's look.
- **Ask the hosts first** before anything visible changes: the outer size beyond 10 %, the shape, or where buttons, windows, eyes, ports or speakers sit on the outside.

## Requests

One line each, newest last: `- [open] 5→4: …`. The other stage marks it `[done]` once it's in its model or board, or `[asked hosts]`.

- [done] 5→4 (chat, before fit.json existed): board 50 × 34 R3 1.0, faces top, holes (±21, −13), module/usb/button/plug_a/plug_b/cells/antenna as sent. All in the first fit.json.
- [done] 4→5: fit check design is `4-model/fit_model.solidcraft` (no louvres or pixel tiles); cells centred ±68 mm of arc. Stage 5 ran the fit check against it: PASS, 0 overlaps.
