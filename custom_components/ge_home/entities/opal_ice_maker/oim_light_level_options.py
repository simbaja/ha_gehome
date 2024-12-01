import logging
from typing import List, Any, Optional

from gehomesdk import ErdCodeType, ErdOimLightLevel, ErdCode
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

_LOGGER = logging.getLogger(__name__)

class OimLightLevelOptionsConverter(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in ErdOimLightLevel]
    def from_option_string(self, value: str) -> Any:
        try:
            return ErdOimLightLevel[value.upper()]
        except:
            _LOGGER.warning(f"Could not set hood light level to {value.upper()}")
            return ErdOimLightLevel.OFF
    def to_option_string(self, value: ErdOimLightLevel) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except:
            pass
        return ErdOimLightLevel.OFF.stringify()
