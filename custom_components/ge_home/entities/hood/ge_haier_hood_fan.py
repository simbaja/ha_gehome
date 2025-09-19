from __future__ import annotations
import logging
from typing import List, Any, Optional

from ...devices import ApplianceApi
from ..common import GeErdSelect, OptionsConverter

from ...erd.haier_hood_codes import (
    HaierHoodFanSpeed,
    ERD_HAIER_HOOD_FAN_SPEED,
)
from ...erd.haier_hood_converters import HaierHoodFanSpeedConverter
from ...erd.registry_compat import ensure_converters_on_appliance

_LOGGER = logging.getLogger(__name__)

class _HaierFanOptions(OptionsConverter):
    @property
    def options(self) -> List[str]:
        return [m.stringify() for m in HaierHoodFanSpeed]

    def from_option_string(self, value: str) -> Any:
        v = (value or "").strip().lower()
        for m in HaierHoodFanSpeed:
            if m.stringify().lower() == v or m.name.lower() == v:
                return m
        _LOGGER.warning("Unknown Haier fan option %r; defaulting to Off", value)
        return HaierHoodFanSpeed.OFF

    # Tolerate raw bytes when the SDK hasn’t decoded yet
    def to_option_string(self, value: Optional[Any]) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            try:
                value = HaierHoodFanSpeed(int(value[0]))
            except Exception:
                return None
        if isinstance(value, HaierHoodFanSpeed):
            return value.stringify()
        try:
            return HaierHoodFanSpeed(int(value)).stringify()
        except Exception:
            return None


class GeHaierHoodFan(GeErdSelect):
    """Select entity for Haier hood fan speed."""
    def __init__(self, api: ApplianceApi):
        # Ensure converters exist on this appliance even if the global registry is missing.
        ensure_converters_on_appliance(
            api.appliance,
            ERD_HAIER_HOOD_FAN_SPEED,
            None,  # not used here
            HaierHoodFanSpeedConverter(),
            None
        )
        super().__init__(api, ERD_HAIER_HOOD_FAN_SPEED, _HaierFanOptions())
