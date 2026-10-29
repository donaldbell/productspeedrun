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

1. From the brief and the two favorite images, decide the overall form, approximate dimensions in mm, and the main parts (shell, lid, buttons, windows, mounting for the board). Write that plan to `4-model/NOTES.md` before modeling, and start the shared **`FIT.md`** (see "Stages 4 and 5 work together" below) with the board outline, posts and feature positions. If `5-electronics/SIZE.md` exists, the board must be at least the area it gives. If it isn't there yet, model the outer shell first and size the board when it arrives; if it still isn't there, leave generous room and mark the board size provisional in `FIT.md`.
2. Build a simple parametric model: a few sketches and features, with named parameters for the key dimensions. Leave room inside for the electronics described in the brief.
3. Save the Solidcraft design file in `4-model/`.
4. Take an isometric screenshot with Solidcraft's `screenshot` tool and save it as `4-model/iso.png`.
5. Export **STEP** (`model.step`) and **OBJ or STL** (`model.obj` / `model.stl`).
6. Convert the mesh to **`4-model/model.glb`** for the web viewer, for example with Python: `pip install trimesh` then `trimesh.load("model.obj").export("model.glb")`. Scale to meters if the viewer shows it huge (Solidcraft works in mm: multiply by 0.001). **Colours:** glTF's `baseColorFactor` (and `emissiveFactor`) are linear, not sRGB, so convert hex colours first (`c/12.92` if `c ≤ 0.04045`, else `((c+0.055)/1.055)^2.4`) and write the exact floats back after trimesh, which rounds them to 8 bits. Otherwise the model renders washed out. Start from `episodes/002-jordan-pilot-episode/4-model/make_glb.py`, which does both.

Before every export, re-read `FIT.md` and take in any change requests from Stage 5: rebuild from the parameters, re-export, then mark the request done.

## Stages 4 and 5 work together

The enclosure and the board are designed at the same time in two Claude Code windows, and each is allowed to change the other. **`episodes/<slug>/FIT.md`** is the contract between them, and both read it before every step that depends on the other:

- **Fit:** board outline (width × height, corner radius), which face carries parts, mounting posts, and the position of everything the board lines up with (buttons, sensors, LEDs, windows, connectors, antenna edge), in the enclosure's coordinates with the origin at its centre. Stage 4 writes it first; either stage may update it.
- **Requests:** a log at the bottom, one line each: `- [open] 5→4: board needs 54 × 31 (SIZE.md says 1600 mm²); posts to (±21, −7.25)`. The other stage marks it `[done]` once it's in its model or board, or `[asked hosts]`.

What each stage may change without asking:

- **Stage 5** may change the board's size, shape, posts and the inside positions of parts and connectors. It writes the change into Fit and adds a request so Stage 4 follows.
- **Stage 4** may move posts, ribs and internal features, and may grow the enclosure by up to about 10 % in any direction to make room, keeping the concept's look.
- **Ask the hosts first** (stop and say so in the chat) before anything visible changes: the outer size beyond 10 %, the shape, or where buttons, windows, eyes, ports or speakers sit on the outside.

Edit `FIT.md` with small, targeted edits and re-read it just before writing, since the other window may have changed it. Neither stage calls itself finished while a request to it is still open.

## Stage 5: Electronics (KiCad)

The deliverable is a **routed 2-layer PCB** that fits the Stage 4 enclosure, plus its schematic and BOM. A board on screen is the point of this stage, so don't stop at a schematic. Pick the simplest design that achieves the brief, using the rolled board (ESP32, Raspberry Pi, Pi Pico or nRF52840) as a module or dev board where sensible. Prefer common, easy-to-source parts (JLCPCB/LCSC basic parts where possible).

**Start early, in a second Claude Code window.** Steps 1–2 need only the brief, so run them while Stage 4 models. The schematic build writes `5-electronics/SIZE.md` with the board area the parts need; post a request in `FIT.md` if Stage 4's board is smaller. Placement and routing (steps 3–4) start from `FIT.md`, and whenever placement or routing needs a bigger board, moved posts or a different connector position, change `FIT.md` and post a request rather than squeezing.

