# Board size check

From the schematic's footprints (written by `tools/kicad/size_board.py`; rerun with `tools/kicad/build.sh episodes/<slug> schematic`).

| | mm² |
|---|---|
| Parts area (31 parts) | 449 |
| Big parts (none), with a 2 mm ring | 0 |
| **Smallest comfortable board** | **1122** (e.g. 33 x 33, or 42 x 26) |

Parts on both faces don't make it smaller: episode 002 needed this area with parts on both faces.
Add about 4 mm to each side for mounting holes and posts if they sit outside the parts area. No side can be shorter than the biggest part, 17.2 mm, plus 8 mm.
Corners cut by a large radius, cut-outs and keep-outs (antennas, under tall parts) need extra area on top.

## Biggest parts

| Ref | Footprint | W × H mm | Note |
|---|---|---|---|
| U3 | ESP32-C6-MINI-1 | 13.8 × 17.2 | body and pads only: the courtyard includes a clearance zone (TRIM_COURTYARD on a tight board) |
| J3 | SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm | 6.2 × 2.7 |  |
| J2 | SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm | 6.2 × 2.7 |  |
| U2 | SOT-23-5 | 4.2 × 3.4 |  |
| U1 | SOT-23-5 | 4.2 × 3.4 |  |
| Q1 | SOT-23 | 3.9 × 3.4 |  |
| P2 | TestPoint_Pad_D2.0mm | 3.1 × 3.1 |  |
| P1 | TestPoint_Pad_D2.0mm | 3.1 × 3.1 |  |
