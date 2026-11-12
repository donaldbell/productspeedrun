# Color-Sensing Aquarium Accent Light: design read

Sources: the favourite concept art (`2-concept/Steampunk-Rainbow-Aquarium-Light-Blueprint.png`) and the control drawing (`3-layout/ctrlSteampunk-LED-Light-Bar-Blueprint.png`: two face views, one side view and a 3/4 view).

**What to trust.** The concept sets the look: an antique-brass deck over a dark gunmetal body, the rainbow LED window, the warm brass end clusters and the finials. The control drawing gives the outlines, proportions and where each outside feature sits. Everything drawn *inside* the windows (the XIAO, its chip, "PIR"), the labels and the "≈ 8–10 mm / 300 mm" numbers are made up. Sizes come from the brief (an under-cabinet light bar, about a foot long, phone-thin) and the real parts.

**Decisions from the host (chat, 2026-11-11) that change what the art shows:**
- **One USB-C, on the long side edge** (the control drawing's side view), behind a gasketed brass plug. The big oval "USB" on the LED face becomes the **colour-sensor window**. The face itself has no port.
- **The faceted dome stays.** Behind it sits an optical reflectance / proximity sensor (APDS-9960 class) that sees fish moving near the surface, not a PIR, since a PIR can't see fish through water.
- **The found object is the aquarium itself:** the light lives in (and reads) the tank. The housing is moulded plastic, painted and antiqued to look like carved, milled brass over gunmetal.
- **Mounting:** a thin rail sticks under the lid with VHB tape, and the bar clips into it. It can't drop into the tank, and it comes off for charging without lifting the lid.

Orientation in the model: **LED face up (+Z)**, so the iso view matches the concept's view of the face. In use it hangs upside down under the lid, LEDs and sensors looking down at the water. X runs along the bar (dome end −X, electronics end +X); the side with the USB-C is −Y (the side the control drawing's side view shows).

## Signature features

| # | Feature | How it's modelled |
|---|---|---|
| F1 | **A very long, slim bar.** About 12 : 1 length to width and 27 : 1 length to thickness. The long sides run straight, and the ends taper in plan like a pen barrel into the finials. It must read as a stick, not a box. | Plan outline: two straight long sides plus **fit-point spline** tapered ends, extruded. Side outline: fit-point spline ends, extruded across the width and **intersected** with the plan body. Edges softened with `fit: reduce` fillets. |
| F2 | **Turned brass finials at both ends.** A wide collar ring, then a smaller rounded nub, coaxial with the bar. They're slightly flattened, since the bar is wider than it is thick. | Revolved collar and nub (sketch on XZ, revolve about the bar's centre line), then flattened to an ellipse by intersecting with an extruded elliptical section. One finial is modelled and mirrored to the other end. |
| F3 | **Two-tone horizontal split: an antique-brass deck over a dark gunmetal body.** The concept's side view shows the brass top plate sitting on a dark slab, with its ends ramping down short of the slab's rounded ends. That is the parting line. | Gunmetal **base body** (z 0 → 6.3) and a separate brass **deck body** on top (z 6.3 → 11), inset ~0.8 mm from the base's sides, so the step reads as the parting line. The deck's ends ramp down (side spline). Each is its own body and colour. |
| F4 | **Long stadium LED window**, ~60 % of the length (x 0.19 → 0.78 of the bar), in a raised brass bezel, with a frosted diffuser and **12 evenly spaced square LEDs** glowing in a rainbow. | A stadium (slot) bezel ring 0.5 mm proud. The diffuser is recessed 0.6 mm inside it. Twelve 3.2 mm squares sit on the diffuser as thin coloured bodies (magenta → blue → cyan → green → yellow → orange, as in the concept). |
| F5 | **Faceted dome lens at the dome end** (x ≈ 0.10), almost the deck's full width, standing well proud of the face (~0.4 × its diameter). It's milky white with hex/pentagon facets, like a Fresnel PIR lens. | Revolve a polyline arc (three flat latitude bands), then intersect it with a 10-sided prism, so the faces come out as facets. It sits on a brass **collar ring** with sloped flanks (the riser in the control side view). |
| F6 | **Small porthole button next to the dome** (x ≈ 0.155): a round brass boss with concentric rings, like a gauge or eyepiece. | A stepped cylinder pair (boss Ø 7.5, cap Ø 4.5) with a dark centre: the host's mode / AP button. |
| F7 | **Right-end electronics cluster.** A dark rounded-rect **viewing window** (x ≈ 0.835) showing the "machinery" (the XIAO really is under it). Then the **chrome oval window** (x ≈ 0.905), which in the art is the USB-C and here becomes the colour-sensor window. | Window: a rounded rect cut 0.6 mm into the deck, filled with dark smoked glass and a lighter "chip" square under it. Oval: a stadium chrome bezel with a dark lens. |
| F8 | **Rivets and filigree** packed around both end clusters: brass dome-head rivets at the corners, plus scroll cut-outs that show the dark gunmetal beneath. | Rivets: Ø 1.6 dome-head bodies, about 8 per cluster. Scrollwork: a few shallow fit-point "comma" recesses (0.4 mm) in the deck around the clusters (pass 2, if the time budget allows). |
| F9 | **The side reads quiet and slim.** One long groove line along the gunmetal body, the USB-C's **brass plug** near the right end of the −Y side, and nothing else. | A 0.4 mm groove. The plug is a stadium cap 0.8 mm proud with a small tether nub. |

