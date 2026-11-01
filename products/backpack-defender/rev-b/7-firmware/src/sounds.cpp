// Sound library. Melodies are public-domain tunes (or our own), written out as RTTTL by ear: check them
// on the speaker before shipping. Effects are pitch sweeps on one oscillator (see Seg in synth.h).
// The 20 mm speaker has little below ~600 Hz, so most voices play an octave up.
#include "sounds.h"

#define N(a) (uint8_t)(sizeof(a) / sizeof((a)[0]))

// ---------------------------------------------------------------- voices
//                         wave      att dec  sus  rel  vib(Hz/10, %/10) octave
static const Voice CHIP   = {SQUARE,    2, 60, 170,  30,  0,  0, 1};
static const Voice CHIP25 = {PULSE,     2, 40, 190,  20, 55, 6, 1};
static const Voice FLUTE  = {TRIANGLE, 25, 80, 220,  60, 50, 8, 1};
static const Voice BRASS  = {SAW,      20, 90, 200,  50, 45, 5, 0};
static const Voice BELLS  = {BELL,      1, 500, 40, 300,  0,  0, 1};
static const Voice HARP   = {PLUCK,     1, 10, 255, 120,  0,  0, 0};
static const Voice PIPES  = {ORGAN,    10, 50, 230,  60, 60, 4, 0};
static const Voice STOMP  = {SAW,       3, 120, 90,  40,  0,  0, 1};

// ---------------------------------------------------------------- effects
//   wave      f0    f1    ms  v0   v1  lfoHz lfo%  flags
static const Seg SIREN[] = {
  {TRIANGLE,  650, 1500, 900, 255, 255, 0, 0, LIN},
  {TRIANGLE, 1500,  650, 900, 255, 255, 0, 0, LIN},
};
static const Seg WHOOP[] = {
  {SQUARE,    450, 1800, 520, 230, 255, 0, 0, EXP},
  {SQUARE,      0,    0, 140,   0,   0, 0, 0, LIN},
};
static const Seg KLAXON[] = {
  {SAW,       320,  640, 650, 255, 255, 0, 0, EXP},
  {SAW,       640,  640, 150, 255,  80, 0, 0, LIN},
  {SAW,         0,    0, 250,   0,   0, 0, 0, LIN},
};
static const Seg BEEPS[] = {
  {SQUARE,   2100, 2100,  90, 220, 220, 0, 0, LIN}, {SQUARE, 0, 0,  70, 0, 0, 0, 0, LIN},
  {SQUARE,   2100, 2100,  90, 220, 220, 0, 0, LIN}, {SQUARE, 0, 0,  70, 0, 0, 0, 0, LIN},
  {SQUARE,   2100, 2100,  90, 220, 220, 0, 0, LIN}, {SQUARE, 0, 0, 450, 0, 0, 0, 0, LIN},
};
static const Seg LASER[] = {
  {SQUARE,   2600,  160, 170, 255, 120, 0, 0, EXP}, {SQUARE, 0, 0, 60, 0, 0, 0, 0, LIN},
  {SQUARE,   2600,  160, 170, 255, 120, 0, 0, EXP}, {SQUARE, 0, 0, 60, 0, 0, 0, 0, LIN},
  {SQUARE,   3200,  120, 320, 255,  60, 0, 0, EXP}, {SQUARE, 0, 0, 380, 0, 0, 0, 0, LIN},
};
static const Seg ROBOT[] = {
  {SQUARE,    220, 1300, 1300, 200, 200, 13, 0, RANDOM},
  {SQUARE,      0,    0,  250,   0,   0,  0, 0, LIN},
};
static const Seg COMPUTER[] = {
  {SINE,      700, 3400, 1000, 255, 255, 18, 0, RANDOM},
  {SINE,     3000, 3000,  150, 255,   0,  0, 0, LIN},
  {SINE,        0,    0,  200,   0,   0,  0, 0, LIN},
};
static const Seg UFO[] = {
  {SINE,      700, 1100, 1200, 255, 255, 8, 25, LIN},
  {SINE,     1100,  700, 1200, 255, 255, 8, 25, LIN},
};
static const Seg BOING[] = {
  {TRIANGLE,  220,  520,  80, 255, 255,  0,  0, EXP},
  {SINE,      520,  480, 700, 255,   0, 22, 22, LIN},
  {SINE,        0,    0, 200,   0,   0,  0,  0, LIN},
};
static const Seg SLIDE_WHISTLE[] = {
  {TRIANGLE,  500, 2100, 650, 200, 255, 6, 2, EXP},
  {TRIANGLE, 2100,  420, 550, 255, 200, 6, 2, EXP},
  {TRIANGLE,    0,    0, 180,   0,   0, 0, 0, LIN},
};
static const Seg RASPBERRY[] = {
  {SAW,       150,  120, 900, 255, 140, 28, 35, LIN},
  {SAW,         0,    0, 300,   0,   0,  0,  0, LIN},
};
static const Seg BIRDS[] = {
  {SINE,     2300, 4300,  60, 200, 255, 0, 0, EXP}, {SINE, 0, 0, 45, 0, 0, 0, 0, LIN},
  {SINE,     2500, 4600,  60, 200, 255, 0, 0, EXP}, {SINE, 0, 0, 45, 0, 0, 0, 0, LIN},
  {SINE,     4200, 2700, 110, 255, 120, 0, 0, EXP}, {SINE, 0, 0, 420, 0, 0, 0, 0, LIN},
};
static const Seg BUBBLES[] = {
  {SINE,      350, 1500,  70, 255,  60, 0, 0, EXP}, {SINE, 0, 0,  60, 0, 0, 0, 0, LIN},
  {SINE,      450, 1900,  60, 255,  60, 0, 0, EXP}, {SINE, 0, 0, 110, 0, 0, 0, 0, LIN},
  {SINE,      300, 1300,  90, 255,  60, 0, 0, EXP}, {SINE, 0, 0, 260, 0, 0, 0, 0, LIN},
};
static const Seg DRUMROLL[] = {
  {NOISE, 9000, 9000, 45, 255, 40, 0, 0, LIN}, {NOISE, 9000, 9000, 45, 230, 40, 0, 0, LIN},
  {NOISE, 9000, 9000, 45, 255, 40, 0, 0, LIN}, {NOISE, 9000, 9000, 45, 230, 40, 0, 0, LIN},
  {NOISE, 9000, 9000, 45, 255, 40, 0, 0, LIN}, {NOISE, 9000, 9000, 45, 230, 40, 0, 0, LIN},
  {NOISE, 9000, 9000, 45, 255, 40, 0, 0, LIN}, {NOISE, 9000, 9000, 45, 230, 40, 0, 0, LIN},
  {NOISE, 5000, 5000, 380, 255, 0, 0, 0, LIN}, {NOISE, 0, 0, 200, 0, 0, 0, 0, LIN},
};

