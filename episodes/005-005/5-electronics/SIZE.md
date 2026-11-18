# Board size check

From the schematic's footprints (written by `tools/kicad/size_board.py`; rerun with `tools/kicad/build.sh episodes/<slug> schematic`).

| | mm² |
|---|---|
| Parts area (31 parts) | 935 |
| Big parts (U1), with a 2 mm ring | 627 |
| **Smallest comfortable board** | **1859** (e.g. 43 x 43, or 55 x 34) |

Parts on both faces don't make it smaller: episode 002 needed this area with parts on both faces.
Add about 4 mm to each side for mounting holes and posts if they sit outside the parts area. No side can be shorter than the biggest part, 22.8 mm, plus 8 mm.
Corners cut by a large radius, cut-outs and keep-outs (antennas, under tall parts) need extra area on top.

## Biggest parts

| Ref | Footprint | W × H mm | Note |
|---|---|---|---|
| U1 | Seeed_XIAO_nRF52840_SMD | 19.4 × 22.8 |  |
| J4 | JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal | 11.2 × 10.2 |  |
| J3 | JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal | 11.2 × 10.2 |  |
| SW1 | SW_SPST_PTS810 | 5.8 × 3.8 |  |
| J2 | SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm | 6.2 × 2.7 |  |
| J1 | SolderWire-0.1sqmm_1x02_P3.6mm_D0.4mm_OD1mm | 6.2 × 2.7 |  |
| U4 | SOT-23-5 | 4.2 × 3.4 |  |
| U3 | SOT-23-5 | 4.2 × 3.4 |  |
