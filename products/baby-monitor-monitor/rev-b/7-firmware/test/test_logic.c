// Host test for the hardware-free logic: the sensor's sound-level detector and the watch's haptic patterns.
// Builds the firmware's own detector.c and haptic.c with the Mac's compiler: test/run_tests.sh
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

#include "../common/bmm_protocol.h"     // its _Static_asserts check the radio timing too
#include "../receiver/src/haptic.h"
#include "../sensor/src/detector.h"
#include "../sensor/src/levels.h"

static int fails;
#define CHECK(cond, ...)                                    \
    do {                                                    \
        if (cond) {                                         \
            printf("  ok    ");                             \
        } else {                                            \
            printf("  FAIL  ");                             \
            fails++;                                        \
        }                                                   \
        printf(__VA_ARGS__);                                \
        printf("\n");                                       \
    } while (0)

// The firmware's own numbers (sensor/src/levels.h). If those are retuned, these expectations may need to move.
static detector_t new_detector(void) {
    detector_cfg_t c = {.rel_db = LEVEL_REL_DB, .abs_min_db = LEVEL_ABS_MIN_DB, .floor_min_db = FLOOR_MIN_DB,
                        .floor_max_db = FLOOR_MAX_DB, .floor_rise_db = FLOOR_RISE_DB, .floor_fall = FLOOR_FALL,
                        .attack_windows = ATTACK_WINDOWS, .release_ms = RELEASE_MS};
    detector_t d;
    detector_init(&d, &c);
    return d;
}

static int64_t t;
static int feed(detector_t *d, float db, int secs) {    // 250 ms windows; returns the level at the end
    int lvl = 0;
    for (int i = 0; i < secs * 4; i++) lvl = detector_update(d, db, t += 250);
    return lvl;
}

static void test_detector(void) {
    printf("detector\n");
    detector_t d = new_detector();
    CHECK(feed(&d, 40, 20) == 0, "quiet room (40 dB) -> level 0, floor %.1f", d.floor_db);
    CHECK(d.floor_db > 39 && d.floor_db < 41, "floor settles on the room (%.1f dB)", d.floor_db);

    int lvl = detector_update(&d, 85, t += 250);
    lvl = feed(&d, 40, 1);
    CHECK(lvl == 0, "one loud window (door slam, 85 dB) -> still 0");

    CHECK(feed(&d, 56, 2) == 1, "fussing (56 dB) -> level 1");
    CHECK(feed(&d, 63, 2) == 2, "crying (63 dB) -> level 2");
    CHECK(feed(&d, 80, 2) == 3, "screaming (80 dB) -> level 3");

    // Crying with breaths: 3 loud windows, 1 quiet, for a minute
    int min_lvl = 3;
    for (int i = 0; i < 240; i++) {
        lvl = detector_update(&d, (i % 4 == 3) ? 42 : 68, t += 250);
        if (i > 40 && lvl < min_lvl) min_lvl = lvl;
    }
    CHECK(min_lvl >= 2, "a minute of crying with breaths holds level >= 2 (lowest %d)", min_lvl);
    CHECK(d.floor_db < 42, "the floor didn't creep up during the crying (%.1f dB)", d.floor_db);

    CHECK(feed(&d, 40, 5) >= 1, "5 s of quiet: not over yet (breath / pause)");
    CHECK(feed(&d, 40, 20) == 0, "25 s of quiet -> back to 0 (one level per 6 s)");

    // A loud TV / white-noise machine: the floor follows it, so a steady 55 dB stops counting as fussing
    detector_t n = new_detector();
    feed(&n, 40, 10);
    feed(&n, 49, 300);          // just under level 1's 50 dB minimum, for 5 min
    CHECK(n.floor_db > 47, "steady 49 dB white noise raises the floor (%.1f dB)", n.floor_db);
    CHECK(feed(&n, 56, 3) == 0, "then 56 dB isn't fussing any more (needs floor + 10)");
    CHECK(feed(&n, 62, 3) == 1, "but 62 dB is");
}

static double energy(const hpattern_t *p, int vbat_mv) {    // mean motor drive (fraction of 3 V) over a loop
    haptic_t h;
    haptic_play(&h, p, 0);
    double sum = 0;
    int n = 0;
    int64_t len = 0;
    for (int i = 0; i < p->n; i++) len += p->steps[i].ms;
    for (int64_t ms = 0; ms < len; ms++, n++) {
        uint32_t duty = haptic_duty(haptic_tick(&h, ms), vbat_mv, 1023);
        sum += duty / 1023.0 * vbat_mv / 3000.0;
    }
    return sum / n;
}

static void test_haptics(void) {
    printf("haptics\n");
    double e2 = energy(&HAPTIC_LEVEL[2], 3900), e3 = energy(&HAPTIC_LEVEL[3], 3900);
    CHECK(e2 > 0 && e2 < e3, "louder sound, stronger buzz: mean drive crying %.0f%% < screaming %.0f%%",
          e2 * 100, e3 * 100);
    haptic_t f;
    haptic_play(&f, &HAPTIC_LEVEL[1], 0);
    CHECK(!haptic_active(&f) && haptic_tick(&f, 100) == 0, "fussing never runs the motor (glow only)");
    CHECK(haptic_duty(100, 4200, 1023) <= 1023 * 3000 / 4200 + 1, "full cell (4.2 V): 100%% = %u/1023 (3.0 V avg, motor rating)",
          haptic_duty(100, 4200, 1023));
    CHECK(haptic_duty(100, 2900, 1023) == 1023, "flat cell: 100%% saturates at full duty");
    CHECK(haptic_duty(45, 4200, 1023) < haptic_duty(45, 3500, 1023), "same feel on a tired cell: duty rises as VBAT falls");
    CHECK(haptic_duty(0, 3900, 1023) == 0, "0%% = off");

    haptic_t h;
    haptic_play(&h, &HAPTIC_LEVEL[2], 0);
    CHECK(haptic_tick(&h, 10) == 100 && haptic_tick(&h, 60) == 70, "softer pulse starts with a %d ms kick, then 70%%",
          HAPTIC_KICK_MS);
    CHECK(haptic_tick(&h, 2500 + 60) == 70, "level patterns loop (2.5 s later it's pulsing again)");
    haptic_play(&h, &HAPTIC_TEST, 0);
    CHECK(haptic_tick(&h, 60000) == 0 && !haptic_active(&h), "one-shot patterns end");
}

int main(void) {
    test_detector();
    test_haptics();
    printf(fails ? "\n%d FAILED\n" : "\nall passed\n", fails);
    return fails ? 1 : 0;
}