// ---------------------------------------------------------------- the library
#define MEL(tune, voice) {tune, &voice, nullptr, 0}
#define FX(segs) {nullptr, nullptr, segs, N(segs)}

static const SoundInfo SOUNDS[] = {
  // Alarm
  {"siren", "Siren", "Alarm", "🚨", FX(SIREN)},
  {"whoop", "Whoop Whoop", "Alarm", "📢", FX(WHOOP)},
  {"klaxon", "Klaxon", "Alarm", "⚠️", FX(KLAXON)},
  {"beeps", "Beep Beep Beep", "Alarm", "⏰", FX(BEEPS)},
  {"charge", "Charge!", "Alarm", "🎺",
   MEL("charge:d=8,o=5,b=150:g,c6,e6,4.g6,e6,2g6,4p", BRASS)},
  // Goofy
  {"boing", "Boing", "Goofy", "🤪", FX(BOING)},
  {"slide", "Slide Whistle", "Goofy", "🎈", FX(SLIDE_WHISTLE)},
  {"raspberry", "Raspberry", "Goofy", "😛", FX(RASPBERRY)},
  {"dino", "Dino Stomp", "Goofy", "🦖",
   MEL("dino:d=8,o=4,b=130:4c,4c,g3,4c,p,4d#,4d#,c,4d#,p,4f,4f#,4g,2c5,4p", STOMP)},
  // Robot
  {"laser", "Laser Zap", "Robot", "🔫", FX(LASER)},
  {"robot", "Robot Talk", "Robot", "🤖", FX(ROBOT)},
  {"computer", "Computer", "Robot", "💻", FX(COMPUTER)},
  {"ufo", "UFO", "Robot", "🛸", FX(UFO)},
  // Playful
  {"birds", "Birdies", "Playful", "🐦", FX(BIRDS)},
  {"bubbles", "Bubbles", "Playful", "🫧", FX(BUBBLES)},
  {"drumroll", "Drum Roll", "Playful", "🥁", FX(DRUMROLL)},
  {"levelup", "Level Up!", "Playful", "⭐",
   MEL("levelup:d=16,o=5,b=140:c,e,g,c6,e,g,c6,e6,g,c6,e6,4g6,8p,8e6,2g6,4p", CHIP)},
  {"bumblebee", "Bumblebee", "Playful", "🐝",
   MEL("bee:d=16,o=5,b=120:e6,d#6,d6,c#6,d6,c#6,c6,b,c6,c#6,d6,c#6,d6,d#6,e6,d#6,e6,d#6,d6,c#6,d6,c#6,c6,b,"
       "c6,c#6,d6,c#6,c6,b,a#,a,8p", CHIP25)},
  // Musical
  {"mountainking", "Mountain King", "Musical", "👑",
   MEL("hall:d=8,o=5,b=160:a,b,c6,d6,e6,c6,4e6,d#6,b,4d#6,d6,a#,4d6,a,b,c6,d6,e6,c6,e6,a6,g6,e6,c6,e6,2g6,4p",
       PIPES)},
  {"williamtell", "Galloping Horse", "Musical", "🐎",
   MEL("tell:d=16,o=5,b=110:g,g,8g,g,g,8g,g,g,8c6,8d6,8e6,g,g,8g,g,g,8g,g,g,8e6,8d6,4c6,4p", CHIP)},
  {"cancan", "Can-Can", "Musical", "💃",
   MEL("cancan:d=8,o=5,b=180:4c,d,f,e,d,4g,4g,g,a,e,f,4d,4d,d,f,e,d,c,c6,b,a,g,f,e,d,2c,4p", CHIP)},
  {"entertainer", "The Entertainer", "Musical", "🎹",
   MEL("ent:d=8,o=5,b=140:d,d#,e,4c6,e,4c6,e,2c6,p,c6,d6,d#6,e6,c6,d6,4e6,b,4d6,2c6,4p", HARP)},
  {"furelise", "Für Elise", "Musical", "🎼",
   MEL("elise:d=8,o=5,b=140:e6,d#6,e6,d#6,e6,b,d6,c6,4a,p,c,e,a,4b,p,e,g#,b,4c6,p,e,e6,d#6,e6,d#6,e6,b,d6,c6,"
       "4a,p,c,e,a,4b,p,e,c6,b,2a,4p", HARP)},
  {"odetojoy", "Ode to Joy", "Musical", "🔔",
   MEL("ode:d=4,o=5,b=150:e,e,f,g,g,f,e,d,c,c,d,e,e.,8d,2d,e,e,f,g,g,f,e,d,c,c,d,e,d.,8c,2c,p", BELLS)},
  {"twinkle", "Twinkle Star", "Musical", "✨",
   MEL("twinkle:d=4,o=5,b=140:c,c,g,g,a,a,2g,f,f,e,e,d,d,2c,p", BELLS)},
  {"frerejacques", "Frère Jacques", "Musical", "🪈",
   MEL("jacques:d=4,o=5,b=150:c,d,e,c,c,d,e,c,e,f,2g,e,f,2g,8g,8a,8g,8f,e,c,8g,8a,8g,8f,e,c,c,g4,2c,c,g4,2c,p",
       FLUTE)},
  {"cucaracha", "La Cucaracha", "Musical", "🪇",
   MEL("cuca:d=8,o=5,b=180:c,c,c,4f,4a,p,c,c,c,4f,4a,4p,4f,f,e,e,d,d,2c,4p", BRASS)},
  {"macdonald", "Old MacDonald", "Musical", "🐮",
   MEL("farm:d=4,o=5,b=160:g,g,g,d,e,e,2d,b,b,a,a,2g,p", FLUTE)},
};

