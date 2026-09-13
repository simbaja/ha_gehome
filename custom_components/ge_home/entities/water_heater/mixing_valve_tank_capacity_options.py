import logging
from typing import List, Any, Optional

from gehomesdk import ErdWaterHeaterMixingValveTankCapacity
from ..common import OptionsConverter

_LOGGER = logging.getLogger(__name__)

class MixingValveTankCapacityOptionsConverter(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [
            i.stringify()
            for i in ErdWaterHeaterMixingValveTankCapacity
            if i != ErdWaterHeaterMixingValveTankCapacity.UNKNOWN
        ]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdWaterHeaterMixingValveTankCapacity[value.upper().replace("-", "_")]
        except:
            _LOGGER.warning(f"Could not set mixing valve tank capacity to {value.upper()}")
            return ErdWaterHeaterMixingValveTankCapacity.NORMAL
    def to_option_string(self, value: ErdWaterHeaterMixingValveTankCapacity) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdWaterHeaterMixingValveTankCapacity.NORMAL.stringify()
