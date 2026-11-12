// Haptic patterns for the watch's ERM coin motor: sound level in, buzz out.
// Plain C with no ESP-IDF calls, so test/test_logic.c also runs it on a computer.
//
// A pattern is a list of (intensity %, ms) steps, played once or looped. Intensity is a fraction of the
// motor's rated 3.0 V; haptic_duty() turns it into a PWM duty for the battery's present voltage, so a
// level feels the same on a full cell (4.2 V) as on a tired one (3.5 V) and the motor never sees more than 3 V.
//
// Alert levels (hosts, Rev B: fussing only glows, it never buzzes):
//   1 fussing    no buzz: the face breathes soft pink
//   2 crying     three firm pulses every 2.5 s
//   3 screaming  long full-strength buzzes, nearly continuous
// A crying alert nobody acknowledges escalates to screaming after BMM_ESCALATE_MS (in the watch's main loop).
#pragma once
#include <stdbool.h>
#include <stdint.h>

#define HAPTIC_MOTOR_MV   3000    // ERM rated voltage (generic 1027 coin motor)
#define HAPTIC_KICK_MS    40      // full-strength kick at the start of a soft pulse, to get the ERM spinning
#define HAPTIC_KICK_BELOW 80      // only pulses softer than this get the kick

typedef struct {
    uint8_t pct;                  // 0 = off, 1-100 = % of HAPTIC_MOTOR_MV
    uint16_t ms;
} hstep_t;

typedef struct {
    const char *name;
    const hstep_t *steps;
    uint8_t n;
    bool loop;
} hpattern_t;

typedef struct {
    const hpattern_t *pat;
    int idx;
    int64_t step_start_ms;
} haptic_t;

extern const hpattern_t HAPTIC_LEVEL[4];        // [0] is silence
extern const hpattern_t HAPTIC_TEST, HAPTIC_PAIRED, HAPTIC_LOST, HAPTIC_LOW_BATT;

void haptic_play(haptic_t *h, const hpattern_t *p, int64_t now_ms);   // replaces whatever is playing
void haptic_stop(haptic_t *h);
bool haptic_active(const haptic_t *h);
int haptic_tick(haptic_t *h, int64_t now_ms);   // intensity 0-100 for now (with the kick); ends one-shots
uint32_t haptic_duty(int pct, int vbat_mv, uint32_t pwm_max);
