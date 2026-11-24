"""AC target temperature: read the setpoint whichever byte order the unit used.

gehomesdk decodes ERD 0x7003 (AC_TARGET_TEMPERATURE) with int(value, 16), i.e. big endian
for any length, and writes it back as two big-endian bytes ("0042" = 66). Some AC units also report the same setpoint as the two bytes "4200", which the SDK
reads as 16896 (= 66 * 256), flipping between 66 and 16896 across updates.

A setpoint is a whole number of degrees Fahrenheit that fits in one byte. When the SDK hands
over something larger, swap its two bytes; if that gives a plausible temperature it is the
real setpoint, otherwise the value is returned exactly as read.
"""
from typing import Any


# A swapped value only counts as a setpoint inside this window of degrees Fahrenheit.
_PLAUSIBLE_MIN_F = 32
_PLAUSIBLE_MAX_F = 140


def normalize_ac_target_temperature(value: Any) -> Any:
    """Return the setpoint in degrees F; the value as read when it is not a swapped 16-bit setpoint."""
    if value is None or isinstance(value, bool):
        return value
    try:
        number = int(value)
    except (TypeError, ValueError):
        return value
    if number <= 0xFF or number > 0xFFFF:
        return value
    swapped = ((number & 0xFF) << 8) | (number >> 8)
    if _PLAUSIBLE_MIN_F <= swapped <= _PLAUSIBLE_MAX_F:
        return swapped
    return value
