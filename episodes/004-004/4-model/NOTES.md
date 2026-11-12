# Stage 4 notes: Color-Sensing Aquarium Accent Light (004)

## Summary

**Done (2026-11-11):**
- Design read (`DESIGN.md`), three blockout passes plus a final compare (`compare.png`: every signature feature reads; the filigree is simplified).
- The parametric engineered model `model.solidcraft`, from `build_model.py` (~7 min full build, ~45 s with `--blockout`).
- `fit.json` / `FIT.md` agreed with Stage 5. Their two requests are done. One 4→5 request (color/view moved) is waiting for them to mark it done.
- Exports: `iso.png`, `model.step`, `model.stl`, `model.glb`.

**Fit check round 1 (Stage 5):** one overlap, the XIAO's USB-C mouth against the plug stem and the base. Fixed: the opening is now centred at z 3.2 and the plug's inner face sits at y −12.05. Model re-saved and re-exported.

**Fit check round 2:** PASS (0 overlaps), but `inspect.clearance` still reported a 0.00 contact at the opening's bottom edge, although probes showed a real 0.2 mm gap (two nearly concentric stadium arcs). The opening is now 9.6 × 4.0, with its bottom level with the floor, and a matching stand-in measures 0.31 mm minimum. Near misses Stage 5 reported, all clear: Deck–PCB 0.03 at (120.1, 5.4) (a deck boss over the board), Port Cap–PTS810 0.09, Deck–XIAO 0.10, Base–PCB 0.11, USB Plug–XIAO 0.15.

**Fit check final: PASS** (0 overlaps, no contacts; Stage 5 commit 547ae3a). No requests are open in either direction. **Stage 4 is done.** The host questions are answered (below). After the light barrier: the fit check still passes. The rib clears the APDS-9960 by 0.20 in the real board, against 0.30 in this model: the exported part sits ~0.08 above the board's top face (board side, probed), which is fine. Its results land in `5-electronics/fitcheck.md`.

The product: a 300 × 26 × 11 mm brass-and-gunmetal bar (the dome stands 10 mm proud; the clip rail adds 2.4 mm on the back). It's an antique-brass deck over a gunmetal base, turned finials at both ends, a faceted dome on a dark panel, a stadium LED window with 12 rainbow squares, a smoked viewing window and a chrome colour-sensor oval at the electronics end, and a brass plug over the side USB-C.

## Host decisions (chat, 2026-11-11)

- One USB-C, on the long −Y side edge, behind a gasketed brass plug. No port on the LED face. The art's face "USB oval" is the colour-sensor window.
- Optical reflectance sensor (APDS-9960) under the faceted dome instead of a PIR.
- The found object is the aquarium itself. The housing is moulded plastic painted to look like antique brass.
- A stick-on rail under the lid, and the bar clips into it.

## Plan (mm, model frame: LED face up, back on z 0)

