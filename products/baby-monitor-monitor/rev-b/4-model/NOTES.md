# Baby Monitor Monitor Rev B: enclosure notes

## Rev B summary (start here)

**Done:** the enclosure's outer form was reworked toward the concept art (goal in `../rev.json`), keeping every board position in `../fit.json`. `DESIGN.md` is the design read and the per-feature score; `../REV.md` is the changelog. In short:

- The sensor is a fit-point-spline loft (a low teardrop with an asymmetric shoulder), with a round bezel nose and a shallow honeycomb dome. It has an S-curve lavender swoosh with a chrome trim band, a kidney-bean status light on the −y cheek, a Ø13 dimpled button and an inset back panel. The body is 64 × 44.3 × 29.8.
- The watch is a lofted pillow case with a stepped bezel, a recessed two-tone lens and smaller lugs.
- Outputs: `model.solidcraft` (saved with its evaluated cache), `iso.png`, `model.step`, `model.stl`, `model.glb`, `compare.png`, and `blockout-01.png` with `progress-05…08.png`.

**Left / open:** the sensor still reads longer and more tube-like than the concept's pebble (the 50 mm cell sets the length), and the back recess is too big. A pass 2 with a steeper fall and a smaller recess was written but ran over an hour without finishing and was stopped, so the model is pass 1. Pass 2's numbers are in `../REV.md`. Two requests to Stage 5 are open in `../FIT.md`. **The fit check has not been run to completion** on Rev B: the board model paths don't resolve at revision depth (that's one of the requests), and on a scratch copy the clearance pass ran over 2 h. See `../REV.md`.

**Questions for the hosts:** none blocking. Both of these could change the look:

1. Should the sensor shorten toward the concept's pebble? That needs a shorter cell than the 103450 (e.g. a 103040, ~1300 mAh, ~2 nights unplugged).
2. The concept's back has a "connect" button that Rev A dropped. Keep it dropped?

### Solidcraft findings this pass (for `tools/form/README.md`)

| Tried | Result |
|---|---|
| Loft through 14 sections, each a `sketch.spline.fit_point` superellipse + base line | Works, and it's fast (0.6 s on its own). The surface is smooth both ways: far less boxy than lines + arcs. |
| Same with 41 points per section | Booleans against it took ~160 s each. **With 21 points: 8 s.** Keep spline sections light. |
| Cutting a window with a body clipped to the same skin (pipe = prism ∩ shell, then shell − pipe) | Fails ("no result"): coincident faces. Cut with a second, unclipped prism instead. |
| Two-lump tool body (both side panels in one body) for an intersect | "Intersection is empty". Intersect each side on its own, then join. |
| Trim band = (shell ∩ band tool) − lavender piece | Fails: shared skin. Make every piece from the original shell with its own prism (below the curve / band between two curves / cutter under the higher curve). |
| Swoosh cutter whose flat inner face (\|y\| = 15) ran nearly tangent to the nose round-over | The cut was refused as unreliable. At \|y\| = 12 it worked. |
| `body.rename` after heavy booleans | ~3 min per rename (it re-evaluates the features that name the body). Name bodies at creation instead. |
| Opening a finished design to render or export | The first render or export re-tessellates the spline-trimmed faces: ~15 min here (CLI `snapshot --in` and MCP alike). In the MCP session later views are instant, so open once and take every view and export there. `file.save_as {cache: true}` at the end of the build script skips the rebuild on open. |
| Full build | ~13 min headless (mostly the swoosh and hollow booleans). Pass 2 (rear exponents 2.0–2.2, recess inset 3.0) ran > 60 min and was stopped. |

---

# Rev A notes (as aired, kept for reference; Rev B changes are in `../REV.md`)

## 003 Baby Monitor Monitor: Stage 4 model notes

Two devices in one design (`model.solidcraft`), side by side on z 0:

