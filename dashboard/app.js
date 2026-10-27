// Product Speedrun console. Talks to server.mjs on the same machine.
const ROLLER_ORIGIN = "https://donaldbell.github.io";
const ROLLER_URL = ROLLER_ORIGIN + "/random-project-generator/show.html";

const STAGES = [
  { n: 1, name: "Roll & brief", dir: null },
  { n: 2, name: "Concept sketches", dir: "2-concept" },
  { n: 3, name: "Isometric layout", dir: "3-layout" },
  { n: 4, name: "3D model", dir: "4-model" },
  { n: 5, name: "Electronics", dir: "5-electronics" },
  { n: 6, name: "Showcase", dir: "6-showcase" },
  { n: 7, name: "Keep or shelve", dir: null },
];
const IMG = /\.(png|jpe?g|webp|gif)$/i;

const $ = (id) => document.getElementById(id);
function h(tag, attrs, ...kids) {
  const n = document.createElement(tag);
  if (attrs) for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") n.className = v;
    else if (k === "text") n.textContent = v;
    else if (k === "html") n.innerHTML = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat()) if (c != null && c !== false) n.append(c.nodeType ? c : document.createTextNode(String(c)));
  return n;
}
const local = {
  get(k, d) { try { const v = localStorage.getItem("psr:" + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("psr:" + k, JSON.stringify(v)); } catch {} },
};

const S = {
  config: { providers: {} }, episodes: [], ep: null, files: {}, view: null,
  arrivals: new Set(), developing: {}, prefs: { safe: "none", showSafe: false, sound: true, provider: "pollinations", ...local.get("prefs", {}) },
};

/* ---------- api ---------- */
async function api(path, opts = {}) {
  const r = await fetch("/api" + path, opts);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `Request failed (${r.status}).`);
  return j;
}
let saveT = null;
function save(now) {
  if (!S.ep) return;
  clearTimeout(saveT);
  const run = () => api(`/episodes/${S.ep.slug}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(S.ep) })
    .catch((e) => toast("Couldn't save: " + e.message, true));
  if (now) return run();
  saveT = setTimeout(run, 400);
}
const fileUrl = (rel) => `/episodes/${S.ep.slug}/${rel.split("/").map(encodeURIComponent).join("/")}`;
const filesIn = (dir) => (S.files[dir] || []).filter((f) => !f.name.endsWith(".prompt.txt") && f.name !== ".gitkeep");
const imagesIn = (dir) => filesIn(dir).filter((f) => IMG.test(f.name));
const favOrLatest = (dir) => { const imgs = imagesIn(dir), fav = S.ep.favorites[dir]; return fav && imgs.some((f) => `${dir}/${f.name}` === fav) ? fav : imgs.length ? `${dir}/${imgs[imgs.length - 1].name}` : null; };
const pickFile = (dir, re) => { const fs = filesIn(dir).filter((f) => re.test(f.name)); return fs.length ? fs[fs.length - 1] : null; };

/* ---------- sound ---------- */
let ac = null;
function tone(f, { type = "triangle", dur = .18, vol = .06, at = 0, f2 = null } = {}) {
  if (!S.prefs.sound) return;
  try { ac = ac || new AudioContext(); if (ac.state === "suspended") ac.resume(); } catch { return; }
  const t = ac.currentTime + at, o = ac.createOscillator(), g = ac.createGain();
  o.type = type; o.frequency.setValueAtTime(f, t); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t + dur);
  g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(.0001, t + dur);
  o.connect(g).connect(ac.destination); o.start(t); o.stop(t + dur + .02);
}
const sfx = {
  split: () => [784, 1047, 1319].forEach((f, i) => tone(f, { at: i * .07, dur: .25 })),
  arrive: () => { tone(523, { dur: .12 }); tone(1047, { at: .1, dur: .3, vol: .05 }); },
  stage: () => tone(392, { dur: .12, vol: .04, f2: 587 }),
  stamp: () => { tone(110, { type: "sine", dur: .35, vol: .4, f2: 45 }); tone(220, { type: "square", dur: .06, vol: .05 }); },
  start: () => tone(660, { dur: .1 }),
};

/* ---------- toast ---------- */
let toastT;
function toast(msg, isErr) { const t = $("toast"); t.textContent = msg; t.classList.toggle("error", !!isErr); t.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("show"), isErr ? 5000 : 2400); }

/* ---------- timer ---------- */
function stageMs(n) {
  const t = S.ep?.timer; if (!t) return 0;
  return (t.splits?.[n] || 0) + (t.running && S.ep.stage === n ? Date.now() - t.since : 0);
}
const totalMs = () => STAGES.reduce((a, s) => a + stageMs(s.n), 0);
function fmt(ms, tenths = true) {
  const s = Math.floor(ms / 1000), hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = s % 60;
  const base = hh ? `${hh}:${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}` : `${mm}:${String(ss).padStart(2, "0")}`;
  return tenths ? `${base}.${Math.floor((ms % 1000) / 100)}` : base;
}
function bankTime() { const t = S.ep.timer; if (t.running) { t.splits[S.ep.stage] = (t.splits[S.ep.stage] || 0) + Date.now() - t.since; t.since = Date.now(); } }
function toggleTimer() {
  if (!S.ep) return;
  const t = S.ep.timer;
  if (t.running) { bankTime(); t.running = false; t.since = null; }
  else { t.running = true; t.since = Date.now(); sfx.start(); }
  save(true); tick();
}
function tick() {
  if (!S.ep) return;
  const running = S.ep.timer.running;
  document.body.classList.toggle("running", running);
  $("clockTotal").textContent = fmt(totalMs());
  $("clockSub").textContent = running ? `Stage ${S.ep.stage} · ${fmt(stageMs(S.ep.stage), false)}` : (totalMs() ? "Paused · press T" : "Press T to start the run");
  document.querySelectorAll(".split").forEach((el) => { const n = Number(el.dataset.n); el.querySelector(".t").textContent = stageMs(n) ? fmt(stageMs(n), false) : "—"; });
}
setInterval(tick, 100);

/* ---------- navigation ---------- */
function goStage(n, { silent } = {}) {
  if (!S.ep) return;
  n = Math.max(1, Math.min(7, n));
  if (n !== S.ep.stage) { bankTime(); S.ep.stage = n; save(); if (!silent) sfx.stage(); }
  document.body.dataset.stage = n;
  const st = STAGES[n - 1];
  $("stageKicker").textContent = `Stage ${n} of 7`;
  $("stageName").textContent = st.name;
  renderSplits(); mountStage();
}
function split() {
  if (!S.ep) return;
  const n = S.ep.stage;
  if (!S.ep.done.includes(n)) S.ep.done.push(n);
  sfx.split();
  const el = document.querySelector(`.split[data-n="${n}"]`); el?.classList.remove("flash"); void el?.offsetWidth; el?.classList.add("flash");
  toast(`Split! ${STAGES[n - 1].name} in ${fmt(stageMs(n), false)}`);
  if (n < 7) setTimeout(() => goStage(n + 1, { silent: true }), 350); else { save(); renderSplits(); }
}

/* ---------- splits / evidence rail ---------- */
function evidence(n) {
  const ep = S.ep, ev = h("div", { class: "ev" });
  const img = (rel) => rel && h("img", { src: fileUrl(rel), alt: "" });
  if (n === 1) { if (ep.brief.name) ev.append(h("span", { text: ep.brief.name })); else if (ep.roll.length) ev.append(h("span", { text: ep.roll.map((r) => r.label).join(" · ") })); }
  if (n === 2 || n === 3) {
    const dir = STAGES[n - 1].dir, imgs = imagesIn(dir), rel = favOrLatest(dir);
    if (rel) ev.append(img(rel), h("span", { text: `${imgs.length} image${imgs.length === 1 ? "" : "s"}` }));
  }
  if (n === 4) {
    const shot = imagesIn("4-model").pop(), glb = pickFile("4-model", /\.(glb|gltf)$/i);
    if (shot) ev.append(img(`4-model/${shot.name}`)); if (glb) ev.append(h("span", { text: glb.name }));
  }
  if (n === 5) {
    const shot = imagesIn("5-electronics").pop();
    if (shot) ev.append(img(`5-electronics/${shot.name}`));
    const bits = [pickFile("5-electronics", /\.kicad_sch$/i) && "schematic", pickFile("5-electronics", /\.kicad_pcb$/i) && "board", pickFile("5-electronics", /bom.*\.csv$/i) && "BOM"].filter(Boolean);
    if (bits.length) ev.append(h("span", { text: bits.join(" · ") }));
  }
  if (n === 6 && pickFile("6-showcase", /^index\.html$/i)) ev.append(h("span", { text: "Showcase page ready" }));
  if (n === 7 && ep.decision) ev.append(h("span", { class: "tag " + ep.decision, text: ep.decision === "keep" ? "Keep building" : "Shelved" }));
  return ev;
}
function renderSplits() {
  const box = $("splits"); box.replaceChildren();
  if (!S.ep) return;
  for (const st of STAGES) {
    const cls = ["split", S.ep.stage === st.n && "current", S.ep.done.includes(st.n) && "done", S.arrivals.has(st.dir) && "arrive"].filter(Boolean).join(" ");
    box.append(h("button", { type: "button", class: cls, "data-n": st.n, onclick: () => goStage(st.n) },
      h("span", { class: "n", text: String(st.n).padStart(2, "0") }), h("span", { class: "nm", text: st.name }), h("span", { class: "t", text: "—" }),
      evidence(st.n)));
  }
  tick();
}

/* ---------- stage views ---------- */
function mountStage() {
  const work = $("work"); work.replaceChildren();
  if (!S.ep) return mountWelcome();
  const n = S.ep.stage;
  S.view = ({ 1: viewRoll, 2: () => viewLab("2-concept"), 3: () => viewLab("3-layout"), 4: viewModel, 5: viewElectronics, 6: viewShowcase, 7: viewDecision })[n]();
  work.append(S.view.el);
  S.arrivals.delete(STAGES[n - 1].dir);
}
function mountWelcome() {
  $("work").append(h("div", { class: "stage-view" }, h("div", { class: "empty" },
    h("h2", { text: "Ready when you are." }),
    h("p", { text: "Start an episode to open a fresh run." }),
    h("div", null, h("button", { class: "btn primary big", type: "button", onclick: () => openSheet("episodes"), text: "Start episode" })))));
  S.view = null;
}

// Stage 1: roller + brief
function viewRoll() {
  const ep = S.ep;
  const chips = h("div", { class: "chips" });
  const drawChips = (fresh) => {
    chips.replaceChildren();
    if (!ep.roll.length) chips.append(h("span", { class: "label", text: "Lock in a roll on the left (Enter) and it lands here." }));
    ep.roll.forEach((r, i) => chips.append(h("span", { class: "chip" + (fresh ? " new" : ""), "data-group": r.group || "", style: fresh ? `animation-delay:${i * 90}ms` : null },
      r.label, h("button", { type: "button", "aria-label": "Remove " + r.label, text: "×", onclick: () => { ep.roll.splice(i, 1); save(); drawChips(); renderSplits(); } }))));
  };
  drawChips();
  const field = (key, label, kind = "textarea", ph = "") => {
    const input = kind === "input"
      ? h("input", { id: "brief-" + key, class: key === "name" ? "name" : null, type: "text", value: ep.brief[key] || "", placeholder: ph, autocomplete: "off" })
      : h("textarea", { id: "brief-" + key, placeholder: ph, rows: 2 }, ep.brief[key] || "");
    input.addEventListener("input", () => { ep.brief[key] = input.value; save(); if (key === "name") renderSplits(); });
    return h("label", { class: "field" }, h("span", { class: "label", text: label }), input);
  };
  const el = h("div", { class: "stage-view s1" },
    h("iframe", { class: "roller", src: ROLLER_URL, title: "Random Project Generator", allow: "fullscreen" }),
    h("div", { class: "panel-col" },
      h("div", { class: "label", text: "The roll" }), chips,
      field("name", "Product name", "input", "Name it"),
      field("pitch", "One-line pitch", "textarea", "A ___ that ___ for ___"),
      field("who", "Who it's for", "textarea"),
      field("does", "What it does", "textarea", "The moment someone uses it…"),
      field("electronics", "Electronics notes", "textarea", "Board, sensors, outputs, power…")));
  return { el, refresh() {}, onRoll() { drawChips(true); } };
}
window.addEventListener("message", (e) => {
  if (e.origin !== ROLLER_ORIGIN || !S.ep) return;
  const d = e.data;
  if (!d || d.source !== "rpg" || d.type !== "lockin" || !Array.isArray(d.ingredients)) return;
  S.ep.roll = d.ingredients.slice(0, 12).map((i) => ({ bucket: String(i.bucket || ""), group: String(i.group || ""), label: String(i.label || "").slice(0, 80) })).filter((i) => i.label);
  save(); renderSplits(); S.view?.onRoll?.(); sfx.arrive(); toast("Roll captured");
});

// Stages 2 and 3: image lab
const PRESETS = {
  "2-concept": [
    ["Marker sketch", "Loose product-design concept sketch, black marker and grey copic shading on white sketchbook paper, quick annotations and arrows, not photorealistic."],
    ["Napkin doodle", "Rough ballpoint doodle on a cafe napkin, playful, a few handwritten labels, not photorealistic."],
    ["Storyboard", "Three-panel storyboard sketch showing the product being used, pencil with a single accent color, not photorealistic."],
  ],
  "3-layout": [
    ["Isometric line", "Clean isometric technical illustration, thin black linework on white, semi-transparent enclosure revealing the circuit board, battery and components inside, small callout labels, not photorealistic."],
    ["Exploded view", "Isometric exploded-view diagram, parts separated along vertical axis with dashed guide lines, labeled enclosure shell, PCB, battery, buttons, flat colors, not photorealistic."],
    ["Blueprint", "Isometric blueprint drawing, white lines on blue grid paper, dimension lines and part labels, not photorealistic."],
  ],
};
function basePrompt(dir, style) {
  const b = S.ep.brief, roll = S.ep.roll.map((r) => r.label).join(", ");
  const clean = (t) => String(t || "").trim().replace(/[.!?\s]+$/, "");
  const what = [b.name && `"${clean(b.name)}"`, clean(b.pitch)].filter(Boolean).join(": ") || "a small electronic gadget";
  if (dir === "2-concept") return `${style}\n\nThe product: ${what}.${b.does ? ` ${clean(b.does)}.` : ""}${b.who ? `\nShow it in use by ${clean(b.who).toLowerCase()}.` : ""}${roll ? `\nIngredients: ${roll}.` : ""}`;
  return `${style}\n\nThe product: ${what}.${b.electronics ? `\nInside: ${clean(b.electronics)}.` : ""}${roll ? `\nIngredients: ${roll}.` : ""}\nMatch the shape of the product in the reference sketch.`;
}
function viewLab(dir) {
  const ep = S.ep; ep.prompts = ep.prompts || {};
  const presets = PRESETS[dir];
  let style = ep.prompts[dir + ":style"] ?? 0;
  const ta = h("textarea", { class: "prompt", id: "prompt-" + dir, spellcheck: "true" });
  ta.value = ep.prompts[dir] || basePrompt(dir, presets[style][1]);
  ta.addEventListener("input", () => { ep.prompts[dir] = ta.value; save(); });
  const presetRow = h("div", { class: "row presets" }, presets.map(([name, text], i) => h("button", {
    type: "button", class: "btn", "aria-pressed": String(i === style), text: name,
    onclick: () => { style = i; ep.prompts[dir + ":style"] = i; ta.value = basePrompt(dir, text); ep.prompts[dir] = ta.value; save(); presetRow.querySelectorAll("button").forEach((b, j) => b.setAttribute("aria-pressed", String(j === i))); },
  })));
  const rebuild = h("button", { type: "button", class: "btn ghost", text: "Rebuild from brief", onclick: () => { ta.value = basePrompt(dir, presets[style][1]); ep.prompts[dir] = ta.value; save(); } });

  // References: earlier favorites plus this stage's images
  const refsBox = h("div", { class: "refs" });
  const chosen = new Set(ep.prompts[dir + ":refs"] || (dir === "3-layout" && favOrLatest("2-concept") ? [favOrLatest("2-concept")] : []));
  const drawRefs = () => {
    refsBox.replaceChildren();
    const cands = [];
    if (dir === "3-layout") imagesIn("2-concept").forEach((f) => cands.push(`2-concept/${f.name}`));
    imagesIn(dir).forEach((f) => cands.push(`${dir}/${f.name}`));
    const prov = S.config.providers[providerSel.value];
    if (!cands.length) { refsBox.append(h("span", { class: "hint", text: dir === "3-layout" ? "Concept sketches will appear here as references." : "Generated or dropped images can be used as references for the next one." })); return; }
    cands.slice(-10).forEach((rel) => refsBox.append(h("button", {
      type: "button", class: "ref", "aria-pressed": String(chosen.has(rel)), title: rel,
      onclick: (e) => { chosen.has(rel) ? chosen.delete(rel) : chosen.add(rel); ep.prompts[dir + ":refs"] = [...chosen]; save(); e.currentTarget.setAttribute("aria-pressed", String(chosen.has(rel))); },
    }, h("img", { src: fileUrl(rel), alt: "" }))));
    if (prov && !prov.refs) refsBox.append(h("span", { class: "hint", text: `${prov.label} ignores references.` }));
  };

  const providerSel = h("select", { id: "provider-" + dir, "aria-label": "Image generator" },
    Object.entries(S.config.providers).map(([k, p]) => h("option", { value: k, disabled: !p.ready, selected: k === S.prefs.provider, text: p.label + (p.ready ? "" : " (needs key)") })));
  providerSel.addEventListener("change", () => { S.prefs.provider = providerSel.value; local.set("prefs", S.prefs); drawRefs(); });
  const aspectSel = h("select", { id: "aspect-" + dir, "aria-label": "Aspect ratio" }, ["16:9", "4:3", "1:1", "3:4"].map((a) => h("option", { value: a, text: a })));
  const genBtn = h("button", { type: "button", class: "btn primary big", text: "Generate", onclick: () => generate(dir, ta.value, providerSel.value, aspectSel.value, [...chosen]) });

  const gallery = h("div", { class: "gallery", id: "gallery-" + dir });
  const drawGallery = (fresh = new Set()) => {
    gallery.replaceChildren();
    for (const job of Object.values(S.developing).filter((j) => j.dir === dir))
      gallery.append(h("div", { class: "shot develop" }, h("b", { text: "Developing…" }), h("span", { class: "dev-time", "data-start": job.start, text: "0s" }), h("span", { text: S.config.providers[job.provider]?.label || "" })));
    const imgs = imagesIn(dir).slice().reverse();
    if (!imgs.length && !Object.values(S.developing).some((j) => j.dir === dir))
      gallery.append(h("div", { class: "empty", style: "grid-column:1/-1;min-height:40vh" },
        h("h2", { text: dir === "2-concept" ? "Sketch it." : "Lay it out." }),
        h("p", { text: "Generate on the left, or drag images in from anywhere." })));
    for (const f of imgs) {
      const rel = `${dir}/${f.name}`, fav = ep.favorites[dir] === rel;
      gallery.append(h("div", { class: "shot" + (fav ? " fav" : "") + (fresh.has(rel) ? " reveal" : ""), tabindex: "0", onclick: () => openLightbox(dir, rel), onkeydown: (e) => { if (e.key === "Enter") openLightbox(dir, rel); } },
        h("img", { src: fileUrl(rel), alt: f.name, loading: "lazy" }),
        h("div", { class: "acts" },
          h("button", { type: "button", text: fav ? "★ Favorite" : "☆ Favorite", onclick: (e) => { e.stopPropagation(); setFavorite(dir, rel); } }),
          h("button", { type: "button", text: "Remove", onclick: (e) => { e.stopPropagation(); removeFile(dir, f.name); } }))));
    }
  };
  drawRefs(); drawGallery();

  const el = h("div", { class: "stage-view lab" },
    h("div", { class: "panel-col" },
      h("div", { class: "label", text: "Style" }), presetRow,
      h("div", { class: "row", style: "justify-content:space-between" }, h("span", { class: "label", text: "Prompt" }), rebuild), ta,
      h("div", { class: "selects" }, providerSel, aspectSel), genBtn,
      h("div", { class: "label", text: "References" }), refsBox),
    gallery);
  return { el, refresh(fresh) { drawRefs(); drawGallery(fresh); }, gallery: () => drawGallery() };
}
setInterval(() => document.querySelectorAll(".dev-time").forEach((s) => { s.textContent = Math.floor((Date.now() - Number(s.dataset.start)) / 1000) + "s"; }), 500);

async function generate(dir, prompt, provider, aspect, refs) {
  const id = Math.random().toString(36).slice(2);
  S.developing[id] = { dir, provider, start: Date.now() };
  S.view?.gallery?.();
  try {
    const r = await api(`/episodes/${S.ep.slug}/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ stageDir: dir, provider, prompt, aspect, refs }) });
    delete S.developing[id];
    await reloadFiles(new Set([r.file]));
  } catch (e) {
    delete S.developing[id]; S.view?.gallery?.(); toast(e.message, true);
  }
}
function setFavorite(dir, rel, quiet) {
  S.ep.favorites[dir] = rel; save(); renderSplits(); S.view?.refresh?.();
  if (!quiet) { tone(1175, { dur: .2 }); toast("Favorite set"); }
}
async function removeFile(dir, name) {
  try {
    await api(`/episodes/${S.ep.slug}/files/${dir}/${name.split("/").map(encodeURIComponent).join("/")}`, { method: "DELETE" });
    if (S.ep.favorites[dir] === `${dir}/${name}`) { delete S.ep.favorites[dir]; save(); }
    toast("Removed (kept in the folder's .trash)");
    await reloadFiles();
  } catch (e) { toast(e.message, true); }
}

