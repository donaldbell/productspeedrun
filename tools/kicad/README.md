# KiCad kit

Shared tools for Stage 5. An episode describes its board in two short Python files, and one command turns them into a checked, routed 2-layer PCB with everything the dashboard shows. The kit grew out of episode 001's Backpack Defender board, which came from the earlier bollard v2 board.

```
episodes/<slug>/5-electronics/
  src/design.py    parts and nets            (you write this)
  src/layout.py    outline and placement     (you write this)
  <name>.kicad_sch / .kicad_pcb / .kicad_pro, lib/, bom.csv, erc.rpt, drc.rpt,
  schematic.png, board.png, board-bottom.png, board-iso.png, board.glb   (the kit writes these)
  output/          netlist, DRC JSON, Freerouting logs, placement.txt (not committed)
```

## Commands

Run from the repo folder.

| Command | What it does | Time |
|---|---|---|
| `tools/kicad/new_board.sh episodes/<slug> <name> "<Title>"` | Starts `src/design.py` and `src/layout.py` from the template | instant |
| `tools/kicad/build.sh episodes/<slug> schematic` | Schematic, ERC, netlist check, `bom.csv`, `schematic.png`, and `SIZE.md` (how much board area the parts need) | seconds |
| `tools/kicad/build.sh episodes/<slug> place` | Also places the board and renders a quick `board.png` | under a minute |
| `tools/kicad/build.sh episodes/<slug>` | Everything: Freerouting, DRC fix-ups, silkscreen tidy, DRC, renders, `board.glb` | 5–15 min |
| `tools/kicad/export.sh episodes/<slug>` | Only the BOM, pictures and GLB again (after a hand edit in KiCad) | about a minute |
| `tools/kicad/selftest.sh [place]` | Rebuilds episode 001's board in a scratch folder to check the kit works on this computer; the full run fails unless DRC is 0 violations, 0 unconnected | as a build |
| `tools/kicad/selftest.sh all blocks/<name>` | The same for one of the brain blocks below | 2–5 min |

Each step saves as it goes, so the dashboard shows the schematic first, then the placed board, then the routed one.

## Writing `design.py`

- `setup("plant-whisperer", lib="plant", title="Plant Whisperer", company="Product Speedrun 002")` first.
- `part(ref, lib_id, value, footprint, lcsc, mpn, at(col, row), {pin: net}, description, dnp=True?)` for each part. Every pin needs a net, or `None` for no-connect. `cap()` and `res()` cover common 0603/0805 values (tables `CAPS` and `RES` in `schkit.py`; add values as needed).
- Stock KiCad symbols and footprints by their library IDs. A part KiCad doesn't ship gets a `box_symbol()`. When one is drawn, move it into `parts.py` so the next episode can reuse it.
- `NOTES` puts text on the sheet, and `OFF_BOARD` adds BOM lines for batteries, speakers and cables.
- Copy whole blocks from `example/design.py` where they fit: the 2 × AAA boost with reverse-battery FET, the ESP32-C3 module with EN RC, strap pull-ups and USB pogo pads, the I2S amp, the PIR with its supply filter, the button, test pads, holes and fiducials.

## Proven blocks

Copy these rather than drawing them again. Every board here passed ERC, DRC 0 and 0 unconnected.

