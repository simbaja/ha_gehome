from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import ErdApplianceType

from .base import ApplianceApi
from ..entities import (
    GeErdRawBoolLight,
    GeToasterOven,
    GeToasterOvenConvectionSensor,
    GeToasterOvenCookModeSensor,
    GeToasterOvenCookTimeRemainingSensor,
    GeToasterOvenCrispFinishSensor,
    GeToasterOvenRemoteEnabledSensor,
    GeToasterOvenStateSensor,
)


class ToasterOvenApi(ApplianceApi):
    """API class for toaster oven objects."""

    APPLIANCE_TYPE = ErdApplianceType.TOASTER_OVEN

    def get_all_entities(self) -> List[Entity]:
        entities = super().get_all_entities()
        entities.extend(
            [
                GeErdRawBoolLight(self, "0x9201", "light", control_erd_code="0x9202"),
                GeToasterOven(self),
                GeToasterOvenCookModeSensor(self),
                GeToasterOvenCrispFinishSensor(self),
                GeToasterOvenConvectionSensor(self),
                GeToasterOvenStateSensor(self),
                GeToasterOvenRemoteEnabledSensor(self),
                GeToasterOvenCookTimeRemainingSensor(self),
            ]
        )
        return entities
