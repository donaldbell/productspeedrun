# Backpack Defender Rev B: firmware brief

What the firmware has to do, for the code track. Build it as a PlatformIO project in this folder (`7-firmware/`), following "Revisions → Firmware" in the repo's `CLAUDE.md`:
- Generate `include/pins.h` from `../5-electronics/src/design.py`, so the code and the board can't disagree.
- Stub what needs real hardware.
- Make `pio run` build cleanly.
- Record flash/RAM use, the libraries used and any hardware wishes in `7-firmware/NOTES.md`.
- Post hardware changes as requests in `../FIT.md`.

Background: `../REV.md` (what changed in Rev B) and `../5-electronics/NOTES.md` (the board, plus its "Firmware notes" section).

## The product in one paragraph

Backpack Defender is a kid's motion alarm that clips onto a backpack (or sits in a locker). It's a mint pebble with a kawaii face. A PIR sensor under a purple dome watches for someone reaching in. When it trips, it plays a sound the kid chose, flashes the white eye LEDs and lights the clear button in colour. The big button silences it. A settings page over the device's own Wi-Fi hotspot lets the kid pick the sound and the button colour.

## Hardware

- **MCU:** ESP32-C3-WROOM-02-N4 (4 MB flash, no PSRAM). Use PlatformIO board `esp32-c3-devkitm-1` (Arduino or ESP-IDF; Arduino is fine).
- **Power:** 2 × AAA → slide switch (off = cells disconnected) → reverse-battery FET → TPS61023 boost → 3.3 V, always on while switched on. There's no charging and no USB power in normal use.
- **Programming:** native USB (IO18/IO19) on a Tag-Connect TC2030 pad. Serial logs go over USB-CDC, because UART0's pins are used for the RGB LED.

| GPIO | Net | Direction / level | What it is |
|---|---|---|---|
| IO0 | PIR_OUT | in, **high = motion** (~2 s pulse) | AM312 PIR. Deep-sleep wake source |
| IO1 | BTN | in, **low = pressed** (100 k pull-up on the board) | Big silence button. Deep-sleep wake source |
| IO3 | VBAT_SENSE | analog in | Battery voltage ÷ 2 (1 M / 1 M divider, 100 nF) |
| IO4 | I2S_BCLK | out | MAX98357A bit clock |
| IO5 | I2S_LRCLK | out | MAX98357A word select |
| IO6 | I2S_DIN | out | MAX98357A data |
| IO7 | AMP_SD | out, **high = amp on** (100 k pull-down) | Amp enable; mono, left channel when high. Gain 9 dB (GAIN_SLOT open) |
| IO10 | EYE_LED | out, **high = both eye LEDs on** (100 k pull-down) | Two white LEDs under the eye light pipes, via an N-FET. PWM is fine |
| IO20 | RGB_DATA | out | WS2812B-2020 data (one pixel) under the clear button |
| IO21 | RGB_PWR_N | out, **low = LED powered** (100 k pull-up) | P-FET high-side switch for the RGB LED's supply |
| IO2, IO8, IO9 | straps | pulled high | Leave alone (IO9 low at reset = download mode) |
| IO18 / IO19 | USB D− / D+ | | Native USB |

- **Speaker:** 20 mm, 8 Ω, 1 W, driven by the MAX98357A from 3.3 V. Expect roughly 0.5 W peak at most. Keep the volume sensible, because the boost runs from AAA cells.

## Behaviour

1. **Power on (slide switch).**
   - Button held at power-on → **Setup mode** (step 5).
   - Otherwise a short "I'm awake" chirp and a gentle eye blink, then **Armed**.
2. **Armed: deep sleep.**
   - Wake on IO0 high (PIR) or IO1 low (button): `esp_deep_sleep_enable_gpio_wakeup`. On the C3 only IO0–IO5 can wake it, and both are in range.
   - Target a few µA. Before sleeping:
     - AMP_SD low
     - EYE_LED low
     - RGB_PWR_N high (or released to its pull-up): a dark WS2812 still draws about 1 mA
     - Wi-Fi off
   - Use GPIO hold if a level must survive sleep.
3. **Alarm** (PIR wake):
   - Amp on, play the chosen sound for about 10 s (setting).
   - Flash the eye LEDs in time with it.
   - Light the button LED in the chosen colour, or run the rainbow.
   - Then everything off and back to Armed.
   - Ignore PIR re-triggers during a short hold-off.
4. **Silence** (button press, during an alarm or on a button wake):
   - Stop the sound at once.
   - A brief button-LED flash as feedback.
   - Skip PIR wakes for a cool-down (e.g. 60 s, setting): a timer wake, then re-arm.
5. **Setup mode (AP + captive portal).**
   - Start a SoftAP `BackpackDefender-XXXX` (last 4 hex of the MAC) with a captive portal page, made friendly for kids.
   - **Alarm sound:** a list of sounds and melodies with a Preview button that plays on the device.
   - **Button colour:** a palette of colours plus a **Rainbow** option (slow HSV hue sweep around the colour wheel), with a live preview on the LED as you choose. Optionally a brightness slider (low by default).
   - Optional: alarm length, volume, cool-down.
   - Save everything to NVS. Leave setup mode by pressing Save (then reboot into Armed) or after a few minutes idle.
6. **Low battery.**
   - Read IO3 on a wake (VBAT = 2 × reading; calibrate with the ADC's eFuse calibration).
   - Below about 2.1 V, play a "sad" chirp, at most once a day.
   - Below about 1.9 V, skip the alarm sound so the boost doesn't brown out. Flash the eyes only.

## Sounds (hosts' request: "a more interesting library of sounds and melodies")

The MAX98357A plays real I2S audio, so this can go well beyond beeps. Rev A's tone families were goofy, playful, musical, robotic and classic alarm. Candidates to evaluate (not yet checked on the ESP32-C3):

- **ESP8266Audio** (Earle Philhower): WAV / MP3 / MIDI (TinySoundFont) / RTTTL / MOD over I2S, and it supports ESP32 targets.
- **pschatzmann/arduino-audio-tools**: I2S output plus synthesis, including STK instruments.
- **Mozzi**: synth voices, envelopes and effects. Check its I2S support on the C3.
- **RTTTL ringtone collections**: tiny, and a quick way to a big melody list.

Keep clips short: mono 16 kHz PCM, or synthesised. The 4 MB flash leaves room for a LittleFS partition of clips. Record what you choose, and its flash use, in `NOTES.md`.

## Not hardware yet / stubs

- The PIR and the button can be simulated over serial (e.g. typing `p` or `b`) so the state machine can be tested on a bare ESP32-C3 dev board.
- A plain ESP32-C3 dev board has its own WS2812 on **GPIO8**, not IO20. Make the RGB pin a build flag so a dev board can stand in for the real one.

## Done when

- `pio run` builds cleanly.
- `include/pins.h` is generated from `design.py`.
- The states above are implemented, or stubbed where hardware is needed.
- `7-firmware/NOTES.md` records flash/RAM use, the libraries chosen and anything the hardware should change.
