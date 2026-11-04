# Fit check: bmm-sensor in the enclosure

Real board (KiCad STEP export, parts included) placed in `4-model/model.solidcraft` where `fit.json` puts it, with Stage 4's stand-ins removed (S PCB, S Mic, S Status LED, S Tact Switch, S USB-C, S Power Switch, S Switch Lever). Re-run with `python3 tools/fit/fitcheck.py episodes/003-003/5-electronics/sensor`.

**Result: FAIL**: 1 overlaps, 5 gaps under 0.3 mm, 0 pairs the checker couldn't measure.

Board placed at enclosure x -66.0..-14.0, y -12.0..12.0, z 13.0..14.5.

## Overlaps

- **Fusion_sp** into **Switch Slider**: 0.22 mm³ at board (25.3, 5.5), +0.9 mm from the top face; enclosure (-14.7, 5.5, 15.4)

## Close (under 0.3 mm)

- Sensor Upper to bmm-sensor_PCB: 0.02 mm (posts: the board rests on them, lifted 0.02 mm for the check)
- Switch Slider to bmm-sensor_PCB: 0.17 mm
- S Battery to C_0603_1608Metric: 0.18 mm
- Sensor Button to LinkGroup: 0.23 mm
- Sensor Light Pipe to LED_0603_1608Metric: 0.24 mm

![fit check](fitcheck.png)
