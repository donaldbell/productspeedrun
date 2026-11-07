# Baby Monitor Monitor: design read (Rev B)

Written for Rev B, which had no `DESIGN.md`. Sources: the favourite concept art (`episodes/003-003/2-concept/Watercolor-Baby-Monitor-Concept-Board.png`), the control drawing (`episodes/003-003/3-layout/…xdww.jpeg`) and Rev A's hero render (`episodes/003-003/4-model/render-…qcnt.jpeg`).

**Rev B goal (hosts):** "a truer representation of the concept art, with the style nuances, complex curves, asymmetry and details". Rev A's sensor reads as a rounded box with a flat nose face and a straight, planar colour split. Its watch reads as an extruded square with horn lugs. Both fit their parts, so Rev B keeps every part position (`fit.json`) and reworks the outer form around them.

**What to trust:** the concept art sets the look (sensor 3/4 view, back view and status close-up; watch front and side). The control drawing confirms the teardrop side profile and the inset back panel. Every part label, dimension and the "haptic motor in the sensor" in both images is made up, so ignore them. Sizes come from the parts (`fit.json`, Stage 5). Where they differ from the art, the hosts' decisions win: the watch has **no side button and no USB**, and the sensor's "Connect" button is gone (hold the top button to pair).

---

## Sensor (Wireless Mic Sensor)

### Signature features

| # | Feature | How it's modelled |
|---|---|---|
| S1 | **Low teardrop / pebble body.** A tall round nose, the crown just behind it, then one long, smooth fall to a lower, rounded back. No flat faces except the base and the back panel. | `solid.loft` through 14 cross-sections. Each is a **fit-point spline** superellipse (not lines and arcs) over a flat base line, so the surface is smooth in both directions. The sections come from the side, plan and front silhouettes below. |
| S2 | **Asymmetry.** The right (+y, the side the concept shows) is fuller and rounder-shouldered; the left is ~1.4 mm narrower with a steeper, tighter shoulder. The swoosh also sits differently on each side. | Each section has its own half-width and superellipse exponent per side (right 2.7, left 2.2). There is a separate swoosh curve per side. |
| S3 | **Round nose face filled by the grille.** A near-circular front face. A chrome bezel ring takes ~85 % of its height, and the dark honeycomb grille fills the ring as a shallow dome. | The loft's first section is close to a circle (R≈13.5). The chrome **collar ring** (R12.2 out, 1 proud) is a revolve. The grille is a revolved **shallow dome** (bulges ~3.5 mm, flatter than Rev A's SM58 ball), with a hex hole pattern. |
| S4 | **S-curve swoosh, two-colour.** A lavender lower side panel starts as a sliver under the nose bezel. It rises in an S-curve to ~60 % of the height toward the back, then rolls over onto the back corners. A **bright trim band** runs along the top of the swoosh, continuing the bezel's chrome. | Side tool bodies are extruded from **fit-point S-curves** in the side view (one per side) and kept to \|y\| > 15, so only the side walls are lavender. Lavender = shell ∩ tool. The trim band is the same tool raised 1.4 mm, minus the lavender. |
| S5 | **Kidney-bean status light on the cheek** just behind the bezel, on the visible (+y) side. It's a vertical, slightly bowed capsule. | A bean outline (fit-point periodic spline) on a side plane, cut through the wall. The light pipe is the same bean, clipped to the outer skin so it sits flush, with a block back to the board LED. |
| S6 | **Big disc button on the crown** (~30 % of the width) with a centre dimple, flush to slightly proud. | Ø13 revolved cap with a 0.4 mm centre dimple in its profile and a domed edge. (It stays over the tact switch at board (6, 0): moving it forward would hit the module.) |
| S7 | **Inset back panel** holding the slide switch and USB-C, with a dark foot strip along the base. | A 0.6 mm recess cut into the loft's flat back cap, following the cap outline inset by ~2.5 mm. The USB-C and slider openings sit in it. The base slab stays dark grey. |

### Proportions

- Concept side view: length : height ≈ 2.1 : 1 (≈ 50 : 24 by its own labels). Control-drawing side view: ≈ 2.0 : 1.
- Concept back view: width : height ≈ 1.6–1.7 : 1.
- The crown peaks at ~30–40 % of the length from the nose. The back is ~70 % of the crown height.
- The grille + bezel is ~85 % of the nose height, centred a little below mid-height.
- Rev B: **64 × 44.3 × 29.8 mm body** (+ ~4.5 for bezel and dome), against Rev A's 63 × 42.8 × 32.6. It is lower and wider (L : H 2.15, W : H 1.5), driven by the cell (34 wide), the board (top 14.5) and the button switch (top 19.5).

### Silhouettes (0–1 box)

Side profile, top edge, nose (x 0) to back (x 1), z 0 = base, z 1 = crown:

```
(0.00,0.10) (0.00,0.50) (0.01,0.91) (0.03,0.94) (0.06,0.97) (0.12,0.99) (0.22,1.00) (0.36,0.99)
(0.52,0.97) (0.67,0.93) (0.80,0.87) (0.89,0.82) (0.95,0.77) (0.98,0.73) (1.00,0.69) (1.00,0.10)
```

Top plan, half-widths of the right (+y) and left (−y) sides, as fractions of the max width (45 mm):

