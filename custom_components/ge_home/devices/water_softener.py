import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType

from .base import ApplianceApi
from ..entities import (
    GeErdSensor,
    GeErdPropertySensor,
    GeErdBinarySensor,
    GeErdShutoffPositionSelect,
)

_LOGGER = logging.getLogger(__name__)


class WaterSoftenerApi(ApplianceApi):
    """API class for water softener objects"""

    APPLIANCE_TYPE = ErdApplianceType.WATER_SOFTENER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        ws_entities = [
            GeErdBinarySensor(self, ErdCode.WH_FILTER_MANUAL_MODE, icon_on_override="mdi:human", icon_off_override="mdi:robot"),
            GeErdPropertySensor(self, ErdCode.WH_FILTER_FLOW_RATE, "flow_rate"),
            GeErdBinarySensor(self, ErdCode.WH_FILTER_FLOW_ALERT, device_class_override="moisture"),
            GeErdSensor(self, ErdCode.WH_FILTER_DAY_USAGE, device_class_override="water"),
            GeErdSensor(self, ErdCode.WH_SOFTENER_ERROR_CODE, icon_override="mdi:alert-circle"),
            GeErdBinarySensor(self, ErdCode.WH_SOFTENER_LOW_SALT, icon_on_override="mdi:alert", icon_off_override="mdi:grain"),
            GeErdSensor(self, ErdCode.WH_SOFTENER_SHUTOFF_VALVE_STATE, icon_override="mdi:state-machine"),
            GeErdSensor(self, ErdCode.WH_SOFTENER_SALT_LIFE_REMAINING, icon_override="mdi:calendar-clock"),
            GeErdShutoffPositionSelect(self, ErdCode.WH_SOFTENER_SHUTOFF_VALVE_CONTROL),
        ]
        entities = base_entities + ws_entities
        return entities