- **Sensor** ("Wireless Mic Sensor"), centred at design x −40. It sits next to (or is VHB-taped onto) the parents' existing monitor and listens to its speaker. It's also where the parent taps **"I'm awake"**.
- **Receiver** ("Wearable Haptic Receiver"), centred at design x +25. A sealed buzzer, worn on the wrist or ankle on a replaceable 20 mm elastic band.

The concept art draws the sensor at ~50 × 24 mm and the watch at 32 × 32 × 10 mm. Those numbers don't come from real parts, so the sizes below are worked out from the parts list instead (Stage 5 picked ESP32-C6-MINI-1 modules; LiPo cells, ERM motor, MEMS mic, USB-C, switches).

## Hosts' decisions (after the first pass)

- **Sensor top button:** tap = "I'm awake" (stops the buzzing), hold = test/pair.
- **Sensor power:** a slide switch to turn it off. USB-C is the main power input (plugged in by the monitor) and also charges a built-in cell for unplugged use (camping, travel). Cell: **103450 flat LiPo, ~2000 mAh, about 3 nights unplugged.** It was picked over an 18650, which would have stretched the sensor to ~78 mm.
- **Watch: no button and no USB**, so it can be waterproof and there's nothing to press by accident in bed. It charges through **two sealed contacts on the back** that a magnetic clip-on USB charger snaps onto (fitness-band style), picked over Qi, which would add ~1 mm and a receiver IC.

## Design language

Y2K gadget: pearl/chrome-look white shells and a lavender accent piece. It borrows Oakley's swoosh parting line, Aibo-style soft lozenges, a MiniDisc-style dark grille disc, and a glowing magenta "Winamp" lens on the watch. Shells are moulded PC/ABS. The chrome look must be **NCVM** (non-conductive vacuum metallising) or pearl paint, because real metal plating would block the 2.4 GHz antennas.

## Sensor: 63 × 43 × 33 mm "mouse" body + SM58 cage (~69 mm long overall)

Second pass, after the hosts asked for the concept's swooping, asymmetric, gamer-mouse form and a bulging stage-mic grille. The concept art drives the shape: the nose is tall and round, the crown sits just behind it and sweeps down to a lower back, and a lavender panel sweeps up the lower sides.

| Part | Plan |
|---|---|
| Body | **Lofted through 12 cross-sections**. The nose rounds over in four quick steps. The crown peaks at 32.6 mm just behind the grille and falls to 22 mm at the flat back. It's asymmetric: the right side is fuller with a soft R14 crown edge, and the left (thumb) side is narrower with a tighter R10 edge. Walls are 1.8 mm, hollowed by a second, inset loft. |
| Swoosh | The shell is split along a plane tilted front-to-back (z 2.5 at the nose → 18 at the back) and slightly side-to-side, so the **lavender lower piece** sweeps up toward the back and sits higher on one side than the other. |
| Base | A 1.8 mm dark-grey foot slab under the whole body, with a **VHB pad** under that. |
| Nose | An **SM58-style grille**: a chrome collar ring stands ~1.2 mm proud of the nose, carrying a **domed honeycomb ball cage** (R10.2, bulging ~6 mm). It tells you at a glance where the mic is. A green **status slit** (1.2 × 4.8) sits beside it on the nose face, fed by a light pipe. |
| Top | Ø12 **"I'm awake" button** on the crown (tap = ack, hold = test/pair) over a 6 × 6 × 5 tact switch. |
| Back | Flat back face: **USB-C** (power + charging) and a lavender **power slider** that reaches in to the PCM12 switch's short lever. |
| Inside | 103450 LiPo (10 × 34 × 50) on the base. A 52 × 24 board hangs from two posts in the crown with heat-staked pins, 1.0 mm above the cell, top face 14.5 mm up. The mic sits at the board's front edge, behind the cage. |

