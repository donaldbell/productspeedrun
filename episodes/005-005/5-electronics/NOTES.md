# Stage 5 notes: Smart Bucket Hat (episode 005)

## Summary

**Done.** A routed 2-layer XIAO nRF52840 Sense carrier, 50 × 34 × 1.0 mm, standing in the pod at the back of the crown: **ERC 0, DRC 0 violations / 0 unconnected, fit check PASS (0 overlaps).** No open requests in `FIT.md` either way.

- **Left for the hosts:** the runtime question below (2,496 LEDs idle at ~1 A). Before ordering, confirm the XIAO's battery pads and antenna end on a real board.

- **Board:** a XIAO carrier (the brief's `boardStyle: "carrier"`), the XIAO **nRF52840 Sense**. It fits: the hat needs 4 of the XIAO's 11 I/O and no part a XIAO lacks, so no full custom board.
- **Matrix:** HUB75 is out (see "Why not HUB75"). The band is Stage 4's **12 × 208 px at 2.8 mm** (2,496 addressable RGB LEDs, the concept's density), on flex in two halves of 12 × 104, each on its own plug, switch and data line.
- **The cost of 2,496 LEDs is runtime:** addressable LEDs idle at 0.3–0.7 mA each, so the dark band alone draws 0.75–1.75 A. Expect **~1–1.5 h of light show** from 2 × 1200 mAh (beacon-only mode: weeks). See "Questions for the hosts".

## Block diagram

```
 2 x LiPo pouch (parallel) ──J1/J2──► VBAT ─┬─► XIAO BAT+ pad (XIAO: 3V3 LDO, VBAT ADC, 50 mA charger)
                                           ├─► Q1 AO3401A ─► VLED_A ─► U3 buffer ─► J3 ─► band half A (left side, 12 x 104)
                                           └─► Q2 AO3401A ─► VLED_B ─► U4 buffer ─► J4 ─► band half B (right side, 12 x 104)
                                                 ▲ gates together: Q3 AO3400A ◄── LED_EN (D2)
 XIAO 5V pin (USB VBUS) ─► U2 MCP73831, 500 mA ─► VBAT          CHG_STAT ─► D9
 XIAO D8 / D3 ─► LED data A / B (through U3 / U4, 3.3 V → VLED swing)
 MODE button ─► D1 (wake from System OFF, next show, hold = beacon only / off)
 On the XIAO Sense: PDM mic (reacts to music), 6-axis IMU (tap, nod), BLE 5 radio + antenna
```

## Why a XIAO carrier works here

| Check | Result |
|---|---|
| Room | The board needs ~1670 mm²: a 52 × 32 mm pod board, small next to a hat's crown. |
| Pins | 4 of 11 used: 2 × LED data, LED_EN, button, plus CHG_STAT (5). Battery voltage and USB-present come from the XIAO itself (P0.31 divider, nRF52840 VBUS detect). |
| Parts | Mic and IMU are on the Sense; BLE and its antenna are on the XIAO. Nothing here needs a part the XIAO family lacks. |

**XIAO model:** the roll is nRF52840, so it's the **XIAO nRF52840 Sense** rather than the plain one. The Sense's PDM microphone covers the roll's "reacts to music" twist with no extra part, and its IMU gives tap-to-change and a "nod to wave at a friend" gesture for free. The pin rows and outline are the same as the plain XIAO nRF52840.

## Why not HUB75

The brief allowed "hub 75 or neopixel matrix". A HUB75 panel needs ~14 fast GPIOs (6 colour lines, 5 address lines, clock, latch, OE), more than the XIAO's 11. It also needs a 5 V supply at several amps and constant CPU refresh. Flexible HUB75 panels are also stiff, wide modules. Addressable WS2812-type LEDs need **one data pin per chain**, hold their own colour, and come on thin flex. That's the right match for a fabric band. The trade-off: a scanned panel draws almost nothing when dark, while 2,496 addressable LEDs idle at ~1 A (see the power budget). Getting both, a scanned matrix with drivers on the flex, is a full custom board and a Rev B question.

## Part choices

