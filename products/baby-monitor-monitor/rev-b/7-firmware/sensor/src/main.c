// Baby Monitor Monitor Rev B: sensor firmware (ESP32-C6-MINI-1). See ../../NOTES.md.
//
// Listens to the baby monitor's speaker, turns the sound into a level 0-3 and tells the watch how hard to buzz.
// The snooze bar: tap = "I'm awake" (the watch stops), hold 3 s = test buzz on the watch + 30 s pairing offer.
//
// Tasks: audio (I2S -> 250 ms windows), tx (sends each packet BMM_TX_REPEATS times), and this main loop
// (20 ms tick: button, detector, alert / ack logic, lights, radio replies).
#include <string.h>
#include "audio.h"
#include "bmm_common.h"
#include "bmm_protocol.h"
#include "config.h"
#include "detector.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_mac.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "pins.h"

static const char *TAG = "sensor";

#define PWM_STATUS 0                // LEDC channel for the green status LED
#define TICK_MS 20

// ---------------------------------------------------------------- radio: tx task with repeats
typedef struct {
    uint8_t mac[6];
    uint8_t len;
    uint8_t data[sizeof(bmm_status_t)];
} tx_item_t;

static QueueHandle_t s_tx_q;        // a few packets deep; each gets its full burst (160 ms)
static QueueHandle_t s_rx_q;
static uint16_t s_seq;

typedef struct {
    uint8_t mac[6];
    int8_t rssi;
    uint8_t len;
    uint8_t data[32];
} rx_item_t;

static void tx_task(void *arg) {
    tx_item_t it;
    for (;;) {
        xQueueReceive(s_tx_q, &it, portMAX_DELAY);
        for (int i = 0; i < BMM_TX_REPEATS; i++) {      // one burst per packet, so it lands in a watch wake window
            bmm_link_send(it.mac, it.data, it.len);
            if (i < BMM_TX_REPEATS - 1) vTaskDelay(pdMS_TO_TICKS(BMM_TX_SPACING_MS));
        }
    }
}

static void queue_tx(const uint8_t mac[6], void *pkt, int len, uint8_t type) {
    bmm_hdr_t *h = pkt;
    h->magic = BMM_MAGIC, h->version = BMM_PROTO_VERSION, h->type = type, h->seq = ++s_seq;
    tx_item_t it = {.len = (uint8_t)len};
    memcpy(it.mac, mac, 6);
    memcpy(it.data, pkt, len);
    if (xQueueSend(s_tx_q, &it, 0) != pdTRUE) ESP_LOGW(TAG, "tx queue full: packet %u dropped", h->seq);
}

static void on_rx(const uint8_t mac[6], const uint8_t *data, int len, int8_t rssi) {   // Wi-Fi task
    rx_item_t it = {.rssi = rssi, .len = (uint8_t)(len > 32 ? 32 : len)};
    memcpy(it.mac, mac, 6);
    memcpy(it.data, data, it.len);
    xQueueSend(s_rx_q, &it, 0);
}

// ---------------------------------------------------------------- state
static struct {
    bool paired;
    uint8_t peer[6];
    // sound
    detector_t det;
    int level, instant;
    float spl_db;
    int64_t last_window_ms, quiet_since_ms;
    // alert / ack
    int alert, acked_level;
    bool acked;
    int64_t alert_start_ms, snooze_until_ms;
    // watch
    int64_t watch_seen_ms;
    bmm_watch_t watch;
    // pairing
    int64_t pair_until_ms, next_offer_ms;
    // power
    int vbat_mv;
    bool charging;
    // ui
    int64_t flash_until_ms;
    uint8_t flash_rgb[3];
    int flash_period_ms;
    bool pressed;
    int64_t press_ms;
    bool hold_fired;
    int64_t last_status_tx_ms;
    uint8_t last_sent_alert, last_sent_level, last_sent_flags;
} S;

static bool watch_linked(int64_t now) { return S.watch_seen_ms && now - S.watch_seen_ms < BMM_LINK_LOST_MS; }

static uint8_t status_flags(int64_t now) {
    uint8_t f = 0;
    if (S.acked) f |= BMM_SF_ACKED;
    if (now < S.pair_until_ms) f |= BMM_SF_PAIRING;
    if (S.vbat_mv && S.vbat_mv < VBAT_LOW_MV) f |= BMM_SF_LOW_BATT;
    if (S.charging) f |= BMM_SF_CHARGING;
#ifdef BMM_FAKE_AUDIO
    f |= BMM_SF_FAKE_AUDIO;
#endif
    return f;
}

