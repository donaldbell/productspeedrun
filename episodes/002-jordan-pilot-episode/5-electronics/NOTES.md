# Gamer Companion: Stage 5 electronics notes

One 2-layer board stands upright right behind the robot's face. The **front** (KiCad top) faces the smoked visor and carries what has to see out: the PIR and the two eye LEDs. The **back** (KiCad bottom) carries the ESP32-S3 module, power, the audio parts and the connectors. The blower, the speaker and the USB-C socket are off-board on short JST-SH leads. USB is 5 V only, with no battery.

## Block diagram (in words)

```
USB-C breakout (back wall, 5.1k CC pull-downs) --JST-SH 4--> J1: VBUS, D-, D+, GND
VBUS 5 V --+--> U1 AP2112K-3.3 LDO --> 3V3 --> ESP32-S3 module, mic, PIR (RC-filtered)
           +--> U3 MAX98357A I²S amp (runs on 5 V for more headroom) --> J3 --> Ø28 mm 8 Ω speaker
           +--> J2 blower (+) ; blower (−) --> Q1 AO3400A low-side switch, PWM from the MCU, D1 flyback
           +--> D2 1N4148W --> VLED ≈ 4.3 V --> 2 × WS2812B-2020 eye LEDs (data chained)
ESP32-S3 native USB (IO19 / IO20) <-- D− / D+ on J1: flashing, logs, updates
ICS-43434 I²S MEMS mic (bottom port, through a hole in the board) --> ESP32-S3 I²S1
AM312 PIR --> IO15 (wakes the chip from light sleep when someone sits down)
```

## Part choices and why

| Ref | Part | Why |
|---|---|---|
| U2 | **ESP32-S3-WROOM-1-N16R8** (16 MB flash, 8 MB octal PSRAM), on the back | The rolled "ESP32", in the version that does on-device speech. Espressif's **ESP-SR** (WakeNet wake word + MultiNet commands) needs the S3's vector instructions and PSRAM. It also has two I²S ports (mic in, amp out) and native USB, so no USB-UART chip is needed. |
| U1 | **AP2112K-3.3** LDO, 600 mA, SOT-23-5 | 5 V → 3.3 V. It covers the S3's Wi-Fi bursts (~350 mA) with margin, in a tiny package. A buck isn't worth it at these currents. |
| U3 | **MAX98357A** I²S class-D amp | No codec and no output filter. On 5 V it gives ~1 W into 8 Ω, enough for a voice over game audio. The block is reused from episode 001. |
| U4 | **ICS-43434** I²S MEMS mic, bottom port | A digital mic, so no analogue front end is needed. It sits on the back with its port over a Ø1 hole through the board, and a small rubber boot carries sound from the face's mic port (Stage 4: x 0, z −6). |
| U5 | **AM312** mini PIR | 3 V, ~15 µA, digital out. Its dome pokes through the visor (PMMA blocks IR). It gets an RC-filtered supply because PIRs false-trigger on ripple from the amp, the Wi-Fi and the fan. |
| LED1, LED2 | **WS2812B-2020** RGB | The eyes light only when a reminder needs attention, and the colour can say which (blue = water, orange = snack, purple = posture). They're chained on one GPIO. |
| D2 | **1N4148W** in the LED supply | WS2812s want 3.7–5.3 V, and at 5 V their data input needs 3.5 V high, more than the S3's 3.3 V. One diode drop (VLED ≈ 4.3 V) brings the threshold to ~3.0 V, so no level shifter is needed. |
| Q1, D1 | **AO3400A** N-MOSFET + **1N5819WS** Schottky | Low-side PWM switch for the 5 V blower ("gentle breeze" = low duty). D1 catches the motor's flyback. There's a 100 Ω gate resistor and a 100 k pull-down so the fan stays off at boot. |
| J1–J3 | **JST-SH** (1.0 mm) SMD right-angle | Small and cheap. J1 = USB harness to the USB-C breakout on the back wall, J2 = blower, J3 = speaker. |

## GPIO map (ESP32-S3)

