"""Brew start button for Cafe Speciality Grind and Brew.

Pressing this button assembles the 12-byte adhoc brew settings payload
from the strength/temperature/cups entities and writes it to ERD 0x9051,
which kicks off a brew on the Grind and Brew model.

Inherits from GeErdButton so the HA button platform picks it up.

Byte layout for 0x9051 (from issue #251):
  [0]  = Gold toggle
  [1]  = Bloom toggle
  [2]  = always 0x00
  [3]  = Single toggle
  [4]  = Brew Strength (0=light, 1=medium, 2=bold, 3=gold)
  [5]  = Temperature (185-205)
  [6]  = Ounces (6-24)
  [7]  = Cups (4-10)
  [8]  = always 0x00
  [9]  = always 0x00
  [10] = always 0x00
  [11] = Bloom time (5-30)

For now, bytes we don't have UI controls for are preserved from the
current device value so we don't clobber settings like gold/bloom toggles.
"""

import logging

from homeassistant.const import EntityCategory

from ...devices import ApplianceApi
from ..common.ge_erd_button import GeErdButton

_LOGGER = logging.getLogger(__name__)

ERD_CCM_GRIND_BREW_SETTINGS = "0x9051"


class GeCcmGrindBrewStartButton(GeErdButton):
    """Button to start a brew on the Grind and Brew by writing 0x9051."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            erd_code=ERD_CCM_GRIND_BREW_SETTINGS,
            erd_override="Start Brewing",
            entity_category=None,
        )

    async def async_press(self) -> None:
        """Handle the button press — assemble settings and write to 0x9051."""
        from ...devices import CcmApi

        if not isinstance(self.api, CcmApi):
            _LOGGER.warning("Start Brewing button pressed but API is not CcmApi")
            return

        await self.api.start_brewing()

    @property
    def unique_id(self) -> str | None:  # type: ignore
        base = super().unique_id
        return f"{base}_start_brew" if base else None
