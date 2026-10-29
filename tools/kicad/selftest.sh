#!/bin/sh
# Check the kit on this computer by rebuilding the Backpack Defender example (episode 001's board)
# in a scratch folder. Nothing in episodes/ is touched. Takes about as long as a real build.
#   tools/kicad/selftest.sh                       full build, routing included
#   tools/kicad/selftest.sh place                 stop after placement (a minute or so)
#   tools/kicad/selftest.sh all blocks/pico       build a proven block instead of the example
set -e
KIT=$(cd "$(dirname "$0")" && pwd)
SRC=${2:-example}
[ -f "$KIT/$SRC/design.py" ] || { echo "no $KIT/$SRC/design.py"; exit 2; }
T=${TMPDIR:-/tmp}/psr-kicad-selftest
[ "$SRC" = example ] || T="$T-$(basename "$SRC")"
rm -rf "$T"
mkdir -p "$T/5-electronics/src"
cp "$KIT/$SRC/design.py" "$KIT/$SRC/layout.py" "$T/5-electronics/src/"
sh "$KIT/build.sh" "$T" "${1:-all}" || { echo "SELF-TEST FAILED (output in $T/5-electronics)"; exit 1; }
echo ""
echo "Self-test passed. Output is in $T/5-electronics (open the .kicad_pcb in KiCad to look)."
