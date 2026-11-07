# Baby Monitor Monitor Rev B: how the two devices work together

| Device | Board | Does | Power |
|---|---|---|---|
| **Sensor** (the bean) | `5-electronics/sensor/`, ESP32-C6-MINI-1 | Sits next to the baby monitor's parent unit and listens to its speaker (ICS-43434 I2S mic). It turns the sound into a level 0–3 and decides whether the watch should buzz. The snooze bar on top is "I'm awake" (tap) and "test / pair" (hold 3 s) | USB-C most nights; 2000 mAh 103450 for unplugged nights |
| **Watch** (the receiver) | `5-electronics/receiver/`, ESP32-C6-MINI-1 | Sealed, with no button and no USB. Fussing only glows (soft pink); crying and screaming buzz an ERM coin motor, harder for louder sound, and crying escalates to screaming while nobody presses "I'm awake". The face glows in the level's colour. It buzzes "link lost" if the sensor goes silent | 150 mAh 402025, charged daily on a magnetic pogo clip |

**Same family on purpose:** both are ESP32-C6-MINI-1-N4 with the same charger (MCP73831), LDO (AP2112K-3.3) and battery-sense divider (1M / 1M on IO0). One toolchain (ESP-IDF 5.5 in PlatformIO) and one radio stack cover both. Firmware is in `7-firmware/sensor/` and `7-firmware/receiver/`, sharing `7-firmware/common/`.

## Link: ESP-NOW

ESP-NOW on 2.4 GHz channel 1. It needs no router, no app and no cloud. The protocol is `7-firmware/common/bmm_protocol.h`:

- **Sensor → watch, STATUS:** level, alert (0 = nothing, 1 = glow, 2–3 = buzz), flags (acked, pairing, low battery, charging), dB SPL and floor, battery, and how long the alert has run. It's sent on any change and as a heartbeat every 2 s.
- **Watch → sensor, WATCH:** one reply per new STATUS, with battery, buzzing / charging / low-battery flags and RSSI. The sensor shows "watch not answering" (red bar) after 10 s without one.
- **TEST** (hold 3 s): the watch plays each level once.
- **The sensor decides everything** (level, alert, ack). The watch only follows, so the two can't disagree about whether to buzz.
- **The watch's radio is duty-cycled** to save its cell: it listens 50 ms in every 200 ms. So the sensor sends every packet 5 times, 40 ms apart, and the watch drops repeats by sequence number. Worst-case latency is ~200 ms.
- **Link lost:** the watch hears nothing for 10 s, waits a 20 s grace, then gives a long-short-long buzz, every 5 min, 3 times at most (not while charging). For a sleeping parent, a monitor that has silently stopped is the failure that matters most.

## Pairing

The watch has no button. It accepts a pairing offer when it has no sensor yet, while it's charging, or in the first 2 min after it starts.

1. Put the watch on its clip.
2. Hold the sensor's snooze bar 3 s. The bar breathes blue and the sensor broadcasts offers for 30 s.
3. The watch answers, stores the sensor's MAC in NVS and gives three quick ticks. The sensor stores the watch's MAC and blinks green.

Offers from other sensors are ignored once a watch is paired and off its clip. ESP-NOW packets aren't encrypted yet; a per-pair key set at pairing is the next step.

## Power budget (first-pass estimates; see `5-electronics/NOTES.md` and `7-firmware/NOTES.md`)

| | Sensor | Watch |
|---|---|---|
| Average | ~25–30 mA (I2S continuous, radio always listening, 80 MHz) | ~11 mA (radio 25 % duty, light sleep between) |
| Peaks | TX bursts ~250 mA for under 1 ms | motor ~80 mA + glow ~15 mA during an alert |
| Battery life | ~3 nights unplugged; normally on USB | **~13 h on 150 mAh**, not measured yet: the tightest number in the project |
| Charging | 256 mA from USB-C | 100 mA from the pogo clip |
