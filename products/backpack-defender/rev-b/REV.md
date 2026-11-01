# Backpack Defender Rev B

Based on `episodes/001-demo-1` (Rev A, episode 001).
The hosts' goals and feedback are in `rev.json`; Claude Code records what changed below.

## Changelog

### Enclosure (track "cad", 2026-11-01)

- **Ported to `fit.json`.** Rev A predates the fit kit, so `fit.json` was first written from Rev A's numbers (board 70 × 45 R9 at z 14.5–16.1, holes (±31, ±17), button, PIR, piezo, module). Then `4-model/build_model.py` was changed to read the board, posts and every feature from it through `tools/fit/fitlib.py`. *Why:* CLAUDE.md "Revisions": port first, then change.
- **Thinner: 26 → 22.5 mm (−13 %), same 76 × 51 plan view.** The 2 × AAA now sit in a cradle in the bottom plate instead of a 12 mm holder box. The board drops 1 mm to an underside at 13.5. SW1 goes to a 12 × 12 × 4.3 low-profile switch, so nothing on top is taller than 4.3 mm. *Why:* hosts: "make it thinner, if possible". Going thinner still would mean leaving AAA cells (Ø10.5) for a LiPo (see Still open).
- **Rounder, slicker shell.** The top round is now R7.5 on a 22.5 mm body (a third of the height; Rev A was R7 on 26). There's a 0.6 × 0.8 mm shadow-line reveal where the lid meets the base, so the parting line reads as deliberate. The loop edges are rounded. The front grille slots are gone. *Why:* hosts: "a little slicker, less basic".
- **Triangular carabiner loop.** It replaces the Ø4 charm tab. It's a rounded triangle sticking out about 23 mm on the left end, 6 mm thick, with 4.5 mm webs. A Ø12 circle fits in the hole, which takes the usual backpack carabiner. It is joined into 35 mm of the base's end wall. *Why:* hosts: "a larger, triangular loop … large enough for a carabiner hook".
- **Power slide switch.** A C&K OS102011MA1Q right-angle slide switch hangs under the board, in series with battery +. Its 4 mm lever comes out through a slot in the base's right end and ends flush with the wall, inside a thumb pocket. (The first pass had a separate slider cap; the real part's lever made it unnecessary.) *Why:* hosts: "a physical on/off switch that disconnects power" (also Rev A's open question "No power switch").
- **Speaker instead of piezo.** A Ø20 × 4 mm 8 Ω micro speaker faces up under a 19-hole "flower" grille, between the smile and the button. The lid holds it down on a foam ring and pad. The piezo's 7 holes are gone. *Why:* hosts: "change from piezo to a small speaker" (also Rev A's open question about musical tones).
- **No more pink cheeks.** The two pink cheek inlays and their lid pockets are gone, so the face is just the eyes, the smile and the speaker grille. *Why:* hosts: "do away with the pink printed dimples on the face".
- **Clear dichroic (or glitter) silence button.** It replaces the coral one, with the same size, dome and captive flange. The hosts' sample is clear arcade-style buttons with a rainbow dichroic finish.
  - **CAD:** the button is pale and 80 % opaque, so `iso.png` shows a frosted clear dome for the render while keeping its shape.
  - **`model.glb`:** the button uses glTF's transmission, IOR and iridescence material extensions, which `<model-viewer>` renders as a clear dome with a colour-shifting sheen. A viewer without those extensions shows a pale button instead.
  - **Making it:** clear PC or PMMA with either glitter flakes in the resin (common, cheap) or a dichroic film insert-moulded on top (IML) or a PVD coating. The sample looks like the film/coating route.
  - *Why:* hosts: "a custom clear option in the same size and style with either glitter in the plastic or a kind of dichroic effect".
- **Eye lights.** Each eye's highlight dot is now a white Ø2.56 light pipe through the lid, in a boss that keeps the light from bleeding sideways. Each pipe stops 1 mm above a white 0603 LED on the board. *Why:* hosts: "white LEDs to the small dots in the eyes that flash when the alarm goes off".
- **"PROPERTY OF:" name plate on the back.** "PROPERTY OF:" is in white Arial Rounded, with a 46 × 16.5 mm white write-on panel on the battery door below it for a dark marker. It's modelled as 0.4 mm flush inlays; production would use pad print. It reads when the pebble is turned over like a page. *Why:* hosts.
- **PIR drops through the board.** To keep the purple dome at 3.5 mm proud on the thinner lid, the AM312 now passes through a Ø10.8 board cutout and stands on a tube boss in the bottom plate, with its legs wired to the board. Post H3 moved from (−31, 17) to (−31, 5) to make room.
- **Board-side requests** for all of the above are posted in `FIT.md` (9 lines, 4→5): new board height, H3, PIR cutout, speaker, eye LEDs, module to the bottom face (suggested), power switch, low-profile SW1, no parts over the cells. All are done.

### Electronics (track "electronics", 2026-11-01)

