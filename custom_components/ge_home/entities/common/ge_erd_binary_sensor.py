from propcache.api import cached_property
from typing import Optional

from homeassistant.const import EntityCategory
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from gehomesdk import ErdCodeType, ErdCodeClass

from ...devices import ApplianceApi
from .ge_erd_entity import GeErdEntity


class GeErdBinarySensor(GeErdEntity, BinarySensorEntity):
    """GE Entity for binary sensors"""

    def __init__(
            self, 
            api: ApplianceApi, 
            erd_code: ErdCodeType, 
            erd_override: Optional[str] = None, 
            icon_on_override: Optional[str] = None, 
            icon_off_override: Optional[str] = None, 
            device_class_override: Optional[str] = None,
            entity_category: Optional[EntityCategory] = None
        ):
        super().__init__(api, erd_code, erd_override, icon_on_override, device_class_override, entity_category)
        self._icon_on_override = icon_on_override
        self._icon_off_override = icon_off_override

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available

    @property
    def is_on(self) -> bool | None: # type: ignore
        """Return True if entity is on."""
        return self._boolify(self.appliance.get_erd_value(self.erd_code))
    
    @cached_property
    def device_class(self) -> BinarySensorDeviceClass | None:
        # Use GeEntity’s logic, but adapt to HA’s BinarySensorDeviceClass expectations
        dc = super(GeErdEntity, self).device_class  # call GeEntity version

        if isinstance(dc, str):
            try:
                return BinarySensorDeviceClass(dc)
            except ValueError:
                return None

        return dc

    def _get_icon(self):
        if self._icon_on_override and self.is_on:
            return self._icon_on_override
        if self._icon_off_override and not self.is_on:
            return self._icon_off_override

        if self._erd_code_class == ErdCodeClass.DOOR or self.device_class == "door":
            return "mdi:door-open" if self.is_on else "mdi:door-closed"

        return super()._get_icon()

    def _get_device_class(self) -> Optional[str]:
        if self._device_class_override:
            return self._device_class_override
        if self._erd_code_class == ErdCodeClass.DOOR:
            return "door"
        return None
