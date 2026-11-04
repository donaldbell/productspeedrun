// Product Speedrun show console: a small local server with no dependencies.
// Run with `npm start` (or `node server.mjs`), then open http://localhost:4321
//
// It serves the dashboard, reads and writes episode folders, saves dropped files,
// proxies image generation (so API keys stay on this machine), and pushes live
// "file changed" events so whatever Claude Code writes shows up on screen.

import http from "node:http";
import { readFile, writeFile, mkdir, readdir, stat, rename, cp } from "node:fs/promises";
import { existsSync, watch, createReadStream, readFileSync } from "node:fs";
import path from "node:path";
import { execFile } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const EPISODES = path.join(ROOT, "episodes");
const PRODUCTS = path.join(ROOT, "products");   // revisions: products/<product>/rev-b/, rev-c/ …
const DASHBOARD = path.join(ROOT, "dashboard");
const PORT = Number(process.env.PORT) || 4321;

// ---------- .env (KEY=VALUE lines, optional) ----------
try {
  for (const line of readFileSync(path.join(ROOT, ".env"), "utf8").split(/\r?\n/)) {
    const m = /^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/.exec(line);
    if (m && !(m[1] in process.env)) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
} catch {}

const PROVIDERS = {
  pollinations: { label: "Pollinations (free, no key)", ready: true, refs: false },
  gemini: { label: "Gemini", ready: !!process.env.GEMINI_API_KEY, refs: true, model: process.env.GEMINI_IMAGE_MODEL || "gemini-3.1-flash-lite-image" },
  openai: { label: "OpenAI", ready: !!process.env.OPENAI_API_KEY, refs: true, model: process.env.OPENAI_IMAGE_MODEL || "gpt-image-1" },
};

export const STAGE_DIRS = ["2-concept", "3-layout", "4-model", "5-electronics", "6-showcase"];
export const REV_DIRS = ["4-model", "5-electronics", "6-showcase", "7-firmware"];
// Multi-unit products (a transmitter and a receiver, say): each unit has its own enclosure and
// board in units/<unit>/ (fit.json, FIT.md, 4-model/, 5-electronics/, and 7-firmware/ in revisions).
// A product without units/ is a one-piece product and works exactly as before.
export const UNIT_DIRS = ["4-model", "5-electronics"];
const UNIT_RE = /^[a-z0-9][a-z0-9-]{0,40}$/;
const UNIT_DIR_RE = /^units\/[a-z0-9][a-z0-9-]{0,40}\/(4-model|5-electronics|7-firmware)$/;
async function unitsIn(root) {
  try { return (await readdir(path.join(root, "units"), { withFileTypes: true })).filter((e) => e.isDirectory() && UNIT_RE.test(e.name)).map((e) => e.name).sort(); } catch { return []; }
}
async function unitDirs(root, sub = UNIT_DIRS) { return (await unitsIn(root)).flatMap((u) => sub.map((d) => `units/${u}/${d}`)); }
// A stage folder in a request: "4-model", or "units/<unit>/4-model" given as three URL segments.
function stageDirFrom(parts, i) {
  if (parts[i] === "units") return { sd: parts.slice(i, i + 3).join("/"), rest: parts.slice(i + 3) };
  return { sd: parts[i], rest: parts.slice(i + 1) };
}
async function ensureUnits(dir, units) {
  for (const u of Array.isArray(units) ? units : []) {
    if (!u || !UNIT_RE.test(u.key || "")) continue;
    for (const d of UNIT_DIRS) {
      const p = path.join(dir, "units", u.key, d);
      if (!existsSync(p)) { await mkdir(p, { recursive: true }); await writeFile(path.join(p, ".gitkeep"), ""); }
    }
  }
}
const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif",
  ".glb": "model/gltf-binary", ".gltf": "model/gltf+json", ".bin": "application/octet-stream",
  ".csv": "text/csv; charset=utf-8", ".md": "text/markdown; charset=utf-8", ".txt": "text/plain; charset=utf-8",
  ".kicad_sch": "text/plain; charset=utf-8", ".kicad_pcb": "text/plain; charset=utf-8", ".kicad_pro": "application/json",
  ".stl": "model/stl", ".obj": "text/plain", ".step": "application/step", ".mp4": "video/mp4", ".webm": "video/webm",
};

