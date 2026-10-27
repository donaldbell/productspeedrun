// Builds the public site into _site/: an episode gallery plus each episode's files
// (its showcase page in 6-showcase/ links to images and models with relative paths).
// Run: node scripts/build-site.mjs
import { readdir, readFile, writeFile, mkdir, cp, rm, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const EP = path.join(ROOT, "episodes");
const OUT = path.join(ROOT, "_site");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const IMG = /\.(png|jpe?g|webp|gif)$/i;
const enc = (rel) => rel.split("/").map(encodeURIComponent).join("/");


await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

const episodes = [];
if (existsSync(EP)) {
  for (const d of await readdir(EP, { withFileTypes: true })) {
    if (!d.isDirectory()) continue;
    const dir = path.join(EP, d.name);
    let ep; try { ep = JSON.parse(await readFile(path.join(dir, "episode.json"), "utf8")); } catch { continue; }
    await cp(dir, path.join(OUT, "episodes", d.name), { recursive: true, filter: (src) => !/[\\/]\.(trash|git)([\\/]|$)/.test(src) });
    let cover = ep.favorites?.["2-concept"] || ep.favorites?.["3-layout"];
    if (!cover) for (const sd of ["2-concept", "3-layout", "4-model"]) {
      try { const f = (await readdir(path.join(dir, sd))).find((n) => IMG.test(n)); if (f) { cover = `${sd}/${f}`; break; } } catch {}
    }
    const showcase = existsSync(path.join(dir, "6-showcase", "index.html"));
    episodes.push({ slug: d.name, ep, cover, showcase });
  }
}
episodes.sort((a, b) => (b.ep.number || 0) - (a.ep.number || 0));

const cards = episodes.map(({ slug, ep, cover, showcase }) => {
  const href = showcase ? `episodes/${enc(slug)}/6-showcase/` : cover ? `episodes/${enc(slug)}/${enc(cover)}` : null;
  const tag = ep.decision === "keep" ? '<span class="tag keep">Keep building</span>' : ep.decision === "shelve" ? '<span class="tag shelve">Shelved</span>' : `<span class="tag">In progress · stage ${esc(ep.stage || 1)}</span>`;
  const roll = (ep.roll || []).map((r) => `<li>${esc(r.label)}</li>`).join("");
  return `<article class="card">
  ${href ? `<a class="cover" href="${href}">` : '<div class="cover">'}${cover ? `<img src="episodes/${enc(slug)}/${enc(cover)}" alt="" loading="lazy">` : '<div class="blank">No art yet</div>'}${href ? "</a>" : "</div>"}
  <div class="body">
    <div class="meta"><span>#${esc(String(ep.number || "").padStart(3, "0"))}</span>${tag}</div>
    <h2>${href ? `<a href="${href}">` : ""}${esc(ep.brief?.name || ep.title)}${href ? "</a>" : ""}</h2>
    ${ep.brief?.pitch ? `<p>${esc(ep.brief.pitch)}</p>` : ""}
    ${roll ? `<ul class="roll">${roll}</ul>` : ""}
  </div>
</article>`;
}).join("\n");

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Product Speedrun</title>
<meta name="description" content="Random product ideas, taken from brainstorm to concept art, 3D model, circuit board and showcase page as fast as we can.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root { color-scheme: dark; --bg: #0C0F14; --panel: #141922; --line: #283142; --ink: #F3EFE6; --muted: #8C96A8; --gold: #F6C14B; --run: #63E39A;
  --display: "Bricolage Grotesque", "Avenir Next", system-ui, sans-serif; --mono: "JetBrains Mono", ui-monospace, Menlo, monospace; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.5 var(--mono); }
.wrap { max-width: 1200px; margin: 0 auto; padding-inline: 16px; padding-block: 48px 72px; }
header { display: grid; gap: 12px; margin-bottom: 40px; }
h1 { margin: 0; font-family: var(--display); font-weight: 800; font-size: clamp(44px, 9vw, 104px); line-height: .9; letter-spacing: -0.03em; text-wrap: balance; }
h1 span { color: var(--run); }
.lede { margin: 0; color: var(--muted); max-width: 60ch; font-size: 16px; }
.steps { display: flex; flex-wrap: wrap; gap: 6px 14px; padding: 0; margin: 8px 0 0; list-style: none; color: var(--muted); font-size: 13px; letter-spacing: .06em; }
.steps li::before { content: counter(s) " "; counter-increment: s; color: var(--gold); }
.steps { counter-reset: s; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 16px; overflow: hidden; display: grid; grid-template-rows: auto 1fr; min-width: 0; }
.cover { display: block; aspect-ratio: 16/10; background: #F4F1EA; }
.cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
.blank { height: 100%; display: grid; place-items: center; color: #6b6b6b; background: #1A2030; }
.body { padding: 16px 18px 20px; display: grid; gap: 10px; align-content: start; min-width: 0; }
.meta { display: flex; flex-wrap: wrap; gap: 6px 12px; align-items: center; font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums; }
.tag { border: 1px solid var(--line); border-radius: 999px; padding: 1px 9px; text-transform: uppercase; letter-spacing: .08em; font-size: 11px; }
.tag.keep { color: var(--run); border-color: var(--run); }
.tag.shelve { color: var(--gold); border-color: var(--gold); }
h2 { margin: 0; font-family: var(--display); font-size: 26px; line-height: 1.1; text-wrap: balance; }
h2 a { color: inherit; text-decoration: none; } h2 a:hover { text-decoration: underline; }
.body p { margin: 0; color: var(--muted); }
.roll { display: flex; flex-wrap: wrap; gap: 6px; margin: 0; padding: 0; list-style: none; }
.roll li { font-size: 12px; border: 1px solid var(--line); border-radius: 999px; padding: 2px 9px; }
.none { color: var(--muted); border: 1px dashed var(--line); border-radius: 16px; padding: 32px; }
a:focus-visible { outline: 3px solid var(--gold); outline-offset: 2px; }
footer { margin-top: 48px; color: var(--muted); font-size: 13px; }
footer a { color: var(--ink); }
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Product <span>Speedrun</span></h1>
  <p class="lede">We roll random ingredients, then race a product idea from brainstorm to concept art, a 3D model, a circuit board and a showcase page. Some we keep building. Some we shelve.</p>
  <ol class="steps"><li>Roll &amp; brief</li><li>Concept sketches</li><li>Isometric layout</li><li>3D model</li><li>Electronics</li><li>Showcase</li><li>Keep or shelve</li></ol>
</header>
<main>
${episodes.length ? `<div class="grid">${cards}</div>` : '<p class="none">The first run is on its way.</p>'}
</main>
<footer>Every episode's files, models and KiCad projects are on <a href="https://github.com/donaldbell/productspeedrun">GitHub</a>.</footer>
</div>
</body>
</html>
`;
await writeFile(path.join(OUT, "index.html"), html);
await writeFile(path.join(OUT, ".nojekyll"), "");
console.log(`Built _site with ${episodes.length} episode${episodes.length === 1 ? "" : "s"}.`);
