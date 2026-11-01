#include "ringtone.h"
#include <string.h>
#include "spmidi/include/midifile_player.h"
#include "spmidi/include/spmidi.h"

static SPMIDI_Context *ctx = nullptr;
static const int TAIL_BLOCKS = RINGTONE_RATE * 4 / RINGTONE_FRAMES;   // ring out for at most 4 s

bool Ringtone::begin() {
  if (ctx) return true;
  if (SPMIDI_GetFramesPerBuffer() != RINGTONE_FRAMES) return false;
  SPMIDI_Initialize();
  if (SPMIDI_CreateContext(&ctx, RINGTONE_RATE) < 0) {
    ctx = nullptr;
    return false;
  }
  return true;
}

static void allSoundOff() {
  for (int ch = 0; ch < 16; ch++) {
    SPMIDI_WriteCommand(ctx, 0xB0 | ch, 120, 0);     // all sound off
    SPMIDI_WriteCommand(ctx, 0xB0 | ch, 121, 0);     // reset controllers (bend, modulation, ...)
  }
}

bool Ringtone::start(const SoundDef *def, bool loop) {
  stop();
  if (!ctx) return false;
  MIDIFilePlayer *p;
  if (MIDIFilePlayer_Create(&p, RINGTONE_RATE, def->mid, def->len) < 0) return false;
  player_ = p;
  SPMIDI_SetMasterVolume(ctx, def->volume);
  loop_ = loop;
  fileDone_ = false;
  tail_ = TAIL_BLOCKS;
  playing_ = true;
  return true;
}

void Ringtone::stop() {
  if (player_) {
    MIDIFilePlayer_Delete((MIDIFilePlayer *)player_);
    player_ = nullptr;
  }
  if (ctx) allSoundOff();
  playing_ = false;
}

int Ringtone::activeNotes() const { return ctx ? SPMIDI_GetActiveNoteCount(ctx) : 0; }

bool Ringtone::render(int16_t *buf, int n) {
  for (int i = 0; i < n; i += RINGTONE_FRAMES) {
    if (playing_ && !fileDone_) {
      int r = MIDIFilePlayer_PlayFrames((MIDIFilePlayer *)player_, ctx, RINGTONE_FRAMES);
      if (r != 0) {                                    // > 0 end of file, < 0 corrupt
        if (r > 0 && loop_) MIDIFilePlayer_Rewind((MIDIFilePlayer *)player_);
        else fileDone_ = true;
      }
    }
    if (playing_ && fileDone_ && (SPMIDI_GetActiveNoteCount(ctx) == 0 || --tail_ <= 0)) stop();
    if (!playing_) {
      memset(buf + i, 0, (n - i) * sizeof(int16_t));
      return false;
    }
    SPMIDI_ReadFrames(ctx, buf + i, RINGTONE_FRAMES, 1, 16);
  }
  return true;
}