// ---------- helpers ----------
const SLUG_RE = /^[a-z0-9][a-z0-9-]{0,80}$/;
function slugify(s) {
  return String(s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 50) || "untitled";
}
function safeName(name) {
  const base = path.basename(String(name || "file")).replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+/, "");
  return base.slice(0, 120) || "file";
}
function inside(parent, child) {
  const rel = path.relative(parent, child);
  return rel && !rel.startsWith("..") && !path.isAbsolute(rel);
}
function send(res, code, body, type = "application/json; charset=utf-8") {
  res.writeHead(code, { "Content-Type": type, "Cache-Control": "no-store" });
  res.end(typeof body === "string" || Buffer.isBuffer(body) ? body : JSON.stringify(body));
}
async function readBody(req, limit = 60 * 1024 * 1024) {
  const chunks = []; let n = 0;
  for await (const c of req) { n += c.length; if (n > limit) throw Object.assign(new Error("File is too large (60 MB max)."), { code: 413 }); chunks.push(c); }
  return Buffer.concat(chunks);
}
async function readJson(req) {
  const b = await readBody(req, 2 * 1024 * 1024);
  try { return JSON.parse(b.toString("utf8") || "{}"); } catch { throw Object.assign(new Error("Body is not valid JSON."), { code: 400 }); }
}
async function uniquePath(dir, name) {
  const ext = path.extname(name), stem = name.slice(0, name.length - ext.length);
  let p = path.join(dir, name), i = 2;
  while (existsSync(p)) p = path.join(dir, `${stem}-${i++}${ext}`);
  return p;
}
const stamp = () => new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "-");

// ---------- episodes ----------
function epDir(slug) {
  if (!SLUG_RE.test(slug)) throw Object.assign(new Error("Unknown episode."), { code: 404 });
  return path.join(EPISODES, slug);
}
async function loadEpisode(slug) {
  try { return JSON.parse(await readFile(path.join(epDir(slug), "episode.json"), "utf8")); }
  catch (e) { if (e.code === 404) throw e; throw Object.assign(new Error("Episode not found."), { code: 404 }); }
}
async function listFiles(slug) { const dir = epDir(slug); return listDirFiles(dir, [...STAGE_DIRS, ...await unitDirs(dir)]); }
async function listDirFiles(root, dirs) {
  const out = {};
  for (const d of dirs) {
    const dir = path.join(root, d); out[d] = [];
    async function walk(sub) {
      let entries = [];
      try { entries = await readdir(path.join(dir, sub), { withFileTypes: true }); } catch { return; }
      for (const e of entries) {
        if (e.name.startsWith(".") || e.name === "node_modules") continue;
        const rel = sub ? `${sub}/${e.name}` : e.name;
        if (e.isDirectory()) { if (rel.split("/").length < 4) await walk(rel); continue; }
        const s = await stat(path.join(dir, rel));
        out[d].push({ name: rel, size: s.size, mtime: s.mtimeMs });
      }
    }
    await walk("");
    out[d].sort((a, b) => a.mtime - b.mtime);
  }
  return out;
}
async function listEpisodes() {
  await mkdir(EPISODES, { recursive: true });
  const out = [];
  for (const e of await readdir(EPISODES, { withFileTypes: true })) {
    if (!e.isDirectory() || !SLUG_RE.test(e.name)) continue;
    try {
      const ep = JSON.parse(await readFile(path.join(EPISODES, e.name, "episode.json"), "utf8"));
      out.push({ slug: e.name, number: ep.number, title: ep.title, product: ep.brief?.name || "", decision: ep.decision || null, stage: ep.stage || 1, createdAt: ep.createdAt });
    } catch {}
  }
  return out.sort((a, b) => (b.number || 0) - (a.number || 0));
}
async function createEpisode(title) {
  const list = await listEpisodes();
  const number = Math.max(0, ...list.map((e) => e.number || 0)) + 1;
  const slug = `${String(number).padStart(3, "0")}-${slugify(title)}`;
  const dir = epDir(slug);
  await mkdir(dir, { recursive: true });
  for (const d of STAGE_DIRS) await mkdir(path.join(dir, d), { recursive: true });
  const ep = {
    slug, number, title: String(title || "Untitled build").slice(0, 120), createdAt: new Date().toISOString(),
    stage: 1, roll: [], brief: { name: "", pitch: "", what: "", does: "", who: "", electronics: "", design: "", looksLike: "", size: "" },
    prompts: {}, promptEdited: {}, favorites: {}, done: [], decision: null,
  };
  await writeFile(path.join(dir, "episode.json"), JSON.stringify(ep, null, 2) + "\n");
  for (const d of STAGE_DIRS) await writeFile(path.join(dir, d, ".gitkeep"), "");
  return ep;
}

