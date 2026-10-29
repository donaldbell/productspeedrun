# Showcase pages: the series look

Every episode's showcase page shares one frame, so the gallery reads as a series, while each product keeps its own colour and its own interactive moment.

- `kit/showcase.css`: type, layout, spacing and components. Pages link it as `../../../kit/showcase.css`.
- `kit/series-bar.js`: the dark Product Speedrun strip at the top of every page, with the link back to the gallery and to the previous and next episodes. The public site build fills in its details.
- `kit/showcase.js`: the BOM table (read from `bom.csv`), load-on-click 3D viewers, view buttons, and the keep-or-shelve verdict (read from `episode.json`).
- `kit/showcase/template.html`: the page to copy, filled in with episode 002 as the worked example.

## What a page may change

- **The accent:** three colours (`--accent`, `--accent-ink`, `--accent-soft`), with dark-mode versions of the last two, taken from the product itself. These are the only colours a page sets.
- **The words and pictures**, of course.
- **The free slot** (`.ps-free`, the "A nudge you feel" section in the template): one interactive or explanatory moment in the product's own style, such as a demo, a timeline or a diagram. Its styles stay scoped to its own class names.

Everything else stays as the template has it: the fonts, the section order, the run strip, the footer, and the class names.

## Section order

1. `<ps-series-bar>`: always first.
2. Hero (`.ps-hero`): the roll, name, pitch, a short lede, four facts, the hero concept art.
3. Run strip (`.ps-run`): the seven stages with thumbnails, linked to their sections. Stage 7 shows the verdict.
4. Who it's for (`.ps-person` × 2, `.ps-moment`): the user, the buyer if different, and the moment it's used.
5. The free slot (`.ps-section.tint` + `.ps-free`).
6. The 3D model (`.ps-viewer` + `.ps-views` + `.ps-callouts`).
7. What's inside (`.ps-stats`, the board viewer, `.ps-parts`, `details.ps-bom`, `.ps-files`).
8. How we got here (`.ps-trail`): concept, layout, model, electronics.
9. What we still don't know (`.ps-questions`).
10. Footer (`.ps-foot`): "a concept, not for sale", All episodes, Files on GitHub.

Leave a section out if the episode has nothing for it (no board, for example) rather than padding it.
