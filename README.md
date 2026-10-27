# Product Speedrun

A show about racing a random product idea from brainstorm to a showcase-ready concept. Each episode runs seven stages, and this repo holds the show console, every episode's work, and the public site.

1. **Roll & brief:** roll ingredients with the [Random Project Generator](https://donaldbell.github.io/random-project-generator/show.html) and write the brief.
2. **Concept sketches:** AI concept art of the product in use.
3. **Isometric layout:** an AI isometric drawing of how it could be put together.
4. **3D model:** Claude Code + [Solidcraft](https://solidcraft.pro/) build a first-pass model.
5. **Electronics:** Claude Code designs a schematic, KiCad board and BOM.
6. **Showcase:** Claude Code builds an interactive product page.
7. **Keep or shelve:** the hosts decide.

## Run the show console

Needs Node 20 or newer. No packages to install.

```sh
npm start
```

Then open http://localhost:4321 in Chrome and share that window in Riverside.

### Controls

| Key | Action |
|---|---|
| ← → or 1–7 | Change stage |
| N | Split: mark the stage done and move to the next one |
| T (or click the clock) | Start or pause the run timer |
| E | Episodes: switch or start a new one |
| , | Settings: image generators, room for your faces, sound |
| F | Full screen |
| Click an image | Show it full screen (← → to browse, F to favorite, Esc to close) |

In stage 1, click into the roller and use its own keys (Space to roll, 1–9 to cast off, Enter to lock in). Locking in sends the roll to the brief.

Drag files from anywhere onto stages 2–6 to add them to that stage's folder.

### Image generation

Stages 2 and 3 can generate images in the console. Pollinations works with no setup (free, best effort). For better results and the ability to refine from a reference image, copy `.env.example` to `.env`, add a Gemini or OpenAI API key, and restart `npm start`. Keys stay on your computer: the browser never sees them. Each generated image is saved next to a `.prompt.txt` recording the prompt.

### Stages 4–6 with Claude Code

Open Claude Code in this folder. Each of those stages has a **Copy prompt** button. Paste it into Claude Code, which follows `CLAUDE.md` and writes into the episode's folder. The console watches the folder, so the model, schematic, board, BOM and showcase page appear on screen as they're saved.

## Episode folders

```
episodes/001-plant-whisperer/
  episode.json     roll, brief, favorites, timer, decision (written by the console)
  2-concept/       3-layout/       4-model/       5-electronics/       6-showcase/
```

## Public site

Every push to `main` builds a gallery of all episodes with links to each showcase page, and publishes it to GitHub Pages. In the repo's **Settings → Pages**, set the source to **GitHub Actions** once. To preview locally: `npm run build:site`, then open `_site/index.html`.
