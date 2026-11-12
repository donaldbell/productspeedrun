/* Backpack Defender's build of the Mobileer engine (read by spmidi_config.h when SPMIDI_USER_CONFIG is defined).
 * ME1000: virtual-analog instruments only, no wavetables. Mono, one context, one player, static memory.
 * The firmware and test/render_sounds.sh both compile with this file, so they make the same sound. */
#ifndef BD_SPMIDI_USER_CONFIG_H
#define BD_SPMIDI_USER_CONFIG_H

#define SPMIDI_ME3000                  (0)
#define SPMIDI_ME2000                  (0)     /* = ME1000 */
#define SPMIDI_PRODUCTION              (1)     /* no error-message text in RAM */
#define SPMIDI_MAX_VOICES              (16)    /* FiverEcho's echo tails want ~28; 16 sounds the same (NOTES.md) */
#define SPMIDI_MAX_SAMPLES_PER_FRAME   (1)     /* mono: one speaker */
#define SPMIDI_MAX_SAMPLE_RATE         (22050)
#define SPMIDI_MAX_NUM_CONTEXTS        (1)
#define SPMIDI_MAX_NUM_PLAYERS         (1)
#define SPMIDI_SUPPORT_MALLOC          (0)     /* everything in static pools: RAM use shows in the link map */
#define SPMIDI_SUPPORT_LOADING         (0)
#define SPMIDI_USE_PRINTF              (0)

#endif