| Signal | GPIO | Notes |
|---|---|---|
| PIR_OUT | IO15 | Level with the PIR's OUT leg: a 4 mm straight track. RTC GPIO, so it can wake the chip from sleep |
| LED_DIN | IO16 | 100 Ω series resistor, via to the front |
| FAN_PWM | IO12 | LEDC PWM, ~25 kHz so it's inaudible |
| AMP BCLK / LRCLK / DIN / SD | IO4 / IO5 / IO18 / IO8 | I²S0 out; SD high = on (left channel); 100 k pull-down keeps it off at boot |
| MIC SCK / WS / SD | IO9 / IO10 / IO11 | I²S1 in, on the module's bottom pin row next to the mic; L/R tied low = left slot |
| USB D− / D+ | IO19 / IO20 | Native USB-Serial-JTAG: flashing works with no buttons |
| EN, IO0 | test pads | EN RC reset (10 k / 1 µF). IO0 relies on the S3's internal pull-up (normal boot), with a pad to force download mode if ever needed |

The octal PSRAM uses IO35–IO37, so they stay unconnected. Strap pins IO3, IO45 and IO46 are left at their defaults. IO6, IO7 and IO17 face the PIR's legs on the board, so they're left unused to keep that routing channel free. The pins were chosen for the layout, not by function: the S3's GPIO matrix puts I²S, LEDC and RMT on any pin.

## Power budget (5 V from USB)

| Load | Typical | Peak |
|---|---|---|
| ESP32-S3, listening (ESP-SR running, Wi-Fi off) | ~90 mA | ~350 mA (Wi-Fi TX bursts) |
| MAX98357A + speaker, speaking | ~80 mA | ~300 mA |
| Blower 3010 at a low PWM duty | ~50 mA | ~150 mA |
| 2 × WS2812B-2020, one colour | ~25 mA | ~70 mA (white, full) |
| PIR, mic, LDO quiescent | ~2 mA | |
| **Total** | **~150–250 mA** | **~870 mA** if everything peaks at once |

A laptop or PC USB 2.0 port only promises 500 mA. The firmware should never run Wi-Fi, the voice at full volume and the fan at full speed together (easy, because a reminder plays speech *then* breeze). On a Type-C charger the 5.1 k CC pull-downs give 1.5 A or more anyway. LDO dissipation stays under ~0.3 W typical, (5 − 3.3) V × 150 mA.

## How it fits the enclosure (from 4-model/NOTES.md, with one change)

- **Plane:** the board stands in the enclosure's XZ plane, with its front face at y = −15 (facing the lens). **Board coordinates** in `layout.py`: x = enclosure x, y = enclosure z − 6 (the board centre sits at z = +6).
- **Change from Stage 4:** the board is now **54 × 31, R5**, spanning enclosure x −27 to +27 and z −9.5 to +21.5 (it was 48 × 26, z −8 to +18). The extra height fits the module and its screw heads. The extra width is what let Freerouting finish: at 48 mm wide it left 2–7 nets open on every run. It has **3 M2 screws** at enclosure (x, z) **(−21, −7.25), (21, −7.25), (21, 18.5)**, which are board (x, y) (−21, −13.25), (21, −13.25), (21, 12.5).
  - **Why:** the 18 × 25.5 mm WROOM module has to sit on the back, clear of the PIR's legs at x 0. It's on the **left**, at x −22 to −4 and z −4.9 to 20.7, with its antenna along the top-left edge (away from the speaker magnet on the right wall) and its pin row facing the centre, where the decoupling sits.
  - **Fourth post:** (−21, 18.5) stays as a plain rest under the antenna end, with no screw.
  - The Stage 4 model is updated to match in revision 2 (see `4-model/NOTES.md`).
