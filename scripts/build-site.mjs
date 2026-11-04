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
    let cover = [ep.favorites?.render, ep.favorites?.["2-concept"], ep.favorites?.["3-layout"]].find((c) => c && existsSync(path.join(dir, c)));
    if (!cover) for (const sd of ["2-concept", "3-layout", "4-model"]) {
      try { const f = (await readdir(path.join(dir, sd))).find((n) => IMG.test(n)); if (f) { cover = `${sd}/${f}`; break; } } catch {}
    }
    const showcase = existsSync(path.join(dir, "6-showcase", "index.html"));
    episodes.push({ slug: d.name, ep, cover, showcase });
  }
}
episodes.sort((a, b) => (b.ep.number || 0) - (a.ep.number || 0));

// Newsletter signup (Beehiiv). One block, added by the build to the gallery and to every
// showcase page (before the page's footer), so episode folders never need to carry it.
const BEEHIIV_FORM = "fb6aa340-96bf-486d-843d-1315f50baa10";
const SIGNUP = `<section class="ps-signup" id="subscribe" aria-labelledby="ps-signup-h">
<style>
.ps-signup { --ps-ink: #1B1F27; --ps-muted: #5D6573; --ps-line: #DADEE4; --ps-panel: #F6F7F9; --ps-run: #17864D;
  box-sizing: border-box; width: min(720px, calc(100% - 32px)); margin: 48px auto; padding: 24px clamp(16px, 4vw, 28px);
  background: var(--ps-panel); color: var(--ps-ink); border: 1px solid var(--ps-line); border-radius: 14px;
  font: 15px/1.5 "JetBrains Mono", ui-monospace, Menlo, monospace; text-align: center; }
@media (prefers-color-scheme: dark) { .ps-signup { --ps-ink: #F3EFE6; --ps-muted: #8C96A8; --ps-line: #283142; --ps-panel: #141922; --ps-run: #63E39A; } }
:root[data-theme="dark"] .ps-signup { --ps-ink: #F3EFE6; --ps-muted: #8C96A8; --ps-line: #283142; --ps-panel: #141922; --ps-run: #63E39A; }
:root[data-theme="light"] .ps-signup { --ps-ink: #1B1F27; --ps-muted: #5D6573; --ps-line: #DADEE4; --ps-panel: #F6F7F9; --ps-run: #17864D; }
.ps-signup h2 { margin: 0 0 6px; font: 800 clamp(22px, 4vw, 28px)/1.1 "Bricolage Grotesque", "Avenir Next", system-ui, sans-serif; letter-spacing: -0.01em; color: var(--ps-ink); }
.ps-signup h2 span { color: var(--ps-run); }
.ps-signup p { margin: 0 auto 14px; max-width: 52ch; color: var(--ps-muted); }
.ps-signup .ps-signup-form { display: flex; justify-content: center; min-height: 60px; }
.ps-signup .ps-signup-form iframe { max-width: 100%; }
</style>
<h2 id="ps-signup-h">Get each run <span>by email</span></h2>
<p>A short diary of every episode: the roll, the turns the idea took, and the board at the end. One email per episode.</p>
<div class="ps-signup-form"><script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" data-beehiiv-form="${BEEHIIV_FORM}"></script></div>
</section>`;
const addSignup = (page) => {
  if (page.includes("data-beehiiv-form")) return page;
  const at = page.toLowerCase().lastIndexOf("<footer");
  if (at > -1) return page.slice(0, at) + SIGNUP + "\n" + page.slice(at);
  return page.replace(/<\/body>/i, SIGNUP + "\n</body>");
};

// Shared showcase look and the series bar (kit/), then give every showcase page a filled-in
// <ps-series-bar> linking home and to the episodes either side.
if (existsSync(path.join(ROOT, "kit"))) await cp(path.join(ROOT, "kit"), path.join(OUT, "kit"), { recursive: true });
const shown = episodes.filter((e) => e.showcase).sort((a, b) => (a.ep.number || 0) - (b.ep.number || 0));
for (const [i, e] of shown.entries()) {
  const file = path.join(OUT, "episodes", e.slug, "6-showcase", "index.html");
  const page = await readFile(file, "utf8");
  const nb = (o) => (o ? `../../${enc(o.slug)}/6-showcase/` : "");
  const name = (o) => (o ? o.ep.brief?.name || o.ep.title || "" : "");
  const prev = shown[i - 1], next = shown[i + 1];
  const tag = `<ps-series-bar home="../../../" number="${esc(e.ep.number || "")}" name="${esc(name(e))}" prev="${nb(prev)}" prev-name="${esc(name(prev))}" next="${nb(next)}" next-name="${esc(name(next))}"></ps-series-bar>`;
  let out;
  if (/<ps-series-bar[\s>]/.test(page)) out = page.replace(/<ps-series-bar[^>]*>(\s*<\/ps-series-bar>)?/, tag);
  else out = page.replace(/<body[^>]*>/i, (m) => `${m}\n${tag}`);
  if (!out.includes("kit/series-bar.js")) out = out.replace(/<\/head>/i, '<script type="module" src="../../../kit/series-bar.js"></script>\n</head>');
  await writeFile(file, addSignup(out));
}

// Revisions (products/<product>/rev-b/ …): copy them, give their pages the series bar, and point
// each product's gallery card at its latest revision page.
const slugify = (t) => String(t || "").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
  .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 50) || "untitled";
