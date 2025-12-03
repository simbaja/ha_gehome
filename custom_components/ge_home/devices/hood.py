import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdApplianceType,
    ErdHoodFanSpeedAvailability,
    ErdHoodLightLevelAvailability,
    ErdHoodFanSpeed,
    ErdHoodLightLevel,
    ErdOnOff
)

from .base import ApplianceApi
from ..entities import (
    GeHoodLightLevelSelect, 
    GeHoodFanSpeedSelect, 
    GeErdTimerSensor, 
    GeErdSwitch, 
    ErdOnOffBoolConverter
)

_LOGGER = logging.getLogger(__name__)


class HoodApi(ApplianceApi):
    """API class for Oven Hood objects"""
    APPLIANCE_TYPE = ErdApplianceType.HOOD

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        #old-style entities
        fan_availability: ErdHoodFanSpeedAvailability | None = self.try_get_erd_value(ErdCode.HOOD_FAN_SPEED_AVAILABILITY)
        light_availability: ErdHoodLightLevelAvailability | None = self.try_get_erd_value(ErdCode.HOOD_LIGHT_LEVEL_AVAILABILITY)
        timer_availability: ErdOnOff | None = self.try_get_erd_value(ErdCode.HOOD_TIMER_AVAILABILITY)

        #new-style entities
        available_fan_speeds: int | None = self.try_get_erd_value(ErdCode.HOOD_AVAILABLE_FAN_SPEEDS)
        available_light_levels: int | None = self.try_get_erd_value(ErdCode.HOOD_AVAILABLE_LIGHT_LEVELS)
        actual_fan_speed: ErdHoodFanSpeed | None = self.try_get_erd_value(ErdCode.HOOD_ACTUAL_FAN_SPEED)
        actual_light_level: ErdHoodLightLevel | None = self.try_get_erd_value(ErdCode.HOOD_ACTUAL_LIGHT_LEVEL)

        hood_entities: List[Entity] = [
            #looks like this is always available?
            GeErdSwitch(self, ErdCode.HOOD_DELAY_OFF, bool_converter=ErdOnOffBoolConverter(), icon_on_override="mdi:power-on", icon_off_override="mdi:power-off"),
        ]

        #old-style
        if fan_availability is not None and fan_availability.is_available:
            hood_entities.append(GeHoodFanSpeedSelect(self, ErdCode.HOOD_FAN_SPEED))
        if light_availability is not None and light_availability.is_available:
            hood_entities.append(GeHoodLightLevelSelect(self, ErdCode.HOOD_LIGHT_LEVEL))
        
        #new-style
        if available_fan_speeds is not None and available_fan_speeds > 0 and actual_fan_speed is not None:
            hood_entities.append(GeHoodFanSpeedSelect(self, ErdCode.HOOD_ACTUAL_FAN_SPEED, ErdCode.HOOD_REQUESTED_FAN_SPEED))
        if available_light_levels is not None and available_light_levels > 0 and actual_light_level is not None:
            hood_entities.append(GeHoodLightLevelSelect(self, ErdCode.HOOD_ACTUAL_LIGHT_LEVEL, ErdCode.HOOD_REQUESTED_LIGHT_LEVEL))

        #timer
        if timer_availability is not None:
            hood_entities.append(GeErdTimerSensor(self, ErdCode.HOOD_TIMER, suggested_uom="h"))

        entities = base_entities + hood_entities
        return entities
        