static void send_status(int64_t now) {
    if (!S.paired) return;
    bmm_status_t p = {
        .level = (uint8_t)S.level, .alert = (uint8_t)S.alert, .flags = status_flags(now),
        .spl_db = (uint8_t)(S.spl_db < 0 ? 0 : S.spl_db > 255 ? 255 : S.spl_db),
        .floor_db = (uint8_t)S.det.floor_db, .vbat_mv = (uint16_t)S.vbat_mv,
        .alert_ms = S.alert ? (uint32_t)(now - S.alert_start_ms) : 0,
    };
    queue_tx(S.peer, &p, sizeof p, BMM_MSG_STATUS);
    S.last_status_tx_ms = now;
    S.last_sent_alert = p.alert, S.last_sent_level = p.level, S.last_sent_flags = p.flags;
}

static void flash(const uint8_t rgb[3], int ms, int period_ms, int64_t now) {
    memcpy(S.flash_rgb, rgb, 3);
    S.flash_until_ms = now + ms;
    S.flash_period_ms = period_ms;
}

// ---------------------------------------------------------------- alert / ack
static void update_alert(int64_t now) {
    int was = S.alert;
    if (S.level == 0) {
        if (!S.quiet_since_ms) S.quiet_since_ms = now;
        if (S.acked && now - S.quiet_since_ms >= ACK_RESET_QUIET_MS) {
            S.acked = false;            // episode over: the next sound alerts again
            ESP_LOGI(TAG, "quiet for %d s: ack cleared", ACK_RESET_QUIET_MS / 1000);
        }
        S.alert = 0;
    } else {
        S.quiet_since_ms = 0;
        if (S.acked && (S.level > S.acked_level || now >= S.snooze_until_ms)) {
            S.acked = false;            // louder than when they pressed, or the snooze ran out
            ESP_LOGI(TAG, "re-alert: level %d (acked at %d)%s", S.level, S.acked_level,
                     now >= S.snooze_until_ms ? ", snooze over" : "");
        }
        S.alert = S.acked ? 0 : S.level;
    }
    if (S.alert && !was) S.alert_start_ms = now;
    if (S.alert != was) ESP_LOGI(TAG, "alert %d -> %d (%s, %.0f dB, floor %.0f)", was, S.alert,
                                 bmm_level_name(S.level), S.spl_db, S.det.floor_db);
}

static void on_tap(int64_t now) {
    static const uint8_t ack_rgb[3] = BAR_ACK_FLASH, white[3] = {60, 60, 60};
    if (S.alert || S.level) {
        S.acked = true;
        S.acked_level = S.level;
        S.snooze_until_ms = now + SNOOZE_MS;
        S.alert = 0;
        ESP_LOGI(TAG, "I'm awake: alert stopped, snoozed %d min unless it gets louder", SNOOZE_MS / 60000);
        flash(ack_rgb, 1500, 250, now);
        send_status(now);
    } else {
        flash(white, 300, 0, now);      // nothing to stop: just show the press registered
    }
}

static void on_hold(int64_t now) {
    ESP_LOGI(TAG, "hold: test buzz + pairing offer for %d s", BMM_PAIR_WINDOW_MS / 1000);
    S.pair_until_ms = now + BMM_PAIR_WINDOW_MS;
    S.next_offer_ms = now;
    if (S.paired) {
        bmm_bare_t t;
        queue_tx(S.peer, &t, sizeof t, BMM_MSG_TEST);
    }
}

static void poll_button(int64_t now) {
    static int raw_last = 1;
    static int64_t raw_since;
    int raw = gpio_get_level(PIN_BTN);
    if (raw != raw_last) raw_last = raw, raw_since = now;
    if (now - raw_since < BTN_DEBOUNCE_MS) return;
    bool down = raw == 0;
    if (down && !S.pressed) {
        S.pressed = true, S.press_ms = now, S.hold_fired = false;
    } else if (!down && S.pressed) {
        S.pressed = false;
        if (!S.hold_fired) on_tap(now);         // any press shorter than a hold is a tap
    } else if (down && !S.hold_fired && now - S.press_ms >= BTN_HOLD_MS) {
        S.hold_fired = true;
        on_hold(now);
    }
}

