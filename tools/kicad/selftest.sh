#!/bin/sh
# Check the kit on this computer by rebuilding the Backpack Defender example (episode 001's board)
# in a scratch folder. Nothing in episodes/ is touched. Takes about as long as a real build.
#   tools/kicad/selftest.sh            full build, routing included
#   tools/kicad/selftest.sh place      stop after placement (a minute or so)
set -e
KIT=$(cd "$(dirname "$0")" && pwd)
T=${TMPDIR:-/tmp}/psr-kicad-selftest
rm -rf "$T"
mkdir -p "$T/5-electronics/src"
cp "$KIT/example/design.py" "$KIT/example/layout.py" "$T/5-electronics/src/"
sh "$KIT/build.sh" "$T" "${1:-all}" || { echo "SELF-TEST FAILED (output in $T/5-electronics)"; exit 1; }
echo ""
echo "Self-test passed. Output is in $T/5-electronics (open the .kicad_pcb in KiCad to look)."
