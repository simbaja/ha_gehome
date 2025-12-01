from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode,
    ErdApplianceType,
    ErdOnOff,
    ErdHotWaterStatus,
    FridgeIceBucketStatus,
    IceMakerControlStatus,
    ErdFilterStatus,
    HotWaterStatus,
    FridgeModelInfo,
    ErdConvertableDrawerMode,
    ErdDataType
)

from .base import ApplianceApi
# This block is now split to import from the correct sub-folders
from ..entities import (
    ErdOnOffBoolConverter,
    GeErdSensor,
    GeErdBinarySensor,
    GeErdSwitch,
    GeErdSelect,
    GeErdLight,
    GeErdPropertySensor,
    GeErdPropertyBinarySensor
)
from ..entities.fridge import (
    GeFridge,
    GeFreezer,
    GeDispenser,
    ConvertableDrawerModeOptionsConverter,
    GeFridgeIceControlSwitch,
    GeKCupSwitch
)


_LOGGER = logging.getLogger(__name__)

class FridgeApi(ApplianceApi):
    """API class for fridge objects"""
    APPLIANCE_TYPE = ErdApplianceType.FRIDGE

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        fridge_entities: List[Entity] = []
        freezer_entities: List[Entity] = []
        dispenser_entities: List[Entity] = []

        # Get the statuses used to determine presence

        ice_maker_control: IceMakerControlStatus | None = self.try_get_erd_value(ErdCode.ICE_MAKER_CONTROL)
        ice_bucket_status: FridgeIceBucketStatus | None = self.try_get_erd_value(ErdCode.ICE_MAKER_BUCKET_STATUS)
        water_filter: ErdFilterStatus | None = self.try_get_erd_value(ErdCode.WATER_FILTER_STATUS)
        air_filter: ErdFilterStatus | None = self.try_get_erd_value(ErdCode.AIR_FILTER_STATUS)
        hot_water_status: HotWaterStatus | None = self.try_get_erd_value(ErdCode.HOT_WATER_STATUS)
        fridge_model_info: FridgeModelInfo | None = self.try_get_erd_value(ErdCode.FRIDGE_MODEL_INFO)
        convertable_drawer: ErdConvertableDrawerMode | None = self.try_get_erd_value(ErdCode.CONVERTABLE_DRAWER_MODE)

        interior_light: int | None = self.try_get_erd_value(ErdCode.INTERIOR_LIGHT)
        proximity_light: ErdOnOff | None = self.try_get_erd_value(ErdCode.PROXIMITY_LIGHT)
        display_mode: ErdOnOff | None = self.try_get_erd_value(ErdCode.DISPLAY_MODE)
        lockout_mode: ErdOnOff | None = self.try_get_erd_value(ErdCode.LOCKOUT_MODE)
        turbo_cool: ErdOnOff | None = self.try_get_erd_value(ErdCode.TURBO_COOL_STATUS)
        turbo_freeze: ErdOnOff | None = self.try_get_erd_value(ErdCode.TURBO_FREEZE_STATUS)
        ice_boost: ErdOnOff | None = self.try_get_erd_value(ErdCode.FRIDGE_ICE_BOOST)

        units = self.hass.config.units

        # Common entities
        common_entities = [
            GeErdSensor(self, ErdCode.FRIDGE_MODEL_INFO, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.DOOR_STATUS, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdPropertyBinarySensor(self, ErdCode.DOOR_STATUS, "any_open", entity_category=EntityCategory.DIAGNOSTIC)
        ]
        if(ice_bucket_status and (ice_bucket_status.is_present_fridge or ice_bucket_status.is_present_freezer)):
            common_entities.append(GeErdSensor(self, ErdCode.ICE_MAKER_BUCKET_STATUS, entity_category=EntityCategory.DIAGNOSTIC))

        # Fridge entities
        if fridge_model_info is None or fridge_model_info.has_fridge:
            fridge_entities.extend([
                GeErdPropertySensor(self, ErdCode.CURRENT_TEMPERATURE, "fridge"),
                GeFridge(self),
            ])
            if turbo_cool is not None:
                fridge_entities.append(GeErdSwitch(self, ErdCode.FRIDGE_ICE_BOOST, entity_category=EntityCategory.CONFIG))
            if(ice_maker_control and ice_maker_control.status_fridge != ErdOnOff.NA):
                fridge_entities.append(GeErdPropertyBinarySensor(self, ErdCode.ICE_MAKER_CONTROL, "status_fridge", entity_category=EntityCategory.DIAGNOSTIC))
                fridge_entities.append(GeFridgeIceControlSwitch(self, "fridge"))
            if(water_filter and water_filter != ErdFilterStatus.NA):
                fridge_entities.append(GeErdSensor(self, ErdCode.WATER_FILTER_STATUS, entity_category=EntityCategory.DIAGNOSTIC))
            if(air_filter and air_filter != ErdFilterStatus.NA):
                fridge_entities.append(GeErdSensor(self, ErdCode.AIR_FILTER_STATUS, entity_category=EntityCategory.DIAGNOSTIC))
            if(ice_bucket_status and ice_bucket_status.is_present_fridge):
                fridge_entities.append(GeErdPropertySensor(self, ErdCode.ICE_MAKER_BUCKET_STATUS, "state_full_fridge", entity_category=EntityCategory.DIAGNOSTIC))
            if(interior_light and interior_light != 255):
                fridge_entities.append(GeErdLight(self, ErdCode.INTERIOR_LIGHT, entity_category=EntityCategory.CONFIG))
            if(proximity_light and proximity_light != ErdOnOff.NA):
                fridge_entities.append(GeErdSwitch(self, ErdCode.PROXIMITY_LIGHT, ErdOnOffBoolConverter(), icon_on_override="mdi:lightbulb-on", icon_off_override="mdi:lightbulb", entity_category=EntityCategory.CONFIG))
            if(convertable_drawer and convertable_drawer != ErdConvertableDrawerMode.NA):
                fridge_entities.append(GeErdSelect(self, ErdCode.CONVERTABLE_DRAWER_MODE, ConvertableDrawerModeOptionsConverter(units), entity_category=EntityCategory.CONFIG))
            if(display_mode and display_mode != ErdOnOff.NA):
                fridge_entities.append(GeErdSwitch(self, ErdCode.DISPLAY_MODE, ErdOnOffBoolConverter(), icon_on_override="mdi:lightbulb-on", icon_off_override="mdi:lightbulb", entity_category=EntityCategory.CONFIG))
            if(lockout_mode and lockout_mode != ErdOnOff.NA):
                fridge_entities.append(GeErdSwitch(self, ErdCode.LOCKOUT_MODE, ErdOnOffBoolConverter(), icon_on_override="mdi:lock", icon_off_override="mdi:lock-open", entity_category=EntityCategory.CONFIG))

        # Freezer entities
        if fridge_model_info is None or fridge_model_info.has_freezer:
            freezer_entities.extend([
                GeErdPropertySensor(self, ErdCode.CURRENT_TEMPERATURE, "freezer"),
                GeFreezer(self),
            ])
            if turbo_freeze is not None:
                freezer_entities.append(GeErdSwitch(self, ErdCode.TURBO_FREEZE_STATUS, entity_category=EntityCategory.CONFIG))
            if ice_boost is not None:
                freezer_entities.append(GeErdSwitch(self, ErdCode.FRIDGE_ICE_BOOST, entity_category=EntityCategory.CONFIG))
            if(ice_maker_control and ice_maker_control.status_freezer != ErdOnOff.NA):
                freezer_entities.append(GeErdPropertyBinarySensor(self, ErdCode.ICE_MAKER_CONTROL, "status_freezer", entity_category=EntityCategory.DIAGNOSTIC))
                freezer_entities.append(GeFridgeIceControlSwitch(self, "freezer"))
            if(ice_bucket_status and ice_bucket_status.is_present_freezer):
                freezer_entities.append(GeErdPropertySensor(self, ErdCode.ICE_MAKER_BUCKET_STATUS, "state_full_freezer", entity_category=EntityCategory.DIAGNOSTIC))

        # Dispenser entities
        if(hot_water_status and hot_water_status.status != ErdHotWaterStatus.NA):
            dispenser_entities.extend([
                GeErdBinarySensor(self, ErdCode.HOT_WATER_IN_USE, entity_category=EntityCategory.DIAGNOSTIC),
                GeErdSensor(self, ErdCode.HOT_WATER_SET_TEMP, entity_category=EntityCategory.DIAGNOSTIC),
                GeErdPropertySensor(self, ErdCode.HOT_WATER_STATUS, "status", icon_override="mdi:information-outline", entity_category=EntityCategory.DIAGNOSTIC),
                GeErdPropertySensor(self, ErdCode.HOT_WATER_STATUS, "time_until_ready", icon_override="mdi:timer-outline", entity_category=EntityCategory.DIAGNOSTIC),
                GeErdPropertySensor(self, ErdCode.HOT_WATER_STATUS, "current_temp", device_class_override=SensorDeviceClass.TEMPERATURE, data_type_override=ErdDataType.INT, entity_category=EntityCategory.DIAGNOSTIC),
                GeErdPropertyBinarySensor(self, ErdCode.HOT_WATER_STATUS, "faulted", device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
                GeDispenser(self),
                GeKCupSwitch(self)
            ])

        entities = base_entities + common_entities + fridge_entities + freezer_entities + dispenser_entities
        return entities