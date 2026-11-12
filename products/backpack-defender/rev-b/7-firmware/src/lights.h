// Eye LEDs (PWM on one N-FET) and the button's WS2812B-2020 (power-switched by a P-FET).
#pragma once
#include <Arduino.h>

void lightsBegin();
void eyes(uint8_t level);                 // 0..255
void buttonLed(uint32_t rgb, uint8_t brightnessPct);   // 0 = dark (and powered off)
uint32_t rainbowColor(uint32_t ms);       // slow trip round the colour wheel
void buttonLedSetting(uint32_t ms, uint8_t extraPct = 0);  // the kid's colour / rainbow, from settings
void lightsOff();                         // everything dark and unpowered
void lightsPrepareSleep();                // drive + hold safe levels through deep sleep
