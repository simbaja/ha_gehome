import logging
from typing import List, Any, Optional

from homeassistant.components.fan import FanEntity, FanEntityFeature
from propcache.api import cached_property
from gehomesdk import ErdCodeType, ErdHoodFanSpeedAvailability, ErdHoodFanSpeed, ErdCode
from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdEntity, GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

class HoodFanSpeedOptionsConverter(OptionsConverter):
    def __init__(self, availability: ErdHoodFanSpeedAvailability):
        super().__init__()
        self.availability = availability
        self.excluded_speeds = []
        if not availability.off_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.OFF)
        if not availability.low_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.LOW)
        if not availability.med_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.MEDIUM)
        if not availability.high_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.HIGH)
        if not availability.boost_available:
            self.excluded_speeds.append(ErdHoodFanSpeed.BOOST)

    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in ErdHoodFanSpeed if i not in self.excluded_speeds]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdHoodFanSpeed[value.upper()]
        except:
            _LOGGER.warning(f"Could not set hood fan speed to {value.upper()}")
            return ErdHoodFanSpeed.OFF
    def to_option_string(self, value: ErdHoodFanSpeed) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdHoodFanSpeed.OFF.stringify()

class GeHoodFanSpeedSelect(GeErdSelect):
    def __init__(
            self,
            api: ApplianceApi,
            erd_code: ErdCodeType,
            control_erd_code: Optional[ErdCodeType] = None,
            enabled_default: bool = True
        ):

        # old-style
        self._availability: ErdHoodFanSpeedAvailability | None = api.try_get_erd_value(ErdCode.HOOD_FAN_SPEED_AVAILABILITY)

        # new-style
        if self._availability is None:
            fs: int | None = api.try_get_erd_value(ErdCode.HOOD_AVAILABLE_FAN_SPEEDS)
            if fs is not None:
                self._availability = ErdHoodFanSpeedAvailability.from_count(fs)

        # default
        if self._availability is None:
            self._availability = ErdHoodFanSpeedAvailability(off_available=True)

        self._attr_entity_registry_enabled_default = enabled_default
        super().__init__(api, erd_code, HoodFanSpeedOptionsConverter(self._availability), control_erd_code=control_erd_code)

class GeHoodFan(GeErdEntity, FanEntity):
    """Fan entity for GE hood fan speed controls."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, control_erd_code: Optional[ErdCodeType] = None):

        # old-style
        self._availability: ErdHoodFanSpeedAvailability | None = api.try_get_erd_value(ErdCode.HOOD_FAN_SPEED_AVAILABILITY)

        # new-style
        if self._availability is None:
            fs: int | None = api.try_get_erd_value(ErdCode.HOOD_AVAILABLE_FAN_SPEEDS)
            if fs is not None:
                self._availability = ErdHoodFanSpeedAvailability.from_count(fs)

        # default
        if self._availability is None:
            self._availability = ErdHoodFanSpeedAvailability(off_available=True)

        super().__init__(api, erd_code)
        self._converter = HoodFanSpeedOptionsConverter(self._availability)
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
    def available(self) -> bool: # type: ignore
        return super().available

    @cached_property
    def supported_features(self) -> FanEntityFeature:
        features = FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        if self._boost_option is not None:
            features |= FanEntityFeature.PRESET_MODE
        return features

    @cached_property
    def speed_count(self) -> int:
        return len(self._speed_options)

    @property
    def is_on(self) -> bool | None: # type: ignore
        return self.current_option.lower() != ErdHoodFanSpeed.OFF.stringify().lower()

    @property
    def percentage(self) -> int | None: # type: ignore
        option = self.current_option
        if option.lower() == ErdHoodFanSpeed.OFF.stringify().lower():
            return 0
        if self._boost_option is not None and option.lower() == self._boost_option.lower():
            return 100

        try:
            speed_index = self._speed_options.index(option) + 1
            return (speed_index * 100) // self.speed_count
        except ValueError:
            _LOGGER.debug(f"Unable to map hood fan speed {option} to percentage")
            return 0

    @property
    def preset_mode(self) -> str | None: # type: ignore
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
        return self._converter.to_option_string(self.appliance.get_erd_value(self.erd_code))

    @cached_property
    def _speed_options(self) -> List[str]:
        return [
            option
            for option in self._converter.options
            if option.lower() not in (
                ErdHoodFanSpeed.OFF.stringify().lower(),
                ErdHoodFanSpeed.BOOST.stringify().lower(),
            )
        ]

    @cached_property
    def _boost_option(self) -> str | None:
        return next(
            (
                option
                for option in self._converter.options
                if option.lower() == ErdHoodFanSpeed.BOOST.stringify().lower()
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

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs):
        """Turn the hood fan on."""
        if percentage is None:
            # HomeKit may set speed before active state; preserve that request.
            # Plain "on" commands still default to a middle speed instead of boost.
            percentage = self._requested_percentage or self.percentage or 50
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs):
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
            return ErdHoodFanSpeed.OFF.stringify()

        speed_index = round((percentage * self.speed_count) / 100)
        speed_index = min(max(speed_index, 1), self.speed_count)
        return self._speed_options[speed_index - 1]

    @property
    def _writeable_erd_code(self) -> ErdCodeType:
        if self._control_erd_code:
            return self._control_erd_code

        return self.erd_code
