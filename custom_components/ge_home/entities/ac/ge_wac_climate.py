import logging
from propcache.api import cached_property
from typing import Any, List, Optional

from homeassistant.components.climate.const import (
    HVACMode,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntityFeature,
)
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
        modes = [HVACMode.AUTO, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY]
        if self._available_modes and self._available_modes.has_heat:
            modes.append(HVACMode.HEAT)
        return [i.value for i in modes]

    def from_option_string(self, value: str) -> Any:
        try:
            hvac = HVACMode(value.lower())
            if self._available_modes and self._available_modes.has_auto:
                auto_mode = ErdAcOperationMode.AUTO
            else:
                auto_mode = ErdAcOperationMode.ENERGY_SAVER
            return {
                HVACMode.AUTO: auto_mode,
                HVACMode.COOL: ErdAcOperationMode.COOL,
                HVACMode.HEAT: ErdAcOperationMode.HEAT,
                HVACMode.DRY: ErdAcOperationMode.DRY,
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
                ErdAcOperationMode.DRY: HVACMode.DRY,
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

    @cached_property
    def supported_features(self) -> ClimateEntityFeature:
        features = super().supported_features
        if self._modes and self._modes.has_eco:
            features |= ClimateEntityFeature.PRESET_MODE
        return features

    @property
    def preset_mode(self) -> str | None: # type: ignore
        mode = self.appliance.get_erd_value(self.hvac_mode_erd_code)
        if mode == ErdAcOperationMode.ENERGY_SAVER:
            return PRESET_ECO
        return PRESET_NONE

    @cached_property
    def preset_modes(self) -> list[str] | None:
        if not (self._modes and self._modes.has_eco):
            return None
        return [PRESET_NONE, PRESET_ECO]

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == PRESET_ECO:
            await self.appliance.async_set_erd_value(
                self.hvac_mode_erd_code, ErdAcOperationMode.ENERGY_SAVER
            )
        elif preset_mode == PRESET_NONE:
            # If turning off eco, revert to the appropriate mode for the current HVAC mode
            if self.hvac_mode == HVACMode.AUTO:
                if self._modes and self._modes.has_auto:
                    await self.appliance.async_set_erd_value(self.hvac_mode_erd_code, ErdAcOperationMode.AUTO)
                else:
                    await self.appliance.async_set_erd_value(self.hvac_mode_erd_code, ErdAcOperationMode.COOL)

