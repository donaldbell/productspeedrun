// Baby Monitor Monitor: helpers shared by the sensor and watch firmwares (both are ESP32-C6-MINI-1 boards).
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "esp_now.h"
#include "esp_timer.h"

static inline int64_t bmm_now_ms(void) { return esp_timer_get_time() / 1000; }

// --- radio (ESP-NOW on BMM_WIFI_CHANNEL)
typedef void (*bmm_rx_fn)(const uint8_t mac[6], const uint8_t *data, int len, int8_t rssi);
// Starts NVS, Wi-Fi (station, not connected) and ESP-NOW. power_save: duty-cycle the receiver (watch).
void bmm_link_init(bmm_rx_fn on_rx, bool power_save);
bool bmm_link_send(const uint8_t mac[6], const void *data, int len);   // one copy, no repeats
bool bmm_link_add_peer(const uint8_t mac[6]);
extern const uint8_t BMM_BROADCAST[6];

// --- pairing, kept in NVS (namespace "bmm", key "peer")
bool bmm_peer_load(uint8_t mac[6]);
void bmm_peer_save(const uint8_t mac[6]);
#define BMM_MAC_FMT "%02x:%02x:%02x:%02x:%02x:%02x"
#define BMM_MAC_ARGS(m) (m)[0], (m)[1], (m)[2], (m)[3], (m)[4], (m)[5]

// --- battery: VBAT through the board's divider (VBAT_SENSE_RATIO from pins.h) on PIN_VBAT_SENSE (ADC1)
void bmm_battery_init(void);
int bmm_battery_mv(void);            // averaged, calibrated; BMM_FAKE_VBAT_MV overrides it on a dev board

// --- one WS2812B (GRB) on an RMT channel
void bmm_rgb_init(int gpio);
void bmm_rgb_set(uint8_t r, uint8_t g, uint8_t b);   // skips the write if nothing changed

// --- LEDC PWM (one shared 20 kHz, 10-bit timer: inaudible for the ERM, flicker-free for LEDs)
#define BMM_PWM_MAX 1023
void bmm_pwm_init(int channel, int gpio);
void bmm_pwm_set(int channel, uint32_t duty);         // 0 .. BMM_PWM_MAX

// --- small maths for light effects: 0..255 triangle "breathing" with the given period
uint8_t bmm_breathe(int64_t now_ms, int period_ms);
