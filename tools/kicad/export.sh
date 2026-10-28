#!/bin/sh
# Pictures and 3D for the dashboard. build.sh calls this; run it alone after editing in KiCad.
#   tools/kicad/export.sh <episode> schematic     schematic.png
#   tools/kicad/export.sh <episode> board-quick   board.png only (fast, for the placed board)
#   tools/kicad/export.sh <episode> board         board.png, board-bottom.png, board-iso.png, board.glb
#   tools/kicad/export.sh <episode>               all of the above, plus bom.csv
set -e
KIT=$(cd "$(dirname "$0")" && pwd)
E=$(cd "$1" && pwd)
case "$E" in */5-electronics) ;; *) E="$E/5-electronics" ;; esac
cd "$E"
WHAT=${2:-all}
CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
P=$(python3 -I "$KIT/gen_schematic.py" "$E" --name)
mkdir -p output

if [ "$WHAT" = all ]; then
  "$CLI" sch export netlist -o output/$P.net $P.kicad_sch
  python3 -I "$KIT/make_bom.py" "$E" output/$P.net > bom.csv
fi
if [ "$WHAT" = all ] || [ "$WHAT" = schematic ]; then
  "$CLI" sch export pdf -o output/$P-schematic.pdf $P.kicad_sch
  if command -v qlmanage >/dev/null 2>&1; then
    qlmanage -t -s 3000 -o output output/$P-schematic.pdf >/dev/null 2>&1 && mv output/$P-schematic.pdf.png schematic.png
  elif command -v pdftoppm >/dev/null 2>&1; then
    pdftoppm -png -r 200 -singlefile output/$P-schematic.pdf schematic
  else
    echo "no qlmanage or pdftoppm: schematic.png skipped (the PDF is in output/)"
  fi
fi
if [ "$WHAT" = board-quick ]; then
  "$CLI" pcb render --side top --quality basic --width 1600 --height 1100 --zoom 1.0 -o board.png $P.kicad_pcb
fi
if [ "$WHAT" = all ] || [ "$WHAT" = board ]; then
  "$CLI" pcb render --side top --quality high --width 2000 --height 1400 --zoom 1.0 -o board.png $P.kicad_pcb
  "$CLI" pcb render --side bottom --quality high --width 2000 --height 1400 --zoom 1.0 -o board-bottom.png $P.kicad_pcb
  "$CLI" pcb render --quality high --width 2000 --height 1400 --rotate '-50,0,-30' --perspective --zoom 0.9 -o board-iso.png $P.kicad_pcb
  "$CLI" pcb export glb -f --subst-models --include-tracks --include-pads --include-zones --include-silkscreen \
    --include-soldermask -o output/board-raw.glb $P.kicad_pcb
  python3 "$KIT/glb_to_meters.py" output/board-raw.glb board.glb
fi
