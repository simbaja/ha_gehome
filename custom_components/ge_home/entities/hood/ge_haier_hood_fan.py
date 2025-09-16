import logging
from typing import List, Any, Optional

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter
from ...erd.haier_hood_codes import HaierHoodFanSpeed, ERD_HAIER_HOOD_FAN_SPEED

_LOGGER = logging.getLogger(__name__)


class HaierFanOptionsConverter(OptionsConverter):
    def __init__(self):
        super().__init__()
        # All options included; if future appliances restrict availability, add filtering here.
        self.excluded = []

    @property
    def options(self) -> List[str]:
        return [i.stringify() for i in HaierHoodFanSpeed if i not in self.excluded]

    def from_option_string(self, value: str) -> Any:
        try:
            return HaierHoodFanSpeed[value.upper()]
        except Exception as e:
            _LOGGER.warning(f"Could not set Haier hood fan speed to {value.upper()}: {e}")
            return HaierHoodFanSpeed.OFF

    def to_option_string(self, value: HaierHoodFanSpeed) -> Optional[str]:
        try:
            if value is not None:
                return value.stringify()
        except Exception:
            pass
        return HaierHoodFanSpeed.OFF.stringify()


class GeHaierHoodFan(GeErdSelect):
    """Select entity for Haier hood fan speed."""

    def __init__(self, api: ApplianceApi):
        super().__init__(api, ERD_HAIER_HOOD_FAN_SPEED, HaierFanOptionsConverter())
