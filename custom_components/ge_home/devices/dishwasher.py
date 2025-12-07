import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType, ErdRemoteCommand

from .base import ApplianceApi
from ..entities import GeErdSensor, GeErdBinarySensor, GeErdPropertySensor, GeErdNumber, GeDishwasherCommandButton

_LOGGER = logging.getLogger(__name__)


class DishwasherApi(ApplianceApi):
    """API class for dishwasher objects"""
    APPLIANCE_TYPE = ErdApplianceType.DISH_WASHER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        dishwasher_entities = [
            GeErdSensor(self, ErdCode.DISHWASHER_CYCLE_NAME),
            GeErdSensor(self, ErdCode.DISHWASHER_CYCLE_STATE, icon_override="mdi:state-machine"),
            GeErdSensor(self, ErdCode.DISHWASHER_OPERATING_MODE),
            GeErdNumber(self, ErdCode.DISHWASHER_PODS_REMAINING_VALUE, uom_override="pods", min_value=0, max_value=255, entity_category=EntityCategory.CONFIG),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "add_rinse_aid", icon_override="mdi:shimmer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "clean_filter", icon_override="mdi:dishwasher-alert", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "sanitized", icon_override="mdi:silverware-clean", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.DISHWASHER_TIME_REMAINING, suggested_uom="h"),
            GeErdBinarySensor(self, ErdCode.DISHWASHER_DOOR_STATUS, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.DISHWASHER_IS_CLEAN),

            #User Setttings
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "mute", icon_override="mdi:volume-mute", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "lock_control", icon_override="mdi:lock", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "sabbath", icon_override="mdi:star-david", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "cycle_mode", icon_override="mdi:state-machine", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "presoak", icon_override="mdi:water", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "bottle_jet", icon_override="mdi:bottle-tonic-outline", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "wash_temp", icon_override="mdi:coolant-temperature", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "rinse_aid", icon_override="mdi:shimmer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "dry_option", icon_override="mdi:fan", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "wash_zone", icon_override="mdi:dock-top", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "delay_hours", icon_override="mdi:clock-fast", entity_category=EntityCategory.DIAGNOSTIC),

            #Cycle Counts
            GeErdPropertySensor(self, ErdCode.DISHWASHER_CYCLE_COUNTS, "started", icon_override="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_CYCLE_COUNTS, "completed", icon_override="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_CYCLE_COUNTS, "reset", icon_override="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC)
        ]

        # check for remote command availability and add if present
        if self.has_erd_code(ErdCode.DISHWASHER_REMOTE_START_ENABLE):
            dishwasher_entities.extend(
                [
                    GeErdBinarySensor(self, ErdCode.DISHWASHER_REMOTE_START_ENABLE, entity_category=EntityCategory.DIAGNOSTIC),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.START_RESUME),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.PAUSE),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.CANCEL)
                ]
            )

        entities = base_entities + dishwasher_entities
        return entities
        
