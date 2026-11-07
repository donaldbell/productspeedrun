// Baby Monitor Monitor Rev B: watch (receiver) firmware (ESP32-C6-MINI-1). See ../../NOTES.md.
//
// Follows the sensor: STATUS.alert 0-3 becomes a haptic pattern on the ERM (haptic.c), escalating one level
// every BMM_ESCALATE_MS until a parent taps the sensor's snooze bar. The face glows in the level's colour.
// If the sensor goes quiet for BMM_LINK_LOST_MS, the watch buzzes a "lost" pattern (a sleeping parent's worst
// case is a monitor that has silently stopped).
//
// Power: the radio listens BMM_WAKE_WINDOW_MS in every BMM_WAKE_INTERVAL_MS, and the CPU light-sleeps between
// (esp_pm + tickless idle), except while the motor or the glow is running.
#include <string.h>
#include "bmm_common.h"
#include "bmm_protocol.h"
#include "config.h"
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_pm.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "haptic.h"
#include "pins.h"

static const char *TAG = "watch";

#define PWM_MOTOR 0
#define PWM_LINK 1

typedef struct {
    uint8_t mac[6];
    int8_t rssi;
    uint8_t len;
    uint8_t data[32];
} rx_item_t;

static QueueHandle_t s_rx_q;

static void on_rx(const uint8_t mac[6], const uint8_t *data, int len, int8_t rssi) {   // Wi-Fi task
    rx_item_t it = {.rssi = rssi, .len = (uint8_t)(len > 32 ? 32 : len)};
    memcpy(it.mac, mac, 6);
    memcpy(it.data, data, it.len);
    xQueueSend(s_rx_q, &it, 0);
}

static struct {
    bool paired;
    uint8_t peer[6];
    int last_seq;
    uint16_t my_seq;
    bmm_status_t st;
    int64_t boot_ms, status_ms;
    // haptics
    haptic_t hap;
    int playing_level;          // alert level whose pattern is looping (0 = none)
    int motor_pct;
    // link lost
    bool lost, lost_reported;
    int64_t next_lost_buzz_ms;
    int lost_buzzes;
    // power
    int vbat_mv;
    bool charging;
    int64_t next_vbat_ms, next_low_ms;
    // lights
    int64_t glow_until_ms, link_blip_until_ms;
    uint8_t glow_rgb[3];
    int8_t last_rssi;
} W;

static bool linked(int64_t now) { return now - W.status_ms < BMM_LINK_LOST_MS; }

static void reply(const uint8_t mac[6], uint16_t ack_seq, uint8_t type, int8_t rssi) {
    uint8_t buf[sizeof(bmm_watch_t)];
    int len;
    if (type == BMM_MSG_WATCH) {
        bmm_watch_t *p = (bmm_watch_t *)buf;
        p->ack_seq = ack_seq, p->vbat_mv = (uint16_t)W.vbat_mv, p->rssi = rssi;
        p->flags = (W.playing_level ? BMM_WF_BUZZING : 0) | (W.charging ? BMM_WF_CHARGING : 0) |
                   (W.vbat_mv && W.vbat_mv < VBAT_LOW_MV ? BMM_WF_LOW_BATT : 0) | (W.lost_reported ? BMM_WF_LINK_LOST : 0);
        W.lost_reported = false;
        len = sizeof(bmm_watch_t);
    } else {
        len = sizeof(bmm_bare_t);
    }
    bmm_hdr_t *h = (bmm_hdr_t *)buf;
    h->magic = BMM_MAGIC, h->version = BMM_PROTO_VERSION, h->type = type, h->seq = ++W.my_seq;
    bmm_link_send(mac, buf, len);       // the sensor always listens: one copy is enough
}

static void glow_flash(const uint8_t rgb[3], int ms, int64_t now) {
    memcpy(W.glow_rgb, rgb, 3);
    W.glow_until_ms = now + ms;
}

