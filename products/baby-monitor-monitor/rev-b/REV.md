# Baby Monitor Monitor Rev B

Based on `episodes/003-003` (Rev A, episode 003).
The hosts' goals and feedback are in `rev.json`; Claude Code records what changed below.

**Goal (CAD track):** a product enclosure that is a truer representation of the concept art, with its style nuances, complex curves, asymmetry and details. (No host feedback on the enclosure yet.)

## Changelog

### Enclosure (4-model)

- **Wrote `4-model/DESIGN.md`** (Rev A had none). It covers signature features, proportions, silhouettes, colours and "must not become" for both devices, and a score table per compare pass. *Why:* the Revisions rules ask for it, and the goal is about the concept's look.
- **Sensor body re-lofted as a low teardrop pebble.** It now goes through 14 superellipse cross-sections drawn as **fit-point splines** (Rev A: lines and arcs, which read as a rounded box). The nose is round, the crown sits just behind it, and the body falls in one long curve to a rounded back. Body 64 × 44.3 × 29.8 (Rev A 63 × 42.8 × 32.6): 2.8 mm lower and 1.5 mm wider, which is the concept's ratio (L : H ≈ 2.1). *Why:* the goal (concept silhouette, complex curves).
- **Asymmetry:** the −y side (the side the concept and `iso.png` show) is fuller, with a rounder shoulder (superellipse n 2.7). The +y side is 1.4 mm narrower with a tighter shoulder (n 2.2). *Why:* the goal (asymmetry). Rev A had the fuller side away from the camera.
- **Round nose face filled by the grille:** a 24 mm chrome bezel ring (Rev A: 18 mm collar) holds a shallow honeycomb dome. The dome bulges 2.8 mm, flatter than Rev A's 6 mm SM58 ball, as in the concept, and has larger Ø1.6 holes. *Why:* the concept's grille fills the nose.
- **S-curve two-colour swoosh with a chrome trim band.** The lavender side panels sit below a fit-point S-curve (a different curve per side). The curve starts under the bezel, rises to ~60 % of the height toward the back, and wraps the back corners. A 1.5 mm bright trim band runs along its top. Rev A split along a tilted plane. *Why:* the concept's swoosh and highlight line.
- **Status light moved to the concept's kidney-bean window on the −y cheek**, just behind the bezel. Rev A had a straight slit on the nose face beside the grille. The light pipe now runs across under the top wall from the board LED, which does **not** move. The note in `fit.json` was updated and an FYI request posted in `FIT.md`. *Why:* the concept's green bean is a signature detail.
- **Bigger disc button** (Ø13, was Ø12), 1 mm proud, with a domed edge and the concept's centre dimple. It stays over the tact switch at board (6, 0), since moving it forward would hit the module. *Why:* the concept's big disc.
- **Inset back panel:** a 0.6 mm recess in the back cap, inset 2.2 mm from its outline. The USB-C and the slider sit in it, and the slider now stands 0.6 proud of the recess. *Why:* the concept's back view.
- **Board posts made from the cavity:** each post (and its heat-stake pin) is cut out of the cavity loft before hollowing, so it runs exactly from the inside of the curved top wall down to the board. Rev A estimated the wall height. Same positions, same Ø3.6/Ø1.9 sizes.
- **Watch case re-lofted as a pillow:** 7 rounded-rect sections. The sides bulge to 38.6 a third of the way up, and the top edge rolls into a flat 32.6 bezel. Rev A was an extrusion with a 3.5 fillet. The plan at the back plate is unchanged (38, R9), so the cell, board and back plate fit as before. *Why:* the concept's soft, convex watch.
- **Recessed, glowing lens:** a 0.6 mm bezel step round an 18.4 mm lens (was 20, flush and 0.7 proud). The lens sits 0.25 below the bezel, with a lighter 14 mm centre face so its edge reads as the concept's magenta ring. The lens shrank to keep the link-LED dot (board (0, −11.6)) clear of the step. *Why:* the concept's lens.
- **Smaller lugs:** spring bars at y ±21.4, z 4.6 (were ±22, 5). The horns now stand out ~4 mm instead of 5.6 and are lower, so the band seems to tuck under the case. *Why:* the concept's lugs barely show.
- **Fixed the `fitlib` import path** in `build_model.py`. A revision folder sits one level deeper than an episode, so the copied script couldn't find `tools/fit/`.
- **`make_glb.py`** exports the new bodies (`Sensor Trim`, `Lens Face`) with linear colours.

### Snooze bar, bar light and boards (hosts' feedback, round 2)

Hosts' decisions: **keep the sensor's length** (the longer battery life is a bonus for parents). **No connect button:** pairing is a long press of the top button. And: *"make the top button larger and more accessible for sleep-deprived parents who need to push the button in dark conditions… something elongated like an alarm clock snooze bar… illuminated… a clear acrylic button and a color changing LED beneath it to indicate states."*

