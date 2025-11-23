import logging
from typing import List, Any, Optional

from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType, ErdOvenLightLevelAvailability, ErdOvenLightLevel, ErdCode

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

class OvenLightLevelOptionsConverter(OptionsConverter):
    def __init__(self, availability: Optional[ErdOvenLightLevelAvailability]):
        super().__init__()
        self.availability = availability
        self.excluded_levels = [ErdOvenLightLevel.NOT_AVAILABLE]

        if not availability or not availability.dim_available:
            self.excluded_levels.append(ErdOvenLightLevel.DIM)
        
    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in ErdOvenLightLevel if i not in self.excluded_levels]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdOvenLightLevel[value.upper()]
        except:
            _LOGGER.warning(f"Could not set Oven light level to {value.upper()}")
            return ErdOvenLightLevel.OFF
    def to_option_string(self, value: ErdOvenLightLevel) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdOvenLightLevel.OFF.stringify()

class GeOvenLightLevelSelect(GeErdSelect):

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, erd_override: Optional[str] = None):
        self._availability: ErdOvenLightLevelAvailability | None = api.try_get_erd_value(ErdCode.LOWER_OVEN_LIGHT_AVAILABILITY)

        #check to see if we have a status
        value: ErdOvenLightLevel | None = api.try_get_erd_value(erd_code)
        self._has_status = value is not None and value != ErdOvenLightLevel.NOT_AVAILABLE
        self._assumed_state = ErdOvenLightLevel.OFF

        super().__init__(api, erd_code, OvenLightLevelOptionsConverter(self._availability), erd_override=erd_override, entity_category=EntityCategory.CONFIG)

    @property
    def assumed_state(self) -> bool: # type: ignore
        return not self._has_status
    
    @property
    def current_option(self) -> str | None:
        if self.assumed_state:
            return self._assumed_state.name

        return self._converter.to_option_string(self.appliance.get_erd_value(self.erd_code))

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug(f"Setting select from {self.current_option} to {option}")
        
        new_state: ErdOvenLightLevel = self._converter.from_option_string(option)
        await self.appliance.async_set_erd_value(self.erd_code, new_state)        
        self._assumed_state = new_state
        