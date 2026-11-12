// Builds the public site into _site/: an episode gallery plus each episode's files
// (its showcase page in 6-showcase/ links to images and models with relative paths).
// Run: node scripts/build-site.mjs
import { readdir, readFile, writeFile, mkdir, mkdtemp, cp, rm, stat } from "node:fs/promises";
import os from "node:os";
import { existsSync, readFileSync } from "node:fs";
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
const slugify = (t) => String(t || "").toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
  .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 50) || "untitled";
// Every version of a product that has a page, for the series bar's Rev A · Rev B switcher:
// product slug -> [{ letter, page }] (page relative to the site root). Rev A is the episode.
const versions = {};
if (existsSync(path.join(ROOT, "products"))) {
  for (const prod of await readdir(path.join(ROOT, "products"))) {
    let revs = []; try { revs = (await readdir(path.join(ROOT, "products", prod))).filter((n) => /^rev-[b-z]$/.test(n)).sort(); } catch { continue; }
    revs = revs.filter((rev) => existsSync(path.join(ROOT, "products", prod, rev, "6-showcase", "index.html")));
    if (!revs.length) continue;
    const ep = episodes.find((e) => e.showcase && slugify(e.ep.brief?.name || e.ep.title) === prod);
    versions[prod] = [...(ep ? [{ letter: "A", page: `episodes/${enc(ep.slug)}/6-showcase/` }] : []),
      ...revs.map((rev) => ({ letter: rev.slice(4).toUpperCase(), page: `products/${enc(prod)}/${rev}/6-showcase/` }))];
  }
}
const revAttrs = (prod, letter) => {
  const v = versions[prod];
  return v && v.length > 1 ? ` revs="${esc(v.map((x) => `${x.letter}:${x.page}`).join(";"))}" rev="${esc(letter)}"` : "";
};
const shown = episodes.filter((e) => e.showcase).sort((a, b) => (a.ep.number || 0) - (b.ep.number || 0));
for (const [i, e] of shown.entries()) {
  const file = path.join(OUT, "episodes", e.slug, "6-showcase", "index.html");
  const page = await readFile(file, "utf8");
  const nb = (o) => (o ? `../../${enc(o.slug)}/6-showcase/` : "");
  const name = (o) => (o ? o.ep.brief?.name || o.ep.title || "" : "");
  const prev = shown[i - 1], next = shown[i + 1];
  const tag = `<ps-series-bar home="../../../" number="${esc(e.ep.number || "")}" name="${esc(name(e))}" prev="${nb(prev)}" prev-name="${esc(name(prev))}" next="${nb(next)}" next-name="${esc(name(next))}"${revAttrs(slugify(name(e)), "A")}></ps-series-bar>`;
  let out;
  if (/<ps-series-bar[\s>]/.test(page)) out = page.replace(/<ps-series-bar[^>]*>(\s*<\/ps-series-bar>)?/, tag);
  else out = page.replace(/<body[^>]*>/i, (m) => `${m}\n${tag}`);
  if (!out.includes("kit/series-bar.js")) out = out.replace(/<\/head>/i, '<script type="module" src="../../../kit/series-bar.js"></script>\n</head>');
  await writeFile(file, addSignup(out));
}

// Revisions (products/<product>/rev-b/ …): copy them, give their pages the series bar, and point
// each product's gallery card at its latest revision page.
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
      const tag = `<ps-series-bar home="../../../../" number="${esc(r.number || "")}" name="${esc((r.product || prod) + " Rev " + letter)}"${revAttrs(prod, letter)}></ps-series-bar>`;
      let out = /<ps-series-bar[\s>]/.test(page) ? page.replace(/<ps-series-bar[^>]*>(\s*<\/ps-series-bar>)?/, tag) : page.replace(/<body[^>]*>/i, (m) => `${m}\n${tag}`);
      if (!out.includes("kit/series-bar.js")) out = out.replace(/<\/head>/i, '<script type="module" src="../../../../kit/series-bar.js"></script>\n</head>');
      await writeFile(file, addSignup(out));
    }
  }
}

