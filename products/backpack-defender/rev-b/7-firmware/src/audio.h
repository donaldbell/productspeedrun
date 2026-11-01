// I2S output to the MAX98357A, fed by the synth from its own task.
#pragma once
#include "synth.h"

void audioBegin();
void audioPlay(const SoundDef *def, bool loop, uint8_t volume);   // volume 1..5; turns the amp on
void audioStop();                // silent at once: amp off, queue flushed
bool audioBusy();
uint8_t audioLevel();            // 0..255, loudness of the last ~16 ms (drives the eye LEDs)
void audioWait(uint32_t timeoutMs);   // block until the sound ends (system chirps)
void audioPrepareSleep();        // amp off and held off through deep sleep
