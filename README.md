# Product Speedrun

**Product Speedrun** is a show about racing a randomly rolled product idea to a showcase-ready concept: an enclosure design, a circuit board and a product page. Everything the show designs is open, and this repository holds it.

**See the products:** https://donaldbell.github.io/productspeedrun/

Every product here is a **design proposal**, not something you can buy. Nothing has been manufactured, and each page lists what we still don't know.

## What's here

```
episodes/<NNN-slug>/        one folder per episode (Rev A, as aired)
  2-concept/, 3-layout/     concept art and control drawings
  4-model/                  the enclosure: model.step, model.stl, model.glb, notes
  5-electronics/            the circuit board: KiCad project, bom.csv, schematic and board renders, notes
  6-showcase/               the product page
products/<product>/rev-b/   later revisions of products we kept building, including firmware (7-firmware/)
tools/kicad/footprints/     custom footprints the KiCad projects use
tools/kicad/models/         3D models of parts the KiCad projects use
kit/                        the shared look of the product pages
```

## Using the designs

- **Enclosures:** open `4-model/model.step` in any CAD program, or print from `model.stl`. `build_model.py` and `model.solidcraft` are kept as a record of how the model was made; edit the STEP file.
- **Circuit boards:** open the `.kicad_pro` in [KiCad](https://www.kicad.org/) (the version each board was saved with is on its page). Keep the repository's folder layout so the custom footprints and 3D models in `tools/kicad/` are found. `src/design.py` and `src/layout.py` record the parts, nets and placement the board was generated from; edit the KiCad files.
- **Firmware:** PlatformIO projects in `products/<product>/rev-*/7-firmware/`.
- Each product page has a **Build on it** section with direct downloads and a prompt that hands the project to an AI coding agent.

## Licence and credit

Hardware is under CERN-OHL-P v2, writing and images under CC BY 4.0, and code under MIT. Details are in [LICENSE](LICENSE), the full texts in [LICENSES/](LICENSES/), and who made each episode in [CREDITS.md](CREDITS.md).

Credit line for reuse: *Based on Product Speedrun episode NNN by Donald Bell and &lt;guest&gt;, https://donaldbell.github.io/productspeedrun/*

The name "Product Speedrun" and its logo aren't covered by these licences.
