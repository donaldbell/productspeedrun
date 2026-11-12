// Kid-chosen settings, kept in NVS.
#pragma once
#include <Arduino.h>

struct Settings {
  int sound;              // index into the sound catalogue (stored by its key, so reordering is safe)
  uint32_t color;         // 0xRRGGBB for the button LED
  bool rainbow;           // slow hue sweep instead of one colour
  uint8_t brightness;     // button LED, percent (low by default: it sits right under a clear button)
  uint8_t volume;         // 1..5
  uint8_t alarmSecs;      // how long the alarm plays
  uint16_t cooldownSecs;  // PIR ignored this long after the button silences it
};

extern Settings settings;

void settingsLoad();
void settingsSave();
void settingsClamp(Settings &s);
