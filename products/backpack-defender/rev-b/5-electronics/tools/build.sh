#!/bin/sh
# Rebuild the Backpack Defender board end to end:
#   schematic -> ERC + netlist check -> placement -> Freerouting -> DRC fix-ups -> DRC -> exports.
# Usage: tools/build.sh            (from anywhere; writes into 5-electronics/)
set -e
cd "$(dirname "$0")/.."
CLI=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
PY=${KICAD_PY:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3}
P=backpack-defender
mkdir -p output
python3 -I tools/gen_schematic.py
"$CLI" sch erc --severity-all --exit-code-violations -o erc.rpt $P.kicad_sch
"$CLI" sch export netlist -o output/$P.net $P.kicad_sch
python3 -I tools/check_netlist.py output/$P.net
"$PY" tools/gen_pcb.py
"$PY" tools/route_pcb.py
for pass in 1 2; do
  "$CLI" pcb drc --schematic-parity --severity-all --refill-zones --save-board --format json -o output/drc.json $P.kicad_pcb || true
  "$PY" tools/fix_route.py output/drc.json
done
"$PY" tools/tidy_silk.py
"$CLI" pcb drc --schematic-parity --severity-all --refill-zones --save-board --format json -o output/drc.json $P.kicad_pcb || true
"$CLI" pcb drc --schematic-parity --severity-all -o drc.rpt $P.kicad_pcb || true
sh tools/export.sh
