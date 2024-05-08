import logging
from typing import List, Any, Optional

from gehomesdk import ErdConvertableDrawerMode
from homeassistant.const import UnitOfTemperature
from homeassistant.util.unit_system import UnitSystem, UnitOfTemperature
from ..common import OptionsConverter

_LOGGER = logging.getLogger(__name__)

_TEMP_MAP = {
    ErdConvertableDrawerMode.MEAT: 29,
    ErdConvertableDrawerMode.BEVERAGE: 33,
    ErdConvertableDrawerMode.SNACK: 37,
    ErdConvertableDrawerMode.WINE: 42
}

class ConvertableDrawerModeOptionsConverter(OptionsConverter):
    def __init__(self, units: UnitSystem):
        super().__init__()
        self._excluded_options = [
            ErdConvertableDrawerMode.UNKNOWN0, 
            ErdConvertableDrawerMode.UNKNOWN1,
            ErdConvertableDrawerMode.NA
        ]
        self._units = units

    @property
    def options(self) -> List[str]:
        return [self.to_option_string(i) for i in ErdConvertableDrawerMode if i not in self._excluded_options]

    def from_option_string(self, value: str) -> Any:
        try:
            v = value.split(" ")[0]
            return ErdConvertableDrawerMode[v.upper()]
        except:
            _LOGGER.warn(f"Could not set drawer mode to {value.upper()}")
            return ErdConvertableDrawerMode.NA
    def to_option_string(self, value: ErdConvertableDrawerMode) -> Optional[str]:
        try:
            if value is not None:
                v = value.stringify()
                t = _TEMP_MAP.get(value, None)

                if t and self._units.temperature_unit == UnitOfTemperature.CELSIUS:
                    t = self._units.temperature(float(t), UnitOfTemperature.FAHRENHEIT)
                    t = round(t,1)
                
                if t:
                    return f"{v} ({t}{self._units.temperature_unit})"
                return v
        except:
            pass
        
        return ErdConvertableDrawerMode.NA.stringify()

