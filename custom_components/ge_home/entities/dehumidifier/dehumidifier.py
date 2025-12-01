"""GE Home Dehumidifier"""
import logging
from propcache.api import cached_property
from typing import Optional

from homeassistant.components.humidifier import HumidifierDeviceClass
from homeassistant.components.humidifier.const import HumidifierEntityFeature
from gehomesdk import ErdCode, DehumidifierTargetRange

from ...devices import ApplianceApi
from ..common import GeHumidifier
from .const import *
from .dehumidifier_fan_options import DehumidifierFanSettingOptionsConverter

_LOGGER = logging.getLogger(__name__)

class GeDehumidifier(GeHumidifier):
    """GE Dehumidifier"""

    def __init__(self, api: ApplianceApi):        
        
        #try to get the range
        range: DehumidifierTargetRange | None = api.try_get_erd_value(ErdCode.DHUM_TARGET_HUMIDITY_RANGE)
        low = DEFAULT_MIN_HUMIDITY if range is None else range.min_humidity
        high = DEFAULT_MAX_HUMIDITY if range is None else range.max_humidity

        #try to get the fan mode and determine feature
        mode = api.try_get_erd_value(ErdCode.AC_FAN_SETTING)
        self._has_fan = mode is not None
        self._mode_converter = DehumidifierFanSettingOptionsConverter()

        #initialize the dehumidifier
        super().__init__(api, 
            HumidifierDeviceClass.DEHUMIDIFIER,
            ErdCode.AC_POWER_STATUS,
            ErdCode.DHUM_TARGET_HUMIDITY,
            ErdCode.DHUM_CURRENT_HUMIDITY,
            low,
            high
        )

    @property
    def icon(self) -> str | None:
        return "mdi:air-humidifier"        

    @cached_property
    def supported_features(self) -> HumidifierEntityFeature:
        if self._has_fan:
            return HumidifierEntityFeature(HumidifierEntityFeature.MODES)
        else:
            return HumidifierEntityFeature(0)

    @property
    def mode(self) -> str | None: # type: ignore
        if not self._has_fan:
            raise NotImplementedError()
        
        return self._mode_converter.to_option_string(
            self.appliance.get_erd_value(ErdCode.AC_FAN_SETTING)
        )

    @cached_property
    def available_modes(self) -> list[str] | None:
        if not self._has_fan:
            raise NotImplementedError()
                
        return self._mode_converter.options
    
    async def async_set_mode(self, mode: str) -> None:
        if not self._has_fan:
            raise NotImplementedError()

        """Change the selected mode."""
        _LOGGER.debug(f"Setting mode from {self.mode} to {mode}")
        
        new_state = self._mode_converter.from_option_string(mode)
        await self.appliance.async_set_erd_value(ErdCode.AC_FAN_SETTING, new_state)
