import logging
from propcache.api import cached_property
from typing import Optional

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, 
    LightEntity
)
from homeassistant.components.light.const import (
    ColorMode
)
from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from .ge_erd_entity import GeErdEntity

_LOGGER = logging.getLogger(__name__)

def to_ge_level(level):
    """Convert the given Home Assistant light level (0-255) to GE (0-100)."""
    return int(round((level * 100) / 255))

def to_hass_level(level):
    """Convert the given GE (0-100) light level to Home Assistant (0-255)."""
    return int((level * 255) // 100)

class GeErdLight(GeErdEntity, LightEntity):
    """Lights for ERD codes."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, erd_override: Optional[str] = None, color_mode: ColorMode = ColorMode.BRIGHTNESS, entity_category: Optional[EntityCategory] = None):
        super().__init__(api, erd_code, erd_override, entity_category=entity_category)
        self._color_mode = color_mode

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available

    @cached_property
    def supported_color_modes(self) -> set[ColorMode]:
        """Flag supported color modes."""
        return set([ColorMode.BRIGHTNESS])
    
    @property
    def color_mode(self) -> ColorMode: # type: ignore
        """Return the color mode of the light."""
        return self._color_mode

    @property
    def brightness(self): # type: ignore
        """Return the brightness of the light."""
        return to_hass_level(self.appliance.get_erd_value(self.erd_code))        

    @property
    def is_on(self) -> bool: # type: ignore
        """Return True if light is on."""
        return self.appliance.get_erd_value(self.erd_code) > 0

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        brightness = kwargs.pop(ATTR_BRIGHTNESS, 255)

        _LOGGER.debug(f"Turning on {self.unique_id}")
        await self._set_brightness(brightness, **kwargs)

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        _LOGGER.debug(f"Turning off {self.unique_id}")
        await self._set_brightness(0, **kwargs)

    async def _set_brightness(self, brightness, **kwargs):
        await self.appliance.async_set_erd_value(self.erd_code, to_ge_level(brightness))

