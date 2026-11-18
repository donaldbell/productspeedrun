# Stage 4 notes: Smart Bucket Hat (005)

## Summary

**Done (2026-11-18):**
- `DESIGN.md` design read, two blockout passes plus the engineered model (`compare.png`: every signature feature reads; the piping is finer than the concept's seam).
- `model.solidcraft` from `build_model.py` (~8 min full build, ~5 min `--blockout`, 47 s `--fit`). 573 bodies: band, 219 louvres, 335 pixel tiles, pod, lid, key, cells, stand-ins.
- `fit.json` / `FIT.md` agreed with Stage 5 (their numbers taken as sent, no open requests either way).
- Fit check: **PASS**, 0 overlaps (Stage 5, against `fit_model.solidcraft`). Near misses: Mode Key–PTS810 ~0.18, Pod–PCB 0.11, Pod–XIAO 0.26, Lid–PCB 0.27.
- Exports: `iso.png`, `model.step`, `model.stl`, `model.glb` (14 meshes, one per colour; pixels emissive).

**The product:** a 58 cm hat's LED band. It's an oval cone 182 × 208 mm over the cords and 39.6 mm tall, leaning in 7°. A 12 × 208 pixel screen (2.8 mm pitch, black louvre grid over deep navy) shows tiki art across the front, fish and waves on the sides and ALOHA across the back, between fabric piping cords. Hidden inside at the back is a charcoal TPU pod (±102 mm of arc × 36 × 13.6 deep) holding the XIAO nRF52840 Sense carrier, two 1200 mAh cells, the mode key and the mic port. USB-C faces down, under the sweatband.

**Left for the hosts:** the four questions below (pod size, runtime vs pixel density, where the mode button lives, the piping colour).

## What's modelled (host's call, 2026-11-18)

The band, not the hat. The product is the LED band a hat maker fuses into an ordinary bucket hat: a tapered oval pixel screen with fabric piping at the top and bottom, plus the electronics pod hidden inside at the back. The crown, brim, eyelets and sweatband belong to the hat and aren't modelled.

## Plan (mm, model frame: Z up, brim seam on z 0, the hat's front −Y, back +Y)

| Part | What | Size / place |
|---|---|---|
| **Screen** (deep navy) | The band's core: TPU back skin (fused to the crown fabric), two flex LED matrices, diffuser. An oval cone leaning in 7° | 3.0 thick, z 0 → 39.6; screen surface 178 × 204 at the brim seam (a 58 cm hat) |
| **Louvres** (black) | The pixel grid, 0.5 proud of the diffuser: 208 vertical ribs and 11 rings | 0.5 wide, 2.8 pitch, 12 rows × 208 columns |
| **Pixel tiles** | The lit cells of the art (tiki, palms, hibiscus, sparkles, fish, waves, ALOHA), as coloured tiles in the cells | 335 bodies, 9 colours, map in `build_model.py` |
| **Cords** | Fabric-wrapped piping at the top and bottom of the screen, where the band is sewn into the crown and the brim seam | 3.0 tall, 2.25 proud |
| **Pod** (charcoal TPU) | Tub against the inside of the band at the back, behind the sweatband: offset-oval band d −3.8 → −17.4 (0.8 left for the crown fabric), 102 mm of arc either side of the back centre, z 1.2 → 37.6, 1.2 walls | ~204 mm of arc × 36.4 × 13.6 deep |
| **Pod lid** | Closes the tub's top; the board and cells drop in from above | 1.2 thick, z 37.6 → 38.8 |
| **Carrier board** | 50 × 34 × 1.0, standing at the back centre, leaning with the band, top face toward the head. XIAO nRF52840 Sense at the centre of the top face, USB-C down | from `fit.json` |
| Posts | Four posts from the pod's outer wall to the board's bottom face. Heat-stake pins through the two holes (±21, −13); the rests (±21, +13) only support | Ø4.2, from `fit.json` |
| USB-C opening | Stadium 9.6 × 4.0 through the pod's bottom wall, along the receptacle's axis. You fold the sweatband down to plug in | from `fit.json` `usb` |
| Mic port | Seven Ø1.2 hex holes in the pod's inner face over the XIAO's PDM mic (felt inside, the sweatband outside) | from `fit.json` `mic` |
| Mode key | Orange octagonal TPU key through the inner face with a flange inside, 0.2 above the PTS810 | from `fit.json` `button` |
| Lead exits | Two octagonal holes through the outer wall beside the plugs, where the band halves' leads go into the band's back seam | from `fit.json` `plug_a`, `plug_b` |
| Cells | 2 × LiPo 6 × 34 × 50 (~1200 mAh each), flat in the wings, ends 0.4 off the outer wall, centred 68 mm of arc either side of the back | off-board, in the model |

## Fit with Stage 5

- `fit.json` holds the board, holes, rests, features and the band's numbers. Stage 5's numbers were taken as sent: board 50 × 34 R3, holes (±21, −13), module, usb, button, plugs, cells, antenna keep-out.
- `fit.json`'s `model.design` is **`fit_model.solidcraft`**: the same build without the 219 louvres and 335 tiles (`python3 build_model.py --fit`). They all sit on the band's outer face, outside the Screen body, which the check still includes. With 560 bodies, a full check would take far longer.
- My own clearance check of the stand-ins against the pod: no overlaps after round 3. Intended contacts and near misses: Pod–PCB 0.0 (the posts), Mode Key–Button SW 0.20, Pod–Mode Key 0.32, Pod–XIAO USB-C 0.33, Pod Lid–PCB 0.25, Pod–cells 0.35, Pod–XIAO 0.58.
  - Round 1: the key went the wrong way (a sign error), the USB cutter stopped short of the wall, and the cells hit the pod's round ends and the plugs.
  - Round 2: the leaning cells clipped the floor by 0.1, so the floor dropped 0.4.
  - Round 3: the cells' far ends clipped the pod's round ends, because arc lengths measured on the screen surface shrink ~12 % at the cavity's depth. The pod grew to ±102 mm and 13.6 deep.

## Questions for the hosts

1. **The pod is big:** ~204 mm of arc (a third of the band) × 13.6 mm deep, at the back of the head behind the sweatband. That's two 1200 mAh cells beside the board, plus room for the band leads. Shorter cells (40 mm) would save ~26 mm of length. Stage 5 also asked about 8 mm cells (~1500 mAh each, ~2 mm deeper pod); I kept 6 mm for comfort.
2. **Runtime vs pixel density:** 2,496 LEDs, as the art shows. Stage 5 says ~1–1.5 h of light show on 2 × 1200 mAh, because WS2812-class LEDs draw current even when dark. Fewer rows or bigger cells would buy runtime but lose the look.
3. **Mode button:** it's on the pod's inner face, so you reach it under the sweatband. "From outside" would need a button through the band (a visible change), or a tap/shake gesture on the XIAO Sense's IMU instead.
4. **Piping colour:** modelled in the festival hat's weathered olive-grey. A hat maker would wrap it in each hat's own fabric (khaki for the lake hat).

## Shortcuts and open questions

- The pod's edges are square: fillets on its curved edges aren't supported, and extra loft sections twisted or bulged it. A production pod would be overmoulded with soft radii.
- The band's back seam (where the two flex halves meet), the lead entry through the crown fabric and the stitching flanges aren't modelled.
- The pixel art is one frame of what the app would show.

## Solidcraft lessons (also in `tools/form/README.md`)

- **Elliptical cone surfaces:** a loft between two ellipse sketches is exact and fast (~1 s). A tapered extrude of an ellipse came out as 16 cone patches with wrong mass properties. A loft through an annulus sketch ignored the hole, so use an outer loft minus an inner loft.
- **Repeated detail on a curved band:**
  - Intersect the thin shell with a single *comb* profile: one closed polygon with a tooth per feature, joined by a base that lies outside the shell. One extrude, ~20 s for 208 ribs.
  - An intersect with several tool bodies is the intersection of all of them, so it comes out empty.
  - Joining the rib comb to a ring comb first ran over 2 min, so it was stopped; two separate intersects are fast.
- **Naming:** an intersect that leaves n pieces names them `<name>`, `<name> (1)` … `<name> (n−1)`. A colour assigned before the intersect stays only on the first piece, so assign after it, by those names.
- **Big designs:** `measure {names_only}` on 500 bodies is a ~60 KB reply. Don't.
- **Pod loft:** periodic fit-point spline sections twisted the loft (a third of the volume). Two splines + two three-point arcs per section, and only two sections, gave the right volume. Four sections with inset ends bulged outward past the band.
