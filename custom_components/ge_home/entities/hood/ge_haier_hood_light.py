import logging
from typing import List, Any, Optional

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter
from ...erd.haier_hood_codes import HaierHoodLightLevel, ERD_HAIER_HOOD_LIGHT_LEVEL

_LOGGER = logging.getLogger(__name__)


class HaierLightOptionsConverter(OptionsConverter):
    def __init__(self):
        super().__init__()
        self.excluded = []

    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in HaierHoodLightLevel if i not in self.excluded]

    def from_option_string(self, value: str) -> Any:
        try:
            return HaierHoodLightLevel[value.upper()]
        except Exception as e:
            _LOGGER.warning(f"Could not set Haier hood light level to {value.upper()}: {e}")
            return HaierHoodLightLevel.OFF

    def to_option_string(self, value: HaierHoodLightLevel) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except Exception:
            pass
        return HaierHoodLightLevel.OFF.stringify()


class GeHaierHoodLight(GeErdSelect):
    """Select entity for Haier hood light level."""

    def __init__(self, api: ApplianceApi):
        super().__init__(api, ERD_HAIER_HOOD_LIGHT_LEVEL, HaierLightOptionsConverter())
