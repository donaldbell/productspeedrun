// Renders every sound in the library to preview/<key>.wav on a desktop (no ESP32 needed), and checks
// each one ends, isn't silent and doesn't clip. Build + run: test/render_sounds.sh
#include <stdio.h>
#include "../src/sounds.h"

static void wav(const char *path, const int16_t *s, uint32_t n) {
  FILE *f = fopen(path, "wb");
  uint32_t rate = SYNTH_RATE, bytes = n * 2, v32;
  uint16_t v16;
  fwrite("RIFF", 1, 4, f); v32 = 36 + bytes; fwrite(&v32, 4, 1, f); fwrite("WAVEfmt ", 1, 8, f);
  v32 = 16; fwrite(&v32, 4, 1, f); v16 = 1; fwrite(&v16, 2, 1, f); fwrite(&v16, 2, 1, f);
  fwrite(&rate, 4, 1, f); v32 = rate * 2; fwrite(&v32, 4, 1, f); v16 = 2; fwrite(&v16, 2, 1, f);
  v16 = 16; fwrite(&v16, 2, 1, f); fwrite("data", 1, 4, f); fwrite(&bytes, 4, 1, f);
  fwrite(s, 2, n, f);
  fclose(f);
}

static int render(const char *key, const SoundDef *def, const char *dir) {
  static Synth synth;
  static int16_t buf[SYNTH_RATE * 20];
  synth.start(def);
  uint32_t n = 0;
  while (n < sizeof(buf) / 2 - 256 && synth.render(buf + n, 256)) n += 256;
  n += 256;
  int32_t peak = 0, clipped = 0; double sq = 0;
  for (uint32_t i = 0; i < n; i++) {
    peak = max<int32_t>(peak, abs(buf[i]));
    sq += (double)buf[i] * buf[i];
    clipped += i && abs(buf[i]) == 32767 && buf[i] == buf[i - 1];   // flat top = clipped
  }
  double secs = (double)n / SYNTH_RATE, rms = sqrt(sq / n);
  bool ok = secs < 19 && peak > 3000 && sqrt(sq / n) > 2000 && clipped < 4;
  printf("%-14s %5.2f s  peak %5d  rms %5.0f  %s\n", key, secs, peak, rms, ok ? "ok" : "CHECK");
  char path[256];
  snprintf(path, sizeof(path), "%s/%s.wav", dir, key);
  wav(path, buf, n);
  return ok ? 0 : 1;
}

int main(int argc, char **argv) {
  const char *dir = argc > 1 ? argv[1] : "preview";
  int bad = 0;
  for (int i = 0; i < soundCount(); i++) bad += render(soundInfo(i).key, &soundInfo(i).def, dir);
  const char *sys[] = {"_awake", "_sad", "_silenced", "_saved"};
  for (int i = 0; i < 4; i++) bad += render(sys[i], systemSound((SystemSound)i), dir);
  printf("%d sounds, %d to check\n", soundCount() + 4, bad);
  return bad != 0;
}
