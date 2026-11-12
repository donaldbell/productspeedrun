# Stage 5 notes: Color-Sensing Aquarium Accent Light (episode 004)

## Summary

**Done.** A routed 2-layer **XIAO ESP32-C6 carrier**, 248 × 21.4 × 1.0 mm (the brief's `boardStyle: "carrier"`). It's the first carrier in the series, so the kit gained the XIAO symbol, footprint, stand-in model and a footprint library. **ERC 0, DRC 0 violations / 0 unconnected, fit check PASS (0 overlaps).**

- **Inside:** XIAO ESP32-C6 (MCU, USB-C, charger, 3.3 V) soldered flat on the bottom face; 12 × WS2812B-2020 behind the window squares on a P+N FET high-side switch; APDS-9960 IR reflectance / ambient sensor under the dome (fish motion near the surface, "tank is dim"); APDS-9251 RGB sensor under the chrome oval (tank colour); PTS810 porthole button; VBAT and USB-present sense; 2 × ~600 mAh pouch cells, about 4 nights at a dim 5 h a night.
- **Left for the hosts:** confirm the XIAO's battery pads and antenna end on a real board before ordering (see "Open questions").
- **No open requests** in `FIT.md` either way. The last one (more room round the USB-C) is done: Stage 4 opened the port to 9.6 × 4.0.

## Decisions from the host (chat, 2026-11-11)

- **USB-C on the long side edge** (−Y side near the electronics end), behind a gasketed brass plug, as in Stage 4's `DESIGN.md`. The XIAO lies *across* the bar with its USB-C at the board's −Y edge. No port faces the water, and the finials stay solid. (Pogo pins were considered. Rev A keeps the brief's plain USB-C. Pogo pads are an easy Rev B change: two pads into the XIAO's 5V pin through a Schottky.)
- **No PIR.** A PIR sees far-infrared, which water absorbs within millimetres and glass blocks, so it can't see fish from under the lid. Motion and colour come from **optical reflectance sensors** instead (see "Sensors").
- **One long board** carries the LEDs, sensors, button and XIAO. No separate LED strip.
- **Runtime:** dim, sleep-friendly mood light, on for **4–6 h a night** by default (adjustable). The target is **several nights per charge**.

## Block diagram

```
 2 x LiPo pouch (parallel) ──J1/J2──► VBAT ─┬─► XIAO BAT+ pad (XIAO charges it from USB-C)
                                           ├─► Q1 P-FET high-side switch ─► VLED ─► 12 x WS2812B-2020 (chain)
                                           ├─► APDS-9960 IR LED anode (LEDA)
                                           └─► R1/R2 200k:200k ─► VBAT_SENSE (D0)
 XIAO 5V pin (VBUS when USB is in) ─► R3/R4 ─► VBUS_SENSE (D1): "charging" wakes the C6
 XIAO 3V3 ─► APDS-9960 (dome: proximity + gesture + ambient)   ┐ I2C on D4/D5
           ─► APDS-9251 (oval window: RGB + IR colour sensor)   ┘ 4.7k pull-ups
 Porthole button ─► D2 (LP GPIO: wakes from deep sleep, opens the Wi-Fi control panel)
```

## Part choices

| Block | Part | Why |
|---|---|---|
| MCU, USB-C, charger, 3.3 V | **Seeed XIAO ESP32-C6**, soldered flat by its castellations | The brief's ESP32 via the carrier rule. C6 over C3/S3: **on-board ceramic antenna** (the C3 and S3 need a flying FPC/U.FL antenna inside a slim bar), the lowest deep sleep (15 µA), LP GPIOs D0–D2 for wake, and no strapping pins on the castellations. Soldered flat, not socketed: the bar is ~11 mm thick, and 2.54 mm sockets would add ~8 mm. |
| Fish motion | **Broadcom APDS-9960** (proximity / gesture / RGBC / ambient), I2C 0x39, under the faceted dome | An optical reflectance sensor: its IR LED pulses and it reads what comes back. Fish rising near the surface change the return. It also gives ambient light for "tank is dim → lights on". KiCad ships the footprint (`Sensor:Avago_APDS-9960`). |
| Tank colour | **Broadcom APDS-9251-001** RGB + IR, I2C 0x52, behind the chrome oval window | A real RGB sensor (separate R, G, B and IR channels, up to 20-bit), so colour matching isn't stuck with the 9960's coarse RGBC. Firmware lights the tank white for a moment through the main LEDs and reads the reflected colour. No extra illuminator. KiCad ships symbol and footprint. |
| Light | **12 × WS2812B-2020** at the 12 squares of the LED window | Proven on episode 002, stand-in model in the kit. 12 matches the concept and keeps idle current low. |
| LED power | **AO3401A** P-FET high side + **AO3400A** driver | WS2812s draw ~0.7–1 mA each even when dark, so the whole chain is switched off outside the night window. |
| Button | **C&K PTS810** 4.2 × 3.2 × 2.5 mm SMD tact | Low enough to sit under the porthole boss. Wakes the C6 and opens the control-panel access point. |
| Battery | 2 × LiPo pouch ~4 × 20 × 80 mm (~600 mAh each), parallel, on solder pads J1 / J2 | Lie on the back of the board in the long middle section, ≥10 mm clear of the XIAO's antenna end. Cells with their own protection PCBs. |

## Pin budget (XIAO ESP32-C6, 11 I/O)

| XIAO pin | GPIO | Net | Note |
|---|---|---|---|
| D0 | GPIO0 (LP, ADC) | VBAT_SENSE | VBAT / 2 through 200k / 200k (Seeed's suggested divider), 100 nF |
| D1 | GPIO1 (LP, ADC) | VBUS_SENSE | 5V pin × 0.6 (100k / 150k) ≈ 3.0 V when USB is in; 0 V on battery (Seeed: "no voltage on the 5V pin" on battery). Wakes the C6 on plug-in |
| D2 | GPIO2 (LP) | BTN | Porthole button to GND, 10k pull-up: deep-sleep wake |
| D3 | GPIO21 | LED_IO → 100 Ω → LED_DIN | WS2812 data |
| D4 | GPIO22 | SDA | 4.7k to 3V3 |
| D5 | GPIO23 | SCL | 4.7k to 3V3 |
| D6 | GPIO16 | LED_EN | LED power switch, 100k pull-down (LEDs off at boot) |
| D7 | GPIO17 | RGB_INT | APDS-9251 INT, open drain, 10k pull-up (the colour sensor is beyond this side of the XIAO) |
| D8 | GPIO19 | PROX_INT | APDS-9960 INT, open drain, 10k pull-up (D8, not D7: pin 8 sits in the antenna keep-out) |
| D9, D10 | GPIO20, GPIO18 | spare | |
| BAT+ / BAT− | (underside pads) | VBAT / GND | Pads on the carrier under the XIAO's battery pads, reflowed together |

The XIAO is on the carrier's **bottom** face (Stage 4: that puts its USB-C in the gunmetal base, not the deck's rounded edge), so its D0–D6 row faces the LEDs and dome (−x) and the D7–D10 / power row faces the bar's end (+x). A dry run with the XIAO on top left LED_EN and PROX_INT unrouted where they had to wrap round it.

## Power budget

| State | Draw | Notes |
|---|---|---|
| Day, deep sleep | ~30 µA | C6 15 µA, VBAT divider 10 µA, both sensors in sleep ~2 µA, LED chain switched off. Wakes every 60 s to read ambient light (~20 µA average). About 1 mAh a day. |
| Night, lights on, Wi-Fi off | ~55 mA | C6 ~20 mA (light sleep between 30 fps frames), WS2812 idle 12 × ~1 mA, dim mood light ~5 % of full ≈ 22 mA, APDS-9960 proximity ~1 mA |
| Control panel open (AP) | +~80 mA | Only on demand: button press, USB plug-in, and the first 10 min after power-up; closes after 10 min idle |
| Peak | ~450 mA | All 12 LEDs full white for a colour reading flash (a fraction of a second) |

A 5 h night costs ~280 mAh (plus ~15 mAh for a control-panel session). With 2 × 600 mAh ≈ **1200 mAh, about 4 nights per charge**. At a brighter 10–15 % that drops to ~2–3 nights.

**WS2812B-2020 from the cell:** VLED is VBAT through Q1, 3.0–4.2 V. 3.3 V data meets their input-high (0.7 × VDD ≤ 2.94 V at 4.2 V), so no level shifter is needed. Below ~3.6 V the blue channel fades, so firmware stops the lights at VBAT 3.5 V and asks for a charge. Rev B could add a 5 V boost.

## How it fits the enclosure

From `fit.json` (Stage 4 wrote it, Stage 5 changed the antenna keep-out; the request log is in `FIT.md`):

- **Board 248 × 21.4 mm, R3, 1.0 mm thick**, top face at enclosure z 6.6, running almost the whole bar (x −124…124). 4 M2 holes at (−120, ±7.5) and (121, ±7.5); one rest post under the middle at (−5.5, 0) between the cells.
- **Top face (the LED face, toward the water):** APDS-9960 under the dome (−116, 0), PTS810 under the porthole plunger (−98.5, 0), 12 WS2812B-2020s on the window squares (x −82…77, every 14.5 mm), the LED power switch between cell B's pads and the XIAO (x ≈ 84…88), and the APDS-9251 under the chrome oval (116.5, 0). Above the XIAO, the deck's smoked **viewing window** (19 × 16 at (98, 0)) shows the board, so that patch has no parts, just gold-silkscreen gears and "N° 004".
- **Bottom face:** the **XIAO ESP32-C6** soldered flat at (100, −0.2), USB-C at the −y edge. Stage 4 moved it here: on top its USB-C would land in the deck's rounded edge, but on the bottom it sits at z ≈ 3.2 in the gunmetal base, behind the side plug. Beside its D0–D6 row are the sense dividers and pull-ups (0603s, x 84…89). The two cells lie on the floor under x −89…78, 0.3 mm below the bare bottom face. Their leads come up through J1 (x −93) and J2 (x 81.5), just past each cell's tab end.
- **Antenna keep-out** (both layers): (93.5, 7.0, 106.5, 10.7), the XIAO's ceramic antenna between its pin rows at the far end. It starts at y 7.0, clear of the BAT pads (y 3.9…6.6), and stays inside the pad rows so the D6 / D7 castellations at that end can route out. That cost one routing pass to find.

## Open questions

- **XIAO battery pads.** Seeed's own `XIAO-ESP32-C6-SMD` KiCad footprint (OPL library) has two unnamed 2.5 × 1.1 mm underside pads at the D5/D8 row height. The wiki says BAT− sits by the D8 marking and BAT+ by the D5 marking, so Seeed's pad 23 = BAT+ and pad 24 = BAT− (renumbered 15 and 16 in the kit footprint). **Check against a real board before ordering.**
- **XIAO ESP32-C6 antenna end.** Taken as the end opposite the USB-C (ceramic antenna + U.FL). Check against a board. The carrier keeps copper out from under it.
- **XIAO ESP32-C6 charge current** isn't stated by Seeed (other XIAOs are ~100 mA). At 100 mA, 1200 mAh takes ~12 h: an overnight charge.
- **Dome material (settled).** The hosts chose a see-through smoky-amber dome (Stage 4, 18a2f4b), which answers the IR-path question: a milky dome would have scattered the APDS-9960's IR back into its own receiver. Amber and smoke dyes are usually near-clear at 950 nm, but tinted plastics vary, so check the chosen resin with the sensor's proximity reading before committing. Stage 4 added a 0.6 mm light-barrier rib across the dome (820479a) and kept the dome's underside flat and clear. In the footprint the receiver window is at −1.27 mm and the IR LED window at +1.43 mm along x, so the rib is centred on the gap between them at x −115.87 (0.55 mm clear of each window). The fit check measures it 0.20 mm above the sensor.
- **Proximity through water** only reaches a few cm: water absorbs the 950 nm IR. Fish are seen near the surface. Firmware also watches the APDS-9251's colour for fast flicker as a second motion cue.
- **Paint.** If the "brass" is a metallic paint with real metal flakes, it must stay off the area above the XIAO's antenna.
- **Humidity.** Conformal-coat the carrier (not the XIAO's USB-C or button).

## Questions for the hosts

- None open. (The dome question is answered: see-through smoky amber.)

## Kit changes (tools/kicad)

The first XIAO carrier, so the kit gained:

- `parts.xiao_esp32c6()` symbol (D0–D10, 3V3, GND, 5V, BAT+, BAT−) and `parts.apds9960()`.
- A kit footprint library, `footprints/ProductSpeedrun.pretty`, with `Seeed_XIAO_ESP32C6_SMD` (Seeed's OPL pads, re-centred, with BAT pads). `pcbkit.load_fp` looks there first, and the schematic build writes an `fp-lib-table` so KiCad finds it.
- Stand-in STEPs (made in Solidcraft): `Seeed_XIAO_ESP32C6.step`, `APDS-9960.step` (KiCad's footprint names a model it doesn't ship) and `Broadcom_LGA-8_2x2mm.step`.
- **Board thickness from `fit.json`.** Before this, every board was exported at KiCad's default 1.6 mm, whatever `fit.json` said. This board's first fit check put a 1.6 mm PCB into both cells. `gen_pcb.py` now sets it from `board.thickness` (or `layout.BOARD_THICKNESS`).
- 150k and 200k resistors in `schkit.RES`. The self-test (`selftest.sh place`) still passes after these changes.

## Results

- **ERC:** 0 violations (`erc.rpt`).
- **DRC:** 0 violations, 0 unconnected (`drc.rpt`), routed on the first Freerouting try.
- **Fit check:** **PASS**, 0 overlaps (`fitcheck.md`, `fitcheck.png`). Near misses: Deck–PCB 0.03, Port Cap–PTS810 0.09, Deck–XIAO 0.10, Base–PCB 0.11, USB Plug–XIAO 0.15 mm.
- **How it got there:**
  1. First fit check: the kit exported a 1.6 mm board into both cells. Fixed in the kit: thickness now follows `fit.json`.
  2. Then the USB-C met the plug and the wall. Stage 4 re-centred the opening at z 3.2 and moved the plug out to y −12.05.
  3. Then the stand-in's square USB-C corners clashed with the stadium opening. The stand-in now has a real shell's round ends.
  4. The checker then reported Base–XIAO at 0.00 mm. Stage 4's probes showed a real 0.2 mm gap: two nearly concentric arcs (R1.6 inside R1.8) seem to fool `inspect.clearance`. Stage 4 opened the port to 9.6 × 4.0 (R2.0 ends) anyway, and the contact is gone.
