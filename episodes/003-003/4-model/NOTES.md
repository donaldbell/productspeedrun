# 003 Baby Monitor Monitor: Stage 4 model notes

Two devices in one design (`model.solidcraft`), side by side on z 0:

- **Sensor** ("Wireless Mic Sensor"), centred at design x −40. It sits next to (or is VHB-taped onto) the parents' existing monitor and listens to its speaker.
- **Receiver** ("Wearable Haptic Receiver"), centred at design x +25. Worn on the wrist or ankle on a replaceable 20 mm elastic band.

The concept art draws the sensor at ~50 × 24 mm and the watch at 32 × 32 × 10 mm. Those numbers don't come from real parts, so the sizes below are worked out from the parts list (Stage 5 picked ESP32-C6-MINI-1 modules; LiPo, ERM motor, MEMS mic, USB-C, switches) instead.

## Design language

Y2K gadget: pearl/chrome-look white shells and a lavender accent piece. It borrows Oakley's swoosh parting line, Aibo-style soft lozenges, a MiniDisc-style dark grille disc, and a glowing magenta "Winamp" lens on the watch. Shells are moulded PC/ABS. The chrome look must be **NCVM** (non-conductive vacuum metallising) or pearl paint, because real metal plating would block the 2.4 GHz antennas.

## Sensor: 52 × 34 × 24 mm bean

| Part | Plan |
|---|---|
| Shell | Rounded-rect lozenge 52 × 34, plan corners R12, top edge R9, 1.8 wall, open at the bottom. It's split along a **tilted plane** (low at the front, high at the back) into a pearl upper shell and a lavender lower "swoosh" piece, the Oakley line from the concept. |
| Bottom plate | 1.8 mm, flush inside the shell. A light-grey **VHB pad** (0.8 mm) on the outside sticks it to the monitor. |
| Front | Ø16 **grille disc** (dark graphite) with a hex pattern of Ø1.2 holes, pointing at the monitor's speaker. A green **status slit** (2 × ~5.7) sits on the front corner, fed by a light pipe from the LED. |
| Top | Ø12 lavender **button cap** (press = test/pair, hold 3 s = on/off). |
| Back | **USB-C** opening. The concept also shows a slide switch and a second "connect" button; both are dropped (see below). |
| Inside | 602530 LiPo (6 × 25 × 30, ~500 mAh) on the bottom plate. 44 × 20 board (parts on both faces) on two M2 posts, 1.0 mm above the cell, top face 10.5 mm up. Mic at the board's front edge, opening into a small chamber behind the grille. |

**Choking hazard:** the small-parts cylinder is Ø31.7 mm. At 34 mm wide and 24 mm tall the sensor can't go into it in any orientation, so it isn't a small part. That's the reason it isn't shrunk to the concept's ~30 mm width.

## Receiver: 38 × 38 × 13.4 mm watch (+ lens dome), 20 mm quick-release band

| Part | Plan |
|---|---|
| Case | Square 38 × 38, plan corners R9, top edge R3.5, 1.6 wall, open at the back. Integrated lugs at 12 and 6 o'clock take standard **20 mm quick-release spring bars**, so washable elastic bands in any size swap in (wrist or ankle). |
| Top | 20 × 20 R6 frosted magenta **lens** (the "display"; it's a diffuser over an RGB LED, not a screen). A Ø1.6 green **link-LED pipe** sits at 6 o'clock under it, as in the concept. |
| Sides | Lavender **"I'm awake" button** at 3 o'clock, as in the concept. **USB-C** at 9 o'clock with a silicone plug (the band gets washed). |
| Back | 1.4 mm lavender back plate (skin side). The **ERM coin motor** is glued to it so the buzz goes straight into the skin. |
| Inside | 402025 LiPo (4 × 20 × 25, ~150 mAh) and a Ø10 × 2.7 ERM coin motor (Stage 5: MOSFET drive, no LRA driver IC) lie side by side on the back plate. A 30 × 30 R8 board (parts on both faces) hangs from two lid posts with heat-staked pins, 1.0 mm above the cell. Top face 8.1 mm up. |
| Band | Purple 20 × 1.6 elastic band (stand-in loop for a ~60 mm wrist), shown for scale. |

The concept is 10 mm thick; this one is 13.4 (+0.7 lens dome). The stack needs it: 1.4 back + 0.1 foam + 4.0 LiPo + 1.0 for bottom-face parts + 1.6 board + 3.3 tallest part (USB-C / side switch) + 0.4 gap + 1.6 top wall. A 1.0 mm board, a mid-mount USB-C and a 3 mm cell would win back about 2 mm.

## Board contract (fit.json)

`fit.json` uses Stage 5's `boards` layout, with one entry each for `sensor` (44 × 20, both faces) and `receiver` (30 × 30 R8, both faces). Both point at `4-model/model.solidcraft`, and the origins are in this shared design frame. Stand-in bodies are prefixed `S ` / `R `. Both boards are `provisional` until Stage 5's SIZE.md arrives.

## Open questions / shortcuts

- Sensor power: listening continuously on an ESP32-C6 (I2S + ESP-NOW TX) draws ~30 mA, so ~500 mAh lasts about one night. In practice it would stay plugged into USB, with the battery as backup. Should it be USB-only (smaller, no LiPo)?
- Receiver power: ESP-NOW receiving with light sleep, if the duty cycle is low enough, should fit 150 mAh in one night. Firmware has to prove it.
- The concept's slide power switch and second "connect" button on the sensor were dropped for a single button (tap = test/pair, hold = on/off). Do the hosts want the switch back?
- "I'm awake" button: the concept puts it on the side. A groggy parent would find it easier to hit by pressing the whole lens. That's an option if the hosts like it (it would be a visible change).
- The mic chamber behind the grille needs a foam gasket so the mic hears the monitor rather than the inside of the case.
- Watch IP rating: the band is washable but the case isn't. Gasket the back plate, plug the USB-C, or switch to pogo-pin charging later.
- Fasteners are first-pass: the sensor bottom plate and watch back plate are shown as drop-in plates (screws/snaps not modelled).