| Block | Part | Why |
|---|---|---|
| MCU, BLE, USB-C, 3.3 V, mic, IMU | **Seeed XIAO nRF52840 Sense**, soldered flat by its castellations | The roll's nRF52840. BLE for the phone app and the friend-finder beacon. Soldered flat (no sockets) to keep the pod thin. |
| Fast charging | **MCP73831** at 500 mA (R1 = 2k), from the XIAO's 5V pin | The XIAO's own BQ25101 charges at only 50 or 100 mA: ~24 h for this pack. With the MCP73831 the pack fills in ~5 h. A proven part (episode 003). |
| Band power | **2 × AO3401A** high-side P-FETs (one per half) + **AO3400A** gate driver | 2,496 addressable LEDs idle at ~1 A even when dark, so the band is switched off whenever it isn't showing anything (beacon-only mode, System OFF). One FET per half: ≤ 1.2 A each, ~0.1 W. |
| Band data | **2 × SN74LV1T34** single buffers on VLED, 100 Ω series | Running the LEDs straight off the cell (3.0–4.2 V), 3.3 V data is marginal at a full cell (VIH = 0.7 × 4.2 = 2.94 V), and the data runs ~30 cm along the band next to amps of LED current. The LV1T34 accepts 3.3 V in at any VCC and drives a full VLED swing. |
| Band connectors | **2 × JST PH 3-pin SMD side entry** (S3B-PH-SM4-TB: VLED, DIN, GND, tabs to GND) | The pod unplugs from the band so the hat can be washed. SMD, not through-hole: the board's ends sit ~1 mm from the band's back, and through-hole leads would poke 2.4 mm out. Mounting tabs take the cable's pull. PH is rated 2 A a pin; firmware caps each half at 1.2 A. KiCad ships no 3D model for it, so the kit has a stand-in. |
| Button | **C&K PTS810** SMD tact, 2.5 mm tall | Pressed through the pod's fabric cover. Wake, next show; hold 2 s = beacon only; hold 5 s = off. |
| Battery | 2 × LiPo pouch ~1200 mAh (603450, 6 × 34 × 50 mm), parallel, on solder pads J1 / J2 | One each side of the pod along the inside of the crown, to spread the weight. Cells with their own protection PCBs. |
| LED band (off-board) | 2 × flex matrix, 12 × 104 addressable RGB LEDs at 2.8 mm pitch (~34 × 292 mm each) | Stage 4's band, from the art: 12 rows × 208 columns, square cells, 585 mm round. At 2.8 mm pitch the LED is a 1515 or 1010 addressable part; pick the **lowest idle current** one. Two halves, both starting at the back seam where the pod is: each gets its own power and data line, which also doubles the frame rate (1,248 LEDs a chain ≈ 37 ms a frame, ~25 fps). |

## Pin budget (XIAO nRF52840 Sense, 11 I/O)

Picked from the placement: the XIAO lies USB-C down, so its D7–D10 / power row faces band half A's side (left) and its D0–D6 row faces half B's side (right).

