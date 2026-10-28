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
AM312 PIR --> IO4 (wakes the chip from light sleep when someone sits down)
```

## Part choices and why

| Ref | Part | Why |
|---|---|---|
| U2 | **ESP32-S3-WROOM-1-N16R8** (16 MB flash, 8 MB octal PSRAM) | The rolled "ESP32", in the version that does on-device speech. Espressif's **ESP-SR** (WakeNet wake word + MultiNet commands) needs the S3's vector instructions and PSRAM. It also has two I²S ports (mic in, amp out) and native USB, so no USB-UART chip is needed. |
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
| PIR_OUT | IO4 | RTC GPIO: can wake from sleep |
| LED_DIN | IO5 | 100 Ω series resistor |
| FAN_PWM | IO6 | LEDC PWM, ~25 kHz so it's inaudible |
| AMP BCLK / LRCLK / DIN / SD | IO7 / IO15 / IO16 / IO17 | I²S0 out; SD high = on (left channel); 100 k pull-down keeps it off at boot |
| MIC SCK / WS / SD | IO18 / IO8 / IO9 | I²S1 in; L/R tied low = left slot |
| USB D− / D+ | IO19 / IO20 | Native USB-Serial-JTAG: flashing works with no buttons |
| EN, IO0 | test pads | EN RC reset (10 k / 1 µF); IO0 pulled up, with a pad to force download mode if ever needed |

The octal PSRAM uses IO35–IO37, so they stay unconnected. Strap pins IO3, IO45 and IO46 are left at their defaults.

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
- **Change from Stage 4:** the board is now **48 × 30, R3** (enclosure z −9 to +21, was −8 to +18). With **3 M2 screws** at enclosure (x, z) **(−21, −6.75), (21, −6.75), (−21, 18)**. That's because the 18 × 25.5 mm WROOM module must sit on the back at x 4 to 22 (clear of the PIR's legs at x 0), and that covers the old right-hand posts at x 21. The module now spans z −4.5 to 21, with its antenna on the board's top edge. The fourth post (21, 18) stays as a plain rest under the module's antenna end, so no screw goes there. The Stage 4 model gets these posts, board and module positions in a revision 2 (see that NOTES file).
- **Front side (top):**
  - PIR centred at (0, −2) board.
  - Eye LEDs at (±11, 2) board.
  - Nothing taller than 8 mm except the PIR, since the lens is 10 mm away.
- **Back side (bottom):**
  - Module at the right.
  - LDO, amp, fan driver and connectors at the left.
  - Mic at (0, −12) board, over the face's mic port.
  - Max height ~6 mm (the JST-SH plugs). Below the board's bottom edge is the blower duct (z −12).
- **Antenna:** at the top edge, under the shell's top. Plastic only: the speaker magnet is at x ≥ 25.5 and the blower is below.

## Results

(filled in after the build)

## Open questions

- **"Whisper" isn't realistic on an ESP32-S3**, because Whisper-tiny alone needs far more RAM. ESP-SR gives a wake word plus ~200 fixed voice commands, which covers "snooze", "done" and "I drank water". Free-form speech-to-text would need an ESP32-P4 or a small Linux SoC.
- **No ESD or fuse on USB** (simplest first pass). The cable is long and a kid's desk is a hostile place, so add a USBLC6-2SC6 and a 1206 PTC before production.
- The ICS-43434's LCSC stock and the AM312's pin order need checking against the supplier's drawing (the same note as episode 001).
- The blower connector: most 3010 blowers ship with a 2-pin PH 1.25 or 2.0 lead, so re-terminate it with an SH plug or swap J2's footprint.
- The rubber boot between the mic port and the face is a guess. A short gasketed channel moulded into the face cap may work better.
