# 004-004: fit between enclosure and board

The contract between Stage 4 (`4-model/`) and Stage 5 (`5-electronics/`). The numbers live in `fit.json`; this file holds the generated summary, the rules and the request log.

<!-- fit:start: generated from fit.json by tools/fit/fitmd.py. Edit fit.json, not this section -->
## Fit

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/004-004` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 248 × 21.4 mm, R3, 1 thick, parts on both faces.
- **Where:** top face looks +z (up); its centre is at enclosure (0, 0, 6.6). The board spans enclosure x −124 to 124, y −10.7 to 10.7, z 5.6 to 6.6. Its posts touch the bottom face.
- **Screw holes** (Ø2.2): H1 board (−120, 7.5) = enclosure (−120, 7.5, 6.6); H2 board (−120, −7.5) = enclosure (−120, −7.5, 6.6); H3 board (121, 7.5) = enclosure (121, 7.5, 6.6); H4 board (121, −7.5) = enclosure (121, −7.5, 6.6).
- **Rest posts** (no hole): board (−5.5, 0) = enclosure (−5.5, 0, 6.6).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| module | (100, −0.2) | bottom | (100, −0.2, 5.6) | 17.8 × 21 mm. XIAO ESP32-C6 soldered flat on the BOTTOM face (castellations + BAT pads), USB-C toward -y; top of its USB-C 3.2 mm below the module |
| usb | (100, −10.7) | bottom | (100, −10.7, 5.6) | XIAO USB-C mouth at the board's -y edge; its centre is 3.0 mm above the enclosure floor's outside (z 3.0), opening through the gunmetal side wall |
| dome | (−116, 0) | top | (−116, 0, 6.6) | APDS-9960 centred under the faceted dome; deck hole d7 above it |
| button | (−98.5, 0) | top | (−98.5, 0, 6.6) | PTS810 under the porthole plunger (plunger bottom 0.2 above the switch) |
| color | (116.5, 0) | top | (116.5, 0, 6.6) | APDS-9251 under the chrome oval window |
| view | (98, 0) | top | (98, 0, 6.6) | 19 × 16 mm. smoked viewing window in the deck above the XIAO: this patch of the board's top shows, so gold-silk art (a gear?) is welcome; no parts taller than 1 mm |
| cell1 | (−49, 0) | bottom | (−49, 0, 5.6) | 80 × 20 mm. off-board LiPo 4 x 20 x 80 on the floor, 0.3 mm below the board |
| cell2 | (38, 0) | bottom | (38, 0, 5.6) | 80 × 20 mm. off-board LiPo 4 x 20 x 80 on the floor |
| led1 | (−82, 0) | top | (−82, 0, 6.6) |  |
| led2 | (−67.55, 0) | top | (−67.55, 0, 6.6) |  |
| led3 | (−53.09, 0) | top | (−53.09, 0, 6.6) |  |
| led4 | (−38.64, 0) | top | (−38.64, 0, 6.6) |  |
| led5 | (−24.18, 0) | top | (−24.18, 0, 6.6) |  |
| led6 | (−9.73, 0) | top | (−9.73, 0, 6.6) |  |
| led7 | (4.73, 0) | top | (4.73, 0, 6.6) |  |
| led8 | (19.18, 0) | top | (19.18, 0, 6.6) |  |
| led9 | (33.64, 0) | top | (33.64, 0, 6.6) |  |
| led10 | (48.09, 0) | top | (48.09, 0, 6.6) |  |
| led11 | (62.55, 0) | top | (62.55, 0, 6.6) |  |
| led12 | (77, 0) | top | (77, 0, 6.6) |  |

- **Keep-outs** (board x0, y0, x1, y1): antenna (93.5, 7, 106.5, 10.7).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/004-004`): the real board in `4-model/model.solidcraft`, without Stage 4's stand-ins PCB, XIAO, XIAO USB-C, APDS-9960, APDS-9251, Button SW, LED 1, LED 2, LED 3, LED 4, LED 5, LED 6, LED 7, LED 8, LED 9, LED 10, LED 11, LED 12.

<!-- fit:end -->

## Rules

What each stage may change without asking (the full version is in CLAUDE.md, "Stages 4 and 5 work together"):

