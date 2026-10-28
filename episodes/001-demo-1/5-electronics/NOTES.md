# Backpack Defender: Stage 5 electronics notes

First-pass electronics for the kawaii motion alarm. It's one 2-layer board, 70 × 45 mm with R9 corners, and it drops onto the four posts in the Stage 4 enclosure (`4-model/`). It runs from 2 × AAA cells underneath the board. All parts are on the top side, because the battery holder sits 0.5 mm below the board.

## Block diagram (in words)

```
2 x AAA (2.0-3.2 V) --J1--> Q1 P-FET (reverse-battery guard) --VBAT--> U1 TPS61023 boost --3V3--+
                                                     |                                           |
                                                     +--> R3/R4 divider --> IO3 (battery level)  |
   +-----------------------------------------------------------------------------------------+
   |
   +--> U2 ESP32-C3-WROOM-02 (Wi-Fi SoftAP settings page, tone player, deep sleep)
   |       IO0 <-- PIR OUT        (deep-sleep wake)
   |       IO1 <-- big button SW1 (deep-sleep wake, 100k pull-up)
   |       IO4/IO5/IO6 --> I2S BCLK / LRCLK / DIN --> U3
   |       IO7 --> AMP_SD (100k pull-down: amp is off unless the MCU turns it on)
   |       IO18/IO19 USB --> J2 programming pads (with 3V3, GND, EN, IO9)
   +--> U3 MAX98357A I2S class-D amp --R12/R13 100R--> BZ1 piezo transducer (TDK PS1240)
   +--> R10 100R + C8 10uF filter --> U4 AM312 mini PIR (dome pokes through the lid)
```

How it behaves (firmware sketch):
- **Armed:** the ESP32-C3 sits in deep sleep (about 5 µA) and wakes on PIR OUT (IO0) or the button (IO1).
- **Alarm:** on a PIR wake it enables the amp (IO7 high), streams the chosen tone over I2S for about 10 s, then goes back to sleep. Wi-Fi stays off.
- **Silence:** pressing the big button stops the tone and skips PIR wakes for a cool-down, e.g. 60 s.
- **Setup:** hold the big button while putting the batteries in. The C3 starts a SoftAP ("BackpackDefender-XXXX") with a captive settings page. The kid picks a tone (goofy / playful / musical / robotic / classic alarm) and hears a preview, and the choice is saved to flash (NVS). Tones are short 8-bit/16 kHz PCM or synthesised in firmware, and the 4 MB flash holds plenty.
- **Low battery:** IO3 reads VBAT/2. Below about 2.1 V, it plays a sad little chirp once a day.

## Part choices and why

