import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdDataType,
    ErdApplianceType, 
    OvenConfiguration, 
    ErdCooktopConfig, 
    CooktopStatus,
    ErdOvenLightLevel,
    ErdOvenLightLevelAvailability,
    ErdOvenWarmingState
)

from .base import ApplianceApi
from ..entities import (
    GeErdSensor, 
    GeErdTimerSensor,
    GeErdBinarySensor, 
    GeErdPropertySensor,
    GeErdPropertyBinarySensor,
    GeOven, 
    GeOvenLightLevelSelect,
    GeOvenWarmingStateSelect,
    UPPER_OVEN, 
    LOWER_OVEN
)

_LOGGER = logging.getLogger(__name__)

class OvenApi(ApplianceApi):
    """API class for oven objects"""
    APPLIANCE_TYPE = ErdApplianceType.OVEN

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()
        oven_config: OvenConfiguration = self.appliance.get_erd_value(ErdCode.OVEN_CONFIGURATION)

        cooktop_config = ErdCooktopConfig.NONE
        if self.has_erd_code(ErdCode.COOKTOP_CONFIG):
            cooktop_config: ErdCooktopConfig = self.appliance.get_erd_value(ErdCode.COOKTOP_CONFIG)

        has_upper_raw_temperature = self.has_erd_code(ErdCode.UPPER_OVEN_RAW_TEMPERATURE)
        has_lower_raw_temperature = self.has_erd_code(ErdCode.LOWER_OVEN_RAW_TEMPERATURE)

        has_upper_probe_temperature = self.has_erd_code(ErdCode.UPPER_OVEN_PROBE_DISPLAY_TEMP)
        has_lower_probe_temperature = self.has_erd_code(ErdCode.LOWER_OVEN_PROBE_DISPLAY_TEMP)

        upper_light: ErdOvenLightLevel | None = self.try_get_erd_value(ErdCode.UPPER_OVEN_LIGHT)
        upper_light_availability: ErdOvenLightLevelAvailability | None = self.try_get_erd_value(ErdCode.UPPER_OVEN_LIGHT_AVAILABILITY)
        lower_light: ErdOvenLightLevel | None = self.try_get_erd_value(ErdCode.LOWER_OVEN_LIGHT)
        lower_light_availability: ErdOvenLightLevelAvailability | None = self.try_get_erd_value(ErdCode.LOWER_OVEN_LIGHT_AVAILABILITY)

        upper_warm_drawer : ErdOvenWarmingState | None = self.try_get_erd_value(ErdCode.UPPER_OVEN_WARMING_DRAWER_STATE)
        lower_warm_drawer : ErdOvenWarmingState | None = self.try_get_erd_value(ErdCode.LOWER_OVEN_WARMING_DRAWER_STATE)
        warm_drawer : ErdOvenWarmingState | None = self.try_get_erd_value(ErdCode.WARMING_DRAWER_STATE)

        _LOGGER.debug(f"Oven Config: {oven_config}")
        _LOGGER.debug(f"Cooktop Config: {cooktop_config}")
        oven_entities = []
        cooktop_entities = []

        if oven_config.has_lower_oven:
            oven_entities.extend([
                GeErdSensor(self, ErdCode.LOWER_OVEN_COOK_MODE, entity_category=EntityCategory.DIAGNOSTIC),
                GeErdSensor(self, ErdCode.LOWER_OVEN_CURRENT_STATE, entity_category=EntityCategory.DIAGNOSTIC),
                GeErdSensor(self, ErdCode.LOWER_OVEN_COOK_TIME_REMAINING, suggested_uom="h"),
                GeErdTimerSensor(self, ErdCode.LOWER_OVEN_KITCHEN_TIMER, suggested_uom="h"),
                GeErdSensor(self, ErdCode.LOWER_OVEN_USER_TEMP_OFFSET, entity_category=EntityCategory.DIAGNOSTIC),
                GeErdSensor(self, ErdCode.LOWER_OVEN_DISPLAY_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC),
                GeErdBinarySensor(self, ErdCode.LOWER_OVEN_REMOTE_ENABLED, entity_category=EntityCategory.DIAGNOSTIC),

                GeOven(self, LOWER_OVEN, True, self._temperature_code(has_lower_raw_temperature))
            ])
            if has_lower_raw_temperature:
                oven_entities.append(GeErdSensor(self, ErdCode.LOWER_OVEN_RAW_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC))
            if lower_light_availability is None or lower_light_availability.is_available or lower_light is not None:
                oven_entities.append(GeOvenLightLevelSelect(self, ErdCode.LOWER_OVEN_LIGHT))
            if lower_warm_drawer is not None:
                oven_entities.append(GeOvenWarmingStateSelect(self, ErdCode.LOWER_OVEN_WARMING_DRAWER_STATE))
            if has_lower_probe_temperature:
                oven_entities.append(GeErdSensor(self, ErdCode.LOWER_OVEN_PROBE_DISPLAY_TEMP, entity_category=EntityCategory.DIAGNOSTIC))

        oven_entities.extend([
            GeErdSensor(self, ErdCode.UPPER_OVEN_COOK_MODE, self._single_name(ErdCode.UPPER_OVEN_COOK_MODE, not oven_config.has_lower_oven), entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.UPPER_OVEN_CURRENT_STATE, self._single_name(ErdCode.UPPER_OVEN_CURRENT_STATE, not oven_config.has_lower_oven), entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.UPPER_OVEN_COOK_TIME_REMAINING, self._single_name(ErdCode.UPPER_OVEN_COOK_TIME_REMAINING, not oven_config.has_lower_oven), suggested_uom="h"),
            GeErdTimerSensor(self, ErdCode.UPPER_OVEN_KITCHEN_TIMER, self._single_name(ErdCode.UPPER_OVEN_KITCHEN_TIMER, not oven_config.has_lower_oven), suggested_uom="h"),
            GeErdSensor(self, ErdCode.UPPER_OVEN_USER_TEMP_OFFSET, self._single_name(ErdCode.UPPER_OVEN_USER_TEMP_OFFSET, not oven_config.has_lower_oven), entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE, self._single_name(ErdCode.UPPER_OVEN_DISPLAY_TEMPERATURE, not oven_config.has_lower_oven), entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.UPPER_OVEN_REMOTE_ENABLED, self._single_name(ErdCode.UPPER_OVEN_REMOTE_ENABLED, not oven_config.has_lower_oven), entity_category=EntityCategory.DIAGNOSTIC),
            
            GeOven(self, UPPER_OVEN, False, self._temperature_code(has_upper_raw_temperature))
        ])
        if has_upper_raw_temperature:
            oven_entities.append(GeErdSensor(self, ErdCode.UPPER_OVEN_RAW_TEMPERATURE, self._single_name(ErdCode.UPPER_OVEN_RAW_TEMPERATURE, not oven_config.has_lower_oven), entity_category=EntityCategory.DIAGNOSTIC))
        if upper_light_availability is None or upper_light_availability.is_available or upper_light is not None:
            oven_entities.append(GeOvenLightLevelSelect(self, ErdCode.UPPER_OVEN_LIGHT, self._single_name(ErdCode.UPPER_OVEN_LIGHT, not oven_config.has_lower_oven)))
        if upper_warm_drawer is not None:
            oven_entities.append(GeOvenWarmingStateSelect(self, ErdCode.UPPER_OVEN_WARMING_DRAWER_STATE, self._single_name(ErdCode.UPPER_OVEN_WARMING_DRAWER_STATE, not oven_config.has_lower_oven)))
        if has_upper_probe_temperature:
            oven_entities.append(GeErdSensor(self, ErdCode.UPPER_OVEN_PROBE_DISPLAY_TEMP, self._single_name(ErdCode.UPPER_OVEN_PROBE_DISPLAY_TEMP, not oven_config.has_lower_oven), entity_category=EntityCategory.DIAGNOSTIC))

        if oven_config.has_warming_drawer and warm_drawer is not None:
            oven_entities.append(GeErdSensor(self, ErdCode.WARMING_DRAWER_STATE, entity_category=EntityCategory.DIAGNOSTIC))

        if cooktop_config == ErdCooktopConfig.PRESENT:
            # attempt to get the cooktop status using legacy status
            cooktop_status_erd = ErdCode.COOKTOP_STATUS
            cooktop_status: CooktopStatus | None = self.try_get_erd_value(ErdCode.COOKTOP_STATUS)

            # if we didn't get it, try using the new version
            if cooktop_status is None:
                cooktop_status_erd = ErdCode.COOKTOP_STATUS_EXT
                cooktop_status = self.try_get_erd_value(ErdCode.COOKTOP_STATUS_EXT)

            # if we got a status through either mechanism, we can add the entities
            if cooktop_status is not None:
                cooktop_entities.append(GeErdBinarySensor(self, cooktop_status_erd))
            
                for (k, v) in cooktop_status.burners.items():
                    if v.exists:
                        prop = self._camel_to_snake(k)
                        cooktop_entities.append(GeErdPropertyBinarySensor(self, cooktop_status_erd, prop+".on"))
                        cooktop_entities.append(GeErdPropertyBinarySensor(self, cooktop_status_erd, prop+".synchronized", entity_category=EntityCategory.DIAGNOSTIC))                    
                        if not v.on_off_only:
                            cooktop_entities.append(GeErdPropertySensor(self, cooktop_status_erd, prop+".power_pct", icon_override="mdi:fire", device_class_override=SensorDeviceClass.POWER_FACTOR, data_type_override=ErdDataType.INT))

        return base_entities + oven_entities + cooktop_entities

    def _single_name(self, erd_code: ErdCode, make_single: bool):
        name = erd_code.name
        
        if make_single:
            name = name.replace(UPPER_OVEN+"_","")
            
        return name.replace("_", " ").title()

    def _camel_to_snake(self, s):
        return ''.join(['_'+c.lower() if c.isupper() else c for c in s]).lstrip('_')    

    def _temperature_code(self, has_raw: bool):
        return "RAW_TEMPERATURE" if has_raw else "DISPLAY_TEMPERATURE"
