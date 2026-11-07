#include "detector.h"

#include <string.h>

void detector_init(detector_t *d, const detector_cfg_t *cfg) {
    memset(d, 0, sizeof *d);
    d->cfg = *cfg;
    d->floor_db = -1;       // set by the first window
}

int detector_instant(const detector_t *d, float spl_db) {
    int k = 0;
    for (int i = 1; i <= 3; i++) {
        float thr = d->floor_db + d->cfg.rel_db[i];
        if (thr < d->cfg.abs_min_db[i]) thr = d->cfg.abs_min_db[i];
        if (spl_db >= thr) k = i;
    }
    return k;
}

static void track_floor(detector_t *d, float spl_db, int may_rise) {
    if (d->floor_db < 0) {
        d->floor_db = spl_db;
    } else if (spl_db < d->floor_db) {
        d->floor_db += (spl_db - d->floor_db) * d->cfg.floor_fall;
    } else if (may_rise) {
        float up = spl_db - d->floor_db;
        d->floor_db += up < d->cfg.floor_rise_db ? up : d->cfg.floor_rise_db;
    }
    if (d->floor_db < d->cfg.floor_min_db) d->floor_db = d->cfg.floor_min_db;
    if (d->floor_db > d->cfg.floor_max_db) d->floor_db = d->cfg.floor_max_db;
}

int detector_update(detector_t *d, float spl_db, int64_t now_ms) {
    if (d->floor_db < 0) track_floor(d, spl_db, 1);
    int inst = detector_instant(d, spl_db);
    // Quiet windows teach the floor; during an episode (breaths between cries) it may only fall.
    if (inst == 0) track_floor(d, spl_db, d->level == 0);

    // Steady run: restart it whenever this window would stretch it past steady_spread_db.
    float lo = spl_db < d->run_min ? spl_db : d->run_min, hi = spl_db > d->run_max ? spl_db : d->run_max;
    if (d->run_n == 0 || hi - lo > d->cfg.steady_spread_db) {
        d->run_min = d->run_max = d->run_sum = spl_db;
        d->run_n = 1;
        d->run_start_ms = now_ms;
    } else {
        d->run_min = lo, d->run_max = hi, d->run_sum += spl_db, d->run_n++;
    }
    // Only up to floor_max_db: a steady sound louder than that (an unbroken scream) is never learned away.
    if (inst > 0 && now_ms - d->run_start_ms >= d->cfg.steady_learn_ms &&
        d->run_sum / d->run_n <= d->cfg.floor_max_db) {
        // It has been loud and unchanging for too long to be a baby: it's the new background.
        d->floor_db = d->run_sum / d->run_n;
        if (d->floor_db < d->cfg.floor_min_db) d->floor_db = d->cfg.floor_min_db;
        memset(d->hist, 0, sizeof d->hist);
        d->level = 0;
        d->learned++;
        inst = detector_instant(d, spl_db);
    }

    d->hist[d->hist_i] = (uint8_t)inst;
    d->hist_i = (d->hist_i + 1) % DET_HISTORY;
    if (d->windows < DET_HISTORY) d->windows++;

    int cand = 0;       // highest level with enough recent windows at or above it
    for (int k = 3; k >= 1 && !cand; k--) {
        int n = 0;
        for (int i = 0; i < d->windows; i++) n += d->hist[i] >= k;
        if (n >= d->cfg.attack_windows) cand = k;
    }
    if (cand >= d->level) {
        if (cand > 0) d->hold_ms = now_ms;
        d->level = cand;
    } else if (now_ms - d->hold_ms >= d->cfg.release_ms) {
        d->level--;
        d->hold_ms = now_ms;
    }
    return d->level;
}
