# Smart Bucket Hat: design read

Sources: the favourite concept art (`2-concept/Smart-Bucket-Hat-Festival-Poster.png`: the tiki festival hat, with a close-up of the matrix and the phone app), the second concept (`2-concept/Smart-Bucket-Hat-by-the-Lake.png`: the angler's khaki hat, front, back and detail views) and the control drawing (`3-layout/tech_LED-Pixel-Bucket-Hat-Design-Sheet.png`: front, three-quarter, back three-quarter and top views).

**What we're modelling (host's call, 2026-11-18): the band, not the hat.** The product is the manufactured LED band that a hat maker fuses into an ordinary bucket hat: the pixel screen ring with its top and bottom piping, plus the hidden electronics pod. The crown, brim, eyelets and fabric stay the hat maker's; they aren't modelled. So the silhouette to match is the band's: the slice of the concept between the crown seam and the brim seam.

**What to trust.** The concept sets the look: a dark screen band framed by fabric piping, a tight black grid of square pixels, and saturated tiki pixel art (a tiki mask at the front, palms either side, hibiscus outboard, sparkles). The control drawing gives the band's proportions, its taper, the piping above and below and the pixel density. The pixel art itself is a stand-in for whatever the app shows. Nothing inside the hat is drawn, so the pod is ours.

**Orientation in the model:** Z up, the bottom of the band (the brim seam) on z 0. The hat's front is **−Y** (the sunset), the back **+Y** (where the pod hides inside). X is across the head.

## Signature features

| # | Feature | How it's modelled |
|---|---|---|
| F1 | **A wide, short oval ring** round the crown, about 0.22 × as tall as it is wide (control drawing front view), continuous all the way round with no seam, box or bump showing from outside. It's oval in plan (longer front to back, like a head), not round. | Every surface is a loft between two ellipses (bottom and top), with semi-axes from the brim-seam oval minus the taper. The ring = outer loft minus inner loft. |
| F2 | **A slight inward lean**: the band follows the crown, narrowing about 7° towards the top (front view: 480 px wide at the top against 505 at the bottom over 105 px). | Each ellipse's semi-axes shrink by z · tan 7°. |
| F3 | **Piping at both edges**: a rounded fabric cord along the top and bottom of the screen, standing proud of it and framing it (the light rims in both concepts; the doubled lines in the control drawing). This is where the band is sewn into the hat. | Loft through 7 ellipse sections whose offset bulges out like a cord (proud by 1.7), minus the inner loft. In the hat's fabric colour. |
| F4 | **A tight black grid of square pixels**: 12 rows of square cells with black louvres between them, dense enough to read as a screen, not as dots (12 rows in the poster close-up, 11 in the drawing). | A black louvre layer 0.5 proud of the screen: vertical ribs (a comb profile intersected with the louvre shell) and horizontal rings (a comb in the side plane intersected with a copy of it). 2.8 mm pitch, 208 columns. |
| F5 | **A dark screen ground**: unlit, the band is a near-black navy stripe, so the hat reads as a plain hat with a dark band when it's off. | The screen core in deep navy; the louvres black. |
| F6 | **Saturated tropical pixel art**, the poster's look: a sunset over the sea at front centre (amber and orange sun, a red horizon, its orange reflection in cyan and blue waves; it replaced the poster's tiki mask, see the note at the end), green palms with amber trunks on either side, magenta hibiscus outboard of them, blue sparkles between. | Lit cells as thin coloured tiles inside the louvre cells, cut from a tile shell row by row (a copy of the shell intersected with a comb of the lit cells in that row, per colour). The art is written as a 12 × 208 character map in `build_model.py`, so it can be redrawn. |
| F7 | **The marquee runs all the way round**: the angler concept shows fish, waves and trees round the sides and back. | Waves and a jumping fish on each side, and "ALOHA" across the back (the text mode). |
| F8 | **The brains are invisible**: the electronics live in a slim pod inside the band at the back, behind the sweatband, following the band's curve. USB-C faces down into the hat, so you fold the sweatband down to charge. | A pod lofted between two offset-oval sections (a concentric arc, so it hugs the band), hollowed after the blockout. Charcoal. |

## Proportions

From the control drawing's front view (pixels, the band between the welts' outer edges): band height 105, width 480 at the top and 505 at the bottom.

- Height : width ≈ **0.21–0.22** (105 / 490 at mid-height).
- Lean ≈ **7°** each side ((505 − 480) / 2 over 105 px).
- Piping ≈ **8 %** of the band height each (≈ 8 px of 105 at the top and bottom).
- Pixels: 12 rows over the screen (poster close-up), square cells, grid lines ≈ 15 % of the pitch.
- Plan: the top view is close to round. A real head is about 1.25 : 1 and a crown softer, so the model is **1.15 : 1** (front to back : side to side).

