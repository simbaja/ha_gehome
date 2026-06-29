import logging
from typing import List, Optional, Any

from homeassistant.components.fan import FanEntityFeature
from propcache.api import cached_property
from gehomesdk import ErdCodeType, ErdHoodFanSpeed
from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdFan
from .ge_hood_fan_options import detect_hood_fan_speed

_LOGGER = logging.getLogger(__name__)

class GeHoodFan(GeErdFan):
    """Fan entity for GE hood fan speed controls."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, control_erd_code: Optional[ErdCodeType] = None):
        self._availability, self._converter = detect_hood_fan_speed(api)
        super().__init__(api, erd_code)
        self._control_erd_code = control_erd_code
        self._requested_percentage: int | None = None

    @cached_property
    def name(self) -> Optional[str]:
        return f"{self.serial_or_mac} Hood Fan"

    @cached_property
    def unique_id(self) -> Optional[str]:
        return f"{DOMAIN}_{self.serial_or_mac}_hood_fan"

    @property
    def icon(self) -> str | None: 
        return "mdi:fan"

    @property
    def supported_features(self) -> FanEntityFeature: 
        features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self._boost_option is not None:
            features |= FanEntityFeature.PRESET_MODE
        return features

    @cached_property
    def speed_count(self) -> int: 
        return len(self._speed_options)

    @property
    def is_on(self) -> bool: 
        off_str = str(ErdHoodFanSpeed.OFF.stringify())
        return self.current_option.lower() != off_str.lower()

    @property
    def percentage(self) -> int: 
        option = self.current_option
        off_str = str(ErdHoodFanSpeed.OFF.stringify())
        if option.lower() == off_str.lower():
            return 0
        if self._boost_option is not None and option.lower() == self._boost_option.lower():
            return 100

        try:
            opts = self._speed_options
            speed_index = opts.index(option) + 1
            return (speed_index * 100) // self.speed_count
        except ValueError:
            _LOGGER.debug(f"Unable to map hood fan speed {option} to percentage")
            return 0

    @property
    def preset_mode(self) -> str | None: # pyright: ignore[reportIncompatibleVariableOverride]
        if self._boost_option is not None and self.current_option.lower() == self._boost_option.lower():
            return self._boost_option
        return None

    @cached_property
    def preset_modes(self) -> list[str] | None:
        if self._boost_option is not None:
            return [self._boost_option]
        return None

    @property
    def current_option(self) -> str:
        try:
            val = self._converter.to_option_string(self.appliance.get_erd_value(self.erd_code))
            if val is not None:
                return str(val)
        except Exception:
            pass
        return str(ErdHoodFanSpeed.OFF.stringify())

    @cached_property
    def _speed_options(self) -> List[str]:
        off_str = str(ErdHoodFanSpeed.OFF.stringify())
        boost_str = str(ErdHoodFanSpeed.BOOST.stringify())
        return [
            option
            for option in self._converter.options
            if option.lower() not in (
                off_str.lower(),
                boost_str.lower(),
            )
        ]

    @cached_property
    def _boost_option(self) -> str | None:
        boost_str = str(ErdHoodFanSpeed.BOOST.stringify())
        return next(
            (
                option
                for option in self._converter.options
                if option.lower() == boost_str.lower()
            ),
            None
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the hood fan speed percentage."""
        self._requested_percentage = percentage
        option = self._option_from_percentage(percentage)
        if option != self.current_option:
            _LOGGER.debug(f"Setting hood fan from {self.current_option} to {option}")
            await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.from_option_string(option))

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        """Turn the hood fan on."""
        if percentage is None:
            percentage = self._requested_percentage or self.percentage or 50
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the hood fan off."""
        await self.async_set_percentage(0)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the hood fan preset mode."""
        if self._boost_option is None or preset_mode.lower() != self._boost_option.lower():
            raise ValueError(f"Unsupported hood fan preset mode: {preset_mode}")

        self._requested_percentage = 100
        if self.current_option.lower() != self._boost_option.lower():
            _LOGGER.debug(f"Setting hood fan from {self.current_option} to {self._boost_option}")
            await self.appliance.async_set_erd_value(self._writeable_erd_code, self._converter.from_option_string(self._boost_option))

    def _option_from_percentage(self, percentage: int) -> str:
        if percentage <= 0 or self.speed_count == 0:
            return str(ErdHoodFanSpeed.OFF.stringify())

        speed_index = round((percentage * self.speed_count) / 100)
        speed_index = min(max(speed_index, 1), self.speed_count)
        return self._speed_options[speed_index - 1]

    @property
    def _writeable_erd_code(self) -> ErdCodeType:
        if self._control_erd_code:
            return self._control_erd_code

        return self.erd_code
