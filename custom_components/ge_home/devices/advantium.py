import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk.erd import ErdCode, ErdApplianceType, ErdDataType

from .base import ApplianceApi
from ..entities import GeAdvantium, GeErdSensor, GeErdBinarySensor, GeErdPropertySensor, GeErdPropertyBinarySensor, UPPER_OVEN

_LOGGER = logging.getLogger(__name__)

class AdvantiumApi(ApplianceApi):
    """API class for Advantium objects"""
    APPLIANCE_TYPE = ErdApplianceType.ADVANTIUM

    @property
    def sw_version(self) -> str:
        appVer = self.try_get_erd_value(ErdCode.APPLIANCE_SW_VERSION)
        if appVer == "0.0.0.0":
            appVer = self.try_get_erd_value(ErdCode.LCD_SW_VERSION)
        wifiVer = self.try_get_erd_value(ErdCode.WIFI_MODULE_SW_VERSION)

        return 'Appliance=' + str(appVer or 'Unknown') + '/Wifi=' + str(wifiVer or 'Unknown')

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        advantium_entities = [
            GeErdSensor(self, ErdCode.PERSONALITY, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.UPPER_OVEN_REMOTE_ENABLED, self._single_name(ErdCode.UPPER_OVEN_REMOTE_ENABLED), entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.MICROWAVE_REMOTE_ENABLE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE, self._single_name(ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE), entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.ADVANTIUM_KITCHEN_TIME_REMAINING, suggested_uom="h"),
            GeErdSensor(self, ErdCode.ADVANTIUM_COOK_TIME_REMAINING, suggested_uom="h"),
            GeAdvantium(self),

            #Cook Status
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "cook_mode", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "termination_reason", icon_override="mdi:information-outline", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "preheat_status", icon_override="mdi:fire", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "temperature", icon_override="mdi:thermometer", data_type_override=ErdDataType.INT, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "power_level", icon_override="mdi:gauge", data_type_override=ErdDataType.INT, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "warm_status", icon_override="mdi:radiator", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "door_status", device_class_override="door", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "sensing_active", icon_on_override="mdi:flash-auto", icon_off_override="mdi:flash-off", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "cooling_fan_status", icon_on_override="mdi:fan", icon_off_override="mdi:fan-off", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.ADVANTIUM_COOK_STATUS, "oven_light_status", icon_on_override="mdi:lightbulb-on", icon_off_override="mdi:lightbulb-off", entity_category=EntityCategory.DIAGNOSTIC),
        ]
        entities = base_entities + advantium_entities
        return entities

    def _single_name(self, erd_code: ErdCode):
        return erd_code.name.replace(UPPER_OVEN+"_","").replace("_", " ").title()

