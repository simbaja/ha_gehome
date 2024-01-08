"""GE Home Sensor Entities - Oven"""
import logging
from typing import List, Optional

from gehomesdk import (
    ErdCode,
    ErdWaterHeaterMode
)

from homeassistant.components.water_heater import WaterHeaterEntityFeature

from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from ...devices import ApplianceApi
from ..common import GeAbstractWaterHeater
from .heater_modes import WhHeaterModeConverter

_LOGGER = logging.getLogger(__name__)

class GeWaterHeater(GeAbstractWaterHeater):
    """GE Whole Home Water Heater"""

    icon = "mdi:water-boiler"

    def __init__(self, api: ApplianceApi):
        super().__init__(api)
        self._modes_converter = WhHeaterModeConverter()

    @property
    def heater_type(self) -> str:
        return "heater"

    @property
    def supported_features(self):
        return (WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.TARGET_TEMPERATURE)

    @property
    def temperature_unit(self):
        return UnitOfTemperature.FAHRENHEIT

    @property
    def current_temperature(self) -> Optional[int]:
        return self.appliance.get_erd_value(ErdCode.WH_HEATER_TEMPERATURE)

    @property
    def current_operation(self) -> Optional[str]:
        erd_mode = self.appliance.get_erd_value(ErdCode.WH_HEATER_MODE)
        return self._modes_converter.to_option_string(erd_mode)

    @property
    def operation_list(self) -> List[str]:
        return self._modes_converter.options

    @property
    def target_temperature(self) -> Optional[int]:
        """Return the temperature we try to reach."""
        return self.appliance.get_erd_value(ErdCode.WH_HEATER_TARGET_TEMPERATURE)

    @property
    def min_temp(self) -> int:
        """Return the minimum temperature."""
        min_temp, _ = self.appliance.get_erd_value(ErdCode.WH_HEATER_MIN_MAX_TEMPERATURE)
        return min_temp

    @property
    def max_temp(self) -> int:
        """Return the maximum temperature."""
        _, max_temp = self.appliance.get_erd_value(ErdCode.WH_HEATER_MIN_MAX_TEMPERATURE)
        return max_temp

    async def async_set_operation_mode(self, operation_mode: str):
        """Set the operation mode."""

        erd_mode = self._modes_converter.from_option_string(operation_mode)

        if (erd_mode != ErdWaterHeaterMode.UNKNOWN):
            await self.appliance.async_set_erd_value(ErdCode.WH_HEATER_MODE, erd_mode)

    async def async_set_temperature(self, **kwargs):
        """Set the water temperature"""

        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return

        await self.appliance.async_set_erd_value(ErdCode.WH_HEATER_TARGET_TEMPERATURE, target_temp)

