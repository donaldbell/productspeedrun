// Sensor firmware tunables. Everything marked TUNE needs a real board next to a real baby monitor.
#pragma once
#include "bmm_protocol.h"
#include "pins.h"

// --- board checks: stop the build if the board changes under the firmware
#if !defined(PIN_MIC_SCK) || !defined(PIN_MIC_WS) || !defined(PIN_MIC_SD) || !defined(PIN_BTN) || \
    !defined(PIN_BAR_IO) || !defined(PIN_LED_IO) || !defined(PIN_VBAT_SENSE) || !defined(PIN_CHG_STAT)
#error "pins.h is missing a net the sensor firmware uses: was the board's design.py changed?"
#endif
#if PIN_BTN_PULLDOWN || PIN_CHG_STAT_PULLDOWN
#error "BTN and CHG_STAT are active low and rely on (internal) pull-ups"
#endif
#ifndef VBAT_SENSE_RATIO
#error "no VBAT_SENSE divider found on the board"
#endif

// --- microphone / levels: levels.h (no pins.h there, so test/test_logic.c can use the same numbers)
#include "levels.h"

// --- "I'm awake" (snooze bar: SW1 + SW3 in parallel on BTN)
#define BTN_DEBOUNCE_MS     30
#define BTN_HOLD_MS         3000    // hold = test the watch + offer pairing
#define SNOOZE_MS           (3 * 60 * 1000)   // an ack holds this long unless it gets louder
#define ACK_RESET_QUIET_MS  30000   // quiet this long ends the episode: the next sound alerts again

// --- battery (103450, 2000 mAh)
#define VBAT_LOW_MV         3550    // the AP2112K needs ~3.45 V in for 3.3 V out at this load
#define VBAT_READ_MS        10000

// --- lights. WS2812B under the clear bar; values are 0-255 per channel before BAR_SCALE.  TUNE through the acrylic
#define BAR_SCALE           100     // percent: one knob for the whole bar
#define BAR_ARMED           {12, 7, 2}        // dim warm white: "here I am", night-light level
#define BAR_ALERT           {255, 110, 0}     // amber, pulsing faster with the level
#define BAR_ACKED           {0, 60, 10}       // soft green: acknowledged, still hearing sound
#define BAR_ACK_FLASH       {0, 255, 40}      // bright green blinks: "I'm awake" registered
#define BAR_PAIRING         {0, 40, 255}      // blue breathing
#define BAR_LOST            {60, 0, 0}        // red pulse: the watch isn't answering
#define BAR_UNPAIRED        {0, 10, 60}       // slow dim blue blink: hold 3 s to pair
#define BAR_LOW_BATT        {40, 12, 0}       // dim orange instead of armed white
#define BAR_PRESS           {90, 90, 90}      // while the bar is held down
#define STATUS_VU           {0, 80, 300, 700} // green status LED duty (of 1023) per instant level: "it hears it"
#define STATUS_BLIP         60                // alive blip duty, every 4 s
