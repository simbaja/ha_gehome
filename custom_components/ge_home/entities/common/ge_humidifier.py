import abc
import logging
from propcache.api import cached_property
from typing import Any, Optional

from homeassistant.components.humidifier import HumidifierEntity, HumidifierDeviceClass
from homeassistant.components.humidifier.const import HumidifierEntityFeature

from gehomesdk import ErdCodeType, ErdOnOff

from ...const import DOMAIN
from ...devices import ApplianceApi
from .ge_entity import GeEntity

DEFAULT_TARGET_PRECISION = 5

_LOGGER = logging.getLogger(__name__)

class GeHumidifier(GeEntity, HumidifierEntity, metaclass=abc.ABCMeta):
    """GE Humidifier Abstract Entity """

    def __init__(
        self,
        api: ApplianceApi,
        device_class: HumidifierDeviceClass,
        power_status_erd_code: ErdCodeType,
        target_humidity_erd_code: ErdCodeType,
        current_humidity_erd_code: ErdCodeType,
        range_min: int,
        range_max: int,
        target_precision = DEFAULT_TARGET_PRECISION
    ):
        super().__init__(api)
        self._device_class = device_class
        self._power_status_erd_code = power_status_erd_code
        self._target_humidity_erd_code = target_humidity_erd_code
        self._current_humidity_erd_code = current_humidity_erd_code
        self._range_min = range_min
        self._range_max = range_max
        self._target_precision = target_precision

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_{self._device_class}"

    @cached_property
    def name(self) -> Optional[str]:
        return f"{self.serial_or_mac} {self._device_class.title()}"

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available

    @property
    def target_humidity(self) -> int | None: # type: ignore
        return int(self.appliance.get_erd_value(self._target_humidity_erd_code))

    @property
    def current_humidity(self) -> int | None: # type: ignore
        return int(self.appliance.get_erd_value(self._current_humidity_erd_code))

    @cached_property
    def min_humidity(self) -> int:
        return self._range_min

    @cached_property
    def max_humidity(self) -> int:
        return self._range_max

    @cached_property
    def supported_features(self) -> HumidifierEntityFeature:
        return HumidifierEntityFeature(HumidifierEntityFeature.MODES)

    @property
    def is_on(self) -> bool: # type: ignore
        return self.appliance.get_erd_value(self._power_status_erd_code) == ErdOnOff.ON

    @cached_property
    def device_class(self) -> HumidifierDeviceClass | None:
        return self._device_class

    async def async_set_humidity(self, humidity: int) -> None:
        # round to target precision
        target = round(humidity / self._target_precision) * self._target_precision

        # if it's the same, just exit
        if self.target_humidity == target:
            return

        _LOGGER.debug(f"Setting Target Humidity from {self.target_humidity} to {target}")

        # make sure we're on
        if not self.is_on:
            await self.async_turn_on()

        # set the target humidity
        await self.appliance.async_set_erd_value(
            self._target_humidity_erd_code,
            target,
        )

    async def async_turn_on(self, **kwargs: Any):
        await self.appliance.async_set_erd_value(
            self._power_status_erd_code, ErdOnOff.ON
        )

    async def async_turn_off(self, **kwargs: Any):
        await self.appliance.async_set_erd_value(
            self._power_status_erd_code, ErdOnOff.OFF
        )