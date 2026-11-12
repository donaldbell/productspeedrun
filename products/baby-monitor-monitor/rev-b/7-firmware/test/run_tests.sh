#!/bin/sh
# Build and run the host test of the hardware-free logic (detector + haptic patterns) with the computer's compiler.
set -e
cd "$(dirname "$0")"
cc -std=c11 -Wall -Wextra -O1 -o test_logic test_logic.c ../sensor/src/detector.c ../receiver/src/haptic.c -lm
./test_logic
