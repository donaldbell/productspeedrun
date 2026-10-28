#!/bin/sh
# Build an episode's electronics from 5-electronics/src/design.py and src/layout.py.
#
#   tools/kicad/build.sh episodes/002-plant-whisperer             everything (about 5-15 min, mostly routing)
#   tools/kicad/build.sh episodes/002-plant-whisperer schematic   schematic, ERC, netlist check, BOM, schematic.png
#   tools/kicad/build.sh episodes/002-plant-whisperer place       ...plus the placed (unrouted) board and board.png
#
# Each step saves into 5-electronics/ as it goes, so the dashboard shows the schematic, then the
# placed board, then the routed board. Machine paths: KICAD_CLI, KICAD_PY, KICAD_SHARE, JAVA,
# FREEROUTING_JAR (defaults are the macOS KiCad app and ~/.local/opt/freerouting).
set -e
KIT=$(cd "$(dirname "$0")" && pwd)
[ -n "$1" ] || { echo "usage: $0 <episode folder> [schematic|place|all]"; exit 2; }
MODE=${2:-all}
E=$(cd "$1" && pwd)
case "$E" in */5-electronics) ;; *) E="$E/5-electronics" ;; esac
cd "$E"
CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
command -v "$CLI" >/dev/null 2>&1 || { echo "kicad-cli not found at $CLI: set KICAD_CLI"; exit 1; }
step() { printf '\n== %s\n' "$*"; }

step "schematic"
python3 -I "$KIT/gen_schematic.py" "$E"
P=$(python3 -I "$KIT/gen_schematic.py" "$E" --name)
mkdir -p output
step "ERC"
"$CLI" sch erc --severity-all --exit-code-violations -o erc.rpt $P.kicad_sch || { cat erc.rpt; exit 1; }
"$CLI" sch export netlist -o output/$P.net $P.kicad_sch
python3 -I "$KIT/check_netlist.py" "$E" output/$P.net
python3 -I "$KIT/make_bom.py" "$E" output/$P.net > bom.csv
sh "$KIT/export.sh" "$E" schematic
[ "$MODE" = schematic ] && exit 0

step "placement"
"$PY" "$KIT/gen_pcb.py" "$E" output/$P.net
sh "$KIT/export.sh" "$E" board-quick
[ "$MODE" = place ] && exit 0

step "routing (Freerouting)"
"$PY" "$KIT/route_pcb.py" "$E"
for pass in 1 2; do
  step "DRC fix-ups $pass"
  "$CLI" pcb drc --schematic-parity --severity-all --refill-zones --save-board --format json -o output/drc.json $P.kicad_pcb || true
  "$PY" "$KIT/fix_route.py" "$E" output/drc.json
done
step "silkscreen"
"$PY" "$KIT/tidy_silk.py" "$E"
step "DRC"
"$CLI" pcb drc --schematic-parity --severity-all --refill-zones --save-board --format json -o output/drc.json $P.kicad_pcb || true
"$CLI" pcb drc --schematic-parity --severity-all -o drc.rpt $P.kicad_pcb || true
grep -E "^\*\* Found|violations|unconnected" drc.rpt || true
step "renders and 3D"
sh "$KIT/export.sh" "$E" board
echo ""
echo "Done: $E"
