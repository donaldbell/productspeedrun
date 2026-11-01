// Minimal Arduino shim so synth.cpp / sounds.cpp build on a desktop for test/render_sounds.cpp
#pragma once
#include <ctype.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
template <class T> static inline T max(T a, T b) { return a > b ? a : b; }
template <class T> static inline T min(T a, T b) { return a < b ? a : b; }
#ifndef PI
#define PI 3.14159265358979f
#endif
#define constrain(amt, low, high) ((amt) < (low) ? (low) : ((amt) > (high) ? (high) : (amt)))
