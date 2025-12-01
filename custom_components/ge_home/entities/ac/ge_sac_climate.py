import logging
from propcache.api import cached_property
from typing import Any, List, Optional

from homeassistant.components.climate.const import HVACMode
from gehomesdk import ErdCode, ErdAcOperationMode, ErdAcAvailableModes, ErdSacTargetTemperatureRange

from ...devices import ApplianceApi
from ..common import GeClimate, OptionsConverter
from .fan_mode_options import AcFanOnlyFanModeOptionsConverter, AcFanModeOptionsConverter

_LOGGER = logging.getLogger(__name__)

class SacHvacModeOptionsConverter(OptionsConverter):
    def __init__(self, available_modes: Optional[ErdAcAvailableModes] = None):
        self._available_modes = available_modes

    @property
    def options(self) -> List[str]:
        modes = [HVACMode.COOL, HVACMode.FAN_ONLY]
        if self._available_modes and self._available_modes.has_heat:
            modes.append(HVACMode.HEAT)
            modes.append(HVACMode.AUTO)
        if self._available_modes and self._available_modes.has_dry:
            modes.append(HVACMode.DRY)
        return [i.value for i in modes]
    
    def from_option_string(self, value: str) -> Any:
        try:
            hvac = HVACMode(value.lower())    
            return {
                HVACMode.AUTO: ErdAcOperationMode.AUTO,
                HVACMode.COOL: ErdAcOperationMode.COOL,
                HVACMode.HEAT: ErdAcOperationMode.HEAT,
                HVACMode.FAN_ONLY: ErdAcOperationMode.FAN_ONLY,
                HVACMode.DRY: ErdAcOperationMode.DRY
            }.get(hvac)
        except ValueError:
            _LOGGER.warning(f"Could not set HVAC mode to {value.upper()}")
            return ErdAcOperationMode.COOL
        
    def to_option_string(self, value: Any) -> Optional[str]:
        mapped = {
                ErdAcOperationMode.ENERGY_SAVER: HVACMode.AUTO,
                ErdAcOperationMode.AUTO: HVACMode.AUTO,
                ErdAcOperationMode.COOL: HVACMode.COOL,
                ErdAcOperationMode.HEAT: HVACMode.HEAT,
                ErdAcOperationMode.DRY: HVACMode.DRY,
                ErdAcOperationMode.FAN_ONLY: HVACMode.FAN_ONLY
            }.get(value)
        
        if(isinstance(mapped, HVACMode)):
            return mapped

        _LOGGER.warning(f"Could not determine operation mode mapping for {value}")
        return HVACMode.COOL
      
class GeSacClimate(GeClimate):
    """Class for Split AC units"""
    def __init__(self, api: ApplianceApi):
        #get a couple ERDs that shouldn't change if available
        self._modes: ErdAcAvailableModes | None = api.try_get_erd_value(ErdCode.AC_AVAILABLE_MODES)
        self._temp_range: ErdSacTargetTemperatureRange | None = api.try_get_erd_value(ErdCode.SAC_TARGET_TEMPERATURE_RANGE)

        #initialize the climate control
        super().__init__(api, SacHvacModeOptionsConverter(self._modes), AcFanModeOptionsConverter(), AcFanOnlyFanModeOptionsConverter())

    @cached_property
    def min_temp(self) -> float:
        temp = 60
        if self._temp_range:
            temp = self._temp_range.min
        return self._convert_temp(temp)

    @cached_property
    def max_temp(self) -> float:
        temp = 86
        if self._temp_range:
            temp = self._temp_range.max        
        return self._convert_temp(temp)