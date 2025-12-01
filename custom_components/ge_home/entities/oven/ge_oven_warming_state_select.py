import logging
from typing import List, Any, Optional

from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType, ErdOvenWarmingState
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

class OvenWarmingStateOptionsConverter(OptionsConverter):       
    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in ErdOvenWarmingState]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdOvenWarmingState[value.upper()]
        except:
            _LOGGER.warning(f"Could not set Oven warming state to {value.upper()}")
            return ErdOvenWarmingState.OFF
    def to_option_string(self, value: ErdOvenWarmingState) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdOvenWarmingState.OFF.stringify()

class GeOvenWarmingStateSelect(GeErdSelect):

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, erd_override: Optional[str] = None):
        #check to see if we have a status
        value: ErdOvenWarmingState | None = api.try_get_erd_value(erd_code)
        self._has_status = value is not None and value != ErdOvenWarmingState.NOT_AVAILABLE
        self._assumed_state = ErdOvenWarmingState.OFF

        super().__init__(api, erd_code, OvenWarmingStateOptionsConverter(), erd_override=erd_override, entity_category=EntityCategory.CONFIG)

    @property
    def assumed_state(self) -> bool: # type: ignore
        return not self._has_status
    
    @property
    def current_option(self):
        if self.assumed_state:
            return self._assumed_state.name

        return self._converter.to_option_string(self.appliance.get_erd_value(self.erd_code))

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        _LOGGER.debug(f"Setting select from {self.current_option} to {option}")
        
        new_state: ErdOvenWarmingState = self._converter.from_option_string(option)
        await self.appliance.async_set_erd_value(self.erd_code, new_state)
        self._assumed_state = new_state
        