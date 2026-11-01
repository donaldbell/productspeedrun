# Backpack Defender Rev B

Based on `episodes/001-demo-1` (Rev A, episode 001).
The hosts' goals and feedback are in `rev.json`; Claude Code records what changed below.

## Changelog

### Enclosure (track "cad", 2026-11-01)

- **Ported to `fit.json`.** Rev A predates the fit kit, so `fit.json` was first written from Rev A's numbers (board 70 × 45 R9 at z 14.5–16.1, holes (±31, ±17), button, PIR, piezo, module). Then `4-model/build_model.py` was changed to read the board, posts and every feature from it through `tools/fit/fitlib.py`. *Why:* CLAUDE.md "Revisions": port first, then change.
- **Thinner: 26 → 22.5 mm (−13 %), same 76 × 51 plan view.** The 2 × AAA now sit in a cradle in the bottom plate instead of a 12 mm holder box. The board drops 1 mm to an underside at 13.5. SW1 goes to a 12 × 12 × 4.3 low-profile switch, so nothing on top is taller than 4.3 mm. *Why:* hosts: "make it thinner, if possible". Going thinner still would mean leaving AAA cells (Ø10.5) for a LiPo (see Still open).
- **Rounder, slicker shell.** The top round is now R7.5 on a 22.5 mm body (a third of the height; Rev A was R7 on 26). There's a 0.6 × 0.8 mm shadow-line reveal where the lid meets the base, so the parting line reads as deliberate. The loop edges are rounded. The front grille slots are gone. *Why:* hosts: "a little slicker, less basic".
- **Triangular carabiner loop.** It replaces the Ø4 charm tab. It's a rounded triangle sticking out about 23 mm on the left end, 6 mm thick, with 4.5 mm webs. A Ø12 circle fits in the hole, which takes the usual backpack carabiner. It is joined into 35 mm of the base's end wall. *Why:* hosts: "a larger, triangular loop … large enough for a carabiner hook".
- **Power slide switch.** A coral slider cap sits in a thumb pocket on the right end (base), and a right-angle SPDT slide switch hangs under the board behind it, in series with battery +. *Why:* hosts: "a physical on/off switch that disconnects power" (also Rev A's open question "No power switch").
- **Speaker instead of piezo.** A Ø20 × 4 mm 8 Ω micro speaker faces up under a 19-hole "flower" grille, between the smile and the button. The lid holds it down on a foam ring and pad. The piezo's 7 holes are gone. *Why:* hosts: "change from piezo to a small speaker" (also Rev A's open question about musical tones).
- **Eye lights.** Each eye's highlight dot is now a white Ø2.56 light pipe through the lid, in a boss that keeps the light from bleeding sideways. Each pipe stops 1 mm above a white 0603 LED on the board. *Why:* hosts: "white LEDs to the small dots in the eyes that flash when the alarm goes off".
- **"PROPERTY OF:" name plate on the back.** "PROPERTY OF:" is in white Arial Rounded, with a 46 × 16.5 mm white write-on panel on the battery door below it for a dark marker. It's modelled as 0.4 mm flush inlays; production would use pad print. It reads when the pebble is turned over like a page. *Why:* hosts.
- **PIR drops through the board.** To keep the purple dome at 3.5 mm proud on the thinner lid, the AM312 now passes through a Ø10.8 board cutout and stands on a tube boss in the bottom plate, with its legs wired to the board. Post H3 moved from (−31, 17) to (−31, 5) to make room.
- **Board-side requests** for all of the above are posted in `FIT.md` (9 lines, 4→5): new board height, H3, PIR cutout, speaker, eye LEDs, module to the bottom face (suggested), power switch, low-profile SW1, no parts over the cells.

## Results

- **Model:** `4-model/model.solidcraft` has 38 bodies: the enclosure and visible parts, plus 11 electronics stand-ins listed in `fit.json` `model.stand_ins` (the speaker, cells and PIR stay in for the fit check). It was exported as `model.step`, `model.stl` and `model.glb` (16 coloured parts, 99.5 × 51 × 26 mm including the loop and the button/dome), and rendered to `iso.png`. Progress shots: `progress-05.png` (shell + lid), `-06` (first full build), `-07` (back with the name plate), `-08` (side profile).
- **Clearance check, all bodies:** no overlaps (86 pairs measured). The smallest gaps are button to lid 0.085 mm (same as Rev A), speaker to the lid's inner round 0.175 mm, PIR dome to lid 0.2 mm, eye light pipes to LEDs 0.2 mm, and SW1 plunger to button 0.3 mm.
- **Not yet run:** the real-board fit check (`tools/fit/fitcheck.py`). It needs the Stage 5 board to follow the requests in `FIT.md`.

## Still open

- **Electronics** (track "electronics"): the 9 requests in `FIT.md` are open. The board needs the speaker pads, eye LEDs + driver, power switch, PIR cutout and wires, H3 move, and probably U2 moved to the bottom face.
- **Sound library** (for the code track): the hosts want "a more interesting library of sounds and melodies … from existing I2S synth and sound libraries". The MAX98357A + speaker can play real audio now. Candidates to try in `7-firmware/`, not yet checked for ESP32-C3 support:
  - ESP8266Audio (WAV/MP3/MIDI/RTTTL over I2S)
  - pschatzmann's arduino-audio-tools, with its STK instruments
  - Mozzi (synth voices)
  - RTTTL ringtone collections for melodies
- **Thinner still:** the next step down (about 18 mm) means a flat LiPo (e.g. 502535) plus USB-C charging instead of AAA. That trades away the "teacher pulls the batteries" disarm, which the power switch now partly covers.
- **Light pipes:** clear PC/PMMA rods, glued in or a two-shot moulding. The real LED and pipe need a brightness test in daylight.
- **Speaker sealing:** the foam ring between the speaker and the lid is assumed, not modelled. A back volume (the space under the speaker) might help bass; check by ear on a prototype.
- **Slide switch part:** the model assumes a ~4.4 × 8.6 × 3.6 right-angle SPDT with its actuator 1.8 mm below the board. Pick the real part and adjust the slot and cap.
- **Fastening and battery door latch:** still open from Rev A.