static void handle_rx(const rx_item_t *it, int64_t now) {
    if (!bmm_valid(it->data, it->len, sizeof(bmm_hdr_t))) return;
    const bmm_hdr_t *h = (const bmm_hdr_t *)it->data;
    bool from_peer = W.paired && !memcmp(it->mac, W.peer, 6);

    if (h->type == BMM_MSG_PAIR_OFFER) {
        if (from_peer) {
            if (h->seq != W.last_seq) reply(it->mac, h->seq, BMM_MSG_PAIR_ACCEPT, it->rssi);   // confirm, quietly
            W.last_seq = h->seq;
            return;
        }
        bool may_pair = !W.paired || W.charging || now - W.boot_ms < PAIR_AFTER_BOOT_MS;
        if (!may_pair) return;
        memcpy(W.peer, it->mac, 6);
        W.paired = true;
        W.last_seq = h->seq;
        W.status_ms = now;
        bmm_peer_save(W.peer);
        bmm_link_add_peer(W.peer);
        reply(W.peer, h->seq, BMM_MSG_PAIR_ACCEPT, it->rssi);
        static const uint8_t blue[3] = GLOW_PAIRED;
        glow_flash(blue, 1500, now);
        haptic_play(&W.hap, &HAPTIC_PAIRED, now);
        return;
    }
    if (!from_peer || h->seq == W.last_seq) return;     // someone else's sensor, or a repeat
    W.last_seq = h->seq;
    W.last_rssi = it->rssi;

    if (h->type == BMM_MSG_STATUS && it->len >= (int)sizeof(bmm_status_t)) {
        bmm_status_t prev = W.st;
        memcpy(&W.st, it->data, sizeof W.st);
        if (W.lost) {
            ESP_LOGI(TAG, "sensor back (RSSI %d dBm)", it->rssi);
            W.lost = false, W.lost_buzzes = 0, W.lost_reported = true;
        }
        W.status_ms = now;
        W.link_blip_until_ms = now + LINK_BLIP_MS;
        if (W.st.alert != prev.alert || W.st.level != prev.level)
            ESP_LOGI(TAG, "sensor: %s (%u dB, floor %u), alert %u%s", bmm_level_name(W.st.level), W.st.spl_db,
                     W.st.floor_db, W.st.alert, (W.st.flags & BMM_SF_ACKED) ? ", acked" : "");
        if ((W.st.flags & BMM_SF_ACKED) && !(prev.flags & BMM_SF_ACKED)) {
            static const uint8_t green[3] = GLOW_ACKED;
            glow_flash(green, 2000, now);       // "they pressed it": the alert stops below
        }
        reply(it->mac, h->seq, BMM_MSG_WATCH, it->rssi);
    } else if (h->type == BMM_MSG_TEST) {
        ESP_LOGI(TAG, "test pattern");
        W.status_ms = now;
        haptic_play(&W.hap, &HAPTIC_TEST, now);
        W.playing_level = 0;
        reply(it->mac, h->seq, BMM_MSG_WATCH, it->rssi);
    }
}

// Decide what the motor should be doing: alert pattern (with escalation), link-lost, low battery.
static void update_haptics(int64_t now) {
    int want = 0;
    if (W.paired && linked(now) && W.st.alert) {
        int64_t running = (int64_t)W.st.alert_ms + (now - W.status_ms);
        want = W.st.alert + (int)(running / BMM_ESCALATE_MS);
        if (want > BMM_LEVEL_MAX) want = BMM_LEVEL_MAX;
    }
    if (want != W.playing_level) {
        if (want) {
            ESP_LOGI(TAG, "buzz: %s%s", HAPTIC_LEVEL[want].name, want > W.st.alert ? " (escalated)" : "");
            haptic_play(&W.hap, &HAPTIC_LEVEL[want], now);
        } else if (W.playing_level) {
            haptic_stop(&W.hap);
        }
        W.playing_level = want;
    }

    // Link lost: a few buzzes, then glow only. Not while charging (it's on the clip, not on a wrist).
    if (W.paired && !linked(now)) {
        if (!W.lost) {
            W.lost = true;
            W.next_lost_buzz_ms = now + LOST_GRACE_MS;
            ESP_LOGW(TAG, "sensor lost (last heard %lld s ago)", (long long)((now - W.status_ms) / 1000));
        }
        if (now >= W.next_lost_buzz_ms && !haptic_active(&W.hap) && !W.charging && W.lost_buzzes < LOST_MAX_BUZZES) {
            haptic_play(&W.hap, &HAPTIC_LOST, now);
            W.lost_buzzes++;
            W.next_lost_buzz_ms = now + LOST_REPEAT_MS;
        }
    }

    if (W.vbat_mv && W.vbat_mv < VBAT_LOW_MV && !W.charging && now >= W.next_low_ms && !haptic_active(&W.hap)) {
        ESP_LOGW(TAG, "battery low: %d mV", W.vbat_mv);
        haptic_play(&W.hap, &HAPTIC_LOW_BATT, now);
        W.next_low_ms = now + LOW_BATT_REPEAT_MS;
    }

    W.motor_pct = haptic_tick(&W.hap, now);
    bmm_pwm_set(PWM_MOTOR, haptic_duty(W.motor_pct, W.vbat_mv ? W.vbat_mv : 3900, BMM_PWM_MAX));
}