// ---------- revisions (Rev B, C, …) of "keep building" products ----------
// Rev A is the episode folder, untouched. Each later revision is products/<product>/rev-<x>/,
// a copy of the previous revision's model and electronics plus rev.json (owned by the console),
// REV.md (goals and changelog, written by Claude Code) and 7-firmware/.
const REV_RE = /^rev-[b-z]$/;
const LETTERS = "abcdefghijklmnopqrstuvwxyz";
function revDir(product, rev) {
  if (!SLUG_RE.test(product) || !REV_RE.test(rev)) throw Object.assign(new Error("Unknown revision."), { code: 404 });
  return path.join(PRODUCTS, product, rev);
}
async function loadRev(product, rev) {
  try { return JSON.parse(await readFile(path.join(revDir(product, rev), "rev.json"), "utf8")); }
  catch (e) { if (e.code === 404) throw e; throw Object.assign(new Error("Revision not found."), { code: 404 }); }
}
async function revsOf(product) {
  try { return (await readdir(path.join(PRODUCTS, product))).filter((n) => REV_RE.test(n)).sort(); } catch { return []; }
}
async function listShelf() {
  const out = [];
  for (const e of await listEpisodes()) {
    if (e.decision !== "keep") continue;
    const ep = await loadEpisode(e.slug);
    const name = ep.brief?.name || ep.title, product = slugify(name);
    const revs = [];
    for (const r of await revsOf(product)) { try { const j = await loadRev(product, r); revs.push({ rev: r, letter: j.letter, createdAt: j.createdAt, done: j.done || [] }); } catch {} }
    const img = ep.favorites?.render || ep.favorites?.["2-concept"] || null;
    out.push({ episode: e.slug, number: e.number, name, product, pitch: ep.brief?.pitch || "", image: img ? `/episodes/${e.slug}/${img}` : null, revs });
  }
  return out;
}
async function prevHero(dir, product, rev) {
  try { const j = JSON.parse(await readFile(path.join(dir, "rev.json"), "utf8")); return j.hero ? `/products/${product}/${rev}/${j.hero}` : j.previousHero || null; } catch { return null; }
}
const SKIP_COPY = /(^|[\\/])(output|\.trash|__pycache__|[^\\/]*-backups|fp-info-cache|[^\\/]*\.kicad_prl|render-[^\\/]*)([\\/]|$)/;
async function createRevision(episode) {
  const ep = await loadEpisode(episode);
  if (ep.decision !== "keep") throw Object.assign(new Error("Only products marked “keep building” go on the shelf."), { code: 400 });
  const name = ep.brief?.name || ep.title, product = slugify(name);
  const prev = await revsOf(product);
  const letter = LETTERS[(prev.length ? LETTERS.indexOf(prev[prev.length - 1].slice(4)) : 0) + 1];
  const rev = `rev-${letter}`, dir = revDir(product, rev);
  const base = prev.length ? path.join(PRODUCTS, product, prev[prev.length - 1]) : epDir(episode);
  const baseRel = path.relative(ROOT, base).split(path.sep).join("/");
  await mkdir(dir, { recursive: true });
  for (const d of ["4-model", "5-electronics"]) {
    if (existsSync(path.join(base, d))) await cp(path.join(base, d), path.join(dir, d), { recursive: true, filter: (src) => !SKIP_COPY.test(path.relative(base, src)) });
    else await mkdir(path.join(dir, d), { recursive: true });
  }
  for (const f of ["fit.json", "FIT.md", "SYSTEM.md"]) if (existsSync(path.join(base, f))) await cp(path.join(base, f), path.join(dir, f));
  for (const u of await unitsIn(base)) {
    for (const d of UNIT_DIRS) {
      const from = path.join(base, "units", u, d), to = path.join(dir, "units", u, d);
      if (existsSync(from)) await cp(from, to, { recursive: true, filter: (src) => !SKIP_COPY.test(path.relative(base, src)) });
      else await mkdir(to, { recursive: true });
    }
    for (const f of ["fit.json", "FIT.md"]) if (existsSync(path.join(base, "units", u, f))) await cp(path.join(base, "units", u, f), path.join(dir, "units", u, f));
    await mkdir(path.join(dir, "units", u, "7-firmware"), { recursive: true }); await writeFile(path.join(dir, "units", u, "7-firmware", ".gitkeep"), "");
  }
  for (const d of ["6-showcase", "7-firmware"]) { await mkdir(path.join(dir, d), { recursive: true }); await writeFile(path.join(dir, d, ".gitkeep"), ""); }
  const L = letter.toUpperCase();
  const r = { product: name, productSlug: product, rev, letter: L, episode, number: ep.number, basedOn: baseRel, createdAt: new Date().toISOString(),
    guest: "", goals: "", feedback: { cad: "", electronics: "", code: "", showcase: "" }, promptEdited: {}, prompts: {}, done: [], hero: null,
    previousHero: prev.length ? await prevHero(path.join(PRODUCTS, product, prev[prev.length - 1]), product, prev[prev.length - 1]) : (ep.favorites?.render ? `/episodes/${episode}/${ep.favorites.render}` : null) };
  await writeFile(path.join(dir, "rev.json"), JSON.stringify(r, null, 2) + "\n");
  await writeFile(path.join(dir, "REV.md"), `# ${name} Rev ${L}\n\nBased on \`${baseRel}\` (${prev.length ? "Rev " + prev[prev.length - 1].slice(4).toUpperCase() : "Rev A, episode " + String(ep.number).padStart(3, "0")}).\nThe hosts' goals and feedback are in \`rev.json\`; Claude Code records what changed below.\n\n## Changelog\n\n## Results\n\n## Still open\n`);
  return r;
}

