from propcache.api import cached_property
from typing import Optional

import magicattr
from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from .ge_erd_binary_sensor import GeErdBinarySensor

class GeErdPropertyBinarySensor(GeErdBinarySensor):
    """GE Entity for property binary sensors"""
    def __init__(
            self, 
            api: ApplianceApi, 
            erd_code: ErdCodeType, 
            erd_property: str, erd_override: Optional[str] = None, 
            icon_on_override: Optional[str] = None, 
            icon_off_override: Optional[str] = None, 
            device_class_override: Optional[str] = None,
            entity_category: Optional[EntityCategory] = None
        ):
        super().__init__(api, erd_code, erd_override, icon_on_override, icon_off_override, device_class_override, entity_category)
        self.erd_property = erd_property
        self._erd_property_cleansed = erd_property.replace(".","_").replace("[","_").replace("]","_")

    @cached_property
    def unique_id(self) -> Optional[str]:
        return f"{super().unique_id}_{self._erd_property_cleansed}"

    @cached_property
    def name(self) -> Optional[str]:
        base_string = super().name
        property_name = self._erd_property_cleansed.replace("_", " ").title()
        return f"{base_string} {property_name}"
    
    @property
    def is_on(self) -> Optional[bool]:
        """Return True if entity is on."""
        try:
            value = magicattr.get(self.appliance.get_erd_value(self.erd_code), self.erd_property)
        except KeyError:
            return None
        return self._boolify(value)