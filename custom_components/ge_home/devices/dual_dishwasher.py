import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType, ErdRemoteCommand, ErdBrand

from .base import ApplianceApi
from ..entities import GeErdSensor, GeErdBinarySensor, GeErdPropertySensor, GeErdPropertyBinarySensor, GeDishwasherCommandButton, GeDishwasherProgramSelect, GeDishwasherModifierSelect

_LOGGER = logging.getLogger(__name__)


class DualDishwasherApi(ApplianceApi):
    """API class for dual dishwasher objects"""
    APPLIANCE_TYPE = ErdApplianceType.DUAL_DISH_WASHER

    def _is_fisher_paykel(self) -> bool:
        """True for Fisher & Paykel (incl. rebadged) dual DishDrawers.

        The wash-modifier registers and the program low-byte map were confirmed only on F&P hardware,
        and the program selector writes using that F&P-specific map — so F&P-specific entities are
        gated on the brand ERD (0x0099) rather than assuming every DUAL_DISH_WASHER is an F&P unit.
        """
        return self.try_get_erd_value(ErdCode.BRAND) == ErdBrand.FISHER_PAYKEL

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

        # Status/diagnostics reported by F&P duals (e.g. DDD196US) that the SDK already decodes.
        # Guarded since not every dual dishwasher reports them.
        if self.has_erd_code(ErdCode.DISHWASHER_IS_CLEAN):
            lower_entities.append(
                GeErdBinarySensor(self, ErdCode.DISHWASHER_IS_CLEAN, erd_override="lower_is_clean")
            )
        if self.has_erd_code(ErdCode.DISHWASHER_ERROR):
            lower_entities.append(
                GeErdSensor(self, ErdCode.DISHWASHER_ERROR, erd_override="lower_error", entity_category=EntityCategory.DIAGNOSTIC)
            )
        if self.has_erd_code(ErdCode.DISHWASHER_CYCLE_COUNTS):
            lower_entities.extend(
                [
                    GeErdPropertySensor(self, ErdCode.DISHWASHER_CYCLE_COUNTS, "started", erd_override="lower_cycle_counts", icon_override="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC),
                    GeErdPropertySensor(self, ErdCode.DISHWASHER_CYCLE_COUNTS, "completed", erd_override="lower_cycle_counts", icon_override="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC),
                    GeErdPropertySensor(self, ErdCode.DISHWASHER_CYCLE_COUNTS, "reset", erd_override="lower_cycle_counts", icon_override="mdi:counter", entity_category=EntityCategory.DIAGNOSTIC)
                ]
            )

        # The upper tub reports the same status ERDs at (lower + 0x0200), but the SDK has no converters
        # for them yet, so they decode as raw bytes.  Exposed read-only as diagnostics to confirm the
        # mapping (payload shapes match their lower counterparts exactly).
        for upper_code, name in (
            (ErdCode.DISHWASHER_UPPER_UNKNOWN_3208, "upper_error_raw"),
            (ErdCode.DISHWASHER_UPPER_UNKNOWN_3209, "upper_cycle_counts_raw"),
            ("0xD203", "upper_is_clean_raw"),
        ):
            if self.has_erd_code(upper_code):
                upper_entities.append(
                    GeErdSensor(self, upper_code, erd_override=name, entity_category=EntityCategory.DIAGNOSTIC)
                )

        # Fisher & Paykel-specific decoding.  The wash-modifier registers and the program low-byte map
        # were ground-truthed only on an F&P dual DishDrawer (DDD196US), and the program selector *writes*
        # using that F&P map — so gate all of it on the brand.  Other brands that happen to enumerate as
        # DUAL_DISH_WASHER keep the generic read-only entities above and skip this block.
        if self._is_fisher_paykel():
            # Wash modifier (None / Extra Dry / Quick / Sanitize).  The SDK reports these ERDs as
            # "unknown", so we read/write the raw byte locally.  Both registers confirmed by labeled live
            # capture 2026-07-23 (0x40=Extra Dry, 0x02=Quick, 0x04=Sanitize, 0x00=None); cloud writes were
            # verified to hold AND light the physical panel.  NOTE the two tubs use ASYMMETRIC codes (not
            # the usual +0x0200): upper=0x3222, lower=0x3086.  As a select this both shows and sets it.
            if self.has_erd_code(ErdCode.DISHWASHER_UPPER_UNKNOWN_3222):
                upper_entities.append(
                    GeDishwasherModifierSelect(self, ErdCode.DISHWASHER_UPPER_UNKNOWN_3222, erd_override="upper_wash_modifier", icon_override="mdi:tune-variant")
                )
            if self.has_erd_code(ErdCode.DISHWASHER_UNKNOWN_3086):
                lower_entities.append(
                    GeDishwasherModifierSelect(self, ErdCode.DISHWASHER_UNKNOWN_3086, erd_override="lower_wash_modifier", icon_override="mdi:tune-variant")
                )

            # Wash-program selector per tub.  The program is the low byte (mask 0x1E) of the user-setting
            # word; GeDishwasherProgramSelect read-modify-writes just those bits (raw write, preserving
            # co-located fields) rather than round-tripping the whole struct through the GE encoder.
            # Write control was verified live on a DDD196US 2026-07-23 (Medium->Eco held and recomputed).
            if self.has_erd_code(ErdCode.DISHWASHER_USER_SETTING):
                lower_entities.append(
                    GeDishwasherProgramSelect(self, ErdCode.DISHWASHER_USER_SETTING, erd_override="lower_program", icon_override="mdi:dishwasher")
                )
            if self.has_erd_code(ErdCode.DISHWASHER_UPPER_USER_SETTING):
                upper_entities.append(
                    GeDishwasherProgramSelect(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, erd_override="upper_program", icon_override="mdi:dishwasher")
                )

        # Remote commands are always supported, enabled by a physical button per tub, disabled when the tub is opened (lower)
        if True:
            lower_entities.extend(
                [
                    GeErdPropertyBinarySensor(self, ErdCode.DISHWASHER_USER_SETTING, "wifi_enabled", erd_override="lower_remote_command_enable", icon_off_override="mdi:wifi-off", icon_on_override="mdi:wifi"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.START_RESUME, erd_override="lower_remote_command"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.PAUSE, erd_override="lower_remote_command"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_REMOTE_START_COMMAND, ErdRemoteCommand.CANCEL, erd_override="lower_remote_command")
                ]
            )

        # Remote commands are always supported, enabled by a physical button per tub, disabled when the tub is opened (upper)
        if True:
            upper_entities.extend(
                [
                    GeErdPropertyBinarySensor(self, ErdCode.DISHWASHER_UPPER_USER_SETTING, "wifi_enabled", erd_override="upper_remote_command_enable", icon_off_override="mdi:wifi-off", icon_on_override="mdi:wifi"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_UPPER_REMOTE_START_COMMAND, ErdRemoteCommand.START_RESUME, erd_override="upper_remote_command"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_UPPER_REMOTE_START_COMMAND, ErdRemoteCommand.PAUSE, erd_override="upper_remote_command"),
                    GeDishwasherCommandButton(self, ErdCode.DISHWASHER_UPPER_REMOTE_START_COMMAND, ErdRemoteCommand.CANCEL, erd_override="upper_remote_command")
                ]
            )

        entities = base_entities + lower_entities + upper_entities
        return entities
        
