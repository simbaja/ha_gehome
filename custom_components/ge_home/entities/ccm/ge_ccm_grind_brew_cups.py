"""Brew cups number for Cafe Speciality Grind and Brew (ERD 0x9051).

The Grind and Brew uses a 12-byte adhoc brew settings format at ERD 0x9051.
This entity reads/writes the cups byte (position 7, 0-based) within
that 12-byte structure.

Cups values: 4-10

Inherits from GeErdNumber so the HA number platform picks it up.
"""

import logging
from typing import Optional

from homeassistant.components.number import NumberMode
from homeassistant.const import EntityCategory

from ...devices import ApplianceApi
from ..common.ge_erd_number import GeErdNumber
from .ge_ccm_cached_value import GeCcmCachedValue

_LOGGER = logging.getLogger(__name__)

ERD_CCM_GRIND_BREW_SETTINGS = "0x9051"

MIN_CUPS = 4
MAX_CUPS = 10


class GeCcmGrindBrewCupsNumber(GeErdNumber, GeCcmCachedValue):
    """Number entity for brew cups on the Grind and Brew (byte [7] of 0x9051)."""

    def __init__(self, api: ApplianceApi):
        GeErdNumber.__init__(
            self,
            api=api,
            erd_code=ERD_CCM_GRIND_BREW_SETTINGS,
            erd_override="Brew Cups",
            icon_override="mdi:coffee-outline",
            min_value=MIN_CUPS,
            max_value=MAX_CUPS,
            step_value=1,
            mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG,
        )
        GeCcmCachedValue.__init__(self)

    @property
    def native_value(self) -> float | None:  # type: ignore
        try:
            raw = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if not isinstance(raw, (bytes, bytearray)) or len(raw) < 8:
            return None
        device_value = float(raw[7])
        return self.get_value(device_value=device_value)

    async def async_set_native_value(self, value: float) -> None:
        GeCcmCachedValue.set_value(self, value)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str | None:  # type: ignore
        base = super().unique_id
        return f"{base}_cups" if base else None
