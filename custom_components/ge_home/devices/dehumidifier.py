import logging
from typing import List

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdApplianceType
)

from .base import ApplianceApi
from ..entities import (
    GeErdSensor, 
    GeErdPropertyBinarySensor,
    GeErdSwitch, 
    ErdOnOffBoolConverter,
    GeDehumidifierFanSpeedSensor,
    GeDehumidifier
)

_LOGGER = logging.getLogger(__name__)


class DehumidifierApi(ApplianceApi):
    """API class for Dehumidifier objects"""
    APPLIANCE_TYPE = ErdApplianceType.DEHUMIDIFIER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        dhum_entities = [
            GeErdSwitch(self, ErdCode.AC_POWER_STATUS, bool_converter=ErdOnOffBoolConverter(), icon_on_override="mdi:power-on", icon_off_override="mdi:power-off"),
            GeDehumidifierFanSpeedSensor(self, ErdCode.AC_FAN_SETTING, icon_override="mdi:fan"),
            GeErdSensor(self, ErdCode.DHUM_CURRENT_HUMIDITY, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.DHUM_TARGET_HUMIDITY, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.DHUM_MAINTENANCE, "empty_bucket", device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.DHUM_MAINTENANCE, "clean_filter", device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
            GeDehumidifier(self)
        ]

        entities = base_entities + dhum_entities
        return entities
        
