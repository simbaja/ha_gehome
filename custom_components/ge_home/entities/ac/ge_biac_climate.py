import logging
from typing import Any, List, Optional

from homeassistant.components.climate.const import HVACMode
from gehomesdk import ErdAcOperationMode

from ...devices import ApplianceApi
from ..common import GeClimate, OptionsConverter
from .fan_mode_options import AcFanModeOptionsConverter, AcFanOnlyFanModeOptionsConverter

_LOGGER = logging.getLogger(__name__)

class BiacHvacModeOptionsConverter(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [HVACMode.AUTO, HVACMode.COOL, HVACMode.FAN_ONLY]
    
    def from_option_string(self, value: str) -> Any:
        try:
            hvac = HVACMode(value.lower())
            return {
                    HVACMode.AUTO: ErdAcOperationMode.ENERGY_SAVER,
                    HVACMode.COOL: ErdAcOperationMode.COOL,
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
                ErdAcOperationMode.FAN_ONLY: HVACMode.FAN_ONLY
            }.get(value)

        if(isinstance(mapped, HVACMode)):
            return mapped

        _LOGGER.warning(f"Could not determine operation mode mapping for {value}")
        return HVACMode.COOL
  
class GeBiacClimate(GeClimate):
    """Class for Built-In AC units"""
    def __init__(self, api: ApplianceApi):
        super().__init__(api, BiacHvacModeOptionsConverter(), AcFanModeOptionsConverter(), AcFanOnlyFanModeOptionsConverter())
