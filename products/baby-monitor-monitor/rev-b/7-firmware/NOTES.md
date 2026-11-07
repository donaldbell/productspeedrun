# Baby Monitor Monitor Rev B: firmware notes

## Summary (start here)

**Done:** first-pass firmware for both devices, as two PlatformIO projects (ESP-IDF 5.5 on the ESP32-C6-MINI-1) with a shared radio protocol.
- The **sensor** turns what it hears into a level from 0 to 3.
- The **watch** buzzes at that level, harder for louder sound, and steps up while nobody acknowledges it. The sensor's snooze bar stops it.

**Status:**
- All four envs build with **0 warnings**.
- The host test of the level detector and the haptic patterns passes.
- `pins.h` is generated from each board's `design.py`.
- **Nothing has run on hardware yet:** there is no Rev B board, and no dev board has been flashed.

**Still to do:**
- Bench-tune the thresholds, the buzz strengths and the radio duty cycle (see "Stubbed or untested").
- Three optional board changes are posted in `../FIT.md` as `[open] 7→5`.

**Questions for the hosts** are at the end.

## Build and try it

```sh
cd products/baby-monitor-monitor/rev-b/7-firmware
(cd sensor   && pio run)            # real sensor board (env sensor), 0 warnings
(cd sensor   && pio run -e devkit)  # ESP32-C6-DevKitC-1 stand-in, scripted sounds, 0 warnings
(cd receiver && pio run)            # real watch board (env receiver), 0 warnings
(cd receiver && pio run -e devkit)  # ESP32-C6-DevKitC-1 stand-in, 0 warnings
test/run_tests.sh                   # host test of the detector + haptic patterns (the Mac's cc)
(cd sensor && pio run -t upload)    # flash the sensor over its USB-C (native USB)
pio device monitor                  # logs (sensor: every 5 s; watch: every 10 s, plus every change)
```

PlatformIO is at `~/.platformio/penv/bin/pio`; it isn't on `PATH` on this Mac. The platform is `espressif32@6.12.0` with **framework `espidf`** (ESP-IDF 5.5.0, toolchain riscv32-esp 14.2.0). It isn't Arduino: this platform's Arduino core (2.0.17) has no ESP32-C6 support, and the backpack-defender project uses that core on a C3. The first build downloads ESP-IDF (~3 min).

**Trying it on two dev boards** (`-e devkit` on both):
1. Flash both boards.
2. Reset the watch board. It accepts pairing for 2 min after a reset.
3. Hold the sensor board's BOOT button 3 s.
4. The sensor then plays a scripted night (quiet → fussing → quiet → crying → screaming → quiet …). The watch board's RGB LED glows with each alert, and the motor PWM is on IO2 (put an LED + 1 kΩ there to see the patterns).
5. Tap BOOT on the sensor to stop an alert.

To use a real mic instead of the script, wire an ICS-43434 or INMP441 breakout (SCK IO4, WS IO5, SD IO2, L/R to GND) and remove `-DBMM_FAKE_AUDIO` from the devkit env.

## Layout

```
7-firmware/
  common/bmm_protocol.h     the radio protocol: message structs, timing, checks that the sensor's bursts hit the watch's wake windows
  common/bmm_common.[ch]    ESP-NOW link + pairing in NVS, battery ADC, WS2812B (RMT), LEDC PWM
  common/scripts/gen_pins.py, pio_pre.py   pins.h from 5-electronics/<board>/src/design.py, before every build
  sensor/    PlatformIO project: src/audio.c (I2S mic), detector.c (levels), main.c (button, ack, lights, radio)
  receiver/  PlatformIO project: src/haptic.c (patterns), main.c (follow the sensor, link-lost, glow, power)
  test/      test_logic.c + run_tests.sh: detector.c and haptic.c on the computer
```

Each project's `src/CMakeLists.txt` also compiles `../common/*.c`. Its `partitions.csv` has two 1.875 MB OTA slots (4 MB flash), so a sealed watch can take updates over the air later without reflashing the partition table.

## pins.h comes from the board

