# rev-b: fit between enclosure and board

The contract between Stage 4 (`4-model/`) and Stage 5 (`5-electronics/`). The numbers live in `fit.json`; this file holds the generated summary, the rules and the request log.

<!-- fit:start: generated from fit.json by tools/fit/fitmd.py. Edit fit.json, not this section -->
## Fit

Generated from `fit.json`: edit that file, then run `python3 tools/fit/fitmd.py episodes/rev-b` (the kit's build and the fit check also do it). Board positions are board mm (origin at the board centre, +x right and +y up as seen from the top face); enclosure positions are the enclosure's mm (origin at its centre).

- **Board:** 70 × 45 mm, R9, 1.6 thick, parts on both faces.
- **Where:** top face looks +z (up); its centre is at enclosure (0, 0, 15.1). The board spans enclosure x −35 to 35, y −22.5 to 22.5, z 13.5 to 15.1. Its posts touch the bottom face.
- **Screw holes** (Ø2.2): H1 board (−31, −17) = enclosure (−31, −17, 15.1); H2 board (31, −17) = enclosure (31, −17, 15.1); H3 board (−31, 5) = enclosure (−31, 5, 15.1); H4 board (31, 17) = enclosure (31, 17, 15.1).

| Feature | Board (x, y) | Face | Enclosure (x, y, z) | Note |
|---|---|---|---|---|
| button | (18, 0) | top | (18, 0, 15.1) | 12 × 12 mm. big silence button over SW1, now a 12 x 12 x 4.3 low-profile tact switch (Rev A: 7.3) |
| pir | (−26, 13) | top | (−26, 13, 15.1) | 10.8 × 10.8 mm. Ø10.8 board cutout: the AM312 drops through it onto a boss in the bottom plate (its base 1.9 below the board's underside); legs reach the board by 3 short wires |
| speaker | (0, −11) | top | (0, −11, 15.1) | 21 × 21 mm. Ø20 x 4 mm 8 Ω micro speaker (replaces the BZ1 piezo) on a 0.3 mm foam pad, held down by the lid: no parts in this Ø21 circle; two wire pads beside it |
| eye_led_l | (−17.6, 6.4) | top | (−17.6, 6.4, 15.1) | 1.6 × 0.8 mm. white 0603 LED under the left eye's highlight light pipe (pipe ends 1.4 above the board); flashes with the alarm |
| eye_led_r | (−1.6, 6.4) | top | (−1.6, 6.4, 15.1) | 1.6 × 0.8 mm. white 0603 LED under the right eye's highlight light pipe |
| power_switch | (31.8, −6) | bottom | (31.8, −6, 13.5) | 4.4 × 8.6 mm. C&K OS102011MA1Q right-angle slide switch (body centre); its 4 mm lever leaves the body face at x 34, centre 2.6 mm below the board (enclosure z 10.9), tip flush with the base's outer wall in a thumb pocket; in series with battery + |
| module | (−7, 11.8) | bottom | (−7, 11.8, 13.5) | 18 × 20 mm. suggested: U2 ESP32-C3-WROOM-02 moves to the bottom face so the eye LEDs get the top; antenna end on the +y edge, clear of the cells |
| button_led | (18, 9.2) | top | (18, 9.2, 15.1) | 2.2 × 2.2 mm. WS2812B-2020 RGB LED inside the clear button's footprint (9.2 mm from its centre, beside SW1), lighting it from below |
| amp | (12, −12.5) | top | (12, −12.5, 15.1) | 3 × 3 mm. U3 MAX98357A, now driving the speaker |
| cells | (0, −9.75) | bottom | (0, −9.75, 13.5) | 52 × 23 mm. 2 x AAA in a cradle in the bottom plate, 0.9 mm below the bottom face: no parts here, THT leads clipped to 0.5 |

- **Keep-outs** (board x0, y0, x1, y1): antenna (−18, 15.3, 4, 22.5).
- **Fit check** (`python3 tools/fit/fitcheck.py episodes/rev-b`): the real board in `4-model/model.solidcraft`, without Stage 4's stand-ins PCB, ESP32-C3-WROOM-02, Tact Switch, Switch Plunger, MAX98357A, Eye LED L, Eye LED R, Power Switch, Power Switch Lever, Button LED.

<!-- fit:end -->

## Rules

What each stage may change without asking (the full version is in CLAUDE.md, "Stages 4 and 5 work together"):

- **Stage 5** may change the board's size, shape, posts and the inside positions of parts and connectors. It edits `fit.json` and adds a request below so Stage 4 follows.
- **Stage 4** may move posts, ribs and internal features, and may grow the enclosure by up to about 10 % in any direction to make room, keeping the concept's look.
- **Ask the hosts first** before anything visible changes: the outer size beyond 10 %, the shape, or where buttons, windows, eyes, ports or speakers sit on the outside.

## Requests

One line each, newest last: `- [open] 5→4: …`. The other stage marks it `[done]` once it's in its model or board, or `[asked hosts]`.

- [done] 4→5: Rev B thinner case (26 → 22.5 mm): board moved down 1 mm (`board.origin` z 16.1 → 15.1, underside 13.5). Top-face parts ≤ 4.3 mm tall, and ≤ 3 mm within 1.5 mm of the outline (the lid's inner round comes down to 3.06 mm above the top face at the edge). `faces` is now "both".
- [done] 4→5: H3 moved (−31, 17) → (−31, 5): the PIR now passes below the board and the old post was in its way. Holes are `holes[2]`.
- [done] 4→5: `pir`: Ø10.8 board cutout at (−26, 13). The AM312 drops through it onto a boss in the bottom plate; wire its 3 legs to pads beside the cutout (U4 becomes pads, no footprint body).
- [done] 4→5: new `speaker` (0, −11): BZ1 piezo → Ø20 × 4 mm 8 Ω micro speaker (hosts: "change from piezo to a small speaker"). Keep the Ø21 circle free of parts; 2 wire pads beside it; fit 0 Ω for R12/R13 (or drop them) as the Rev A notes say.
- [done] 4→5: new `eye_led_l` (−17.6, 6.4) and `eye_led_r` (−1.6, 6.4): white 0603 LEDs under the eye light pipes (hosts: "white LEDs in the small dots in the eyes that flash when the alarm goes off"). One GPIO, through a transistor if both run off it. These spots are where U2 sits today, hence the next line.
- [done] 4→5: `module` suggestion: U2 to the bottom face at (−7, 12.5), antenna on the +y edge (`keepouts.antenna` moved with it). Anywhere else is fine too, as long as the two LED spots are free.
- [done] 4→5: new `power_switch` (32.8, −6), bottom face: right-angle SPDT slide switch, body flush with the +x edge, actuator 1.8 mm under the board (enclosure z 11.7) poking into the slider cap in the base's right-end slot. In series with battery + before Q1 (hosts: "a physical on/off switch that disconnects power"). J2's pads at x 30 need to move.
- [done] 4→5: SW1 → 12 × 12 × 4.3 mm low-profile tact switch (was 7.3), plus a 3D model of that height.
- [done] 4→5: new `cells` (0, −9.75), bottom face: 2 × AAA now sit in a cradle 0.9 mm under the board (no holder box). No parts on the bottom face over them, THT leads clipped to 0.5 mm, battery contacts wired to J1.
- [done] 5→4: `power_switch` (32.8, −6) → (31.8, −6): the real part is a C&K OS102011MA1Q, 4.7 mm deep under the board, with a 4 mm lever centred 2.6 mm below it. The lever tip now ends flush with the base's outer wall. The slot, pocket and stand-ins follow it, and the separate slider cap is dropped.
- [done] 5→4: `module` (−7, 12.5) → (−7, 11.8) and `keepouts.antenna` 0.7 mm lower: the module's silkscreen sat 0.1 mm past the board edge.
- [done] 5→4: eye light pipes end 1.4 mm above the board (was 1.0): KiCad's 0603 LED model is 1.1 mm tall.
- Rev B board: DRC 0 / 0 unconnected, fit check PASS (0 overlaps; closest 0.11 mm, bottom plate to board).
- [done] 4→5 and 5→4: new `button_led` (18, 9.2), top face: WS2812B-2020 under the clear button. It has a stand-in in the model ("Button LED"). Fit check PASS.
- [done] 7→5: **VBAT bulk capacitance** (firmware track, `fit.json` unchanged): add 47–100 µF at U1's input beside C1 (10 µF). Wi-Fi TX bursts in setup mode (~0.6 A from 2 V cells) and speaker peaks on tired AAA cells could brown out the C3. The firmware already limits the AP to 8.5 dBm and the amp to ~0.5 W, and skips sound below 1.9 V. Details in `7-firmware/NOTES.md`.
  - Done: C12/C13 2 × 47 µF X5R 1206 (CL31A476MQHNNNE, LCSC C96123, to confirm) on VBAT beside C1 and U1. Routed DRC 0 / 0, fit check PASS.
