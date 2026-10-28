#!/bin/sh
# Exports for the dashboard: bom.csv, schematic.png, board renders, board.glb.
# Usage: tools/export.sh   (tools/build.sh calls it last)
set -e
cd "$(dirname "$0")/.."
CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
P=backpack-defender
python3 -I tools/make_bom.py output/$P.net > bom.csv
"$CLI" sch export pdf -o output/$P-schematic.pdf $P.kicad_sch
qlmanage -t -s 3000 -o output output/$P-schematic.pdf >/dev/null 2>&1
mv output/$P-schematic.pdf.png schematic.png
"$CLI" pcb render --side top --quality high --width 2000 --height 1400 --zoom 1.0 -o board.png $P.kicad_pcb
"$CLI" pcb render --side bottom --quality high --width 2000 --height 1400 --zoom 1.0 -o board-bottom.png $P.kicad_pcb
"$CLI" pcb render --quality high --width 2000 --height 1400 --rotate '-50,0,-30' --perspective --zoom 0.9 -o board-iso.png $P.kicad_pcb
"$CLI" pcb export glb -f --subst-models --include-tracks --include-pads --include-zones --include-silkscreen \
  --include-soldermask -o output/board-raw.glb $P.kicad_pcb
python3 tools/glb_to_meters.py output/board-raw.glb board.glb
