// Sound library. The alarm sounds are the hosts' picks from Phil Burk's Mobileer ringtones; the list,
// names and system chirps live in scripts/gen_sounds.py, which writes the MIDI data into sound_data.h.
#include "sounds.h"
#include <Arduino.h>
#include "sound_data.h"

#define N(a) (int)(sizeof(a) / sizeof((a)[0]))

static const SoundInfo SOUNDS[] = {SOUND_TABLE};
static const SoundDef SYSTEM[] = {SYSTEM_TABLE};

int soundCount() { return N(SOUNDS); }
const SoundInfo &soundInfo(int i) { return SOUNDS[constrain(i, 0, soundCount() - 1)]; }
const SoundDef *systemSound(SystemSound s) { return &SYSTEM[s]; }

int soundFind(const char *key) {
  for (int i = 0; i < soundCount(); i++)
    if (!strcmp(SOUNDS[i].key, key)) return i;
  return -1;
}
