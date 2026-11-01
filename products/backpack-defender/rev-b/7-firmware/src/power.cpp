#include "power.h"
#include <driver/gpio.h>
#include <esp_sleep.h>
#include <sys/time.h>
#include "audio.h"
#include "config.h"
#include "lights.h"
#if BD_SIM_SLEEP
#include "portal.h"
#include "settings.h"
#include "sounds.h"
#endif

static char pendingKey = 0;     // a p / b typed while we were doing something else

void powerBegin() {
  gpio_deep_sleep_hold_dis();   // each output releases its own pin's hold as it starts (lights, audio)
#if BD_INTERNAL_PULLS
  pinMode(PIN_PIR_OUT, INPUT_PULLDOWN);
  pinMode(PIN_BTN, INPUT_PULLUP);
#else
  pinMode(PIN_PIR_OUT, INPUT);  // AM312 drives its output; BTN has R9 to 3V3
  pinMode(PIN_BTN, INPUT);
#endif
  analogSetPinAttenuation(PIN_VBAT_SENSE, ADC_11db);
}

Wake wakeCause() {
  if (esp_reset_reason() != ESP_RST_DEEPSLEEP) return WAKE_POWER_ON;
  switch (esp_sleep_get_wakeup_cause()) {
    case ESP_SLEEP_WAKEUP_TIMER:
      return WAKE_TIMER;
    case ESP_SLEEP_WAKEUP_GPIO: {
      uint64_t pins = esp_sleep_get_gpio_wakeup_status();
      if (pins & BIT64(PIN_BTN)) return WAKE_BUTTON;    // button wins if both
      if (pins & BIT64(PIN_PIR_OUT)) return WAKE_PIR;
      return buttonPressed() ? WAKE_BUTTON : WAKE_PIR;
    }
    default:
      return WAKE_POWER_ON;
  }
}

const char *wakeName(Wake w) {
  static const char *names[] = {"power-on", "PIR", "button", "timer"};
  return names[w];
}

void holdPin(int pin, int level) {
  gpio_num_t g = (gpio_num_t)pin;
  gpio_reset_pin(g);                   // back to plain GPIO (off the RMT / LEDC / I2S signal), then drive it
  gpio_pullup_dis(g);
  gpio_pulldown_dis(g);
  gpio_set_direction(g, GPIO_MODE_OUTPUT);
  gpio_set_level(g, level);
  gpio_hold_en(g);
}

bool pirActive() { return digitalRead(PIN_PIR_OUT) == PIR_ACTIVE; }
bool buttonPressed() { return digitalRead(PIN_BTN) == BTN_PRESSED; }

uint16_t batteryMv() {
#ifdef BD_FAKE_VBAT_MV
  return BD_FAKE_VBAT_MV;              // dev board: IO3 floats
#endif
  uint32_t sum = 0;
  for (int i = 0; i < 16; i++) sum += analogReadMilliVolts(PIN_VBAT_SENSE);
  return (uint16_t)(sum / 16 * VBAT_SENSE_RATIO);
}

uint32_t secondsNow() {
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  return tv.tv_sec;
}

char serialPoll() {
  if (pendingKey) {
    char c = pendingKey;
    pendingKey = 0;
    return c;
  }
  return Serial.available() ? Serial.read() : 0;
}

#if BD_SIM_SLEEP
// Dev board: stay awake on USB, pretend to sleep, wake on the same conditions (or p / b typed).
Wake sleepNow(const SleepPlan &plan) {
  Serial.printf("[sleep] pir=%d button=%d timer=%lums (simulated)\n", plan.pir, plan.button, (unsigned long)plan.timerMs);
  lightsOff();
  uint32_t t0 = millis();
  for (;;) {
    char c = serialPoll();
    if (plan.pir && (c == 'p' || pirActive())) return WAKE_PIR;
    if (plan.button && (c == 'b' || buttonPressed())) return WAKE_BUTTON;
    if (plan.timerMs && millis() - t0 >= plan.timerMs) return WAKE_TIMER;
    if (c == 'r') ESP.restart();
    if (c == 's') runSetupMode();
    if (c == 'v') Serial.printf("battery %u mV\n", batteryMv());
    if (c == 'c') audioLogStats();       // engine CPU use of the last sound
    if (c == '+' || c == '-') {          // browse the sound library on the bench
      settings.sound = (settings.sound + (c == '+' ? 1 : soundCount() - 1)) % soundCount();
      Serial.printf("sound %d: %s\n", settings.sound, soundInfo(settings.sound).name);
      audioPlay(&soundInfo(settings.sound).def, false, settings.volume);
    }
    delay(5);
  }
}
#else
Wake sleepNow(const SleepPlan &plan) {
  Serial.printf("[sleep] pir=%d button=%d timer=%lums\n", plan.pir, plan.button, (unsigned long)plan.timerMs);
  Serial.flush();
  audioPrepareSleep();
  lightsPrepareSleep();
  // (Wi-Fi is only ever on in setup mode, which leaves by restarting.)
  if (plan.pir) esp_deep_sleep_enable_gpio_wakeup(BIT64(PIN_PIR_OUT), ESP_GPIO_WAKEUP_GPIO_HIGH);
  if (plan.button) esp_deep_sleep_enable_gpio_wakeup(BIT64(PIN_BTN), ESP_GPIO_WAKEUP_GPIO_LOW);
  if (plan.timerMs) esp_sleep_enable_timer_wakeup((uint64_t)plan.timerMs * 1000);
  gpio_deep_sleep_hold_en();
  esp_deep_sleep_start();
  return WAKE_POWER_ON;  // not reached
}
#endif