| Block | Where |
|---|---|
| ESP32-C3-WROOM-02 with EN RC, strap pull-ups, USB pogo pads | `example/design.py` (episode 001) |
| 2 × AAA → 3.3 V boost (TPS61023) with reverse-battery P-FET | `example/design.py` |
| MAX98357A I2S amp + piezo or speaker | both episodes |
| AM312 PIR with RC-filtered supply | both episodes |
| ESP32-S3-WROOM-1 (N16R8) with native USB, EN RC, IO0 pad | `episodes/002-jordan-pilot-episode/5-electronics/src/design.py` |
| USB 5 V in → AP2112K-3.3 LDO | episode 002 |
| ICS-43434 I2S MEMS mic, WS2812B-2020 LEDs on a diode-dropped supply, low-side fan/motor PWM switch | episode 002 |
| Double-sided placement (`BOTTOM`), `TRIM_COURTYARD` for WROOM-1's antenna zone | `episodes/002-jordan-pilot-episode/5-electronics/src/layout.py` |
| Raspberry Pi Pico / Pico 2 soldered flat by its castellations: 5 V in through a Schottky into VSYS, 3V3 decoupling, RUN button, SWD pads under D1–D3, LED (46 × 60 mm) | `blocks/pico/` |
| nRF52840 as a Raytac MDBT50Q-1MV2: USB-C (5.1k CC) → AP2112K-3.3 → VDD + VDDH, native USB, Tag-Connect TC2030 SWD, reset on P0.18, LED, antenna keep-out to the edge (32 × 44 mm) | `blocks/nrf52840/` |
| Raspberry Pi HAT: 65 × 56.5 mm outline, M2.5 holes on the 58 × 49 pattern, 2 × 20 socket on the underside where the Pi's header is, ID EEPROM (CAT24C32 at 0x50, WP pad), decoupling, LED on GPIO17 | `blocks/pi-hat/` |

The blocks are small boards of their own (`design.py` + `layout.py`), not part of an episode: copy their parts and placement into an episode's files. Each file's docstring gives the module's pad coordinates, so the rest of the layout can be planned around it. Notes from building them:

- Pico: the `RaspberryPi_Pico_Debug` symbol adds the SWD pads D1–D3; its AGND and GND pins are both power outputs, so ERC wants a part between them (R2 0R, or a ferrite). Keep the micro-USB end on a board edge.
- nRF52840: use the module's outer pad rows. Their 0.8 mm pitch leaves no room for a track to reach the inner row, so P0.18 (nRESET, inner only) gets a track inward under the module. No `POWER_NETS` on module pins. A blank module needs SWD for its first flash.
- Pi HAT: `BOTTOM = ["J1"]` with `ROWS` pin 1 at (-24.13, 22.98) puts the socket's pins exactly on the Pi's header. Check against the current HAT+ spec before ordering.

## Board size

Most of episode 002's Stage 5 time went into a board that was too small: Stage 4 picked 48 × 26 mm before the parts were known, and Freerouting never finished on it. `build.sh … schematic` now writes `SIZE.md` with the area the parts need. Big parts (modules, sockets) count once with a 2 mm ring round them, and everything else needs 2.5 times its own area. That matches every board so far, including 002's failed 48 × 26 board and the 54 × 31 one that routed. Give Stage 4 that number before it fixes the enclosure, and treat it as the minimum. Putting parts on both faces doesn't shrink it.

## Writing `layout.py`

Coordinates are the Stage 4 enclosure's (origin at the centre, mm, +y up), from the "For Stage 5" list in `4-model/NOTES.md`.