`common/scripts/gen_pins.py <board>` runs `5-electronics/<board>/src/design.py` against a stub of the kit's `schkit`, so it needs no KiCad. It then writes `<board>/include/pins.h`:

- It finds the ESP32-C6-MINI-1 and maps its pads to GPIOs with the datasheet table.
- When KiCad is installed, it checks that table against KiCad's own `ESP32-C6-MINI-1` symbol and stops on any mismatch. It passed on this Mac.
- It writes one `PIN_<NET>` per signal net, each `#ifndef`-wrapped so the devkit envs can move it.
- It writes `PIN_<NET>_PULLUP` / `_PULLDOWN`, read from the resistors on that net, and `VBAT_SENSE_RATIO` (2.0, from the 1M / 1M divider).
- Each pin gets a comment naming what it connects to, plus whether it's a strapping pin, an LP GPIO or an ADC channel.

`pio_pre.py` runs it before every build, using the project folder's name as the board name. `python3 common/scripts/gen_pins.py sensor --check` fails if the checked-in file is stale. Each `src/config.h` `#error`s if:

- a net the firmware uses disappears;
- the watch loses MOT_PWM's pull-down (R6, which keeps the motor off while the C6 boots);
- BTN or CHG_STAT gains a pull-down;
- the battery divider is gone.

| Sensor net | GPIO | | Watch net | GPIO |
|---|---|---|---|---|
| VBAT_SENSE | 0 (ADC1) | | VBAT_SENSE | 0 (ADC1) |
| MIC_SD | 2 (internal pull-down) | | CHG_STAT | 1 (internal pull-up) |
| LED_IO (status) | 3 | | MOT_PWM | 2 (R6 pull-down) |
| MIC_SCK / MIC_WS | 4 / 5 (strapping pins; the mic only listens) | | LED_IO (glow) | 6 |
| BAR_IO (WS2812B) | 6 | | LINK_IO | 7 |
| BTN (SW1 + SW3) | 7 (internal pull-up) | | | |
| CHG_STAT | 21 (internal pull-up) | | | |

## How it behaves

### Sensor: sound → level

1. **I2S:** 32 kHz, 32-bit slots, left slot (the board ties L/R low). That's 32 kHz rather than the 16 kHz in the electronics notes, so the 2.048 MHz bit clock sits well inside the ICS-43434's clock range. Check that against the datasheet on the bench.
2. **Filter:** integer only, because the C6 has no FPU. A one-pole high-pass at ~330 Hz removes rumble and hum, and a one-pole low-pass at ~3.7 kHz removes the baby monitor's hiss. That keeps the band a cry occupies through a small speaker.
3. **Loudness:** RMS over 250 ms → dB SPL (sensitivity −26 dBFS at 94 dB SPL, plus `MIC_CAL_DB`).
4. **Detector** (`detector.c`, numbers in `levels.h`):
   - The **noise floor** follows the room while it's quiet: it falls fast and rises 12 dB a minute at most. During an episode it can only fall, so the breaths in a long cry can't raise it.
   - **Level k** needs `max(floor + 10 / 18 / 26 dB, 50 / 58 / 66 dB SPL)`. The relative part makes it mostly independent of how loud the parent sets the monitor.
   - **Attack:** 1 s of sound within 2 s, so a door slam or a cough doesn't count.
   - **Release:** one level down per 6 s, so breaths between cries don't end it.
5. **Alert and ack** (`main.c`):
   - The alert is the level unless a parent has pressed "I'm awake".
   - An ack stops the watch at once and holds for 3 min, unless the sound gets **louder** than when they pressed.
   - 30 s of quiet ends the episode, so the next sound alerts again.
   - The STATUS packet carries `alert_ms`, so the watch's escalation survives a watch reboot.

**Snooze bar** (BTN, both tacts in parallel, 30 ms debounce):

| Press | Does |
|---|---|
| Tap (anything shorter than 3 s) | "I'm awake": the watch stops, and the bar blinks green. With nothing to stop, it gives a short white blink |
| Hold 3 s | **Test + pair:** the watch plays every level once, and the sensor offers pairing for 30 s (the bar breathes blue). While held, the bar lights white and turns blue at 2 s, so a parent knows when to let go |

