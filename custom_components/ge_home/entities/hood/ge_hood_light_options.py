import logging
from typing import List, Any, Optional, Tuple
from gehomesdk import ErdHoodLightLevelAvailability, ErdHoodLightLevel, ErdHoodLightLevelNew, ErdCode
from ...devices import ApplianceApi
from ..common import OptionsConverter

_LOGGER = logging.getLogger(__name__)

class HoodLightLevelOptionsConverter(OptionsConverter):
    def __init__(self, availability: ErdHoodLightLevelAvailability):
        super().__init__()
        self.availability = availability
        self.excluded_levels: List[ErdHoodLightLevel] = []
        if not availability.off_available:
            self.excluded_levels.append(ErdHoodLightLevel.OFF)
        if not availability.dim_available:
            self.excluded_levels.append(ErdHoodLightLevel.DIM)
        if not availability.med_available:
            self.excluded_levels.append(ErdHoodLightLevel.MED)
        if not availability.high_available:
            self.excluded_levels.append(ErdHoodLightLevel.HIGH)

    @property
    def options(self) -> List[str]:
        return [str(i.stringify()) for i in ErdHoodLightLevel if i not in self.excluded_levels]

    def from_option_string(self, value: str) -> Any:
        try:
            return ErdHoodLightLevel[value.upper()]
        except Exception:
            _LOGGER.warning(f"Could not set hood light level to {value.upper()}")
            return ErdHoodLightLevel.OFF

    def to_option_string(self, value: Any) -> Optional[str]:
        try:
            if value is not None and hasattr(value, "stringify"):
                return str(value.stringify())
        except Exception:
            pass
        return str(ErdHoodLightLevel.OFF.stringify())
    
class HoodLightLevelNewOptionsConverter(OptionsConverter):
    def __init__(self, availability: ErdHoodLightLevelAvailability):
        super().__init__()
        self.availability = availability
        self.excluded_levels: List[ErdHoodLightLevelNew] = []
        if not availability.off_available:
            self.excluded_levels.append(ErdHoodLightLevelNew.OFF)
        if not availability.dim_available:
            self.excluded_levels.append(ErdHoodLightLevelNew.L1)
        if not availability.med_available:
            self.excluded_levels.append(ErdHoodLightLevelNew.L2)
        if not availability.high_available:
            self.excluded_levels.append(ErdHoodLightLevelNew.L3)

    @property
    def options(self) -> List[str]:
        return [str(i.stringify()) for i in ErdHoodLightLevelNew if i not in self.excluded_levels]

    def from_option_string(self, value: str) -> Any:
        try:
            return ErdHoodLightLevelNew[value.upper()]
        except Exception:
            _LOGGER.warning(f"Could not set hood light level to {value.upper()}")
            return ErdHoodLightLevelNew.OFF

    def to_option_string(self, value: Any) -> Optional[str]:
        try:
            if value is not None and hasattr(value, "stringify"):
                return str(value.stringify())
        except Exception:
            pass
        return str(ErdHoodLightLevelNew.OFF.stringify())

def detect_hood_light_level(api: ApplianceApi) -> Tuple[ErdHoodLightLevelAvailability, OptionsConverter]:
    if (a := api.try_get_erd_value(ErdCode.HOOD_LIGHT_LEVEL_AVAILABILITY)) is not None:
        return a, HoodLightLevelOptionsConverter(a)

    if (ll := api.try_get_erd_value(ErdCode.HOOD_AVAILABLE_LIGHT_LEVELS)) is not None:
        a = ErdHoodLightLevelAvailability.from_count(ll)
        return a, HoodLightLevelNewOptionsConverter(a)

    a = ErdHoodLightLevelAvailability(off_available=True)
    return a, HoodLightLevelOptionsConverter(a)
