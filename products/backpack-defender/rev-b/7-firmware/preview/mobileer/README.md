# Mobileer ringtone previews (Phase 1)

**Picked (now in the firmware):** `rings/FiverEcho`, `rings/RingAndTing_rt`, `rings/Tremolo1_SteelDrum`, `songs/EchoEcho_rt`, `songs/FurElise_rt` and `songs/UpAndDown_rt`. The firmware's own renders (22.05 kHz mono, 16 voices) are in `../` (`preview/<key>.wav`).

All 64 MIDI files from [philburk/mobileer-synth](https://github.com/philburk/mobileer-synth) `data/ringtones/phil/` (Apache-2.0, © Phil Burk / Mobileer), rendered on the Mac with the repo's own `bin/play_midifile` (commit `bb1ec40`).

## Two sets

| Folder | Engine build | Fits the ESP32-C3? |
|---|---|---|
| `rings/`, `songs/` | **ME1000**: virtual-analog instruments, no wavetables (`-DSPMIDI_ME2000=0 -DSPMIDI_ME3000=0`). The test binary is 134 KB | **Should**: the engine's README gives 20–30 KB of code, 14 KB of instruments and 20–30 KB of RAM. It hasn't been built for the C3 yet. This is what Phase 2 would port |
| `me2000/rings/`, `me2000/songs/` | The default CMake build (ME2000): adds the 1 MB `export_1mb` wavetable set (piano, guitar, sax, drums …). The test binary is 1 MB | Not really: the wavetables alone are ~1 MB of flash |

**Sound check:** I compared each pair's average spectrum in ⅓-octave bands.
- 10 files are **identical** in both builds, because their instruments are synthesized in both, and 4 more are close (under 3 dB).
- 50 differ by more than 3 dB. ME1000 is usually **brighter and buzzier**: its stand-ins for trumpet, sax, guitar and glockenspiel are oscillators and filters, not recordings.
- So listen to the ME1000 set to choose: it's what the C3 would play.

**Format:** 44.1 kHz stereo 16-bit. That's `play_midifile`'s hard-coded rate, and the songs pan their parts. The firmware would play mono at 16–22 kHz through a 20 mm speaker, so expect less bass and less sparkle on the device. Each file includes the engine's tail of up to 4 s while the last notes ring out.

`Brightness` is the spectral centroid of the ME1000 render. Low numbers sound mellow, high numbers sound shrill. A 20 mm speaker has little below ~600 Hz.

## Rings

| File | Group | Length | ME1000 vs ME2000 | Brightness (ME1000) |
|---|---|---|---|---|
| `rings/BirdChirp_rt.wav` | rings | 2.0 s | same (0.0 dB) | 2427 Hz |
| `rings/DuoDing.wav` | rings | 1.8 s | very different (10.6 dB) | 4623 Hz |
| `rings/FastHorn.wav` | rings | 4.0 s | different (6.9 dB) | 3086 Hz |
| `rings/FastTrumpet.wav` | rings | 4.0 s | very different (8.8 dB) | 3755 Hz |
| `rings/Fiver.wav` | rings | 2.9 s | very different (8.6 dB) | 3450 Hz |
| `rings/FiverEcho.wav` | rings | 2.9 s | same (0.0 dB) | 2084 Hz |
| `rings/FourLowFourHigh_rt.wav` | rings | 2.8 s | very different (8.1 dB) | 1637 Hz |
| `rings/LongHighTrill.wav` | rings | 10.0 s | very different (9.5 dB) | 7095 Hz |
| `rings/LongLowTrill.wav` | rings | 10.0 s | very different (8.2 dB) | 1483 Hz |
| `rings/LongLowTrill_Trumpet.wav` | rings | 10.0 s | very different (14.9 dB) | 4174 Hz |
| `rings/LoudArpeggios.wav` | rings | 6.5 s | very different (8.6 dB) | 2959 Hz |
| `rings/LoudHello.wav` | rings | 9.4 s | very different (7.2 dB) | 3063 Hz |
| `rings/LoudHello2_0rgan.wav` | rings | 9.4 s | same (0.0 dB) | 1370 Hz |
| `rings/LoudHello2_Trumpet.wav` | rings | 9.4 s | very different (8.3 dB) | 4142 Hz |
| `rings/LoudHocket.wav` | rings | 7.1 s | different (4.6 dB) | 1796 Hz |
| `rings/MonoMania.wav` | rings | 5.4 s | very different (8.3 dB) | 2003 Hz |
| `rings/OldPhoneAscending.wav` | rings | 52.9 s | same (0.0 dB) | 2399 Hz |
| `rings/OldPhoneShortLong_rt.wav` | rings | 2.4 s | same (0.0 dB) | 2315 Hz |
| `rings/OldPhone_rt.wav` | rings | 2.4 s | same (0.0 dB) | 2372 Hz |
| `rings/RingAndTing.wav` | rings | 4.0 s | different (5.3 dB) | 1169 Hz |
| `rings/RingAndTing_rt.wav` | rings | 4.0 s | very different (7.2 dB) | 1628 Hz |
| `rings/RiseUp.wav` | rings | 5.4 s | very different (7.5 dB) | 2876 Hz |
| `rings/SoftLoud.wav` | rings | 20.0 s | close (2.3 dB) | 598 Hz |
| `rings/Tremolo1.wav` | rings | 4.0 s | very different (9.6 dB) | 1580 Hz |
| `rings/Tremolo1_Square.wav` | rings | 4.0 s | very different (9.6 dB) | 1580 Hz |
| `rings/Tremolo1_SteelDrum.wav` | rings | 4.0 s | same (0.0 dB) | 2650 Hz |
| `rings/TwoTrills.wav` | rings | 3.6 s | very different (8.3 dB) | 4483 Hz |
| `rings/TwoTrillsMixed.wav` | rings | 3.6 s | close (1.4 dB) | 3279 Hz |
| `rings/TwoTrillsWiggle.wav` | rings | 3.6 s | very different (8.3 dB) | 4521 Hz |
| `rings/WarbleHigh_Glock.wav` | rings | 4.9 s | different (6.0 dB) | 1579 Hz |
| `rings/WarbleHigh_Guitar.wav` | rings | 4.9 s | very different (12.3 dB) | 1660 Hz |
| `rings/WarbleLow.wav` | rings | 4.9 s | very different (10.3 dB) | 3473 Hz |
| `rings/WarbleLow_Sax.wav` | rings | 4.9 s | very different (10.3 dB) | 3473 Hz |
| `rings/WarbleLow_Square.wav` | rings | 3.3 s | very different (9.4 dB) | 1515 Hz |

## Songs

| File | Group | Length | ME1000 vs ME2000 | Brightness (ME1000) |
|---|---|---|---|---|
| `songs/AnswerMeNow_rt.wav` | songs | 3.0 s | different (5.2 dB) | 1966 Hz |
| `songs/AuldToonOfAyr.wav` | songs | 14.5 s | different (3.7 dB) | 527 Hz |
| `songs/Bach_PartitaDMinor.wav` | songs | 13.6 s | different (4.9 dB) | 536 Hz |
| `songs/Bach_Sonata3EMajor.wav` | songs | 24.2 s | different (3.0 dB) | 538 Hz |
| `songs/Belgique_rt.wav` | songs | 8.0 s | different (4.7 dB) | 930 Hz |
| `songs/Belgique_sp_rt.wav` | songs | 8.0 s | different (4.7 dB) | 930 Hz |
| `songs/EchoEcho_rt.wav` | songs | 12.0 s | different (5.4 dB) | 901 Hz |
| `songs/FunToy8.wav` | songs | 28.0 s | different (3.8 dB) | 529 Hz |
| `songs/FunToy8_sp.wav` | songs | 28.0 s | different (3.8 dB) | 529 Hz |
| `songs/FurEliseCelesta_rt.wav` | songs | 9.0 s | same (0.0 dB) | 605 Hz |
| `songs/FurEliseOrgan_rt.wav` | songs | 9.0 s | same (0.0 dB) | 447 Hz |
| `songs/FurEliseSquare_rt.wav` | songs | 9.0 s | very different (7.7 dB) | 570 Hz |
| `songs/FurEliseSteelDrum_rt.wav` | songs | 9.0 s | same (0.0 dB) | 1083 Hz |
| `songs/FurEliseTrumpet_rt.wav` | songs | 9.0 s | different (3.7 dB) | 1815 Hz |
| `songs/FurElise_rt.wav` | songs | 9.0 s | different (4.8 dB) | 419 Hz |
| `songs/FurryLisa_rt.wav` | songs | 9.7 s | different (5.7 dB) | 467 Hz |
| `songs/LakeTahoe.wav` | songs | 18.3 s | different (3.0 dB) | 708 Hz |
| `songs/LakeTahoe_rt.wav` | songs | 11.4 s | close (2.8 dB) | 640 Hz |
| `songs/RingBop.wav` | songs | 18.0 s | different (3.2 dB) | 1396 Hz |
| `songs/RingBop_rt.wav` | songs | 6.0 s | different (5.0 dB) | 1276 Hz |
| `songs/RinginReggae_rt.wav` | songs | 8.0 s | different (6.3 dB) | 653 Hz |
| `songs/RinginReggae_sp_rt.wav` | songs | 8.0 s | different (6.3 dB) | 653 Hz |
| `songs/RockAndRing_rt.wav` | songs | 4.0 s | different (4.1 dB) | 861 Hz |
| `songs/Strasbourg.wav` | songs | 10.0 s | very different (9.1 dB) | 2709 Hz |
| `songs/TimeBefore.wav` | songs | 27.5 s | very different (8.3 dB) | 3330 Hz |
| `songs/TimeBefore_sp.wav` | songs | 27.5 s | very different (8.3 dB) | 3330 Hz |
| `songs/UpAndDown_rt.wav` | songs | 2.0 s | different (4.5 dB) | 1060 Hz |
| `songs/VibratingReggae_rt.wav` | songs | 8.3 s | different (4.7 dB) | 1256 Hz |
| `songs/rel_tuning.wav` | songs | 114.5 s | different (4.7 dB) (probably a tuning/timing test file, by its name and length) | 423 Hz |
| `songs/subdiv.wav` | songs | 167.7 s | close (1.0 dB) (probably a tuning/timing test file, by its name and length) | 674 Hz |

## Not in git

The WAVs total ~293 MB, so `7-firmware/.gitignore` keeps them out of commits. Only this README is tracked. Re-render from a clone of the repo: build `spmidi` with CMake (plus `-DCMAKE_C_FLAGS=-DSPMIDI_ME2000=0` for ME1000), then run `bin/play_midifile -w<out.wav> <file.mid>` from the build folder.