- `BOARD = (width, height, corner_radius)`. Use radius = half the width for a pill, or a square with half-width radius for a disc.
- `HOLES` holds positions for H1, H2 and so on, and `HOLE_KEEPOUT` is the keep-out around each one (no parts, no copper).
- `FIXED` holds parts that must sit exactly under the enclosure's features (module, buttons, sensors, LEDs). The footprint origin goes at the given point, and for THT parts that's often pin 1.
- `ROWS` holds pad rows (headers, wire pads, THT sensors), given as pin 1 plus the direction to pin 2. `ROW_LABELS` adds their silkscreen pin names (`"left"`, `"right"`, `"below"` or `"above"` the pads, and optionally where the title goes).
- `PREFER` holds everything else, in priority order (each IC first, then its decoupling). The auto-fitter spirals out up to 16 mm to the nearest free spot and lists what it moved in `output/placement.txt`.
- `BOTTOM` lists refs that go on the bottom face (mirrored). Their positions and orientations are still given as seen from the top. The auto-fitter lets SMD parts on opposite faces share board area. Keep-outs, through-hole parts and an SMD part's plated holes (module and QFN thermal vias, which carry copper on both faces) block both faces. FIXED parts aren't moved, so check those against the vias yourself. Episode 002 is the worked case: a vertical board with the PIR and LEDs on the front and the module on the back.
- `TRIM_COURTYARD` lists refs whose stock courtyard is replaced by their body outline (Fab layer + 0.25 mm), for modules like the ESP32-S3-WROOM-1 whose courtyard includes an antenna clearance zone wider than a small board. It also drops the footprint's own keep-out zone, and the build turns off DRC's footprint-vs-library check for that board. Pair it with a `NO_COPPER` keep-out under the antenna.
- `NO_PARTS` rectangles keep parts out of both faces (under tall parts, antennas). Write `(rect, "F")` or `(rect, "B")` to keep one face clear, for example under a sensor body that stands on the top face only. `NO_COPPER` keeps copper out (antenna keep-outs).
- Optional: `POWER_NETS` (0.5 mm tracks), `GND_VIA_PADS` (parts with a big ground pad), `MODEL_SUBST` (stand-in 3D models), `HIDE_TEXT`, and a `silk(board, placed)` function for extra silkscreen such as the product name on the back.
- Optional: `PREROUTE`, fixed tracks laid before Freerouting for connections it keeps fumbling or that must be short (a boost converter's switch node). Each entry is a path: `"REF.PAD"`, then `(x, y)` points in board mm, a number to set the track width from there on (default 0.5 mm on `POWER_NETS`, else 0.25 mm), `"via"` to drop a via and carry on on the other layer, ending with `"REF.PAD"` on the same net. It starts on the first pad's layer (the bottom for a bottom-side SMD pad) and must end on a layer the last pad is on. The tracks are locked, so Freerouting routes around them. The points are absolute, so re-check them if you move the parts. The example's BOOST_SW entry is a worked case.

## What the full build does

1. Generates the schematic and project, runs ERC, exports the netlist and checks every pin landed on its intended net.
2. Loads stock footprints, places them, then adds the outline, keep-outs and the bottom GND pour.
3. Lays the `PREROUTE` tracks, adds GND vias at the big ground pads and the top GND pour, then runs Freerouting twice headless (`ROUTE_PASSES`, default 40) and stitches GND vias across the pours and islands. Each Freerouting run is stopped after `ROUTE_TIMEOUT` seconds (default 300), because now and then it never finishes; if the second run fails that way, the first run's routing is kept.
4. Runs two DRC passes with fixes: widens neck-downs, gives unreached GND pads a via, and removes dangling vias and dangling track spurs. If anything is still unconnected, steps 3 and 4 start again from the placed board, up to `ROUTE_TRIES` times (default 3), and the best try is kept.
5. Moves reference labels off pads, then runs the final DRC, writes `drc.rpt` and prints `DRC: N violations, N unconnected`.
6. Writes the renders and `board.glb` (scaled to metres for the web viewer). If the DRC wasn't 0 and 0, the build then says so in a banner and exits with an error.

Freerouting varies from run to run, so a rebuild gives a slightly different board. Once a board is hand-edited in KiCad, stop running `build.sh` on it (it overwrites) and use `export.sh`.

## Machine setup

The defaults are the macOS KiCad app and Freerouting under `~/.local/opt/`. Override them with environment variables if needed:

| Variable | Default |
|---|---|
| `KICAD_CLI` | `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` |
| `KICAD_PY` | KiCad's bundled `python3` (it has `pcbnew`) |
| `KICAD_SHARE` | `/Applications/KiCad/KiCad.app/Contents/SharedSupport` |
| `JAVA` | newest `~/.local/opt/jdk*`, else `java` on the PATH |
| `FREEROUTING_JAR` | newest `~/.local/opt/freerouting/freerouting-*.jar` |

`schematic.png` uses `qlmanage` on macOS, or `pdftoppm` elsewhere. `board.glb` needs `trimesh` in the system `python3` (`pip3 install trimesh`).