const PRODUCTS = path.join(ROOT, "products");
const revPages = {};   // product slug -> [{ rev, letter }]
if (existsSync(PRODUCTS)) {
  await cp(PRODUCTS, path.join(OUT, "products"), { recursive: true, filter: (src) => !/[\\/](\.trash|\.git|output|__pycache__)([\\/]|$)/.test(src) });
  for (const prod of await readdir(PRODUCTS)) {
    let revs = []; try { revs = (await readdir(path.join(PRODUCTS, prod))).filter((n) => /^rev-[b-z]$/.test(n)).sort(); } catch { continue; }
    for (const rev of revs) {
      const file = path.join(OUT, "products", prod, rev, "6-showcase", "index.html");
      if (!existsSync(file)) continue;
      let r = {}; try { r = JSON.parse(await readFile(path.join(PRODUCTS, prod, rev, "rev.json"), "utf8")); } catch {}
      const letter = rev.slice(4).toUpperCase();
      (revPages[prod] ||= []).push({ rev, letter, hero: r.hero && existsSync(path.join(PRODUCTS, prod, rev, r.hero)) ? `products/${prod}/${rev}/${r.hero}` : null });
      const page = await readFile(file, "utf8");
      const tag = `<ps-series-bar home="../../../../" number="${esc(r.number || "")}" name="${esc((r.product || prod) + " Rev " + letter)}"></ps-series-bar>`;
      let out = /<ps-series-bar[\s>]/.test(page) ? page.replace(/<ps-series-bar[^>]*>(\s*<\/ps-series-bar>)?/, tag) : page.replace(/<body[^>]*>/i, (m) => `${m}\n${tag}`);
      if (!out.includes("kit/series-bar.js")) out = out.replace(/<\/head>/i, '<script type="module" src="../../../../kit/series-bar.js"></script>\n</head>');
      await writeFile(file, addSignup(out));
    }
  }
}

const cards = episodes.map(({ slug, ep, cover, showcase }) => {
  const revs = revPages[slugify(ep.brief?.name || ep.title)] || [], latest = revs[revs.length - 1];
  const prod = slugify(ep.brief?.name || ep.title);
  const href = latest ? `products/${enc(prod)}/${latest.rev}/6-showcase/` : showcase ? `episodes/${enc(slug)}/6-showcase/` : cover ? `episodes/${enc(slug)}/${enc(cover)}` : null;
  const latestHero = [...revs].reverse().find((x) => x.hero)?.hero;
  const revLinks = latest ? `<p class="revs">${[showcase ? `<a href="episodes/${enc(slug)}/6-showcase/">Rev A</a>` : "Rev A", ...revs.map((x) => `<a href="products/${enc(prod)}/${x.rev}/6-showcase/">Rev ${x.letter}</a>`)].join(" · ")}</p>` : "";
  const tag = latest ? `<span class="tag keep">Rev ${latest.letter}</span>` : ep.decision === "keep" ? '<span class="tag keep">Keep building</span>' : ep.decision === "shelve" ? '<span class="tag shelve">Shelved</span>' : `<span class="tag">In progress · stage ${esc(ep.stage || 1)}</span>`;
  const roll = (ep.roll || []).map((r) => `<li>${esc(r.label)}</li>`).join("");
  return `<article class="card">
  ${href ? `<a class="cover" href="${href}">` : '<div class="cover">'}${latestHero ? `<img src="${latestHero.split("/").map(encodeURIComponent).join("/")}" alt="" loading="lazy">` : cover ? `<img src="episodes/${enc(slug)}/${enc(cover)}" alt="" loading="lazy">` : '<div class="blank">No art yet</div>'}${href ? "</a>" : "</div>"}
  <div class="body">
    <div class="meta"><span>#${esc(String(ep.number || "").padStart(3, "0"))}</span>${tag}</div>
    <h2>${href ? `<a href="${href}">` : ""}${esc(ep.brief?.name || ep.title)}${href ? "</a>" : ""}</h2>
    ${ep.brief?.pitch ? `<p>${esc(ep.brief.pitch)}</p>` : ""}
    ${roll ? `<ul class="roll">${roll}</ul>` : ""}
    ${revLinks}
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
.revs { margin: 0; font-size: 13px; color: var(--muted); } .revs a { color: var(--ink); }
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
  <p class="lede"><a href="#subscribe" style="color:var(--run)">Get each episode by email →</a></p>
  <ol class="steps"><li>Roll &amp; brief</li><li>Concept sketches</li><li>Isometric layout</li><li>3D model</li><li>Electronics</li><li>Showcase</li><li>Keep or shelve</li></ol>
</header>
<main>
${episodes.length ? `<div class="grid">${cards}</div>` : '<p class="none">The first run is on its way.</p>'}
</main>
${SIGNUP}
<footer>Every episode's files, models and KiCad projects are on <a href="https://github.com/donaldbell/productspeedrun">GitHub</a>, free to build, change and even sell: hardware under <a href="https://github.com/donaldbell/productspeedrun/blob/main/LICENSES/CERN-OHL-P-2.0.txt">CERN-OHL-P v2</a>, words and images under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>, software under <a href="https://github.com/donaldbell/productspeedrun/blob/main/LICENSES/MIT.txt">MIT</a>. If you build something from them, we'd love a credit and to hear about it.</footer>
</div>
</body>
</html>
`;
await writeFile(path.join(OUT, "index.html"), html);
await writeFile(path.join(OUT, ".nojekyll"), "");
console.log(`Built _site with ${episodes.length} episode${episodes.length === 1 ? "" : "s"}.`);
