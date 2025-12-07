import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType, ErdRemoteCommand

from .base import ApplianceApi
from ..entities import GeErdSensor, GeErdBinarySensor, GeErdPropertySensor, GeDishwasherCommandButton

_LOGGER = logging.getLogger(__name__)


class DualDishwasherApi(ApplianceApi):
    """API class for dual dishwasher objects"""
    APPLIANCE_TYPE = ErdApplianceType.DISH_WASHER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        lower_entities = [
            GeErdSensor(self, ErdCode.DISHWASHER_CYCLE_STATE, erd_override="lower_cycle_state", icon_override="mdi:state-machine"),
            GeErdSensor(self, ErdCode.DISHWASHER_TIME_REMAINING, erd_override="lower_time_remaining", suggested_uom="h"),
            GeErdBinarySensor(self, ErdCode.DISHWASHER_DOOR_STATUS, erd_override="lower_door_status", entity_category=EntityCategory.DIAGNOSTIC),

            #Reminders
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "add_rinse_aid", erd_override="lower_reminder", icon_override="mdi:shimmer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "clean_filter", erd_override="lower_reminder", icon_override="mdi:dishwasher-alert", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "sanitized", erd_override="lower_reminder", icon_override="mdi:silverware-clean", entity_category=EntityCategory.DIAGNOSTIC),

            #User Setttings
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "mute", erd_override="lower_setting", icon_override="mdi:volume-mute", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "lock_control", erd_override="lower_setting", icon_override="mdi:lock", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "sabbath", erd_override="lower_setting", icon_override="mdi:star-david", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "cycle_mode", erd_override="lower_setting", icon_override="mdi:state-machine", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "presoak", erd_override="lower_setting", icon_override="mdi:water", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "bottle_jet", erd_override="lower_setting", icon_override="mdi:bottle-tonic-outline", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "wash_temp", erd_override="lower_setting", icon_override="mdi:coolant-temperature", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "rinse_aid", erd_override="lower_setting", icon_override="mdi:shimmer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "dry_option", erd_override="lower_setting", icon_override="mdi:fan", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "wash_zone", erd_override="lower_setting", icon_override="mdi:dock-top", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "delay_hours", erd_override="lower_setting", icon_override="mdi:clock-fast", entity_category=EntityCategory.DIAGNOSTIC)
        ]

        upper_entities = [
            GeErdSensor(self, ErdCode.DISHWASHER_UPPER_CYCLE_STATE, erd_override="upper_cycle_state", icon_override="mdi:state-machine"),
            GeErdSensor(self, ErdCode.DISHWASHER_UPPER_TIME_REMAINING, erd_override="upper_time_remaining", suggested_uom="h"),
            GeErdBinarySensor(self, ErdCode.DISHWASHER_UPPER_DOOR_STATUS, erd_override="upper_door_status", entity_category=EntityCategory.DIAGNOSTIC),

            #Reminders
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_REMINDERS, "add_rinse_aid", erd_override="upper_reminder", icon_override="mdi:shimmer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_REMINDERS, "clean_filter", erd_override="upper_reminder", icon_override="mdi:dishwasher-alert", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_REMINDERS, "sanitized", erd_override="upper_reminder", icon_override="mdi:silverware-clean", entity_category=EntityCategory.DIAGNOSTIC),

            #User Setttings
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "mute", erd_override="upper_setting", icon_override="mdi:volume-mute", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "lock_control", erd_override="upper_setting", icon_override="mdi:lock", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "sabbath", erd_override="upper_setting", icon_override="mdi:star-david", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "cycle_mode", erd_override="upper_setting", icon_override="mdi:state-machine", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "presoak", erd_override="upper_setting", icon_override="mdi:water", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "bottle_jet", erd_override="upper_setting", icon_override="mdi:bottle-tonic-outline", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "wash_temp", erd_override="upper_setting", icon_override="mdi:coolant-temperature", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "rinse_aid", erd_override="upper_setting", icon_override="mdi:shimmer", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "dry_option", erd_override="upper_setting", icon_override="mdi:fan", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "wash_zone", erd_override="upper_setting", icon_override="mdi:dock-top", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "delay_hours", erd_override="upper_setting", icon_override="mdi:clock-fast", entity_category=EntityCategory.DIAGNOSTIC)
        ]

        # check for remote command availability and add if present (lower)
        if self.has_erd_code(ErdCode.DISHWASHER_REMOTE_START_ENABLE):
            lower_entities.extend(
                [
                    GeErdBinarySensor(self, ErdCode.DISHWASHER_REMOTE_START_ENABLE, erd_override="lower_remote_command_enable", entity_category=EntityCategory.DIAGNOSTIC),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.START_RESUME, erd_override="lower_remote_command"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.PAUSE, erd_override="lower_remote_command"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.CANCEL, erd_override="lower_remote_command")
                ]
            )

        # check for remote command availability and add if present (upper)
        if self.has_erd_code(ErdCode.DISHWASHER_UPPER_REMOTE_START_ENABLE):
            upper_entities.extend(
                [
                    GeErdBinarySensor(self, ErdCode.DISHWASHER_UPPER_REMOTE_START_ENABLE, erd_override="upper_remote_command_enable", entity_category=EntityCategory.DIAGNOSTIC),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_UPPER_REMOTE_START_COMMAND, ErdRemoteCommand.START_RESUME, erd_override="upper_remote_command"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_UPPER_REMOTE_START_COMMAND, ErdRemoteCommand.PAUSE, erd_override="upper_remote_command"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_UPPER_REMOTE_START_COMMAND, ErdRemoteCommand.CANCEL, erd_override="upper_remote_command")
                ]
            )

        entities = base_entities + lower_entities + upper_entities
        return entities
        
