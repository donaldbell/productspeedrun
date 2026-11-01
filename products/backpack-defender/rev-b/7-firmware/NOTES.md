# Backpack Defender Rev B: firmware notes

A PlatformIO project (Arduino on ESP32-C3) for the Rev B board in `../5-electronics/`. The brief is in `BRIEF.md`. **It builds cleanly but has not run on hardware yet**: there is no Rev B board, and nobody has flashed a dev board yet.

## Build and try it

```sh
cd products/backpack-defender/rev-b/7-firmware
pio run                     # the real board (env backpack-defender): 0 warnings
pio run -e devkit           # a plain ESP32-C3-DevKitM-1 on the bench: 0 warnings
pio run -t upload           # real board: Tag-Connect TC2030 on J2 (native USB), hold IO9 low for download mode
pio device monitor          # logs, and the serial test keys below
test/render_sounds.sh       # render every sound to preview/*.wav on the Mac, and check them
```

PlatformIO is installed in `~/.platformio/penv/bin/pio` (not on `PATH` on this Mac). It uses platform `espressif32@6.12.0`, which is Arduino-ESP32 2.0.17 on ESP-IDF 4.4.

| env | for | differences |
|---|---|---|
| `backpack-defender` | the Rev B board | real deep sleep. Wakes on IO0 (PIR, high) / IO1 (button, low) / timer. Logs over native USB-CDC |
| `devkit` | ESP32-C3-DevKitM-1 (WS2812 on GPIO8, USB-UART bridge) | `-DPIN_RGB_DATA=8`, `PIN_BTN=9` (the BOOT button), `PIN_RGB_PWR_N=1`, logs on UART0, simulated sleep, internal pulls, battery faked at 2.9 V |

**Serial test keys** (devkit; the real board reads `b` during an alarm): `p` fakes the PIR, `b` the button, `s` enters setup mode, `+` / `-` step through the sound library and play each one, `v` reads the battery, `r` restarts. To try the sounds on a devkit, wire a MAX98357A breakout to IO4 (BCLK), IO5 (LRC), IO6 (DIN) and IO7 (SD).

## pins.h comes from the board

`scripts/gen_pins.py` runs `../5-electronics/src/design.py` against a stub of the kit's `schkit` (no KiCad needed). It finds the ESP32-C3-WROOM-02 and maps the module's pins to GPIOs using the datasheet's pin table, and writes `include/pins.h`:

- one `PIN_<NET>` per signal net, each `#ifndef`-wrapped so a build flag can move it
- `PIN_<NET>_PULLUP` / `_PULLDOWN`, read from the resistors on that net
- `VBAT_SENSE_RATIO` from R3/R4

`scripts/pio_pins.py` runs it before every build, so a board change shows up in the next `pio run`. `python3 scripts/gen_pins.py --check` fails if the checked-in `pins.h` is stale. `src/config.h` `#error`s if the board loses a pull the firmware relies on (AMP_SD / EYE_LED pull-downs, RGB_PWR_N and BTN pull-ups). It also fails if a wake pin moves outside GPIO0–5, the only pins the C3 can wake from deep sleep on.

## How it behaves

Every wake from deep sleep is a fresh boot. `setup()` works out why it woke, does one job, picks the next sleep and sleeps. RTC memory holds what must survive: why the timer was set, when the sad chirp last played, and the alarm count.

| Wake | What happens | Sleeps next with |
|---|---|---|
| Power on (slide switch), button held 0.6 s | **Setup mode** (below) | restarts |
| Power on | "I'm awake" chirp, eyes blink twice in the chosen button colour, battery check | **Armed**: PIR + button + 24 h timer |
| PIR | **Alarm** for `alarmSecs` (default 10 s): the chosen sound loops. The eyes flash with its loudness, and the button LED shows the colour or rainbow at +30 % brightness | **Hold-off**: button + 5 s timer (PIR ignored) |
| Button press during the alarm, or button wake | **Silence**: amp off at once, 3 quick button-LED flashes | **Cool-down**: button + `cooldownSecs` timer (default 60 s, PIR ignored) |
| Timer | Daily: battery check. Hold-off / cool-down: nothing | Armed |

Details:

- **Arming with the PIR still high** (its ~2 s pulse after an alarm): the wake is level-triggered, so it would fire at once. The firmware sleeps 2 s more on a timer, then tries again.
- **Button still held when going to sleep:** it waits up to 3 s for the release. If the button is still down after that, it sleeps without a button wake and on a 5 s timer, so a stuck button can't keep it awake.
- **Before deep sleep:**
  - AMP_SD low, EYE_LED low, RGB_PWR_N high (LED unpowered) and RGB_DATA low (so the unpowered LED isn't fed through its data pin), each with `gpio_hold_en` + `gpio_deep_sleep_hold_en`.
  - I2S is uninstalled.
  - Wi-Fi is only ever on in setup mode, which leaves by restarting.
- **Battery:** VBAT = 2 × IO3 (ADC1, 11 dB, eFuse-calibrated `analogReadMilliVolts`, 16 samples), read on every wake before the amp turns on.
  - Below 2.1 V: a sad chirp and droopy eyes, at most once every 24 h (and at power-on). The clock is `gettimeofday`, which keeps running through deep sleep.
  - Below 1.9 V: the alarm is lights only (eyes flash at 4 Hz), with no sound and no chirps.
- **Setup mode:**
  - An open SoftAP `BackpackDefender-XXXX` (the last 2 MAC bytes) at 8.5 dBm, with a DNS catch-all and a captive-portal redirect for every unknown URL (Android, Apple and Windows probes).
  - The page (`src/portal_html.h`, ~5 KB, no external files) shows sound tiles grouped by family with a ▶ preview that plays on the device, 10 colour swatches plus Rainbow with a live preview on the LED, and a brightness slider (12 % by default).
  - Under "Extras": volume 1–5, alarm length 3–30 s and quiet time 10–300 s.
  - **Save & start guarding!** writes NVS (namespace `bd`; the sound is stored by its key, so reordering the library is safe), plays a "saved" jingle and restarts into Armed. With no page request for 5 minutes it restarts without saving.
  - The big button stops a preview.

## Sound library

The hosts asked for "a more interesting library of sounds and melodies … from existing I2S synth and sound libraries". I tried the candidates on this exact toolchain (ESP32-C3, Arduino 2.0.17):

| Library | Result on the C3 |
|---|---|
| **ESP8266Audio 2.4.1** (latest) | **Doesn't build**: it needs ESP-IDF 5's `driver/i2s_std.h` (Arduino-ESP32 3.x) |
| **ESP8266Audio 1.9.7** | Builds. An RTTTL-over-I2S test uses 240 KB flash / 13.5 KB RAM. It's worth it for MP3/WAV/MIDI clips |
| **arduino-audio-tools** (pschatzmann, git head) | Builds. A sine-to-I2S test uses 284 KB flash / 14.7 KB RAM. Its generators and STK instruments are float maths, and the C3 has **no FPU** |
| **Mozzi** | Not tried. It is built for 8-bit-style fixed-point synthesis; its I2S output on the C3 is unchecked |
| **RTTTL collections** | The format is used, but the tunes were written out for this project: most collections are copyrighted pop and film themes |

**Chosen: our own fixed-point synth** (`src/synth.cpp`, `src/sounds.cpp`).

- **Size and dependencies:** about 8 KB of flash and no dependencies.
- **Maths:** integer only (RV32IMC has hardware multiply and divide, but no float). Nothing divides per sample.
- **Output:** 16 kHz mono through the core's legacy I2S driver (stereo frames, the same sample in both slots), from its own FreeRTOS task with 4 × 16 ms DMA buffers.
- **Stopping:** stop is immediate, because the amp's SD pin drops before the queue flushes.
- **Waveforms:** square, 25 % pulse, triangle, saw, sine, a 4-harmonic organ table, LFSR noise, a 2-operator FM bell, and a Karplus-Strong plucked string.
- **Melodies:** RTTTL strings played on a voice (ADSR + vibrato). The 20 mm speaker has little below ~600 Hz, so most voices play an octave up.
- **Effects:** lists of segments, each a linear or exponential pitch sweep with a volume ramp and a wobble LFO, or a random-pitch burst.

**The library: 28 alarm sounds** in Rev A's five families, plus 4 system sounds (awake, sad, silenced, saved). `test/render_sounds.sh` renders all of them to `preview/<key>.wav` and checks that each one ends, isn't silent and doesn't clip. All 32 pass. Melody pitches were spot-checked by autocorrelation.

| Family | Sounds |
|---|---|
| Alarm | Siren, Whoop Whoop, Klaxon, Beep Beep Beep, Charge! (bugle) |
| Goofy | Boing, Slide Whistle, Raspberry, Dino Stomp (ours) |
| Robot | Laser Zap, Robot Talk (random bleeps), Computer, UFO |
| Playful | Birdies, Bubbles, Drum Roll, Level Up! (ours), Bumblebee (Rimsky-Korsakov) |
| Musical | Mountain King (Grieg), Galloping Horse (Rossini's William Tell), Can-Can (Offenbach), The Entertainer (Joplin), Für Elise, Ode to Joy (Beethoven), Twinkle Star, Frère Jacques, La Cucaracha, Old MacDonald (traditional) |

**The tunes were written out from memory: check them by ear** (`preview/*.wav`) before anyone ships them. They are all public domain or our own.

**Volume:** five steps, with gain 30–160/256 on top of the synth's ~75 % peak. The top step is ~62 % of full scale. At the amp's 9 dB gain from 3.3 V that is an estimated ~0.5 W peak into 8 Ω (a square wave is the worst case). That is about what the brief allows the boost to deliver from AAA cells. The default is step 3; chirps play at step 2.

## Flash and RAM

From `pio run` (partition table `min_spiffs.csv`: two 1.9 MB OTA app slots + 128 KB SPIFFS, on the 4 MB flash):

| env | Flash (app) | RAM (static) |
|---|---|---|
| backpack-defender | 837,720 B of 1,966,080 (42.6 %) | 43,300 B of 327,680 (13.2 %) |
| devkit | 842,652 B (42.9 %) | 43,244 B (13.2 %) |

Our own code is ~31 KB of that (portal 13 KB, synth + library 8 KB). The rest is Wi-Fi, lwIP, WebServer and the Arduino core. The app slot has room for ~1 MB of PCM clips later, or for ESP8266Audio, without changing the partition table. A LittleFS clip partition would need a custom table.

**Libraries:** none beyond the Arduino-ESP32 2.0.17 core: WiFi, WebServer, DNSServer, Preferences (NVS), `neopixelWrite` (RMT) for the WS2812, LEDC for the eye PWM, and the ESP-IDF legacy I2S driver.

## Sleep current (estimate, to be measured)

| Draw | Estimate | Source |
|---|---|---|
| ESP32-C3 deep sleep, GPIO wake | ~5 µA | datasheet |
| AM312 PIR | ~12–15 µA | always powered |
| VBAT divider R3/R4 | 1.5 µA | 3 V / 2 MΩ |
| TPS61023 boost quiescent, plus leakage | tens of µA | **unknown: measure on the board** |

The ESP32 side is ~20 µA before the boost. Two AAA (~1000 mAh) would last years in standby if the boost's no-load draw is small. An alarm costs roughly 10 s × ~150 mA. Setup mode with Wi-Fi is the heaviest load.

## Stubbed or untested (needs real hardware)

- Everything has only been compiled. Nothing has run on a C3 yet. The first bench session should check:
  - The deep-sleep wake on IO0-high / IO1-low with two `esp_deep_sleep_enable_gpio_wakeup` calls, and `esp_sleep_get_gpio_wakeup_status()` telling them apart.
  - The sleep current with the pin holds.
  - That ESP-IDF releases the digital pin holds on wake as documented. `lightsBegin` / `audioBegin` also release them.
- The PIR and the button are simulated over serial (`p` / `b`) and by the devkit's BOOT button. The devkit's battery reading is faked (`BD_FAKE_VBAT_MV`).
- The sound library has been heard only as rendered WAVs, not through the 20 mm speaker. Expect to retune the voice octaves and the effect pitches by ear.
- The captive portal was built against the core's WebServer and DNSServer but hasn't been tried on iOS or Android.
- There is no OTA update, and no factory reset beyond reflashing (a long press during setup could clear NVS later).

## Hardware wishes

Posted in `../FIT.md` as requests to Stage 5:

- **Bulk capacitance on VBAT.** C1 is 10 µF. Wi-Fi TX bursts in setup mode (~300 mA at 3.3 V, so ~0.6 A from 2 V cells) and amp peaks on tired cells could brown out the C3. Adding 47–100 µF at U1's input is cheap insurance. The firmware already caps the AP at 8.5 dBm and the amp at ~0.5 W, and skips sound below 1.9 V.

Noted only, no change asked:

- **IO21 (RGB_PWR_N) is UART0 TX.** The ROM bootloader prints its boot banner there on every wake, which pulses Q3 and the button LED's supply for a few ms (the LED stays dark without data). If it's ever visible, either burn the `UART_PRINT_CONTROL` eFuse (ROM log off) or move RGB_PWR_N in a later revision.
- The firmware leans on R11, R16 and R17 to keep the amp, the eyes and the RGB LED off while the C3 boots. `config.h` checks they're still in `design.py`.

## Open questions

- Should the button LED glow softly while armed? It's off for now to protect the battery (the WS2812 draws ~1 mA even when dark). A slow "breathe" every few seconds on a timer wake would cost little.
- Should a button wake while armed (not during an alarm) do something more useful than a 60 s cool-down? For example, play the chosen sound once, as a "test" for the kid.
- The setup AP is open, on purpose, for kids. Add a password printed on the name plate if that's a concern.
- Volume steps and alarm loudness, once there's a speaker to listen to.