static void update_lights(int64_t now) {
    static const uint8_t levels[4][3] = GLOW_LEVEL, lost[3] = GLOW_LOST, chg[3] = GLOW_CHARGING;
    const uint8_t *c = NULL;
    int pct = 0;
    if (now < W.glow_until_ms) {
        c = W.glow_rgb;
        pct = (int)((W.glow_until_ms - now) * 100 / 1500);     // fade out
        if (pct > 100) pct = 100;
    } else if (W.playing_level) {
        c = levels[W.playing_level];
        pct = GLOW_BASE_PCT + W.motor_pct * (100 - GLOW_BASE_PCT) / 100;   // pulses with the motor
    } else if (haptic_active(&W.hap)) {
        c = W.lost ? lost : levels[2];
        pct = W.motor_pct;
    } else if (W.lost && (now % 5000) < 60) {
        c = lost, pct = 40;
    } else if (W.charging) {
        c = chg, pct = 5 + bmm_breathe(now, 4000) * 25 / 255;
    }
    if (c) {
        int k = pct * GLOW_MAX;                 // pct x GLOW_MAX / 25500
        bmm_rgb_set(c[0] * k / 25500, c[1] * k / 25500, c[2] * k / 25500);
    } else {
        bmm_rgb_set(0, 0, 0);
    }
    bmm_pwm_set(PWM_LINK, now < W.link_blip_until_ms ? LINK_BLIP_DUTY : 0);
}

void app_main(void) {
    ESP_LOGI(TAG, "%s, firmware " __DATE__ " " __TIME__, BOARD_NAME);
    W.boot_ms = bmm_now_ms();
    W.last_seq = -1;

    gpio_config_t in = {.pin_bit_mask = 1ULL << PIN_CHG_STAT, .mode = GPIO_MODE_INPUT,
                        .pull_up_en = GPIO_PULLUP_ENABLE};      // MCP73831 STAT is open drain
    ESP_ERROR_CHECK(gpio_config(&in));
    bmm_pwm_init(PWM_MOTOR, PIN_MOT_PWM);
    bmm_pwm_init(PWM_LINK, PIN_LINK_IO);
    bmm_rgb_init(PIN_LED_IO);
    bmm_battery_init();

#if CONFIG_PM_ENABLE
    esp_pm_config_t pm = {.max_freq_mhz = 80, .min_freq_mhz = 40, .light_sleep_enable = true};
    ESP_ERROR_CHECK(esp_pm_configure(&pm));
    esp_pm_lock_handle_t awake;     // held while the motor / glow run: LEDC stops in light sleep
    ESP_ERROR_CHECK(esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0, "haptic", &awake));
    bool holding = false;
#endif

    s_rx_q = xQueueCreate(8, sizeof(rx_item_t));
    bmm_link_init(on_rx, true);
    W.paired = bmm_peer_load(W.peer);
    if (W.paired) {
        bmm_link_add_peer(W.peer);
        ESP_LOGI(TAG, "paired sensor " BMM_MAC_FMT, BMM_MAC_ARGS(W.peer));
    } else {
        ESP_LOGW(TAG, "no sensor paired: hold the sensor's snooze bar 3 s");
    }
    W.status_ms = bmm_now_ms();     // give the sensor a full BMM_LINK_LOST_MS after boot

    int64_t next_log = 0;
    for (;;) {
        bool busy = haptic_active(&W.hap) || bmm_now_ms() < W.glow_until_ms || W.charging;
        rx_item_t it;
        if (xQueueReceive(s_rx_q, &it, pdMS_TO_TICKS(busy ? 10 : 100)) == pdTRUE) {
            int64_t now = bmm_now_ms();
            do handle_rx(&it, now);
            while (xQueueReceive(s_rx_q, &it, 0) == pdTRUE);
        }
        int64_t now = bmm_now_ms();
        if (now >= W.next_vbat_ms && !W.motor_pct) {        // not under motor load (it sags the cell)
            W.vbat_mv = bmm_battery_mv();
            W.charging = gpio_get_level(PIN_CHG_STAT) == 0;
            W.next_vbat_ms = now + VBAT_READ_MS;
        }
        update_haptics(now);
        update_lights(now);
#if CONFIG_PM_ENABLE
        bool need = haptic_active(&W.hap) || now < W.glow_until_ms || now < W.link_blip_until_ms || W.charging;
        if (need != holding) {
            need ? esp_pm_lock_acquire(awake) : esp_pm_lock_release(awake);
            holding = need;
        }
#endif
        if (now >= next_log) {
            ESP_LOGI(TAG, "%s | alert %u playing %d | RSSI %d | vbat %d mV%s", linked(now) ? "linked" : "NO SENSOR",
                     W.st.alert, W.playing_level, W.last_rssi, W.vbat_mv, W.charging ? " charging" : "");
            next_log = now + 10000;
        }
    }
}
