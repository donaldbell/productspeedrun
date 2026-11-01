#include "portal.h"
#include <DNSServer.h>
#include <WebServer.h>
#include <WiFi.h>
#include "audio.h"
#include "config.h"
#include "lights.h"
#include "portal_html.h"
#include "power.h"
#include "settings.h"
#include "sounds.h"

static WebServer server(80);
static DNSServer dns;
static uint32_t lastActivity;
static String apName;
static bool restartPending;
static uint32_t restartAt;

// What the page shows on the LED: the saved settings until it sends a live preview
static uint32_t liveColor;
static bool liveRainbow;
static uint8_t liveBright;

static String hex6(uint32_t c) {
  char b[7];
  snprintf(b, sizeof(b), "%06lx", (unsigned long)(c & 0xFFFFFF));
  return b;
}

static String jsonEscape(const char *s) {
  String o;
  for (; *s; s++) {
    if (*s == '"' || *s == '\\') o += '\\';
    o += *s;
  }
  return o;
}

static void sendState() {
  lastActivity = millis();
  String j = "{\"name\":\"" + apName + "\",\"sound\":\"" + soundInfo(settings.sound).key + "\",\"color\":\"" +
             hex6(settings.color) + "\",\"rainbow\":" + (settings.rainbow ? "true" : "false") +
             ",\"bright\":" + settings.brightness + ",\"volume\":" + settings.volume +
             ",\"alarm\":" + settings.alarmSecs + ",\"cool\":" + settings.cooldownSecs + ",\"sounds\":[";
  for (int i = 0; i < soundCount(); i++) {
    const SoundInfo &s = soundInfo(i);
    if (i) j += ',';
    j += "{\"k\":\"" + jsonEscape(s.key) + "\",\"n\":\"" + jsonEscape(s.name) + "\",\"f\":\"" + s.family +
         "\",\"e\":\"" + s.emoji + "\"}";
  }
  j += "]}";
  server.send(200, "application/json", j);
}

static void redirectHome() {
  lastActivity = millis();
  server.sendHeader("Location", "http://" + WiFi.softAPIP().toString() + "/", true);
  server.send(302, "text/plain", "");
}

void runSetupMode() {
  Serial.println("[setup] starting AP");
  uint8_t mac[6];
  WiFi.macAddress(mac);
  char name[32];
  snprintf(name, sizeof(name), "BackpackDefender-%02X%02X", mac[4], mac[5]);
  apName = name;
  WiFi.mode(WIFI_AP);
  WiFi.softAP(name);              // open network: it's only up for a few minutes, on purpose (see NOTES.md)
  WiFi.setTxPower(SETUP_AP_TX_POWER);
  dns.start(53, "*", WiFi.softAPIP());
  liveColor = settings.color;
  liveRainbow = settings.rainbow;
  liveBright = settings.brightness;

  server.on("/", [] { lastActivity = millis(); server.send_P(200, "text/html; charset=utf-8", PORTAL_HTML); });
  server.on("/api/state", sendState);
  server.on("/api/preview", [] {
    lastActivity = millis();
    int i = soundFind(server.arg("k").c_str());
    if (i >= 0) audioPlay(&soundInfo(i).def, false, server.hasArg("v") ? server.arg("v").toInt() : settings.volume);
    server.send(200, "text/plain", "ok");
  });
  server.on("/api/light", [] {
    lastActivity = millis();
    liveColor = strtoul(server.arg("c").c_str(), nullptr, 16) & 0xFFFFFF;
    liveRainbow = server.arg("r") == "1";
    liveBright = constrain(server.arg("b").toInt(), 1, 100);
    server.send(200, "text/plain", "ok");
  });
  server.on("/api/save", HTTP_POST, [] {
    Settings s = settings;
    int i = soundFind(server.arg("sound").c_str());
    if (i >= 0) s.sound = i;
    s.color = strtoul(server.arg("color").c_str(), nullptr, 16);
    s.rainbow = server.arg("rainbow") == "1";
    s.brightness = server.arg("bright").toInt();
    s.volume = server.arg("volume").toInt();
    s.alarmSecs = server.arg("alarm").toInt();
    s.cooldownSecs = server.arg("cool").toInt();
    settingsClamp(s);
    settings = s;
    settingsSave();
    Serial.printf("[setup] saved: sound=%s colour=%06lx rainbow=%d\n", soundInfo(s.sound).key,
                  (unsigned long)s.color, s.rainbow);
    server.send(200, "text/plain", "saved");
    audioPlay(systemSound(SND_SAVED), false, settings.volume);
    restartPending = true;
    restartAt = millis() + 1500;
  });
  // Captive-portal probes (Android, Apple, Windows) and anything else: send them to the page
  server.onNotFound(redirectHome);

  server.begin();
  lastActivity = millis();
  Serial.printf("[setup] AP \"%s\" at %s\n", name, WiFi.softAPIP().toString().c_str());

  bool btnWas = true;              // the button is still held from power-on
  for (;;) {
    dns.processNextRequest();
    server.handleClient();
    uint32_t now = millis();

    // LED shows the choice live; rainbow sweeps
    buttonLed(liveRainbow ? rainbowColor(now) : liveColor, liveBright);
    eyes(audioBusy() ? audioLevel() : 40);

    // Big button: stop a preview
    bool btn = buttonPressed();
    if (btn && !btnWas) audioStop();
    btnWas = btn;
    if (serialPoll() == 'b') audioStop();

    if (restartPending && (int32_t)(now - restartAt) >= 0) {
      lightsOff();
      ESP.restart();
    }
    if (now - lastActivity > SETUP_IDLE_MS) {
      Serial.println("[setup] idle, leaving without saving");
      lightsOff();
      ESP.restart();
    }
    delay(2);
  }
}