// Shared bits for stages 4 to 6
function handoffCard(n) {
  const text = handoffPrompt(n);
  return h("div", { class: "handoff" },
    h("div", { class: "row", style: "justify-content:space-between" }, h("span", { class: "label", text: "Hand off to Claude Code" }),
      h("button", { type: "button", class: "btn primary", text: "Copy prompt", onclick: async () => {
        try { await navigator.clipboard.writeText(text); toast("Prompt copied. Paste it into Claude Code."); }
        catch { toast("Copy failed. Select the text and copy it by hand.", true); }
      } })),
    h("pre", { text }));
}
function handoffPrompt(n) {
  const slug = S.ep.slug;
  const imgs = [favOrLatest("2-concept"), favOrLatest("3-layout")].filter(Boolean).map((p) => `episodes/${slug}/${p}`).join(" and ") || "the images in 2-concept and 3-layout";
  if (n === 4) return `Run Stage 4 (3D model) for episode ${slug}, following CLAUDE.md.\nRead episodes/${slug}/episode.json and look at ${imgs}.\nUse Solidcraft to build a rough first-pass model, then save it to episodes/${slug}/4-model/ as model.glb plus an isometric screenshot.`;
  if (n === 5) return `Run Stage 5 (electronics) for episode ${slug}, following CLAUDE.md.\nRead episodes/${slug}/episode.json, the brief's electronics notes, and look at ${imgs} and the model in 4-model/.\nDesign the schematic, KiCad board and BOM in episodes/${slug}/5-electronics/, then export board.glb and a board render.`;
  return `Run Stage 6 (showcase) for episode ${slug}, following CLAUDE.md.\nUse everything in episodes/${slug}/ to build an interactive showcase page at episodes/${slug}/6-showcase/index.html.`;
}
function fileList(dir) {
  const fs = filesIn(dir);
  return h("div", { class: "files" }, fs.length ? fs.map((f) => h("a", { href: fileUrl(`${dir}/${f.name}`), target: "_blank", rel: "noopener", text: f.name })) : h("span", { text: "No files yet." }));
}
function waiting(title, sub) { return h("div", { class: "empty", style: "height:100%" }, h("div", { class: "radar" }), h("h2", { text: title }), h("p", { text: sub })); }

