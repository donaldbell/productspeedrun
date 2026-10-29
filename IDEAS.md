# Ideas for later

Things to add once the show as it is becomes routine.

## Firmware sketch (a quick check inside Stage 5)

A rough first pass at the code, run in a third Claude Code window once the schematic exists, to find hardware problems that only show up in code before the board is routed: a library that needs a different pin, RAM or flash that doesn't fit (episode 002's "can Whisper run on an S3?"), peripherals that clash.

- An Arduino or PlatformIO project that sets up every part on the board and stubs the main behaviour. Done means "it compiles", with flash and RAM use reported.
- `tools/kicad` generates `pins.h` from `design.py`, so the code and the board share one pin map.
- If the code needs a different pin, more memory or another chip, it posts a request in `FIT.md` like Stages 4 and 5.
- The showcase page adds a line such as "Firmware: compiles, X KB of flash" and shows the main loop.
- Install the ESP32 toolchain once off-camera; the first download is slow.
- Maybe later: run the firmware in the Wokwi simulator (ESP32 and Pi Pico, not nRF52840) for an on-screen demo, e.g. LED eyes lighting when a virtual PIR trips.
