#include "synth.h"
#include <math.h>

static int16_t SINE_T[256], ORGAN_T[256];
static const int32_t ENV_MAX = 32767 << 8;     // ~2^23, so scaling by the envelope is a shift
// FM depth at full envelope is 2^16 x the modulator (about half a cycle): env_ >> 7

// C4..B4 in milli-Hz; other octaves are shifts of these
static const uint32_t BASE_MHZ[12] = {261626, 277183, 293665, 311127, 329628, 349228,
                                      369994, 391995, 415305, 440000, 466164, 493883};

static void tablesInit() {
  static bool done = false;
  if (done) return;
  for (int i = 0; i < 256; i++) {
    float a = i * 2 * PI / 256;
    SINE_T[i] = (int16_t)(32767 * sinf(a));
    ORGAN_T[i] = (int16_t)(32767 * (sinf(a) + 0.5f * sinf(2 * a) + 0.3f * sinf(3 * a) + 0.15f * sinf(4 * a)) / 1.55f);
  }
  done = true;
}

static uint32_t mhzToInc(uint64_t mhz) { return (uint32_t)((mhz << 32) / (SYNTH_RATE * 1000ULL)); }
static uint32_t hzToInc(uint32_t hz) { return mhzToInc((uint64_t)hz * 1000); }
static uint32_t msToSamples(uint32_t ms) { return ms * (SYNTH_RATE / 1000); }

void Synth::start(const SoundDef *def) {
  tablesInit();
  def_ = def;
  left_ = 0;
  phase_ = lfoPhase_ = modPhase_ = 0;
  stage_ = 4;
  env_ = 0;
  if (def->rtttl) {
    // header "name:d=4,o=5,b=140:"
    const char *p = strchr(def->rtttl, ':');
    p = p ? p + 1 : def->rtttl;
    defDur_ = 4; defOct_ = 6; bpm_ = 63;
    while (*p && *p != ':') {
      char k = tolower(*p);
      if ((k == 'd' || k == 'o' || k == 'b') && p[1] == '=') {
        int v = atoi(p + 2);
        if (k == 'd' && v > 0) defDur_ = v;
        if (k == 'o' && v >= 3 && v <= 8) defOct_ = v;
        if (k == 'b' && v > 0) bpm_ = v;
      }
      p++;
    }
    p_ = *p ? p + 1 : p;
  } else {
    seg_ = 0;
    segStart();
  }
}

// ---------------------------------------------------------------- melodies

bool Synth::nextNote() {
  const char *p = p_;
  while (*p == ',' || *p == ' ') p++;
  if (!*p) return false;
  int dur = 0;
  while (isdigit(*p)) dur = dur * 10 + (*p++ - '0');
  if (!dur) dur = defDur_;
  bool dotted = false;
  if (*p == '.') { dotted = true; p++; }   // "4.g6" as well as "4g6."
  static const int8_t SEMI[7] = {9, 11, 0, 2, 4, 5, 7};   // a b c d e f g
  char c = tolower(*p);
  int semi = -1;
  if (c >= 'a' && c <= 'g') semi = SEMI[c - 'a'];
  if (*p) p++;
  if (*p == '#') { semi++; p++; }
  if (*p == '.') { dotted = true; p++; }
  int oct = defOct_;
  if (isdigit(*p)) oct = *p++ - '0';
  if (*p == '.') { dotted = true; p++; }
  while (*p && *p != ',') p++;
  p_ = p;

  // a whole note is 4 beats
  uint32_t samples = (uint32_t)SYNTH_RATE * 60 * 4 / ((uint32_t)bpm_ * dur);
  if (dotted) samples += samples / 2;
  if (semi < 0) {                      // rest
    stage_ = 4;
    env_ = 0;
    left_ = gate_ = samples;
    return true;
  }
  if (semi == 12) { semi = 0; oct++; }  // b#
  oct += def_->voice->octave;
  uint32_t mhz = BASE_MHZ[semi];
  mhz = oct >= 4 ? mhz << (oct - 4) : mhz >> (4 - oct);
  noteOn(mhz, samples);
  return true;
}

