"""GE Home Water Heater Boost Switch"""
import logging
from gehomesdk import ErdCode, ErdOnOff

from ...devices import ApplianceApi
from ..common import GeErdSwitch, ErdOnOffBoolConverter

_LOGGER = logging.getLogger(__name__)

class GeWaterHeaterBoostSwitch(GeErdSwitch):
    """Switch for controlling water heater boost mode."""
    
    icon = "mdi:water-boiler"
    
    def __init__(self, api: ApplianceApi):
        """Initialize the water heater boost switch."""
        super().__init__(api, ErdCode.WH_HEATER_BOOST_STATE, ErdOnOffBoolConverter())
        self._attr_name = f"{self.serial_or_mac} Water Heater Boost"
        self._attr_unique_id = f"{self.serial_or_mac}_water_heater_boost"
    
    @property
    def is_on(self) -> bool:
        """Return True if boost mode is on."""
        # Use the boost mode to determine if the boost mode is on
        boost_state = self.appliance.get_erd_value(ErdCode.WH_HEATER_BOOST_MODE)
        return boost_state == ErdOnOff.ON
    
    async def async_turn_on(self, **kwargs):
        """Turn the boost mode on."""
        _LOGGER.debug(f"Turning on water heater boost mode {self.unique_id}")
        await self.appliance.async_set_erd_value(self.erd_code, ErdOnOff.ON)
    
    async def async_turn_off(self, **kwargs):
        """Turn the boost mode off."""
        _LOGGER.debug(f"Turning off water heater boost mode {self.unique_id}")
        await self.appliance.async_set_erd_value(self.erd_code, ErdOnOff.OFF)
