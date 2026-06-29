import logging
from typing import Optional, Any
from propcache.api import cached_property

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature
)
from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from .ge_erd_entity import GeErdEntity

_LOGGER = logging.getLogger(__name__)

class GeErdFan(GeErdEntity, FanEntity):
    """Fans for ERD codes."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, erd_override: Optional[str] = None, entity_category: Optional[EntityCategory] = None):
        super().__init__(api, erd_code, erd_override, entity_category=entity_category)

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available

    @property
    def supported_features(self) -> FanEntityFeature: # type: ignore
        return FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    @property
    def is_on(self) -> bool: # type: ignore
        """Return True if fan is on."""
        try:
            val: Any = self.appliance.get_erd_value(self.erd_code)
            return bool(val > 0) if val is not None else False
        except (KeyError, TypeError):
            return False

    @property
    def percentage(self) -> int: # type: ignore
        """Return the current speed percentage."""
        try:
            val: Any = self.appliance.get_erd_value(self.erd_code)
            return int(val) if val is not None else 0
        except (KeyError, ValueError, TypeError):
            return 0

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        """Turn the fan on."""
        if percentage is None:
            percentage = self.percentage or 100
        await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self.async_set_percentage(0)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        await self.appliance.async_set_erd_value(self.erd_code, percentage)