```
x:     0.00  0.01  0.03  0.06  0.12  0.22  0.36  0.52  0.67  0.80  0.89  0.95  0.98  1.00
right: 0.30  0.36  0.41  0.44  0.47  0.49  0.50  0.50  0.50  0.49  0.47  0.45  0.41  0.36
left:  0.30  0.35  0.39  0.42  0.44  0.46  0.46  0.47  0.47  0.46  0.44  0.42  0.39  0.35
```

Front section (at the crown): a superellipse over a flat base. The widest point is at ~35 % of the height. Above it the right shoulder is fuller (n 2.7) and the left tighter (n 2.2). Below it the sides tuck under to the base (n 4).

Swoosh (top edge of the lavender), side view, as (x, z) fractions:

```
right: (0.08,-0.05) (0.20,0.05) (0.35,0.13) (0.48,0.25) (0.58,0.40) (0.67,0.53) (0.76,0.60) (0.86,0.62) (0.95,0.60) (1.05,0.55)
left:  (0.08,-0.05) (0.22,0.04) (0.38,0.11) (0.52,0.22) (0.62,0.35) (0.71,0.47) (0.80,0.53) (0.90,0.55) (1.05,0.52)
```

### Colours and surface

Pearl/chrome-look white upper shell (`#eef0f5`), lavender swoosh panels (`#b4acdc`), a bright chrome trim band and bezel (`#c8ccd6`), dark grey foot (`#8f93a6`), near-black grille (`#2c2b35`), glowing green status bean. Soft, glossy, rounded everywhere. No sharp edges except the parting lines.

### What it must not become

A rounded box (Rev A). Symmetric. A flat front face with a small grille in it. A straight, planar colour split.

---

## Receiver (Wearable Haptic Receiver)

### Signature features

| # | Feature | How it's modelled |
|---|---|---|
| R1 | **Pillow squircle case.** A square plan with big corner radii. The sides bulge outward and roll into a flat-topped bezel, and the back tucks in slightly. | `solid.loft` through 7 rounded-rect sections (z 0 → 12.7). The widest point is 38.6 at z ≈ 5. The top cap is 32.6, so the top edge rolls over in a long curve instead of a fixed fillet. |
| R2 | **Recessed glowing lens.** A squircle window ~53 % of the face, sitting below a stepped bezel, with a **bright magenta ring** round a softer, lighter centre. | A 0.6 mm counterbore step round the lens opening. The lens body (magenta) gets a pocket, with a lighter inner face body in it. |
| R3 | **Link LED dot at 6 o'clock** in the bezel. | Kept from Rev A (light pipe over the board's link LED). |
| R4 | **Small integrated lugs**, so the band seems to tuck under the case. | Lugs are shorter and lower than Rev A's horns (stick out ~4 mm instead of 5.6), with round ends. 20 mm spring bars are kept. |
| R5 | **Two-tone: pearl case, lavender back, purple band.** | As Rev A. |

### Proportions

Concept front: square, 1 : 1, corner radius ≈ 25 % of the width, lens ≈ 55 % of the width. Concept side: ~10 mm thick (ours is 12.7 + lens, set by the cell + board stack: see `NOTES.md`). The side is convex, at its widest a third of the way up.

Side profile (half-width as a fraction of 19.3 mm, z as a fraction of 12.7):

```
(z 0.00, 0.974) (0.12, 0.985) (0.39, 1.000) (0.67, 0.995) (0.85, 0.958) (0.94, 0.907) (1.00, 0.845)
```

### Colours

Pearl case (`#e6e9f0`), lavender back (`#b9b3d9`), magenta lens ring (`#d86cff`) round a pale lilac centre (`#f0c8ff`), green link dot, purple band (`#6e58a8`).

### What it must not become

An extruded square with a fillet (Rev A). A flat lens flush with the top. Lugs that read as separate horns.

---

## Score (compare passes)

Filled in after each `tools/form/compare.py` pass. ✓ reads, partly, ✗ doesn't.

| Feature | Rev A | Blockout pass 1 (`blockout-01.png`) | Final (`iso.png`, `compare.png`) |
|---|---|---|---|
| S1 teardrop body | ✗ (box) | partly: round nose, but the middle reads as a tube; steeper fall to the back and rounder rear shoulders for pass 2 | partly: round nose and a crown falling to the back, but still longer and more tube-like than the concept's pebble (the 50 mm cell sets the length). Pass 2 (steeper fall) didn't build in time: see NOTES.md |
| S2 asymmetry | partly | partly (visible in the back view; subtle) | partly: subtle; shows in the back view and the different swoosh height per side |
| S3 round nose / big grille | partly | ✓ | ✓ |
| S4 S-curve swoosh + trim | ✗ (planar) | ✓ | ✓ |
| S5 kidney status light on cheek | ✗ (front face) | ✓ | ✓ |
| S6 disc button | ✓ | ✓ | ✓ |
| S7 inset back panel + foot | partly | partly: the recess is too big; inset 2.2 → 3.0 | partly: the recess reads as a big flat panel; inset 3.0 was in pass 2 |
| R1 pillow squircle case | partly | ✓ | ✓ |
| R2 recessed glowing lens | partly | ✓ | ✓ |
| R3 link dot | ✓ | ✓ | ✓ |
| R4 small lugs | partly | ✓ | ✓ |
