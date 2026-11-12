// Sound level detector: 250 ms loudness windows (dB SPL) in, a smoothed level 0-3 out.
// Plain C with no ESP-IDF calls, so test/test_logic.c runs it on a computer.
//
//  - Noise floor: tracks the room (and the baby monitor's hiss) while it's quiet. Down quickly, up slowly
//    (floor_rise_db per quiet window), and only down during an episode, so the breaths in a long cry can't raise it.
//  - Steady sound is background too: a sound that stays within steady_spread_db for steady_learn_ms (a
//    white-noise machine or fan switched on later, the monitor turned up) becomes the floor even though it's
//    above the fussing threshold, up to floor_max_db (so an unbroken scream is never learned away). Crying
//    isn't steady: breaths and sobs swing it 10-20 dB every few seconds.
//  - Instant level of a window: the highest k with spl >= max(floor + REL_DB[k], ABS_MIN_DB[k]).
//  - Attack: the level goes up to k once ATTACK_WINDOWS of the last HISTORY windows reached k (1 s of sound
//    within 2 s: a door slam or a cough doesn't count, a cry with breaths in it does).
//  - Release: it steps down one level per RELEASE_MS without qualifying sound (breaths between cries
//    don't end an alert).
#pragma once
#include <stdint.h>

#define DET_HISTORY 8

typedef struct {
    float rel_db[4];        // above the floor, per level (index 0 unused)
    float abs_min_db[4];    // and never below this, per level
    float floor_min_db, floor_max_db, floor_rise_db, floor_fall;
    int attack_windows;
    int release_ms;
    float steady_spread_db;     // max - min of a "steady" run
    int steady_learn_ms;        // how long a steady run above level 0 lasts before it becomes the floor
} detector_cfg_t;

typedef struct {
    detector_cfg_t cfg;
    float floor_db;
    uint8_t hist[DET_HISTORY];
    int hist_i, windows;
    int level;
    int64_t hold_ms;        // last time `level` was confirmed by sound
    float run_min, run_max, run_sum;    // the current steady run
    int run_n;
    int64_t run_start_ms;
    int learned;            // how many times a steady sound became the floor (logs)
} detector_t;

void detector_init(detector_t *d, const detector_cfg_t *cfg);
int detector_instant(const detector_t *d, float spl_db);
int detector_update(detector_t *d, float spl_db, int64_t now_ms);   // returns the smoothed level
