import logging
from typing import List, Optional, Any

from homeassistant.components.light import ATTR_BRIGHTNESS
from propcache.api import cached_property
from gehomesdk import ErdCodeType, ErdHoodLightLevel
from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdLight
from .ge_hood_light_options import detect_hood_light_level

_LOGGER = logging.getLogger(__name__)

class GeHoodLight(GeErdLight):
    """Light entity for GE hood light level controls."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, control_erd_code: Optional[ErdCodeType] = None):
        super().__init__(api, erd_code)
        self._availability, self._converter = detect_hood_light_level(api)
        self._control_erd_code = control_erd_code

    @cached_property
    def name(self) -> Optional[str]:
        return f"{self.serial_or_mac} Hood Light"

    @cached_property
    def unique_id(self) -> Optional[str]:
        return f"{DOMAIN}_{self.serial_or_mac}_hood_light"

    @property
    def icon(self) -> str | None: 
        return "mdi:lightbulb"

    @property
    def brightness(self) -> int: 
        """Return the brightness of the light."""
        option = self._current_option
        if option == self._off_option:
            return 0

        try:
            opts = self._light_options
            level_index = opts.index(option) + 1
            return round((level_index * 255) / len(opts))
        except ValueError:
            _LOGGER.debug(f"Unable to map hood light level {option} to brightness")
            return 0

    @property
    def is_on(self) -> bool: 
        """Return True if light is on."""
        return self._current_option != self._off_option

    @property
    def _current_option(self) -> str:
        try:
            val = self._converter.to_option_string(self.appliance.get_erd_value(self.erd_code))
            if val is not None:
                return str(val)
        except Exception:
            pass
        return self._off_option

    @cached_property
    def _off_option(self) -> str:
        off_str = str(ErdHoodLightLevel.OFF.stringify())
        return next(
            (
                option
                for option in self._converter.options
                if option.lower() == off_str.lower()
            ),
            off_str
        )

    @cached_property
    def _light_options(self) -> List[str]:
        return [
            option
            for option in self._converter.options
            if option.lower() != self._off_option.lower()
        ]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness: int = kwargs.pop(ATTR_BRIGHTNESS, self.brightness or 255)
        option = self._option_from_brightness(brightness)
        if option != self._current_option:
            _LOGGER.debug(f"Setting hood light from {self._current_option} to {option}")
            await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.from_option_string(option))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        if self._current_option != self._off_option:
            _LOGGER.debug(f"Turning off {self.unique_id}")
            await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.from_option_string(self._off_option))

    def _option_from_brightness(self, brightness: int) -> str:
        opts = self._light_options
        if brightness <= 0 or len(opts) == 0:
            return self._off_option

        level_index = round((brightness * len(opts)) / 255)
        level_index = min(max(level_index, 1), len(opts))
        return opts[level_index - 1]

    @property
    def _writeable_erd_code(self) -> ErdCodeType:
        if self._control_erd_code:
            return self._control_erd_code

        return self.erd_code
