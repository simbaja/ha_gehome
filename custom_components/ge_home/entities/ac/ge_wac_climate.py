import logging
from typing import Any, List, Optional

from homeassistant.components.climate.const import HVACMode
from gehomesdk import ErdAcOperationMode, ErdCode, ErdAcAvailableModes

from ...devices import ApplianceApi
from ..common import GeClimate, OptionsConverter
from .fan_mode_options import AcFanModeOptionsConverter, AcFanOnlyFanModeOptionsConverter

_LOGGER = logging.getLogger(__name__)

class WacHvacModeOptionsConverter(OptionsConverter):
    def __init__(self, available_modes: Optional[ErdAcAvailableModes] = None):
        self._available_modes = available_modes

    @property
    def options(self) -> List[str]:
        modes = [HVACMode.AUTO, HVACMode.COOL, HVACMode.FAN_ONLY]
        if self._available_modes and self._available_modes.has_heat:
            modes.append(HVACMode.HEAT)
        return [i.value for i in modes]

    def from_option_string(self, value: str) -> Any:
        try:
            hvac = HVACMode(value.lower())    
            return {
                HVACMode.AUTO: ErdAcOperationMode.ENERGY_SAVER,
                HVACMode.COOL: ErdAcOperationMode.COOL,
                HVACMode.HEAT: ErdAcOperationMode.HEAT,
                HVACMode.FAN_ONLY: ErdAcOperationMode.FAN_ONLY
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
                ErdAcOperationMode.FAN_ONLY: HVACMode.FAN_ONLY
            }.get(value)

        if(isinstance(mapped, HVACMode)):
            return mapped
        
        _LOGGER.warning(f"Could not determine operation mode mapping for {value}")
        return HVACMode.COOL
  
class GeWacClimate(GeClimate):
    """Class for Window AC units"""
    def __init__(self, api: ApplianceApi):
        #get the available modes
        self._modes: ErdAcAvailableModes | None = api.try_get_erd_value(ErdCode.AC_AVAILABLE_MODES)

        super().__init__(api, WacHvacModeOptionsConverter(self._modes), AcFanModeOptionsConverter(), AcFanOnlyFanModeOptionsConverter())