- **Stage 5** may change the board's size, shape, posts and the inside positions of parts and connectors. It edits `fit.json` and adds a request below so Stage 4 follows.
- **Stage 4** may move posts, ribs and internal features, and may grow the enclosure by up to about 10 % in any direction to make room, keeping the concept's look.
- **Ask the hosts first** before anything visible changes: the outer size beyond 10 %, the shape, or where buttons, windows, eyes, ports or speakers sit on the outside.

## Requests

One line each, newest last: `- [open] 5→4: …`. The other stage marks it `[done]` once it's in its model or board, or `[asked hosts]`.

- [done] 4→5: first fit.json. Board 248 × 21.4, 1.0 thick, top face at z 6.6, 4 M2 holes at (−120, ±7.5) and (121, ±7.5), one rest post at (−5.5, 0) between the cells. **The XIAO goes on the BOTTOM face** (`module` at (100, −0.2), USB-C to the −y edge). With everything on top, its USB-C would sit at z ≈ 9, in the brass deck's rounded top edge with no wall round it. On the bottom, the USB-C centre lands at z 3.0 in the gunmetal base, where the side plug is. The cells only run under the middle (x −89…78), so the bottom face is still bare from x −89 to 78. Antenna keep-out under the XIAO's +y end. Width 21.4 (not 22): the deck's inner walls are ±10.8.
- [done] 4→5: optional: the `view` window (19 × 16 at (98, 0)) shows the board's top face above the XIAO; gold silkscreen art there would make it read as "machinery".
- [done] 4→5: `color` moved to (116.5, 0) and `view` to (98, 0), so the oval and window flanges clear the deck's end wall.
- [done] 5→4 (board-only, no enclosure change): antenna keep-out now starts at board y 7.0 (was 5.0): the XIAO's BAT+/BAT− pads sit at module y +5.5 (y 3.9…6.6 on the board) and need copper. The ceramic antenna is in the XIAO's last ~3 mm (y 7.3…10.3). Nothing else in the enclosure changes.
- [done] 5→4: cell pads (through-hole, the leads come up from the bottom) at x −93 (cell1's tabs at its −x end) and x 81.5 (cell2's tabs at its +x end), both at y 5.5 and 1.9. Please orient the cell stand-ins' tab ends that way and keep the floor clear of a ~1 mm solder fillet on the bottom there.
- [done] 5→4 (noted, no change needed): 0603 passives ≤0.6 mm on the bottom face at x 84…89: nothing of the enclosure's sits there (cell2 ends at 78, its tabs at 81.5 sit at z 3.3; the floor is at z 1.2).
- [done] 5→4 (board-only, no enclosure change): antenna keep-out narrowed to (93.5, 7.0, 106.5, 10.7), the ceramic antenna between the XIAO's pin rows, so tracks can leave its D6 / D7 castellations at the antenna end.
- [done] 5→4 (opening centred z 3.2, 9.4 × 3.6; plug inner face y −12.05; model re-saved): fit check: the XIAO's USB-C overlaps **USB Plug** (2.6 mm³ at (100, −11.8, 3.1)) and **Base** (0.4 mm³ at (100, −11.7, 4.2)). The receptacle (stand-in `tools/kicad/models/Seeed_XIAO_ESP32C6.step`) is 8.94 wide (enclosure x 95.5…104.5), z 1.6…4.8 (centre 3.2, not 3.0: the board is now really 1.0 thick, top at 6.6, and the XIAO's PCB is 0.8), and its mouth reaches y −11.9 (1.2 mm past the XIAO's edge at −10.7). Please move the wall opening to centre z 3.2 with ≥0.2 mm clearance round 8.94 × 3.2, and keep the plug's inner face at y ≤ −12.0. Board unchanged.
- [done] 5→4 (opening now 9.6 × 4.0 at z 3.2, bottom level with the floor at z 1.2; a stadium receptacle stand-in measures 0.31 mm minimum, no contact; model re-saved): fit check PASSES (0 overlaps), but Base touches the XIAO's USB-C at 0.00 mm at (97.13, −11.6, 1.6): the receptacle's lower edge meets the opening's bottom edge right at the base wall's inner face. Please give the opening ≥0.2 mm under z 1.6 through the whole wall depth (y −10.8 … −12.05). The kit's stand-in now has round ends (stadium 8.94 × 3.2, R1.6, ends centred at x 100 ± 2.87), like a real USB-C shell. Board unchanged.
