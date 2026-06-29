import logging
from typing import List, Any, Optional, Tuple
from gehomesdk import ErdHoodFanSpeedAvailability, ErdHoodFanSpeed, ErdCode
from ...devices import ApplianceApi
from ..common import OptionsConverter

_LOGGER = logging.getLogger(__name__)

class HoodFanSpeedOptionsConverter(OptionsConverter):
    def __init__(self, availability: ErdHoodFanSpeedAvailability):
        super().__init__()
        self.availability = availability
        self.excluded_speeds: List[ErdHoodFanSpeed] = []
        if not availability.off_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.OFF)
        if not availability.low_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.LOW)
        if not availability.med_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.MEDIUM)
        if not availability.high_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.HIGH)
        if not availability.boost_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.BOOST)

    @property
    def options(self) -> List[str]:
        return [str(i.stringify()) for i in ErdHoodFanSpeed if i not in self.excluded_speeds]

    def from_option_string(self, value: str) -> Any:
        try:
            return ErdHoodFanSpeed[value.upper()]
        except Exception:
            _LOGGER.warning(f"Could not set hood fan speed to {value.upper()}")
            return ErdHoodFanSpeed.OFF

    def to_option_string(self, value: Any) -> Optional[str]:
        try:
            if value is not None and hasattr(value, "stringify"):
                return str(value.stringify())
        except Exception:
            pass
        return str(ErdHoodFanSpeed.OFF.stringify())

def detect_hood_fan_speed(api: ApplianceApi) -> Tuple[ErdHoodFanSpeedAvailability, OptionsConverter]:
    if (a := api.try_get_erd_value(ErdCode.HOOD_FAN_SPEED_AVAILABILITY)) is not None:
        return a, HoodFanSpeedOptionsConverter(a)

    if (fs := api.try_get_erd_value(ErdCode.HOOD_AVAILABLE_FAN_SPEEDS)) is not None:
        a = ErdHoodFanSpeedAvailability.from_count(fs)
        return a, HoodFanSpeedOptionsConverter(a)

    a = ErdHoodFanSpeedAvailability(off_available=True)
    return a, HoodFanSpeedOptionsConverter(a)

