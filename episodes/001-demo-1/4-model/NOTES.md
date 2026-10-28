# Backpack Defender: Stage 4 model notes

First-pass enclosure. It takes its look from the favourite concept (mint pebble with a kawaii face, purple dome, big friendly button) and its layout from the favourite CAD sheet (2×AAA under a board, face on the lid, dome and button on the right). The dimensions come from real, cheap parts, not from the art.

## Overall form

- **Size:** 76 × 51 × 26 mm (3 × 2 × 1 in, "deck of cards"). It lies on its big flat side in a locker, and that same side faces out on a backpack.
- **Shape:** a soft pebble: a rounded rectangle (R12 corners), a generous R7 round on the top edge and a small R1.5 round on the bottom edge.
- **Wall:** 2.0 mm (PLA/PETG for a prototype, ABS/PC for injection moulding later).
- **Colours (kawaii, gender-neutral pastels):**
  - lid: mint
  - base: butter yellow
  - bottom plate and battery door: lavender
  - big button: coral
  - PIR dome: lavender
  - face: dark plum eyes and smile with pink cheeks, as flush inlays

## Parts

| # | Part | Notes |
|---|------|-------|
| 1 | **Lid** (upper housing) | z 12–26. Carries the face, the Ø24 big-button opening, the Ø10.4 PIR dome opening and a 3-slot speaker grille on the front. |
| 2 | **Base** (lower housing) | z 0–12. Open bottom, with a kawaii "charm loop" tab (Ø4 hole) on the left end for a keyring, carabiner or zip tie. That's the "clip/tie to a backpack" option. |
| 3 | **Bottom plate** | Sits in the base's bottom opening. Four posts hold the PCB, with a battery-door opening. |
| 4 | **Battery door** | Pops out so a teacher can pull the AAAs to disarm it. Thumb notch. |
| 5 | **Big "silence" button** | A Ø24 pill-dome cap that stands 2.5 mm proud. A flange under the lid keeps it captive, and it presses a 12×12 mm tact switch. |
| 6 | **Face inlays** | Eyes (with highlight islands), smile and cheeks, sitting flush in 0.6 mm pockets. Print in a second colour, or pad-print later. |

## Electronics assumed (stand-in bodies in the model)

| Part | Size (mm) | Why |
|---|---|---|
| **ESP-12F** (ESP8266) | 24 × 16 × 3.2 | Cheapest Wi-Fi module that runs a SoftAP settings page. It has I2S out, and it's flat, unlike the ESP-01 in the art, which needs a tall header. |
| **MAX98357A** I2S class-D amp | 3 × 3 QFN on the board | Common, cheap, needs no codec. Drives the transducer. |
| **Piezo transducer** (12 mm, low profile) | Ø12 × 3 | Behind the front grille. *Open question:* a 20–28 mm 8 Ω micro speaker would sound better for "musical" tones. |
| **AM312 mini PIR** | Ø10 lens, ~14 tall | Its dome pokes 4 mm through the lid, giving the purple "eye" dome. It faces up, which suits a locker (hand or door) and a backpack (someone reaching). |
| **12 × 12 × 7 mm tact switch** | 12 × 12 × 7.0 | Under the big button. |
| **2 × AAA holder** (side by side) | 52 × 25 × 12 | 3 V straight to the ESP8266 (via a low-dropout regulator or a small boost converter, see open questions). |
| PCB | 70 × 45 × 1.6, R9 corners | Sits on 4 posts at z 14.5, above the batteries. |

Stack (z, mm): floor 0–2, AAAs 2–14, PCB 14.5–16.1, parts up to ~23, lid top 24–26, button top ~28.5, PIR dome ~30.

## What was built (SolidCraft, headless)

- **Source:** `build_model.py` generates `model_build.json`, which runs through `solidcraft-cli run`. Named parameters: `length`, `width`, `height`, `wall`, `top_round`, `split_z`. Every other dimension is a constant at the top of the script.
- **Outputs:** `model.solidcraft` (17 bodies: 11 enclosure parts and 6 electronics stand-ins), `model.step`, `model.stl`, `model.glb`, `iso.png` and `progress-01…03.png`.
  - **`model.glb`:** the 11 visible parts (enclosure, button, face inlays, PIR dome) in their colours, scaled to metres and rotated to Y-up for the web viewer.
  - **`model.stl`:** all bodies in one file for viewing. Parts that touch (inlays in their pockets, parts on the PCB) share faces, so it isn't a print file. Export each body on its own for printing.
- **Checks:** every body is a single closed solid. A clearance check over all 17 bodies shows **no overlaps**; the only contacts are the intended resting ones.
- **Changes from the plan while modelling:**
  - The big button moved to x = 18 with a Ø27 captive flange (Ø28 clipped the lid's inner round).
  - The cheeks moved to x = −24.5 / 2.5 to stay clear of the button opening.
  - The bottom round is 1.0 mm, applied after hollowing (1.5 before hollowing wouldn't offset).

## Shortcuts and open questions (first pass)

- **LiPo vs AAA:** the Stage 4 request mentioned "a small LiPo battery", but the brief and both favourite images use AAA cells so teachers can disarm it easily. The model uses **2 × AAA**. If a LiPo is wanted, a 502535 (5 × 25 × 35) fits in the same bay, but it would need USB-C charging and adds cost.
- **Running ESP8266 Wi-Fi off 2 × AAA:** the module needs about 3.0–3.6 V at bursts of ~300 mA. Two alkaline cells sag below 3 V when they're low, so a small boost converter (e.g. TPS61023) is probably needed. 3 × AAA would make the case about 10 mm longer.
- **Fastening:** the lid, base and bottom plate are not yet fastened together (snap lip or screws TBD). The battery door has no latch yet.
- **No power switch:** pulling a battery disarms it. A slide switch could go on the right end. The setup page could be reached by holding the big button at power-on.
- The PIR window and lens choice need a real test inside a locker.
- The face could be pad printing or a sticker in production, instead of inlays.
