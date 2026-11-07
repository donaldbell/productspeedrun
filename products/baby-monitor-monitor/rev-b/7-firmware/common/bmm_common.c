// Baby Monitor Monitor: shared helpers (see bmm_common.h).
#include "bmm_common.h"

#include <string.h>
#include "bmm_protocol.h"
#include "driver/ledc.h"
#include "driver/rmt_tx.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "pins.h"

static const char *TAG = "bmm";
const uint8_t BMM_BROADCAST[6] = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff};

// ---------------------------------------------------------------- radio
static bmm_rx_fn s_on_rx;

static void espnow_rx(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
    if (s_on_rx) s_on_rx(info->src_addr, data, len, info->rx_ctrl ? info->rx_ctrl->rssi : 0);
}

void bmm_link_init(bmm_rx_fn on_rx, bool power_save) {
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_ERROR_CHECK(esp_wifi_set_channel(BMM_WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE));
    ESP_ERROR_CHECK(esp_now_init());
    s_on_rx = on_rx;
    ESP_ERROR_CHECK(esp_now_register_recv_cb(espnow_rx));
    if (power_save) {
        // Connectionless power save (needs CONFIG_ESP_WIFI_STA_DISCONNECTED_PM_ENABLE): the radio listens
        // BMM_WAKE_WINDOW_MS in every BMM_WAKE_INTERVAL_MS; the sensor's repeats are sized to hit that.
        ESP_ERROR_CHECK(esp_now_set_wake_window(BMM_WAKE_WINDOW_MS));
        ESP_ERROR_CHECK(esp_wifi_connectionless_module_set_wake_interval(BMM_WAKE_INTERVAL_MS));
    }
    uint8_t mac[6];
    esp_wifi_get_mac(WIFI_IF_STA, mac);
    ESP_LOGI(TAG, "ESP-NOW up on channel %d, me " BMM_MAC_FMT "%s", BMM_WIFI_CHANNEL, BMM_MAC_ARGS(mac),
             power_save ? ", radio duty-cycled" : "");
}

bool bmm_link_add_peer(const uint8_t mac[6]) {
    if (esp_now_is_peer_exist(mac)) return true;
    esp_now_peer_info_t peer = {.channel = BMM_WIFI_CHANNEL, .ifidx = WIFI_IF_STA, .encrypt = false};
    memcpy(peer.peer_addr, mac, 6);
    esp_err_t err = esp_now_add_peer(&peer);
    if (err != ESP_OK) ESP_LOGW(TAG, "add peer " BMM_MAC_FMT ": %s", BMM_MAC_ARGS(mac), esp_err_to_name(err));
    return err == ESP_OK;
}

bool bmm_link_send(const uint8_t mac[6], const void *data, int len) {
    if (!bmm_link_add_peer(mac)) return false;
    esp_err_t err = esp_now_send(mac, data, len);
    if (err != ESP_OK) ESP_LOGD(TAG, "send: %s", esp_err_to_name(err));
    return err == ESP_OK;
}

// ---------------------------------------------------------------- pairing
bool bmm_peer_load(uint8_t mac[6]) {
    nvs_handle_t h;
    if (nvs_open("bmm", NVS_READONLY, &h) != ESP_OK) return false;
    size_t len = 6;
    bool ok = nvs_get_blob(h, "peer", mac, &len) == ESP_OK && len == 6;
    nvs_close(h);
    return ok;
}

void bmm_peer_save(const uint8_t mac[6]) {
    nvs_handle_t h;
    if (nvs_open("bmm", NVS_READWRITE, &h) != ESP_OK) return;
    nvs_set_blob(h, "peer", mac, 6);
    nvs_commit(h);
    nvs_close(h);
    ESP_LOGI(TAG, "paired with " BMM_MAC_FMT, BMM_MAC_ARGS(mac));
}

// ---------------------------------------------------------------- battery
#ifndef BMM_FAKE_VBAT_MV
static adc_oneshot_unit_handle_t s_adc;
static adc_channel_t s_adc_ch;
static adc_cali_handle_t s_cali;
#endif

void bmm_battery_init(void) {
#ifndef BMM_FAKE_VBAT_MV
    adc_unit_t unit;
    ESP_ERROR_CHECK(adc_oneshot_io_to_channel(PIN_VBAT_SENSE, &unit, &s_adc_ch));
    adc_oneshot_unit_init_cfg_t ucfg = {.unit_id = unit};
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&ucfg, &s_adc));
    adc_oneshot_chan_cfg_t ccfg = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_DEFAULT};
    ESP_ERROR_CHECK(adc_oneshot_config_channel(s_adc, s_adc_ch, &ccfg));
    adc_cali_curve_fitting_config_t cal = {.unit_id = unit, .chan = s_adc_ch, .atten = ADC_ATTEN_DB_12,
                                           .bitwidth = ADC_BITWIDTH_DEFAULT};
    if (adc_cali_create_scheme_curve_fitting(&cal, &s_cali) != ESP_OK) {
        s_cali = NULL;
        ESP_LOGW(TAG, "no ADC calibration in eFuse: battery readings are raw estimates");
    }
