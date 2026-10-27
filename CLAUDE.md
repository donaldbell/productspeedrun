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

1. From the brief and the two favorite images, decide the overall form, approximate dimensions in mm, and the main parts (shell, lid, buttons, windows, mounting for the board). Write that plan to `4-model/NOTES.md` before modeling.
2. Build a simple parametric model: a few sketches and features, with named parameters for the key dimensions. Leave room inside for the electronics described in the brief.
3. Save the Solidcraft design file in `4-model/`.
4. Take an isometric screenshot with Solidcraft's `screenshot` tool and save it as `4-model/iso.png`.
5. Export **STEP** (`model.step`) and **OBJ or STL** (`model.obj` / `model.stl`).
6. Convert the mesh to **`4-model/model.glb`** for the web viewer, for example with Python: `pip install trimesh` then `trimesh.load("model.obj").export("model.glb")`. Scale to meters if the viewer shows it huge (Solidcraft works in mm: multiply by 0.001).

## Stage 5: Electronics (KiCad)

Pick the simplest design that achieves the brief, using the rolled board (ESP32, Raspberry Pi, Pi Pico or nRF52840) as a module or dev board where sensible. Prefer common, easy-to-source parts.

1. Write `5-electronics/NOTES.md`: block diagram in words, part choices and why, power budget, and open questions.
2. Create a KiCad project in `5-electronics/`: `<name>.kicad_pro`, `<name>.kicad_sch` (and sub-sheets if needed), `<name>.kicad_pcb`. Use standard KiCad library symbols and footprints. The schematic should pass ERC; route the board if practical, and note unrouted nets in NOTES.md. Size the board to fit inside the Stage 4 enclosure.
3. Write **`5-electronics/bom.csv`** with a header row. Use these columns: `Ref,Qty,Value,Description,Footprint,MPN`.
4. If `kicad-cli` is available: export a 3D board model to **`5-electronics/board.glb`** (or export STEP/VRML and convert with trimesh), plus renders or SVG/PNG plots of the schematic and board (`schematic.png`, `board.png`). Run ERC (`kicad-cli sch erc`) and DRC (`kicad-cli pcb drc`) and save the reports. If kicad-cli isn't installed, say so in NOTES.md rather than faking output.

The dashboard shows the schematic and board live in the browser (KiCanvas), the 3D board, and the BOM table.

## Stage 6: Showcase page

Build **`6-showcase/index.html`**: a single, self-contained, attractive product page that makes the idea feel real. It is published on the public site, so:

- Use only relative paths to the episode's own files, for example `../2-concept/<file>.png`, `../4-model/model.glb`, `../5-electronics/board.glb`. Copy anything else it needs into `6-showcase/`.
- Include: product name and pitch, the hero concept art, who it's for and the moment it's used, an interactive 3D view of the model (and the board if there is one) using `<model-viewer>` from `https://cdn.jsdelivr.net/npm/@google/model-viewer@4.4.0/dist/model-viewer.min.js`, a "what's inside" section drawn from the BOM and notes, and an honest "what's next" list of open questions.
- Give it its own visual identity that fits the product's vibe from the roll. It must work on phones and in both light and dark viewing.
- No trackers, no external forms.

## Publishing

Pushing to `main` rebuilds the public site (`scripts/build-site.mjs`, `.github/workflows/site.yml`): a gallery of all episodes plus each episode's showcase page and assets.