Tried and dropped (SolidCraft limits, worth knowing for Rev B):
- An extruded plan with a filleted crown: the fillet ran 5 min, then failed.
- `solid.shell` on the loft: it can't offset freeform faces, hence the inset cavity loft.
- A curved (cylindrical) swoosh split: "section does not close".
- A spherical thumb dimple on the left: the cavity cut failed where the sphere met the swoosh face.

The grille and slit are kept inside the nose's flat end face, because cuts through the lofted nose took ~3 min each.

**Choking hazard:** the small-parts cylinder is Ø31.7 mm. At 43 × 33 mm the sensor can't go into it in any orientation, so it isn't a small part.

## Receiver: 38 × 38 × 12.7 mm sealed watch (+ lens dome), 20 mm quick-release band

| Part | Plan |
|---|---|
| Case | Square 38 × 38, plan corners R9, top edge R3.5, 1.6 wall, open at the back. **No openings in the sides.** Integrated lugs at 12 and 6 o'clock take standard **20 mm quick-release spring bars**, so washable elastic bands in any size swap in (wrist or ankle). |
| Top | 20 × 20 R6 frosted magenta **lens** (the "display"; it's a diffuser over an RGB LED, not a screen). A Ø1.6 green **link-LED pipe** sits at 6 o'clock under it, as in the concept. |
| Back | 1.4 mm lavender back plate (skin side), gasketed to the case. It carries **two gold charge contacts** that spring pogo pins on the board press on, and **two Ø3 magnets** that hold the clip-on charger. The magnets sit off-centre, so the charger only fits one way round (polarity keyed). The **ERM coin motor** is glued inside so the buzz goes straight into the skin. |
| Inside | 402025 LiPo (4 × 20 × 25, ~150 mAh) and a Ø10 × 2.7 ERM coin motor (MOSFET drive) side by side on the back plate. A 30 × 30 R8 board (parts on both faces) hangs from two lid posts with heat-staked pins, 1.0 mm above the cell. Top face 8.1 mm up; top-face parts ≤ 2.6 mm. |
| Band | Purple 20 × 1.6 elastic band (stand-in loop for a ~60 mm wrist), shown for scale. |

The concept is 10 mm thick; this one is 12.7 (+0.7 lens dome). The stack: 1.4 back + 0.1 foam + 4.0 LiPo + 1.0 for bottom-face parts + 1.6 board + 2.6 module + 0.4 gap + 1.6 top wall. A 1.0 mm board and a 3 mm cell would win back about 1.5 mm.

## Board contract (fit.json)

`fit.json` uses Stage 5's `boards` layout, with one entry each for `sensor` (52 × 24, both faces, provisional after the hosts' changes) and `receiver` (30 × 30 R8, both faces). Both point at `4-model/model.solidcraft`, and the origins are in this shared design frame. Stand-in bodies are prefixed `S ` / `R `. The switch lever and pogo pins are stand-ins too, since the real ones come with the board.

## Open questions / shortcuts

- Watch on/off: with no button, the firmware has to decide. Proposal: it sleeps when the sensor goes quiet (switched off) and wakes on the charger or on the sensor's next heartbeat. Firmware has to prove the 150 mAh lasts a night of ESP-NOW listening.
- Feedback for "I'm awake": the watch could stop buzzing and blink the lens green, so the parent knows the tap registered.
- Sensor run time unplugged: ~30 mA while listening → ~2000 mAh lasts about 60 h. Charging a 2000 mAh cell over USB-C takes ~4 h at 500 mA.
- The power switch's lever height (2.6 above the board) is assumed; Stage 5 confirms the part.
- The mic chamber behind the grille needs a foam gasket so the mic hears the monitor rather than the inside of the case.
- Watch sealing: an O-ring or adhesive gasket on the back plate, contacts insert-moulded. Aim for IPX7 (hand-washing, showers).
- Fasteners are first-pass: the sensor bottom plate and watch back plate are shown as drop-in plates (screws/snaps not modelled).
