# Board size check

From the schematic's footprints (written by `tools/kicad/size_board.py`; rerun with `tools/kicad/build.sh episodes/<slug> schematic`).

| | mm² |
|---|---|
| Parts area (56 parts) | 815 |
| Big parts (U1), with a 2 mm ring | 627 |
| **Smallest comfortable board** | **1559** (e.g. 39 x 39, or 50 x 31) |

Parts on both faces don't make it smaller: episode 002 needed this area with parts on both faces.
Add about 4 mm to each side for mounting holes and posts if they sit outside the parts area. No side can be shorter than the biggest part, 22.8 mm, plus 8 mm.
Corners cut by a large radius, cut-outs and keep-outs (antennas, under tall parts) need extra area on top.

## Biggest parts

| Ref | Footprint | W × H mm | Note |
|---|---|---|---|
| U1 | Seeed_XIAO_ESP32C6_SMD | 19.4 × 22.8 |  |
| SW1 | SW_SPST_PTS810 | 5.8 × 3.8 |  |
| J2 | SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm | 6.2 × 2.7 |  |
| J1 | SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm | 6.2 × 2.7 |  |
| Q2 | SOT-23 | 3.9 × 3.4 |  |
| Q1 | SOT-23 | 3.9 × 3.4 |  |
| U2 | Avago_APDS-9960 | 4.5 × 2.9 |  |
| LED9 | LED_WS2812B-2020_PLCC4_2.0x2.0mm | 3.1 × 2.6 |  |
