import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType

from .base import ApplianceApi
from ..entities import GeErdSensor, GeErdBinarySensor, GeErdPropertySensor
from ..entities.laundry.ge_washer_cycle_button import GeWasherCycleButton


_LOGGER = logging.getLogger(__name__)


class WasherApi(ApplianceApi):
    """API class for washer objects"""
    APPLIANCE_TYPE = ErdApplianceType.WASHER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        common_entities = [
            GeErdSensor(self, ErdCode.LAUNDRY_MACHINE_STATE),
            GeErdSensor(self, ErdCode.LAUNDRY_CYCLE, icon_override="mdi:state-machine"),
            GeErdSensor(self, ErdCode.LAUNDRY_SUB_CYCLE, icon_override="mdi:state-machine"),
            GeErdBinarySensor(self, ErdCode.LAUNDRY_END_OF_CYCLE),
            GeErdSensor(self, ErdCode.LAUNDRY_TIME_REMAINING, suggested_uom="min"),
            GeErdSensor(self, ErdCode.LAUNDRY_DELAY_TIME_REMAINING, suggested_uom="h"),
            GeErdBinarySensor(self, ErdCode.LAUNDRY_DOOR, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.LAUNDRY_REMOTE_STATUS, entity_category=EntityCategory.DIAGNOSTIC),
        ]

        washer_entities = self.get_washer_entities()

        washer_entities.append(GeWasherCycleButton(self))

        entities = base_entities + common_entities + washer_entities
        return entities

    def get_washer_entities(self) -> List[Entity]:
        washer_entities: List[Entity] = [
            GeErdSensor(self, ErdCode.LAUNDRY_WASHER_SOIL_LEVEL, icon_override="mdi:emoticon-poop", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.LAUNDRY_WASHER_WASHTEMP_LEVEL, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.LAUNDRY_WASHER_SPINTIME_LEVEL, icon_override="mdi:speedometer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.LAUNDRY_WASHER_RINSE_OPTION, icon_override="mdi:shimmer", entity_category=EntityCategory.DIAGNOSTIC),
        ]

        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_DOOR_LOCK):
            washer_entities.extend([GeErdBinarySensor(self, ErdCode.LAUNDRY_WASHER_DOOR_LOCK, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_TANK_STATUS):
            washer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_WASHER_TANK_STATUS, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_TANK_SELECTED):
            washer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_WASHER_TANK_SELECTED, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_TIMESAVER):
            washer_entities.extend([GeErdBinarySensor(self, ErdCode.LAUNDRY_WASHER_TIMESAVER, icon_on_override="mdi:sort-clock-ascending", icon_off_override="mdi:sort-clock-ascending-outline", entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_POWERSTEAM):
            washer_entities.extend([GeErdBinarySensor(self, ErdCode.LAUNDRY_WASHER_POWERSTEAM, icon_on_override="mdi:kettle-steam", icon_off_override="mdi:kettle-steam-outline", entity_category=EntityCategory.DIAGNOSTIC)])
        
        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_PREWASH):
            washer_entities.extend([GeErdBinarySensor(self, ErdCode.LAUNDRY_WASHER_PREWASH, icon_on_override="mdi:water-plus", icon_off_override="mdi:water-remove-outline", entity_category=EntityCategory.DIAGNOSTIC)])
        
        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_TUMBLECARE):
            washer_entities.extend([GeErdBinarySensor(self, ErdCode.LAUNDRY_WASHER_TUMBLECARE, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_SMART_DISPENSE):
            washer_entities.extend([GeErdPropertySensor(self, ErdCode.LAUNDRY_WASHER_SMART_DISPENSE, "loads_left", uom_override="loads", entity_category=EntityCategory.DIAGNOSTIC)])
        
        if self.has_erd_code(ErdCode.LAUNDRY_WASHER_SMART_DISPENSE_TANK_STATUS):
            washer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_WASHER_SMART_DISPENSE_TANK_STATUS, entity_category=EntityCategory.DIAGNOSTIC)])

        return washer_entities