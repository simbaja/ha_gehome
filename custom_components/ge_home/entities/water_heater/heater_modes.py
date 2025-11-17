import logging
from typing import List, Any, Optional

from gehomesdk import ErdWaterHeaterMode

from ..common import OptionsConverter

_LOGGER = logging.getLogger(__name__)

class WhHeaterModeConverter(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [
            s
            for i in ErdWaterHeaterMode
            for s in [i.stringify()]
            if s is not None
        ]
    
    def from_option_string(self, value: str) -> Any:
        enum_val = value.upper().replace(" ","_")
        try:
            return ErdWaterHeaterMode[enum_val]
        except:
            _LOGGER.warning(f"Could not heater mode to {enum_val}")
            return ErdWaterHeaterMode.UNKNOWN
        
    def to_option_string(self, value: ErdWaterHeaterMode) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdWaterHeaterMode.UNKNOWN.stringify()
