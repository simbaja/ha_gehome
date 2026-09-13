import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode,
    ErdApplianceType,
    ErdOnOff,
    ErdWaterHeaterMixingValveTankCapacity
)

from custom_components.ge_home.entities.water_heater.ge_water_heater import GeWaterHeater

from .base import ApplianceApi
from ..entities import (
    GeErdSensor,
    GeErdSwitch,
    GeErdSelect,
    GeErdPropertyBinarySensor,
    ErdOnOffBoolConverter,
    MixingValveTankCapacityOptionsConverter
)

_LOGGER = logging.getLogger(__name__)


class WaterHeaterApi(ApplianceApi):
    """API class for Water Heater objects"""
    APPLIANCE_TYPE = ErdApplianceType.WATER_HEATER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        boost_mode: ErdOnOff | None = self.try_get_erd_value(ErdCode.WH_HEATER_BOOST_STATE)
        active: ErdOnOff | None = self.try_get_erd_value(ErdCode.WH_HEATER_ACTIVE_STATE)
        mixing_valve_capacity: ErdWaterHeaterMixingValveTankCapacity | None = self.try_get_erd_value(ErdCode.WH_HEATER_MIXING_VALVE_TANK_CAPACITY)
        mixing_valve_available_capacities = self.try_get_erd_value(ErdCode.WH_HEATER_MIXING_VALVE_AVAILABLE_TANK_CAPACITIES)
        anode_rod_remaining = self.try_get_erd_value(ErdCode.WH_HEATER_ANODE_ROD_REMAINING)
        time_to_temperature = self.try_get_erd_value(ErdCode.WH_HEATER_TIME_TO_TEMPERATURE)
        hot_water_remaining = self.try_get_erd_value(ErdCode.WH_HEATER_HOT_WATER_REMAINING)

        wh_entities = [
            GeErdSensor(self, ErdCode.WH_HEATER_TARGET_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.WH_HEATER_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.WH_HEATER_MODE_HOURS_REMAINING, entity_category=EntityCategory.DIAGNOSTIC, suggested_uom="h"),
            GeErdSensor(self, ErdCode.WH_HEATER_ELECTRIC_MODE_MAX_TIME, entity_category=EntityCategory.DIAGNOSTIC, suggested_uom="h"),
            GeErdSensor(self, ErdCode.WH_HEATER_VACATION_MODE_MAX_TIME, entity_category=EntityCategory.DIAGNOSTIC, suggested_uom="h"),
            GeWaterHeater(self)
        ]

        if(boost_mode and boost_mode != ErdOnOff.NA):
            wh_entities.append(GeErdSwitch(self, ErdCode.WH_HEATER_BOOST_STATE, ErdOnOffBoolConverter(), icon_on_override="mdi:rocket-launch", icon_off_override="mdi:rocket-launch-outline", control_erd_code=ErdCode.WH_HEATER_BOOST_CONTROL, entity_category=EntityCategory.CONFIG))

        if(active and active != ErdOnOff.NA):
            wh_entities.append(GeErdSwitch(self, ErdCode.WH_HEATER_ACTIVE_STATE, ErdOnOffBoolConverter(), icon_on_override="mdi:power", icon_off_override="mdi:power-standby", control_erd_code=ErdCode.WH_HEATER_ACTIVE_CONTROL, entity_category=EntityCategory.CONFIG))

        if(mixing_valve_capacity and mixing_valve_capacity != ErdWaterHeaterMixingValveTankCapacity.UNKNOWN):
            wh_entities.append(GeErdSelect(self, ErdCode.WH_HEATER_MIXING_VALVE_TANK_CAPACITY, MixingValveTankCapacityOptionsConverter(), icon_override="mdi:water-thermometer", entity_category=EntityCategory.CONFIG))

        if(mixing_valve_available_capacities is not None):
            wh_entities.append(GeErdPropertyBinarySensor(self, ErdCode.WH_HEATER_MIXING_VALVE_AVAILABLE_TANK_CAPACITIES, "has_normal", icon_on_override="mdi:water-thermometer", entity_category=EntityCategory.DIAGNOSTIC))
            wh_entities.append(GeErdPropertyBinarySensor(self, ErdCode.WH_HEATER_MIXING_VALVE_AVAILABLE_TANK_CAPACITIES, "has_high", icon_on_override="mdi:water-thermometer", entity_category=EntityCategory.DIAGNOSTIC))
            wh_entities.append(GeErdPropertyBinarySensor(self, ErdCode.WH_HEATER_MIXING_VALVE_AVAILABLE_TANK_CAPACITIES, "has_x_high", icon_on_override="mdi:water-thermometer", entity_category=EntityCategory.DIAGNOSTIC))

        if(anode_rod_remaining is not None):
            wh_entities.append(GeErdSensor(self, ErdCode.WH_HEATER_ANODE_ROD_REMAINING, icon_override="mdi:magnet", entity_category=EntityCategory.DIAGNOSTIC))

        if(time_to_temperature is not None):
            wh_entities.append(GeErdSensor(self, ErdCode.WH_HEATER_TIME_TO_TEMPERATURE, icon_override="mdi:timer-sand", entity_category=EntityCategory.DIAGNOSTIC, suggested_uom="min"))

        if(hot_water_remaining is not None):
            wh_entities.append(GeErdSensor(self, ErdCode.WH_HEATER_HOT_WATER_REMAINING, icon_override="mdi:water", entity_category=EntityCategory.DIAGNOSTIC))

        entities = base_entities + wh_entities
        return entities
        