// "Build on it": added by the build to every showcase page, just above the newsletter signup.
// Links to the editable files on GitHub (3D design, each KiCad board, firmware), one-click zips,
// and a prompt that hands the whole project to any AI agent. Episode folders never carry it.
const REPO = "donaldbell/productspeedrun";
const GH = `https://github.com/${REPO}`;
const SITE = "https://donaldbell.github.io/productspeedrun";
const ghTree = (rel) => `${GH}/tree/main/${enc(rel)}`;
const ghBlob = (rel) => `${GH}/blob/main/${enc(rel)}`;
const listDir = async (abs) => { try { return await readdir(abs, { withFileTypes: true }); } catch { return []; } };
const has = (abs) => existsSync(abs);
const SKIP_ZIP = ["*.png", "*.jpg", "*.jpeg", "*.glb", "*/output/*", "*/__pycache__/*", "*.bak", "*/.gitkeep", "*-backups/*"];
async function zipFolder(absDir, outFile) {
  // zip is on GitHub's runners and on macOS; without it the page links to GitHub instead.
  const { execFileSync } = await import("node:child_process");
  try {
    await mkdir(path.dirname(outFile), { recursive: true });
    execFileSync("zip", ["-qr", outFile, ".", "-x", ...SKIP_ZIP], { cwd: absDir, stdio: "ignore" });
    return existsSync(outFile);
  } catch { return false; }
}
// A board's zip has to open on its own, but some boards point at custom footprints and 3D models in
// tools/kicad/ (outside their folder). Copy the ones a board uses into parts/ inside the zip and point
// the zipped KiCad files there. The repo's own files are unchanged.
const KIT_REF = /\$\{KIPRJMOD\}\/((?:\.\.\/)+)tools\/kicad\/((?:models|footprints)\/[^")\s]+)/g;
async function zipBoard(absDir, outFile) {
  const texts = new Map();
  for (const e of await listDir(absDir)) {
    if (!e.isFile() || !/\.(kicad_pcb|kicad_sch|kicad_pro)$|^(fp|sym)-lib-table$/.test(e.name)) continue;
    const t = await readFile(path.join(absDir, e.name), "utf8");
    if (t.includes("tools/kicad/")) texts.set(e.name, t);
  }
  if (!texts.size) return zipFolder(absDir, outFile);
  const kit = path.join(ROOT, "tools", "kicad"), used = new Set();
  const tmp = await mkdtemp(path.join(os.tmpdir(), "ps-zip-"));
  try {
    await cp(absDir, tmp, { recursive: true, filter: (src) => !/[\\/](output|__pycache__)([\\/]|$)/.test(src) });
    for (const [name, t] of texts) {
      await writeFile(path.join(tmp, name), t.replace(KIT_REF, (whole, ups, rest) => {
        const src = path.resolve(absDir, ups + "tools/kicad/" + rest);
        if (!src.startsWith(kit + path.sep) || !existsSync(src)) return whole;   // nothing to bundle: leave it
        used.add(rest);
        return "${KIPRJMOD}/parts/" + rest;
      }));
    }
    for (const rest of used) {
      await mkdir(path.dirname(path.join(tmp, "parts", rest)), { recursive: true });
      await cp(path.join(kit, rest), path.join(tmp, "parts", rest), { recursive: true });
    }
    return await zipFolder(tmp, outFile);
  } finally { await rm(tmp, { recursive: true, force: true }); }
}
// The boards in a project folder: 5-electronics itself, or one per 5-electronics/<device>/ (episode 003's layout).
async function boardsIn(absProject) {
  const hw = path.join(absProject, "5-electronics");
  const pro = (d) => listDir(d).then((es) => es.find((e) => e.isFile() && e.name.endsWith(".kicad_pro")));
  const top = await pro(hw);
  if (top) return [{ key: null, dir: "5-electronics", project: top.name.replace(/\.kicad_pro$/, "") }];
  const out = [];
  for (const e of await listDir(hw)) {
    if (!e.isDirectory() || ["lib", "src", "output", "tools"].includes(e.name)) continue;
    const p = await pro(path.join(hw, e.name));
    if (p) out.push({ key: e.name, dir: `5-electronics/${e.name}`, project: p.name.replace(/\.kicad_pro$/, "") });
  }
  return out;
}
// Firmware: 7-firmware/ (one PlatformIO project) or 7-firmware/<device>/ (one per device).
async function firmwareIn(absProject) {
  const fw = path.join(absProject, "7-firmware");
  if (has(path.join(fw, "platformio.ini"))) return [{ key: null, dir: "7-firmware" }];
  const out = [];
  for (const e of await listDir(fw)) if (e.isDirectory() && has(path.join(fw, e.name, "platformio.ini"))) out.push({ key: e.name, dir: `7-firmware/${e.name}` });
  return out;
}
// The KiCad version that saved a board ("10.0" → 10), so makers know which KiCad opens it.
const kicadVersion = async (absPcb) => { try { const m = /\(generator_version "(\d+)/.exec((await readFile(absPcb, "utf8")).slice(0, 400)); return m ? Number(m[1]) : null; } catch { return null; } };
const titleCase = (k) => (k ? k[0].toUpperCase() + k.slice(1).replace(/-/g, " ") : "");

// ctx: { rel: repo path of this project ("episodes/003-003" or "products/x/rev-b"), page: site path of the page,
//        name, number, epRel (the episode's repo path), revs: ["rev-b", …] (all revision folders of the product), revRel?: this revision }
async function buildOn(ctx) {
  const abs = path.join(ROOT, ctx.rel), dl = `${SITE}/downloads/${ctx.rel.replace(/\//g, "-")}`;
  const cards = [], zips = [];
  // 3D model
  const m = path.join(abs, "4-model"), mf = (n) => has(path.join(m, n));
  if (has(m)) {
    const links = [];
    if (mf("model.step")) links.push([`${ctx.rel}/4-model/model.step`, "model.step", "opens in any CAD tool (FreeCAD, Fusion, Onshape…)", true]);
    if (mf("model.stl")) links.push([`${ctx.rel}/4-model/model.stl`, "model.stl", "mesh for 3D printing", true]);
    if (mf("model.solidcraft")) links.push([`${ctx.rel}/4-model/model.solidcraft`, "model.solidcraft", "the editable Solidcraft design", true]);
    if (mf("build_model.py")) links.push([`${ctx.rel}/4-model/build_model.py`, "build_model.py", "a record of how the show built the model (it needs the show's own tools to run)", false]);
    if (mf("NOTES.md")) links.push([`${ctx.rel}/4-model/NOTES.md`, "NOTES.md", "dimensions, decisions and open questions", false]);
    const z = await zipFolder(m, path.join(OUT, "downloads", `${ctx.rel.replace(/\//g, "-")}-3d-model.zip`));
    if (links.length) cards.push({ title: "3D model", sub: "Enclosure, ready to edit or print", folder: `${ctx.rel}/4-model`, zip: z && `${dl}-3d-model.zip`, links });
  }
  // KiCad boards
  const boards = await boardsIn(abs);
  for (const b of boards) {
    const bd = `${ctx.rel}/${b.dir}`, ab = path.join(abs, b.dir), links = [];
    for (const ext of ["kicad_pro", "kicad_sch", "kicad_pcb"]) if (has(path.join(ab, `${b.project}.${ext}`))) links.push([`${bd}/${b.project}.${ext}`, `${b.project}.${ext}`, { kicad_pro: "KiCad project", kicad_sch: "schematic", kicad_pcb: "routed 2-layer board" }[ext], false]);
    if (has(path.join(ab, "bom.csv"))) links.push([`${bd}/bom.csv`, "bom.csv", "parts list with manufacturer part numbers", true]);
    if (has(path.join(ab, "src", "design.py"))) links.push([`${bd}/src/design.py`, "src/design.py", "the parts and nets the board was generated from (a record, not runnable)", false]);
    if (has(path.join(ab, "src", "layout.py"))) links.push([`${bd}/src/layout.py`, "src/layout.py", "the outline and placement it was generated from (a record)", false]);
    const z = await zipBoard(ab, path.join(OUT, "downloads", `${(bd).replace(/\//g, "-")}-kicad.zip`));
    const kv = await kicadVersion(path.join(ab, `${b.project}.kicad_pcb`));
    cards.push({ title: b.key ? `Board · ${titleCase(b.key)}` : "Circuit board", sub: kv ? `KiCad project, schematic and BOM. Saved with KiCad ${kv}: open it in ${kv} or newer.` : "KiCad project, schematic and BOM", folder: bd, zip: z && `${SITE}/downloads/${bd.replace(/\//g, "-")}-kicad.zip`, links });
  }
  // Firmware
  for (const f of await firmwareIn(abs)) {
    const fd = `${ctx.rel}/${f.dir}`, af = path.join(abs, f.dir), links = [[`${fd}/platformio.ini`, "platformio.ini", "PlatformIO project", false]];
    if (has(path.join(af, "src"))) links.push([`${fd}/src`, "src/", "the code", false, true]);
    if (has(path.join(af, "NOTES.md"))) links.push([`${fd}/NOTES.md`, "NOTES.md", "flash and RAM use, libraries, what's stubbed", false]);
    const z = await zipFolder(af, path.join(OUT, "downloads", `${fd.replace(/\//g, "-")}-firmware.zip`));
    cards.push({ title: f.key ? `Firmware · ${titleCase(f.key)}` : "Firmware", sub: "PlatformIO, first pass", folder: fd, zip: z && `${SITE}/downloads/${fd.replace(/\//g, "-")}-firmware.zip`, links });
  }

  // The prompt for an AI agent
  const prod = ctx.revs.length ? `products/${ctx.product}` : null;
  const latest = ctx.revs[ctx.revs.length - 1];
  const sparse = [ctx.epRel, prod, "tools/kicad"].filter(Boolean).join(" ");
  const here = ctx.revRel || (latest ? `products/${ctx.product}/${latest}` : ctx.epRel);
  const has3 = (p) => has(path.join(ROOT, here, p));
  const read = [
    "README.md (the folder layout and how to open the files)",
    `${ctx.epRel}/episode.json (the brief: what it is and does, who it's for, what's inside, design language, form factor)`,
    has(path.join(ROOT, here, "SYSTEM.md")) ? `${here}/SYSTEM.md (how the devices work together)` : null,
    ctx.revRel || latest ? `${here}/REV.md (what changed in this revision, and what's still open)` : null,
    has3("4-model/NOTES.md") ? `${here}/4-model/NOTES.md (the enclosure: dimensions and decisions)` : null,
    has3("5-electronics/NOTES.md") ? `${here}/5-electronics/NOTES.md (the electronics: parts, power, open questions)` : null,
    ...(await boardsIn(path.join(ROOT, here))).filter((b) => b.key && has(path.join(ROOT, here, b.dir, "NOTES.md"))).map((b) => `${here}/${b.dir}/NOTES.md`),
    has3("FIT.md") ? `${here}/FIT.md and fit.json (how the board sits in the enclosure, shared by both)` : null,
    `the concept art in ${ctx.epRel}/2-concept/ and the model screenshot ${here}/4-model/iso.png`,
  ].filter(Boolean);
  for (const b of await boardsIn(path.join(ROOT, here))) { const v = await kicadVersion(path.join(ROOT, here, b.dir, `${b.project}.kicad_pcb`)); if (v && (!ctx.kicad || v > ctx.kicad)) ctx.kicad = v; }
  const fwNote = (await firmwareIn(path.join(ROOT, here))).length ? ` Firmware is a PlatformIO project in ${here}/7-firmware/.` : "";
  const prompt = `I'd like to keep developing ${ctx.name}, an open-source hardware concept from Product Speedrun${ctx.number ? ` episode ${String(ctx.number).padStart(3, "0")}` : ""} (${SITE}/${ctx.page}). Its files are in the GitHub repository ${REPO}: the episode in ${ctx.epRel}/${latest ? `, and later revisions in products/${ctx.product}/ (the latest is Rev ${latest.slice(4).toUpperCase()})` : ""}.${ctx.revRel ? ` Start from ${ctx.revRel}/.` : ""}

1. Get the files. First ask me whether to fork the repository on GitHub (so my work shows up as a fork and can go back as a pull request) or just clone it. Then fetch only this project and the KiCad part libraries it uses:
   git clone --filter=blob:none --sparse <my fork's URL, or ${GH}.git>
   cd productspeedrun
   git sparse-checkout set ${sparse}

2. Read these, in order:
${read.map((r) => `   - ${r}`).join("\n")}

3. How to change it:
   - The enclosure is ${here}/4-model/model.step (with model.stl for printing). Edit it in a CAD tool I have.${has3("4-model/build_model.py") ? " build_model.py is a record of how the show generated it; it relies on the show's own tools, which aren't public, so don't try to run it." : ""}
   - Each circuit board is a KiCad project (saved with KiCad ${ctx.kicad || "9 or newer"}). Edit it in KiCad. Its custom footprints and 3D part models are in tools/kicad/footprints and tools/kicad/models, so keep the folder layout. src/design.py and src/layout.py record the parts, nets and placement the show generated it from: read them as notes, not as something to run.
   - fit.json and FIT.md record how the board sits in the enclosure (outline, posts, and what lines up with windows and buttons). If you change one side, check the other against them by hand.${fwNote}

4. Before changing anything, give me a short summary of the project and the open questions from the notes, and ask what I want to change. Work on a branch or in a new folder of my own, so the original stays as it aired.

5. Licences: hardware CERN-OHL-P v2, words and images CC BY 4.0, code MIT. Anything I make or publish from this should credit Product Speedrun${ctx.number ? ` episode ${String(ctx.number).padStart(3, "0")}` : ""} and link to ${SITE}/${ctx.page}.

6. When we're done, ask me how I'd like to share it: a pull request back to ${REPO}, a link to my fork, or keep it to myself.`;

  const link = ([rel, label, note, raw, tree]) => `<li><a href="${raw ? `${SITE}/${enc(rel)}` : tree ? ghTree(rel) : ghBlob(rel)}"${raw ? " download" : ""}>${esc(label)}</a><span>${esc(note)}</span></li>`;
  const card = (c) => `<article class="psb-card"><h3>${esc(c.title)}</h3><p class="psb-sub">${esc(c.sub)}</p><ul>${c.links.map(link).join("")}</ul>
<p class="psb-acts">${c.zip ? `<a class="psb-btn" href="${c.zip}" download>Download .zip</a>` : ""}<a class="psb-btn ghost" href="${ghTree(c.folder)}">Folder on GitHub</a></p></article>`;
  return `<section class="ps-build" id="build-on-it" aria-labelledby="ps-build-h">
<style>
.ps-build { --pb-ink: #1B1F27; --pb-muted: #5D6573; --pb-line: #DADEE4; --pb-panel: #F6F7F9; --pb-card: #FFFFFF; --pb-run: #17864D; --pb-on-run: #FFFFFF;
  box-sizing: border-box; width: min(1100px, calc(100% - 32px)); margin: 56px auto 0; padding: clamp(18px, 4vw, 32px);
  background: var(--pb-panel); color: var(--pb-ink); border: 1px solid var(--pb-line); border-radius: 16px;
  font: 15px/1.5 "JetBrains Mono", ui-monospace, Menlo, monospace; }
@media (prefers-color-scheme: dark) { .ps-build { --pb-ink: #F3EFE6; --pb-muted: #8C96A8; --pb-line: #283142; --pb-panel: #10141B; --pb-card: #141922; --pb-run: #63E39A; --pb-on-run: #06140B; } }
:root[data-theme="dark"] .ps-build { --pb-ink: #F3EFE6; --pb-muted: #8C96A8; --pb-line: #283142; --pb-panel: #10141B; --pb-card: #141922; --pb-run: #63E39A; --pb-on-run: #06140B; }
:root[data-theme="light"] .ps-build { --pb-ink: #1B1F27; --pb-muted: #5D6573; --pb-line: #DADEE4; --pb-panel: #F6F7F9; --pb-card: #FFFFFF; --pb-run: #17864D; --pb-on-run: #FFFFFF; }
.ps-build * { box-sizing: border-box; }
.ps-build h2 { margin: 0 0 6px; font: 800 clamp(26px, 5vw, 38px)/1.05 "Bricolage Grotesque", "Avenir Next", system-ui, sans-serif; letter-spacing: -0.02em; color: var(--pb-ink); }
.ps-build h2 span { color: var(--pb-run); }
.ps-build h3 { margin: 0; font: 700 19px/1.2 "Bricolage Grotesque", "Avenir Next", system-ui, sans-serif; color: var(--pb-ink); }
.ps-build .psb-lede { margin: 0 0 16px; max-width: 70ch; color: var(--pb-muted); }
.ps-build a { color: var(--pb-run); text-underline-offset: 3px; overflow-wrap: anywhere; }
.ps-build a:focus-visible, .ps-build button:focus-visible { outline: 3px solid var(--pb-run); outline-offset: 2px; border-radius: 4px; }
.ps-build .psb-top { display: flex; flex-wrap: wrap; gap: 10px; margin: 0 0 22px; }
.ps-build .psb-btn { display: inline-flex; align-items: center; gap: .4em; padding: 9px 16px; border-radius: 999px; background: var(--pb-run); color: var(--pb-on-run); border: 1.5px solid var(--pb-run);
  font: 700 14px/1 "Bricolage Grotesque", "Avenir Next", system-ui, sans-serif; text-decoration: none; cursor: pointer; }
.ps-build .psb-btn.ghost { background: transparent; color: var(--pb-ink); border-color: var(--pb-line); }
.ps-build .psb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 290px), 1fr)); gap: 14px; }
.ps-build .psb-card { background: var(--pb-card); border: 1px solid var(--pb-line); border-radius: 12px; padding: 16px; display: grid; gap: 8px; align-content: start; min-width: 0; }
.ps-build .psb-sub { margin: 0; color: var(--pb-muted); font-size: 13px; }
.ps-build ul { list-style: none; margin: 4px 0 0; padding: 0; display: grid; gap: 6px; font-size: 13.5px; }
.ps-build li { display: grid; gap: 0; }
.ps-build li span { color: var(--pb-muted); font-size: 12.5px; }
.ps-build .psb-acts { display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 0; }
.ps-build .psb-acts .psb-btn { font-size: 13px; padding: 7px 12px; }
.ps-build .psb-ai { margin-top: 22px; background: var(--pb-card); border: 1.5px dashed var(--pb-run); border-radius: 12px; padding: 16px; display: grid; gap: 10px; }
.ps-build .psb-ai p { margin: 0; color: var(--pb-muted); max-width: 75ch; }
.ps-build .psb-ai textarea { width: 100%; min-height: 220px; resize: vertical; background: var(--pb-panel); color: var(--pb-ink); border: 1px solid var(--pb-line); border-radius: 8px; padding: 12px;
  font: 12.5px/1.5 "JetBrains Mono", ui-monospace, Menlo, monospace; }
.ps-build .psb-ai .psb-row { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; }
.ps-build .psb-lic { margin: 18px 0 0; font-size: 12.5px; color: var(--pb-muted); }
</style>
<h2 id="ps-build-h">Build <span>on it</span></h2>
<p class="psb-lede">Everything behind ${esc(ctx.name)} is open: the 3D design, the KiCad boards${cards.some((c) => /^Firmware/.test(c.title)) ? ", the firmware" : ""} and the notes. Download it, change it, make it, even sell it. All we ask is a credit and a link back.</p>
<p class="psb-top"><a class="psb-btn" href="${ghTree(ctx.rel)}">Open the project on GitHub</a>${ctx.revRel ? `<a class="psb-btn ghost" href="${ghTree(ctx.epRel)}">Rev A (the episode)</a>` : latest ? `<a class="psb-btn ghost" href="${ghTree(`products/${ctx.product}`)}">Later revisions</a>` : ""}</p>
<div class="psb-grid">${cards.map(card).join("\n")}</div>
<div class="psb-ai">
<div class="psb-row"><h3>Continue it with an AI agent</h3><button type="button" class="psb-btn" data-psb-copy>Copy prompt</button></div>
<p>Paste this into Claude Code, Codex, Cursor or any agent that can run commands. It fetches just this project and its part libraries, reads the notes in the right order, and asks you before it changes anything.</p>
<textarea readonly aria-label="Prompt for an AI agent" data-psb-prompt>${esc(prompt)}</textarea>
</div>
<p class="psb-lic">Hardware under <a href="${GH}/blob/main/LICENSES/CERN-OHL-P-2.0.txt">CERN-OHL-P v2</a>, words and images under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>, code under <a href="${GH}/blob/main/LICENSES/MIT.txt">MIT</a>.</p>
<script>
document.querySelectorAll("[data-psb-copy]").forEach((b) => b.addEventListener("click", async () => {
  const t = b.closest(".psb-ai").querySelector("[data-psb-prompt]");
  try { await navigator.clipboard.writeText(t.value); b.textContent = "Copied"; } catch { t.focus(); t.select(); b.textContent = "Press Cmd/Ctrl+C"; }
  setTimeout(() => { b.textContent = "Copy prompt"; }, 2400);
}));
</script>
</section>`;
}
const addBuildOn = (page, block) => {
  if (page.includes('id="build-on-it"')) return page;
  const at = page.indexOf('<section class="ps-signup"');
  return at > -1 ? page.slice(0, at) + block + "\n" + page.slice(at) : page.replace(/<\/body>/i, block + "\n</body>");
};
// Every revision folder of a product (not only those with a page), for the prompt.
const allRevs = async (prod) => (await listDir(path.join(ROOT, "products", prod))).filter((e) => e.isDirectory() && /^rev-[b-z]$/.test(e.name)).map((e) => e.name).sort();
for (const e of episodes.filter((x) => x.showcase)) {
  const file = path.join(OUT, "episodes", e.slug, "6-showcase", "index.html");
  const product = slugify(e.ep.brief?.name || e.ep.title);
  const block = await buildOn({ rel: `episodes/${e.slug}`, epRel: `episodes/${e.slug}`, page: `episodes/${enc(e.slug)}/6-showcase/`, name: e.ep.brief?.name || e.ep.title, number: e.ep.number, product, revs: await allRevs(product) });
  await writeFile(file, addBuildOn(await readFile(file, "utf8"), block));
}
for (const [prod, list] of Object.entries(revPages)) {
  for (const { rev, letter } of list) {
    const file = path.join(OUT, "products", prod, rev, "6-showcase", "index.html");
    let r = {}; try { r = JSON.parse(await readFile(path.join(PRODUCTS, prod, rev, "rev.json"), "utf8")); } catch {}
    const block = await buildOn({ rel: `products/${prod}/${rev}`, revRel: `products/${prod}/${rev}`, epRel: `episodes/${r.episode || ""}`, page: `products/${prod}/${rev}/6-showcase/`,
      name: `${r.product || prod} Rev ${letter}`, number: r.number, product: prod, revs: await allRevs(prod) });
    await writeFile(file, addBuildOn(await readFile(file, "utf8"), block));
  }
}

// A card's description is the pitch line of the page it links to (the latest revision's, else the
// episode's), so the careful "design proposal" wording on the pages carries to the gallery.
// episode.json's brief.pitch (the dashboard's raw brief) is only the fallback.
const decode = (s) => s.replace(/<[^>]+>/g, "").replace(/&(amp|lt|gt|quot|#39|rsquo|lsquo|nbsp);/g, (m, k) =>
  ({ amp: "&", lt: "<", gt: ">", quot: '"', "#39": "'", rsquo: "’", lsquo: "‘", nbsp: " " }[k])).replace(/\s+/g, " ").trim();
const pagePitch = (file) => {
  try { const m = readFileSync(file, "utf8").match(/<p class="(?:ps-)?pitch">([\s\S]*?)<\/p>/); return m ? decode(m[1]) : ""; } catch { return ""; }
};
const cards = episodes.map(({ slug, ep, cover, showcase }) => {
  const revs = revPages[slugify(ep.brief?.name || ep.title)] || [], latest = revs[revs.length - 1];
  const prod = slugify(ep.brief?.name || ep.title);
  const pitch = (latest && pagePitch(path.join(ROOT, "products", prod, latest.rev, "6-showcase", "index.html")))
    || (showcase && pagePitch(path.join(EP, slug, "6-showcase", "index.html"))) || ep.brief?.pitch || "";
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
    ${pitch ? `<p>${esc(pitch)}</p>` : ""}
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
  <ol class="steps"><li>Roll &amp; brief</li><li>Concept sketches</li><li>Control drawing</li><li>3D model</li><li>Electronics</li><li>Showcase</li><li>Keep or shelve</li></ol>
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
