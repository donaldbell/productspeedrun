// Small helpers shared by every showcase page (loaded from ../../../kit/showcase.js).
//  - <div data-bom="../5-electronics/bom.csv"> fills itself with the BOM table; [data-bom-count] gets the line count.
//  - <button data-load-model="../5-electronics/board.glb" data-alt="..."> swaps itself for a 3D viewer (big files load on demand).
//  - <button data-orbit="0deg 75deg auto" data-target="#enclosure"> turns a model-viewer to that view.
//  - [data-verdict] shows the keep-or-shelve decision from ../episode.json.

const csvRows = (text) => {
  const rows = []; let row = [], cell = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') q = false; else cell += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(cell); if (row.some((v) => v !== "")) rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  row.push(cell); if (row.some((v) => v !== "")) rows.push(row);
  return rows;
};
const el = (tag, text) => { const e = document.createElement(tag); if (text != null) e.textContent = text; return e; };

for (const box of document.querySelectorAll("[data-bom]")) {
  fetch(box.dataset.bom).then((r) => (r.ok ? r.text() : Promise.reject())).then((text) => {
    const [head, ...rows] = csvRows(text);
    const col = (name) => head.indexOf(name);
    const cols = ["Ref", "Qty", "Value", "Description", "MPN"].filter((c) => col(c) >= 0);
    const table = el("table"), thead = el("thead"), tr = el("tr");
    cols.forEach((c) => tr.append(el("th", c === "Value" ? "Part" : c)));
    thead.append(tr); table.append(thead);
    const tbody = el("tbody");
    for (const r of rows) {
      const row = el("tr");
      cols.forEach((c) => { const td = el("td", r[col(c)] || ""); if (c === "MPN") td.className = "mono"; row.append(td); });
      tbody.append(row);
    }
    table.append(tbody); box.replaceChildren(table);
    document.querySelectorAll("[data-bom-count]").forEach((n) => (n.textContent = rows.length));
  }).catch(() => { box.textContent = "The parts list isn't available here."; });
}

for (const btn of document.querySelectorAll("[data-load-model]")) {
  btn.addEventListener("click", () => {
    const mv = document.createElement("model-viewer");
    mv.setAttribute("src", btn.dataset.loadModel);
    mv.setAttribute("alt", btn.dataset.alt || "3D model");
    mv.setAttribute("camera-controls", "");
    mv.setAttribute("auto-rotate", "");
    mv.setAttribute("shadow-intensity", "0.6");
    mv.setAttribute("interaction-prompt", "none");
    (btn.closest(".load") || btn).replaceWith(mv);
  });
}

for (const btn of document.querySelectorAll("[data-orbit]")) {
  btn.addEventListener("click", () => {
    const mv = document.querySelector(btn.dataset.target);
    if (!mv) return;
    mv.cameraOrbit = btn.dataset.orbit;
    mv.autoRotate = false;
    btn.parentElement.querySelectorAll("[data-orbit]").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
  });
}

const verdicts = document.querySelectorAll("[data-verdict]");
if (verdicts.length) {
  fetch("../episode.json").then((r) => (r.ok ? r.json() : Promise.reject())).then((ep) => {
    const [text, cls] = ep.decision === "keep" ? ["Keep building", "keep"] : ep.decision === "shelve" ? ["Shelved", "shelve"] : ["Still deciding", "open"];
    verdicts.forEach((v) => { v.textContent = text; v.classList.remove("keep", "shelve", "open"); v.classList.add(cls); });
  }).catch(() => {});
}