**Scaled to the hat:** a 58 cm hat (M/L). The screen surface at the brim seam is an oval of 178 × 204 mm (semi-axes 89 and 102), so the band's inside is about 58 cm round. Twelve rows at a **2.8 mm pitch** make a 33.6 mm screen, plus two 3.0 mm cords: the band is **39.6 mm tall** and 181 mm wide over the cords: 0.22 ✓. The column pitch matches (584.6 mm round at mid-height / 208 = 2.81), so the cells are square: **2,496 pixels**.

## Silhouettes

The band is a ruled oval cone, so its silhouettes are the cross-section and the plan.

**Cross-section** (at any angle round the band), d = outward offset from the screen surface in mm, z up from the brim seam:

```
bottom cord   z 0.0 → 3.0     d: 0.3 1.1 1.55 1.7 1.55 1.1 0.3 at z 0 0.4 0.9 1.5 2.1 2.6 3.0
screen        z 3.0 → 36.6    d 0 (navy core), louvres to d 0.5, lit tiles d −0.05 → 0.2
top cord      z 36.6 → 39.6   as the bottom cord
inner face    d −3.0 the whole height (the back skin bonded to the crown fabric)
```

**Plan** at height z: ellipse with semi-axes (89 − z·tan7° + d) across and (102 − z·tan7° + d) front to back.

**Pod** (inside, at the back): in plan, a band of the oval between d −3.8 (0.8 for the crown fabric) and d −17.4, from −102 to +102 mm of arc either side of the back centre, with round ends; in height, z 1.2 → 38.8 (tub plus a 1.2 lid). Square edges: rounding them by loft or fillet failed (NOTES.md).

## Colours and surface

| Body | Colour | Note |
|---|---|---|
| Piping (both cords) | weathered charcoal-olive `#5a5242` | The festival hat's fabric. A hat maker would wrap it in the hat's own cloth (khaki for the lake hat). Matte. |
| Screen core | deep navy `#151b2c` | The unlit screen, satin |
| Louvres | black `#0a0b0f` | Matte |
| Sunset | amber `#ffc23a`, orange `#ff7a1a`, red `#ff3b1f` | Glowing |
| Palms | green `#39e64a`, trunk amber `#e0a020` | |
| Hibiscus | magenta `#ff3fd2`, violet `#b44dff`, yellow centre | |
| Sparkles, waves | blue `#3b7bff`, cyan `#29d3ff` | |
| Fish, ALOHA | warm white `#fff1c9` / ice `#dff1ff` | |
| Pod | charcoal `#26282d` | Soft-touch TPU, hidden |

Soft fabric cords against a crisp, glossy screen. Symmetric left to right, but the art runs all the way round, so front and back differ.

## What it must not become

A rigid headband or crown. A box or bump on the outside of the hat. A flat display panel. A perfect circle. A thin LED strip with dots: it has to read as a screen of square pixels. A rainbow: the art is tiki-coloured.

## Score (compare passes)

Filled in after each `tools/form/compare.py` pass. ✓ reads, partly, ✗ doesn't.

| Feature | Pass 1 (`blockout-01`) | Pass 2 (`blockout-02`) | Pass 3 (engineered) | Final (`iso.png`) |
|---|---|---|---|---|
| F1 wide, short oval ring | ✓ | ✓ | ✓ | ✓ |
| F2 inward lean | ✓ | ✓ | ✓ | ✓ |
| F3 piping top and bottom | partly: thin dark lines | partly: proud 2.25, still reads as a fine rim | partly: warmer colour | partly: a fine rim at this scale, as in the poster |
| F4 black square pixel grid | ✓ | ✓ blacker louvres | ✓ | ✓ |
| F5 dark screen ground | partly: grey-blue | ✓ deep navy | ✓ | ✓ |
| F6 tiki pixel art | ✗ most lit cells came out grey (split pieces lost their colour); too sparse | ✓ tiki, palms, hibiscus, sparkles packed across the front like the poster | ✓ | ✓ |
| F7 marquee all the way round | ✓ ALOHA across the back | ✓ fish and waves round the sides | ✓ | ✓ |
| F8 invisible brains (pod) | partly: hidden from outside, but the loft twisted (a third of its volume) | partly: same pod | ✓ two-section loft, right volume; hidden from outside | ✓ the mode key and mic port show only from inside |

Pass 1 → 2: coloured every split tile by name; spread the sprites over the front half (tiki, sparkles, palms, hibiscus at ±45°, fish over waves on the sides, second palms further back); darker screen, blacker louvres, fatter cords.

Pass 3 (engineered model): the pod was rebuilt from two-curve-pair sections (the periodic-spline loft had twisted), and lengthened and deepened for the cells. The cords are a touch warmer. Still off: the piping reads finer than in the concept, where it's the hat's own seam. At hat scale a 3 mm cord is right, and the render can lift it.

**Change, 2026-11-19 (hosts' call):** the tiki mask at the front centre is gone, replaced by a sunset over the sea, the same motif as the hosts' chosen hero render. As a grid of pixels, the mask's face (big eyes, a wide red mouth) could read as a racist caricature, so it is no longer used anywhere in the model or the page. The palms, hibiscus, sparkles, fish, waves and ALOHA are unchanged. The pass table above is kept as it was recorded.
