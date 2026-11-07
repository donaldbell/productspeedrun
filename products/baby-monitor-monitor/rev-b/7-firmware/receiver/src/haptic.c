#include "haptic.h"

#include <stddef.h>

#define N(a) (uint8_t)(sizeof(a) / sizeof((a)[0]))

// TUNE on a real watch on a real wrist: these are a first guess.
static const hstep_t L2[] = {{70, 250}, {0, 150}, {70, 250}, {0, 150}, {70, 250}, {0, 1450}}; // 2.5 s
static const hstep_t L3[] = {{100, 800}, {0, 200}};                                          // 1.0 s
static const hstep_t TEST[] = {{70, 250}, {0, 150}, {70, 250}, {0, 700},
                               {100, 800}};
static const hstep_t PAIRED[] = {{60, 80}, {0, 80}, {60, 80}, {0, 80}, {60, 80}};             // three quick ticks
static const hstep_t LOST[] = {{80, 600}, {0, 200}, {80, 150}, {0, 200}, {80, 600}};          // long-short-long
static const hstep_t LOW_BATT[] = {{40, 100}, {0, 250}, {40, 100}};                          // two faint taps

const hpattern_t HAPTIC_LEVEL[4] = {
    {"quiet", NULL, 0, false},
    {"fussing", NULL, 0, false},       // hosts: fussing glows only, no buzz
    {"crying", L2, N(L2), true},
    {"screaming", L3, N(L3), true},
};
const hpattern_t HAPTIC_TEST = {"test", TEST, N(TEST), false};
const hpattern_t HAPTIC_PAIRED = {"paired", PAIRED, N(PAIRED), false};
const hpattern_t HAPTIC_LOST = {"link lost", LOST, N(LOST), false};
const hpattern_t HAPTIC_LOW_BATT = {"low battery", LOW_BATT, N(LOW_BATT), false};

void haptic_play(haptic_t *h, const hpattern_t *p, int64_t now_ms) {
    h->pat = (p && p->n) ? p : NULL;
    h->idx = 0;
    h->step_start_ms = now_ms;
}

void haptic_stop(haptic_t *h) { h->pat = NULL; }

bool haptic_active(const haptic_t *h) { return h->pat != NULL; }

int haptic_tick(haptic_t *h, int64_t now_ms) {
    if (!h->pat) return 0;
    while (now_ms - h->step_start_ms >= h->pat->steps[h->idx].ms) {
        h->step_start_ms += h->pat->steps[h->idx].ms;
        if (++h->idx >= h->pat->n) {
            if (!h->pat->loop) {
                h->pat = NULL;
                return 0;
            }
            h->idx = 0;
        }
    }
    const hstep_t *s = &h->pat->steps[h->idx];
    int prev = h->pat->steps[h->idx ? h->idx - 1 : h->pat->n - 1].pct;
    if (h->idx == 0 && !h->pat->loop) prev = 0;
    if (s->pct && s->pct < HAPTIC_KICK_BELOW && prev == 0 && now_ms - h->step_start_ms < HAPTIC_KICK_MS) return 100;
    return s->pct;
}

uint32_t haptic_duty(int pct, int vbat_mv, uint32_t pwm_max) {
    if (pct <= 0) return 0;
    if (vbat_mv < 2500) vbat_mv = 2500;            // implausible reading: don't over-drive
    uint64_t d = (uint64_t)pct * HAPTIC_MOTOR_MV * pwm_max / (100ull * (uint64_t)vbat_mv);
    return d > pwm_max ? pwm_max : (uint32_t)d;
}
