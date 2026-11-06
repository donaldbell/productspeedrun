#!/usr/bin/env python3
"""Put the concept art, the layout sheet and the model side by side, so Stage 4 can check its form.

  python3 tools/form/compare.py episodes/<slug> [--shot 4-model/blockout-02.png] [--out 4-model/compare.png]
  python3 tools/form/compare.py products/<product>/rev-b

Reads the favourites from episode.json (or, for a revision, rev.json's previous hero and the episode's
concept art). The model image is --shot, else the newest blockout-*.png, else iso.png. Needs Pillow
(pip3 install pillow).
"""
import argparse
import glob
import json
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("compare.py needs Pillow: pip3 install pillow")

H = 720          # height of each panel
LABEL = 44       # label strip under each panel
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def refs(folder):
    """[(label, path)] for the concept art and layout sheet (or the previous hero, for a revision)."""
    out = []
    ep_json = os.path.join(folder, "episode.json")
    rev_json = os.path.join(folder, "rev.json")
    if os.path.isfile(ep_json):
        fav = json.load(open(ep_json)).get("favorites", {})
        for key, label in (("2-concept", "Concept art"), ("3-layout", "Layout sheet")):
            if fav.get(key) and os.path.isfile(os.path.join(folder, fav[key])):
                out.append((label, os.path.join(folder, fav[key])))
    elif os.path.isfile(rev_json):
        r = json.load(open(rev_json))
        prev = r.get("previousHero")
        if prev and os.path.isfile(os.path.join(REPO, prev.lstrip("/"))):
            out.append(("Previous hero render", os.path.join(REPO, prev.lstrip("/"))))
        ep = os.path.join(REPO, "episodes", r.get("episode", ""))
        if os.path.isfile(os.path.join(ep, "episode.json")):
            fav = json.load(open(os.path.join(ep, "episode.json"))).get("favorites", {})
            if fav.get("2-concept") and os.path.isfile(os.path.join(ep, fav["2-concept"])):
                out.append(("Concept art (Rev A)", os.path.join(ep, fav["2-concept"])))
    return out


def model_shot(folder, shot):
    if shot:
        p = shot if os.path.isabs(shot) else os.path.join(folder, shot)
        if not os.path.isfile(p):
            sys.exit("no such screenshot: " + p)
        return p
    blocks = sorted(glob.glob(os.path.join(folder, "4-model", "blockout-*.png")), key=os.path.getmtime)
    if blocks:
        return blocks[-1]
    iso = os.path.join(folder, "4-model", "iso.png")
    return iso if os.path.isfile(iso) else None


def font(size):
    for f in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.isfile(f):
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                pass
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--shot")
    ap.add_argument("--out", default="4-model/compare.png")
    a = ap.parse_args()
    folder = os.path.abspath(a.folder)
    panels = refs(folder)
    shot = model_shot(folder, a.shot)
    if not shot:
        sys.exit("no model screenshot yet: save 4-model/blockout-01.png or iso.png first")
    panels.append(("Model: " + os.path.basename(shot), shot))
    imgs = []
    for label, p in panels:
        im = Image.open(p).convert("RGB")
        im = im.resize((max(1, round(im.width * H / im.height)), H))
        imgs.append((label, im))
    W = sum(im.width for _, im in imgs) + 16 * (len(imgs) + 1)
    sheet = Image.new("RGB", (W, H + LABEL + 32), "white")
    d, f, x = ImageDraw.Draw(sheet), font(26), 16
    for label, im in imgs:
        sheet.paste(im, (x, 16))
        d.text((x, H + 24), label, fill=(30, 30, 30), font=f)
        x += im.width + 16
    out = a.out if os.path.isabs(a.out) else os.path.join(folder, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print("wrote", os.path.relpath(out, os.getcwd()))


if __name__ == "__main__":
    main()
