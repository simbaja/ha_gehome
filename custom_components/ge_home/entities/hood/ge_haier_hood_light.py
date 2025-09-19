import logging
from typing import List, Any, Optional, Union

from gehomesdk import ErdCodeType
from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter
from ...erd.haier_hood_codes import (
    HaierHoodLightLevel,
    ERD_HAIER_HOOD_LIGHT_LEVEL,
)
from ...erd.haier_hood_converters import HaierHoodLightLevelConverter

_LOGGER = logging.getLogger(__name__)

_converter = HaierHoodLightLevelConverter()

class _LightOptions(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in HaierHoodLightLevel]

    def from_option_string(self, value: str) -> Any:
        try:
            return _converter.erd_encode(HaierHoodLightLevel[value.upper()])
        except Exception:
            _LOGGER.warning("Haier Hood: invalid light level %s, using OFF", value)
            return _converter.erd_encode(HaierHoodLightLevel.OFF)

    def to_option_string(self, value: Union[HaierHoodLightLevel, bytes, None]) -> Optional[str]:
        try:
            if isinstance(value, bytes):
                value = _converter.erd_decode(value)
            if isinstance(value, HaierHoodLightLevel):
                return value.stringify()
        except Exception:
            pass
        return HaierHoodLightLevel.OFF.stringify()


class GeHaierHoodLight(GeErdSelect):
    """Select for Haier/F&P hood light level (0x5B15)."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType = ERD_HAIER_HOOD_LIGHT_LEVEL):
        super().__init__(api, erd_code, _LightOptions())
