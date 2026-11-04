# Baby Monitor Monitor: electronics (Stage 5)

Two devices, so two boards, each a kit project of its own:

| Board | Folder | What it is |
|---|---|---|
| **Sensor** | `sensor/` (`bmm-sensor.*`) | the puck stuck to the baby monitor: listens, sends a loudness level |
| **Receiver** | `receiver/` (`bmm-receiver.*`) | the watch-sized wearable: buzzes at that level, "I'm awake" button |

The kit gained multi-board support for this (see "Kit changes" below). `fit.json` has one entry per board under `boards`.

## Block diagram

```
SENSOR                                                RECEIVER
ICS-43434 I2S mic ─► ESP32-C6-MINI-1 ── ESP-NOW ──►  ESP32-C6-MINI-1 ─► AO3400A ─► ERM coin motor
top button ───────►  (RMS over 250 ms,     2.4 GHz    │                ─► WS2812B glow (face)
green status LED ◄─   3 thresholds → 0-3)  ◄── ack ── │                ─► green link LED
USB-C ─► MCP73831 ─► LiPo 400 mAh                    side "awake" button
   └─► Schottky / P-FET power path ─► AP2112K 3V3    USB-C ─► MCP73831 ─► LiPo 150 mAh ─► AP2112K 3V3
```

- **Sensor:** sound pressure → I2S → the C6 computes RMS every 250 ms and compares it with three thresholds (quiet / fussing / crying / screaming → level 0–3). On a change, and as a heartbeat every few seconds, it sends the level over ESP-NOW. The green LED shows on / linked / low battery.
- **Receiver:** level 1–3 → three PWM duty cycles on the ERM motor, in a rising pattern until the wearer presses the side button. The press is sent back to the sensor, and the glow LED colour shows the level. The link LED blinks green while the heartbeat keeps arriving and goes dark (with a "lost link" buzz) if it stops. That covers the failure that matters most to a sleeping parent.

## Part choices and why

- **ESP32-C6-MINI-1-N4 on both.** The brief says ESP32 with Bluetooth or ESP-NOW. ESP-NOW is the simplest link: no router, no pairing UI, ~1 ms latency, and it works between two ESP32s alone. The MINI module (13.2 × 16.6 mm) is the smallest Espressif module with a stock KiCad footprint. KiCad has no C3-MINI footprint, and the C3-WROOM-02 used before is 18 × 20. It has native USB, so flashing goes over the USB-C and needs no boot buttons. KiCad ships no 3D model for it, so the kit gained a body-sized stand-in (`tools/kicad/models/ESP32-C6-MINI-1.step`).
- **ICS-43434 I2S MEMS mic** (proven in 002). Digital, so there's no analog gain stage to tune. The bottom port sits over a hole through the board, toward the front grille.
- **ERM coin motor + AO3400A low-side switch + 1N5819WS flyback** (the proven fan-switch block from 002) is the "motor driver circuit". Intensity is PWM duty. An LRA would buzz more crisply but needs a driver IC (DRV2605L), so it's on the upgrade list.
- **MCP73831 charger + AP2112K-3.3 LDO** on both: common SOT-23-5 parts on LCSC. The AP2112K is the kit's proven LDO.
- **Sensor power path:** 1N5819WS from USB plus an AO3401A from the cell (gate pulled to GND, held off by VBUS). The sensor usually lives plugged in, so it runs from USB and the charger can finish and stop, instead of float-charging under load all night.
- **No power switch.** On the sensor, holding the top button sends the C6 to deep sleep and pressing it wakes it up (IO3 is an LP GPIO). The receiver has no switch at all, because it should never be accidentally off.
- **Internal pull-ups** for the buttons, the charger's STAT and the IO9 strap, and the C6's internal pull-down on the mic's SD line instead of the usual 100k, to save board area (these are very tight boards).

### Pins

| | Sensor | Receiver |
|---|---|---|
| IO0 (ADC) | VBAT_SENSE (VBAT / 2) | VBAT_SENSE (VBAT / 2) |
| IO1 | | CHG_STAT (pull-up) |
| IO2 | MIC_SD (pull-down) | MOT_PWM (~20 kHz) |
| IO3 | status LED | BTN (wakes from deep sleep) |
| IO4 / IO5 | MIC_SCK / MIC_WS | |
| IO6 / IO7 | — / BTN (wakes from deep sleep) | glow LED (WS2812B) / link LED |
| IO8 | 10k pull-up (strap) | 10k pull-up (strap) |
| IO9 | boot strap, TP1 pad | boot strap, TP1 pad |
| IO12 / IO13 | USB D− / D+ | USB D− / D+ |
| IO21 | CHG_STAT (pull-up) | |

Pins were picked by layout: each signal uses the module pin on the side facing its part. The exception is the buttons, which have to sit on LP GPIO0–7 to wake the C6 from deep sleep.

## Power budget (first-pass estimates)