#endif
}

int bmm_battery_mv(void) {
#ifdef BMM_FAKE_VBAT_MV
    return BMM_FAKE_VBAT_MV;
#else
    // The divider is 1M / 1M with 100 nF on the pin: plenty of charge for a burst of 16 conversions.
    int sum = 0, n = 0;
    for (int i = 0; i < 16; i++) {
        int raw, mv;
        if (adc_oneshot_read(s_adc, s_adc_ch, &raw) != ESP_OK) continue;
        if (!s_cali || adc_cali_raw_to_voltage(s_cali, raw, &mv) != ESP_OK) mv = raw * 3100 / 4095;
        sum += mv;
        n++;
    }
    return n ? (int)(sum / n * VBAT_SENSE_RATIO) : 0;
#endif
}

// ---------------------------------------------------------------- WS2812B
static rmt_channel_handle_t s_rmt;
static rmt_encoder_handle_t s_rmt_enc;
static uint8_t s_rgb_last[3] = {1, 1, 1};   // forces the first write

void bmm_rgb_init(int gpio) {
    rmt_tx_channel_config_t ch = {.gpio_num = gpio, .clk_src = RMT_CLK_SRC_DEFAULT, .resolution_hz = 10000000,
                                  .mem_block_symbols = 48, .trans_queue_depth = 2};
    ESP_ERROR_CHECK(rmt_new_tx_channel(&ch, &s_rmt));
    // 10 MHz ticks: 0 = 0.3 us high + 0.9 us low, 1 = 0.9 us high + 0.3 us low (WS2812B datasheet)
    rmt_bytes_encoder_config_t enc = {
        .bit0 = {.level0 = 1, .duration0 = 3, .level1 = 0, .duration1 = 9},
        .bit1 = {.level0 = 1, .duration0 = 9, .level1 = 0, .duration1 = 3},
        .flags.msb_first = 1,
    };
    ESP_ERROR_CHECK(rmt_new_bytes_encoder(&enc, &s_rmt_enc));
    ESP_ERROR_CHECK(rmt_enable(s_rmt));
    bmm_rgb_set(0, 0, 0);
}

void bmm_rgb_set(uint8_t r, uint8_t g, uint8_t b) {
    if (!s_rmt || (s_rgb_last[0] == r && s_rgb_last[1] == g && s_rgb_last[2] == b)) return;
    static uint8_t grb[3];      // must outlive the (async) transmit
    rmt_tx_wait_all_done(s_rmt, 10);      // the line idles low between frames: that's the >280 us reset
    grb[0] = g, grb[1] = r, grb[2] = b;
    rmt_transmit_config_t tx = {.loop_count = 0};
    if (rmt_transmit(s_rmt, s_rmt_enc, grb, sizeof grb, &tx) == ESP_OK) {
        s_rgb_last[0] = r, s_rgb_last[1] = g, s_rgb_last[2] = b;
    }
}

// ---------------------------------------------------------------- PWM
void bmm_pwm_init(int channel, int gpio) {
    static bool timer_ready;
    if (!timer_ready) {
        ledc_timer_config_t t = {.speed_mode = LEDC_LOW_SPEED_MODE, .duty_resolution = LEDC_TIMER_10_BIT,
                                 .timer_num = LEDC_TIMER_0, .freq_hz = 20000, .clk_cfg = LEDC_AUTO_CLK};
        ESP_ERROR_CHECK(ledc_timer_config(&t));
        timer_ready = true;
    }
    ledc_channel_config_t c = {.gpio_num = gpio, .speed_mode = LEDC_LOW_SPEED_MODE, .channel = channel,
                               .timer_sel = LEDC_TIMER_0, .duty = 0, .hpoint = 0};
    ESP_ERROR_CHECK(ledc_channel_config(&c));
}

void bmm_pwm_set(int channel, uint32_t duty) {
    if (duty > BMM_PWM_MAX) duty = BMM_PWM_MAX;
    ledc_set_duty(LEDC_LOW_SPEED_MODE, channel, duty);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, channel);
}

uint8_t bmm_breathe(int64_t now_ms, int period_ms) {
    int phase = (int)(now_ms % period_ms) * 510 / period_ms;    // 0..509
    return (uint8_t)(phase < 255 ? phase : 509 - phase);
}
