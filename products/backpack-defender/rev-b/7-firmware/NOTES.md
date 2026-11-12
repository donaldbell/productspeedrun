# Backpack Defender Rev B: firmware notes

A PlatformIO project (Arduino on ESP32-C3) for the Rev B board in `../5-electronics/`. The brief is in `BRIEF.md`. **It builds cleanly but has not run on hardware yet**: there is no Rev B board, and nobody has flashed a dev board yet.

## Build and try it

```sh
cd products/backpack-defender/rev-b/7-firmware
pio run                     # the real board (env backpack-defender): 0 warnings
pio run -e devkit           # a plain ESP32-C3-DevKitM-1 on the bench: 0 warnings
pio run -t upload           # real board: Tag-Connect TC2030 on J2 (native USB), hold IO9 low for download mode
pio device monitor          # logs, and the serial test keys below
test/render_sounds.sh       # render every sound to preview/*.wav on the Mac with the firmware's own engine, and check them
```

PlatformIO is installed in `~/.platformio/penv/bin/pio` (not on `PATH` on this Mac). It uses platform `espressif32@6.12.0`, which is Arduino-ESP32 2.0.17 on ESP-IDF 4.4.

| env | for | differences |
|---|---|---|
| `backpack-defender` | the Rev B board | real deep sleep. Wakes on IO0 (PIR, high) / IO1 (button, low) / timer. Logs over native USB-CDC |
| `devkit` | ESP32-C3-DevKitM-1 (WS2812 on GPIO8, USB-UART bridge) | `-DPIN_RGB_DATA=8`, `PIN_BTN=9` (the BOOT button), `PIN_RGB_PWR_N=1`, logs on UART0, simulated sleep, internal pulls, battery faked at 2.9 V |

**Serial test keys** (devkit; the real board reads `b` during an alarm): `p` fakes the PIR, `b` the button, `s` enters setup mode, `+` / `-` step through the sound library and play each one, `c` prints the engine's CPU use for the last sound, `v` reads the battery, `r` restarts. To try the sounds on a devkit, wire a MAX98357A breakout to IO4 (BCLK), IO5 (LRC), IO6 (DIN) and IO7 (SD).

## pins.h comes from the board

`scripts/gen_pins.py` runs `../5-electronics/src/design.py` against a stub of the kit's `schkit` (no KiCad needed). It finds the ESP32-C3-WROOM-02 and maps the module's pins to GPIOs using the datasheet's pin table, and writes `include/pins.h`:

- one `PIN_<NET>` per signal net, each `#ifndef`-wrapped so a build flag can move it
- `PIN_<NET>_PULLUP` / `_PULLDOWN`, read from the resistors on that net
- `VBAT_SENSE_RATIO` from R3/R4

`scripts/pio_pre.py` runs it (and `gen_sounds.py`, below) before every build, so a board change shows up in the next `pio run`. `python3 scripts/gen_pins.py --check` fails if the checked-in `pins.h` is stale. `src/config.h` `#error`s if the board loses a pull the firmware relies on (AMP_SD / EYE_LED pull-downs, RGB_PWR_N and BTN pull-ups). It also fails if a wake pin moves outside GPIO0–5, the only pins the C3 can wake from deep sleep on.

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

## Sound library: Phil Burk's Mobileer ringtones

The hosts disliked the custom synth's sounds, so the alarm sounds are now the hosts' picks from Phil Burk's **Mobileer** ringtones. They play on his Mobileer engine ([philburk/mobileer-synth](https://github.com/philburk/mobileer-synth), Apache-2.0), the General MIDI ringtone synth that shipped in the Palm Treo. The previews they chose from are in `preview/mobileer/` (see its README).

**The library** (`scripts/gen_sounds.py`; the first entry is the default):

