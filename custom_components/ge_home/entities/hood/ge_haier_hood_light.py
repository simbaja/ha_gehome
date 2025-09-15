import logging
from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from ..common import GeEntity

_LOGGER = logging.getLogger(__name__)

class GeHaierHoodLight(GeEntity, LightEntity):
    """A light entity for a Haier Hood appliance."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType):
        # Correctly call the parent constructor with ONLY the api object
        super().__init__(api)
        # Store the ERD code on this instance for the other methods to use
        self.erd_code = erd_code

    @property
    def is_on(self) -> bool:
        """Return True if the light is on."""
        return self.appliance.get_erd_value(self.erd_code) == 1

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        _LOGGER.debug(f"Turning on {self.unique_id}")
        await self.appliance.async_set_erd_value(self.erd_code, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        _LOGGER.debug(f"Turning off {self.unique_id}")
        await self.appliance.async_set_erd_value(self.erd_code, 0)

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """This light only supports on/off."""
        return {ColorMode.ONOFF}

    @property
    def color_mode(self) -> ColorMode:
        """Return the color mode of the light."""
        return ColorMode.ONOFF

    @property
    def icon(self) -> str:
        return "mdi:lightbulb"