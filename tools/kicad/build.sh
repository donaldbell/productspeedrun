#!/bin/sh
# Build an episode's electronics from 5-electronics/src/design.py and src/layout.py.
#
#   tools/kicad/build.sh episodes/002-plant-whisperer             everything (about 5-15 min, mostly routing)
#   tools/kicad/build.sh episodes/002-plant-whisperer schematic   schematic, ERC, netlist check, BOM, schematic.png, SIZE.md
#   tools/kicad/build.sh episodes/002-plant-whisperer place       ...plus the placed (unrouted) board and board.png
#
# Each step saves into 5-electronics/ as it goes, so the dashboard shows the schematic, then the
# placed board, then the routed board. Routing is retried up to ROUTE_TRIES (default 3) times if it
# leaves anything unconnected. A full build exits with an error, after the renders, unless the final
# DRC is 0 violations and 0 unconnected. Machine paths: KICAD_CLI, KICAD_PY, KICAD_SHARE, JAVA,
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
"$PY" "$KIT/size_board.py" "$E" output/$P.net || echo "(size check failed: carrying on)"
sh "$KIT/export.sh" "$E" schematic
[ "$MODE" = schematic ] && exit 0

step "placement"
"$PY" "$KIT/gen_pcb.py" "$E" output/$P.net
sh "$KIT/export.sh" "$E" board-quick
[ "$MODE" = place ] && exit 0

# Freerouting varies from run to run, so if a try leaves anything unconnected, route again from
# the placed board (up to ROUTE_TRIES, default 3) and keep the best try.
cp $P.kicad_pcb output/placed.kicad_pcb
TRIES=${ROUTE_TRIES:-3}
BEST=""
drc_counts() {
  python3 -I -c 'import json, sys; d = json.load(open(sys.argv[1])); print("U=%d V=%d" % (len(d.get("unconnected_items", [])), len(d.get("violations", []))))' output/drc.json
}
t=1
while [ $t -le $TRIES ]; do
  cp output/placed.kicad_pcb $P.kicad_pcb
  step "routing try $t of $TRIES (Freerouting)"
  if "$PY" "$KIT/route_pcb.py" "$E"; then
    for pass in 1 2; do
      step "DRC fix-ups $pass"
      "$CLI" pcb drc --schematic-parity --severity-all --refill-zones --save-board --format json -o output/drc.json $P.kicad_pcb || true
      "$PY" "$KIT/fix_route.py" "$E" output/drc.json
    done
    "$CLI" pcb drc --schematic-parity --severity-all --refill-zones --save-board --format json -o output/drc.json $P.kicad_pcb || true
    eval "$(drc_counts)"
    echo "try $t: $U unconnected, $V DRC violations"
    if [ -z "$BEST" ] || [ $((U * 1000 + V)) -lt "$BEST" ]; then
      BEST=$((U * 1000 + V))
      cp $P.kicad_pcb output/best.kicad_pcb
    fi
    [ "$U" -eq 0 ] && break
  else
    echo "try $t: routing failed"
  fi
  t=$((t + 1))
done
[ -n "$BEST" ] || { echo "Routing failed on every try; see output/routing/"; exit 1; }
cp output/best.kicad_pcb $P.kicad_pcb
step "silkscreen"
"$PY" "$KIT/tidy_silk.py" "$E"
step "DRC"
"$CLI" pcb drc --schematic-parity --severity-all --refill-zones --save-board --format json -o output/drc.json $P.kicad_pcb || true
"$CLI" pcb drc --schematic-parity --severity-all -o drc.rpt $P.kicad_pcb || true
VIOL=$(sed -n 's/^\*\* Found \([0-9]*\) DRC violations.*/\1/p' drc.rpt)
UNCON=$(sed -n 's/^\*\* Found \([0-9]*\) unconnected pads.*/\1/p' drc.rpt)
echo "DRC: ${VIOL:-?} violations, ${UNCON:-?} unconnected (details in drc.rpt)"
step "renders and 3D"
sh "$KIT/export.sh" "$E" board
echo ""
if [ "${VIOL:-1}" -ne 0 ] || [ "${UNCON:-1}" -ne 0 ]; then
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo "!!  DRC NOT CLEAN: ${VIOL:-?} violations, ${UNCON:-?} unconnected"
  echo "!!  The renders and board.glb were still written. See drc.rpt."
  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  grep -A3 -E '^\*\* Found [1-9]' drc.rpt || true
  exit 1
fi
echo "Done: $E (DRC 0 violations, 0 unconnected)"