| Key | Tile | Family | File (`sounds/mobileer/`) | Length | Peak held notes |
|---|---|---|---|---|---|
| `ringandting` | Ring and Ting 🔔 | Rings | `RingAndTing_rt.mid` | 4.0 s | 4 |
| `fiverecho` | Fiver Echo 📣 | Rings | `FiverEcho.mid` | 3.0 s | 13–14 |
| `steeldrum` | Steel Drum 🥁 | Rings | `Tremolo1_SteelDrum.mid` | 4.0 s | 2 |
| `upanddown` | Up and Down 🎢 | Songs | `UpAndDown_rt.mid` | 2.0 s | 7 |
| `echoecho` | Echo Echo 🏔️ | Songs | `EchoEcho_rt.mid` | 12.0 s | 9–10 |
| `furelise` | Für Elise 🎹 | Songs | `FurElise_rt.mid` | 9.0 s | 4 |

The four **system chirps** (awake, sad, silenced, saved) are tiny MIDI files that `gen_sounds.py` writes into `sounds/system/`: glockenspiel, oboe and marimba notes, played by the same engine. A saved sound key that no longer exists (any of the old synth's 28) falls back to the default.

**How it's built:**

- **Engine:** `lib/mobileer/` is the **ME1000** edition (virtual-analog instruments, no wavetables, 32-bit fixed point, no float). It is 14 of the upstream `.c` files and their 34 headers, with one `#undef assert` added (`lib/mobileer/NOTICE`). `lib/mobileer/config/spmidi_user_config.h` sets 16 voices, mono, a 22.05 kHz maximum, one context, one player and static allocation. `platformio.ini` passes that config to every file, so the firmware and the engine agree on struct sizes.
- **Data:** `scripts/gen_sounds.py` turns each `.mid` into a `const uint8_t[]` in flash (`src/sound_data.h`, an xxd-style dump). It runs before every build, beside `gen_pins.py`. The six picks are 3.3 KB of MIDI in total.
- **Playback:** `src/ringtone.cpp` wraps the engine. The audio task calls `MIDIFilePlayer_PlayFrames` + `SPMIDI_ReadFrames` in 64-frame engine blocks, 256 samples (11.6 ms) per I2S write, through the same legacy I2S path, stereo slots and 4 DMA buffers as before.
  - **Loops:** an alarm restarts the file the moment it ends, so ringing notes carry across the join.
  - **Ends:** a one-shot lets its last notes ring for up to 4 s.
  - **Stop:** stop is still immediate. The amp's SD pin drops first, then all-sound-off goes to all 16 channels.
- **Sample rate: 22.05 kHz.** It is one of the engine's built-in rates, and it gives about 11 kHz of bandwidth. That keeps the bells and the bright ME1000 timbres crisp on a 20 mm speaker, which still has response up there, while it has little below ~600 Hz anyway. 16 kHz would save about a quarter of the CPU, but it dulls the rings.
- **Levels:** the ringtones were authored at very different levels (peaks from 2.7k to 13k at the engine's default volume). Each sound gets its own engine master volume in `gen_sounds.py` (270–2300, where 128 is as authored), so every one peaks near 28,000. `test/render_sounds.sh` prints a suggested value for each sound.
- **Volume steps:** gain 30–160/256 on top of that. The top step is ~53 % of full scale, under the ~0.5 W peak into 8 Ω that the AAA boost should be asked for. The default is step 3; chirps play at step 2.
- **Kept:** the eyes still flash with the loudness of each 11.6 ms block, below 1.9 V there's still no sound, and the setup page's tiles and ▶ preview now list these six.

**Previews:** `test/render_sounds.sh` compiles the vendored engine, `src/ringtone.cpp` and `src/sound_data.h` with the Mac's compiler. It renders every sound to `preview/<key>.wav` (22.05 kHz mono, exactly the firmware's stream before the volume step) and checks that each one ends, isn't silent and doesn't clip. All 10 pass. With enough voices (32), my mono build matches the stock `play_midifile` render sample for sample (correlation 1.00).

## Polyphony and CPU

- **Voice limit: 16.** The picks peak at 2–14 held notes, but released notes keep a voice while they ring out. At its busiest, FiverEcho wants ~28 voices to match the stock render sample for sample, and EchoEcho a little more.
  - **What 16 costs:** with 16, the engine steals the faintest echo tails.
  - **Measured against a 32-voice render:** FiverEcho's spectrum is within 0.1 dB and its loudness envelope matches at the median, differing only at a few moments (95th percentile 2.9 dB). EchoEcho is within 0.5 dB throughout. The other four never reach 16.
  - **Why not more:** going to 32 would roughly double the worst-case CPU for a difference that's hard to hear.
  - **Listen:** compare `preview/mobileer/rings/FiverEcho.wav` (stock, all voices) with `preview/fiverecho.wav` (the firmware's 16).
- **Measured on the Mac (M1):** cost grows linearly with voices, about 0.15 µs of CPU per ms of audio per sustained square-lead voice. Coarse timer; this shows the trend, not the C3's number.
- **Estimate for the C3 at 160 MHz:** Mobileer's own figure is 2.4 MIPS per synthesized voice at 44.1 kHz on an ARM946, so ~1.2 MIPS at 22.05 kHz. On an in-order RV32IMC running from flash cache, that's roughly 1.5–3.5 % of the CPU per voice, so **~20–35 % with all 16 voices**, and well under 15 % for most of the picks. **Not measured on a C3 yet.**
- **The firmware measures it:** the audio task times every render, and after each alarm the log shows `[audio] engine … us avg / … us worst per 11610 us block (…% CPU), up to N notes` (`c` on the devkit). If the worst case ever passes ~70 %, lower `SPMIDI_MAX_VOICES`, drop to 16 kHz, or move the engine's inner loops (`oscillator.c`, `spmidi_hybrid.c`) to IRAM.

## Flash and RAM

From `pio run` (partition table `min_spiffs.csv`: two 1.9 MB OTA app slots + 128 KB SPIFFS, on the 4 MB flash):

| env | Flash (app) | RAM (static) |
|---|---|---|
| backpack-defender, custom synth (before) | 837,720 B of 1,966,080 (42.6 %) | 43,300 B of 327,680 (13.2 %) |
| backpack-defender, **Mobileer (now)** | **855,440 B (43.5 %)** | **49,100 B (15.0 %)** |
| devkit, Mobileer | 860,368 B (43.8 %) | 49,060 B (15.0 %) |

- **The engine adds +17.7 KB of flash** after the linker drops unused functions. Its objects hold 32.5 KB of code and presets, and the six MIDI files are another 3.3 KB.
- **It adds +5.8 KB of static RAM**: 7.2 KB of engine pools (player, context and voices), minus the old synth's buffers.
- **Stack:** the audio task's stack went from 4 to 6 KB (heap, not in the static figure).
- **Headroom:** ~270 KB of RAM is still free.
- **Our own code** is ~25 KB (portal 13 KB, sound tables 4 KB).

**Libraries:** the vendored Mobileer ME1000 engine (Apache-2.0, credited in `lib/mobileer/NOTICE` and the repo's `CREDITS.md`) and the Arduino-ESP32 2.0.17 core: WiFi, WebServer, DNSServer, Preferences (NVS), `neopixelWrite` (RMT) for the WS2812, LEDC for the eye PWM, and the ESP-IDF legacy I2S driver.

**Before the switch:** ESP8266Audio 2.4.1 didn't build on this core. ESP8266Audio 1.9.7 (240 KB) and arduino-audio-tools (284 KB, float maths) did. Our own synth was ~8 KB. Its code is in git history (commit `31dcbe3`).

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
- The Mobileer sounds have been heard only as rendered WAVs, not through the 20 mm speaker, and the engine's CPU use on a C3 is an estimate. The first bench run should read the `[audio] engine` log line during FiverEcho, the busiest sound.
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