| XIAO pin | nRF pin | Net | Note |
|---|---|---|---|
| D8 | P1.13 | LED_IO_A | Band half A data (left row, toward U3) |
| D9 | P1.14 | CHG_STAT | MCP73831 STAT, 10k pull-up: low while charging (left row, by the charger) |
| D3 | P0.29 | LED_IO_B | Band half B data (right row, toward U4); each chain gets its own PWM/DMA instance |
| D2 | P0.28 | LED_EN | Band power, 100k pull-down (band off at boot and in System OFF) |
| D1 | P0.03 | BTN | Mode button to GND, internal pull-up, System OFF wake |
| D0, D4–D7, D10 | | spare | I2C (D4/D5) free for a Rev B sensor |
| BAT+ / BAT− | (underside pads) | VBAT / GND | Carrier pads under the XIAO's battery pads, reflowed together |
| (internal) | P0.31 / P0.14 | VBAT ADC | Keep P0.14 low while reading (Seeed's warning) |
| (internal) | P0.13 | charge rate | Leave Hi-Z: 50 mA (the MCP73831 does the real charging) |

## Power budget

The band: 2 × 12 × 104 = **2,496 LEDs**. Addressable LEDs draw a quiescent current even when dark: 0.3–0.7 mA each depending on the part, so **0.75–1.75 A** for the band before anything lights.

| State | Draw | Notes |
|---|---|---|
| Off (System OFF) | ~10 µA | nRF52840 System OFF + XIAO LDO/charger leakage; band switched off. Months on a shelf. |
| Beacon only | ~0.1 mA | Band off, BLE advertising every 300 ms for friends' phones. About 2 weeks. |
| Show, typical | ~1.5–2 A | Band idle ~1 A (at ~0.4 mA a LED), plus pixel art ~30 % lit at ~5 % brightness ≈ 0.5–0.8 A; nRF52840 with BLE + PDM mic ~5 mA |
| Show, capped peak | 2.4 A | Firmware power limit, 1.2 A per half: 1C of the pack, within the PH contacts (2 A) and the FETs (~0.1 W each). Leaves ~1 A for light after the idle draw: bright at night, dim-ish in full sun. |

With 2 × 1200 mAh ≈ 2400 mAh: **~1–1.5 h of light show**, longer for dim scrolling text, and weeks in beacon-only mode. Charging at ~550 mA (MCP73831 + XIAO): **~5 h**. Ways to stretch it are in "Questions for the hosts".

**LEDs on the cell, no 5 V boost:** VLED is VBAT through Q1/Q2, 3.0–4.2 V. WS2812B-2020s run there, but blue fades below ~3.6 V, so firmware dims and then stops the band at VBAT 3.5 V and keeps the beacon going. A 2 A, 5 V boost would cost a large inductor, ~10 % efficiency and heat on the back of the head.

## How it fits the enclosure

From `fit.json` (Stage 4 wrote it with Stage 5's numbers; no open requests in `FIT.md`):

- **Pod at the back of the crown**, inside the hat, behind the band's back seam where both band halves start. ~162 mm of arc, ~13 mm deep.
- **Board 50 × 34 × 1.0 mm** (1,700 mm²). SIZE.md said 1,670 and now says 1,859 since the SMD plugs, whose courtyards include their mounting tabs; the trial placement routes clean on 50 × 34, so the board stays that size, standing up, tilted 7° with the band. Its **top face looks inward at the head**; +y runs up the slant. Parts on the **top face only**: the board is a flat chord of a ~75 mm curve, so its ends sit ~1 mm from the band behind.
- **XIAO in the middle of the top face, USB-C down** through the pod's bottom face (reach under the sweatband). The mic opening (felt or mesh) is in the pod's inner face over the XIAO.
- **Plugs at the top corners**, mouths on the side edges at y 9.5, leads running left and right into the band.
- **Button** on the top face, lower right, pressed through the pod's inner face from inside the hat.
- **Holes** M2 at the bottom corners (±21, −13). Stage 4 first proposed (±21, +13), which lands on the plugs. **Rests** (pod posts, no hole) at (±21, +13) press the bare bottom face behind the plugs.
- **Placement:** board centre at enclosure (0, 88.3, 20.4), top face toward the head (−Y), +y tilted 7° with the band; the USB-C mouth comes out through the pod's bottom wall (z 1.6–2.8).
- **Cells** 2 × 6 × 34 × 50 mm pouches in the pod's wings, centred 58 mm of arc either side of the back centre, leads to pads J1 / J2 at each side edge. Band half A (plug J3, −x) runs round the wearer's right, half B (J4) the left; their mating plugs and leads have ~8 mm beside each board edge and exit through the pod's outer wall into the band's back seam.
- **Antenna:** no copper above the XIAO's top (antenna) end, between its pad rows up to the board edge. No metal or ribs over it either.

## Open questions

- **XIAO battery pads.** Named from Seeed's v1.0 bottom-silkscreen drawing: BAT− beside D2, BAT+ beside D3. Check on a real board before ordering.
- **XIAO nRF52840 antenna end.** Taken as the end opposite the USB-C, as on the C6. Check it.
- **XIAO 5V pin current.** The MCP73831 draws up to 500 mA through the XIAO's USB-C and VBUS trace. That's within USB default power, but confirm the XIAO's VBUS path (Seeed don't publish a limit).
- **Two chargers on one pack.** The XIAO's BQ25101 (50 mA) and the MCP73831 both charge the cells. Both stop at 4.2 V, so it's safe, but each sees the other's current near termination. Rev B could use one charger (e.g. a 1.5 A switching charger feeding the XIAO's BAT pads).
- **LED band.** A 12 × 104 flex at 2.8 mm pitch isn't a stock part (stock flexible 8 × 32 panels are 10 mm pitch). Rev A assumes a custom 2-layer flex with 1515 or 1010 addressable LEDs, made the way LED strips are. Pick the LED with the lowest quiescent current and measure it: it sets the runtime.
- **Frame rate.** One chain per half of 1,248 LEDs refreshes at ~25 fps. Enough for text and pixel art; a Rev B can split each half into two chains (a 4-pin plug) for ~50 fps.
- **Heat.** The MCP73831 dissipates ~0.6 W while charging. It has thermal regulation, but charging happens off the head anyway.
- **"Location-aware" beacon.** Rev A advertises BLE (an iBeacon-style frame plus the app's service). Friends' phones show distance and direction from signal strength ("warmer / colder"). Real map positions would need the wearer's phone to relay its GPS, an app feature, not hardware.

## Questions for the hosts

- **Runtime vs. the band's density.** 12 × 208 px (the concept's look) idles at ~1 A, so a show lasts ~1–1.5 h on 2 × 1200 mAh. Options, none taken yet: (a) keep it and call it a "night out" hat, with beacon-only mode lasting weeks; (b) bigger cells in the pod's wings (Stage 4 is checking 8 mm thick 1500 mAh cells: ~1.5–2 h); (c) fewer rows, e.g. 8 × 208 (−33 % idle); (d) a Rev B band of plain RGB LEDs on scanned matrix drivers, which idle at milliamps but need a driver chip per ~100 pixels on the flex. Stage 5 kept (a), the conservative choice: nothing visible changes.

