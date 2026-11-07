// Baby Monitor Monitor: the radio protocol between the sensor and the watch (ESP-NOW, shared by both firmwares).
//
//   sensor ── STATUS (level, alert, flags) every 2 s and at once on any change ──► watch
//   sensor ◄── WATCH (battery, buzzing, RSSI) once per new STATUS ─────────────── watch
//   sensor ── TEST (hold the snooze bar 3 s) ─────────────────────────────────────► watch
//   sensor ── PAIR_OFFER (broadcast, 30 s after a 3 s hold) ──────────────────────► watch on its charger / unpaired
//   sensor ◄── PAIR_ACCEPT ──────────────────────────────────────────────────────── watch
//
// The sensor decides everything (sound level, whether the watch should buzz, the "I'm awake" ack). The watch
// just follows `alert` and turns it into a haptic pattern, so the two can never disagree about whether to buzz.
// The watch's radio is duty-cycled to save its 150 mAh cell (it listens BMM_WAKE_WINDOW_MS in every
// BMM_WAKE_INTERVAL_MS), so the sensor sends every packet BMM_TX_REPEATS times, BMM_TX_SPACING_MS apart.
// The watch drops repeats by seq.
#pragma once
#include <stdint.h>

#define BMM_MAGIC           0x4D42u     // "BM"
#define BMM_PROTO_VERSION   1
#define BMM_WIFI_CHANNEL    1           // fixed: there's no access point to follow

// --- timing (ms)
#define BMM_HEARTBEAT_MS      2000      // sensor sends STATUS at least this often
#define BMM_LINK_LOST_MS     10000      // no STATUS (watch) / WATCH (sensor) for this long = link lost
#define BMM_WAKE_INTERVAL_MS   200      // watch radio: wakes every ...
#define BMM_WAKE_WINDOW_MS      50      // ... for this long (25 % RX duty)
#define BMM_TX_REPEATS           5      // sensor: copies of each packet ...
#define BMM_TX_SPACING_MS       40      // ... this far apart
#define BMM_PAIR_WINDOW_MS   30000      // sensor offers pairing this long after a 3 s hold
#define BMM_PAIR_OFFER_MS     1000      // one PAIR_OFFER (burst) per second while offering
#define BMM_ESCALATE_MS      45000      // watch: an un-acked alert steps up one level this often

// A burst must hit a wake window wherever it starts: copies no further apart than the window (so none can
// jump over one), and spread over at least the gap between windows.
_Static_assert(BMM_TX_SPACING_MS <= BMM_WAKE_WINDOW_MS, "repeats could step over a watch wake window");
_Static_assert((BMM_TX_REPEATS - 1) * BMM_TX_SPACING_MS >= BMM_WAKE_INTERVAL_MS - BMM_WAKE_WINDOW_MS,
               "a burst is shorter than the gap between watch wake windows");
_Static_assert(BMM_TX_REPEATS * BMM_TX_SPACING_MS < BMM_HEARTBEAT_MS, "bursts would overlap heartbeats");
_Static_assert(BMM_LINK_LOST_MS >= 4 * BMM_HEARTBEAT_MS, "link-lost must allow a few missed heartbeats");

typedef enum {
    BMM_MSG_STATUS = 1,         // sensor -> watch
    BMM_MSG_WATCH = 2,          // watch -> sensor (reply to each new STATUS / TEST)
    BMM_MSG_TEST = 3,           // sensor -> watch: play the test pattern
    BMM_MSG_PAIR_OFFER = 4,     // sensor -> broadcast
    BMM_MSG_PAIR_ACCEPT = 5,    // watch -> sensor
} bmm_msg_type_t;

// Sound levels (the sensor's verdict, 0-3)
enum { BMM_LEVEL_QUIET = 0, BMM_LEVEL_FUSS = 1, BMM_LEVEL_CRY = 2, BMM_LEVEL_SCREAM = 3, BMM_LEVEL_MAX = 3 };

// STATUS flags
#define BMM_SF_ACKED      0x01  // a parent pressed "I'm awake" for the current episode
#define BMM_SF_PAIRING    0x02  // the sensor is offering pairing
#define BMM_SF_LOW_BATT   0x04  // sensor cell low
#define BMM_SF_CHARGING   0x08  // sensor charger active (CHG_STAT low)
#define BMM_SF_FAKE_AUDIO 0x80  // bench build: the level is synthetic

// WATCH flags
#define BMM_WF_BUZZING    0x01
#define BMM_WF_CHARGING   0x02
#define BMM_WF_LOW_BATT   0x04
#define BMM_WF_LINK_LOST  0x08  // (set in the first reply after the watch had lost the sensor)

typedef struct __attribute__((packed)) {
    uint16_t magic;             // BMM_MAGIC
    uint8_t version;            // BMM_PROTO_VERSION
    uint8_t type;               // bmm_msg_type_t
    uint16_t seq;               // sender's packet counter (repeats keep the same seq)
} bmm_hdr_t;

typedef struct __attribute__((packed)) {
    bmm_hdr_t h;
    uint8_t level;              // what the sensor hears now (0-3, after attack / release smoothing)
    uint8_t alert;              // what the watch should do: 0 = nothing, 1-3 = buzz at that level
    uint8_t flags;              // BMM_SF_*
    uint8_t spl_db;             // last window's sound level, dB SPL (logs / tuning)
    uint8_t floor_db;           // the sensor's noise-floor estimate, dB SPL
    uint8_t reserved;
    uint16_t vbat_mv;           // sensor cell
    uint32_t alert_ms;          // how long this alert has run (the watch escalates from it, so a reboot resumes)
} bmm_status_t;

typedef struct __attribute__((packed)) {
    bmm_hdr_t h;
    uint16_t ack_seq;           // the STATUS / TEST seq this answers
    uint16_t vbat_mv;           // watch cell
    uint8_t flags;              // BMM_WF_*
    int8_t rssi;                // RSSI the watch saw on that packet, dBm
} bmm_watch_t;

typedef struct __attribute__((packed)) {
    bmm_hdr_t h;
} bmm_bare_t;                   // TEST, PAIR_OFFER, PAIR_ACCEPT

_Static_assert(sizeof(bmm_status_t) <= 250 && sizeof(bmm_watch_t) <= 250, "ESP-NOW payloads are <= 250 bytes");

static inline int bmm_valid(const void *data, int len, int min_len) {
    const bmm_hdr_t *h = (const bmm_hdr_t *)data;
    return len >= min_len && len >= (int)sizeof(bmm_hdr_t) && h->magic == BMM_MAGIC && h->version == BMM_PROTO_VERSION;
}

static inline const char *bmm_level_name(int level) {
    static const char *const names[] = {"quiet", "fussing", "crying", "screaming"};
    return (level >= 0 && level <= BMM_LEVEL_MAX) ? names[level] : "?";
}
