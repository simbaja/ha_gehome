import logging
from propcache.api import cached_property

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from gehomesdk import ErdCode

from ...devices import ApplianceApi
from ..common import GeEntity

_LOGGER = logging.getLogger(__name__)

# Define the ON and OFF temperature values as constants
K_CUP_ON_TEMP = 190
K_CUP_OFF_TEMP = 0

class GeKCupSwitch(GeEntity, SwitchEntity):
    """A switch to control the K-Cup hot water feature."""

    def __init__(self, api: ApplianceApi):
        # Pass the api instance to the base class
        super().__init__(api)

    @cached_property
    def unique_id(self) -> str:
        # Create a unique ID for this entity
        return f"{self.api.serial_or_mac}_kcup_hot_water"

    @cached_property
    def name(self) -> str | None:
        # Set the friendly name to match other switches using the device's unique ID
        return f"{self.api.serial_or_mac} K-Cup Hot Water"

    @property
    def icon(self) -> str | None: # type: ignore
        # Set the icon based on the switch's state
        return "mdi:coffee-maker" if self.is_on else "mdi:coffee-maker-off-outline"
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available
        
    @cached_property
    def device_class(self) -> SwitchDeviceClass | None:       
        return None

    @property
    def is_on(self) -> bool: # type: ignore
        """Return true if the hot water is set to a non-zero temperature."""
        try:
            # The switch is "on" if the target temperature is not the "off" value
            current_set_temp = self.api.try_get_erd_value(ErdCode.HOT_WATER_SET_TEMP)
            return current_set_temp != K_CUP_OFF_TEMP
        except Exception as e:
            _LOGGER.warning(f"Could not get K-Cup status for {self.unique_id}: {e}")
            return False

    async def async_turn_on(self, **kwargs):
        """Turn the K-Cup heater on by setting the target temperature."""
        _LOGGER.debug(f"Turning on K-Cup heater for {self.unique_id}")
        await self.api.appliance.async_set_erd_value(
            ErdCode.HOT_WATER_SET_TEMP, K_CUP_ON_TEMP
        )

    async def async_turn_off(self, **kwargs):
        """Turn the K-Cup heater off by setting the target temperature to zero."""
        _LOGGER.debug(f"Turning off K-Cup heater for {self.unique_id}")
        await self.api.appliance.async_set_erd_value(
            ErdCode.HOT_WATER_SET_TEMP, K_CUP_OFF_TEMP
        )