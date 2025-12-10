import logging
from typing import List, Any, Optional

from gehomesdk import ErdWaterHeaterMode, ErdCode, ErdBrand
from ..common import OptionsConverter

_LOGGER = logging.getLogger(__name__)

class WhHeaterModeConverter(OptionsConverter):
    def __init__(self, api=None):
        """Initialize with optional API reference to check brand."""
        self._api = api
        self._brand = None
        if api:
            try:
                self._brand = api.try_get_erd_value(ErdCode.BRAND)
            except:
                pass
    
    @property
    def is_haier(self) -> bool:
        """Check if this is a Haier brand water heater."""
        return self._brand in [ErdBrand.HAIER, ErdBrand.HAIER_FPA]
    
    def _get_mode_name(self, mode: ErdWaterHeaterMode) -> Optional[str]:
        """Get the display name for a mode, considering brand."""
        if mode == ErdWaterHeaterMode.UNKNOWN:
            return None
        
        # Haier-specific mode names (High Demand not supported on Haier)
        if self.is_haier:
            # High Demand mode doesn't exist on Haier water heaters
            if mode == ErdWaterHeaterMode.HIGH_DEMAND:
                return None
            
            haier_names = {
                ErdWaterHeaterMode.HYBRID: "Auto",
                ErdWaterHeaterMode.STANDARD_ELECTRIC: "Electric",
                ErdWaterHeaterMode.HEAT_PUMP: "Eco",
                ErdWaterHeaterMode.VACATION: "Vacation"
            }
            return haier_names.get(mode, mode.stringify())
        
        # Default GE mode names
        return mode.stringify()
    
    def get_mode_name(self, mode: ErdWaterHeaterMode) -> Optional[str]:
        """Public method to get the display name for a mode."""
        return self._get_mode_name(mode)
    
    def get_available_options(self) -> List[str]:
        """Get list of available mode options with brand-specific names."""
        return self.options
    
    def get_mode_from_name(self, name: str) -> Optional[ErdWaterHeaterMode]:
        """Get the mode enum from display name."""
        return self.from_option_string(name)
    
    def set_appliance(self, appliance):
        """Set the appliance reference to check brand."""
        if appliance and not self._brand:
            try:
                self._brand = appliance.get_erd_value(ErdCode.BRAND)
            except:
                pass
    
    @property
    def options(self) -> List[str]:
        """Get list of available mode options with brand-specific names."""
        options = []
        for mode in ErdWaterHeaterMode:
            name = self._get_mode_name(mode)
            if name:
                options.append(name)
        return options
    
    def from_option_string(self, value: str) -> Any:
        """Convert from display string to ErdWaterHeaterMode."""
        # Handle Haier-specific names
        if self.is_haier:
            haier_mapping = {
                "AUTO": ErdWaterHeaterMode.HYBRID,
                "ELECTRIC": ErdWaterHeaterMode.STANDARD_ELECTRIC,
                "ECO": ErdWaterHeaterMode.HEAT_PUMP,
                "VACATION": ErdWaterHeaterMode.VACATION
            }
            normalized = value.upper()
            if normalized in haier_mapping:
                return haier_mapping[normalized]
        
        # Try standard mapping
        enum_val = value.upper().replace(" ", "_")
        try:
            return ErdWaterHeaterMode[enum_val]
        except:
            _LOGGER.warning(f"Could not convert heater mode from {value}")
            return ErdWaterHeaterMode.UNKNOWN
    
    def to_option_string(self, value: ErdWaterHeaterMode) -> Optional[str]:
        """Convert from ErdWaterHeaterMode to display string."""
        try:
            if value is not None:
                return self._get_mode_name(value)
        except:
            pass
        return self._get_mode_name(ErdWaterHeaterMode.UNKNOWN)
