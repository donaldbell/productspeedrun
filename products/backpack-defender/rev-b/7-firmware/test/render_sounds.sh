#!/bin/sh
# Render the whole sound library to preview/*.wav with the desktop compiler (listen before flashing).
set -e
cd "$(dirname "$0")/.."
mkdir -p preview
c++ -std=c++11 -O2 -Wall -Itest/host -o test/render_sounds test/render_sounds.cpp src/synth.cpp src/sounds.cpp
./test/render_sounds preview
