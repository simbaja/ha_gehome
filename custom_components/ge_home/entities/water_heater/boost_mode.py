import logging
from typing import Any

from gehomesdk import ErdCodeType, ErdCode, ErdOnOff
from ...devices import ApplianceApi
from ..common import GeErdSwitch, ErdOnOffBoolConverter

_LOGGER = logging.getLogger(__name__)

class GeWaterHeaterBoostModeSwitch(GeErdSwitch):
    """Switch to control the water heater boost mode"""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api, 
            ErdCode.WH_HEATER_BOOST_MODE, 
            ErdOnOffBoolConverter(), 
            icon_on_override="mdi:rocket-launch", 
            icon_off_override="mdi:rocket-launch-outline"
        )
        self._attr_name = "Boost Mode"

    @property
    def is_on(self) -> bool:
        """Return True if boost mode is on."""
        # Use the read-only ERD to get the current state
        return self._converter.boolify(self.appliance.get_erd_value(ErdCode.WH_HEATER_BOOST_MODE))

    async def async_turn_on(self, **kwargs):
        """Turn the boost mode on."""
        _LOGGER.debug(f"Turning on boost mode for {self.unique_id}")
        # Use the write ERD to set the state
        await self.appliance.async_set_erd_value(ErdCode.WH_HEATER_BOOST_STATE, self._converter.true_value())

    async def async_turn_off(self, **kwargs):
        """Turn the boost mode off."""
        _LOGGER.debug(f"Turning off boost mode for {self.unique_id}")
        # Use the write ERD to set the state
        await self.appliance.async_set_erd_value(ErdCode.WH_HEATER_BOOST_STATE, self._converter.false_value())
