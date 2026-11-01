// The sound library: alarm sounds the kid can pick, plus a few system chirps.
#pragma once
#include "synth.h"

struct SoundInfo {
  const char *key;        // stable id, stored in NVS
  const char *name;       // shown on the settings page
  const char *family;     // Alarm, Goofy, Robot, Playful, Musical (Rev A's tone families)
  const char *emoji;
  SoundDef def;
};

int soundCount();
const SoundInfo &soundInfo(int i);
int soundFind(const char *key);        // -1 if unknown

enum SystemSound { SND_AWAKE, SND_SAD, SND_SILENCED, SND_SAVED };
const SoundDef *systemSound(SystemSound s);
