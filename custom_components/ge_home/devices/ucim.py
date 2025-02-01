import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdApplianceType,
    ErdOnOff
)

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
    """API class for Opal Ice Maker objects"""
    APPLIANCE_TYPE = ErdApplianceType.OPAL_ICE_MAKER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        oim_entities = [
            GeErdSensor(self, ErdCode.OIM_STATUS),
            GeErdBinarySensor(self, ErdCode.OIM_FILTER_STATUS, device_class_override="problem"),            
            GeErdBinarySensor(self, ErdCode.OIM_NEEDS_DESCALING, device_class_override="problem"),            
            GeErdSelect(self, ErdCode.OIM_LIGHT_LEVEL, OimLightLevelOptionsConverter()),
            GeErdSwitch(self, ErdCode.OIM_POWER, bool_converter=ErdOnOffBoolConverter(), icon_on_override="mdi:power-on", icon_off_override="mdi:power-off"),
            GeErdSensor(self, ErdCode.OIM_PRODUCTION),
            GeErdSensor(self, ErdCode.UCIM_CLEAN_STATUS),
            GeErdSensor(self, ErdCode.UCIM_FILTER_USED_PERCENTAGE),
            GeErdBinarySensor(self, ErdCode.UCIM_BIN_FULL, device_class_override="problem"),
        ]

        entities = base_entities + oim_entities
        return entities
        