- **Front side (top):**
  - PIR centred at (0, −2) board.
  - Also on the front: the small parts that would otherwise block the back, namely the LED feed (D2, C10, R5), the PIR supply filter (R3, C8), the EN RC's resistor (R1), and the EN / IO0 test pads. They sit behind the smoked visor, and the front is otherwise nearly empty.
  - Eye LEDs at (±11, 3.2) board (enclosure z 9.2, inside the eye arcs and clear of the module's thermal vias on the other face).
  - Nothing taller than 8 mm except the PIR, since the lens is 10 mm away.
- **Back side (bottom):**
  - Module at the left.
  - LDO, amp, fan driver and connectors at the right (J3 to the speaker on the right edge; J1 and J2 on the bottom edge).
  - Mic at (0, −12) board, over the face's mic port.
  - Max height ~6 mm (the JST-SH plugs). Below the board's bottom edge is the blower duct (z −12).
- **Antenna:** at the top-left edge, under the shell's top, with a copper keep-out on both layers. There's plastic only around it: the speaker magnet is on the far side (x ≥ 25.5) and the blower is below.

## Results

- **ERC:** 0 errors, 0 warnings. **Netlist check:** 41 components and 140 pins, all on their intended nets.
- **DRC: 0 violations, 0 unconnected, 0 schematic-parity issues** (`drc.rpt`). The board is 2-layer, 54 × 31 mm, R5, with a GND pour on both layers.
- **Outputs:** `gamer-companion.kicad_pro/.kicad_sch/.kicad_pcb`, `bom.csv` (22 lines, including 3 off-board items: blower, speaker, USB-C breakout), `erc.rpt`, `drc.rpt`, `schematic.png`, `board.png` (front), `board-bottom.png` (back), `board-iso.png`, `board.glb`.
- **How the clean route was reached** (it took several rounds):
  - First run: 34 violations and 20 unconnected. The stock WROOM-1 footprint carries a 48 mm antenna keep-out zone that blocked the whole board. `TRIM_COURTYARD` now drops it, and our own `NO_COPPER` keeps the antenna area clear.
  - Shorts under the amp: the QFN's and the module's thermal vias put copper on both faces. The placer now keeps the other face clear at plated holes.
  - The rest was congestion around the PIR's legs:
    - GPIOs remapped so no right-going signal leaves the module beside the PIR.
    - Small parts moved to the empty front.
    - Five short `PREROUTE` links (3V3 decoupling, PIR_OUT, the front 3V3 feeds).
    - Board widened from 48 to 54 mm.
  - Freerouting varied between runs. The committed board is a `ROUTE_PASSES=80` run, re-checked with DRC in this folder. A rebuild may land one net short: if so, rerun at 80 passes or try 60–100.
- **Hand edit:** after routing, LED1 and LED2's 3D models were pointed at a same-family stand-in, because KiCad ships no WS2812B-2020 model. That's render-only (`layout.MODEL_SUBST` does the same on a rebuild), and DRC was re-run afterwards (still 0 / 0).

### Changes to tools/kicad made for this board

- `BOTTOM` lists parts that go on the bottom face, and positions and orientations are given as seen from the top. The auto-fitter lets SMD parts on opposite faces share area, and keep-outs, THT parts and plated thermal vias block both faces.
- `NO_PARTS` entries can be limited to one face with `(rect, "F")` or `(rect, "B")`.
- `TRIM_COURTYARD` shrinks a module's courtyard to its body, drops its built-in keep-out zone, and ignores DRC's library-mismatch check for that board.
- `PREROUTE` starts on the first pad's own layer, so a path can start on a bottom pad.

## Open questions

- **Whisper needs a bigger chip than the ESP32-S3.** Whisper-tiny alone needs more RAM than the S3 has. On this board ESP-SR gives a wake word plus ~200 fixed voice commands ("snooze", "done", "I drank water"). **Jordan reports running Whisper on an ESP32-P4 dev board** (not yet reproduced here). That's the upgrade path to free-form speech-to-text. Costs of switching:
  - The P4 has no Wi-Fi or Bluetooth, so it needs an ESP32-C6 alongside, as on Espressif's P4 boards.
  - There's no antenna module for the P4, so it's either the bare QFN with flash, crystal and power parts, or a P4 core board on headers. That means a bigger board and probably a slightly larger head.
  - It draws more power and heat while transcribing.
- **No ESD or fuse on USB** (simplest first pass). The cable is long and a kid's desk is a hostile place, so add a USBLC6-2SC6 and a 1206 PTC before production.
- The ICS-43434's LCSC stock and the AM312's pin order need checking against the supplier's drawing (the same note as episode 001).
- The blower connector: most 3010 blowers ship with a 2-pin PH 1.25 or 2.0 lead, so re-terminate it with an SH plug or swap J2's footprint.
- The rubber boot between the mic port and the face is a guess. A short gasketed channel moulded into the face cap may work better.