// Stage 4: 3D model
function viewModel() {
  const el = h("div", { class: "stage-view s4" });
  const draw = (fresh = new Set()) => {
    el.replaceChildren();
    const glb = pickFile("4-model", /\.(glb|gltf)$/i), shots = imagesIn("4-model");
    const wrap = h("div", { class: "model-wrap" });
    if (glb) wrap.append(h("model-viewer", { class: fresh.has(`4-model/${glb.name}`) ? "arrive-in" : null, src: fileUrl(`4-model/${glb.name}`) + `?v=${glb.mtime}`, "camera-controls": true, "auto-rotate": true, "shadow-intensity": "1", exposure: "1.1", "interaction-prompt": "none", alt: "3D model" }));
    else wrap.append(waiting("Waiting for the model", "Claude Code and Solidcraft are up. The model appears here the moment it's saved."));
    el.append(wrap, h("div", { class: "panel-col" }, handoffCard(4),
      shots.length ? h("div", { class: "label", text: "Screenshots" }) : null,
      shots.length ? h("div", { class: "thumbs" }, shots.map((f) => h("img", { src: fileUrl(`4-model/${f.name}`), alt: f.name, onclick: () => openLightbox("4-model", `4-model/${f.name}`) }))) : null,
      h("div", { class: "label", text: "Files" }), fileList("4-model")));
  };
  draw();
  return { el, refresh: draw };
}

