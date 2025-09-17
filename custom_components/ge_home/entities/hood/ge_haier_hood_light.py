import logging
from typing import List, Any, Optional

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

from ...erd.haier_hood_codes import (
    HaierHoodLightLevel,
    ERD_HAIER_HOOD_LIGHT_LEVEL,
)

_LOGGER = logging.getLogger(__name__)


class _HaierLightOptions(OptionsConverter):
    """Presents Haier light levels as select options."""

    @property
    def options(self) -> List[str]:
        return [
            HaierHoodLightLevel.OFF.stringify(),
            HaierHoodLightLevel.DIM.stringify(),
            HaierHoodLightLevel.HIGH.stringify(),
        ]

    def from_option_string(self, value: str) -> Any:
        v = (value or "").strip().lower()
        mapping = {
            "off": HaierHoodLightLevel.OFF,
            "dim": HaierHoodLightLevel.DIM,
            "high": HaierHoodLightLevel.HIGH,
        }
        if v in mapping:
            return mapping[v]
        _LOGGER.warning("Unknown Haier light option %r; defaulting to Off", value)
        return HaierHoodLightLevel.OFF

    def to_option_string(self, value: Optional[HaierHoodLightLevel]) -> Optional[str]:
        if value is None:
            return None
        return value.stringify()


class GeHaierHoodLight(GeErdSelect):
    """Select entity for Haier hood light."""
    def __init__(self, api: ApplianceApi):
        super().__init__(api, ERD_HAIER_HOOD_LIGHT_LEVEL, _HaierLightOptions())
