import logging
from typing import List

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdApplianceType,
    ErdDataType,
    ErdHoodFanSpeedAvailability,
    ErdHoodLightLevelAvailability
)

from .base import ApplianceApi
from ..entities import (
    GeErdSensor,
    GeHoodLightLevelSelect, 
    GeHoodFanSpeedSelect, 
    GeErdPropertySensor,
    GeErdPropertyBinarySensor,
    GeErdBinarySensor,
    GeErdTimerSensor,
    GeErdTimerNumber
)

_LOGGER = logging.getLogger(__name__)


class MicrowaveApi(ApplianceApi):
    """API class for Microwave objects"""
    APPLIANCE_TYPE = ErdApplianceType.MICROWAVE

    @property
    def sw_version(self) -> str:
        appVer = self.try_get_erd_value(ErdCode.APPLIANCE_SW_VERSION)
        if appVer == "0.0.0.0":
            appVer = self.try_get_erd_value(ErdCode.LCD_SW_VERSION) or appVer
        wifiVer = self.try_get_erd_value(ErdCode.WIFI_MODULE_SW_VERSION)

        return 'Appliance=' + str(appVer or 'Unknown') + '/Wifi=' + str(wifiVer or 'Unknown')

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        #get the availabilities
        fan_availability: ErdHoodFanSpeedAvailability | None = self.try_get_erd_value(ErdCode.HOOD_FAN_SPEED_AVAILABILITY)
        light_availability: ErdHoodLightLevelAvailability | None = self.try_get_erd_value(ErdCode.HOOD_LIGHT_LEVEL_AVAILABILITY)

        mwave_entities: List[Entity] = [
            GeErdBinarySensor(self, ErdCode.MICROWAVE_REMOTE_ENABLE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.MICROWAVE_STATE, "status", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.MICROWAVE_STATE, "door_status", device_class_override=BinarySensorDeviceClass.DOOR, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.MICROWAVE_STATE, "cook_mode", icon_override="mdi:food-turkey", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.MICROWAVE_STATE, "power_level", icon_override="mdi:gauge", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.MICROWAVE_STATE, "temperature", icon_override="mdi:thermometer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdTimerSensor(self, ErdCode.MICROWAVE_COOK_TIMER, suggested_uom="min"),
            GeErdTimerSensor(self, ErdCode.MICROWAVE_KITCHEN_TIMER, suggested_uom="h"),
            GeErdTimerNumber(self, ErdCode.MICROWAVE_KITCHEN_TIMER, max_value=255),
        ]

        if fan_availability and fan_availability.is_available:
            mwave_entities.append(GeHoodFanSpeedSelect(self, ErdCode.HOOD_FAN_SPEED))
        #for now, represent as a select
        if light_availability and light_availability.is_available:
            mwave_entities.append(GeHoodLightLevelSelect(self, ErdCode.HOOD_LIGHT_LEVEL))

        # Newer built-in microwaves / speed ovens (e.g. PWB7030) report as
        # ErdApplianceType.MICROWAVE but publish the Advantium ERD set instead
        # of MICROWAVE_STATE.  build_entities_list drops whatever the appliance
        # doesn't report, so these are no-ops on classic microwaves.
        # Read-only: no GeAdvantium control entity (remote start is untested).
        # Deliberately not exposed, because the PWB7030 firmware doesn't keep
        # them current: door, cooling fan, preheat status (ADVANTIUM_COOK_STATUS),
        # UPPER_OVEN_DISPLAY_TEMPERATURE and ADVANTIUM_KITCHEN_TIME_REMAINING.
        mwave_entities += [
            GeErdBinarySensor(self, ErdCode.UPPER_OVEN_REMOTE_ENABLED, "Microwave Oven Remote Enabled", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.ADVANTIUM_COOK_TIME_REMAINING, "Microwave Cook Time Remaining", suggested_uom="min"),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "cook_action", erd_override="microwave", icon_override="mdi:play-pause", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "cook_mode", erd_override="microwave", icon_override="mdi:microwave", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "termination_reason", erd_override="microwave", icon_override="mdi:information-outline", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "temperature", erd_override="microwave", icon_override="mdi:thermometer", data_type_override=ErdDataType.INT, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "power_level", erd_override="microwave", icon_override="mdi:gauge", data_type_override=ErdDataType.INT, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "warm_status", erd_override="microwave", icon_override="mdi:radiator", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "sensing_active", erd_override="microwave", icon_on_override="mdi:flash-auto", icon_off_override="mdi:flash-off", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "oven_light_status", erd_override="microwave", icon_on_override="mdi:lightbulb-on", icon_off_override="mdi:lightbulb-off", entity_category=EntityCategory.DIAGNOSTIC),
        ]

        entities = base_entities + mwave_entities
        return entities
        
