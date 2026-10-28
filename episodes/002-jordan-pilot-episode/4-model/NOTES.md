# Gamer Companion: Stage 4 model notes

First-pass enclosure. The look comes from the favourite concept board: a charcoal chibi robot with angular cat ears, a smoked visor face with glowing ^ ^ eyes, a PIR "nose", green accent rings on the sides and little feet on the monitor bezel. The layout comes from the GA drawing: face cap plus rear shell, a blower breeze out of the mouth slots, speaker behind a side ring, USB at the back and a rear clip. The concept art wasn't based on real parts, so the dimensions here come from real, cheap parts.

## Overall form

- **Coordinates:** origin at the centre of the shell. **x** points to the robot's right as you face it, **y** points from the face towards the back, and **z** is up. The face is at y = −25. The monitor top is the plane the feet stand on (z = −33).
- **Shell:** 68 W × 50 D × 50 H. Front-view corners R14, front and back edges rounded R8, 2.0 wall.
- **Overall size:** **71 W × 73 H × 53 D mm (2.8 × 2.9 × 2.1 in)**. That covers ear tips (z 40) to the foot pads (z −34), ring to ring, and the PIR dome to the back. The rear clip and the 5 mm front lip hang below the monitor-top plane and aren't counted.
- **Split:** a vertical parting plane at **y = −12**. The **face cap** (front 13 mm) holds the board, lens, PIR and breeze slots. The **rear shell** holds the ears, blower, speaker, USB and clip. They join with 4 screws (TBD).
- **Colours:** charcoal shell, smoked visor, cyan eyes, white PIR dome, neon-green accents (ear inlays and side rings), black feet pads. That's the Razer / Alienware "dark with one neon accent" language, kept friendly by the chibi proportions.

## Parts

| # | Part | Notes |
|---|------|-------|
| 1 | **Face cap** (front shell) | Window 36 × 18 R5 behind the lens, Ø10.4 PIR hole, Ø1.2 mic port, 3 breeze slots ("mouth"), 4 board posts. The front feet have a lip that hooks the monitor's front edge. |
| 2 | **Rear shell** | Ears (solid triangular fins, 16 wide at the shell, tips at z 40 leaning outward), 5 intake slots in the floor under the blower, 4 blower stand-offs, speaker grille and retaining ring on the right wall, vent holes on the left wall, USB-C opening, 3 back vent slots, rear feet and clip knuckle. |
| 3 | **Visor lens** | Smoked PMMA, 44 × 24 R8 × 1.2, sits proud on the face. Eyes are 0.4 mm inlays (cyan), or masked back-paint in production. PMMA blocks the PIR's infrared, so the lens has a hole for the PIR dome. |
| 4 | **Side rings ×2** | Neon-green PC rings pressed into 1 mm grooves. The right ring frames the speaker grille. |
| 5 | **Ear accents ×2** | Green triangle inlays on the ear fronts (a 2-shot or pad-print later). |
| 6 | **Blower duct** | Takes air from the blower outlet to the mouth slots. |
| 7 | **Rear clip** | Hinged arm, shown deployed down the back of the monitor, with a friction hinge. |
| 8 | **Foot pads ×4** | TPU or adhesive silicone. |

## Electronics assumed (stand-ins in the model, sized from real parts)

| Part | Size (mm) | Where | Why |
|---|---|---|---|
| **ESP32-S3-WROOM-1-N16R8** | 18 × 25.5 × 3.1 | Back of the main board, antenna up | Dual-core with vector instructions, 8 MB PSRAM, I²S in and out, native USB. |
| **Main board** | 48 × 26 × 1.6, vertical | Right behind the face | One board for everything that must see out of the face: PIR, eye LEDs, mic. |
| **AM312-class PIR** | Ø10 body, ~13 tall to the lens tip | Board front, centre | Tiny, 3 V, digital out, ~15 µA. The lens pokes through the visor. |
| **2 × WS2812B-2020** | 2 × 2 × 0.8 | Board front, behind each eye | The "lights only for attention" eyes. Colour can match the reminder. |
| **I²S MEMS mic** (bottom port, ICS-43434 class) | 3.5 × 2.65 | Board back, port hole through the board, rubber boot to the face port | Voice commands ("snooze", "done", "I drank water"). |
| **MAX98357A** I²S amp | 3 × 3 | Board back | No codec needed. |
| **Speaker Ø28 × 5, 8 Ω 1 W** | Ø28 × 5 | Right wall, behind the ring grille | Big enough to be heard over a headset leak at speech level. |
| **5 V blower 30 × 30 × 10** (3010 class) | 30 × 30 × 10 | Flat on the floor, intake down through the floor slots, outlet forward through the duct | The "gentle breeze". It's driven by a MOSFET with PWM, and the feet keep an 8 mm air gap under the floor. |
| **USB-C breakout** (4-wire: VBUS, GND, D+, D−) | 12 × 14 board | Back wall | Power plus native-USB flashing. A short JST-SH harness runs to the main board. |

Stack front to back (y, mm): lens −26.2 to −25, wall −25 to −23, board posts −23 to −15, board −15 to −13.4, module −13.4 to −10.3, then open space. The blower sits at z −21 to −11 under the board, and the speaker at x 25.5 to 30.5.

