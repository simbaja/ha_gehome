import logging
from typing import Any

from gehomesdk import ErdCodeType, ErdCode, ErdOnOff, ErdWaterHeaterBoostState
from ...devices import ApplianceApi
from ..common import GeErdSwitch, BoolConverter

_LOGGER = logging.getLogger(__name__)

class WaterHeaterBoostModeBoolConverter(BoolConverter):
    def boolify(self, value: ErdWaterHeaterBoostState) -> bool:
        # Convert ErdWaterHeaterBoostState to bool
        return value == ErdWaterHeaterBoostState.ON
    
    def true_value(self) -> Any:
        return ErdWaterHeaterBoostState.ON
    
    def false_value(self) -> Any:
        return ErdWaterHeaterBoostState.OFF

class GeWaterHeaterBoostModeSwitch(GeErdSwitch):
    """Switch to control the water heater boost mode"""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api, 
            ErdCode.WH_HEATER_BOOST_STATE, 
            WaterHeaterBoostModeBoolConverter(), 
            icon_on_override="mdi:rocket-launch", 
            icon_off_override="mdi:rocket-launch-outline"
        )
        self._attr_name = "Boost Mode"

    @property
    def is_on(self) -> bool:
        """Return True if boost mode is on."""
        # Use the read-only ERD to get the current state
        return self._converter.boolify(self.appliance.get_erd_value(ErdCode.WH_HEATER_BOOST_STATE))

    async def async_turn_on(self, **kwargs):
        """Turn the boost mode on."""
        _LOGGER.debug(f"Turning on boost mode for {self.unique_id}")
        # Use the write ERD to set the state
        await self.appliance.async_set_erd_value(ErdCode.WH_HEATER_BOOST_CONTROL, self._converter.true_value())

    async def async_turn_off(self, **kwargs):
        """Turn the boost mode off."""
        _LOGGER.debug(f"Turning off boost mode for {self.unique_id}")
        # Use the write ERD to set the state
        await self.appliance.async_set_erd_value(ErdCode.WH_HEATER_BOOST_CONTROL, self._converter.false_value())