// ---------------------------------------------------------------- system chirps
static const Seg AWAKE[] = {
  {SINE,  800, 1600, 80, 160, 220, 0, 0, EXP}, {SINE, 0, 0, 40, 0, 0, 0, 0, LIN},
  {SINE, 1200, 2400, 90, 180, 0, 0, 0, EXP},
};
static const Seg SAD[] = {
  {TRIANGLE, 700, 380, 420, 200, 160, 5, 3, EXP}, {TRIANGLE, 0, 0, 80, 0, 0, 0, 0, LIN},
  {TRIANGLE, 520, 260, 600, 180, 0, 5, 3, EXP},
};
static const Seg SILENCED[] = {
  {SINE, 1500, 700, 140, 200, 0, 0, 0, EXP},
};
static const SoundDef SYSTEM[] = {
  FX(AWAKE), FX(SAD), FX(SILENCED),
  MEL("saved:d=16,o=6,b=140:c,e,g,4c7", BELLS),
};

int soundCount() { return N(SOUNDS); }
const SoundInfo &soundInfo(int i) { return SOUNDS[constrain(i, 0, soundCount() - 1)]; }
const SoundDef *systemSound(SystemSound s) { return &SYSTEM[s]; }

int soundFind(const char *key) {
  for (int i = 0; i < soundCount(); i++)
    if (!strcmp(SOUNDS[i].key, key)) return i;
  return -1;
}
