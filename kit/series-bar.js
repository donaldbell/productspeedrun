// <ps-series-bar>: the strip at the top of every showcase page that says "this is Product Speedrun"
// and links back to the gallery and to the episodes either side. Shadow DOM, so it looks the same on
// any page whatever that page's own styles are. The public site build fills in its attributes:
//   <ps-series-bar home="../../../" number="2" name="Gamer Guardian"
//                  prev="../../001-demo-1/6-showcase/" prev-name="Backpack Defender" next="" next-name=""></ps-series-bar>
// Without them it still links home and reads the episode number from the URL.
// Products with revisions also get revs="A:episodes/001-x/6-showcase/;B:products/x/rev-b/6-showcase/" (pages
// relative to home) and rev="A" (this page): a Rev A · Rev B switcher, plus a link to the newest from older pages.
class SeriesBar extends HTMLElement {
  connectedCallback() {
    const a = (k) => this.getAttribute(k) || "";
    const home = a("home") || "../../../";
    const m = /episodes\/(\d+)/.exec(location.pathname);
    const num = a("number") || (m ? String(Number(m[1])) : "");
    const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    const link = (href, label, cls, aria) => href
      ? `<a class="${cls}" href="${esc(href)}" aria-label="${esc(aria)}">${label}</a>` : "";
    const revs = a("revs").split(";").filter(Boolean).map((x) => { const i = x.indexOf(":"); return { letter: x.slice(0, i), href: home + x.slice(i + 1) }; });
    const cur = a("rev"), latest = revs[revs.length - 1];
    const switcher = revs.length > 1 ? `<span class="revs" role="group" aria-label="Versions">${revs.map((r) => r.letter === cur
      ? `<a class="rev on" href="${esc(r.href)}" aria-current="page">Rev ${esc(r.letter)}</a>`
      : `<a class="rev" href="${esc(r.href)}">Rev ${esc(r.letter)}</a>`).join("")}</span>` : "";
    const newer = latest && cur && latest.letter !== cur
      ? `<a class="newer" href="${esc(latest.href)}"><span class="long">Newer:&nbsp;</span>Rev ${esc(latest.letter)} →</a>` : "";
    const root = this.attachShadow({ mode: "open" });
    root.innerHTML = `
<style>
:host { display: block; background: #0C0F14; color: #F3EFE6; font: 500 14px/1.2 "Instrument Sans", system-ui, -apple-system, "Segoe UI", sans-serif; position: relative; z-index: 50; }
nav { max-width: 1160px; margin: 0 auto; padding: 0 16px; min-height: 48px; display: flex; align-items: center; gap: 16px; }
a { color: inherit; text-decoration: none; border-radius: 6px; }
a:focus-visible { outline: 3px solid #F6C14B; outline-offset: 2px; }
.home { display: inline-flex; align-items: center; gap: 10px; min-height: 44px; font: 800 16px/1 "Bricolage Grotesque", "Avenir Next", system-ui, sans-serif; letter-spacing: -0.01em; }
.home svg { flex: none; }
.home b { color: #63E39A; font-weight: 800; }
.home:hover .all { text-decoration: underline; }
.all { font: 500 13px/1 "Instrument Sans", system-ui, sans-serif; color: #8C96A8; letter-spacing: 0; }
.ep { margin-left: auto; color: #8C96A8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
.ep b { color: #F3EFE6; font-weight: 600; }
.step { display: inline-grid; place-items: center; min-width: 44px; min-height: 44px; color: #F3EFE6; font-size: 18px; }
.step:hover { color: #63E39A; }
nav:has(.revs) .home { flex: none; }
.revs { display: inline-flex; gap: 2px; padding: 2px; border: 1px solid #2A3140; border-radius: 999px; flex: none; }
.rev { display: inline-grid; place-items: center; min-height: 28px; padding: 0 10px; border-radius: 999px; font-size: 13px; color: #8C96A8; white-space: nowrap; }
.rev:hover { color: #F3EFE6; }
.rev.on { background: #F3EFE6; color: #0C0F14; font-weight: 600; }
.newer { display: inline-flex; align-items: center; min-height: 32px; padding: 0 12px; border-radius: 999px; background: #63E39A; color: #0C0F14; font-weight: 600; white-space: nowrap; flex: none; }
.newer:hover { background: #8BF0B5; }
@media (max-width: 560px) { .all { display: none; } .ep .name { display: none; } .newer .long { display: none; } nav { gap: 8px; } }
@media (max-width: 400px) { nav:has(.revs) .ep { display: none; } .revs, .newer { margin-left: auto; } .revs:has(+ .newer) { display: none; } }
</style>
<nav aria-label="Product Speedrun">
  <a class="home" href="${esc(home)}">
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><rect x="1" y="1" width="20" height="20" rx="5" fill="none" stroke="#63E39A" stroke-width="2"/><circle cx="7" cy="7" r="1.8" fill="#F6C14B"/><circle cx="11" cy="11" r="1.8" fill="#F6C14B"/><circle cx="15" cy="15" r="1.8" fill="#F6C14B"/></svg>
    <span>Product <b>Speedrun</b></span><span class="all">All episodes</span>
  </a>
  <span class="ep">${num ? `Episode <b>${esc(num.padStart(3, "0"))}</b>` : ""}${a("name") ? `<span class="name"> · ${esc(a("name"))}</span>` : ""}</span>
  ${switcher}${newer}
  ${link(a("prev"), "‹", "step", "Previous episode" + (a("prev-name") ? ": " + a("prev-name") : ""))}
  ${link(a("next"), "›", "step", "Next episode" + (a("next-name") ? ": " + a("next-name") : ""))}
</nav>`;
  }
}
if (!customElements.get("ps-series-bar")) customElements.define("ps-series-bar", SeriesBar);
