from propcache.api import cached_property
from typing import Optional

from homeassistant.const import EntityCategory
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass

from gehomesdk import ErdCodeType
from ...devices import ApplianceApi
from .ge_erd_entity import GeErdEntity


class GeErdButton(GeErdEntity, ButtonEntity):
    """GE Entity for buttons"""
        
    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, erd_override: Optional[str] = None, entity_category: Optional[EntityCategory] = None):
        super().__init__(api, erd_code, erd_override=erd_override, entity_category=entity_category)

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available
        
    @cached_property
    def device_class(self) -> ButtonDeviceClass | None:
        # Use GeEntity’s logic, but adapt to HA’s ButtonDeviceClass expectations
        dc = super(GeErdEntity, self).device_class  # call GeEntity version

        if isinstance(dc, str):
            try:
                return ButtonDeviceClass(dc)
            except ValueError:
                return None

        return dc

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.appliance.async_set_erd_value(self.erd_code, True)