**Bar light** (WS2812B-2020 under the acrylic), from top priority down:
1. held
2. pairing (blue breathing)
3. a green / white feedback blink
4. alert (amber, pulsing faster with the level)
5. unpaired (slow dim blue blink)
6. watch not answering (red pulse)
7. acknowledged but still hearing sound (soft green)
8. armed (dim warm white, or dim orange on a low cell)

This is the scheme proposed in `5-electronics/NOTES.md`, except "off at night", which needs a setting (see the questions). One knob, `BAR_SCALE`, scales it all.

**Status LED (green, under the kidney bean):** a VU meter of the instant level, so a parent can see it hears the monitor while they place it. Otherwise it gives a 60 ms "alive" blip every 4 s.

### Watch: level → haptics

| Alert | Pattern (`haptic.c`) | Mean drive | Glow |
|---|---|---|---|
| 1 fussing | two soft taps (45 %) every 4 s | 4 % | soft pink |
| 2 crying | three firm pulses (70 %) every 2.5 s | 22 % | magenta |
| 3 screaming | 0.8 s full buzz, 0.2 s gap, repeating | 80 % | red-magenta |
| escalation | an un-acked alert steps up one level every 45 s (`BMM_ESCALATE_MS`), to 3 | | |
| test | each level once | | |
| link lost | long-short-long, 20 s after 10 s of silence, then every 5 min, 3 times at most (not while charging), then glow-only red blips | | red |
| low battery (< 3.55 V) | two faint taps, every 30 min | | |
| paired | three quick ticks | | blue |

- **Intensity:** % of the ERM's rated 3.0 V. `haptic_duty()` divides by the measured VBAT, so a level feels the same at 4.2 V and at 3.5 V, and the motor never averages more than 3 V. That gives 71 % duty at most on a full cell, the cap in the electronics notes. Soft pulses start with a 40 ms full-strength kick so the ERM spins up. PWM is 20 kHz (inaudible), 10-bit.
- **Following the sensor:** the watch follows STATUS from its paired sensor only, and drops repeats by `seq`. It answers each new STATUS once with its battery, flags and the RSSI it saw. The sensor uses that answer to show "watch not answering".
- **Pairing (the watch has no button):** it accepts a PAIR_OFFER when it has no sensor yet, while it's charging, or in the first 2 min after it starts. The steps are: put the watch on its clip, then hold the sensor's bar 3 s.
- **Power:**
  - **Radio:** ESP-NOW connectionless power save. The radio listens 50 ms in every 200 ms (25 %). The sensor sends every packet 5 times, 40 ms apart, and `bmm_protocol.h` `_Static_assert`s that a burst always lands in a window.
  - **CPU:** `esp_pm` light sleep at 40–80 MHz with tickless idle. A no-light-sleep lock is held only while the motor, the glow or the link blip runs.

## Flash and RAM

