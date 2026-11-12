# Board size check

From the schematic's footprints (written by `tools/kicad/size_board.py`; rerun with `tools/kicad/build.sh episodes/<slug> schematic`).

| | mm² |
|---|---|
| Parts area (51 parts) | 1184 |
| Big parts (U2), with a 2 mm ring | 578 |
| **Smallest comfortable board** | **2533** (e.g. 50 x 50, or 64 x 40) |

Parts on both faces don't make it smaller: episode 002 needed this area with parts on both faces.
Add about 4 mm to each side for mounting holes and posts if they sit outside the parts area. No side can be shorter than the biggest part, 20.6 mm, plus 8 mm.
Corners cut by a large radius, cut-outs and keep-outs (antennas, under tall parts) need extra area on top.

## Biggest parts

| Ref | Footprint | W × H mm | Note |
|---|---|---|---|
| U2 | ESP32-C3-WROOM-02 | 19.5 × 20.6 | body and pads only: the courtyard includes a clearance zone (TRIM_COURTYARD on a tight board) |
| SW1 | SW_PUSH-12mm | 15.6 × 14.6 (through-hole) |  |
| SW2 | SW_Slide_SPDT_Angled_CK_OS102011MA1Q | 11.4 × 9.4 (through-hole) |  |
| L1 | L_Changjiang_FXL0624 | 8.9 × 7.2 |  |
| J4 | SolderWire-0.25sqmm_1x03_P4.2mm_D0.65mm_OD1.7mm | 11.7 × 2.9 |  |
| J2 | Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical | 7.1 × 4.1 |  |
| J3 | SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm | 7.5 × 2.9 |  |
| J1 | SolderWire-0.25sqmm_1x02_P4.2mm_D0.65mm_OD1.7mm | 7.5 × 2.9 |  |
