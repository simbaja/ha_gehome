import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType

from .base import ApplianceApi
from ..entities import (
    GeErdSensor,
    GeErdPropertySensor,
    GeErdBinarySensor,
    GeErdFilterPositionSelect,
)

_LOGGER = logging.getLogger(__name__)


class WaterFilterApi(ApplianceApi):
    """API class for water filter objects"""

    APPLIANCE_TYPE = ErdApplianceType.POE_WATER_FILTER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        wf_entities = [
            GeErdSensor(self, ErdCode.WH_FILTER_MODE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.WH_FILTER_VALVE_STATE, icon_override="mdi:state-machine", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdFilterPositionSelect(self, ErdCode.WH_FILTER_POSITION),
            GeErdBinarySensor(self, ErdCode.WH_FILTER_MANUAL_MODE, icon_on_override="mdi:human", icon_off_override="mdi:robot", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.WH_FILTER_LEAK_VALIDITY, device_class_override="moisture", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.WH_FILTER_FLOW_RATE, "flow_rate", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.WH_FILTER_DAY_USAGE, device_class_override="water", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.WH_FILTER_LIFE_REMAINING, "life_remaining", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.WH_FILTER_FLOW_ALERT, device_class_override="moisture", entity_category=EntityCategory.DIAGNOSTIC),
        ]
        entities = base_entities + wf_entities
        return entities