From `pio run` (static RAM only; Wi-Fi and FreeRTOS allocate about 60–80 KB more from the heap at runtime, still well inside the C6's 512 KB):

| env | Flash (of the 1.875 MB OTA slot) | Static RAM (of 320 KB) |
|---|---|---|
| `sensor` | 815,487 B (41.5 %) | 37,904 B (11.6 %) |
| `sensor` `devkit` | 785,375 B (39.9 %) | 36,568 B (11.2 %) |
| `receiver` | 811,809 B (41.3 %) | 37,052 B (11.3 %) |
| `receiver` `devkit` | 801,039 B (40.7 %) | 36,764 B (11.2 %) |

Most of that is the Wi-Fi stack ESP-NOW needs. The app itself is a few KB. There's room for OTA and for both slots.

## Libraries

**ESP-IDF 5.5.0 components only, no third-party code:**

| Component | Used for |
|---|---|
| `esp_wifi` / `esp_now` | the radio link |
| `esp_driver_i2s` (std mode) | the mic |
| `esp_driver_rmt` (bytes encoder) | the WS2812B, a single pixel, so no `led_strip` component |
| `esp_driver_ledc` | the motor and LED PWM |
| `esp_adc` (oneshot + curve-fitting calibration) | the battery |
| `nvs_flash` | the pairing |
| `esp_pm` | light sleep on the watch |

## Stubbed or untested (needs hardware)

- **All the sound numbers** (`sensor/src/levels.h`): thresholds, floor rates, attack and release, and `MIC_CAL_DB`. They're a first guess for a sensor next to a monitor's speaker. Tune them with the real board, a real monitor and recorded crying, and check against an SPL meter. Logs print dB, floor, instant and smoothed level every 5 s for this.
- **The buzz patterns and strengths** (`receiver/src/haptic.c`): a guess. Try them on a wrist, half asleep. Level 1 at 4 % mean drive may be too gentle to wake anyone; the 45 s escalation is the backstop.
- **The watch's radio duty cycle and battery life.** Untested:
  - Whether the C6's connectionless power save, with light sleep, really hits 50 ms / 200 ms while staying reliable.
  - The estimate: ~38 mA RX × 25 % + ~1–2 mA base gives **~11 mA, so ~13 h on 150 mAh**. The electronics notes call this the tightest number in the project.
  - If it falls short, there's a knob in `bmm_protocol.h`: interval 400 ms, 8 repeats 50 ms apart. That's ~6 mA (~24 h) for 400 ms latency. Measure it on the jig with a power analyser.
- **Mic start-up:** the first 0.5 s is skipped. The "no audio for 2 s" fault only logs; it has no light colour yet.
- **Battery ADC:** calibration uses the chip's eFuse curve. The divider's 1 MΩ source and its 100 nF cap are assumed to hold up a burst of 16 samples. Check the readings against a meter.
- **WS2812B timing** comes from the datasheet (RMT, 10 MHz ticks). It was not checked on a scope.
- **No encryption on ESP-NOW yet** (first pass). A nearby device could spoof STATUS with `alert = 0`. Next step: a per-pair LMK set at pairing.
- **No OTA code yet.** Only the partition table is ready for it.

## What the hardware should change

Posted in `../FIT.md` as `[open] 7→5` requests. They're all inside the boards, nothing visible changes, and the firmware works without them through the workarounds noted:

1. **Sensor: sense VBUS.** Nothing tells the firmware whether USB is plugged in. CHG_STAT goes high-impedance once the cell is full, which is the same as unplugged. A 100k / 100k divider from VBUS to **IO1** (pad 13, free, ADC1 / LP GPIO) would let it warn about the battery only when it's unplugged, and say "on battery" on the bar. *Now:* low battery is judged from VBAT alone.
2. **Watch: switch the glow LED's supply.** The WS2812B-2020 sits on VBAT and draws roughly 0.5–1 mA even when dark: ~5–10 mAh a night, out of 150 mAh. A P-FET (AO3401A, already on the sensor's BOM) with a gate pull-up, driven from a free pin (e.g. **IO18**, pad 24), would turn it off between alerts. The firmware would also drive its data pin low first. *Now:* the LED is set to black.
3. **Watch: sense the charger.** For the same reason as (1), the watch can't tell "full, on its clip" from "on a wrist". That decides whether it may buzz "link lost" and whether it accepts pairing. A 100k / 100k divider from VBUS (after D2) to **IO3** (pad 6, free LP GPIO) fixes it. *Now:* it only knows "charging", so a full watch left on its clip may buzz "link lost" up to 3 times if the sensor is off.

## Questions for the hosts

- **Level 1 (fussing):** should it buzz at all, or only glow and log? Many parents don't want to be woken for fussing. As written, it buzzes gently and escalates to crying-strength after 45 s.
- **Snooze length:** an ack holds 3 min unless the baby gets louder. Is that right, or should a tap mean "I'm up, stop until it's quiet"?
- **Bar light at night:** the armed state is a dim warm white. Should there be an "off at night" option (for example a double-tap), as the electronics notes suggest?
- **Link lost:** the watch buzzes 3 times over ~10 min, then only glows. Is that enough for the "monitor silently stopped" case, or too much for a parent who walked out of range?
