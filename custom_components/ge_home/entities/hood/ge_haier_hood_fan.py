import logging
from typing import List, Any, Optional, Union

from gehomesdk import ErdCodeType
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter
from ...erd.haier_hood_codes import (
    HaierHoodFanSpeed,
    ERD_HAIER_HOOD_FAN_SPEED,
)
from ...erd.haier_hood_converters import HaierHoodFanSpeedConverter

_LOGGER = logging.getLogger(__name__)

_converter = HaierHoodFanSpeedConverter()

class _FanOptions(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in HaierHoodFanSpeed]

    def from_option_string(self, value: str) -> Any:
        try:
            return _converter.erd_encode(HaierHoodFanSpeed[value.upper()])
        except Exception:
            _LOGGER.warning("Haier Hood: invalid fan speed %s, using OFF", value)
            return _converter.erd_encode(HaierHoodFanSpeed.OFF)

    def to_option_string(self, value: Union[HaierHoodFanSpeed, bytes, None]) -> Optional[str]:
        try:
            if isinstance(value, bytes):
                value = _converter.erd_decode(value)
            if isinstance(value, HaierHoodFanSpeed):
                return value.stringify()
        except Exception:
            pass
        return HaierHoodFanSpeed.OFF.stringify()


class GeHaierHoodFan(GeErdSelect):
    """Select for Haier/F&P hood fan speed (0x5B13)."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType = ERD_HAIER_HOOD_FAN_SPEED):
        super().__init__(api, erd_code, _FanOptions())
