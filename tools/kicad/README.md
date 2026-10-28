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
| `tools/kicad/build.sh episodes/<slug> schematic` | Schematic, ERC, netlist check, `bom.csv`, `schematic.png` | seconds |
| `tools/kicad/build.sh episodes/<slug> place` | Also places the board and renders a quick `board.png` | under a minute |
| `tools/kicad/build.sh episodes/<slug>` | Everything: Freerouting, DRC fix-ups, silkscreen tidy, DRC, renders, `board.glb` | 5–15 min |
| `tools/kicad/export.sh episodes/<slug>` | Only the BOM, pictures and GLB again (after a hand edit in KiCad) | about a minute |
| `tools/kicad/selftest.sh [place]` | Rebuilds episode 001's board in a scratch folder to check the kit works on this computer | as a build |

Each step saves as it goes, so the dashboard shows the schematic first, then the placed board, then the routed one.

## Writing `design.py`

- `setup("plant-whisperer", lib="plant", title="Plant Whisperer", company="Product Speedrun 002")` first.
- `part(ref, lib_id, value, footprint, lcsc, mpn, at(col, row), {pin: net}, description, dnp=True?)` for each part. Every pin needs a net, or `None` for no-connect. `cap()` and `res()` cover common 0603/0805 values (tables `CAPS` and `RES` in `schkit.py`; add values as needed).
- Stock KiCad symbols and footprints by their library IDs. A part KiCad doesn't ship gets a `box_symbol()`. When one is drawn, move it into `parts.py` so the next episode can reuse it.
- `NOTES` puts text on the sheet, and `OFF_BOARD` adds BOM lines for batteries, speakers and cables.
- Copy whole blocks from `example/design.py` where they fit: the 2 × AAA boost with reverse-battery FET, the ESP32-C3 module with EN RC, strap pull-ups and USB pogo pads, the I2S amp, the PIR with its supply filter, the button, test pads, holes and fiducials.

## Writing `layout.py`

Coordinates are the Stage 4 enclosure's (origin at the centre, mm, +y up), from the "For Stage 5" list in `4-model/NOTES.md`.

- `BOARD = (width, height, corner_radius)`. Use radius = half the width for a pill, or a square with half-width radius for a disc.
- `HOLES` holds positions for H1, H2 and so on, and `HOLE_KEEPOUT` is the keep-out around each one (no parts, no copper).
- `FIXED` holds parts that must sit exactly under the enclosure's features (module, buttons, sensors, LEDs). The footprint origin goes at the given point, and for THT parts that's often pin 1.
- `ROWS` holds pad rows (headers, wire pads, THT sensors), given as pin 1 plus the direction to pin 2. `ROW_LABELS` adds their silkscreen pin names.
- `PREFER` holds everything else, in priority order (each IC first, then its decoupling). The auto-fitter spirals out up to 16 mm to the nearest free spot and lists what it moved in `output/placement.txt`.
- `NO_PARTS` rectangles keep parts out (under tall parts, antennas). `NO_COPPER` keeps copper out (antenna keep-outs).
- Optional: `POWER_NETS` (0.5 mm tracks), `GND_VIA_PADS` (parts with a big ground pad), `MODEL_SUBST` (stand-in 3D models), `HIDE_TEXT`, and a `silk(board, placed)` function for extra silkscreen such as the product name on the back.

## What the full build does

1. Generates the schematic and project, runs ERC, exports the netlist and checks every pin landed on its intended net.
2. Loads stock footprints, places them, then adds the outline, keep-outs and the bottom GND pour.
3. Adds GND vias at the big ground pads and the top GND pour, then runs Freerouting twice headless (`ROUTE_PASSES`, default 40) and stitches GND vias across the pours and islands.
4. Runs two DRC passes with fixes: widens neck-downs, gives unreached GND pads a via, and removes dangling vias.
5. Moves reference labels off pads, then runs the final DRC and writes `drc.rpt`.
6. Writes the renders and `board.glb` (scaled to metres for the web viewer).

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
