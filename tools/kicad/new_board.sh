#!/bin/sh
# Start an episode's electronics from the kit template:
#   tools/kicad/new_board.sh episodes/002-plant-whisperer plant-whisperer "Plant Whisperer"
# Writes 5-electronics/src/design.py and src/layout.py (never overwrites) and a .gitignore.
set -e
KIT=$(cd "$(dirname "$0")" && pwd)
[ -n "$3" ] || { echo "usage: $0 <episode folder> <project-name> \"Title\" [one-line summary]"; exit 2; }
EP=$(cd "$1" && pwd)
NUM=$(basename "$EP" | cut -d- -f1)
HW="$EP/5-electronics"
mkdir -p "$HW/src"
LIB=$(echo "$2" | cut -d- -f1)
UPPER=$(echo "$3" | tr '[:lower:]' '[:upper:]')
for f in design.py layout.py; do
  if [ -e "$HW/src/$f" ]; then echo "keeping existing src/$f"; continue; fi
  sed -e "s|__PROJECT__|$2|g" -e "s|__LIB__|$LIB|g" -e "s|__TITLE_UPPER__|$UPPER|g" -e "s|__TITLE__|$3|g" \
      -e "s|__EP__|$NUM|g" -e "s|__SUMMARY__|${4:-first pass}|g" "$KIT/template/$f" > "$HW/src/$f"
  echo "wrote 5-electronics/src/$f"
done
[ -e "$HW/.gitignore" ] || printf 'output/\n*.kicad_prl\n__pycache__/\n*-backups/\nfp-info-cache\n' > "$HW/.gitignore"
