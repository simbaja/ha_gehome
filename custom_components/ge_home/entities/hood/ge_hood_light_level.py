import logging
from typing import List, Any, Optional

from homeassistant.components.light import ATTR_BRIGHTNESS, LightEntity
from homeassistant.components.light.const import ColorMode
from propcache.api import cached_property
from gehomesdk import ErdCodeType, ErdHoodLightLevelAvailability, ErdHoodLightLevel, ErdHoodLightLevelNew, ErdCode
from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdEntity, GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

class HoodLightLevelOptionsConverter(OptionsConverter):
    def __init__(self, availability: ErdHoodLightLevelAvailability):
        super().__init__()
        self.availability = availability
        self.excluded_levels = []
        if not availability.off_available:
            self.excluded_levels.append(ErdHoodLightLevel.OFF)
        if not availability.dim_available:
            self.excluded_levels.append(ErdHoodLightLevel.DIM)
        if not availability.med_available:
            self.excluded_levels.append(ErdHoodLightLevel.MED)
        if not availability.high_available:
            self.excluded_levels.append(ErdHoodLightLevel.HIGH)

    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in ErdHoodLightLevel if i not in self.excluded_levels]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdHoodLightLevel[value.upper()]
        except:
            _LOGGER.warning(f"Could not set hood light level to {value.upper()}")
            return ErdHoodLightLevel.OFF
    def to_option_string(self, value: ErdHoodLightLevel) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdHoodLightLevel.OFF.stringify()
    
class HoodLightLevelNewOptionsConverter(OptionsConverter):
    def __init__(self, availability: ErdHoodLightLevelAvailability):
        super().__init__()
        self.availability = availability
        self.excluded_levels = []
        if not availability.off_available:
            self.excluded_levels.append(ErdHoodLightLevelNew.OFF)
        if not availability.dim_available:
            self.excluded_levels.append(ErdHoodLightLevelNew.L1)
        if not availability.med_available:
            self.excluded_levels.append(ErdHoodLightLevelNew.L2)
        if not availability.high_available:
            self.excluded_levels.append(ErdHoodLightLevelNew.L3)

    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in ErdHoodLightLevelNew if i not in self.excluded_levels]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdHoodLightLevelNew[value.upper()]
        except:
            _LOGGER.warning(f"Could not set hood light level to {value.upper()}")
            return ErdHoodLightLevelNew.OFF
    def to_option_string(self, value: ErdHoodLightLevelNew) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdHoodLightLevelNew.OFF.stringify()

def detect_hood_light_level(api: ApplianceApi):
    if (a := api.try_get_erd_value(ErdCode.HOOD_LIGHT_LEVEL_AVAILABILITY)) is not None:
        return a, HoodLightLevelOptionsConverter(a)

    if (ll := api.try_get_erd_value(ErdCode.HOOD_AVAILABLE_LIGHT_LEVELS)) is not None:
        a = ErdHoodLightLevelAvailability.from_count(ll)
        return a, HoodLightLevelNewOptionsConverter(a)

    a = ErdHoodLightLevelAvailability(off_available=True)
    return a, HoodLightLevelOptionsConverter(a)


class GeHoodLightLevelSelect(GeErdSelect):
    def __init__(
            self,
            api: ApplianceApi,
            erd_code: ErdCodeType,
            control_erd_code: Optional[ErdCodeType] = None,
            enabled_default: bool = True
        ):
        self._availability, converter = detect_hood_light_level(api)
        self._attr_entity_registry_enabled_default = enabled_default
        super().__init__(api, erd_code, converter, control_erd_code=control_erd_code)

class GeHoodLight(GeErdEntity, LightEntity):
    """Light entity for GE hood light level controls."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, control_erd_code: Optional[ErdCodeType] = None):
        self._availability, self._converter = detect_hood_light_level(api)
        self._control_erd_code = control_erd_code
        super().__init__(api, erd_code)

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
    def available(self) -> bool: # type: ignore
        return super().available

    @cached_property
    def supported_color_modes(self) -> set[ColorMode]:
        """Flag supported color modes."""
        return set([ColorMode.BRIGHTNESS])

    @property
    def color_mode(self) -> ColorMode: # type: ignore
        """Return the color mode of the light."""
        return ColorMode.BRIGHTNESS

    @property
    def brightness(self) -> int | None: # type: ignore
        """Return the brightness of the light."""
        option = self.current_option
        if option == self._off_option:
            return 0

        try:
            level_index = self._light_options.index(option) + 1
            return round((level_index * 255) / len(self._light_options))
        except ValueError:
            _LOGGER.debug(f"Unable to map hood light level {option} to brightness")
            return 0

    @property
    def is_on(self) -> bool: # type: ignore
        """Return True if light is on."""
        return self.current_option != self._off_option

    @property
    def current_option(self) -> str:
        return self._converter.to_option_string(self.appliance.get_erd_value(self.erd_code))

    @cached_property
    def _off_option(self) -> str:
        return next(
            (
                option
                for option in self._converter.options
                if option.lower() == ErdHoodLightLevel.OFF.stringify().lower()
            ),
            ErdHoodLightLevel.OFF.stringify()
        )

    @cached_property
    def _light_options(self) -> List[str]:
        return [
            option
            for option in self._converter.options
            if option.lower() != self._off_option.lower()
        ]

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        brightness = kwargs.pop(ATTR_BRIGHTNESS, self.brightness or 255)
        option = self._option_from_brightness(brightness)
        if option != self.current_option:
            _LOGGER.debug(f"Setting hood light from {self.current_option} to {option}")
            await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.from_option_string(option))

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        if self.current_option != self._off_option:
            _LOGGER.debug(f"Turning off {self.unique_id}")
            await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.from_option_string(self._off_option))

    def _option_from_brightness(self, brightness: int) -> str:
        if brightness <= 0 or len(self._light_options) == 0:
            return self._off_option

        level_index = round((brightness * len(self._light_options)) / 255)
        level_index = min(max(level_index, 1), len(self._light_options))
        return self._light_options[level_index - 1]

    @property
    def _writeable_erd_code(self) -> ErdCodeType:
        if self._control_erd_code:
            return self._control_erd_code

        return self.erd_code
