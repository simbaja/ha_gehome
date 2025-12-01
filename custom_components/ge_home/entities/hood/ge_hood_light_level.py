import logging
from typing import List, Any, Optional

from gehomesdk import ErdCodeType, ErdHoodLightLevelAvailability, ErdHoodLightLevel, ErdHoodLightLevelNew, ErdCode
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

class HoodLightLevelOptionsConverter(OptionsConverter):
    def __init__(self, availability: ErdHoodLightLevelAvailability):
        super().__init__()
        self.availability = availability
        self.excluded_levels = []
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
        return [i.stringify() for i in ErdHoodLightLevel if i not in self.excluded_levels]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdHoodLightLevel[value.upper()]
        except:
            _LOGGER.warning(f"Could not set hood light level to {value.upper()}")
            return ErdHoodLightLevel.OFF
    def to_option_string(self, value: ErdHoodLightLevel) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdHoodLightLevel.OFF.stringify()
    
class HoodLightLevelNewOptionsConverter(OptionsConverter):
    def __init__(self, availability: ErdHoodLightLevelAvailability):
        super().__init__()
        self.availability = availability
        self.excluded_levels = []
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
        return [i.stringify() for i in ErdHoodLightLevelNew if i not in self.excluded_levels]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdHoodLightLevelNew[value.upper()]
        except:
            _LOGGER.warning(f"Could not set hood light level to {value.upper()}")
            return ErdHoodLightLevelNew.OFF
    def to_option_string(self, value: ErdHoodLightLevelNew) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdHoodLightLevelNew.OFF.stringify()


class GeHoodLightLevelSelect(GeErdSelect):
    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, control_erd_code: Optional[ErdCodeType] = None):
        self._availability, converter = self._detect_availability(api)
        super().__init__(api, erd_code, converter, control_erd_code=control_erd_code)

    def _detect_availability(self, api: ApplianceApi):
        if (a := api.try_get_erd_value(ErdCode.HOOD_LIGHT_LEVEL_AVAILABILITY)) is not None:
            return a, HoodLightLevelOptionsConverter(a)

        if (ll := api.try_get_erd_value(ErdCode.HOOD_AVAILABLE_LIGHT_LEVELS)) is not None:
            a = ErdHoodLightLevelAvailability.from_count(ll)
            return a, HoodLightLevelNewOptionsConverter(a)

        a = ErdHoodLightLevelAvailability(off_available=True)
        return a, HoodLightLevelOptionsConverter(a)