**Use the shared kit in `tools/kicad/`**. Don't write new generator or routing scripts (read `tools/kicad/README.md` once). An episode only writes two files, `5-electronics/src/design.py` (parts and nets) and `5-electronics/src/layout.py` (outline and placement), and the kit does the schematic, ERC, netlist check, placement, Freerouting, DRC fix-ups, silkscreen tidy, BOM, renders and GLB. Episode 001's board is the worked example in `tools/kicad/example/`, and `tools/kicad/parts.py` holds custom symbols already drawn. If the kit is missing something, improve the kit (and note it in its README) rather than working around it in the episode.

1. Write `5-electronics/NOTES.md`: block diagram in words, part choices and why, power budget, how it fits the enclosure, and open questions. Read `FIT.md` for the board outline, post positions and where buttons, sensors and windows sit.
2. `tools/kicad/new_board.sh episodes/<slug> <project-name> "<Product Name>"` to start `src/`. Fill in `design.py`, copying proven blocks (the table in `tools/kicad/README.md` lists them; episodes 001 and 002 cover the ESP32-C3 and ESP32-S3 modules, battery boost, USB LDO, amp, mic, PIR, LEDs and fan driver). Then run `tools/kicad/build.sh episodes/<slug> schematic` and fix until ERC and the netlist check are clean. Commit (`NNN stage 5: schematic`) so the hosts see it.
3. Fill in `layout.py` (outline, holes, fixed parts under the enclosure's features, preferred spots for the rest), then `tools/kicad/build.sh episodes/<slug> place`. Look at `board.png` and `output/placement.txt`, and adjust spots until the placement is sensible: each IC's decoupling next to its pins, the antenna on an edge with a copper keep-out, short power loops.
4. `tools/kicad/build.sh episodes/<slug>` for the full run: routing, DRC, `board.png`, `board-bottom.png`, `board-iso.png`, `board.glb`. Aim for **DRC 0 and 0 unconnected**. If Freerouting leaves nets unrouted, loosen the placement around them and run again; anything still open goes in NOTES.md. Run it in the background and keep writing NOTES.md while it routes.
5. Record the ERC/DRC results in NOTES.md and commit.

Outputs the dashboard expects in `5-electronics/`: `<name>.kicad_pro/.kicad_sch/.kicad_pcb`, **`bom.csv`** (`Ref,Qty,Value,Description,Footprint,MPN`), `erc.rpt`, `drc.rpt`, `schematic.png`, `board.png`, `board.glb`. If `kicad-cli` or Freerouting isn't installed, say so in NOTES.md rather than faking output. If `tools/kicad/selftest.sh place` has never been run on this computer, run it first: it checks the kit against episode 001's board in a scratch folder.

The dashboard shows the schematic and board live in the browser (KiCanvas), the 3D board, and the BOM table.

## Stage 6: Showcase page

Build **`6-showcase/index.html`**: a product page that makes the idea feel real. Every episode's page uses the shared series look, so the gallery reads as one show:

- **Start from `kit/showcase/template.html`** (read `kit/showcase/README.md` first). Copy it, then replace the words, pictures and the three accent colours (taken from the product itself). Keep the fonts, the section order, the run strip, the footer and the class names from `kit/showcase.css`.
- **Spend the creativity in the free slot:** one interactive or explanatory moment in the product's own style (a demo, a timeline, a diagram). Keep its styles scoped to its own class names.
- **Keep `<ps-series-bar>` as the first thing in `<body>`.** It's the strip that links back to the gallery and to the episodes either side; the public site build fills it in.
- Use only relative paths: the episode's own files (`../2-concept/<file>.png`, `../4-model/model.glb`, `../5-electronics/board.glb`, `../5-electronics/bom.csv`) and the shared kit (`../../../kit/`). Copy anything else it needs into `6-showcase/`.
- Load `<model-viewer>` from `https://cdn.jsdelivr.net/npm/@google/model-viewer@4.4.0/dist/model-viewer.min.js`. Big models (the board GLB) load on a button press (`data-load-model`).
- Content: product name and pitch, the hero concept art, who it's for and the moment it's used, the 3D model, what's inside (from the BOM and notes), how we got here, and an honest "what we still don't know" list.
- It must work on phones and in both light and dark viewing. No trackers, no external forms.

## Publishing

Pushing to `main` rebuilds the public site (`scripts/build-site.mjs`, `.github/workflows/site.yml`): a gallery of all episodes plus each episode's showcase page and assets.