// Stage 5: electronics
function parseCSV(text) {
  const rows = []; let row = [], cell = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') q = false; else cell += c; }
    else if (c === '"') q = true;
    else if (c === "," || c === ";" && !text.includes(",")) { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(cell); if (row.some((x) => x.trim())) rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  row.push(cell); if (row.some((x) => x.trim())) rows.push(row);
  return rows;
}
function viewElectronics() {
  const el = h("div", { class: "stage-view s5" });
  let tab = local.get("e-tab", "schematic");
  const draw = async (fresh = new Set()) => {
    const proj = pickFile("5-electronics", /\.kicad_pro$/i);
    const schs = filesIn("5-electronics").filter((f) => /\.kicad_sch$/i.test(f.name));
    const sch = (proj && schs.find((f) => f.name === proj.name.replace(/\.kicad_pro$/i, ".kicad_sch"))) || schs[0];
    const pcb = pickFile("5-electronics", /\.kicad_pcb$/i);
    const glb = pickFile("5-electronics", /\.(glb|gltf)$/i);
    const bom = pickFile("5-electronics", /bom.*\.csv$/i) || pickFile("5-electronics", /\.csv$/i);
    const avail = { schematic: sch, board: pcb, "3d": glb, bom };
    if (!avail[tab]) tab = Object.keys(avail).find((k) => avail[k]) || "schematic";
    const tabs = h("div", { class: "tabs", role: "tablist" }, [["schematic", "Schematic"], ["board", "Board"], ["3d", "3D board"], ["bom", "BOM"]].map(([k, label]) =>
      h("button", { type: "button", role: "tab", "aria-selected": String(k === tab), disabled: !avail[k], text: label, onclick: () => { tab = k; local.set("e-tab", k); draw(); } })));
    const body = h("div", { class: "tab-body" });
    const f = avail[tab];
    if (!f) body.append(waiting("Waiting for the circuit", "Schematic, board and BOM appear here as Claude Code writes them."));
    else if (tab === "schematic" || tab === "board") body.append(h("kicanvas-embed", { src: fileUrl(`5-electronics/${f.name}`) + `?v=${f.mtime}`, controls: "basic", theme: "kicad", class: fresh.size ? "arrive-in" : null }));
    else if (tab === "3d") body.append(h("model-viewer", { src: fileUrl(`5-electronics/${f.name}`) + `?v=${f.mtime}`, "camera-controls": true, "auto-rotate": true, "shadow-intensity": "1", "interaction-prompt": "none", alt: "Circuit board", style: "background:radial-gradient(70% 70% at 50% 40%,#173328,#07110D)" }));
    let stats = null;
    if (bom) {
      try {
        const rows = parseCSV(await (await fetch(fileUrl(`5-electronics/${bom.name}`) + `?v=${bom.mtime}`)).text());
        const head = rows[0] || [], data = rows.slice(1);
        const qi = head.findIndex((c) => /^(qty|quantity|count)$/i.test(c.trim()));
        const parts = qi >= 0 ? data.reduce((a, r) => a + (parseFloat(r[qi]) || 0), 0) : data.length;
        stats = h("div", { class: "stat" }, h("div", null, h("b", { text: data.length }), h("span", { text: "BOM lines" })), h("div", null, h("b", { text: parts }), h("span", { text: "Parts" })));
        if (tab === "bom") body.append(h("div", { class: "bom" }, h("table", null,
          h("thead", null, h("tr", null, head.map((c) => h("th", { text: c })))),
          h("tbody", null, data.map((r, i) => h("tr", { style: `animation-delay:${Math.min(i, 30) * 40}ms` }, head.map((_, j) => h("td", { text: r[j] || "" }))))))));
      } catch { if (tab === "bom") body.append(waiting("Couldn't read the BOM", bom.name)); }
    }
    el.replaceChildren(h("div", { class: "view-wrap" }, tabs, body),
      h("div", { class: "panel-col" }, stats, handoffCard(5), h("div", { class: "label", text: "Files" }), fileList("5-electronics")));
  };
  draw();
  return { el, refresh: draw };
}

// Stage 6: showcase
function viewShowcase() {
  const el = h("div", { class: "stage-view s6" });
  const draw = () => {
    const page = pickFile("6-showcase", /^index\.html$/i);
    const url = page && fileUrl("6-showcase/index.html") + `?v=${page.mtime}`;
    el.replaceChildren(
      page ? h("iframe", { class: "showcase-frame arrive-in", src: url, title: "Showcase page" }) : waiting("Waiting for the showcase", "The product page appears here when Claude Code saves 6-showcase/index.html."),
      h("div", { class: "panel-col" }, handoffCard(6),
        page ? h("a", { class: "btn", href: url, target: "_blank", rel: "noopener", text: "Open in a new tab" }) : null,
        h("div", { class: "label", text: "Files" }), fileList("6-showcase")));
  };
  draw();
  return { el, refresh: draw };
}

// Stage 7: decision
function viewDecision() {
  const ep = S.ep;
  const el = h("div", { class: "stage-view s7" });
  const draw = () => {
    const card = (label, body, i) => h("div", { class: "card", style: `animation-delay:${i * 120}ms` }, h("div", { class: "label", text: label }), body);
    const imgOr = (rel, txt) => rel ? h("img", { src: fileUrl(rel), alt: "" }) : h("div", { class: "txt", text: txt });
    const glb = pickFile("4-model", /\.(glb|gltf)$/i), board = pickFile("5-electronics", /\.(glb|gltf)$/i), boardShot = imagesIn("5-electronics").pop();
    const recap = h("div", { class: "recap" },
      card("The idea", h("div", { class: "txt" }, h("b", { text: ep.brief.name || "Untitled" }), h("br"), ep.brief.pitch || ep.roll.map((r) => r.label).join(" · ")), 0),
      card("Concept", imgOr(favOrLatest("2-concept"), "No sketch"), 1),
      card("Layout", imgOr(favOrLatest("3-layout"), "No layout"), 2),
      card("Model", glb ? h("model-viewer", { src: fileUrl(`4-model/${glb.name}`), "auto-rotate": true, "interaction-prompt": "none", alt: "Model" }) : h("div", { class: "txt", text: "No model" }), 3),
      card("Board", board ? h("model-viewer", { src: fileUrl(`5-electronics/${board.name}`), "auto-rotate": true, "interaction-prompt": "none", alt: "Board" }) : imgOr(boardShot && `5-electronics/${boardShot.name}`, "No board"), 4));
    const verdict = h("div", { class: "verdict" },
      h("button", { type: "button", class: "btn big shelve", text: "Shelve it", onclick: () => decide("shelve") }),
      h("div", { class: "final-time" }, "Final time", h("br"), h("b", { text: fmt(totalMs()) })),
      h("button", { type: "button", class: "btn big keep", text: "Keep building", onclick: () => decide("keep") }));
    el.replaceChildren(recap, verdict);
    if (ep.decision) el.append(h("div", { class: "stamp " + ep.decision }, h("span", { text: ep.decision === "keep" ? "Keep building" : "Shelved" })));
  };
  const decide = (d) => {
    if (ep.timer.running) { bankTime(); ep.timer.running = false; ep.timer.since = null; }
    ep.decision = d; ep.decidedAt = new Date().toISOString(); if (!ep.done.includes(7)) ep.done.push(7);
    save(true); sfx.stamp(); draw(); renderSplits();
  };
  draw();
  return { el, refresh: draw };
}

/* ---------- lightbox ---------- */
let lb = null;
function openLightbox(dir, rel) {
  const list = imagesIn(dir).map((f) => `${dir}/${f.name}`).reverse();
  lb = { dir, list, i: Math.max(0, list.indexOf(rel)) };
  showLb(); $("lightbox").hidden = false;
}
async function showLb() {
  const rel = lb.list[lb.i]; if (!rel) return closeLb();
  const img = $("lbImg"); img.src = fileUrl(rel); img.style.animation = "none"; void img.offsetWidth; img.style.animation = "";
  $("lbCap").textContent = (S.ep.favorites[lb.dir] === rel ? "★ Favorite · " : "") + rel.split("/").pop();
  try { const r = await fetch(fileUrl(rel + ".prompt.txt")); if (r.ok) $("lbCap").textContent += " · " + (await r.text()).split("\n\n").slice(1).join(" ").slice(0, 260); } catch {}
}
function closeLb() { $("lightbox").hidden = true; lb = null; }
$("lightbox").addEventListener("click", closeLb);

/* ---------- drag and drop ---------- */
let dragDepth = 0;
const dropDir = () => S.ep && STAGES[S.ep.stage - 1].dir;
document.addEventListener("dragenter", (e) => { if (!e.dataTransfer?.types?.includes("Files") || !dropDir()) return; dragDepth++; $("dropTarget").textContent = STAGES[S.ep.stage - 1].name; $("dropveil").hidden = false; });
document.addEventListener("dragleave", () => { if (--dragDepth <= 0) { dragDepth = 0; $("dropveil").hidden = true; } });
document.addEventListener("dragover", (e) => { if (dropDir()) e.preventDefault(); });
document.addEventListener("drop", async (e) => {
  e.preventDefault(); dragDepth = 0; $("dropveil").hidden = true;
  const dir = dropDir(); if (!dir) return toast("Drop files on stages 2 to 6.", true);
  const files = [...(e.dataTransfer?.files || [])]; if (!files.length) return;
  const added = new Set();
  for (const f of files) {
    try { const r = await api(`/episodes/${S.ep.slug}/files/${dir}?name=${encodeURIComponent(f.name)}`, { method: "POST", body: f }); added.add(r.file); }
    catch (err) { toast(`${f.name}: ${err.message}`, true); }
  }
  if (added.size) { toast(`Added ${added.size} file${added.size === 1 ? "" : "s"}`); await reloadFiles(added); }
});

/* ---------- loading and live updates ---------- */
async function loadEpisode(slug) {
  const r = await api(`/episodes/${slug}`);
  S.ep = r.episode; S.files = r.files;
  S.ep.timer = S.ep.timer || { running: false, since: null, splits: {} }; S.ep.timer.splits = S.ep.timer.splits || {};
  S.ep.done = S.ep.done || []; S.ep.favorites = S.ep.favorites || {}; S.ep.roll = S.ep.roll || [];
  S.ep.brief = { name: "", pitch: "", who: "", does: "", electronics: "", ...(S.ep.brief || {}) };
  local.set("last", slug);
  $("epNum").textContent = "#" + String(S.ep.number || "").padStart(3, "0");
  $("epTitle").textContent = S.ep.title;
  document.title = `${S.ep.title} · Product Speedrun`;
  goStage(S.ep.stage || 1, { silent: true });
}
async function reloadFiles(fresh = new Set()) {
  if (!S.ep) return;
  const before = new Set(Object.entries(S.files).flatMap(([d, fs]) => fs.map((f) => `${d}/${f.name}:${f.mtime}`)));
  const r = await api(`/episodes/${S.ep.slug}`);
  S.files = r.files;
  const changed = new Set(fresh);
  for (const [d, fs] of Object.entries(S.files)) for (const f of fs) if (!before.has(`${d}/${f.name}:${f.mtime}`) && !f.name.endsWith(".prompt.txt")) changed.add(`${d}/${f.name}`);
  const cur = STAGES[S.ep.stage - 1].dir;
  for (const rel of changed) { const d = rel.split("/")[0]; if (d !== cur) S.arrivals.add(d); }
  for (const d of ["2-concept", "3-layout"]) if (!imagesIn(d).some((f) => `${d}/${f.name}` === S.ep.favorites[d])) {
    const newest = [...changed].filter((r) => r.startsWith(d + "/") && IMG.test(r)).pop();
    if (newest) { S.ep.favorites[d] = newest; save(); }
  }
  renderSplits();
  if (changed.size) S.view?.refresh?.(changed);
  return changed;
}
let reloadT = null;
function listen() {
  const es = new EventSource("/api/events");
  es.onmessage = (m) => {
    let e; try { e = JSON.parse(m.data); } catch { return; }
    if (!S.ep || e.slug !== S.ep.slug || !e.dir || e.dir === "episode.json") return;
    clearTimeout(reloadT);
    reloadT = setTimeout(async () => {
      const changed = await reloadFiles();
      const external = changed && [...changed].filter((r) => !r.endsWith(".prompt.txt"));
      if (external?.length) { sfx.arrive(); toast("New: " + external.slice(0, 3).map((r) => r.split("/").pop()).join(", ")); }
    }, 600);
  };
}

/* ---------- sheets: episodes and settings ---------- */
function openSheet(id) {
  if (id === "episodes") drawEpisodes();
  if (id === "settings") drawSettings();
  $(id).hidden = false;
  $(id).querySelector("input, button")?.focus();
}
function closeSheets() { ["episodes", "settings"].forEach((id) => { $(id).hidden = true; }); }
document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", closeSheets));
document.querySelectorAll(".sheet").forEach((s) => s.addEventListener("click", (e) => { if (e.target === s) closeSheets(); }));
async function drawEpisodes() {
  const list = $("epList"); list.replaceChildren(h("span", { class: "hint", text: "Loading…" }));
  try { S.episodes = await api("/episodes"); } catch (e) { list.replaceChildren(h("span", { class: "hint", text: e.message })); return; }
  list.replaceChildren(...(S.episodes.length ? S.episodes.map((e) => h("button", { type: "button", onclick: async () => { closeSheets(); await loadEpisode(e.slug); } },
    h("span", { class: "tag", text: "#" + String(e.number).padStart(3, "0") }), h("span", { class: "nm", text: e.title }),
    h("span", { class: "tag " + (e.decision || ""), text: e.decision === "keep" ? "Keep" : e.decision === "shelve" ? "Shelved" : `Stage ${e.stage}` }))) : [h("span", { class: "hint", text: "No episodes yet." })]));
}
$("newEp").addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = $("newEpTitle").value.trim(); if (!title) return $("newEpTitle").focus();
  try { const ep = await api("/episodes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title }) }); $("newEpTitle").value = ""; closeSheets(); await loadEpisode(ep.slug); toast("Episode started"); }
  catch (err) { toast(err.message, true); }
});
function drawSettings() {
  $("providerList").replaceChildren(...Object.values(S.config.providers).map((p) => h("div", null, h("span", { text: p.label + (p.model ? ` · ${p.model}` : "") }), h("span", { class: p.ready ? "ok" : "no", text: p.ready ? "Ready" : "Needs key" }))));
  $("safe-" + S.prefs.safe).checked = true; $("showSafe").checked = S.prefs.showSafe; $("soundOn").checked = S.prefs.sound;
}
document.querySelectorAll("input[name=safe]").forEach((r) => r.addEventListener("change", () => { S.prefs.safe = r.value; local.set("prefs", S.prefs); applyPrefs(); }));
$("showSafe").addEventListener("change", (e) => { S.prefs.showSafe = e.target.checked; local.set("prefs", S.prefs); applyPrefs(); });
$("soundOn").addEventListener("change", (e) => { S.prefs.sound = e.target.checked; local.set("prefs", S.prefs); });
function applyPrefs() {
  document.body.classList.remove("safe-bottom", "safe-left", "safe-right");
  if (S.prefs.safe !== "none") document.body.classList.add("safe-" + S.prefs.safe);
  const o = $("safeOutline"); o.hidden = !(S.prefs.showSafe && S.prefs.safe !== "none");
  const box = { bottom: "left:0;right:0;bottom:0;height:21vh", left: "left:0;top:0;bottom:0;width:24vw", right: "right:0;top:0;bottom:0;width:24vw" }[S.prefs.safe];
  if (box) o.style.cssText = box;
}

/* ---------- keyboard ---------- */
function typing() { const a = document.activeElement; return a && (a.tagName === "INPUT" || a.tagName === "TEXTAREA" || a.tagName === "SELECT" || a.isContentEditable); }
document.addEventListener("keydown", (e) => {
  if (!$("lightbox").hidden) {
    if (e.key === "Escape") closeLb();
    else if (e.key === "ArrowRight") { lb.i = Math.min(lb.list.length - 1, lb.i + 1); showLb(); }
    else if (e.key === "ArrowLeft") { lb.i = Math.max(0, lb.i - 1); showLb(); }
    else if (e.key.toLowerCase() === "f") { setFavorite(lb.dir, lb.list[lb.i]); showLb(); }
    return;
  }
  if (e.key === "Escape") { closeSheets(); document.activeElement?.blur?.(); return; }
  if (typing() || e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (e.key === "ArrowRight") goStage((S.ep?.stage || 1) + 1);
  else if (e.key === "ArrowLeft") goStage((S.ep?.stage || 1) - 1);
  else if (k === "t") toggleTimer();
  else if (k === "n") split();
  else if (k === "e") openSheet("episodes");
  else if (k === ",") openSheet("settings");
  else if (k === "f") { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.().catch(() => {}); }
  else if (/^[1-7]$/.test(k)) goStage(Number(k));
});
$("epBtn").addEventListener("click", () => openSheet("episodes"));
$("clock").addEventListener("click", toggleTimer);
let idleT; document.addEventListener("mousemove", () => { document.body.classList.remove("idle"); clearTimeout(idleT); idleT = setTimeout(() => document.body.classList.add("idle"), 3000); });

/* ---------- boot ---------- */
(async () => {
  applyPrefs();
  try { S.config = await api("/config"); } catch { toast("Can't reach the local server. Is npm start running?", true); return; }
  if (!S.config.providers[S.prefs.provider]?.ready) S.prefs.provider = "pollinations";
  listen();
  S.episodes = await api("/episodes").catch(() => []);
  const last = local.get("last", null);
  const pick = S.episodes.find((e) => e.slug === last) || S.episodes[0];
  if (pick) await loadEpisode(pick.slug); else { mountStage(); renderSplits(); }
})();
