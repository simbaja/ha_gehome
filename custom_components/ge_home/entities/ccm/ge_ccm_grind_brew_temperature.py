"""Brew temperature number for Cafe Speciality Grind and Brew (ERD 0x9051).

The Grind and Brew uses a 12-byte adhoc brew settings format at ERD 0x9051.
This entity reads/writes the temperature byte (position 5, 0-based) within
that 12-byte structure.

Temperature values (Fahrenheit): 185, 190, 195, 200, 205

Inherits from GeErdNumber so the HA number platform picks it up.
"""

import logging
from typing import Optional

from homeassistant.components.number import NumberMode
from homeassistant.const import UnitOfTemperature, EntityCategory

from ...devices import ApplianceApi
from ..common.ge_erd_number import GeErdNumber
from .ge_ccm_cached_value import GeCcmCachedValue

_LOGGER = logging.getLogger(__name__)

ERD_CCM_GRIND_BREW_SETTINGS = "0x9051"

MIN_TEMP = 185
MAX_TEMP = 205


class GeCcmGrindBrewTemperatureNumber(GeErdNumber, GeCcmCachedValue):
    """Number entity for brew temperature on the Grind and Brew (byte [5] of 0x9051)."""

    def __init__(self, api: ApplianceApi):
        GeErdNumber.__init__(
            self,
            api=api,
            erd_code=ERD_CCM_GRIND_BREW_SETTINGS,
            erd_override="Brew Temperature",
            icon_override="mdi:thermometer",
            min_value=MIN_TEMP,
            max_value=MAX_TEMP,
            step_value=5,
            mode=NumberMode.SLIDER,
            uom_override=UnitOfTemperature.FAHRENHEIT,
            entity_category=EntityCategory.CONFIG,
        )
        GeCcmCachedValue.__init__(self)

    @property
    def native_value(self) -> float | None:  # type: ignore
        try:
            raw = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if not isinstance(raw, (bytes, bytearray)) or len(raw) < 6:
            return None
        device_value = float(raw[5])
        return self.get_value(device_value=device_value)

    async def async_set_native_value(self, value: float) -> None:
        GeCcmCachedValue.set_value(self, value)
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str | None:  # type: ignore
        base = super().unique_id
        return f"{base}_temperature" if base else None
