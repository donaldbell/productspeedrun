// ICS-43434 I2S front end. The C6 has no FPU, so the per-sample work is integer only; one log10 per window.
//
//   I2S 32 kHz, 32-bit slots, left slot (the board ties L/R low) -> 24-bit sample (top bits of the slot)
//   -> one-pole high-pass ~330 Hz (rumble, mains hum, handling) -> one-pole low-pass ~3.7 kHz (monitor hiss)
//   -> sum of squares over 250 ms -> RMS -> dB SPL.
//
// The band covers a baby's cry (fundamental ~300-600 Hz, most energy below 4 kHz) as it comes out of a baby
// monitor's small speaker. Mic sensitivity -26 dBFS at 94 dB SPL (1 kHz sine): dB SPL = dBFS(sine) + 120.
// 32 kHz rather than 16: it keeps the bit clock (2.048 MHz) well inside the mic's clock range.
#include "audio.h"

#include <math.h>
#include <string.h>
#include "bmm_common.h"
#include "config.h"
#include "driver/gpio.h"
#include "driver/i2s_std.h"
#include "esp_log.h"
#include "freertos/task.h"
#include "pins.h"

static const char *TAG = "audio";
static QueueHandle_t s_out;

static void post(float spl_db, int32_t peak) {
    audio_window_t w = {.t_ms = bmm_now_ms(), .spl_db = spl_db, .peak = peak};
    if (xQueueSend(s_out, &w, 0) != pdTRUE) {
        audio_window_t old;
        xQueueReceive(s_out, &old, 0);      // main loop is behind: keep the newest
        xQueueSend(s_out, &w, 0);
    }
}

#ifdef BMM_FAKE_AUDIO
// A scripted night for a dev board with no mic: (seconds, dB SPL) steps, looping.
static const struct { int secs; float db; } NIGHT[] = {
    {20, 38}, {15, 56}, {6, 40}, {20, 66}, {15, 80}, {30, 38}, {25, 57}, {40, 38},
};

static void audio_task(void *arg) {
    ESP_LOGW(TAG, "BMM_FAKE_AUDIO: no microphone, playing a scripted night");
    uint32_t rng = 1;
    for (;;) {
        for (size_t i = 0; i < sizeof NIGHT / sizeof NIGHT[0]; i++) {
            for (int n = 0; n < NIGHT[i].secs * 1000 / AUDIO_WINDOW_MS; n++) {
                rng = rng * 1103515245u + 12345u;
                float jitter = (float)((rng >> 16) % 600) / 100.0f - 3.0f;     // +-3 dB
                if (NIGHT[i].db > 50 && (n % 8) == 7) jitter -= 15;            // a breath between cries
                post(NIGHT[i].db + jitter, 0);
                vTaskDelay(pdMS_TO_TICKS(AUDIO_WINDOW_MS));
            }
        }
    }
}
#else
#define FRAME 256                       // samples per DMA read (8 ms)

static void audio_task(void *arg) {
    i2s_chan_handle_t rx;
    i2s_chan_config_t chan = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    chan.dma_frame_num = FRAME;
    ESP_ERROR_CHECK(i2s_new_channel(&chan, NULL, &rx));
    i2s_std_config_t std = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(AUDIO_RATE_HZ),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {.mclk = I2S_GPIO_UNUSED, .bclk = PIN_MIC_SCK, .ws = PIN_MIC_WS,
                     .dout = I2S_GPIO_UNUSED, .din = PIN_MIC_SD},
    };
    std.slot_cfg.slot_mask = I2S_STD_SLOT_LEFT;     // L/R tied low on the board
    ESP_ERROR_CHECK(i2s_channel_init_std_mode(rx, &std));
#if !PIN_MIC_SD_PULLDOWN
    // The mic tri-states SD in the right slot; the board has no resistor, so hold it with the internal pull-down.
    gpio_pulldown_en(PIN_MIC_SD);
#endif
    ESP_ERROR_CHECK(i2s_channel_enable(rx));
    ESP_LOGI(TAG, "I2S mic: SCK IO%d, WS IO%d, SD IO%d, %d Hz", PIN_MIC_SCK, PIN_MIC_WS, PIN_MIC_SD, AUDIO_RATE_HZ);

    static int32_t buf[FRAME];
    const int per_window = AUDIO_RATE_HZ * AUDIO_WINDOW_MS / 1000;
    int32_t hp_lp = 0, lp = 0;          // filter states
    int64_t sumsq = 0;
    int32_t peak = 0;
    int n = 0, settle = AUDIO_RATE_HZ / 2;      // skip the mic's start-up (~0.5 s) and the filters settling

    for (;;) {
        size_t got = 0;
        if (i2s_channel_read(rx, buf, sizeof buf, &got, pdMS_TO_TICKS(200)) != ESP_OK || got == 0) {
            ESP_LOGW(TAG, "no I2S data");
            post(0, 0);         // reads as "very quiet"; the main loop flags a dead mic
            continue;
        }
        for (size_t i = 0; i < got / sizeof buf[0]; i++) {
            int32_t x = buf[i] >> 8;                    // 24-bit signed
            hp_lp += (x - hp_lp) >> 4;                  // low-pass ~330 Hz ...
            int32_t hp = x - hp_lp;                     // ... subtracted = high-pass
            lp += (hp - lp) >> 1;                       // low-pass ~3.7 kHz
            if (settle > 0) {
                settle--;
                continue;
            }
            int32_t a = lp < 0 ? -lp : lp;
            if (a > peak) peak = a;
            sumsq += (int64_t)lp * lp;
            if (++n == per_window) {
                float rms = sqrtf((float)sumsq / (float)n);
                float dbfs = 20.0f * log10f((rms * 1.41421356f + 1e-3f) / 8388607.0f);
                post(dbfs + 120.0f + MIC_CAL_DB, peak);
                sumsq = 0, peak = 0, n = 0;
            }
        }
    }
}
#endif

void audio_start(QueueHandle_t out) {
    s_out = out;
    xTaskCreate(audio_task, "audio", 4096, NULL, 6, NULL);
}
