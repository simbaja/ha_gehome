import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdApplianceType,
    ErdHoodFanSpeedAvailability,
    ErdHoodLightLevelAvailability,
    ErdOnOff
    # NOTE: We are no longer importing ErdCodeType here
)

from .base import ApplianceApi
from ..entities import (
    # Existing entities
    GeHoodLightLevelSelect, 
    GeHoodFanSpeedSelect, 
    GeErdTimerSensor, 
    GeErdSwitch, 
    ErdOnOffBoolConverter,
    # New entities for Haier Hood
    GeHaierHoodFan,
    GeHaierHoodLight
)

_LOGGER = logging.getLogger(__name__)


class HoodApi(ApplianceApi):
    """API class for Hood objects"""
    APPLIANCE_TYPE = ErdApplianceType.HOOD

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()
        
        # Define the unique ERD codes for the Haier FPA Hood as simple strings.
        ERD_HAIER_FAN_SPEED = "0x5B13"
        ERD_HAIER_LIGHT_STATE = "0x5B17"

        # Check if this is a Haier FPA Hood by looking for its specific ERD code
        if self.has_erd_code(ERD_HAIER_FAN_SPEED):
            _LOGGER.debug("Detected Haier FPA Hood, creating Fan and Light entities")
            hood_entities = [
                GeHaierHoodFan(self, ERD_HAIER_FAN_SPEED),
                GeHaierHoodLight(self, ERD_HAIER_LIGHT_STATE)
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