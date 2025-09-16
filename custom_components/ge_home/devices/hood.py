# custom_components/ge_home/devices/hood.py
import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode,
    ErdApplianceType,
    ErdHoodFanSpeedAvailability,
    ErdHoodLightLevelAvailability,
    ErdOnOff,
)

from .base import ApplianceApi
from ..entities import (
    GeHoodLightLevelSelect,
    GeHoodFanSpeedSelect,
    GeErdTimerSensor,
    GeErdSwitch,
    ErdOnOffBoolConverter,
    GeHaierHoodFan,
    GeHaierHoodLight,
)

_LOGGER = logging.getLogger(__name__)


class HoodApi(ApplianceApi):
    """API class for Hood objects (GE + Haier)"""

    APPLIANCE_TYPE = ErdApplianceType.HOOD

    # Haier-specific ERDs
    ERD_HAIER_FAN_SPEED = "0x5B13"
    ERD_HAIER_LIGHT_LEVEL = "0x5B14"

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        # GE availabilities
        fan_availability: ErdHoodFanSpeedAvailability = self.try_get_erd_value(
            ErdCode.HOOD_FAN_SPEED_AVAILABILITY
        )
        light_availability: ErdHoodLightLevelAvailability = self.try_get_erd_value(
            ErdCode.HOOD_LIGHT_LEVEL_AVAILABILITY
        )
        timer_availability: ErdOnOff = self.try_get_erd_value(ErdCode.HOOD_TIMER_AVAILABILITY)

        hood_entities: List[Entity] = [
            # Looks like this is always available?
            GeErdSwitch(
                self,
                ErdCode.HOOD_DELAY_OFF,
                bool_converter=ErdOnOffBoolConverter(),
                icon_on_override="mdi:power-on",
                icon_off_override="mdi:power-off",
            ),
        ]

        # --- GE hoods ---
        if fan_availability and fan_availability.is_available:
            hood_entities.append(GeHoodFanSpeedSelect(self, ErdCode.HOOD_FAN_SPEED))
        if light_availability and light_availability.is_available:
            hood_entities.append(GeHoodLightLevelSelect(self, ErdCode.HOOD_LIGHT_LEVEL))
        if timer_availability == ErdOnOff.ON:
            hood_entities.append(GeErdTimerSensor(self, ErdCode.HOOD_TIMER))

        # --- Haier hoods ---
        # If SDK doesn’t provide availability ERDs, always expose both.
        try:
            if self.try_get_erd_value(self.ERD_HAIER_FAN_SPEED) is not None:
                hood_entities.append(GeHaierHoodFan(self, self.ERD_HAIER_FAN_SPEED))
            if self.try_get_erd_value(self.ERD_HAIER_LIGHT_LEVEL) is not None:
                hood_entities.append(GeHaierHoodLight(self, self.ERD_HAIER_LIGHT_LEVEL))
        except Exception as err:
            _LOGGER.warning(f"Error while adding Haier hood entities: {err}")

        entities = base_entities + hood_entities
        return entities
