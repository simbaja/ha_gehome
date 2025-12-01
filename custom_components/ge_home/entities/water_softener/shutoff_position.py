import logging
from typing import List, Any, Optional

from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType, ErdWaterSoftenerShutoffValveState, ErdCode
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

class FilterPositionOptionsConverter(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [i.name.title() 
            for i in ErdWaterSoftenerShutoffValveState 
            if i not in [ErdWaterSoftenerShutoffValveState.UNKNOWN, ErdWaterSoftenerShutoffValveState.TRANSITION]]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdWaterSoftenerShutoffValveState[value.upper()]
        except:
            _LOGGER.warning(f"Could not set filter position to {value.upper()}")
            return ErdWaterSoftenerShutoffValveState.UNKNOWN
    def to_option_string(self, value: Any) -> Optional[str]:
        try:
            if value is not None:
                return value.name.title()
        except:
            pass
        return ErdWaterSoftenerShutoffValveState.UNKNOWN.name.title()

class GeErdShutoffPositionSelect(GeErdSelect):
    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType):
        super().__init__(api, erd_code, FilterPositionOptionsConverter(), icon_override="mdi:valve", entity_category=EntityCategory.CONFIG)

    @property
    def current_option(self):
        """Return the current selected option"""
        
        #if we're transitioning or don't know what the mode is, don't allow changes
        mode: ErdWaterSoftenerShutoffValveState = self.appliance.get_erd_value(ErdCode.WH_SOFTENER_SHUTOFF_VALVE_STATE)
        if mode in [ErdWaterSoftenerShutoffValveState.TRANSITION, ErdWaterSoftenerShutoffValveState.UNKNOWN]:
            return mode.name.title()

        return self._converter.to_option_string(self.appliance.get_erd_value(self.erd_code))

    @property
    def options(self) -> List[str]: # type: ignore
        """Return a list of options"""

        #if we're transitioning or don't know what the mode is, don't allow changes
        mode: ErdWaterSoftenerShutoffValveState = self.appliance.get_erd_value(ErdCode.WH_SOFTENER_SHUTOFF_VALVE_STATE)
        if mode in [ErdWaterSoftenerShutoffValveState.TRANSITION, ErdWaterSoftenerShutoffValveState.UNKNOWN]:
            return [mode.name.title()]

        return self._converter.options        

    async def async_select_option(self, option: str) -> None:
        value = self._converter.from_option_string(option)
        if value in [ErdWaterSoftenerShutoffValveState.UNKNOWN, ErdWaterSoftenerShutoffValveState.TRANSITION]:
            _LOGGER.debug("Cannot set position to transition/unknown")
            return
        if self.appliance.get_erd_value(ErdCode.WH_SOFTENER_SHUTOFF_VALVE_STATE) == ErdWaterSoftenerShutoffValveState.TRANSITION:
            _LOGGER.debug("Cannot set position if in transition")
            return

        return await super().async_select_option(option)
