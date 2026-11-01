#include "settings.h"
#include <Preferences.h>
#include "sounds.h"

Settings settings;

static const Settings DEFAULTS = {0, 0x7B2FF7, false, 12, 3, 10, 60};

void settingsClamp(Settings &s) {
  if (s.sound < 0 || s.sound >= soundCount()) s.sound = 0;
  s.color &= 0xFFFFFF;
  s.brightness = constrain(s.brightness, 1, 100);
  s.volume = constrain(s.volume, 1, 5);
  s.alarmSecs = constrain(s.alarmSecs, 3, 30);
  s.cooldownSecs = constrain(s.cooldownSecs, 10, 600);
}

void settingsLoad() {
  Preferences p;
  settings = DEFAULTS;
  settings.sound = soundFind("siren");
  if (p.begin("bd", true)) {
    int i = soundFind(p.getString("sound", soundInfo(settings.sound).key).c_str());
    if (i >= 0) settings.sound = i;
    settings.color = p.getUInt("color", DEFAULTS.color);
    settings.rainbow = p.getBool("rainbow", DEFAULTS.rainbow);
    settings.brightness = p.getUChar("bright", DEFAULTS.brightness);
    settings.volume = p.getUChar("volume", DEFAULTS.volume);
    settings.alarmSecs = p.getUChar("alarm_s", DEFAULTS.alarmSecs);
    settings.cooldownSecs = p.getUShort("cool_s", DEFAULTS.cooldownSecs);
    p.end();
  }
  settingsClamp(settings);
}

void settingsSave() {
  Preferences p;
  if (!p.begin("bd", false)) return;
  p.putString("sound", soundInfo(settings.sound).key);
  p.putUInt("color", settings.color);
  p.putBool("rainbow", settings.rainbow);
  p.putUChar("bright", settings.brightness);
  p.putUChar("volume", settings.volume);
  p.putUChar("alarm_s", settings.alarmSecs);
  p.putUShort("cool_s", settings.cooldownSecs);
  p.end();
}
