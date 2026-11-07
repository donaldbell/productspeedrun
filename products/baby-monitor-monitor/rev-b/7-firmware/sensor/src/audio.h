// Microphone front end: ICS-43434 over I2S -> one loudness reading (dB SPL) per 250 ms window.
#pragma once
#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

#define AUDIO_RATE_HZ   32000
#define AUDIO_WINDOW_MS 250

typedef struct {
    int64_t t_ms;
    float spl_db;       // band-limited (~330 Hz - 4 kHz) RMS level of the window, dB SPL
    int32_t peak;       // largest |sample| in the window (24-bit full scale = 8388607): clipping check
} audio_window_t;

// Starts the audio task; it posts one audio_window_t per window to `out` (drops one if `out` is full).
// With BMM_FAKE_AUDIO it plays a scripted night instead (quiet, fussing, crying, screaming), for a dev board.
void audio_start(QueueHandle_t out);
