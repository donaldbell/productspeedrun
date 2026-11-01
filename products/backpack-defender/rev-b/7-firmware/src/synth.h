// A small fixed-point synth for the MAX98357A: 16 kHz mono, integer maths only (the C3 has no FPU).
// Two kinds of sound:
//   - melodies: an RTTTL string played on a Voice (chip, flute, brass, bell, harp, organ ...)
//   - effects: a list of Segs, each a pitch sweep / wobble / random burst on one oscillator
#pragma once
#include <Arduino.h>

#define SYNTH_RATE 16000

enum Wave : uint8_t { SQUARE, PULSE, TRIANGLE, SAW, SINE, ORGAN, NOISE, BELL, PLUCK };

struct Voice {
  Wave wave;
  uint16_t attackMs, decayMs;
  uint8_t sustain;        // 0..255
  uint16_t releaseMs;
  uint8_t vibratoHz10;    // vibrato rate, 0.1 Hz units
  uint8_t vibratoPct10;   // vibrato depth, 0.1 % of pitch
  int8_t octave;          // transpose the tune by whole octaves
};

enum SegFlags : uint8_t { LIN = 0, EXP = 1, RANDOM = 2 };

struct Seg {
  Wave wave;
  uint16_t f0, f1;        // Hz, start and end (RANDOM: range to pick from); f0 = 0 is a rest
  uint16_t ms;
  uint8_t v0, v1;         // volume ramp 0..255
  uint8_t lfoHz;          // wobble rate (RANDOM: new pitch this many times a second)
  uint8_t lfoPct;         // wobble depth, % of pitch
  uint8_t flags;
};

struct SoundDef {
  const char *rtttl;      // melody, or nullptr for an effect
  const Voice *voice;
  const Seg *segs;
  uint8_t nsegs;
};

class Synth {
 public:
  void start(const SoundDef *def);
  // Fill n samples; returns false once the sound has finished (the rest of buf is silence).
  bool render(int16_t *buf, int n);
  bool busy() const { return def_ != nullptr; }

 private:
  // melody
  bool nextNote();
  void noteOn(uint32_t freqMilliHz, uint32_t samples);
  int32_t voiceSample();
  // effect
  void segStart();
  int32_t segSample();

  const SoundDef *def_ = nullptr;
  const char *p_ = nullptr;           // RTTTL read position
  uint8_t defDur_ = 4, defOct_ = 6;
  uint16_t bpm_ = 63;

  uint32_t phase_ = 0, inc_ = 0, lfoPhase_ = 0, lfoInc_ = 0, modPhase_ = 0, vibDepth_ = 0;
  uint32_t left_ = 0, gate_ = 0;      // samples left in the note / segment, and until note-off
  int32_t env_ = 0, envStep_ = 0;     // Q15 << 8
  uint8_t stage_ = 0;                 // 0 attack 1 decay 2 sustain 3 release 4 off
  uint16_t noise_ = 0xACE1;
  int16_t noiseVal_ = 0;
  int16_t ks_[300];                   // Karplus-Strong delay line (down to ~53 Hz)
  uint16_t ksLen_ = 0, ksPos_ = 0;

  uint8_t seg_ = 0;
  uint32_t segN_ = 0;
  int32_t dInc_ = 0;
  uint32_t kInc_ = 0;                 // Q30 per-sample multiplier for EXP sweeps
  int32_t vol_ = 0, dVol_ = 0;        // Q16
};
