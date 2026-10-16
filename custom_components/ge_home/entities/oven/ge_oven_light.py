"""GE Home oven light entity."""

from typing import Any

from homeassistant.components.light.const import ColorMode
from propcache.api import cached_property
from gehomesdk import ErdOvenLightLevel

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeErdLight


class GeOvenLight(GeErdLight):
    """On/off light entity for a GE oven cavity."""

    def __init__(self, api: ApplianceApi, erd_code):
        super().__init__(api, erd_code, color_mode=ColorMode.ONOFF)

    @cached_property
    def name(self) -> str | None:
        return f"{self.entity_identifier} Oven Light"

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.entity_identifier}_{self.erd_code.name.lower()}"

    @cached_property
    def supported_color_modes(self) -> set[ColorMode]:
        return {ColorMode.ONOFF}

    @property
    def brightness(self) -> int | None:
        return None

    @property
    def is_on(self) -> bool:
        value = self.appliance.get_erd_value(self.erd_code)
        return value not in (ErdOvenLightLevel.OFF, ErdOvenLightLevel.NOT_AVAILABLE)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.appliance.async_set_erd_value(self.erd_code, ErdOvenLightLevel.HIGH)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.appliance.async_set_erd_value(self.erd_code, ErdOvenLightLevel.OFF)