// ---------------------------------------------------------------- radio in
static void handle_rx(const rx_item_t *it, int64_t now) {
    const bmm_hdr_t *h = (const bmm_hdr_t *)it->data;
    if (!bmm_valid(it->data, it->len, sizeof(bmm_hdr_t))) return;
    if (h->type == BMM_MSG_PAIR_ACCEPT && now < S.pair_until_ms) {
        bool same = S.paired && !memcmp(S.peer, it->mac, 6);
        memcpy(S.peer, it->mac, 6);
        S.paired = true;
        S.watch_seen_ms = now;
        if (!same) bmm_peer_save(S.peer);
        S.pair_until_ms = 0;
        static const uint8_t green[3] = BAR_ACK_FLASH;
        flash(green, 1200, 200, now);
        ESP_LOGI(TAG, "%s watch " BMM_MAC_FMT, same ? "confirmed" : "paired new", BMM_MAC_ARGS(it->mac));
        send_status(now);
        return;
    }
    if (!S.paired || memcmp(S.peer, it->mac, 6)) return;        // not our watch
    if (h->type == BMM_MSG_WATCH && it->len >= (int)sizeof(bmm_watch_t)) {
        bool was = watch_linked(now);
        memcpy(&S.watch, it->data, sizeof S.watch);
        S.watch_seen_ms = now;
        if (!was) ESP_LOGI(TAG, "watch linked (RSSI %d / %d dBm, %d mV)", it->rssi, S.watch.rssi, S.watch.vbat_mv);
    }
}

// ---------------------------------------------------------------- lights
static void scale_set(const uint8_t rgb[3], int pct) {
    int k = pct * BAR_SCALE;            // pct x BAR_SCALE / 10000
    bmm_rgb_set(rgb[0] * k / 10000, rgb[1] * k / 10000, rgb[2] * k / 10000);
}

static void update_lights(int64_t now) {
    static const uint8_t armed[3] = BAR_ARMED, alert[3] = BAR_ALERT, acked[3] = BAR_ACKED, pairing[3] = BAR_PAIRING,
                         lost[3] = BAR_LOST, unpaired[3] = BAR_UNPAIRED, low[3] = BAR_LOW_BATT, press[3] = BAR_PRESS;
    if (S.pressed && !S.hold_fired) {
        // Brightens while held; turns blue as the hold nears 3 s so a parent knows to let go (or keep holding).
        scale_set(now - S.press_ms > BTN_HOLD_MS * 2 / 3 ? pairing : press, 100);
    } else if (now < S.pair_until_ms) {
        scale_set(pairing, 15 + bmm_breathe(now, 2000) * 85 / 255);
    } else if (now < S.flash_until_ms) {
        bool on = !S.flash_period_ms || (now / S.flash_period_ms) % 2 == 0;
        scale_set(S.flash_rgb, on ? 100 : 0);
    } else if (S.alert) {
        static const int period[4] = {0, 2000, 1200, 600};          // faster with the level
        scale_set(alert, 20 + bmm_breathe(now, period[S.alert]) * 80 / 255);
    } else if (!S.paired) {
        scale_set(unpaired, (now / 1500) % 2 ? 100 : 0);
    } else if (!watch_linked(now)) {
        scale_set(lost, 30 + bmm_breathe(now, 3000) * 70 / 255);
    } else if (S.acked && S.level) {
        scale_set(acked, 100);
    } else {
        scale_set(S.vbat_mv && S.vbat_mv < VBAT_LOW_MV ? low : armed, 100);
    }

    // Green status LED: a VU meter of what it hears (helps place it next to the monitor), else an alive blip.
    static const int vu[4] = STATUS_VU;
    int duty = vu[S.instant];
    if (!duty && (now % 4000) < 60) duty = STATUS_BLIP;
    bmm_pwm_set(PWM_STATUS, duty);
}

