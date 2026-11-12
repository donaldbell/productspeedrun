#include "audio.h"
#include <driver/gpio.h>
#include <driver/i2s.h>
#include <esp_timer.h>
#include "config.h"
#include "power.h"

static const i2s_port_t PORT = I2S_NUM_0;
static const int BLOCK = 256;                  // 11.6 ms at 22.05 kHz: 4 engine blocks
// Output gain per volume step, /256, on sounds levelled to peak near 28000 (scripts/gen_sounds.py).
// 160 puts the loudest moment at ~53 % of full scale: under 0.5 W peak into 8 ohm at 9 dB, which is
// what the boost from 2 x AAA should be asked for (see NOTES.md).
static const uint8_t GAIN[6] = {0, 30, 55, 85, 120, 160};

static Ringtone ringtone;
static TaskHandle_t task;
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
static const SoundDef *reqDef;
static bool reqLoop;
static uint8_t reqGain;
static uint32_t reqGen, seenGen;
static volatile bool busy;
static volatile uint8_t level;
static uint32_t statSumUs, statBlocks, statMaxUs;
static uint8_t statNotes;
static AudioStats lastStats;

static void amp(bool on) { digitalWrite(PIN_AMP_SD, on ? AMP_ON : !AMP_ON); }

static void audioTask(void *) {
  static int16_t mono[BLOCK];
  static int16_t stereo[BLOCK * 2];
  const SoundDef *cur = nullptr;
  bool loop = false;
  uint8_t gain = 0;
  for (;;) {
    if (!cur) ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    portENTER_CRITICAL(&mux);
    bool changed = reqGen != seenGen;
    if (changed) {
      seenGen = reqGen;
      cur = reqDef;
      loop = reqLoop;
      gain = reqGain;
    }
    portEXIT_CRITICAL(&mux);
    if (changed) {
      i2s_zero_dma_buffer(PORT);
      if (cur) {
        if (!ringtone.start(cur, loop)) {       // corrupt MIDI data: say nothing rather than hang busy
          cur = nullptr;
          amp(false);
          busy = false;
        }
        statSumUs = statBlocks = statMaxUs = statNotes = 0;
      } else {
        ringtone.stop();
      }
    }
    if (!cur) {
      level = 0;
      continue;
    }
    int64_t t0 = esp_timer_get_time();
    bool more = ringtone.render(mono, BLOCK);
    uint32_t us = (uint32_t)(esp_timer_get_time() - t0);
    statSumUs += us;
    statBlocks++;
    statMaxUs = max(statMaxUs, us);
    statNotes = max<uint8_t>(statNotes, ringtone.activeNotes());
    int32_t peak = 0;
    for (int i = 0; i < BLOCK; i++) {
      int32_t s = mono[i];
      peak = max(peak, abs(s));
      s = s * gain >> 8;
      stereo[2 * i] = stereo[2 * i + 1] = (int16_t)s;   // the amp takes the left slot; send both
    }
    level = min<int32_t>(255, peak >> 7);
    size_t written;
    i2s_write(PORT, stereo, sizeof(stereo), &written, portMAX_DELAY);
    if (!more) {                         // finished (looping sounds never finish on their own)
      portENTER_CRITICAL(&mux);
      bool replaced = reqGen != seenGen;
      portEXIT_CRITICAL(&mux);
      if (!replaced) {
        vTaskDelay(pdMS_TO_TICKS(70));     // let the DMA queue drain before the amp goes off
        amp(false);
        busy = false;
      }
      cur = nullptr;
      level = 0;
    }
    if (statBlocks) {
      portENTER_CRITICAL(&mux);
      lastStats = {statSumUs / statBlocks, statMaxUs, (uint32_t)(BLOCK * 1000000ULL / RINGTONE_RATE), statNotes};
      portEXIT_CRITICAL(&mux);
    }
  }
}

void audioBegin() {
  gpio_hold_dis((gpio_num_t)PIN_AMP_SD);
  pinMode(PIN_AMP_SD, OUTPUT);
  amp(false);

  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = RINGTONE_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.dma_buf_count = 4;
  cfg.dma_buf_len = BLOCK;
  cfg.tx_desc_auto_clear = true;      // underrun = silence, not a buzz
  i2s_driver_install(PORT, &cfg, 0, nullptr);
  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = PIN_I2S_BCLK;
  pins.ws_io_num = PIN_I2S_LRCLK;
  pins.data_out_num = PIN_I2S_DIN;
  pins.data_in_num = I2S_PIN_NO_CHANGE;
  i2s_set_pin(PORT, &pins);
  i2s_zero_dma_buffer(PORT);
  if (!Ringtone::begin()) Serial.println("[audio] Mobileer engine refused its config: no sound");
  xTaskCreate(audioTask, "audio", 6144, nullptr, 5, &task);
}

void audioPlay(const SoundDef *def, bool loop, uint8_t volume) {
  portENTER_CRITICAL(&mux);
  reqDef = def;
  reqLoop = loop;
  reqGain = GAIN[constrain(volume, 1, 5)];
  reqGen++;
  busy = true;
  portEXIT_CRITICAL(&mux);
  amp(true);
  xTaskNotifyGive(task);
}

void audioStop() {
  amp(false);                          // silent now; the task then flushes the queue
  portENTER_CRITICAL(&mux);
  reqDef = nullptr;
  reqGen++;
  busy = false;
  portEXIT_CRITICAL(&mux);
  xTaskNotifyGive(task);
}

bool audioBusy() { return busy; }

void audioLogStats() {
  AudioStats s = audioStats();
  if (!s.blockUs) return;
  Serial.printf("[audio] engine %lu us avg / %lu us worst per %lu us block (%lu%% / %lu%% CPU), up to %u notes\n",
                (unsigned long)s.avgUs, (unsigned long)s.maxUs, (unsigned long)s.blockUs,
                (unsigned long)(100 * s.avgUs / s.blockUs), (unsigned long)(100 * s.maxUs / s.blockUs), s.peakNotes);
}

AudioStats audioStats() {
  portENTER_CRITICAL(&mux);
  AudioStats s = lastStats;
  portEXIT_CRITICAL(&mux);
  return s;
}
uint8_t audioLevel() { return level; }

void audioWait(uint32_t timeoutMs) {
  uint32_t t0 = millis();
  while (busy && millis() - t0 < timeoutMs) delay(10);
}

void audioPrepareSleep() {
  audioStop();
  delay(20);
  i2s_driver_uninstall(PORT);
  holdPin(PIN_AMP_SD, !AMP_ON);
}
