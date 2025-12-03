import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType

from .base import ApplianceApi
from ..entities import GeErdSensor, GeErdBinarySensor, GeErdButton
from ..entities.laundry.ge_dryer_cycle_button import GeDryerCycleButton


_LOGGER = logging.getLogger(__name__)

class DryerApi(ApplianceApi):
    """API class for dryer objects"""
    APPLIANCE_TYPE = ErdApplianceType.DRYER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        common_entities = [
            GeErdSensor(self, ErdCode.LAUNDRY_MACHINE_STATE, icon_override="mdi:tumble-dryer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.LAUNDRY_CYCLE, icon_override="mdi:state-machine"),
            GeErdSensor(self, ErdCode.LAUNDRY_SUB_CYCLE, icon_override="mdi:state-machine"),
            GeErdBinarySensor(self, ErdCode.LAUNDRY_END_OF_CYCLE, icon_on_override="mdi:tumble-dryer", icon_off_override="mdi:tumble-dryer"),
            GeErdSensor(self, ErdCode.LAUNDRY_TIME_REMAINING, suggested_uom="min"),
            GeErdSensor(self, ErdCode.LAUNDRY_DELAY_TIME_REMAINING, suggested_uom="h"),
            GeErdBinarySensor(self, ErdCode.LAUNDRY_DOOR, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.LAUNDRY_REMOTE_STATUS, icon_on_override="mdi:tumble-dryer", icon_off_override="mdi:tumble-dryer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.LAUNDRY_DRYER_BLOCKED_VENT_FAULT, icon_on_override="mdi:alert-circle", icon_off_override="mdi:alert-circle", entity_category=EntityCategory.DIAGNOSTIC),
        ]

        dryer_entities = self.get_dryer_entities()
        
        # Add the start cycle button
        dryer_entities.append(GeDryerCycleButton(self))

        entities = base_entities + common_entities + dryer_entities
        return entities

    def get_dryer_entities(self):
        dryer_entities = []

        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_DRYNESS_LEVEL):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_DRYNESS_LEVEL, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_DRYNESSNEW_LEVEL):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_DRYNESSNEW_LEVEL, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_TEMPERATURE_OPTION):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_TEMPERATURE_OPTION, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_TEMPERATURENEW_OPTION):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_TEMPERATURENEW_OPTION, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_TUMBLE_STATUS):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_TUMBLE_STATUS, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_EXTENDED_TUMBLE_OPTION_SELECTION):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_EXTENDED_TUMBLE_OPTION_SELECTION, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_WASHERLINK_STATUS):
            dryer_entities.extend([GeErdBinarySensor(self, ErdCode.LAUNDRY_DRYER_WASHERLINK_STATUS, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_LEVEL_SENSOR_DISABLED):
            dryer_entities.extend([GeErdBinarySensor(self, ErdCode.LAUNDRY_DRYER_LEVEL_SENSOR_DISABLED, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_SHEET_USAGE_CONFIGURATION):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_SHEET_USAGE_CONFIGURATION, entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_SHEET_INVENTORY):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_SHEET_INVENTORY, icon_override="mdi:tray-full", uom_override="sheets", entity_category=EntityCategory.DIAGNOSTIC)])
        if self.has_erd_code(ErdCode.LAUNDRY_DRYER_ECODRY_OPTION_SELECTION):
            dryer_entities.extend([GeErdSensor(self, ErdCode.LAUNDRY_DRYER_ECODRY_OPTION_SELECTION, entity_category=EntityCategory.DIAGNOSTIC)])

        return dryer_entities