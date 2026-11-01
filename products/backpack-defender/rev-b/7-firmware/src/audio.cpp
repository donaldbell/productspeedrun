#include "audio.h"
#include <driver/gpio.h>
#include <driver/i2s.h>
#include "config.h"
#include "power.h"

static const i2s_port_t PORT = I2S_NUM_0;
static const int BLOCK = 256;                  // 16 ms at 16 kHz
// Output gain per volume step, /256. 160 is ~62 % of full scale: about 0.5 W peak into 8 ohm at 9 dB,
// which is what the boost from 2 x AAA should be asked for (see NOTES.md).
static const uint8_t GAIN[6] = {0, 30, 55, 85, 120, 160};

static Synth synth;
static TaskHandle_t task;
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
static const SoundDef *reqDef;
static bool reqLoop;
static uint8_t reqGain;
static uint32_t reqGen, seenGen;
static volatile bool busy;
static volatile uint8_t level;

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
      if (cur) synth.start(cur);
    }
    if (!cur) {
      level = 0;
      continue;
    }
    bool more = synth.render(mono, BLOCK);
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
    if (!more) {
      if (loop) {
        synth.start(cur);
      } else {
        portENTER_CRITICAL(&mux);
        bool replaced = reqGen != seenGen;
        portEXIT_CRITICAL(&mux);
        if (!replaced) {
          vTaskDelay(pdMS_TO_TICKS(70));   // let the DMA queue drain before the amp goes off
          amp(false);
          busy = false;
        }
        cur = nullptr;
        level = 0;
      }
    }
  }
}

void audioBegin() {
  gpio_hold_dis((gpio_num_t)PIN_AMP_SD);
  pinMode(PIN_AMP_SD, OUTPUT);
  amp(false);

  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = SYNTH_RATE;
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
  xTaskCreate(audioTask, "audio", 4096, nullptr, 5, &task);
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
