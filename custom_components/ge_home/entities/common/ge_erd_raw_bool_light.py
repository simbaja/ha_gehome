import logging
from propcache.api import cached_property
from typing import Optional

from homeassistant.components.light import LightEntity
from homeassistant.components.light.const import ColorMode
from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType

from ...const import DOMAIN
from ...devices import ApplianceApi
from .ge_erd_entity import GeErdEntity

_LOGGER = logging.getLogger(__name__)


class GeErdRawBoolLight(GeErdEntity, LightEntity):
    """On/off light backed by an unregistered raw ERD hex payload."""

    def __init__(
        self,
        api: ApplianceApi,
        erd_code: ErdCodeType,
        erd_override: Optional[str] = None,
        control_erd_code: Optional[ErdCodeType] = None,
        icon_override: Optional[str] = "mdi:lightbulb",
        entity_category: Optional[EntityCategory] = None,
    ):
        super().__init__(api, erd_code, erd_override, icon_override, entity_category=entity_category)
        self._control_erd_code = control_erd_code

    @cached_property
    def supported_color_modes(self) -> set[ColorMode]:
        return {ColorMode.ONOFF}

    @property
    def color_mode(self) -> ColorMode:  # type: ignore
        return ColorMode.ONOFF

    @property
    def is_on(self) -> bool | None:  # type: ignore
        raw = self.appliance.get_raw_erd_value(self.erd_code)
        if raw is None:
            return None
        return raw != "00"

    async def async_turn_on(self, **kwargs):
        _LOGGER.debug(f"Turning on {self.unique_id}")
        await self.appliance.client.async_set_erd_value(self.appliance, self._writeable_erd_code, "01")

    async def async_turn_off(self, **kwargs):
        _LOGGER.debug(f"Turning off {self.unique_id}")
        await self.appliance.client.async_set_erd_value(self.appliance, self._writeable_erd_code, "00")

    @cached_property
    def unique_id(self) -> str | None:
        erd_name = self._erd_override or self.erd_string.lower()
        return f"{DOMAIN}_{self.serial_or_mac}_{erd_name}"

    @property
    def _writeable_erd_code(self) -> ErdCodeType:
        return self._control_erd_code or self.erd_code
