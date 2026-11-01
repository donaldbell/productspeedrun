// Plays a Standard MIDI File through Phil Burk's Mobileer ME1000 engine (lib/mobileer): 22.05 kHz mono,
// 32-bit fixed point (the C3 has no FPU). One sound at a time; engine memory is static.
#pragma once
#include <stdint.h>

#define RINGTONE_RATE 22050
#define RINGTONE_FRAMES 64          // the engine renders in blocks of this (SPMIDI_GetFramesPerBuffer)

struct SoundDef {
  const uint8_t *mid;               // Standard MIDI File image, in flash
  uint16_t len;
  uint16_t volume;                  // engine master volume, 128 = as authored (levels the sounds)
};

class Ringtone {
 public:
  static bool begin();              // create the engine once; false if it refused (bad config)
  bool start(const SoundDef *def, bool loop);
  void stop();                      // all sound off at once
  // Fill n samples (a multiple of RINGTONE_FRAMES). Returns false once the sound and its tail have
  // finished (the rest of buf is silence). A looping sound starts again as soon as its file ends,
  // so notes still ringing carry across the join.
  bool render(int16_t *buf, int n);
  bool busy() const { return playing_; }
  int activeNotes() const;

 private:
  void *player_ = nullptr;          // MIDIFilePlayer *
  bool playing_ = false, fileDone_ = false, loop_ = false;
  int tail_ = 0;                    // engine blocks left to let the last notes ring out
};
