"""Grinder on/off switch for Cafe Speciality Grind and Brew (ERD 0x9053).

Raw byte values:
  b'\\x00' = Grind On  (switch ON)
  b'\\x01' = Grind Off (switch OFF)

The ERD code 0x9053 is not registered in the gehomesdk, so the SDK decodes
it as raw bytes and cannot encode values for it.  This class bypasses the
SDK encoder by sending the raw hex string directly to the websocket client.
"""

import logging
from typing import Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory

from ...devices import ApplianceApi
from ..common.ge_erd_entity import GeErdEntity

_LOGGER = logging.getLogger(__name__)

ERD_CCM_GRINDER_SETTING = "0x9053"


class GeCcmGrinderSwitch(GeErdEntity, SwitchEntity):
    """Switch to enable/disable the grinder on Grind and Brew models."""

    def __init__(self, api: ApplianceApi):
        super().__init__(
            api,
            erd_code=ERD_CCM_GRINDER_SETTING,
            erd_override="Grinder",
            icon_override="mdi:coffee-grinder",
            entity_category=EntityCategory.CONFIG,
        )
        self._icon_on = "mdi:coffee-grinder"
        self._icon_off = "mdi:coffee-grinder-outline"

    @property
    def is_on(self) -> bool | None:  # type: ignore
        """Return True if the grinder is enabled (Grind On)."""
        try:
            value = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if isinstance(value, (bytes, bytearray)):
            return value == b"\x00"
        return None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the grinder on (send '00')."""
        _LOGGER.debug("Turning grinder on for %s", self.unique_id)
        await self.appliance.client.async_set_erd_value(
            self.appliance, self.erd_code, "00"
        )

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the grinder off (send '01')."""
        _LOGGER.debug("Turning grinder off for %s", self.unique_id)
        await self.appliance.client.async_set_erd_value(
            self.appliance, self.erd_code, "01"
        )

    def _get_icon(self) -> Optional[str]:
        if self.is_on and self._icon_on:
            return self._icon_on
        if not self.is_on and self._icon_off:
            return self._icon_off
        return super()._get_icon()
