import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk.erd import ErdCode, ErdApplianceType

from .base import ApplianceApi
from ..entities import GeErdSensor, GeErdBinarySensor, GeErdPropertySensor

_LOGGER = logging.getLogger(__name__)


class DualDishwasherApi(ApplianceApi):
    """API class for dual dishwasher objects"""
    APPLIANCE_TYPE = ErdApplianceType.DISH_WASHER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        lower_entities = [
            GeErdSensor(self, ErdCode.DISHWASHER_CYCLE_STATE, erd_override="lower_cycle_state", icon_override="mdi:state-machine"),
            GeErdSensor(self, ErdCode.DISHWASHER_TIME_REMAINING, erd_override="lower_time_remaining"),
            GeErdBinarySensor(self, ErdCode.DISHWASHER_DOOR_STATUS, erd_override="lower_door_status"),

            #Reminders
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "add_rinse_aid", erd_override="lower_reminder", icon_override="mdi:shimmer"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "clean_filter", erd_override="lower_reminder", icon_override="mdi:dishwasher-alert"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_REMINDERS, "sanitized", erd_override="lower_reminder", icon_override="mdi:silverware-clean"),

            #User Setttings
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "mute", erd_override="lower_setting", icon_override="mdi:volume-mute"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "lock_control", erd_override="lower_setting", icon_override="mdi:lock"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "sabbath", erd_override="lower_setting", icon_override="mdi:star-david"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "cycle_mode", erd_override="lower_setting", icon_override="mdi:state-machine"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "presoak", erd_override="lower_setting", icon_override="mdi:water"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "bottle_jet", erd_override="lower_setting", icon_override="mdi:bottle-tonic-outline"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "wash_temp", erd_override="lower_setting", icon_override="mdi:coolant-temperature"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "rinse_aid", erd_override="lower_setting", icon_override="mdi:shimmer"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "dry_option", erd_override="lower_setting", icon_override="mdi:fan"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "wash_zone", erd_override="lower_setting", icon_override="mdi:dock-top"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_USER_SETTING, "delay_hours", erd_override="lower_setting", icon_override="mdi:clock-fast")
        ]

        upper_entities = [
            #GeDishwasherControlLockedSwitch(self, ErdCode.USER_INTERFACE_LOCKED),
            GeErdSensor(self, ErdCode.DISHWASHER_UPPER_CYCLE_STATE, erd_override="upper_cycle_state", icon_override="mdi:state-machine"),
            GeErdSensor(self, ErdCode.DISHWASHER_UPPER_TIME_REMAINING, erd_override="upper_time_remaining"),
            GeErdBinarySensor(self, ErdCode.DISHWASHER_UPPER_DOOR_STATUS, erd_override="upper_door_status"),

            #Reminders
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_REMINDERS, "add_rinse_aid", erd_override="upper_reminder", icon_override="mdi:shimmer"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_REMINDERS, "clean_filter", erd_override="upper_reminder", icon_override="mdi:dishwasher-alert"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_REMINDERS, "sanitized", erd_override="upper_reminder", icon_override="mdi:silverware-clean"),

            #User Setttings
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "mute", erd_override="upper_setting", icon_override="mdi:volume-mute"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "lock_control", erd_override="upper_setting", icon_override="mdi:lock"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "sabbath", erd_override="upper_setting", icon_override="mdi:star-david"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "cycle_mode", erd_override="upper_setting", icon_override="mdi:state-machine"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "presoak", erd_override="upper_setting", icon_override="mdi:water"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "bottle_jet", erd_override="upper_setting", icon_override="mdi:bottle-tonic-outline"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "wash_temp", erd_override="upper_setting", icon_override="mdi:coolant-temperature"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "rinse_aid", erd_override="upper_setting", icon_override="mdi:shimmer"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "dry_option", erd_override="upper_setting", icon_override="mdi:fan"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "wash_zone", erd_override="upper_setting", icon_override="mdi:dock-top"),
            GeErdPropertySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "delay_hours", erd_override="upper_setting", icon_override="mdi:clock-fast")
        ]

        entities = base_entities + lower_entities + upper_entities
        return entities
        
