"""Brew strength select for Cafe Speciality Grind and Brew (ERD 0x9051).

The Grind and Brew uses a 12-byte adhoc brew settings format at ERD 0x9051,
completely different from the standard coffee maker's 3-byte format at 0x900b.
This entity reads/writes the brew strength byte (position 4, 0-based) within
that 12-byte structure.

Brew strength values:
  0 = Light
  1 = Medium
  2 = Bold
  3 = Gold

Inherits from GeErdSelect so the HA select platform picks it up.
Uses a no-op OptionsConverter and overrides properties to read from
the shared 12-byte ERD directly.
"""

import logging
from typing import List, Any, Optional

from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from ..common.ge_erd_select import GeErdSelect
from ..common.options_converter import OptionsConverter
from .ge_ccm_cached_value import GeCcmCachedValue

_LOGGER = logging.getLogger(__name__)

ERD_CCM_GRIND_BREW_SETTINGS = "0x9051"

STRENGTH_NAMES = ["Light", "Medium", "Bold", "Gold"]


class _BrewStrengthConverter(OptionsConverter):
    """Trivial converter — the select class handles byte-level logic itself."""

    @property
    def options(self) -> List[str]:
        return STRENGTH_NAMES

    def from_option_string(self, value: str) -> Any:
        return value

    def to_option_string(self, value: Any) -> Optional[str]:
        return value


class GeCcmGrindBrewStrengthSelect(GeErdSelect, GeCcmCachedValue):
    """Select for brew strength on the Grind and Brew (byte [4] of 0x9051)."""

    def __init__(self, api: ApplianceApi):
        GeErdSelect.__init__(
            self,
            api=api,
            erd_code=ERD_CCM_GRIND_BREW_SETTINGS,
            converter=_BrewStrengthConverter(),
            erd_override="Brew Strength",
            icon_override="mdi:coffee",
            entity_category=EntityCategory.CONFIG,
        )
        GeCcmCachedValue.__init__(self)

    @property
    def options(self) -> List[str]:
        return STRENGTH_NAMES

    @property
    def current_option(self) -> str | None:  # type: ignore
        try:
            raw = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if not isinstance(raw, (bytes, bytearray)) or len(raw) < 5:
            return None
        idx = raw[4]
        device_value = STRENGTH_NAMES[idx] if 0 <= idx < len(STRENGTH_NAMES) else None
        return self.get_value(device_value=device_value)

    async def async_select_option(self, option: str) -> None:
        # Cache locally — the actual write to 0x9051 happens when the
        # "Start Brewing" button is pressed.
        GeCcmCachedValue.set_value(self, option)
        self.schedule_update_ha_state()

    @property
    def brew_strength_index(self) -> int:
        """Return the numeric strength index for assembling brew settings."""
        option = self.current_option
        if option and option in STRENGTH_NAMES:
            return STRENGTH_NAMES.index(option)
        return 1  # default Medium

    @property
    def unique_id(self) -> str | None:  # type: ignore
        base = super().unique_id
        return f"{base}_strength" if base else None
