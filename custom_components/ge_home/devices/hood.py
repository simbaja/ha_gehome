import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdApplianceType,
    ErdHoodFanSpeedAvailability,
    ErdHoodLightLevelAvailability,
    ErdOnOff
)
from gehomesdk.erd.converters import ErdIntConverter

from .base import ApplianceApi
from ..entities import (
    GeHoodLightLevelSelect, 
    GeHoodFanSpeedSelect, 
    GeErdTimerSensor, 
    GeErdSwitch, 
    ErdOnOffBoolConverter,
    GeHaierHoodFan,
    GeHaierHoodLight
)

_LOGGER = logging.getLogger(__name__)


class HoodApi(ApplianceApi):
    """API class for Hood objects"""
    APPLIANCE_TYPE = ErdApplianceType.HOOD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define the custom ERD codes
        self.ERD_HAIER_FAN_SPEED = "0x5B13"
        self.ERD_HAIER_LIGHT_STATE = "0x5B17"
        
        # If this is a Haier Hood, we must manually register the converters
        # for our new codes in the SDK's internal encoder registry.
        if self.has_erd_code(self.ERD_HAIER_FAN_SPEED):
            encoder = self.appliance._encoder
            if self.ERD_HAIER_FAN_SPEED not in encoder._registry:
                _LOGGER.debug(f"Registering custom converter for {self.ERD_HAIER_FAN_SPEED}")
                encoder._registry[self.ERD_HAIER_FAN_SPEED] = ErdIntConverter()
            if self.ERD_HAIER_LIGHT_STATE not in encoder._registry:
                _LOGGER.debug(f"Registering custom converter for {self.ERD_HAIER_LIGHT_STATE}")
                encoder._registry[self.ERD_HAIER_LIGHT_STATE] = ErdIntConverter()

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()
        
        if self.has_erd_code(self.ERD_HAIER_FAN_SPEED):
            _LOGGER.debug("Detected Haier FPA Hood, creating Fan and Light entities")
            hood_entities = [
                GeHaierHoodFan(self, self.ERD_HAIER_FAN_SPEED),
                GeHaierHoodLight(self, self.ERD_HAIER_LIGHT_STATE)
            ]
        else:
            _LOGGER.debug("Detected standard GE Hood, creating Select entities")
            # This is the original logic for GE Profile hoods
            fan_availability: ErdHoodFanSpeedAvailability = self.try_get_erd_value(ErdCode.HOOD_FAN_SPEED_AVAILABILITY)
            light_availability: ErdHoodLightLevelAvailability = self.try_get_erd_value(ErdCode.HOOD_LIGHT_LEVEL_AVAILABILITY)
            timer_availability: ErdOnOff = self.try_get_erd_value(ErdCode.HOOD_TIMER_AVAILABILITY)

            hood_entities = [
                GeErdSwitch(self, ErdCode.HOOD_DELAY_OFF, bool_converter=ErdOnOffBoolConverter(), icon_on_override="mdi:power-on", icon_off_override="mdi:power-off"),
            ]

            if fan_availability and fan_availability.is_available:
                hood_entities.append(GeHoodFanSpeedSelect(self, ErdCode.HOOD_FAN_SPEED))
            if light_availability and light_availability.is_available:
                hood_entities.append(GeHoodLightLevelSelect(self, ErdCode.HOOD_LIGHT_LEVEL))
            if timer_availability == ErdOnOff.ON:
                hood_entities.append(GeErdTimerSensor(self, ErdCode.HOOD_TIMER))
                
        return base_entities + hood_entities