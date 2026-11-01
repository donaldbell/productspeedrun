// Backpack Defender Rev B: board assumptions, timings and thresholds.
#pragma once
#include <Arduino.h>
#include "pins.h"

#ifndef BD_SIM_SLEEP
#define BD_SIM_SLEEP 0          // 1 = fake deep sleep (dev board on USB serial)
#endif
#ifndef BD_INTERNAL_PULLS
#define BD_INTERNAL_PULLS 0     // 1 = use the C3's own pulls on PIR / button (dev board)
#endif

// The firmware leans on the board's pulls to keep things off while it boots and sleeps.
// pins.h says what design.py has, so a board change that drops one stops the build.
#if !PIN_AMP_SD_PULLDOWN || !PIN_EYE_LED_PULLDOWN || !PIN_RGB_PWR_N_PULLUP
#error "design.py lost a pull on AMP_SD / EYE_LED / RGB_PWR_N: the amp, eyes or RGB LED could turn on while asleep"
#endif
#if !PIN_BTN_PULLUP && !BD_INTERNAL_PULLS
#error "BTN needs a pull-up (it is active low)"
#endif
#if !BD_SIM_SLEEP
static_assert(PIN_PIR_OUT <= 5 && PIN_BTN <= 5, "ESP32-C3 deep sleep can only wake on GPIO0-5");
#endif

// Active levels (from the schematic: AM312 high = motion, SW1 to GND, N-FET / P-FET switches)
#define PIR_ACTIVE      HIGH
#define BTN_PRESSED     LOW
#define AMP_ON          HIGH
#define RGB_POWER_ON    LOW

// Timings
#define SETUP_HOLD_MS          600          // button held this long at power-on = setup mode
#define HOLDOFF_MS             5000         // ignore PIR re-triggers this long after an alarm
#define PIR_BUSY_RETRY_MS      2000         // PIR still high when arming: wait and try again
#define DAILY_CHECK_S          (24 * 3600)  // timer wake to check the battery
#define SETUP_IDLE_MS          (5 * 60 * 1000UL)
#define SETUP_AP_TX_POWER      WIFI_POWER_8_5dBm   // plenty for a phone at arm's length, easier on AAA

// Battery (2 x AAA, through the boost). VBAT = VBAT_SENSE_RATIO x pin voltage (pins.h)
#define VBAT_LOW_MV            2100   // sad chirp, at most once a day
#define VBAT_CRITICAL_MV       1900   // no alarm sound: the boost would brown out under the amp's load
#define SAD_CHIRP_EVERY_S      (24 * 3600)
