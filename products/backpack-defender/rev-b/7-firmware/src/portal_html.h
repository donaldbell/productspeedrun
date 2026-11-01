// The setup page served in setup mode. Plain HTML/JS, no external files (the phone has no internet here).
#pragma once
#include <pgmspace.h>

static const char PORTAL_HTML[] PROGMEM = R"HTML(<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Backpack Defender</title>
<style>
:root{--mint:#9fe3c9;--mint2:#e8faf3;--ink:#23324a;--purple:#7b4fd6;--card:#fff;--muted:#5b6b80}
@media (prefers-color-scheme:dark){:root{--mint2:#14231e;--ink:#e9f6f0;--card:#1f3029;--muted:#9fb3aa}}
*{box-sizing:border-box}
body{margin:0;font:17px/1.4 ui-rounded,"Arial Rounded MT Bold",system-ui,sans-serif;background:var(--mint2);color:var(--ink)}
header{background:var(--mint);color:#23324a;padding:18px 16px 14px;text-align:center;border-radius:0 0 28px 28px}
.face{font-size:42px;line-height:1}
h1{margin:6px 0 0;font-size:24px}
main{max-width:560px;margin:0 auto;padding:8px 16px 110px}
h2{font-size:19px;margin:22px 0 8px}
h3{font-size:14px;margin:14px 0 6px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.snd{display:flex;align-items:center;gap:8px;background:var(--card);border:3px solid transparent;border-radius:16px;
 padding:10px;cursor:pointer;min-height:56px}
.snd.on{border-color:var(--purple)}
.snd .e{font-size:26px}
.snd .n{flex:1;font-size:15px}
.snd button{border:0;background:var(--mint);color:#23324a;border-radius:50%;width:36px;height:36px;font-size:15px;cursor:pointer}
.sw{display:flex;flex-wrap:wrap;gap:10px}
.sw button{width:52px;height:52px;border-radius:50%;border:4px solid var(--card);cursor:pointer;box-shadow:0 0 0 2px #0002}
.sw button.on{box-shadow:0 0 0 4px var(--purple)}
.rain{background:conic-gradient(red,orange,yellow,lime,cyan,blue,magenta,red)}
label{display:block;margin:12px 0 4px}
input[type=range]{width:100%;accent-color:var(--purple)}
details{background:var(--card);border-radius:16px;padding:10px 14px;margin-top:18px}
summary{cursor:pointer;font-weight:bold}
.save{position:fixed;left:0;right:0;bottom:0;padding:12px 16px;background:linear-gradient(transparent,var(--mint2) 30%)}
.save button{display:block;width:100%;max-width:560px;margin:0 auto;padding:16px;font:inherit;font-size:20px;
 border:0;border-radius:20px;background:var(--purple);color:#fff;cursor:pointer}
#msg{text-align:center;color:var(--muted)}
</style></head><body>
<header><div class="face">• ᴗ •</div><h1>Backpack Defender</h1><div id="name"></div></header>
<main>
<h2>1. Pick your alarm sound</h2>
<p id="msg">Tap ▶ to hear it on your Defender.</p>
<div id="sounds"></div>
<h2>2. Pick your button colour</h2>
<div class="sw" id="colors"></div>
<label for="bright">Glow brightness</label>
<input type="range" id="bright" min="2" max="60">
<details><summary>Extras</summary>
<label for="volume">Volume: <b id="volv"></b></label><input type="range" id="volume" min="1" max="5">
<label for="alarm">Alarm length: <b id="alarmv"></b> s</label><input type="range" id="alarm" min="3" max="30">
<label for="cool">Quiet time after the button: <b id="coolv"></b> s</label><input type="range" id="cool" min="10" max="300" step="10">
</details>
</main>
<div class="save"><button id="save">Save &amp; start guarding!</button></div>
<script>
const COLORS=["ff2a2a","ff8a00","ffd400","38e05a","2fe0b0","19c3ff","2f5bff","8a3dff","ff4fc3","ffffff"];
let S={};const $=id=>document.getElementById(id);
function q(o){return Object.entries(o).map(([k,v])=>k+"="+encodeURIComponent(v)).join("&")}
function light(){fetch("/api/light?"+q({c:S.color,r:S.rainbow?1:0,b:S.bright}))}
function draw(){
 const box=$("sounds");box.innerHTML="";let fam="";let grid;
 S.sounds.forEach(s=>{
  if(s.f!==fam){fam=s.f;const h=document.createElement("h3");h.textContent=fam;box.appendChild(h);
   grid=document.createElement("div");grid.className="grid";box.appendChild(grid)}
  const d=document.createElement("div");d.className="snd"+(s.k===S.sound?" on":"");
  d.innerHTML='<span class="e">'+s.e+'</span><span class="n">'+s.n+'</span><button aria-label="Play">▶</button>';
  d.onclick=()=>{S.sound=s.k;draw()};
  d.querySelector("button").onclick=ev=>{ev.stopPropagation();S.sound=s.k;draw();
   fetch("/api/preview?"+q({k:s.k,v:S.volume}))};
  grid.appendChild(d)});
 const c=$("colors");c.innerHTML="";
 COLORS.concat(["rainbow"]).forEach(h=>{const b=document.createElement("button");
  const on=h==="rainbow"?S.rainbow:(!S.rainbow&&h===S.color);
  b.className=(h==="rainbow"?"rain":"")+(on?" on":"");if(h!=="rainbow")b.style.background="#"+h;
  b.setAttribute("aria-label",h==="rainbow"?"Rainbow":"#"+h);
  b.onclick=()=>{if(h==="rainbow")S.rainbow=true;else{S.rainbow=false;S.color=h}draw();light()};c.appendChild(b)});
 for(const k of ["bright","volume","alarm","cool"])$(k).value=S[k];
 $("volv").textContent=S.volume;$("alarmv").textContent=S.alarm;$("coolv").textContent=S.cool}
for(const k of ["bright","volume","alarm","cool"])$(k).oninput=e=>{S[k]=+e.target.value;draw();if(k==="bright")light()};
$("save").onclick=()=>{fetch("/api/save",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},
 body:q({sound:S.sound,color:S.color,rainbow:S.rainbow?1:0,bright:S.bright,volume:S.volume,alarm:S.alarm,cool:S.cool})})
 .then(()=>{document.body.innerHTML='<header><div class="face">• ᴗ •</div><h1>Saved! On guard.</h1></header>'})};
fetch("/api/state").then(r=>r.json()).then(j=>{S=j;$("name").textContent=j.name;draw();light()});
</script></body></html>)HTML";