| | Sensor | Receiver |
|---|---|---|
| Idle | C6 with I2S running, light sleep between frames: ~20–25 mA | C6 listening for ESP-NOW with modem sleep: ~15–20 mA average (radio duty-cycled to the sensor's heartbeat) |
| Peak | TX burst ~250 mA for under 1 ms | motor ~80 mA + LED ~15 mA + TX |
| Battery | 400 mAh: 16+ h unplugged (it normally runs on USB) | 150 mAh: ~8–10 h, i.e. one night. Needs nightly charging |
| Charge | 210 mA (R 4.7k) | 100 mA (R 10k) |

The receiver's night on 150 mAh is the tightest number in the project. It depends on the C6 listening at a low duty cycle (ESP-NOW with a scheduled wake window, or BLE advertising instead), which is firmware work. If that doesn't hold, the receiver needs a bigger cell (a thicker watch) or the sensor has to sleep the receiver's radio between events.

## How it fits the enclosure

Read from `fit.json` (both devices are in one design, `4-model/model.solidcraft`: sensor at x −40, receiver at x +25):

- **Receiver: 30 × 30 R8**, top face up, hung from two lid posts (Ø3.6, heat-staked pins through H1 (−10.5, 10.5) and H2 (10.5, −10.5)), USB-C at 9 o'clock, side button at 3 o'clock, glow LED under the 20 × 20 lens, link LED under the 6 o'clock light pipe. Module antenna along the 12 o'clock edge with copper kept clear. LiPo and ERM sit under the board on wire leads.
- **Sensor: 44 × 20 R3**, top face up, hung from two upper-shell posts (H1 (−19, −7.5), H2 (12, −7.5)): a floor post would have gone through the cell, USB-C at the back, 6 × 6 tact under the top cap, mic and status LED at the front grille end. Module front-left with its antenna along the +y edge. LiPo under the board.
- **Board area.** `SIZE.md` asks for ~1410 mm² (receiver) and ~1420 mm² (sensor). The shells hold ~900 and 880. Both boards put 0603 passives on the bottom face to make up some of the gap. This is the riskiest assumption here: if Freerouting can't finish at this size, the boards grow, and that needs the hosts' OK (beyond 10 %).

## Kit changes (for multi-board products)

- `tools/fit/fitlib.py`: `fit.json` may hold `{"boards": {name: {...}}}`. `load_fit(path, board=None)` picks the board from a `5-electronics/<name>/` path or the `board=` argument.
- `tools/fit/fitmd.py`: one Fit subsection per board.
- `tools/fit/fitcheck.py`: `fitcheck.py episodes/<slug>/5-electronics/<board>`, or the episode folder to check every board.
- `tools/kicad/env.py`, `build.sh`, `export.sh`, `new_board.sh`: a board folder is any folder holding `src/`, so `build.sh episodes/<slug>/5-electronics/sensor` works.
- `tools/kicad/models/ESP32-C6-MINI-1.step`: stand-in model (13.2 × 16.6 × 0.8 PCB + 12.2 × 10.2 × 1.6 shield).
- `HOLE_CLEARANCE` layout option (written into the project's DRC rules). The stock GCT USB4105 footprint has its GND pads 0.19 mm from its locating-peg holes, below the kit's 0.25 mm, so both boards use 0.18. Check that against the fab's NPTH-to-copper rule (JLC: 0.2 mm) before ordering, or use the HRO TYPE-C-31-M-12 footprint.

## Open questions

- Receiver battery life on 150 mAh (above). Measure it on a dev board before committing to the case thickness.
- LCSC numbers are left blank where I couldn't confirm them (ESP32-C6-MINI-1-N4, GCT USB4105-GF-A, Panasonic EVQ-PUJ02K, 1TS009 tact, ICS-43434). Check stock before ordering. HRO TYPE-C-31-M-12 (C165948) is the usual JLC USB-C, but KiCad has no 3D model for it, so the CAD uses the GCT part.
- The WS2812B-2020 runs from VBAT (3.0–4.2 V). Below ~3.5 V the blue channel dims. That's acceptable for a glow, but a plain pink LED may be all it needs.
- The ERM runs from VBAT and is 3 V rated: firmware caps its duty at ~70 % on a full cell.
- No ESD diodes on USB (a first-pass shortcut). Add a USBLC6-2SC6 if there's room.
- Is a sensor-side "lost link" alarm wanted, e.g. the sensor LED blinking red? It would need an RGB LED.

## Results

| | Sensor | Receiver |
|---|---|---|
| ERC | 0 violations | 0 violations |
| Netlist check | clean (31 parts) | clean (32 parts) |
| DRC | **0 violations, 0 unconnected**, schematic parity clean | **0 violations, 0 unconnected**, schematic parity clean |
| Fit check | see `sensor/fitcheck.md` | **PASS**: 0 overlaps (`receiver/fitcheck.md`) |

How it got there:
- **Receiver** routed on the first try. The only fixes were the USB-C footprint's hole clearance, a courtyard clash between J3 and the button, and silkscreen.
- **Sensor**: Freerouting kept leaving BTN open. That's the module's IO7 (bottom-left) to the button (middle), the length of the board. BTN is now a hand-laid `PREROUTE` along the bottom just under the module's pin row, and CHG_STAT moved to IO21 on the module side facing the charger. The kept board is the clean one of three routing variants run in parallel (`ROUTE_PASSES` 30). Two reference labels were then moved by hand in KiCad (U1 off the board edge, C9 off the mic's port hole), and DRC and the exports were re-run on that board. So a fresh `build.sh` on the sensor routes differently: re-run `export.sh` after hand edits instead.
- Both boards are far below `SIZE.md`'s ~1410 mm² (900 and 880 mm²) and still routed, with 0603s on the bottom faces. On boards this dense, parts on both faces did help, which is worth remembering against the kit's "both faces don't shrink it" note.
