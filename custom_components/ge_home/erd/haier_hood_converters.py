"""Converters for Haier hood custom ERD codes."""

import logging
from typing import Optional, Union

from gehomesdk.erd.converters.erd_value_converter import ErdValueConverter

from .haier_hood_codes import HaierHoodFanSpeed, HaierHoodLightLevel

_LOGGER = logging.getLogger(__name__)

NumberLike = Union[int, str, bytes, bytearray, HaierHoodFanSpeed, HaierHoodLightLevel]

def _to_int(v: NumberLike) -> Optional[int]:
    """Convert many possible SDK-provided value shapes to an int 0..255."""
    try:
        if isinstance(v, (HaierHoodFanSpeed, HaierHoodLightLevel)):
            return int(v)
        if isinstance(v, int):
            return v
        if isinstance(v, (bytes, bytearray)):
            if len(v) == 0:
                return 0
            return v[0]
        if isinstance(v, str):
            s = v.strip().lower()
            if s.startswith("0x"):
                return int(s, 16)
            # sdk often passes hex without 0x; allow both
            return int(s, 16)
    except Exception as e:
        _LOGGER.debug("Failed to coerce value %r to int: %s", v, e)
    return None


class HaierHoodFanSpeedConverter(ErdValueConverter[HaierHoodFanSpeed]):
    """SDK converter for ERD_HAIER_HOOD_FAN_SPEED."""

    def erd_decode(self, value: NumberLike) -> Optional[HaierHoodFanSpeed]:
        ival = _to_int(value)
        if ival is None:
            _LOGGER.warning("Failed to decode Haier hood fan speed from %r", value)
            return None
        try:
            return HaierHoodFanSpeed(ival)
        except ValueError:
            _LOGGER.warning("Unknown Haier hood fan speed byte: 0x%02X", ival)
            return None

    def erd_encode(self, value: HaierHoodFanSpeed) -> str:
        # SDK expects hex-string (it will turn that into bytes)
        return f"{int(value):02X}"


class HaierHoodLightLevelConverter(ErdValueConverter[HaierHoodLightLevel]):
    """SDK converter for ERD_HAIER_HOOD_LIGHT_LEVEL."""

    def erd_decode(self, value: NumberLike) -> Optional[HaierHoodLightLevel]:
        ival = _to_int(value)
        if ival is None:
            _LOGGER.warning("Failed to decode Haier hood light level from %r", value)
            return None
        try:
            return HaierHoodLightLevel(ival)
        except ValueError:
            _LOGGER.warning("Unknown Haier hood light level byte: 0x%02X", ival)
            return None

    def erd_encode(self, value: HaierHoodLightLevel) -> str:
        # SDK expects hex-string (it will turn that into bytes)
        return f"{int(value):02X}"
