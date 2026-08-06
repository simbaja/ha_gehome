"""GE Home toaster oven light."""

import logging
from typing import Any, Optional

from homeassistant.components.light.const import ColorMode
from propcache.api import cached_property
from gehomesdk import ErdCodeType

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdLight

_LOGGER = logging.getLogger(__name__)

class GeToasterOvenLight(GeErdLight):
    """Light entity for GE toaster oven light controls."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, control_erd_code: Optional[ErdCodeType] = None):
        super().__init__(api, erd_code, color_mode=ColorMode.ONOFF)
        self._control_erd_code = control_erd_code

    @cached_property
    def name(self) -> Optional[str]:
        return f"{self.entity_identifier} Toaster Oven Light"

    @cached_property
    def unique_id(self) -> Optional[str]:
        return f"{DOMAIN}_{self.entity_identifier}_toaster_oven_light"

    @property
    def icon(self) -> str | None:
        return "mdi:lightbulb"

    @cached_property
    def supported_color_modes(self) -> set[ColorMode]:
        """Flag supported color modes."""
        return {ColorMode.ONOFF}

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        return None

    @property
    def is_on(self) -> bool:
        """Return True if light is on."""
        try:
            return self.appliance.get_erd_value(self.erd_code) == True
        except KeyError:
            return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        _LOGGER.debug(f"Turning on {self.unique_id}")
        await self.appliance.async_set_erd_value(self._writeable_erd_code, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        _LOGGER.debug(f"Turning off {self.unique_id}")
        await self.appliance.async_set_erd_value(self._writeable_erd_code, False)

    @property
    def _writeable_erd_code(self) -> ErdCodeType:
        if self._control_erd_code:
            return self._control_erd_code
        return self.erd_code