void Synth::noteOn(uint32_t mhz, uint32_t samples) {
  const Voice &v = *def_->voice;
  inc_ = mhzToInc(mhz);
  left_ = samples;
  gate_ = v.wave == PLUCK ? samples : samples * 7 / 8;
  stage_ = 0;
  env_ = 0;
  envStep_ = ENV_MAX / (int32_t)max<uint32_t>(1, msToSamples(v.attackMs));
  lfoInc_ = (uint32_t)(((uint64_t)v.vibratoHz10 << 32) / (SYNTH_RATE * 10));
  vibDepth_ = (uint32_t)((uint64_t)inc_ * v.vibratoPct10 / 1000);
  if (v.wave == PLUCK) {
    ksLen_ = constrain((uint32_t)SYNTH_RATE * 1000 / mhz, 2u, (uint32_t)(sizeof(ks_) / sizeof(ks_[0])));
    for (int i = 0; i < ksLen_; i++) {
      noise_ = (noise_ >> 1) ^ (-(noise_ & 1) & 0xB400);
      ks_[i] = (int16_t)noise_ / 2;
    }
    ksPos_ = 0;
  }
}

int32_t Synth::voiceSample() {
  const Voice &v = *def_->voice;
  // envelope
  switch (stage_) {
    case 0:
      env_ += envStep_;
      if (env_ >= ENV_MAX) {
        env_ = ENV_MAX;
        stage_ = 1;
        envStep_ = (ENV_MAX - (v.sustain << 15)) / (int32_t)max<uint32_t>(1, msToSamples(v.decayMs));
      }
      break;
    case 1:
      env_ -= envStep_;
      if (env_ <= (int32_t)(v.sustain << 15)) { env_ = v.sustain << 15; stage_ = 2; }
      break;
    case 3:
      env_ -= envStep_;
      if (env_ <= 0) { env_ = 0; stage_ = 4; }
      break;
    case 4:
      return 0;
  }
  if (gate_ && --gate_ == 0 && stage_ < 3) {
    stage_ = 3;
    envStep_ = env_ / (int32_t)max<uint32_t>(1, msToSamples(v.releaseMs));
    if (!envStep_) envStep_ = 1;
  }

  uint32_t inc = inc_;
  if (v.vibratoPct10) {
    lfoPhase_ += lfoInc_;
    inc += (int32_t)(((int64_t)vibDepth_ * SINE_T[lfoPhase_ >> 24]) >> 15);
  }
  int32_t s;
  switch (v.wave) {
    case BELL: {
      int32_t idx = env_ >> 7;
      int32_t mod = SINE_T[modPhase_ >> 24];
      modPhase_ += inc / 2 * 7;          // modulator at 3.5 x the note: a glockenspiel-ish clang
      s = SINE_T[(phase_ + (uint32_t)(mod * idx)) >> 24];
      break;
    }
    case PLUCK: {
      int16_t a = ks_[ksPos_];
      uint16_t nx = ksPos_ + 1 == ksLen_ ? 0 : ksPos_ + 1;
      // gentle low-pass (15:1, not the classic 1:1 average, which kills a 1 kHz string in ~50 ms at 16 kHz)
      ks_[ksPos_] = (int16_t)(((int32_t)a * 15 + ks_[nx]) * 1023 >> 14);
      ksPos_ = nx;
      s = a * 2;
      break;
    }
    case NOISE: {
      uint32_t before = phase_;
      if (phase_ + inc < before) {
        noise_ = (noise_ >> 1) ^ (-(noise_ & 1) & 0xB400);
        noiseVal_ = (int16_t)noise_;
      }
      s = noiseVal_;
      break;
    }
    default: {
      uint32_t ph = phase_;
      switch (v.wave) {
        case SQUARE: s = ph < 0x80000000u ? 24000 : -24000; break;
        case PULSE: s = ph < 0x40000000u ? 24000 : -24000; break;
        case SAW: s = (int32_t)(ph >> 16) - 32768; break;
        case TRIANGLE: { int32_t q = ph >> 16; s = q < 32768 ? q * 2 - 32768 : (65535 - q) * 2 - 32768; break; }
        case ORGAN: s = ORGAN_T[ph >> 24]; break;
        default: s = SINE_T[ph >> 24]; break;
      }
    }
  }
  phase_ += inc;
  return (int32_t)(((int64_t)s * env_) >> 23);
}

