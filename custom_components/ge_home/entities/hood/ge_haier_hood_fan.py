import logging
from typing import List, Any, Optional

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

from ...erd.haier_hood_codes import (
    HaierHoodFanSpeed,
    ERD_HAIER_HOOD_FAN_SPEED,
)

_LOGGER = logging.getLogger(__name__)


class _HaierFanOptions(OptionsConverter):
    """Presents Haier fan choices as select options."""

    @property
    def options(self) -> List[str]:
        return [
            HaierHoodFanSpeed.OFF.stringify(),
            HaierHoodFanSpeed.LOW.stringify(),
            HaierHoodFanSpeed.MEDIUM.stringify(),
            HaierHoodFanSpeed.HIGH.stringify(),
            HaierHoodFanSpeed.BOOST.stringify(),
        ]

    def from_option_string(self, value: str) -> Any:
        v = (value or "").strip().lower()
        mapping = {
            "off": HaierHoodFanSpeed.OFF,
            "low": HaierHoodFanSpeed.LOW,
            "medium": HaierHoodFanSpeed.MEDIUM,
            "high": HaierHoodFanSpeed.HIGH,
            "boost": HaierHoodFanSpeed.BOOST,
        }
        if v in mapping:
            return mapping[v]
        _LOGGER.warning("Unknown Haier fan option %r; defaulting to Off", value)
        return HaierHoodFanSpeed.OFF

    def to_option_string(self, value: Optional[HaierHoodFanSpeed]) -> Optional[str]:
        if value is None:
            return None
        return value.stringify()


class GeHaierHoodFan(GeErdSelect):
    """Select entity for Haier hood fan speed."""
    def __init__(self, api: ApplianceApi):
        super().__init__(api, ERD_HAIER_HOOD_FAN_SPEED, _HaierFanOptions())
