# Mobileer ME1000 (vendored)

Phil Burk's Mobileer SP-MIDI synthesizer, ME1000 edition (virtual-analog instruments, no wavetables, 32-bit fixed point). It is from [philburk/mobileer-synth](https://github.com/philburk/mobileer-synth) at commit `bb1ec40`, under Apache-2.0 (`LICENSE`, `NOTICE`).

**What's here:** the 14 engine `.c` files that MIDI-file playback links against, plus the 34 headers they include, copied into `src/spmidi/`. The only change is one `#undef assert` in `engine/spmidi.c`, because newlib already defines it (see `NOTICE`). The headers keep the upstream layout, because the sources include each other as `"spmidi/engine/…"` and `"spmidi/include/…"`.

| Kept | What it is |
|---|---|
| `midifile_parser.c`, `midifile_player.c` | Standard MIDI File parsing and timing |
| `spmidi.c`, `spmidi_fast.c`, `spmidi_util.c`, `spmidi_host.c` | MIDI channel logic, voice allocation, mixing |
| `spmidi_hybrid.c`, `spmidi_orchestra.c`, `spmidi_hybrid_presets_me1000.h` | The ME1000 voice and its General MIDI instrument presets |
| `oscillator.c`, `svfilter.c`, `adsr_envelope.c` | Oscillators, state-variable filter, envelopes |
| `dbl_list.c`, `memtools.c`, `spmidi_synth_util.c` | Support code |

**Left out:** wavetables (`export_1mb`, `wavetable.c`, `wave_manager.c`), DLS / XMF / ME3000, reverb, the compressor, the jukebox, the editor and the examples. Each one was checked by linking a test player without it.

**Config:** `config/spmidi_user_config.h` (ours) sets ME1000, 16 voices, mono, a 22.05 kHz maximum, one context and static allocation. `platformio.ini` passes `-DSPMIDI_USER_CONFIG -Ilib/mobileer/config` to every file, so the firmware sees the same struct sizes as the engine.

To update: re-copy the same files from a newer upstream commit, then check `pio run` and `test/render_sounds.sh`.
