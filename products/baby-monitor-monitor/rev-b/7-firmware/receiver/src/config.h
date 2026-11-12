// Watch (receiver) firmware tunables. Everything marked TUNE needs a real watch on a wrist.
#pragma once
#include "bmm_protocol.h"
#include "pins.h"

// --- board checks
#if !defined(PIN_MOT_PWM) || !defined(PIN_LED_IO) || !defined(PIN_LINK_IO) || !defined(PIN_VBAT_SENSE) || \
    !defined(PIN_CHG_STAT)
#error "pins.h is missing a net the watch firmware uses: was the board's design.py changed?"
#endif
#if !PIN_MOT_PWM_PULLDOWN
#error "MOT_PWM needs its pull-down (R6): it keeps the motor off while the C6 boots or sleeps"
#endif
#if PIN_CHG_STAT_PULLDOWN
#error "CHG_STAT is open drain, active low: it relies on the internal pull-up"
#endif
#ifndef VBAT_SENSE_RATIO
#error "no VBAT_SENSE divider found on the board"
#endif

// --- pairing (no button on the watch): it accepts a sensor's offer when it has no sensor yet, while it's
// charging (on its clip), or in the first minutes after it starts.
#define PAIR_AFTER_BOOT_MS  (2 * 60 * 1000)

// --- link lost (the sensor stopped answering: switched off, out of range, flat)
#define LOST_GRACE_MS       20000             // after BMM_LINK_LOST_MS, wait this long before buzzing
#define LOST_REPEAT_MS      (5 * 60 * 1000)   // then buzz again this often ...
#define LOST_MAX_BUZZES     3                 // ... this many times, then glow only (until it's back)

// --- battery (402025, 150 mAh)
#define VBAT_LOW_MV         3550              // the LDO drops out below ~3.45 V
#define VBAT_READ_MS        30000
#define LOW_BATT_REPEAT_MS  (30 * 60 * 1000)

// --- face glow (WS2812B under the lens) and link LED. TUNE through the lens
#define GLOW_LEVEL          {{0, 0, 0}, {255, 60, 120}, {255, 0, 160}, {255, 0, 60}}  // pink -> magenta -> red
#define GLOW_MAX            90                // 0-255 scale for the brightest moment
#define GLOW_BASE_PCT       15                // glow between pulses during an alert
#define GLOW_ACKED          {0, 255, 60}      // green fade: the parent pressed "I'm awake"
#define GLOW_PAIRED         {0, 60, 255}
#define GLOW_LOST           {255, 0, 0}
#define GLOW_CHARGING       {255, 90, 0}      // slow amber breathing while on the clip
#define LINK_BLIP_MS        25                // green link LED per heartbeat
#define LINK_BLIP_DUTY      120               // of 1023: dim, it's on a wrist at night