- **Ported to the kit.** `5-electronics/src/design.py` and `layout.py` were copied from `tools/kicad/example/` (Rev A), then changed. Everything shared is read from `fit.json`. *Why:* CLAUDE.md "Revisions".
- **SW2 power switch** (C&K OS102011MA1Q, bottom face) between the cells and Q1. *Why:* hosts.
- **Piezo → speaker:** BZ1, R12 and R13 are gone. J3 pads take a 20 mm 8 Ω speaker straight from the MAX98357A. *Why:* hosts.
- **White eye LEDs:** D1/D2 0603s with R14/R15 47 Ω, switched by Q2 AO3400A on IO10 (a spare module pin). R16 keeps them off at boot. *Why:* hosts.
- **AM312 off-board:** it drops through the board's Ø10.8 cutout onto the case boss and is wired to J4. *Why:* the thinner case.
- **SW1 is 12 × 12 × 4.3** low profile, with its own 3D model (`lib/3d/`, made in SolidCraft, because KiCad ships only an 8.5 mm one). *Why:* the thinner case.
- **U2 module on the bottom face**, so the top is free for the eye LEDs.
- **J2 is a Tag-Connect TC2030 pad.** Rev A's 8.5 mm header model would hit the lid.
- **Colour-changing button glow:** LED1, a WS2812B-2020 addressable RGB LED (the kind on ESP32-C3 dev boards), sits under the clear button beside SW1.
  - Q3 (AO3401A) cuts its supply when it's off, because a dark WS2812 draws ~1 mA.
  - Data on IO20, power on IO21 (both freed from UART0). IO8 was avoided because its boot pull-up would leak into the unpowered LED.
  - Boost switch node pre-routed (`PREROUTE`), as in Rev A, after Freerouting missed it three times.
  - *Why:* hosts: "a small, colour changing LED on the PCB near the button to help illuminate it from inside". The colour and a rainbow colour-wheel option are picked on the same AP-mode settings page as the alarm sound (see `7-firmware/BRIEF.md`).
- **Two kit improvements** (`tools/kicad/`, noted in its README): `CUTOUTS` for round holes through a board, and a 47 Ω resistor entry. The kit's `selftest.sh place` still passes.
- **Back to the enclosure:** fit.json `power_switch` moved to (31.8, −6) for the real switch, the module moved 0.7 mm toward the front, and the eye light pipes now stop 1.4 mm above the board. The enclosure was rebuilt for all three. Logged as done in `FIT.md`.

## Results

- **Model:** `4-model/model.solidcraft` has 36 bodies: the enclosure and visible parts, plus 12 electronics stand-ins listed in `fit.json` `model.stand_ins` (the speaker, cells and PIR stay in for the fit check). It was exported as `model.step`, `model.stl` and `model.glb` (13 coloured parts, 99.5 × 51 × 26 mm including the loop and the button/dome), and rendered to `iso.png`. Progress shots: `progress-05.png` (shell + lid), `-06` (first full build), `-07` (back with the name plate), `-08` (side profile), `-09` (face without cheeks).
- **Clearance check, all bodies:** no overlaps (86 pairs measured). The smallest gaps are button to lid 0.085 mm (same as Rev A), speaker to the lid's inner round 0.175 mm, PIR dome to lid 0.2 mm, eye light pipes to LEDs 0.2 mm, and SW1 plunger to button 0.3 mm.
- **Board:**
  - ERC: 0 violations.
  - DRC: **0 violations, 0 unconnected**, including the button LED (with the boost pre-route).
  - SIZE.md asks for 2391 mm². The 70 × 45 board has about 3080 mm².
- **Fit check** (real routed board in the enclosure): **PASS**, 0 overlaps, re-run after the button LED was added.
  - The closest gaps are bottom plate to board 0.11 mm, eye light pipe to LED 0.20 mm, button to SW1 0.20 mm, base to the switch lever 0.27 mm, and speaker to board 0.28 mm.
  - It took two fixes to get there: my SW1 model's pins reached into a cell (the real leads are clipped), and KiCad's LED model is 1.1 mm tall.

## Still open

- **Part numbers to confirm before ordering:** the LCSC numbers I added are KT-0603W white LED C2290 and 47 Ω C23182. The TS-1212-4.3 MPN for SW1 also needs checking against a real low-profile 12 mm switch.
- **White LEDs from 3.3 V:** with a white LED's Vf around 2.9 V there is little headroom, so the brightness depends on the LED batch. Try it on the bench; a 5 V rail isn't worth adding for this.
- **Firmware:** `7-firmware/BRIEF.md` sums up what the firmware must do (pins, states, settings page, sounds) for the code track.
- **Wires:** the PIR and speaker wires, and the cell-contact wires to J1, need routing and strain relief inside the case.
- **Sound library** (for the code track): the hosts want "a more interesting library of sounds and melodies … from existing I2S synth and sound libraries". The MAX98357A + speaker can play real audio now. Candidates to try in `7-firmware/`, not yet checked for ESP32-C3 support:
  - ESP8266Audio (WAV/MP3/MIDI/RTTTL over I2S)
  - pschatzmann's arduino-audio-tools, with its STK instruments
  - Mozzi (synth voices)
  - RTTTL ringtone collections for melodies
- **Thinner still:** the next step down (about 18 mm) means a flat LiPo (e.g. 502535) plus USB-C charging instead of AAA. That trades away the "teacher pulls the batteries" disarm, which the power switch now partly covers.
- **Light pipes:** clear PC/PMMA rods, glued in or a two-shot moulding. The real LED and pipe need a brightness test in daylight.
- **Speaker sealing:** the foam ring between the speaker and the lid is assumed, not modelled. A back volume (the space under the speaker) might help bass; check by ear on a prototype.
- **Slide switch feel:** the OS102011MA1Q lever ends flush with the wall, in a 0.6 mm pocket. Check that a child's thumb can move it; if not, add a press-on cap.
- **Clear button, what shows through:** you can see SW1 (black) and the board through a clear button. Glitter hides it best. With a dichroic finish, a white or silver disc under the button (a sticker on SW1's top, or a frosted inner face) keeps it clean. An LED under the button that lights the glitter would be a nice touch, but it needs a board change.
- **Hero render:** the console makes it from `iso.png` and the concept art. Suggested words for its prompt: "the big round button is clear acrylic with a rainbow dichroic / iridescent finish (pink, gold, green and blue shifting with the angle, like a holographic arcade button), glossy, with fine iridescent glitter suspended inside".
- **Fastening and battery door latch:** still open from Rev A.