## Kit changes (tools/kicad)

- `parts.xiao_nrf52840(sense=True)` symbol, the footprint `ProductSpeedrun:Seeed_XIAO_nRF52840_SMD` (Seeed's OPL pads, re-centred, battery pads beside D2/D3) and the stand-in `models/Seeed_XIAO_nRF52840.step` (the C6 stand-in: same outline, shield and USB-C).
- `2k` in `schkit.RES`.
- **Fit check on tilted boards:** `tools/fit/fitcheck.py` no longer rounds the placement matrix, and `fitlib` re-normalises `x_axis` / `y_axis` exactly when it loads `fit.json`. Earlier boards were flat or upright, so their axes were exact.
- Stand-in `models/JST_PH_S3B-PH-SM4-TB.step` (9.9 × 7.6 × 4.8 mm block over the SMD PH 3-pin side-entry footprint; KiCad's footprint names a model it doesn't ship). Made with `solidcraft-cli run` from two `solid.box`es.

## Results

- **ERC:** 0 violations (`erc.rpt`). Netlist check clean.
- **DRC:** 0 violations, 0 unconnected (`drc.rpt`), routed on the first Freerouting try. A trial on the same outline in a scratch copy found the two placement clashes first: the button at x 12 touched the XIAO's castellations, and the plugs' mounting tabs at y 11 reached the R3 corner.
- **Fit check:** **PASS**, 0 overlaps (`fitcheck.md`, `fitcheck.png`), against Stage 4's `4-model/fit_model.solidcraft` (the model without the ~550 louvre and pixel-tile bodies outside the screen). Near misses: Mode Key–PTS810 0.09 (really ~0.18: the check reads top-face parts ~0.085 high), Pod–PCB 0.11, Pod–XIAO 0.26, Pod Lid–PCB 0.27 mm.
- **How it got there:** the first two fit-check runs stopped in SolidCraft with "matrix is not rigid" (3.8e-7). The board is tilted 7°, and fitcheck.py rounded the placement matrix to 6 decimals, while SolidCraft wants it rigid to 1e-9. Fixed in the kit (below); the check then passed first time.