| Block | Part | Why |
|---|---|---|
| MCU + Wi-Fi | **ESP32-C3-WROOM-02-N4** (U2), 18 × 20 × 3.2 mm, PCB antenna | Cheap (~$1.9). It hosts a SoftAP page easily, has I2S and native USB (no USB-serial chip), and above all can wake from deep sleep on a GPIO with no extra parts. The Stage 4 stand-in was an ESP-12F (ESP8266). It's slightly cheaper, but it can only wake from deep sleep through RST, so the PIR would need an extra pulse circuit, and its I2S data pin is the UART RX pin. Stock KiCad symbol and footprint. |
| Battery | 2 × AAA in a side-by-side holder with wire leads (BT1, off-board) to **J1** | As in Stage 4: easy to buy, and teachers can disarm it by pulling a cell. |
| Reverse battery | **AO3401A** P-FET (Q1), gate to GND | Kids will put cells in backwards. Costs ~1 cent and only ~40 mV drop. Carried over from the bollard v2 lessons. |
| 3.3 V | **TPS61023** boost (U1) + 1 µH (L1), always on | Two AAA cells give 2.0–3.2 V, below what the C3 needs (3.0 V min). It's synchronous, starts from 0.5 V, and has a 3.7 A switch for Wi-Fi bursts. Same part and footprint as bollard v2, which works. VOUT = 0.595 V × (1 + 1 M/220 k) = 3.30 V. |
| Amp | **MAX98357A** (U3), TQFN-16 | The "I2S amp" from the brief: digital in, no DAC or codec, filterless class-D, 3 mm square. SD_MODE from IO7 (high = left channel), GAIN pin open (9 dB). |
| Sound | **TDK PS1240P02BT** piezo (BZ1), Ø12.2 × 6.5 mm | The "piezo" from the brief: loud for its size near its ~4 kHz resonance, cheap, sits behind the front grille. R12/R13 (100 Ω each) in series stop the class-D edges from slamming a capacitive load and form a ~100 kHz low-pass with it. The pads take an 8 Ω micro-speaker on wires too (swap R12/R13 for 0 Ω). |
| Motion | **AM312** mini PIR (U4), Ø10 lens, 3 pins | Near-field (≤ 3–5 m, so it trips in a locker when the door opens or on a backpack when someone reaches in), digital output, ~15 µA. Fed through R10/C8 because PIRs false-trigger on supply ripple (boost, class-D, Wi-Fi). A microwave radar (RCWL-0516) would be the alternative, but it draws ~3 mA and sees through locker walls, so PIR is the better fit. |
| Button | **12 × 12 × 7.3 mm THT tact switch** (SW1) | Sits under Stage 4's Ø24 "silence" cap at (18, 0). |
| Programming | **J2**: 6 unpopulated pads (GND, 3V3, D−, D+, EN, IO9) | The C3's own USB on pogo pins or a cut cable. No USB-C connector on a toy. |
| Bring-up | TP1 VBAT, TP2 3V3, TP3 GND; 3 fiducials | Bollard v2 lesson: probeable rails, plus fiducials for the 0.5 mm-pitch amp. |

Stock KiCad symbols and footprints are used everywhere except the MAX98357A, TPS61023 and AM312 symbols. Those three are small box symbols in `lib/backpack.kicad_sym` on stock footprints.

## Fit in the Stage 4 enclosure

Board coordinates equal the enclosure's XY (origin at its centre; +y is the back, −y the front grille).

| Item | Where | Height above PCB | Check |
|---|---|---|---|
| Board outline | 70 × 45, R9 | — | Inside the 72 × 47 cavity |
| Mounting holes H1–H4 | (±31, ±17), Ø2.2 for M2 self-tappers | — | Match the bottom plate's four posts |
| SW1 tact switch | centred (18, 0) | 7.3 | Lid inside is 7.9 above the PCB, and the button flange is at z 23.2, so its plunger touches at 23.4: **0.2 mm preload, trim the flange in Stage 4 if it's too stiff** |
| U4 AM312 | centred (−26, 13) | ~12 + standoff | Dome under the Ø10.4 lid hole. Raise it ~2.5 mm on its legs so the lens top reaches the model's ~30 mm, which also clears the M2 screw head at (−31, 17) |
| BZ1 piezo | centred (0, −14.5) | 6.5 | Behind the 3-slot front grille; clears the lid's inner R5 edge round by ~0.7 mm |
| U2 module | antenna on the back edge, x −17.6…0.6 | 3.2 | Antenna area copper-free on both layers, away from the cells (which are under the front half) |
| L1, caps, ICs | front-left and right | ≤ 2.4 | — |

The THT leads (switch, PIR, piezo, J1) must be **clipped flush** underneath, since the AAA holder is only 0.5 mm below the board.

## Power budget (2 × AAA alkaline, ~1000 mAh usable)

| State | Load at 3.3 V | From the cells (boost ~70–85 %) |
|---|---|---|
| Armed (deep sleep): C3 5 µA + AM312 ~15 µA + amp off 1 µA + TPS61023 quiescent ~20 µA + FB divider 3 µA | ~45 µA | **~90 µA → about 12–15 months** of standby |
| Alarm sounding (CPU on, Wi-Fi off, amp + piezo) | ~45 mA | ~75 mA → ~0.2 mAh per 10 s alarm |
| Setup page (SoftAP) | ~100 mA avg, 350 mA peaks | ~170 mA avg, ~650 mA peaks at 2.0 V. Fine for the few minutes setup takes |