// ---------------------------------------------------------------- effects

void Synth::segStart() {
  const Seg &s = def_->segs[seg_];
  segN_ = left_ = max<uint32_t>(1, msToSamples(s.ms));
  uint32_t i0 = hzToInc(s.f0), i1 = hzToInc(s.f1 ? s.f1 : s.f0);
  inc_ = i0;
  dInc_ = 0;
  kInc_ = 1u << 30;
  if (s.flags & RANDOM) {
    lfoPhase_ = 0xFFFFFFFF;              // pick a pitch on the first sample
  } else if ((s.flags & EXP) && i0 && i1 != i0) {
    kInc_ = (uint32_t)(pow((double)i1 / i0, 1.0 / segN_) * (1u << 30));
  } else {
    dInc_ = ((int32_t)i1 - (int32_t)i0) / (int32_t)segN_;
  }
  lfoInc_ = hzToInc(s.lfoHz);
  vol_ = s.f0 ? s.v0 << 16 : 0;
  dVol_ = s.f0 ? (((int32_t)s.v1 - s.v0) << 16) / (int32_t)segN_ : 0;
}

int32_t Synth::segSample() {
  const Seg &sg = def_->segs[seg_];
  if (!sg.f0) return 0;
  uint32_t inc = inc_;
  uint32_t lp = lfoPhase_;
  lfoPhase_ += lfoInc_;
  if (sg.flags & RANDOM) {
    if (lfoPhase_ < lp || lp == 0xFFFFFFFF) {
      noise_ = (noise_ >> 1) ^ (-(noise_ & 1) & 0xB400);
      uint32_t hz = sg.f0 + noise_ % (uint32_t)max(1, (int)sg.f1 - (int)sg.f0);
      inc_ = hzToInc(hz);
    }
    inc = inc_;
  } else if (sg.lfoPct) {
    int32_t depth = (int32_t)(((int64_t)inc * (sg.lfoPct * 328)) >> 15);   // lfoPct % of the pitch
    inc += (int32_t)(((int64_t)depth * SINE_T[lfoPhase_ >> 24]) >> 15);
  }

  int32_t s;
  uint32_t ph = phase_;
  switch (sg.wave) {
    case SQUARE: s = ph < 0x80000000u ? 24000 : -24000; break;
    case PULSE: s = ph < 0x40000000u ? 24000 : -24000; break;
    case SAW: s = (int32_t)(ph >> 16) - 32768; break;
    case TRIANGLE: { int32_t q = ph >> 16; s = q < 32768 ? q * 2 - 32768 : (65535 - q) * 2 - 32768; break; }
    case ORGAN: s = ORGAN_T[ph >> 24]; break;
    case NOISE:
      if (ph + inc < ph) {
        noise_ = (noise_ >> 1) ^ (-(noise_ & 1) & 0xB400);
        noiseVal_ = (int16_t)noise_;
      }
      s = noiseVal_;
      break;
    default: s = SINE_T[ph >> 24]; break;
  }
  phase_ += inc;
  if (!(sg.flags & RANDOM)) {
    if (sg.flags & EXP) inc_ = (uint32_t)(((uint64_t)inc_ * kInc_) >> 30);
    else inc_ += dInc_;
  }
  int32_t out = (s * (vol_ >> 16)) >> 8;
  vol_ += dVol_;
  return out;
}

// ---------------------------------------------------------------- both

bool Synth::render(int16_t *buf, int n) {
  for (int i = 0; i < n; i++) {
    while (def_ && !left_) {
      bool more;
      if (def_->rtttl) {
        more = nextNote();
      } else {
        more = ++seg_ < def_->nsegs;
        if (more) segStart();
      }
      if (!more) def_ = nullptr;
    }
    if (!def_) {
      memset(buf + i, 0, (n - i) * sizeof(int16_t));
      return false;
    }
    int32_t s = def_->rtttl ? voiceSample() : segSample();
    buf[i] = (int16_t)constrain(s, -32767, 32767);
    left_--;
  }
  return true;
}
