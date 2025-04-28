import logging
from typing import Any

from gehomesdk import ErdCodeType, ErdCode, ErdOnOff, ErdWaterHeaterActiveState
from ...devices import ApplianceApi
from ..common import GeErdSwitch, BoolConverter

_LOGGER = logging.getLogger(__name__)

class WaterHeaterActiveModeBoolConverter(BoolConverter):
    def boolify(self, value: ErdWaterHeaterActiveState) -> bool:
        # Convert ErdWaterHeaterActiveState to bool
        return value == ErdWaterHeaterActiveState.ON
    
    def true_value(self) -> Any:
        return ErdWaterHeaterActiveState.OFF
    
    def false_value(self) -> Any:
        return ErdWaterHeaterActiveState.OFF

class GeWaterHeaterActiveModeSwitch(GeErdSwitch):
    """Switch to control the water heater Active mode"""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api, 
            ErdCode.WH_HEATER_ACTIVE_STATE, 
            WaterHeaterActiveModeBoolConverter(), 
            icon_on_override="mdi:power", 
            icon_off_override="mdi:power-standby"
        )
        self._attr_name = "Active Mode"

    @property
    def is_on(self) -> bool:
        """Return True if Active mode is on."""
        # Use the read-only ERD to get the current state
        return self._converter.boolify(self.appliance.get_erd_value(ErdCode.WH_HEATER_ACTIVE_STATE))

    async def async_turn_on(self, **kwargs):
        """Turn the Active mode on."""
        _LOGGER.debug(f"Turning on Active mode for {self.unique_id}")
        # Use the write ERD to set the state
        await self.appliance.async_set_erd_value(ErdCode.WH_HEATER_ACTIVE_CONTROL, self._converter.true_value())

    async def async_turn_off(self, **kwargs):
        """Turn the Active mode off."""
        _LOGGER.debug(f"Turning off Active mode for {self.unique_id}")
        # Use the write ERD to set the state
        await self.appliance.async_set_erd_value(ErdCode.WH_HEATER_ACTIVE_CONTROL, self._converter.false_value())
