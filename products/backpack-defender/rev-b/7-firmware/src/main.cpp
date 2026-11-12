// Backpack Defender Rev B firmware.
//
// Every wake from deep sleep is a fresh boot: setup() works out why we woke, does one job (alarm, silence,
// battery check), picks how to sleep next and sleeps. State that must survive sleep is in RTC memory.
//
//   power on --(button held)--> setup mode (AP + settings page) --> restart
//      | chirp + blink
//      v
//   ARMED (deep sleep: PIR / button / daily timer)
//      |-- PIR ----> ALARM (sound + eyes + button colour, alarmSecs) --> HOLD-OFF (timer) --> ARMED
//      |               `-- button --> SILENCE --> COOL-DOWN (timer, PIR ignored) --> ARMED
//      |-- button -> SILENCE --> COOL-DOWN
//      `-- timer --> battery check --> ARMED
#include <Arduino.h>
#include "audio.h"
#include "config.h"
#include "lights.h"
#include "portal.h"
#include "power.h"
#include "settings.h"
#include "sounds.h"

enum TimerFor : uint8_t { TIMER_DAILY, TIMER_COOLDOWN, TIMER_HOLDOFF };

RTC_DATA_ATTR static uint8_t timerFor = TIMER_DAILY;
RTC_DATA_ATTR static uint32_t lastSadChirpS = 0;
RTC_DATA_ATTR static bool sadChirped = false;
RTC_DATA_ATTR static uint32_t alarmCount = 0;

// ---------------------------------------------------------------- next sleep

static SleepPlan armed() {
  if (pirActive()) {                      // level wake would fire at once: wait for the PIR to settle
    timerFor = TIMER_HOLDOFF;
    return {false, true, PIR_BUSY_RETRY_MS};
  }
  timerFor = TIMER_DAILY;
  return {true, true, DAILY_CHECK_S * 1000UL};
}

static SleepPlan holdoff() {
  timerFor = TIMER_HOLDOFF;
  return {false, true, HOLDOFF_MS};
}

static SleepPlan cooldown() {
  timerFor = TIMER_COOLDOWN;
  return {false, true, settings.cooldownSecs * 1000UL};
}

// ---------------------------------------------------------------- moments

static void blinkHello() {
  for (int k = 0; k < 2; k++) {
    for (int i = 0; i <= 255; i += 15) { eyes(i); buttonLedSetting(millis()); delay(6); }
    for (int i = 255; i >= 0; i -= 15) { eyes(i); delay(6); }
    delay(80);
  }
  lightsOff();
}

static void lowBatteryCheck(uint16_t mv, bool atPowerOn) {
  if (mv >= VBAT_LOW_MV) return;
  uint32_t now = secondsNow();
  if (!atPowerOn && sadChirped && now - lastSadChirpS < SAD_CHIRP_EVERY_S) return;
  sadChirped = true;
  lastSadChirpS = now;
  Serial.printf("[battery] low: %u mV\n", mv);
  if (mv >= VBAT_CRITICAL_MV) audioPlay(systemSound(SND_SAD), false, 2);
  for (int i = 255; i >= 0; i -= 3) { eyes(i); delay(8); }   // droopy eyes
  audioWait(2000);
  lightsOff();
}

static void silenceFeedback() {
  audioStop();
  eyes(0);
  for (int k = 0; k < 3; k++) {
    buttonLedSetting(millis(), 40);
    delay(70);
    buttonLed(0, 0);
    delay(70);
  }
}

static SleepPlan alarm(uint16_t mv) {
  alarmCount++;
  bool quiet = mv < VBAT_CRITICAL_MV;
  const SoundInfo &snd = soundInfo(settings.sound);
  Serial.printf("[alarm] #%lu sound=%s%s\n", (unsigned long)alarmCount, snd.key, quiet ? " (battery critical: lights only)" : "");
  if (!quiet) audioPlay(&snd.def, true, settings.volume);

  uint32_t t0 = millis();
  int eye = 0;
  while (millis() - t0 < settings.alarmSecs * 1000UL) {
    uint32_t ms = millis();
    if (buttonPressed() || serialPoll() == 'b') {
      Serial.println("[alarm] silenced");
      silenceFeedback();
      audioLogStats();
      return cooldown();
    }
    if (quiet) {
      eye = (ms / 125) & 1 ? 255 : 0;     // 4 Hz flash instead of sound
    } else {
      int target = min(255, audioLevel() * 2);
      eye = target > eye ? target : eye - (eye >> 3) - 1;   // snap on with the sound, fade between notes
      if (eye < 0) eye = 0;
    }
    eyes(eye);
    buttonLedSetting(ms, 30);           // brighter than the setting while it's going off
    delay(4);
  }
  audioStop();
  audioLogStats();
  lightsOff();
  return holdoff();
}

// ---------------------------------------------------------------- one wake

static bool setupRequested() {
  uint32_t t0 = millis();
  while (millis() - t0 < SETUP_HOLD_MS) {
    if (!buttonPressed()) return false;
    delay(10);
  }
  return true;
}

static SleepPlan handle(Wake w) {
  uint16_t mv = batteryMv();
  Serial.printf("[wake] %s, battery %u mV\n", wakeName(w), mv);
  switch (w) {
    case WAKE_POWER_ON:
      if (setupRequested()) runSetupMode();   // never returns
      if (mv >= VBAT_CRITICAL_MV) audioPlay(systemSound(SND_AWAKE), false, 2);
      blinkHello();
      lowBatteryCheck(mv, true);
      return armed();
    case WAKE_PIR:
      lowBatteryCheck(mv, false);
      return alarm(mv);
    case WAKE_BUTTON:
      silenceFeedback();
      return cooldown();
    case WAKE_TIMER:
    default:
      if (timerFor == TIMER_DAILY) lowBatteryCheck(mv, false);
      return armed();
  }
}

static void waitButtonRelease(SleepPlan &plan) {
  uint32_t t0 = millis();
  while (buttonPressed() && millis() - t0 < 3000) delay(10);
  if (buttonPressed()) {                   // stuck or held: don't wake on it, come back soon
    plan.button = false;
    if (!plan.timerMs || plan.timerMs > 5000) plan.timerMs = 5000;
  }
}

void setup() {
  Serial.begin(115200);
  powerBegin();
  lightsBegin();
  audioBegin();
  settingsLoad();
  Wake w = wakeCause();
  if (w == WAKE_POWER_ON) {
    timerFor = TIMER_DAILY;
    Serial.printf("\n%s firmware, %d sounds; sound=%s colour=%06lx%s bright=%u%% vol=%u alarm=%us cool=%us\n",
                  BOARD_NAME, soundCount(), soundInfo(settings.sound).key, (unsigned long)settings.color,
                  settings.rainbow ? " (rainbow)" : "", settings.brightness, settings.volume, settings.alarmSecs,
                  settings.cooldownSecs);
#if BD_SIM_SLEEP
    Serial.println("Simulated sleep: p = PIR, b = button, s = setup mode, + / - = try sounds, c = engine CPU, v = battery, r = restart");
    delay(1500);                         // time to open the monitor (or hold BOOT for setup)
#endif
  }
  for (;;) {
    SleepPlan plan = handle(w);
    if (plan.button) waitButtonRelease(plan);
    w = sleepNow(plan);                  // real board: deep sleep, and the next wake starts at setup() again
  }
}

void loop() {}
