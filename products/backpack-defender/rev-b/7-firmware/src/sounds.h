// The sound library: the alarm sounds the kid can pick, plus a few system chirps (all MIDI, see ringtone.h).
#pragma once
#include "ringtone.h"

struct SoundInfo {
  const char *key;        // stable id, stored in NVS
  const char *name;       // shown on the settings page
  const char *family;     // Rings or Songs
  const char *emoji;
  SoundDef def;
};

int soundCount();
const SoundInfo &soundInfo(int i);     // 0 is the default
int soundFind(const char *key);        // -1 if unknown

enum SystemSound { SND_AWAKE, SND_SAD, SND_SILENCED, SND_SAVED };
const SoundDef *systemSound(SystemSound s);
