#include "lights.h"
#include <driver/gpio.h>
#include "config.h"
#include "power.h"
#include "settings.h"

static const int EYE_CH = 0;
static bool rgbPowered = false;
static uint32_t rgbLast = 0xFFFFFFFF;

void lightsBegin() {
  gpio_hold_dis((gpio_num_t)PIN_EYE_LED);
  gpio_hold_dis((gpio_num_t)PIN_RGB_PWR_N);
  gpio_hold_dis((gpio_num_t)PIN_RGB_DATA);
  ledcSetup(EYE_CH, 5000, 8);
  ledcAttachPin(PIN_EYE_LED, EYE_CH);
  ledcWrite(EYE_CH, 0);
  pinMode(PIN_RGB_PWR_N, OUTPUT);
  digitalWrite(PIN_RGB_PWR_N, !RGB_POWER_ON);
  neopixelWrite(PIN_RGB_DATA, 0, 0, 0);    // claims the RMT channel; data idles low (no back-powering)
}

void eyes(uint8_t level) {
  ledcWrite(EYE_CH, ((uint16_t)level * level) >> 8);   // rough gamma so a fade looks even
}

void buttonLed(uint32_t rgb, uint8_t pct) {
  uint8_t r = ((rgb >> 16) & 0xFF) * pct / 100, g = ((rgb >> 8) & 0xFF) * pct / 100, b = (rgb & 0xFF) * pct / 100;
  uint32_t c = ((uint32_t)r << 16) | (g << 8) | b;
  if (c == 0) {
    if (rgbPowered) {
      neopixelWrite(PIN_RGB_DATA, 0, 0, 0);
      digitalWrite(PIN_RGB_PWR_N, !RGB_POWER_ON);   // a dark WS2812 still draws ~1 mA
      rgbPowered = false;
    }
    rgbLast = 0;
    return;
  }
  if (!rgbPowered) {
    digitalWrite(PIN_RGB_PWR_N, RGB_POWER_ON);
    delayMicroseconds(500);                         // let VLED come up before the first frame
    rgbPowered = true;
    rgbLast = 0xFFFFFFFF;
  }
  if (c != rgbLast) neopixelWrite(PIN_RGB_DATA, r, g, b);
  rgbLast = c;
}

// HSV (full saturation and value) to RGB, hue 0..1535
static uint32_t hue(uint16_t h) {
  uint8_t x = h & 0xFF;
  switch ((h >> 8) % 6) {
    case 0: return 0xFF0000 | (x << 8);
    case 1: return ((255 - x) << 16) | 0xFF00;
    case 2: return 0x00FF00 | x;
    case 3: return ((255 - x) << 8) | 0xFF;
    case 4: return ((uint32_t)x << 16) | 0xFF;
    default: return 0xFF0000 | (255 - x);
  }
}

uint32_t rainbowColor(uint32_t ms) { return hue((ms / 4) % 1536); }   // ~6 s round the wheel

void buttonLedSetting(uint32_t ms, uint8_t extraPct) {
  buttonLed(settings.rainbow ? rainbowColor(ms) : settings.color, min(100, settings.brightness + extraPct));
}

void lightsOff() {
  eyes(0);
  buttonLed(0, 0);
}

void lightsPrepareSleep() {
  lightsOff();
  ledcDetachPin(PIN_EYE_LED);
  holdPin(PIN_EYE_LED, 0);
  holdPin(PIN_RGB_PWR_N, !RGB_POWER_ON);
  holdPin(PIN_RGB_DATA, 0);             // low, so the unpowered LED isn't fed through its data pin
}