| Part | What | Size / place |
|---|---|---|
| **Base** (gunmetal) | Tray: floor 1.2, side walls 1.4, rounded ends. The USB-C opening is in its −Y wall | z 0 → 6.3, 278.8 × 26 |
| **Deck** (brass) | Lid: top wall 1.2, side walls 1.4, ramped ends, rivets, gear filigree on the ramps. A 0.75 mm tongue drops 1 mm into the base round its whole inside edge | z 6.3 → 11, inset 0.8 from the base's sides (the visible parting step) |
| Finials | Turned brass end caps (flange, neck, bulb), bonded to the ends | 11 mm each |
| Dome | Faceted lens on a brass collar over the APDS-9960, with a d7 light path through the deck | Ø 21 at its base, z 12.25 → 21.1 |
| Diffuser | Frosted stadium, glued in from inside with a 1.2 mm flange under the deck's top wall | 13.4 wide, 177 long |
| Viewing window | Smoked glass over the XIAO end (the board's top face shows) | 19 × 16 |
| Colour oval | Chrome bezel, dark lens over the APDS-9251 | 13.4 × 7.4 |
| Porthole button | Brass cap = plunger. The stem runs through the boss to the PTS810 tact switch, and a stop flange sits under the deck's top wall | Ø 5 cap, Ø 4.8 stem |
| USB plug | Brass stadium cap with a stem that seals in the opening (silicone sleeve, tethered) | 11.8 × 4.6 cap |
| **Carrier board** | 248 × 21.4 × 1.0, top face z 6.6. LEDs, sensors and button on top; **XIAO ESP32-C6 on the bottom** at the USB end | from `fit.json` |
| Cells | 2 × LiPo 4 × 20 × 80 on the floor under the board's middle | from `fit.json` (`cell1`, `cell2`) |
| Fixings | 4 × M2 × 10 pan-head screws from the back: through the base posts (Ø6) and the board into deck bosses (Ø4.6, pilot Ø1.6). They clamp the board between them. One rest post sits between the cells | holes from `fit.json` |
| **Mount rail** | Gunmetal C-channel, 160 long, with VHB foam tape on its back (under the lid). Hooks on its lips snap into 0.7 mm grooves along the base's sides | x ±80, z −2.4 → 2.4 |

### Why the XIAO is on the bottom face

The stack at the XIAO end, from the back: floor 1.2, USB-C 1.4–4.6 (centre 3.0), XIAO 4.6–5.6, carrier 5.6–6.6. With the XIAO on top, its USB-C would sit at z 7.6–10.8, inside the brass deck's rounded top edge with no wall round the opening. On the bottom, the opening sits in the plain gunmetal wall, exactly where the control drawing's side view puts it. The cells live under the middle of the board, where the bottom face is bare. Posted to Stage 5 as a request in `FIT.md`.

### Sealing (water resistant, not submersible)

The bar hangs above the water and sees splashes and condensation, not immersion.

- Tongue-and-groove parting line with a 1 mm silicone cord round the tongue.
- The diffuser, windows and oval lens are glued from inside on their flanges.
- The porthole plunger runs in a thin silicone boot.
- The USB-C plug is a tethered silicone-sleeved brass cap.
- Screws come from the back, under the rail.
- Conformal-coat the carrier (Stage 5's note).

## Stand-ins (removed by the fit check)

`PCB`, `XIAO`, `XIAO USB-C`, `APDS-9960`, `APDS-9251`, `Button SW`, `LED 1`–`LED 12` (listed in `fit.json`). `Cell 1` and `Cell 2` stay, since they're off-board. `Glow n` and `Lamp n` on the diffuser are display-only: they show the light in the renders, not parts.

## Shortcuts and open points

- The real finials would be separate turned or moulded caps, bonded on. Here they're solid bodies touching the ends.
- The scrollwork is simplified to a gear and two hex cut-outs on each end ramp, rivets, and the dark panel round the dome.
- The rail grooves leave a 0.7 mm wall to the cavity, which is thin. A real part might put the hooks in the end zones instead.
- **Light barrier (Stage 5):** a 0.6 mm rib across the dome's light path at x −115.87, the centre of the gap between the receiver window (−1.27) and the IR LED window (+1.43), per Stage 5. It runs from the deck top down to z 8.25, 0.3 mm above the sensor: a printed rib over a part on solder needs that margin. The dome's underside stays flat and clear.
- Paint: metallic "brass" paint must stay off the deck above the XIAO's antenna (+Y end of the XIAO, x 91–109). Use a non-metallic brass-tone there, or keep the whole finish non-metallic (antiqued with a dark wash).

## Host answers (2026-11-11)

1. **Dome:** smoky amber, see-through, faceted (clear to IR for the APDS-9960). Done.
2. **Width 26 mm:** approved.
3. **Filigree:** "play it up". Added a braided vine with beads on both gunmetal sides, an escutcheon and cartouche round the USB-C, whiplash scrolls on two dark panels, and etched lines along the LED window (`DESIGN.md`, "Filigree pass"). All of it is outside the shell, so the board and the fit are unchanged.

## Solidcraft log (this episode)

| Step | Result |
|---|---|
| Plan × side × front-section intersection (base, deck) | Works (~35 s for the whole blockout). Coincident faces between the three tools made the intersect fail ("no result"), so each tool overshoots by ≥0.5 mm where another sets that face |
| Deck ramp crossing the section's top at ~9° | Intersect failed (near tangent). Steepened to ~18°: works |
| Fillets on elliptical (finial) edges | "only straight edges can be blended". Finials made as lofts through 5–7 ellipses instead |
| Faceted dome: sphere cut by tilted planes | Failed (shallow-angle crossings, curved faces). A polyhedron of tapered polygon prisms (3 rings + flat crown), planes only: works |
| Round holes cut through the spline ramp | Failed (curved faces, shallow crossing). Hexagons and a gear outline (lines only): work |
| Running the deck ramp out to the body end (−138.2) | The section intersect failed in that order; the reversed order built but took 4× longer (2.4 min). Kept the ramp end at −136.6 |
| `solid.mirror` of a body | The copy is named "<name> (2)" (no body_name parameter) |
