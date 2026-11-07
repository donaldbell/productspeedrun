// Sound-level tunables for the detector, shared by the firmware (config.h) and test/test_logic.c.
#pragma once

// --- microphone / levels                                       TUNE all of these on the bench
#define MIC_CAL_DB          0.0f    // per-unit offset after checking against an SPL meter
// Level k needs spl >= max(floor + REL_DB[k], ABS_MIN_DB[k]). The sensor sits next to the monitor's speaker,
// so these depend on the parent's monitor volume; the relative part makes them mostly volume-independent.
#define LEVEL_REL_DB        {0, 10, 18, 26}
#define LEVEL_ABS_MIN_DB    {0, 50, 58, 66}
#define FLOOR_MIN_DB        30.0f
#define FLOOR_MAX_DB        62.0f
#define FLOOR_RISE_DB       0.05f   // per 250 ms window while quiet: 12 dB a minute
#define FLOOR_FALL          0.25f   // fraction of the gap per window when it gets quieter
#define ATTACK_WINDOWS      4       // of the last 8 (1 s of sound within 2 s)
#define RELEASE_MS          6000    // one level down per 6 s without it
