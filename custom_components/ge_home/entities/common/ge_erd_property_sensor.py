from propcache.api import cached_property
from typing import Optional
import magicattr

from homeassistant.const import EntityCategory
from gehomesdk import ErdCodeType, ErdDataType

from ...devices import ApplianceApi
from .ge_erd_sensor import GeErdSensor


class GeErdPropertySensor(GeErdSensor):
    """GE Entity for sensors"""
    def __init__(   
        self, 
        api: ApplianceApi, 
        erd_code: ErdCodeType, 
        erd_property: str, 
        erd_override: Optional[str] = None, 
        icon_override: Optional[str] = None, 
        device_class_override: Optional[str] = None, 
        state_class_override: Optional[str] = None, 
        uom_override: Optional[str] = None, 
        data_type_override: Optional[ErdDataType] = None,
        entity_category: Optional[EntityCategory] = None
    ):
        super().__init__(
            api, 
            erd_code, 
            erd_override=erd_override, 
            icon_override=icon_override, 
            device_class_override=device_class_override, 
            state_class_override=state_class_override,
            uom_override=uom_override,
            data_type_override=data_type_override,
            entity_category=entity_category
        )
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
    def native_value(self) -> str | float | int | None: # type: ignore
        try:
            value = magicattr.get(self.appliance.get_erd_value(self.erd_code), self.erd_property)

            # if it's a numeric data type, return it directly
            if self._data_type in [ErdDataType.INT, ErdDataType.FLOAT]:
                return value

            # otherwise, return a stringified version
            # TODO: perhaps enhance so that there's a list of variables available
            #       for the stringify function to consume...
            return self._stringify(value, temp_units=self._temp_units)
        except KeyError:
            return None