Realistic use (say 20 alarms a day plus a setup a week) costs about 4 mAh a day for the alarms, so **a set of AAAs lasts about 6–9 months**. The standby current is what the design really optimises.

## Rough electronics cost (1k units)

ESP32-C3-WROOM-02 $1.90, MAX98357A $1.20, AM312 $0.80, TPS61023 $0.35, PS1240 piezo $0.25, tact switch $0.08, 1 µH $0.10, FET + passives $0.20, PCB $0.40, AAA holder $0.15 → **≈ $5.40** before assembly.
Cost-down options: **NS4168** (SOP-8 I2S class-D, ~$0.15) instead of the MAX98357A saves ~$1. A chip-down ESP32-C3 or an ESP8266 saves more at volume, at the cost of RF work and the wake circuit.

## Build files

- `backpack-defender.kicad_pro / .kicad_sch / .kicad_pcb`: KiCad 10 project. `lib/` holds the three custom symbols.
- `tools/`: the generator scripts (adapted from the bollard v2 board). `tools/build.sh` regenerates everything: schematic → ERC + netlist check → placement → routing (Freerouting) → DRC → BOM, renders and GLB.
- `bom.csv`, `erc.rpt`, `drc.rpt`, `schematic.png`, `board.png`, `board-bottom.png`, `board.glb`

## Check results (2026-10-28, KiCad 10.0.7)

- **ERC:** 0 errors, 0 warnings (`erc.rpt`). The netlist check (`tools/check_netlist.py`) confirms all 111 pins of the 43 components are on their intended nets.
- **DRC:** 0 violations, 0 unconnected pads, schematic parity clean (`drc.rpt`).
- **Routing:** fully routed on 2 layers by Freerouting, with GND pours on both sides and stitching vias. Nothing is unrouted. The boost loop (L1/U1/C2/C3) and the I2S lines were left to the autorouter, so a hand clean-up of the boost loop is worth doing before ordering. Freerouting's results vary from run to run, so re-running `tools/build.sh` gives a slightly different board.
- **Thermal vias:** 4 in the amp's exposed pad and 12 in the module's ground pad. Both come from the stock footprints and use **0.2 mm drills**, so the board rule allows 0.2 mm. Check the JLCPCB 2-layer process minimum before ordering. If it's 0.3 mm, either pay for the finer drill or switch U3 to the non-via TQFN footprint and add 0.3 mm vias.
- **3D models:** the switch uses the Würth 12 mm model (same pad grid) and the amp uses the TQFN EP1.6 model, because KiCad doesn't ship models for the exact footprints. The AM312 shows as a 3-pin header and J1 has no model.

## Shortcuts and open questions (first pass)

- **Piezo vs speaker:** a 12 mm piezo is loud near 4 kHz, but "musical" and "goofy" tones will sound thin and buzzy on it. A 20–28 mm 8 Ω micro-speaker on the lid would sound far better at the same cost. It wires to BZ1's pads, with R12/R13 swapped for 0 Ω. Worth an A/B test with real kids' ears.
- **Verify before ordering:** the AM312 pin order and pitch (the board assumes VCC/OUT/GND at 2.54 mm, which varies between vendors), the MAX98357A TQFN pinout against the datasheet, and every LCSC part number. Only the parts reused from bollard v2 are checked.
- **PIR in a locker:** the dome looks straight up. Test that it trips on a locker door opening (warm hand or arm) and doesn't trip from the metal locker warming up. The firmware can add a sensitivity setting (two triggers within N seconds).
- **No power switch:** pulling a cell disarms it, as the brief wants. A slide switch on the right end would cost ~$0.05 if testing shows teachers want one.
- **J2 programming:** pogo pads only. Production units would be flashed on a jig before the lid goes on.
- **Antenna:** the PCB antenna sits ~5 mm from the plastic wall, with no metal nearby except the cells under the front half. Good enough for a SoftAP at arm's length. Not tuned.
- **Stage 4 follow-ups:** the model's ESP stand-in (24 × 16) should become the WROOM-02 (18 × 20) at x −8.5, y 12.4 (antenna on the back edge). The button flange preload is noted above.
- **Before any order:** run the BoardRepo checks and design review, as was done for the bollard board.
