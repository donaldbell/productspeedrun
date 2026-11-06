# Product Speedrun

This repo is the working folder for **Product Speedrun**, a show where two hosts take a randomly rolled product idea from brainstorm to a showcase-ready concept. Every episode lives in `episodes/<NNN-slug>/`. A local dashboard (`npm start`, http://localhost:4321) shows the run live and watches these folders, so **any file you save in an episode folder appears on screen within a second or two**. That's part of the show, so save outputs as you go rather than all at the end.

## Episode folder layout

```
episodes/<slug>/
  episode.json      # owned by the dashboard: title, roll, brief, prompts, favorite images, decision
  2-concept/        # concept sketches (images). Each generated image has a .prompt.txt beside it
  3-layout/         # isometric layout images
  4-model/          # Stage 4 output: 3D model
  5-electronics/    # Stage 5 output: KiCad project, BOM, board renders
  6-showcase/       # Stage 6 output: the showcase page (index.html and its assets)
```

Rules for every stage:

- **Read `episode.json` first.** `brief` holds the product name, pitch, what it is, what it does, who it's for, what's inside (`electronics`), design language, a reference product for the form factor (`looksLike`) and rough size. `prompts` may hold the hosts' edited prompts for each stage. `roll` holds the random ingredients. `favorites["2-concept"]` and `favorites["3-layout"]` are the chosen images (paths relative to the episode folder). Look at those images.
- **Never edit `episode.json`.** The dashboard owns it and will overwrite your changes. Put notes in the stage folder instead (for example `4-model/NOTES.md`).
- **Keep it a first pass.** This is a speedrun: aim for something credible and buildable by a two-person team, not production-ready. Write down open questions and shortcuts in the stage's `NOTES.md`.
- **Use these file names** so the dashboard picks them up.
- **Commit at the end of each stage** with a message like `003 stage 4: first-pass enclosure model`.

## Stage 4: 3D model (Solidcraft)

Use the Solidcraft MCP server in **headless** mode (`solidcraft-cli mcp`; if it isn't configured, run `claude mcp add solidcraft -- solidcraft-cli mcp`). Headless is faster than driving the desktop app, so don't use bridged mode. Save progress screenshots as you go (`4-model/progress-01.png`, `progress-02.png`, …) so the hosts can follow along on the dashboard.

1. From the brief and the two favorite images, decide the overall form, approximate dimensions in mm, and the main parts (shell, lid, buttons, windows, mounting for the board). Write that plan to `4-model/NOTES.md` before modeling, then start the shared **`fit.json`** (see "Stages 4 and 5 work together" below): where the board sits, its outline, holes and the features it lines up with. Run `python3 tools/fit/fitmd.py episodes/<slug>` to create `FIT.md` from it. If `5-electronics/SIZE.md` exists, the board must be at least the area it gives. If it isn't there yet, model the outer shell first and size the board when it arrives; if it still isn't there, leave generous room and set `"provisional": true` on the board in `fit.json`.
2. Build a simple parametric model: a few sketches and features, with named parameters for the key dimensions. Leave room inside for the electronics described in the brief. **Read the board's outline, posts and anything that lines up with it (windows, buttons, sensor holes) from `fit.json` through `tools/fit/fitlib.py`**, so a change there rebuilds into the model. Don't copy the numbers into the script. List your electronics stand-in bodies in `fit.json`'s `model.stand_ins`.
3. Save the Solidcraft design file in `4-model/`.
4. Take an isometric screenshot with Solidcraft's `screenshot` tool and save it as `4-model/iso.png`.
5. Export **STEP** (`model.step`) and **OBJ or STL** (`model.obj` / `model.stl`).
6. Convert the mesh to **`4-model/model.glb`** for the web viewer, for example with Python: `pip install trimesh` then `trimesh.load("model.obj").export("model.glb")`. Scale to meters if the viewer shows it huge (Solidcraft works in mm: multiply by 0.001). **Colours:** glTF's `baseColorFactor` (and `emissiveFactor`) are linear, not sRGB, so convert hex colours first (`c/12.92` if `c ≤ 0.04045`, else `((c+0.055)/1.055)^2.4`) and write the exact floats back after trimesh, which rounds them to 8 bits. Otherwise the model renders washed out. Start from `episodes/002-jordan-pilot-episode/4-model/make_glb.py`, which does both.

Images named `render-*.png` in `4-model/` are the hosts' hero renders (made in the console's stage 4 from your `iso.png` and the concept art). Leave them alone, and keep `iso.png` a clean three-quarter view of the whole product, since it's the shape reference for those renders.

Before every export, re-read `FIT.md` and take in any change requests from Stage 5. They're already in `fit.json`, so rebuild, re-export, then mark the request done.

## Stages 4 and 5 work together

The enclosure and the board are designed at the same time in two Claude Code windows, and each is allowed to change the other. Two files in the episode folder are the contract between them, and both read them before every step that depends on the other (`tools/fit/README.md` has the details):

- **`fit.json`: the numbers, the single source of truth.** Where the board sits in the enclosure (centre and axes), its outline, which faces carry parts, screw holes and rest posts, and everything the board lines up with (buttons, sensors, LEDs, windows, ports, antenna edge). Board positions are in board mm. Stage 4's `build_model.py` and Stage 5's `layout.py` both read it through `tools/fit/fitlib.py`, so a change made here rebuilds into both. Stage 4 writes it first; either stage may change it.
- **`FIT.md`: the request log and the rules.** Its "Fit" section is generated from `fit.json` (`python3 tools/fit/fitmd.py episodes/<slug>`; the kit's build and the fit check run it too), so never edit that section by hand. Below it:
  - **Rules:** the permission rules below.
  - **Requests:** one line each, for example `- [open] 5→4: board needs 54 × 31 (SIZE.md says 1600 mm²); posts to (±21, −7.25)`. The other stage marks it `[done]` once it's in its model or board, or `[asked hosts]`. A request names what changed in `fit.json`, since the change itself is already there.
- **The fit check** (`python3 tools/fit/fitcheck.py episodes/<slug>`) puts the real routed board, parts and all, into the Stage 4 model where `fit.json` says, and checks every enclosure body against it. It writes `5-electronics/fitcheck.md` and `fitcheck.png`, and fails on any overlap.

What each stage may change without asking:

- **Stage 5** may change the board's size, shape, posts and the inside positions of parts and connectors. It writes the change into `fit.json` and adds a request in `FIT.md` so Stage 4 follows.
- **Stage 4** may move posts (in `fit.json`, with a request so Stage 5 follows), ribs and internal features, and may grow the enclosure by up to about 10 % in any direction to make room, keeping the concept's look.
- **Ask the hosts first** (stop and say so in the chat) before anything visible changes: the outer size beyond 10 %, the shape, or where buttons, windows, eyes, ports or speakers sit on the outside.

Edit `fit.json` and `FIT.md` with small, targeted edits and re-read them just before writing, since the other window may have changed them. Neither stage calls itself finished while a request to it is still open.

## Stage 5: Electronics (KiCad)

The deliverable is a **routed 2-layer PCB** that fits the Stage 4 enclosure, plus its schematic and BOM. A board on screen is the point of this stage, so don't stop at a schematic. Pick the simplest design that achieves the brief, using the rolled board (ESP32, Raspberry Pi, Pi Pico or nRF52840) as a module or dev board where sensible. Prefer common, easy-to-source parts (JLCPCB/LCSC basic parts where possible).

**Start early, in a second Claude Code window.** Steps 1–2 need only the brief, so run them while Stage 4 models. The schematic build writes `5-electronics/SIZE.md` with the board area the parts need. If Stage 4's board is smaller, change it in `fit.json` and post a request in `FIT.md`. Placement and routing (steps 3–4) read `fit.json`. Whenever placement or routing needs a bigger board, moved posts or a different connector position, change `fit.json` and post a request rather than squeezing.

**Use the shared kit in `tools/kicad/`**. Don't write new generator or routing scripts (read `tools/kicad/README.md` once). An episode only writes two files, `5-electronics/src/design.py` (parts and nets) and `5-electronics/src/layout.py` (outline and placement), and the kit does the schematic, ERC, netlist check, placement, Freerouting, DRC fix-ups, silkscreen tidy, BOM, renders and GLB. Episode 001's board is the worked example in `tools/kicad/example/`, and `tools/kicad/parts.py` holds custom symbols already drawn. If the kit is missing something, improve the kit (and note it in its README) rather than working around it in the episode.

1. Write `5-electronics/NOTES.md`: block diagram in words, part choices and why, power budget, how it fits the enclosure, and open questions. Read `FIT.md` (and `fit.json`) for the board outline, post positions and where buttons, sensors and windows sit.
2. `tools/kicad/new_board.sh episodes/<slug> <project-name> "<Product Name>"` to start `src/`. Fill in `design.py`, copying proven blocks (the table in `tools/kicad/README.md` lists them; episodes 001 and 002 cover the ESP32-C3 and ESP32-S3 modules, battery boost, USB LDO, amp, mic, PIR, LEDs and fan driver). Then run `tools/kicad/build.sh episodes/<slug> schematic` and fix until ERC and the netlist check are clean. Commit (`NNN stage 5: schematic`) so the hosts see it.
3. Fill in `layout.py`: the outline, holes and fixed parts under the enclosure's features come from `fit.json` (the template already reads it), then preferred spots for the rest. Then `tools/kicad/build.sh episodes/<slug> place`. Look at `board.png` and `output/placement.txt`, and adjust spots until the placement is sensible: each IC's decoupling next to its pins, the antenna on an edge with a copper keep-out, short power loops.
4. `tools/kicad/build.sh episodes/<slug>` for the full run: routing, DRC, `board.png`, `board-bottom.png`, `board-iso.png`, `board.glb`. Aim for **DRC 0 and 0 unconnected**. If Freerouting leaves nets unrouted, loosen the placement around them and run again; anything still open goes in NOTES.md. Run it in the background and keep writing NOTES.md while it routes.
5. **Run the fit check:** `python3 tools/fit/fitcheck.py episodes/<slug>` (a few minutes, so run it in the background). It must report **PASS** (no overlaps). If it doesn't, move the part or change `fit.json` and post a request for Stage 4, then rebuild and check again. Stage 4 must have saved its latest `model.solidcraft`.
6. Record the ERC, DRC and fit-check results in NOTES.md and commit. **Stage 5 is finished when DRC is 0 violations and 0 unconnected *and* the fit check passes.**

Outputs the dashboard expects in `5-electronics/`: `<name>.kicad_pro/.kicad_sch/.kicad_pcb`, **`bom.csv`** (`Ref,Qty,Value,Description,Footprint,MPN`), `erc.rpt`, `drc.rpt`, `schematic.png`, `board.png`, `board.glb`, `fitcheck.md`, `fitcheck.png`. If `kicad-cli` or Freerouting isn't installed, say so in NOTES.md rather than faking output. If `tools/kicad/selftest.sh place` has never been run on this computer, run it first: it checks the kit against episode 001's board in a scratch folder.

The dashboard shows the schematic and board live in the browser (KiCanvas), the 3D board, and the BOM table.

## Stage 6: Showcase page

Build **`6-showcase/index.html`**: a product page that makes the idea feel real. Every episode's page uses the shared series look, so the gallery reads as one show:

- **Start from `kit/showcase/template.html`** (read `kit/showcase/README.md` first). Copy it, then replace the words, pictures and the three accent colours (taken from the product itself). Keep the fonts, the section order, the run strip, the footer and the class names from `kit/showcase.css`.
- **Spend the creativity in the free slot:** one interactive or explanatory moment in the product's own style (a demo, a timeline, a diagram). Keep its styles scoped to its own class names.
- **Keep `<ps-series-bar>` as the first thing in `<body>`.** It's the strip that links back to the gallery and to the episodes either side; the public site build fills it in.
- Use only relative paths: the episode's own files (`../2-concept/<file>.png`, `../4-model/model.glb`, `../5-electronics/board.glb`, `../5-electronics/bom.csv`) and the shared kit (`../../../kit/`). Copy anything else it needs into `6-showcase/`.
- Load `<model-viewer>` from `https://cdn.jsdelivr.net/npm/@google/model-viewer@4.4.0/dist/model-viewer.min.js`. Big models (the board GLB) load on a button press (`data-load-model`).
- **Hero image:** if `episode.json` has `favorites.render` (the hero render the hosts picked in stage 4), use it as the hero image, linked as `../4-model/<file>`, with a caption saying it's an AI render of the CAD model. The concept art then moves down to "who it's for" or "how we got here". With no render, the favourite concept art is the hero.
- Content: product name and pitch, the hero image, who it's for and the moment it's used, the 3D model, what's inside (from the BOM and notes), how we got here, and an honest "what we still don't know" list.
- Keep the footer's licence line, with the episode's number and both hosts' names: the designs are open (see `LICENSE`), so the page says so and asks for credit.
- It must work on phones and in both light and dark viewing. No trackers and no forms of its own: the site build adds the newsletter signup (Beehiiv) above the footer of every page, so don't add one yourself.
- **Don't add a downloads section.** The site build adds "Build on it" near the bottom of every page: links to the GitHub folder, the 3D files, each KiCad board (with a zip), firmware when there is some, and a prompt that hands the project to any AI agent. It reads them from the folders, so keep the standard file names (`4-model/model.step`, `model.solidcraft`, `build_model.py`, the `.kicad_pro` in `5-electronics/` or `5-electronics/<device>/`, `bom.csv`, `7-firmware/platformio.ini`) and keep each stage's `NOTES.md` current, since the prompt sends agents to them.

## Products with several devices

Some products are two or more separate devices, each with its own enclosure and board: a sensor and a wearable, a transmitter and a receiver, a remote and the thing it controls. The hosts list them as **devices** in Stage 1 (`brief.units` in `episode.json`: `key`, `name`, `does`, `electronics`, `size`; the `key` names the board's folder). With none listed, the product is one piece and nothing here applies. Episode 003 (Baby Monitor Monitor: a sensor and a wristband) is the worked example.

```
episodes/<slug>/
  SYSTEM.md                 how the devices work together (yours, write it first)
  fit.json  FIT.md          one entry per board under "boards" (tools/fit/README.md)
  4-model/                  ONE Solidcraft design holding every device; iso.png shows them all
  5-electronics/<key>/      one kit project per board: src/design.py, src/layout.py, and its outputs
  5-electronics/NOTES.md    notes that cover both boards (optional)
```

- **`SYSTEM.md` first.** Before modelling or drawing a schematic, write `SYSTEM.md` in the episode (or revision) folder: what each device does, how they talk (radio and protocol, or cable and connector), pairing, what they share (microcontroller family, battery, charger, connectors) and each one's power budget. Either stage may update it, with a request in `FIT.md` when it changes the other side.
- **Stage 4:** one design in `4-model/` with a set of bodies per device, laid out side by side, and one `iso.png`, `model.step` and `model.glb` covering them all. `fit.json` gets a `boards` section with one entry per board, named like the board folders; `build_model.py` reads each with `load_fit(__file__, board="<key>")`.
- **Stage 5:** one kit project per board, in `5-electronics/<key>/`: `tools/kicad/new_board.sh episodes/<slug>/5-electronics/<key> <project> "<Product> <Device>"`, `tools/kicad/build.sh episodes/<slug>/5-electronics/<key>`. Give each project its own name (episode 003: `bmm-sensor`, `bmm-receiver`). `layout.py` picks its board from the path. The fit check takes one board (`python3 tools/fit/fitcheck.py episodes/<slug>/5-electronics/<key>`) or all of them (the episode folder).
- **One window per stage, as before.** The Stage 5 window does the boards one after another (or the next schematic while one routes).
- **Same family on purpose.** Use one microcontroller family across the boards where it makes sense, so one toolchain and one radio stack cover them, and give the enclosures a shared design language, so the set reads as one product.
- **Stage 5 is finished when every board is DRC 0 / 0 unconnected and passes its fit check.**
- **Hero render:** one group shot of all the devices (from the one `iso.png`), in `4-model/` as usual.
- **Showcase:** one page. The model viewer shows every device; then each device gets its own board and parts list (`../5-electronics/<key>/board.glb`, `bom.csv`); the free slot shows how the devices work together (from `SYSTEM.md`).
- **Revisions** copy all of it, including `SYSTEM.md`. Firmware is one PlatformIO project per device, in `7-firmware/<key>/`, sharing a protocol header where the devices talk to each other.

## Revisions (Rev B and later)

Products the hosts mark "keep building" go on the shelf and come back for revisions. The episode is **Rev A** and stays exactly as aired: never change an episode folder for a revision. Each later revision is its own folder, made by the console's **Start Rev B** button:

```
products/<product>/rev-b/
  rev.json        # owned by the console: goals, guest, the hosts' feedback per track, done tracks. Never edit it.
  REV.md          # yours: changelog (what changed and why), results, still open
  fit.json  FIT.md
  4-model/        # copied from the previous revision: change it, don't start over (render-*.png are the hosts' hero renders for this revision)
  5-electronics/  # copied from the previous revision: change it, don't start over
  6-showcase/     # this revision's page
  7-firmware/     # PlatformIO project (from Rev B on)
  SYSTEM.md       # products with several devices: boards in 5-electronics/<device>/, firmware in 7-firmware/<device>/
```

The hosts write feedback per track in the console, which turns it into a prompt that names the folder. For every track:

- **Work only in that revision folder.** Read `rev.json` (goals and the feedback for every track, since they affect each other) and the previous revision's notes first.
- **Change, don't redo.** Edit the copied `build_model.py`, `design.py`, `layout.py` and `fit.json`. If the revision predates `fit.json` or the kit's `src/`, port it first (episode 001's board is `tools/kicad/example/`), then make the changes.
- **Same tools and outputs as Rev A:** Solidcraft in headless mode for the enclosure (follow the Stage 4 steps for screenshots, `model.solidcraft`, exports and the GLB's colours) and KiCad through `tools/kicad/` for the board (the Stage 5 steps).
- **Same contract between enclosure and board** as in "Stages 4 and 5 work together", same finish line for electronics: DRC 0 / 0 unconnected and a passing fit check.
- **Log it in `REV.md`** as you go: one changelog line per change, with the reason (usually a host comment or an open question it answers). Move answered questions out of "Still open".
- **Commit** with a message like `gamer-guardian rev B: radar presence sensor, head 3 mm narrower`.

Firmware (track "code", usually done off air in VS Code with PlatformIO, after the CAD and electronics changes): a PlatformIO project in `7-firmware/` for the revision's board. Generate `include/pins.h` from `5-electronics/src/design.py` so code and board can't disagree, stub what needs real hardware, and make `pio run` build cleanly. Record flash and RAM use, libraries and anything the hardware should change in `7-firmware/NOTES.md`, and post hardware changes as requests in `FIT.md`.

Showcase (track "showcase"): build `6-showcase/index.html` from `kit/showcase/template.html` (the kit is `../../../../kit/` from there) for this revision, with the revision's hero render as the hero image when `rev.json` has `hero` (a path in this revision folder, linked as `../<hero>`; caption it as an AI render of the Rev CAD model), with a revision timeline (Rev A from its episode, then each revision's headline changes from `REV.md`). Rev A's images can be linked from `../../../../episodes/<slug>/`. The public site links the product's gallery card to its latest revision page. The site build also gives every version's page (the episode included) a Rev A · Rev B switcher in its series bar, plus a link to the newest revision on older ones, so episode pages never need editing.

## Publishing

Pushing to `main` rebuilds the public site (`scripts/build-site.mjs`, `.github/workflows/site.yml`): a gallery of all episodes plus each episode's showcase page and assets.