- **Snooze bar replaces the Ø13 button:** a 30 × 12 clear acrylic bar along the crown. Its top follows the crown 1 mm proud, with R1.8 rounded edges. A flange under the shell retains it, two plunger legs sit on two tacts, and a light leg runs down to an RGB LED. Tap = "I'm awake" (stop the buzz), hold 3 s = test / pair. *Why:* hosts' feedback (bigger, findable in the dark, pressable anywhere).
- **Two tacts in parallel** (SW1 moved (6, 0) → (10, 0); new SW3 at (−2, 0), both on BTN/IO7). *Why:* a long bar rocks on one switch, so a press at either end must still register. The 12 mm spacing is the least that fits the LED between the switch courtyards.
- **RGB bar light:** WS2812B-2020 (LED2) at (4, 0) on IO6. It's fed from the power switch's output through a 1N5819WS (D2), giving ~4.45 V on USB so 3.3 V data reads high; it's dark and draws nothing when switched off. R10 100 Ω on the data line, C10 1 µF, C11 100 nF. *Why:* hosts' feedback (illuminated, colour shows the state). The colour scheme is a firmware proposal in `5-electronics/NOTES.md`.
- **H2 post (12, −7.5) → (12, −9.5)** so the bar's flange clears it. Charger U1 turned landscape to (15.4, −5.6); D1, Q1, R3 and TP1 nudged. *Why:* room for SW1 at x 10 (fit request in `FIT.md`, done on both sides).
- **Sensor board re-placed and re-routed through the kit:** BTN and the status-LED anode got hand pre-routes; the clean route used Freerouting's default 40 passes (10 / 20 left 1–3 nets open). Final: **ERC 0, DRC 0 violations / 0 unconnected / 0 parity.**
- **Receiver board:** circuit unchanged. Its 3D model paths were fixed to revision depth (the routed `.kicad_pcb` edited, not re-routed, to keep the proven board), and the silk now reads "rev B". **DRC 0 / 0 / 0.**
- **Kit: true-size WS2812B-2020 stand-in** (`tools/kicad/models/WS2812B-2020.step`, 2.0 × 2.0 × 0.84). The Würth PLCC4 stand-in is 2.05 tall and made the fit check report a 0.2 mm clash with the bar's light leg that the real 0.84 mm LED doesn't have.
- **Model:** `iso.png`, `model.step`, `model.stl`, `model.glb` and `model.solidcraft` re-exported with the bar; `compare.png` still reads as the product; `progress-09.png` (bar close-up) and `progress-10.png` (section along the bar: legs over both tacts, light leg over the LED).
- **Kit fix (`tools/kicad/tidy_silk.py`):** non-plated holes (the mic's port) now count as obstacles for reference labels. It had put C9's label over the port (Rev A fixed that by hand).

## Results

- **Model:** `4-model/model.solidcraft` (built headless from `build_model.py`, ~13 min, saved with its evaluated cache), `iso.png`, `model.step`, `model.stl`, `model.glb` (20 parts, linear colours, metres). Progress: `blockout-01.png` (pass 1 blockout), `progress-05.png` (watch blockout), `progress-06.png` (sensor section through post H1), `progress-07.png` (back view), `progress-08.png` (side view).
- **Compare** (`4-model/compare.png`, against the previous hero render and the concept): it reads as the same product, and closer to the concept than Rev A on the grille nose, the green bean, the S-swoosh, the button and the pillow watch with its ring lens. Per-feature scores are in `4-model/DESIGN.md`: 8 ✓, 3 partly (teardrop body, asymmetry, back panel).
- **Checks in `build_model.py`** (they fail the build if broken): the 103450 cell clears the side walls at both ends and the middle; the board and its parts clear the walls; walls ≥ 1.15 mm (1.8 nominal); the bezel sits inside the nose face; the USB-C and slider openings sit inside the back face; the button stem has room; the light-pipe bar clears the posts; the watch back plate still fits. Checked by hand against the routed sensor PCB: the light-pipe bar (1.4 above the board, board x −26…−25.2) passes over only U4 (mic, 1.0 tall) and clears C6 and post H1 (0.4 gap).
- **Fit check (round 2): PASS on both boards.** Sensor: 0 overlaps, 5 intended gaps (bar plunger 0.23 above its tact, status pipe 0.23 above its LED, slider notch 0.03 on the lever, posts). Receiver: 0 overlaps, 3 intended gaps. Each takes ~2 h on this enclosure. Details in `5-electronics/<board>/fitcheck.md`.
- **Pass 2, not built:** steeper fall to the back (heights −1.72: 28.5 … 29.0: 22.0), rear shoulder exponents 2.0–2.2 and back recess inset 3.0. Its full build ran over 60 min without finishing and was stopped, so the model is pass 1. These numbers are the next thing to try, perhaps with fewer stations at the back.

## Still open

- The sensor still reads longer and more tube-like than the concept's pebble: the 50 mm 103450 cell sets the length (question for the hosts in `4-model/NOTES.md`). The back recess reads as a big flat panel (pass 2's inset 3.0).
- `SYSTEM.md` is missing in Rev A and Rev B (the product has two devices). Not written in this enclosure pass.
- The status-light pipe is ~22 mm long: it crosses from the board LED at board y +7.5 to the −y cheek. If it looks dim on a real part, Stage 5 could move the LED to the −y half of the board near the front (it's near post H1 and the mic, so it's a layout question).
- Back panel layout: the concept has the slider top-left, a "connect" button top-right and the USB-C below centre. Rev B keeps the board's USB-C and slider side by side (and no connect button, per the hosts' Rev A decision). Moving them is a Stage 5 change.
- The watch is still 12.7 mm thick (concept ~10): set by the cell + board stack (see `4-model/NOTES.md`).