// ---------------------------------------------------------------- main
void app_main(void) {
    ESP_LOGI(TAG, "%s, firmware " __DATE__ " " __TIME__, BOARD_NAME);

    gpio_config_t in = {.pin_bit_mask = (1ULL << PIN_BTN) | (1ULL << PIN_CHG_STAT), .mode = GPIO_MODE_INPUT,
                        .pull_up_en = GPIO_PULLUP_ENABLE};      // neither has a pull-up on the board
    ESP_ERROR_CHECK(gpio_config(&in));
    bmm_pwm_init(PWM_STATUS, PIN_LED_IO);
    bmm_rgb_init(PIN_BAR_IO);
    bmm_battery_init();

    s_tx_q = xQueueCreate(4, sizeof(tx_item_t));
    s_rx_q = xQueueCreate(8, sizeof(rx_item_t));
    QueueHandle_t audio_q = xQueueCreate(4, sizeof(audio_window_t));
    bmm_link_init(on_rx, false);        // the sensor is mains-powered most nights: radio always listening
    bmm_link_add_peer(BMM_BROADCAST);
    S.paired = bmm_peer_load(S.peer);
    if (S.paired) {
        bmm_link_add_peer(S.peer);
        ESP_LOGI(TAG, "paired watch " BMM_MAC_FMT, BMM_MAC_ARGS(S.peer));
    } else {
        ESP_LOGW(TAG, "no watch paired: put the watch on its charger and hold the snooze bar 3 s");
    }
    xTaskCreate(tx_task, "tx", 3072, NULL, 5, NULL);

    detector_cfg_t dc = {.rel_db = LEVEL_REL_DB, .abs_min_db = LEVEL_ABS_MIN_DB, .floor_min_db = FLOOR_MIN_DB,
                         .floor_max_db = FLOOR_MAX_DB, .floor_rise_db = FLOOR_RISE_DB, .floor_fall = FLOOR_FALL,
                         .attack_windows = ATTACK_WINDOWS, .release_ms = RELEASE_MS,
                         .steady_spread_db = STEADY_SPREAD_DB, .steady_learn_ms = STEADY_LEARN_MS};
    detector_init(&S.det, &dc);
    audio_start(audio_q);

    int64_t next_vbat = 0, next_log = 0;
    for (;;) {
        vTaskDelay(pdMS_TO_TICKS(TICK_MS));
        int64_t now = bmm_now_ms();

        audio_window_t w;
        while (xQueueReceive(audio_q, &w, 0) == pdTRUE) {
            S.spl_db = w.spl_db;
            S.instant = detector_instant(&S.det, w.spl_db);
            int learned = S.det.learned;
            S.level = detector_update(&S.det, w.spl_db, w.t_ms);
            if (S.det.learned != learned)
                ESP_LOGI(TAG, "steady sound for %d s: %.0f dB is the new background", STEADY_LEARN_MS / 1000, S.det.floor_db);
            S.last_window_ms = w.t_ms;
            if (w.peak > 8000000) ESP_LOGW(TAG, "mic clipping (%.0f dB)", w.spl_db);
        }
        if (S.last_window_ms && now - S.last_window_ms > 2000) {
            ESP_LOGE(TAG, "no audio for 2 s");      // TODO: show a fault colour once the light scheme is agreed
            S.last_window_ms = now;
        }
        update_alert(now);
        poll_button(now);

        rx_item_t it;
        while (xQueueReceive(s_rx_q, &it, 0) == pdTRUE) handle_rx(&it, now);

        if (now >= next_vbat) {
            S.vbat_mv = bmm_battery_mv();
            S.charging = gpio_get_level(PIN_CHG_STAT) == 0;
            next_vbat = now + VBAT_READ_MS;
        }
        if (now < S.pair_until_ms && now >= S.next_offer_ms) {
            bmm_bare_t offer;
            queue_tx(BMM_BROADCAST, &offer, sizeof offer, BMM_MSG_PAIR_OFFER);
            S.next_offer_ms = now + BMM_PAIR_OFFER_MS;
        }
        // STATUS on any change at once, otherwise as a heartbeat (also while offering pairing).
        bool changed = S.alert != S.last_sent_alert || S.level != S.last_sent_level ||
                       status_flags(now) != S.last_sent_flags;
        if (changed || now - S.last_status_tx_ms >= BMM_HEARTBEAT_MS) send_status(now);
        update_lights(now);

        if (now >= next_log) {
            ESP_LOGI(TAG, "%.0f dB (floor %.0f) inst %d level %d alert %d%s | watch %s %d mV | vbat %d mV%s",
                     S.spl_db, S.det.floor_db, S.instant, S.level, S.alert, S.acked ? " acked" : "",
                     watch_linked(now) ? "ok" : "--", S.watch.vbat_mv, S.vbat_mv, S.charging ? " charging" : "");
            next_log = now + 5000;
        }
    }
}
