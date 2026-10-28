"""Custom symbols already used on a Product Speedrun board, ready to reuse.

Each function adds the symbol to the episode's own library and returns its lib_id:

    from parts import tps61023
    BOOST = tps61023()
    part("U1", BOOST, "TPS61023DRLR", "Package_TO_SOT_SMD:SOT-563", "C919459", "TPS61023DRLR", at(44, 22), {...})

Status says how far each one is trusted. Add new ones here once a board has used them,
so the next episode doesn't redraw them.
"""

from schkit import box_symbol


def tps61023():
    """Status: pinout proven on the bollard v2 board; used on 001 Backpack Defender (2 x AAA -> 3.3 V).
    Feedback: VOUT = 0.595 V x (1 + Rtop / Rbottom); 1M / 220k gives 3.30 V. L = 1 uH."""
    return box_symbol(
        "TPS61023", "U", "TPS61023DRLR", "Package_TO_SOT_SMD:SOT-563",
        "https://www.ti.com/lit/ds/symlink/tps61023.pdf",
        "3.7 A switch, 0.5-5.5 V in, synchronous boost; VREF 0.595 V (pinout as bollard v2, proven)",
        (-7.62, 6.35, 7.62, -6.35),
        [("power_in", -10.16, 2.54, 0, "VIN", "3"), ("input", -10.16, -2.54, 0, "EN", "2"),
         ("passive", 10.16, 3.81, 180, "SW", "5"), ("power_out", 10.16, 0, 180, "VOUT", "6"),
         ("input", 10.16, -3.81, 180, "FB", "1"), ("power_in", 0, -8.89, 90, "GND", "4")])


def max98357a():
    """Status: drawn for 001 Backpack Defender, DRC clean, not yet built: check the TQFN pinout
    against the datasheet before ordering. GAIN_SLOT open = 9 dB; SD_MODE high = left channel."""
    return box_symbol(
        "MAX98357A", "U", "MAX98357AETE+T", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm_ThermalVias",
        "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf",
        "I2S input class-D mono amplifier, 2.5-5.5 V, filterless; GAIN open = 9 dB; SD_MODE high = left channel",
        (-7.62, 10.16, 7.62, -10.16),
        [("input", -10.16, 7.62, 0, "BCLK", "16"), ("input", -10.16, 5.08, 0, "LRCLK", "14"),
         ("input", -10.16, 2.54, 0, "DIN", "1"), ("input", -10.16, -2.54, 0, "~{SD_MODE}", "4"),
         ("input", -10.16, -5.08, 0, "GAIN_SLOT", "2"),
         ("power_in", 10.16, 7.62, 180, "VDD", "7"), ("power_in", 10.16, 5.08, 180, "VDD", "8"),
         ("output", 10.16, 0, 180, "OUTP", "9"), ("output", 10.16, -2.54, 180, "OUTN", "10"),
         ("no_connect", 10.16, -5.08, 180, "NC", "5"), ("no_connect", 10.16, -7.62, 180, "NC", "6"),
         ("no_connect", 7.62, -12.7, 90, "NC", "12"), ("no_connect", 5.08, -12.7, 90, "NC", "13"),
         ("power_in", -5.08, -12.7, 90, "GND", "3"), ("power_in", -2.54, -12.7, 90, "GND", "11"),
         ("power_in", 0, -12.7, 90, "GND", "15"), ("power_in", 2.54, -12.7, 90, "EP", "17")])


def am312():
    """Status: drawn for 001 Backpack Defender. Pin order VCC/OUT/GND at 2.54 mm varies by vendor:
    check the supplier's drawing. Feed it through 100R + 10uF: PIRs false-trigger on supply ripple."""
    return box_symbol(
        "AM312", "U", "AM312", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "https://www.lcsc.com/search?q=AM312",
        "Mini PIR motion sensor module, 2.7-12 V, ~15 uA, digital output (high ~2 s on motion). "
        "Pin order VCC/OUT/GND and 2.54 mm pitch: verify against the supplier's drawing",
        (-5.08, 3.81, 5.08, -3.81),
        [("power_in", -7.62, 2.54, 0, "VCC", "1"), ("output", 7.62, 0, 180, "OUT", "2"),
         ("power_in", -7.62, -2.54, 0, "GND", "3")])
