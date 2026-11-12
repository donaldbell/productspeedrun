// Waking, sleeping and the battery.
#pragma once
#include <Arduino.h>

enum Wake { WAKE_POWER_ON, WAKE_PIR, WAKE_BUTTON, WAKE_TIMER };

struct SleepPlan {
  bool pir;               // wake on motion
  bool button;            // wake on the big button
  uint32_t timerMs;       // 0 = no timer
};

void powerBegin();                     // inputs, release pins held through sleep
Wake wakeCause();                      // why we're running now (call once, at boot)
Wake sleepNow(const SleepPlan &plan);  // deep sleep (never returns), or the simulation (returns the wake)
void holdPin(int pin, int level);      // drive a level and hold it through deep sleep
bool pirActive();
bool buttonPressed();
uint16_t batteryMv();                  // VBAT, averaged, eFuse-calibrated
uint32_t secondsNow();                 // keeps counting through deep sleep (RTC)
const char *wakeName(Wake w);

// Serial test hooks (p = PIR, b = button tap), also fed while awake
char serialPoll();