## For Stage 5

The main board stands **vertically** in the XZ plane, with its front face at **y = −15**, facing the viewer. All positions below are **(x, z)** in enclosure coordinates, so the board's own X = enclosure x and Y = enclosure z.

- **Outline:** 48 × 26, corner radius R3, from x −24 to +24 and z −8 to +18. 1.6 mm thick.
- **Mounting holes:** 4 × Ø2.2 (M2 self-tapping) at **(−21, −5), (21, −5), (−21, 15), (21, 15)**. Keep the **front** side clear within Ø5.5 of each, because the posts land there.
- **Front side (faces the lens, max 8 mm tall except the PIR):**
  - **PIR** centred at **(0, 4)**. Its lens apex must reach y ≈ −28 (13 mm above the board's front face).
  - **Eye LEDs** at **(−11, 8)** and **(11, 8)**, firing forward. The lens is 10 mm away.
  - **Visible zone:** x −18 to 18, z −4 to 14 is seen through the smoked window. Keep it tidy (black solder mask would look best).
- **Mic port:** a Ø1.0 hole through the board at **(0, −6)**. The bottom-port mic sits over it on the **back** side, and a Ø4 rubber boot fills the 8 mm to the face port at the same (x, z).
- **Back side:**
  - **ESP32-S3-WROOM-1:** x 4 to 22, z −7.5 to 18, antenna at the **top** edge. Copper keep-out under the antenna (z > 12).
  - **Connectors along the bottom edge, x −22 to +2:** J1 USB harness (JST-SH 4-pin), J2 blower (JST-PH 2-pin, low-side MOSFET + flyback diode), J3 speaker (JST-PH 2-pin, from the MAX98357A).
  - Max height 6 mm.
- **Clearances:**
  - Below the board edge (z < −8) is the blower duct (top at z −12).
  - The speaker magnet is at x ≥ 25.5, so keep the antenna end at least 3 mm inside x = 22.

## What was built (SolidCraft, headless)

- **Source:** `build_model.py` generates `model_build.json`, and `solidcraft-cli run model_build.json --save model.solidcraft --out model.step --out model.stl` builds it in about 3 min. Named parameters: `width`, `depth`, `height`, `corner_r`, `edge_r`, `wall`, `split_y`. Every other dimension is a constant at the top of the script.
- **Outputs:** `model.solidcraft` (26 bodies: 16 enclosure parts and 10 electronics stand-ins), `model.step`, `model.stl`, `model.glb`, `iso.png`, `progress-01…03.png` (01: shell and face, 02: front view, 03: see-through shell with the stand-ins).
  - **`model.glb`:** the 16 visible parts in their colours (eyes slightly emissive), in metres, Y-up. `make_glb.py` exports each body from `model.solidcraft` without rebuilding.
  - **`model.stl`:** all bodies in one file for viewing. It isn't a print file, so export bodies one at a time for printing.
- **Checks:** every body is a single closed solid. The clearance check over all 26 bodies finds **no overlaps**. The side rings are seated in grooves cut with the ring itself, so they fit exactly (the checker can't intersect that pin-in-hole pair, so it lists them as unchecked).
- **Changes from the plan while modelling:**
  - The ears' roots run 3 mm into the cavity (z 20). A root that stops inside the 2 mm wall made the union fail on a near-tangent touch with the curved top.
  - The USB-C breakout ribs were trimmed to z −10.8 to clear the blower's top.
  - The ears were enlarged (tips at z 40) to read like the concept board.

## Shortcuts and open questions (first pass)

- **"Whisper on the ESP32" isn't realistic.** Even Whisper-tiny needs about 40 M parameters and far more RAM than an ESP32-S3 has. What the S3 can do on-device is Espressif's **ESP-SR** (WakeNet wake word plus MultiNet, about 200 fixed commands), which covers "snooze / done / drank water". Free-form speech-to-text would need an ESP32-P4 or a small Linux SoC, which means a bigger board and more power. The reminders are spoken from stored phrases, so no speech synthesis is needed on the device.
- **Power:** ESP32-S3 Wi-Fi bursts (~350 mA) + blower (~150 mA) + speaker peaks (~250 mA) can go over a 500 mA USB 2.0 port. The firmware should not run the fan and the voice at full power together, or the board should ask for 1.5 A with Type-C CC resistors on a USB-C charger.
- **Blower noise:** 3010 blowers whine at full speed. Run them at a low PWM duty for a "breeze", and test whether you can feel the air at 50–70 cm. A 40 mm axial fan would move more air but makes the head bigger.
- **PIR through a lens hole:** the dome is exposed, which is fine for a toy. It needs a field-of-view test from 50–80 cm, since the user sits just below the PIR's axis.
- **Fastening:** the face cap and rear shell need 4 screw bosses or snap hooks (not modelled). The rear clip's friction hinge is a placeholder (pin plus wave washer).
- **Ears are solid 10 mm fins.** For injection moulding they should be cored out to avoid sink marks.
- The lens inlays could be pad-printed or back-masked instead of separate parts.