## Proportions

From the control drawing (face view 1, side view 3), measured in pixels:

- Overall length (finial tip to tip) : width : body thickness ≈ **1450 : 102 : 55 px → 14.2 : 1 : 0.54**.
- Dome: Ø ≈ 0.95 × the bar's width, standing ≈ 0.45 × its Ø above the face (side view). Centre at 0.10 of the length.
- LED window: x 0.19 → 0.78 of the length; its height is ≈ 0.6 × the bar's width.
- Finials: ≈ 3.7 % of the length each (collar ~1.4 %, nub ~2.3 %). The collar is ≈ 0.75 × the width tall in the face view and ≈ 0.85 × the thickness in the side view (so it's elliptical).
- Concept side view: the brass deck is ≈ 45 % of the body's thickness and the dark slab ≈ 55 %.

**Scaled to the parts:** 300 mm tip to tip (the brief's "about a foot"), **26 mm wide** and **11 mm thick**. The thickness matches the art (300 / 27 ≈ 11). The width is the one deliberate change: the art's 14 : 1 would give 21 mm, but the XIAO has to lie *across* the bar so its USB-C reaches the side edge (21 mm XIAO + ~1 mm USB overhang + two 1.4 mm walls ≈ 25). So the bar is 11.5 : 1, still far slimmer than the brief's 1.5" (38 mm). The dome is Ø 23 and stands 9.5 mm above the deck.

## Silhouettes (0–1 box)

**Side profile** (control drawing side view), x 0 = left finial tip → 1 = right tip, z 0 = back → 1 = deck top (body only; the dome and finials sit on it). The base slab and the brass deck are separate outlines:

```
base slab (gunmetal), top edge z 0.57, rounded ends:
(0.037,0.10) (0.039,0.30) (0.042,0.45) (0.047,0.54) (0.055,0.57) ... flat ... (0.945,0.57) (0.953,0.54) (0.958,0.45) (0.961,0.30) (0.963,0.10)
base underside: flat at z 0, with the ends rounding up to z 0.10
deck (brass), z 0.57 → 1.0, ramped ends:
(0.046,0.57) (0.052,0.70) (0.060,0.84) (0.068,0.94) (0.076,0.99) (0.082,1.00) ... flat ... (0.918,1.00) (0.924,0.99) (0.932,0.94) (0.940,0.84) (0.948,0.70) (0.954,0.57)
finial, centre line z 0.50: collar x 0.023–0.037, half-height 0.43; nub x 0.000–0.023, half-height 0.30, rounded tip
dome on the deck: centre x 0.10, half-width 0.038 (of the length), rising to z 1.86 (0.86 above the deck)
```

**Top plan** (face view), half-width as a fraction of the max half-width (13 mm), from the left end (mirrored at the right):

```
x:     0.037 0.039 0.042 0.046 0.050 0.056 0.064 0.075 ... 0.5
half:  0.62  0.72  0.80  0.87  0.92  0.96  0.99  1.00  ... 1.00
deck (inset): 0.94 of the base's half-width along the straight run
```

**Front section** (across the bar): a flat-bottomed rounded rectangle. The sides are near vertical, the top edge of the deck rolls over with R ≈ 0.2 × the thickness, and the bottom edge of the base has a smaller R ≈ 0.12 × the thickness. The deck steps in from the base on both sides.

## Colours and surface

| Body | Colour | Note |
|---|---|---|
| Deck, finials, bezels, rivets, porthole | antique brass `#b8863b` | Painted plastic: warm, satin and slightly worn, with darker bronze in the recesses (`#7a5326`) |
| Base body | gunmetal `#3b3d40` | Satin dark, the "slab" in the concept's side view |
| Diffuser | frosted white `#f3eef8`, slightly glowing | |
| LED squares | rainbow: `#ff4fd8` `#c25cff` `#7a6bff` `#4f8dff` `#33c6ff` `#2fe0d0` `#3fe08a` `#a6e43c` `#ffe14a` `#ffb23e` `#ff8a3d` `#ff5f7a` | The concept's rainbow, magenta at the dome end |
| Dome lens | **smoky amber** `#7f4a1c`, see-through (hosts, 2026-11-11: clear to IR for the APDS-9960; the art's milky white scattered its IR) | Faceted, glossy |
| Viewing window | smoked glass `#23272b`, chip `#c9c4b8` | |
| Colour-sensor oval bezel, USB plug face | nickel `#c8cbcf`; dark lens `#15181b` | |

Crisp, machined detail on soft edges. It's symmetric front to back, but the two ends are deliberately different (dome cluster vs electronics cluster).

## What it must not become

A rounded box or a plain extruded bar. A generic aluminium under-cabinet light. One flat colour. A bar with the USB on the face. A finial-less stick. A small dome bump instead of a proud faceted lens.

## Score (compare passes)

Filled in after each `tools/form/compare.py` pass. ✓ reads, partly, ✗ doesn't.

| Feature | Pass 1 (`blockout-01`) | Pass 2 (`blockout-02`) | Pass 3 (`blockout-03`) | Final (`iso.png`) |
|---|---|---|---|---|
| F1 long slim bar, tapered ends | partly: slim, but the ends came to a point | partly | ✓ blunt coned ends into the finials | ✓ |
| F2 turned finials | ✗ blobs | ✓ flange + neck + bulb | ✓ (the flange stands a little proud of the body end, as in the concept) | ✓ |
| F3 brass deck over gunmetal | ✓ | ✓ | ✓ | ✓ (plus the dark clip rail below, by the host's mounting choice) |
| F4 stadium LED window, 12 rainbow LEDs | partly: tiny LEDs on white | ✓ rainbow glow pads + LEDs | ✓ | ✓ |
| F5 faceted dome on collar | partly: dome sat straight on brass | partly: collar cut into the facets | ✓ on its collar, in the dark panel | ✓ |
| F6 porthole button | ✓ | ✓ | ✓ | ✓ (now a working plunger) |
| F7 viewing window + chrome oval | ✓ | ✓ | ✓ | ✓ |
| F8 rivets + filigree | ✗ | partly: gear cut-outs on the ramps, bigger rivets | partly: reads up close; the concept's dense scrollwork is simplified | ✓ after the hosts' filigree pass (below) |
| F9 quiet side, USB plug | ✓ | ✓ | ✓ | ✓ (the plug now seals in the real opening) |

Still off after pass 3: the concept's filigree is far busier (it's AI-drawn ornament, so we chose a few gear and hex cut-outs that a mould can hold). The LED window's glow is a flat pastel band, not light; the render will add the glow.

### Filigree pass (hosts, 2026-11-11: "the artisanal brasswork art nouveau aesthetic is an essential differentiating aspect … play it up")

All of it is relief or inlay on flat faces, so a mould (or paint and etch) can hold it. `progress-01.png` and `progress-02.png` are close-ups.

- **Braided vine along both gunmetal sides:** two whiplash waves half a wave apart. They cross into a chain of eyes, each with a brass bead. The relief is 0.4 proud, kept above the rail's clip lips (z 3.2–5.6).
- **Escutcheon:** a horseshoe-arch brass plate round the USB-C plug. The same plate sits on the +Y side as a blank cartouche (room for a maker's mark).
- **Scrolls:** whiplash scrolls ending in spirals on the dark panel round the dome and porthole, and on a new matching dark panel round the colour-sensor oval. They replace the plain rivets there.
- **Etched lines:** blackened wave lines along both long edges of the LED window.
- **Kept:** the gear cut-outs on the end ramps and the rivets by the viewing window.

