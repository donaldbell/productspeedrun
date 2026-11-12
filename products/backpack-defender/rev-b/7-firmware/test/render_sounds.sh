#!/bin/sh
# Render the whole sound library to preview/*.wav with the desktop compiler, using the firmware's own
# engine (lib/mobileer), engine config and sound data, so what you hear is what the device plays.
set -e
cd "$(dirname "$0")/.."
python3 scripts/gen_sounds.py
mkdir -p preview test/obj
FLAGS="-O2 -DSPMIDI_USER_CONFIG -Ilib/mobileer/config -Ilib/mobileer/src -Itest/host"
for c in lib/mobileer/src/spmidi/engine/*.c; do
  cc $FLAGS -w -c "$c" -o "test/obj/$(basename "$c" .c).o"
done
c++ -std=c++11 -Wall $FLAGS -o test/render_sounds test/render_sounds.cpp src/ringtone.cpp src/sounds.cpp test/obj/*.o
./test/render_sounds preview
