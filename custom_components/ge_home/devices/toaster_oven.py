from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdApplianceType, ErdCode

from .base import ApplianceApi
from ..entities import (
    GeToasterOvenLight,
    GeErdSensor,
    GeErdBinarySensor,
    GeErdPropertySensor,
    GeToasterOven,
    GeToasterOvenCrispFinishSensor,
)

class ToasterOvenApi(ApplianceApi):
    """API class for toaster oven objects."""

    APPLIANCE_TYPE = ErdApplianceType.TOASTER_OVEN

    def get_all_entities(self) -> List[Entity]:
        entities = super().get_all_entities()
        entities.extend(
            [
                GeToasterOvenLight(self, ErdCode.TOASTER_OVEN_LIGHT, control_erd_code=ErdCode.TOASTER_OVEN_LIGHT_CONTROL),
                GeToasterOven(self),
                GeErdPropertySensor(self, ErdCode.TOASTER_OVEN_COOK_SETTING, "cook_mode", erd_override="toaster_oven_cook_mode", icon_override="mdi:toaster-oven", entity_category=EntityCategory.DIAGNOSTIC),
                GeToasterOvenCrispFinishSensor(self),
                GeErdBinarySensor(self, ErdCode.TOASTER_OVEN_CONVECTION, erd_override="toaster_oven_convection", icon_on_override="mdi:fan", entity_category=EntityCategory.DIAGNOSTIC),
                GeErdSensor(self, ErdCode.TOASTER_OVEN_CURRENT_STATE, erd_override="toaster_oven_current_state", icon_override="mdi:toaster-oven", entity_category=EntityCategory.DIAGNOSTIC),
                GeErdBinarySensor(self, ErdCode.UPPER_OVEN_REMOTE_ENABLED, erd_override="toaster_oven_remote_enabled", icon_on_override="mdi:toaster-oven", entity_category=EntityCategory.DIAGNOSTIC),
                GeErdSensor(self, ErdCode.TOASTER_OVEN_COOK_TIME_REMAINING, suggested_uom="h"),
            ]
        )
        return entities
