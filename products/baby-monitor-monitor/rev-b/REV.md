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

## Results

- **Model:** `4-model/model.solidcraft` (built headless from `build_model.py`, ~13 min, saved with its evaluated cache), `iso.png`, `model.step`, `model.stl`, `model.glb` (20 parts, linear colours, metres). Progress: `blockout-01.png` (pass 1 blockout), `progress-05.png` (watch blockout), `progress-06.png` (sensor section through post H1), `progress-07.png` (back view), `progress-08.png` (side view).
- **Compare** (`4-model/compare.png`, against the previous hero render and the concept): it reads as the same product, and closer to the concept than Rev A on the grille nose, the green bean, the S-swoosh, the button and the pillow watch with its ring lens. Per-feature scores are in `4-model/DESIGN.md`: 8 ✓, 3 partly (teardrop body, asymmetry, back panel).
- **Checks in `build_model.py`** (they fail the build if broken): the 103450 cell clears the side walls at both ends and the middle; the board and its parts clear the walls; walls ≥ 1.15 mm (1.8 nominal); the bezel sits inside the nose face; the USB-C and slider openings sit inside the back face; the button stem has room; the light-pipe bar clears the posts; the watch back plate still fits. Checked by hand against the routed sensor PCB: the light-pipe bar (1.4 above the board, board x −26…−25.2) passes over only U4 (mic, 1.0 tall) and clears C6 and post H1 (0.4 gap).
- **Fit check: not run to completion.** `fitcheck.py` on this folder stops before checking: the boards' 3D model paths don't resolve at revision depth (request in `FIT.md`). On a scratch copy where they do resolve, the sensor's clearance pass ran for over 2 h without finishing (Rev A's took minutes: the spline-trimmed shell meshes heavily), and so did an in-session `inspect.clearance` (32 min, no answer). The enclosure moves nothing the board lines up with, but this is still unverified. Run it once Stage 5 fixes the paths, and expect it to be slow.
- **Pass 2, not built:** steeper fall to the back (heights −1.72: 28.5 … 29.0: 22.0), rear shoulder exponents 2.0–2.2 and back recess inset 3.0. Its full build ran over 60 min without finishing and was stopped, so the model is pass 1. These numbers are the next thing to try, perhaps with fewer stations at the back.

## Still open

- Fit check (see Results).
- The sensor still reads longer and more tube-like than the concept's pebble: the 50 mm 103450 cell sets the length (question for the hosts in `4-model/NOTES.md`). The back recess reads as a big flat panel (pass 2's inset 3.0).
- `SYSTEM.md` is missing in Rev A and Rev B (the product has two devices). Not written in this enclosure pass.
- The status-light pipe is ~22 mm long: it crosses from the board LED at board y +7.5 to the −y cheek. If it looks dim on a real part, Stage 5 could move the LED to the −y half of the board near the front (it's near post H1 and the mic, so it's a layout question).
- Back panel layout: the concept has the slider top-left, a "connect" button top-right and the USB-C below centre. Rev B keeps the board's USB-C and slider side by side (and no connect button, per the hosts' Rev A decision). Moving them is a Stage 5 change.
- The watch is still 12.7 mm thick (concept ~10): set by the cell + board stack (see `4-model/NOTES.md`).
