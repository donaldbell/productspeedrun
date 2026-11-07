# Baby Monitor Monitor Rev B: electronics

## Rev B changes (start here)

**Hosts' asks for Rev B:** keep the sensor's length (the 2000 mAh cell is a bonus for parents), drop the concept's "connect" button (pairing stays a long press of the top button), and make the top button **much larger and findable in the dark**: an elongated, alarm-clock-style **snooze bar**, **illuminated** in colour to show its state.

| Change | Parts | Why |
|---|---|---|
| **Snooze bar on two tacts in parallel** | SW3 (new, 1TS009 6 × 6 × 5) at board (−2, 0) joins SW1, which moves from (6, 0) to **(10, 0)**. Both on BTN (IO7, the LP GPIO that wakes the C6). | A 30 × 12 bar pressed at one end would rock on a single switch. Two switches 12 mm apart register a press anywhere along it. Tap = "I'm awake" (stop the buzz); hold 3 s = test / pair (this replaces the concept's connect button). The 12 mm spacing comes from the courtyards: two ±4.25 tacts with a 3.1 mm LED between. |
| **RGB bar light** | LED2 WS2812B-2020 at (4, 0) under the bar's light leg; R10 100 Ω series on the data line; C11 100 nF; data on **IO6** (module pad 15, next to the button's IO7). | It shows where the bar is in the dark, and the state. Firmware sketch: dim warm white = armed; slow amber pulse = watch buzzing (press me); blue breathing = paired / pairing mode on a long press; green blink = "I'm awake" registered; red = watch link lost; off at night if the parent prefers (a long press in the app/firmware later). One data pin, any colour. |
| **Bar light supply** | D2 1N5819WS + C10 1 µF: VBAR = **LDO_EN** (the power switch's output, = VSYS when on) − one Schottky. | This is episode 002's diode-dropped WS2812B block. VSYS is already one Schottky below USB, so a 1N5819WS (not 002's 1N4148W) gives ~4.45 V on USB: 0.7 × VDD = 3.1 V, so the C6's 3.3 V data reads high. On battery it gets ~VBAT − 0.3 (3.4–3.9 V): red and green fine, blue a little dim below ~3.7 V. Feeding it from the switch means the LED's ~1 mA idle draw stops when the sensor is switched off. The PCM12 now carries a few mA (rated 300 mA). |
| H2 post hole (12, −7.5) → **(12, −9.5)** | (fit.json) | The bar's flange needs the room. |
| Charger U1 → (15.4, −5.6), landscape; D1, Q1 back ~1.5 mm; R3 out of H2's new keep-out; TP1 out from under SW3 | (layout.py) | Room for SW1 at x 10. |
| BTN hand pre-routes | (layout.py) | Module IO7 → SW3 along the bottom at y −5.3, then SW1 → SW3 along the bottom at y −3.6, so the top under the bar stays clear for LED2 and its parts. |
| 3D model paths: five `../` (both boards) | (layout.py; the receiver's routed `.kicad_pcb` edited the same way instead of re-routed) | A revision folder sits one level deeper than an episode, so the fit check couldn't find the module and pogo-pin models. |
| Kit: `tidy_silk.py` treats non-plated holes as obstacles | (`tools/kicad/`) | It parked C9's label on the mic's port hole (Rev A fixed that by hand). |

### Rev B results

| | ERC | DRC | Fit check |
|---|---|---|---|
| Sensor | 0 errors, 0 warnings | 0 violations, 0 unconnected, 0 parity | **PASS**: 0 overlaps (5 intended gaps: posts 0.02, slider notch 0.03 on the PCM12 lever, slider 0.17 above the board, bar plunger 0.23 above the front tact, status pipe 0.23 above its LED) |
| Receiver | unchanged (0 / 0) | 0 violations, 0 unconnected, 0 parity | **PASS**: 0 overlaps (3 intended gaps, as Rev A) |

- **Routing:** the sensor took four rounds. LED2 can't sit between tacts closer than 11.7 mm (courtyards), so SW1 went to x 10. That crowded the power corner, so D2 and C10 moved in between the tacts. Freerouting kept dropping the status LED's anode (R9 bottom → LED1 top), so it is now pre-routed. Of four pass counts tried (10 / 20 / 30 / 40), the default 40 routed clean; the board in the folder is that run.
- **Fit check stand-in:** KiCad has no WS2812B-2020 model. The bigger Würth PLCC4 stand-in (2.05 tall) would have run 0.2 mm into the bar's light leg, so the kit gained a true-size stand-in, `tools/kicad/models/WS2812B-2020.step` (2.0 × 2.0 × 0.84), used for LED2. The receiver's glow LED keeps the taller stand-in; it passes with it, so it passes with the real part.
- **Fit check time:** about 2 h per board on this enclosure (the design's ~20 min open, then the clearance pass against the spline-trimmed shells). Run the two boards in parallel.

Pins: IO6 = BAR light (was unused). Everything else is as below. The receiver's circuit is unchanged.

---

# Rev A notes (as aired; Rev B changes above)

## Baby Monitor Monitor: electronics (Stage 5)

Two devices, so two boards, each a kit project of its own:

| Board | Folder | What it is |
|---|---|---|
| **Sensor** | `sensor/` (`bmm-sensor.*`) | the bean beside the baby monitor: listens, sends a loudness level, "I'm awake" button |
| **Receiver** | `receiver/` (`bmm-receiver.*`) | the sealed watch: buzzes at that level, glows, charges on pogo pins |

The kit gained multi-board support for this (see "Kit changes" below). `fit.json` has one entry per board under `boards`.

**Hosts' decisions mid-stage** (relayed by Stage 4, request in `FIT.md`). The first boards had a USB-C port and a side button on the watch, and a 400 mAh sensor with no switch. The hosts changed that to:
1. The sensor runs on a 103450 LiPo (~2000 mAh), so it works unplugged (camping). USB-C is the main power input and charges it.
2. The sensor gets a power slide switch, and its top button becomes "I'm awake": tap = ack, hold = test / pair.
3. The watch has no button and no USB, so it can be sealed and there's nothing to press by accident in bed. It charges through two pogo pins onto contacts in the back plate, with a magnetic clip-on charger.

Both boards were re-done for this and re-routed.

## Block diagram

```
SENSOR (USB-C powered, 2000 mAh backup)                    RECEIVER (sealed watch, 150 mAh)
ICS-43434 I2S mic ─► ESP32-C6-MINI-1 ──── ESP-NOW ────►   ESP32-C6-MINI-1 ─► AO3400A ─► ERM coin motor
"I'm awake" button ►  (RMS over 250 ms,   2.4 GHz         │                ─► WS2812B glow (face)
green status LED ◄─   3 thresholds → 0-3)                 │                ─► green link LED
USB-C ─► MCP73831 ─► LiPo 103450                          pogo + / − ─► 1N5819WS ─► MCP73831 ─► LiPo 402025
   └─► Schottky / P-FET power path ─► AP2112K 3V3 (EN = slide switch)         └─► AP2112K 3V3
```

- **Sensor:** sound pressure → I2S → the C6 computes RMS every 250 ms and compares it with three thresholds (quiet / fussing / crying / screaming → level 0–3). On a change, and as a heartbeat every few seconds, it sends the level over ESP-NOW. Tapping the button sends "awake" and stops the watch buzzing. The green LED shows on / linked / low battery / charging.
- **Receiver:** level 1–3 → three PWM duty cycles on the ERM, in a rising pattern until the "awake" message arrives, with the glow LED colour following the level. The link LED blinks while the heartbeat keeps arriving. If it stops, the LED goes dark and the watch gives a "lost link" buzz, which covers the failure that matters most to a sleeping parent.

## Part choices and why

- **ESP32-C6-MINI-1-N4 on both.** The brief says ESP32 with Bluetooth or ESP-NOW. ESP-NOW is the simplest link: no router, no pairing UI, ~1 ms latency, and it works between two ESP32s alone. The MINI module (13.2 × 16.6 mm) is the smallest Espressif module with a stock KiCad footprint. KiCad has no C3-MINI footprint, and the C3-WROOM-02 used before is 18 × 20. KiCad ships no 3D model for it, so the kit gained a body-sized stand-in (`tools/kicad/models/ESP32-C6-MINI-1.step`).
- **Flashing:** the sensor flashes over its USB-C (native USB, no buttons). The sealed watch is flashed on a pogo jig before the lens goes on, through test pads TP2 / TP3 (D+ / D−) plus the battery pads, and is updated over the air after that.
- **ICS-43434 I2S MEMS mic** (proven in 002). Digital, so there's no analog gain stage to tune. The bottom port sits over a hole through the board, toward the front grille.
- **ERM coin motor + AO3400A low-side switch + 1N5819WS flyback** (the proven fan-switch block from 002) is the "motor driver circuit". Intensity is PWM duty. An LRA would buzz more crisply but needs a driver IC (DRV2605L), so it's on the upgrade list.
- **MCP73831 charger + AP2112K-3.3 LDO** on both: common SOT-23-5 parts on LCSC. The AP2112K is the kit's proven LDO.
- **Watch charge input:** two SMD pogo pins (P1 +, P2 −; ~Ø1.8 × 5 mm, e.g. Mill-Max 0907) press on the back plate's contacts. A 1N5819WS in series blocks reverse polarity and keeps the cell off the exposed contacts, so sweat across them can't drain it.
- **Sensor power path:** 1N5819WS from USB plus an AO3401A from the cell (gate pulled to GND, held off by VBUS). It runs from USB when plugged in, so the charger can finish and stop instead of float-charging under load all night. Charge current is 256 mA (R3 3.9k): ~8 h to fill 2000 mAh, kept modest for the SOT-23-5's heat.
- **Sensor power switch:** C&K PCM12SMTR right-angle SPDT on the AP2112K's enable pin. Off means no 3.3 V, but the cell still charges from USB. It carries no load current, so a tiny switch is fine.
- **Internal pull-ups** for the button, the charger's STAT and the IO9 strap, and the C6's internal pull-down on the mic's SD line instead of the usual 100k, to save board area.

### Pins

| | Sensor | Receiver |
|---|---|---|
| IO0 (ADC) | VBAT_SENSE (VBAT / 2) | VBAT_SENSE (VBAT / 2) |
| IO1 | | CHG_STAT (pull-up) |
| IO2 | MIC_SD (pull-down) | MOT_PWM (~20 kHz) |
| IO3 | status LED | |
| IO4 / IO5 | MIC_SCK / MIC_WS | |
| IO6 / IO7 | Rev B: BAR light (WS2812B) / BTN "I'm awake" (both bar tacts; wakes from deep sleep) | glow LED (WS2812B) / link LED |
| IO8 | 10k pull-up (strap) | 10k pull-up (strap) |
| IO9 | boot strap, TP1 pad | boot strap, TP1 pad |
| IO12 / IO13 | USB D− / D+ (USB-C) | USB D− / D+ (TP3 / TP2, flashing jig) |
| IO21 | CHG_STAT (pull-up) | |

Pins were picked by layout: each signal uses the module pin on the side facing its part. The exception is the button, which has to sit on LP GPIO0–7 to wake the C6 from deep sleep.

## Power budget (first-pass estimates)

| | Sensor | Receiver |
|---|---|---|
| Idle | C6 with I2S running, light sleep between frames: ~20–25 mA | C6 listening for ESP-NOW with modem sleep: ~15–20 mA average (radio duty-cycled to the sensor's heartbeat) |
| Peak | TX burst ~250 mA for under 1 ms | motor ~80 mA + LED ~15 mA + TX |
| Battery | 2000 mAh: ~3 nights unplugged; normally on USB | 150 mAh: ~8–10 h, one night. Charges daily on the clip |
| Charge | 256 mA from USB-C (R 3.9k) | 100 mA from the pogo clip (R 10k) |

The watch's night on 150 mAh is the tightest number in the project. It depends on the C6 listening at a low duty cycle (ESP-NOW with a scheduled wake window, or BLE instead), which is firmware work. If that doesn't hold, the watch needs a bigger cell (thicker) or the sensor has to sleep the watch's radio between events.

## How it fits the enclosure

Read from `fit.json` (both devices are in one design, `4-model/model.solidcraft`: sensor at x −40, receiver at x +25). Both boards hang from posts in the upper shell / lid, with heat-staked pins through their holes and Ø4 kept clear round each.

- **Receiver: 30 × 30 R8** in the 38 × 38 sealed case. Glow LED under the 20 × 20 lens, link LED under the 6 o'clock light pipe, module antenna along the 12 o'clock edge with copper kept clear. Pogo pins on the bottom face at (5.5, −10) and (13, −5). LiPo (402025) and ERM sit under the board on wire leads; 0603s on the bottom over the cell. Top-face parts are ≤ 2.4 mm (the case allows 2.6).
- **Sensor: 52 × 24 R3** in the 60 × 42 × 28 bean. Mic and status LED at the front grille end, module front-left with its antenna on the +y edge, 6 × 6 × 5 "I'm awake" tact under the top cap, USB-C and power switch side by side at the back. The 103450 cell is 1.0 mm under the board; 0603s on the bottom.
- **Board area.** `SIZE.md` asks for ~1120 mm² (receiver, after losing the USB-C and button) and ~1540 mm² (sensor). The boards are 870 and 1250 mm². Both use the bottom face for passives and both routed.

## Kit changes

- **Multi-board products:**
  - `tools/fit/fitlib.py`: `fit.json` may hold `{"boards": {name: {...}}}`, and `load_fit(path, board=None)` picks the board from a `5-electronics/<name>/` path or the `board=` argument.
  - `fitmd.py` writes one Fit subsection per board.
  - `fitcheck.py` checks one board (`episodes/<slug>/5-electronics/<board>`) or every board (the episode folder).
  - `env.py`, `build.sh`, `export.sh` and `new_board.sh` treat any folder holding `src/` as a board folder.
- `tools/kicad/models/`: stand-in models for `ESP32-C6-MINI-1.step` and `PogoPin_D1.8mm_H5.0mm.step`. `MODEL_SUBST` now also works on footprints that ship with no model at all.
- `HOLE_CLEARANCE` layout option, written into the project's DRC rules. The stock GCT USB4105 footprint has its GND pads 0.19 mm from its locating-peg holes, below the kit's 0.25 mm, so the sensor uses 0.18. Check that against the fab's NPTH-to-copper rule (JLC: 0.2 mm) before ordering, or use the HRO TYPE-C-31-M-12 footprint.
- `gen_pcb.py` sets each footprint's BOM / position-file flags to match its symbol (KiCad's test-pad footprints come excluded). `build.sh` now counts schematic-parity errors as violations.

## Open questions

- Watch battery life on 150 mAh (above). Measure it on a dev board before committing to the case thickness.
- Pogo pins: pick the real part (stroke, force, ~5 mm working height) and match it to the clip charger. The back-plate contacts need gold plating and a seal.
- The sensor's PCM12 lever is short (1.55 mm past its body, tip 0.3 mm inside the board edge). Stage 4's slider cap reaches in to it with a notch round the lever. Check the slide feel on the first print.
- LCSC numbers are left blank where I couldn't confirm them (ESP32-C6-MINI-1-N4, GCT USB4105-GF-A, PCM12SMTR, 1TS009 tact, ICS-43434, pogo pins). Check stock before ordering.
- The WS2812B-2020 runs from VBAT (3.0–4.2 V). Below ~3.5 V the blue channel dims. That's fine for a glow, but a plain pink LED may be all it needs.
- The ERM runs from VBAT and is 3 V rated: firmware caps its duty at ~70 % on a full cell.
- No ESD protection on the sensor's USB or the watch's exposed charge contacts (a first-pass shortcut). Add a USBLC6-2SC6 / TVS if there's room.
- With no button, the watch can't be turned off, and the wearer can only stop a buzz from the sensor. Is a "stop buzzing" gesture wanted (a tap, via an accelerometer)?

## Results

| | ERC | DRC | Fit check |
|---|---|---|---|
| Receiver | 0 errors, 0 warnings | 0 violations, 0 unconnected, 0 parity | **PASS**: 0 overlaps |
| Sensor | 0 errors, 0 warnings | 0 violations, 0 unconnected, 0 parity | **PASS**: 0 overlaps |

- **Receiver fit:** 3 gaps under 0.3 mm, all intended. The board rests on its posts (0.02, lifted for the check). The + pogo pin's tip is 0.09 off its back-plate contact; a real pin is compressed there, so it presses. The link light pipe is 0.23 above its LED.
- **Sensor fit:** 6 gaps under 0.3 mm, all intended or harmless. The board rests on its posts (0.02). The slider cap's notch is 0.03 off the PCM12 lever, a snug fit so it drives the lever, and its underside is 0.17 above the board. The cell is 0.18 under a bottom 0603, the button cap 0.23 above the tact, and the light pipe 0.24 above the LED. The first run failed: KiCad's PCM12 model has the lever at one end of its travel (y 5.75, not 6.5), so Stage 4 moved the slider to that end.
- **How the routing got to 0 / 0:** both boards were routed in parallel scratch copies with different Freerouting pass counts, and the clean one was kept. The sensor (`ROUTE_PASSES` 20) needed two hand pre-routes in `layout.py`: BTN, half the board's length from IO7 to the button, and MIC_SD round the mic's VDD pad. Freerouting kept leaving those open. C9's reference was moved off the mic's port hole by hand. On the receiver, P1 / P2's BOM flags were set to match their symbols, a fix that's now in `gen_pcb.py`.
- **Kit fix found during the fit checks:** `fitmd.py` wrote `FIT.md` through a fixed `FIT.md.tmp`, so checking two boards at once crashed one of them. The temp name is now per process.
