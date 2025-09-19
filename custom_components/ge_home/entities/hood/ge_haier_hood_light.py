from __future__ import annotations
import logging
from typing import List, Any, Optional

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

from ...erd.haier_hood_codes import (
    HaierHoodLightLevel,
    ERD_HAIER_HOOD_LIGHT_LEVEL,
)
from ...erd.haier_hood_converters import HaierHoodLightLevelConverter
from ...erd.registry_compat import ensure_converters_on_appliance

_LOGGER = logging.getLogger(__name__)

class _HaierLightOptions(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [m.stringify() for m in HaierHoodLightLevel]

    def from_option_string(self, value: str) -> Any:
        v = (value or "").strip().lower()
        for m in HaierHoodLightLevel:
            if m.stringify().lower() == v or m.name.lower() == v:
                return m
        _LOGGER.warning("Unknown Haier light option %r; defaulting to Off", value)
        return HaierHoodLightLevel.OFF

    def to_option_string(self, value: Optional[Any]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            try:
                value = HaierHoodLightLevel(int(value[0]))
            except Exception:
                return None
        if isinstance(value, HaierHoodLightLevel):
            return value.stringify()
        try:
            return HaierHoodLightLevel(int(value)).stringify()
        except Exception:
            return None


class GeHaierHoodLight(GeErdSelect):
    """Select entity for Haier hood light."""
    def __init__(self, api: ApplianceApi):
        ensure_converters_on_appliance(
            api.appliance,
            None,
            ERD_HAIER_HOOD_LIGHT_LEVEL,
            None,
            HaierHoodLightLevelConverter()
        )
        super().__init__(api, ERD_HAIER_HOOD_LIGHT_LEVEL, _HaierLightOptions())
