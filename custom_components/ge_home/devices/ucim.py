import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType

from .base import ApplianceApi
from ..entities import (
    OimLightLevelOptionsConverter, 
    GeErdSensor, 
    GeErdBinarySensor,
    GeErdSelect,
    GeErdSwitch, 
    ErdOnOffBoolConverter
)

_LOGGER = logging.getLogger(__name__)


class UcimApi(ApplianceApi):
    """API class for Under Counter Ice Maker objects"""
    APPLIANCE_TYPE = ErdApplianceType.OPAL_ICE_MAKER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        oim_entities = [
            GeErdSensor(self, ErdCode.OIM_STATUS, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.OIM_FILTER_STATUS, device_class_override="problem", entity_category=EntityCategory.DIAGNOSTIC),            
            GeErdBinarySensor(self, ErdCode.OIM_NEEDS_DESCALING, device_class_override="problem", entity_category=EntityCategory.DIAGNOSTIC),            
            GeErdSelect(self, ErdCode.OIM_LIGHT_LEVEL, OimLightLevelOptionsConverter(), entity_category=EntityCategory.CONFIG),
            GeErdSwitch(self, ErdCode.OIM_POWER, bool_converter=ErdOnOffBoolConverter(), icon_on_override="mdi:power-on", icon_off_override="mdi:power-off"),
            GeErdSensor(self, ErdCode.OIM_PRODUCTION, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.UCIM_CLEAN_STATUS, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.UCIM_FILTER_PERCENTAGE_USED, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.UCIM_BIN_FULL, device_class_override="problem", entity_category=EntityCategory.DIAGNOSTIC),
        ]

        entities = base_entities + oim_entities
        return entities
        
