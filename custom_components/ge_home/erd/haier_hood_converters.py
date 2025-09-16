import logging
from typing import Optional
from gehomesdk.erd.converters.erd_value_converter import ErdValueConverter
from .haier_hood_codes import HaierHoodFanSpeed, HaierHoodLightLevel

_LOGGER = logging.getLogger(__name__)

class HaierHoodFanSpeedConverter(ErdValueConverter[HaierHoodFanSpeed]):
    def erd_decode(self, value: str) -> Optional[HaierHoodFanSpeed]:
        try:
            return HaierHoodFanSpeed(int(value, 16))
        except Exception as e:
            _LOGGER.warning(f"Failed to decode Haier hood fan speed {value}: {e}")
            return None

    def erd_encode(self, value: HaierHoodFanSpeed) -> str:
        return f"{int(value):02x}"

class HaierHoodLightLevelConverter(ErdValueConverter[HaierHoodLightLevel]):
    def erd_decode(self, value: str) -> Optional[HaierHoodLightLevel]:
        try:
            return HaierHoodLightLevel(int(value, 16))
        except Exception as e:
            _LOGGER.warning(f"Failed to decode Haier hood light level {value}: {e}")
            return None

    def erd_encode(self, value: HaierHoodLightLevel) -> str:
        return f"{int(value):02x}"