// ---------- image generation ----------
async function refToInline(slug, rel) {
  let p;
  if (String(rel).startsWith("/")) {
    p = path.join(ROOT, ...String(rel).split("/").filter(Boolean).map(decodeURIComponent));
    if (!inside(EPISODES, p) && !inside(PRODUCTS, p)) throw Object.assign(new Error("Bad reference path."), { code: 400 });
  } else {
    p = path.join(epDir(slug), rel);
    if (!inside(epDir(slug), p)) throw Object.assign(new Error("Bad reference path."), { code: 400 });
  }
  const buf = await readFile(p);
  return { buf, mime: MIME[path.extname(p).toLowerCase()] || "image/png", name: path.basename(p) };
}
async function netFetch(name, url, opts) {
  try { return await fetch(url, opts); }
  catch { throw Object.assign(new Error(`Couldn't reach ${name}. Check the internet connection and try again.`), { code: 502 }); }
}
const ASPECTS = { "16:9": [1536, 864], "4:3": [1280, 960], "1:1": [1024, 1024], "3:4": [960, 1280] };

async function generate({ provider, prompt, refs = [], aspect = "16:9" }, slug) {
  const p = PROVIDERS[provider];
  if (!p) throw Object.assign(new Error("Unknown image provider."), { code: 400 });
  if (!p.ready) throw Object.assign(new Error(`${p.label} needs an API key in .env first.`), { code: 400 });
  if (!prompt || !String(prompt).trim()) throw Object.assign(new Error("Write a prompt first."), { code: 400 });
  const [w, h] = ASPECTS[aspect] || ASPECTS["16:9"];

  if (provider === "pollinations") {
    const url = `https://image.pollinations.ai/prompt/${encodeURIComponent(prompt)}?width=${w}&height=${h}&nologo=true&seed=${Math.floor(Math.random() * 1e9)}`;
    let r;
    try { r = await fetch(url); } catch { throw Object.assign(new Error("Couldn't reach Pollinations. Check the internet connection and try again."), { code: 502 }); }
    if (!r.ok) throw Object.assign(new Error(`Pollinations returned ${r.status}. It's a free best-effort service; try again in a moment.`), { code: 502 });
    return { buf: Buffer.from(await r.arrayBuffer()), ext: ".jpg" };
  }

  const inline = await Promise.all(refs.slice(0, 4).map((r) => refToInline(slug, r)));

  if (provider === "gemini") {
    const parts = [{ text: `${prompt}\n\nAspect ratio ${aspect}.` }, ...inline.map((i) => ({ inline_data: { mime_type: i.mime, data: i.buf.toString("base64") } }))];
    const r = await netFetch("Gemini", `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(p.model)}:generateContent`, {
      method: "POST", headers: { "Content-Type": "application/json", "x-goog-api-key": process.env.GEMINI_API_KEY },
      body: JSON.stringify({ contents: [{ parts }], generationConfig: { responseModalities: ["IMAGE", "TEXT"] } }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error(`Gemini: ${j.error?.message || r.status}`), { code: 502 });
    const img = (j.candidates?.[0]?.content?.parts || []).find((x) => x.inlineData || x.inline_data);
    const data = img?.inlineData || img?.inline_data;
    if (!data) throw Object.assign(new Error("Gemini answered without an image (it may have refused the prompt). Try rewording it."), { code: 502 });
    return { buf: Buffer.from(data.data, "base64"), ext: (data.mimeType || data.mime_type || "").includes("jpeg") ? ".jpg" : ".png" };
  }

  if (provider === "openai") {
    const size = w > h ? "1536x1024" : w < h ? "1024x1536" : "1024x1024";
    let r;
    if (inline.length) {
      const fd = new FormData();
      fd.append("model", p.model); fd.append("prompt", prompt); fd.append("size", size);
      for (const i of inline) fd.append("image[]", new Blob([i.buf], { type: i.mime }), i.name);
      r = await netFetch("OpenAI", "https://api.openai.com/v1/images/edits", { method: "POST", headers: { Authorization: `Bearer ${process.env.OPENAI_API_KEY}` }, body: fd });
    } else {
      r = await netFetch("OpenAI", "https://api.openai.com/v1/images/generations", {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
        body: JSON.stringify({ model: p.model, prompt, size }),
      });
    }
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error(`OpenAI: ${j.error?.message || r.status}`), { code: 502 });
    const b64 = j.data?.[0]?.b64_json;
    if (!b64) throw Object.assign(new Error("OpenAI answered without an image."), { code: 502 });
    return { buf: Buffer.from(b64, "base64"), ext: ".png" };
  }
}

// ---------- publishing with the local git setup ----------
function git(args) {
  return new Promise((resolve) => execFile("git", args, { cwd: ROOT, timeout: 120000, maxBuffer: 4 * 1024 * 1024 }, (err, stdout, stderr) =>
    resolve({ ok: !err, out: `${stdout || ""}${stderr || ""}`.trim() })));
}
async function publishEpisode(slug) {
  const rel = `episodes/${slug}`;
  if (!(await git(["rev-parse", "--is-inside-work-tree"])).ok) throw Object.assign(new Error("This folder isn't a git repository."), { code: 400 });
  const ep = await loadEpisode(slug);
  await git(["add", "--", rel]);
  const staged = !(await git(["diff", "--cached", "--quiet", "--", rel])).ok;
  if (staged) {
    const what = ep.decision === "keep" ? "keep building" : ep.decision === "shelve" ? "shelved" : `stage ${ep.stage || 1}`;
    const c = await git(["commit", "-m", `${slug}: ${what}`, "--", rel]);
    if (!c.ok) throw Object.assign(new Error("git commit failed: " + c.out.split("\n").slice(-2).join(" ")), { code: 500 });
  }
  let p = await git(["push"]);
  if (!p.ok && /rejected|fetch first|non-fast-forward/i.test(p.out)) {
    const pull = await git(["pull", "--rebase", "--autostash"]);
    if (!pull.ok) throw Object.assign(new Error("Couldn't merge changes from GitHub. Open a terminal in the repo and run git pull."), { code: 500 });
    p = await git(["push"]);
  }
  if (!p.ok) throw Object.assign(new Error("git push failed: " + p.out.split("\n").slice(-2).join(" ")), { code: 500 });
  return { ok: true, pushed: true, message: staged ? "Published. The site updates in a minute or two." : "Nothing new to commit. Pushed anything that was waiting." };
}

async function publishRev(product, rev) {
  const rel = path.relative(ROOT, revDir(product, rev)).split(path.sep).join("/");
  if (!(await git(["rev-parse", "--is-inside-work-tree"])).ok) throw Object.assign(new Error("This folder isn't a git repository."), { code: 400 });
  const r = await loadRev(product, rev);
  await git(["add", "--", rel]);
  const staged = !(await git(["diff", "--cached", "--quiet", "--", rel])).ok;
  if (staged) {
    const c = await git(["commit", "-m", `${product} rev ${r.letter}: ${(r.done || []).length ? "done: " + r.done.join(", ") : "in progress"}`, "--", rel]);
    if (!c.ok) throw Object.assign(new Error("git commit failed: " + c.out.split("\n").slice(-2).join(" ")), { code: 500 });
  }
  let p = await git(["push"]);
  if (!p.ok && /rejected|fetch first|non-fast-forward/i.test(p.out)) {
    const pull = await git(["pull", "--rebase", "--autostash"]);
    if (!pull.ok) throw Object.assign(new Error("Couldn't merge changes from GitHub. Open a terminal in the repo and run git pull."), { code: 500 });
    p = await git(["push"]);
  }
  if (!p.ok) throw Object.assign(new Error("git push failed: " + p.out.split("\n").slice(-2).join(" ")), { code: 500 });
  return { ok: true, message: staged ? "Published. The site updates in a minute or two." : "Nothing new to commit. Pushed anything that was waiting." };
}

// ---------- live events ----------
const clients = new Set();
let pending = new Map(), flushT = null;
function broadcast(evt) { const line = `data: ${JSON.stringify(evt)}\n\n`; for (const res of clients) res.write(line); }
function startWatcher() {
  mkdir(PRODUCTS, { recursive: true }).then(() => {
    try {
      watch(PRODUCTS, { recursive: true }, (_type, file) => {
        if (!file) return;
        const parts = file.split(path.sep);
        if (parts.length < 3 || parts.some((p) => p.startsWith(".") || p === "node_modules" || p === "output")) return;
        const u = parts[2] === "units" && parts.length > 4;
        pending.set("p:" + file, { rev: `${parts[0]}/${parts[1]}`, dir: u ? parts.slice(2, 5).join("/") : parts[2], name: parts.slice(u ? 5 : 3).join("/") || null });
        clearTimeout(flushT);
        flushT = setTimeout(() => { for (const e of pending.values()) broadcast({ type: "change", ...e }); pending.clear(); }, 250);
      });
    } catch {}
  }).catch(() => {});
  try {
    watch(EPISODES, { recursive: true }, (_type, file) => {
      if (!file) return;
      const parts = file.split(path.sep);
      if (parts.some((p) => p.startsWith(".") || p === "node_modules")) return;
      const u = parts[1] === "units" && parts.length > 3;
      pending.set(file, { slug: parts[0], dir: u ? parts.slice(1, 4).join("/") : parts[1] || null, name: parts.slice(u ? 4 : 2).join("/") || null });
      clearTimeout(flushT);
      flushT = setTimeout(() => { for (const e of pending.values()) broadcast({ type: "change", ...e }); pending.clear(); }, 250);
    });
  } catch (e) { console.warn("Live file watching is unavailable here:", e.message); }
}
setInterval(() => { for (const res of clients) res.write(": ping\n\n"); }, 25000).unref();

// ---------- static ----------
async function serveFile(res, file, req) {
  try {
    const s = await stat(file); if (!s.isFile()) return send(res, 404, { error: "Not found." });
    const type = MIME[path.extname(file).toLowerCase()] || "application/octet-stream";
    const range = /bytes=(\d*)-(\d*)/.exec(req.headers.range || "");
    if (range && type.startsWith("video")) {
      const start = Number(range[1] || 0), end = range[2] ? Number(range[2]) : s.size - 1;
      res.writeHead(206, { "Content-Type": type, "Content-Range": `bytes ${start}-${end}/${s.size}`, "Accept-Ranges": "bytes", "Content-Length": end - start + 1 });
      return createReadStream(file, { start, end }).pipe(res);
    }
    res.writeHead(200, { "Content-Type": type, "Content-Length": s.size, "Cache-Control": "no-cache" });
    createReadStream(file).pipe(res);
  } catch { send(res, 404, { error: "Not found." }); }
}

// ---------- router ----------
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const parts = url.pathname.split("/").filter(Boolean).map(decodeURIComponent);
  try {
    if (parts[0] === "api") {
      if (parts[1] === "config" && req.method === "GET")
        return send(res, 200, { providers: Object.fromEntries(Object.entries(PROVIDERS).map(([k, v]) => [k, { label: v.label, ready: v.ready, refs: v.refs, model: v.model || null }])) });

      if (parts[1] === "events") {
        res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-store", Connection: "keep-alive" });
        res.write("retry: 2000\n\n"); clients.add(res); req.on("close", () => clients.delete(res)); return;
      }

      if (parts[1] === "shelf" && req.method === "GET") return send(res, 200, await listShelf());
      // Reveal a file in Finder: POST /api/reveal {path: "/episodes/…" or "/products/…"} (macOS)
      if (parts[1] === "reveal" && req.method === "POST") {
        const b = await readJson(req);
        const p = path.join(ROOT, ...String(b.path || "").split("/").filter(Boolean).map(decodeURIComponent));
        if ((!inside(EPISODES, p) && !inside(PRODUCTS, p)) || !existsSync(p)) return send(res, 404, { error: "File not found." });
        execFile("open", ["-R", p], () => {});
        return send(res, 200, { ok: true });
      }
      if (parts[1] === "revisions") {
        if (parts.length === 2 && req.method === "POST") { const b = await readJson(req); return send(res, 201, await createRevision(String(b.episode || ""))); }
        const product = parts[2], rev = parts[3], dir = revDir(product, rev);
        if (parts.length === 4 && req.method === "GET") return send(res, 200, { rev: await loadRev(product, rev), files: await listDirFiles(dir, [...REV_DIRS, ...await unitDirs(dir, [...UNIT_DIRS, "7-firmware"])]) });
        if (parts.length === 4 && req.method === "PUT") {
          const r = await readJson(req); r.productSlug = product; r.rev = rev;
          await writeFile(path.join(dir, "rev.json"), JSON.stringify(r, null, 2) + "\n");
          return send(res, 200, { ok: true });
        }
        if (parts[4] === "publish" && req.method === "POST") return send(res, 200, await publishRev(product, rev));
        // Upload: POST /api/revisions/:product/:rev/files/:dir?name=   (raw body)
        if (parts[4] === "files" && req.method === "POST") {
          const { sd } = stageDirFrom(parts, 5); if (!REV_DIRS.includes(sd) && !UNIT_DIR_RE.test(sd)) return send(res, 400, { error: "Unknown revision folder." });
          const buf = await readBody(req);
          await mkdir(path.join(dir, sd), { recursive: true });
          const p = await uniquePath(path.join(dir, sd), safeName(url.searchParams.get("name")));
          await writeFile(p, buf);
          return send(res, 201, { file: `${sd}/${path.basename(p)}` });
        }
        // Hero render: POST /api/revisions/:product/:rev/generate {provider, prompt, refs (repo-rooted paths), aspect}
        if (parts[4] === "generate" && req.method === "POST") {
          const b = await readJson(req);
          const { buf, ext } = await generate(b, null);
          const sd = /^units\/[a-z0-9][a-z0-9-]{0,40}\/4-model$/.test(b.stageDir || "") ? b.stageDir : "4-model";
          const p = await uniquePath(path.join(dir, sd), `render-${b.provider}-${stamp()}${ext}`);
          await writeFile(p, buf);
          await writeFile(p + ".prompt.txt", `${b.provider}${PROVIDERS[b.provider].model ? " / " + PROVIDERS[b.provider].model : ""}\nrefs: ${(b.refs || []).join(", ") || "none"}\n\n${b.prompt}\n`);
          return send(res, 201, { file: `${sd}/${path.basename(p)}` });
        }
        return send(res, 404, { error: "Unknown revision route." });
      }

      if (parts[1] === "episodes") {
        if (parts.length === 2 && req.method === "GET") return send(res, 200, await listEpisodes());
        if (parts.length === 2 && req.method === "POST") { const b = await readJson(req); return send(res, 201, await createEpisode(b.title)); }
        const slug = parts[2]; const dir = epDir(slug);
        if (!existsSync(path.join(dir, "episode.json"))) return send(res, 404, { error: "Episode not found." });

        if (parts.length === 3 && req.method === "GET") return send(res, 200, { episode: await loadEpisode(slug), files: await listFiles(slug) });
        if (parts.length === 3 && req.method === "PUT") {
          const ep = await readJson(req); ep.slug = slug;
          await writeFile(path.join(dir, "episode.json"), JSON.stringify(ep, null, 2) + "\n");
          await ensureUnits(dir, ep.brief?.units);
          return send(res, 200, { ok: true });
        }
        // Upload: POST /api/episodes/:slug/files/:stageDir?name=foo.png  (raw body)
        if (parts[3] === "files" && req.method === "POST") {
          const { sd } = stageDirFrom(parts, 4); if (!STAGE_DIRS.includes(sd) && !UNIT_DIR_RE.test(sd)) return send(res, 400, { error: "Unknown stage folder." });
          const buf = await readBody(req);
          await mkdir(path.join(dir, sd), { recursive: true });
          const p = await uniquePath(path.join(dir, sd), safeName(url.searchParams.get("name")));
          await writeFile(p, buf);
          return send(res, 201, { file: `${sd}/${path.basename(p)}` });
        }
        // Remove: DELETE /api/episodes/:slug/files/:stageDir/:name  (moves to a hidden .trash folder)
        if (parts[3] === "files" && req.method === "DELETE") {
          const { sd, rest } = stageDirFrom(parts, 4); if (!STAGE_DIRS.includes(sd) && !UNIT_DIR_RE.test(sd)) return send(res, 400, { error: "Unknown stage folder." });
          const p = path.join(dir, sd, ...rest);
          if (!inside(path.join(dir, sd), p) || !existsSync(p)) return send(res, 404, { error: "File not found." });
          const trash = path.join(dir, sd, ".trash"); await mkdir(trash, { recursive: true });
          await rename(p, await uniquePath(trash, path.basename(p)));
          if (existsSync(p + ".prompt.txt")) await rename(p + ".prompt.txt", await uniquePath(trash, path.basename(p) + ".prompt.txt"));
          return send(res, 200, { ok: true });
        }
        // Publish: POST /api/episodes/:slug/publish  (commit this episode folder and push)
        if (parts[3] === "publish" && req.method === "POST") return send(res, 200, await publishEpisode(slug));
        // Generate: POST /api/episodes/:slug/generate {stageDir, provider, prompt, refs, aspect}
        if (parts[3] === "generate" && req.method === "POST") {
          const b = await readJson(req);
          if (!["2-concept", "3-layout", "4-model"].includes(b.stageDir) && !/^units\/[a-z0-9][a-z0-9-]{0,40}\/4-model$/.test(b.stageDir)) return send(res, 400, { error: "Images are generated into 2-concept, 3-layout or 4-model (hero renders)." });
          const { buf, ext } = await generate(b, slug);
          const p = await uniquePath(path.join(dir, b.stageDir), `${b.stageDir.endsWith("4-model") ? "render-" : ""}${b.provider}-${stamp()}${ext}`);
          await writeFile(p, buf);
          await writeFile(p + ".prompt.txt", `${b.provider}${PROVIDERS[b.provider].model ? " / " + PROVIDERS[b.provider].model : ""}\nrefs: ${(b.refs || []).join(", ") || "none"}\n\n${b.prompt}\n`);
          return send(res, 201, { file: `${b.stageDir}/${path.basename(p)}` });
        }
      }
      return send(res, 404, { error: "Unknown API route." });
    }

    // Revision files: /products/<product>/rev-b/…
    if (parts[0] === "products") {
      const p = path.join(PRODUCTS, ...parts.slice(1));
      if (!inside(PRODUCTS, p)) return send(res, 403, { error: "Forbidden." });
      if (existsSync(p) && (await stat(p)).isDirectory()) return serveFile(res, path.join(p, "index.html"), req);
      return serveFile(res, p, req);
    }

    // Episode files (images, models, KiCad files, the showcase page)
    if (parts[0] === "episodes") {
      const p = path.join(EPISODES, ...parts.slice(1));
      if (!inside(EPISODES, p)) return send(res, 403, { error: "Forbidden." });
      if (existsSync(p) && (await stat(p)).isDirectory()) return serveFile(res, path.join(p, "index.html"), req);
      return serveFile(res, p, req);
    }

    // Shared showcase look (kit/), used by every episode's showcase page as ../../../kit/
    if (parts[0] === "kit") {
      const kit = path.join(ROOT, "kit"), p = path.join(kit, ...parts.slice(1));
      if (!inside(kit, p)) return send(res, 403, { error: "Forbidden." });
      return serveFile(res, p, req);
    }

    // Dashboard
    const p = parts.length ? path.join(DASHBOARD, ...parts) : path.join(DASHBOARD, "index.html");
    if (!inside(DASHBOARD, p) && p !== path.join(DASHBOARD, "index.html")) return send(res, 403, { error: "Forbidden." });
    return serveFile(res, p, req);
  } catch (e) {
    console.error(e.message);
    return send(res, e.code && Number.isInteger(e.code) ? e.code : 500, { error: e.message || "Something went wrong." });
  }
});

await mkdir(EPISODES, { recursive: true });
startWatcher();
server.on("error", (e) => {
  if (e.code === "EADDRINUSE") {
    console.error(`\n  The console is already running on http://localhost:${PORT} (maybe in another Terminal window).\n  Open that address in Chrome, or stop the other copy with:\n\n    lsof -ti tcp:${PORT} | xargs kill\n\n  and then run npm start again.\n`);
    process.exit(1);
  }
  throw e;
});
server.listen(PORT, "127.0.0.1", () => {
  const ready = Object.entries(PROVIDERS).filter(([, v]) => v.ready).map(([, v]) => v.label).join(", ");
  console.log(`\n  Product Speedrun console → http://localhost:${PORT}\n  Image providers ready: ${ready}\n`);
});
