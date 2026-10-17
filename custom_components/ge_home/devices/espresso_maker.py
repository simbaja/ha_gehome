import logging
from typing import List

from homeassistant.const import EntityCategory, UnitOfMass, UnitOfTemperature, UnitOfTime, UnitOfVolume
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode,
    ErdApplianceType,
    ErdDataType
)

from .base import ApplianceApi
from ..entities import (
    GeErdBinarySensor,
    GeErdButton,
    GeErdSensor,
    GeErdPropertySensor,
    GeEspressoRangeNumber,
    GeEspressoDrinkNumber,
    GeEspressoWaterHardnessSelect
)

_LOGGER = logging.getLogger(__name__)

# (current ERD, requested ERD) for each drink's stored parameters
DRINK_PARAMETER_CODES = [
    (ErdCode.ESPRESSO_ESPRESSO_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_ESPRESSO_PARAMETERS),
    (ErdCode.ESPRESSO_AMERICANO_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_AMERICANO_PARAMETERS),
    (ErdCode.ESPRESSO_LUNGO_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_LUNGO_PARAMETERS),
    (ErdCode.ESPRESSO_HOT_WATER_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_HOT_WATER_PARAMETERS),
    (ErdCode.ESPRESSO_STEAM_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_STEAM_PARAMETERS),
    (ErdCode.ESPRESSO_RISTRETTO_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_RISTRETTO_PARAMETERS),
    (ErdCode.ESPRESSO_DOPPIO_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_DOPPIO_PARAMETERS),
    (ErdCode.ESPRESSO_TRIPLE_SHOT_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_TRIPLE_SHOT_PARAMETERS),
    (ErdCode.ESPRESSO_RED_EYE_PARAMETERS, ErdCode.ESPRESSO_REQUESTED_RED_EYE_PARAMETERS),
]

class EspressoMakerApi(ApplianceApi):
    """API class for Espresso Maker objects"""
    APPLIANCE_TYPE = ErdApplianceType.ESPRESSO_MAKER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        em_entities = [
            GeErdBinarySensor(self, ErdCode.CCM_IS_DESCALING, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdButton(self, ErdCode.CCM_CANCEL_DESCALING, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdButton(self, ErdCode.CCM_START_DESCALING, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.CCM_OUT_OF_WATER, device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),

            # status
            GeErdBinarySensor(self, ErdCode.ESPRESSO_IS_BREWING, device_class_override=BinarySensorDeviceClass.RUNNING),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_IS_EMPTYING, device_class_override=BinarySensorDeviceClass.RUNNING),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_EMPTY_WASTE_BIN, device_class_override=BinarySensorDeviceClass.PROBLEM),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_OUT_OF_BEANS, device_class_override=BinarySensorDeviceClass.PROBLEM),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_DESCALE_NEEDED, device_class_override=BinarySensorDeviceClass.PROBLEM),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_SERVICE_DOOR_OPEN, device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_GRIND_HOPPER_PRESENT, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_OVERPRESSURE_DETECTED, device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_GRINDER_BLOCKED, device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.ESPRESSO_GRINDER_OVERHEATED, device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.ESPRESSO_STEAM_KNOB_POSITION, icon_override="mdi:kettle-steam"),

            # current/last brew
            GeErdPropertySensor(self, ErdCode.ESPRESSO_CURRENT_BREW_PARAMETERS, "brew_type", erd_override="LAST", icon_override="mdi:coffee"),
            GeErdPropertySensor(self, ErdCode.ESPRESSO_CURRENT_BREW_PARAMETERS, "volume", erd_override="LAST", icon_override="mdi:cup", device_class_override=SensorDeviceClass.VOLUME, uom_override=UnitOfVolume.MILLILITERS, data_type_override=ErdDataType.INT, suggested_uom=UnitOfVolume.MILLILITERS, suggested_precision=0),
            GeErdPropertySensor(self, ErdCode.ESPRESSO_CURRENT_BREW_PARAMETERS, "temperature", erd_override="LAST", device_class_override=SensorDeviceClass.TEMPERATURE, uom_override=UnitOfTemperature.CELSIUS, data_type_override=ErdDataType.FLOAT, suggested_precision=0),
            GeErdPropertySensor(self, ErdCode.ESPRESSO_CURRENT_BREW_PARAMETERS, "grind_time", erd_override="LAST", icon_override="mdi:grain", device_class_override=SensorDeviceClass.DURATION, uom_override=UnitOfTime.SECONDS, data_type_override=ErdDataType.FLOAT),

            # maintenance and counters
            GeErdSensor(self, ErdCode.ESPRESSO_VOLUME_UNTIL_DESCALE, icon_override="mdi:water-sync", device_class_override=SensorDeviceClass.VOLUME, uom_override=UnitOfVolume.MILLILITERS, entity_category=EntityCategory.DIAGNOSTIC, suggested_uom=UnitOfVolume.LITERS, suggested_precision=1),
            GeErdSensor(self, ErdCode.ESPRESSO_LIFETIME_COFFEE_GROUND, icon_override="mdi:grain", suggested_precision=0, device_class_override=SensorDeviceClass.WEIGHT, state_class_override=SensorStateClass.TOTAL_INCREASING, uom_override=UnitOfMass.GRAMS, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.ESPRESSO_SUPPORTED_BREW_TYPES, entity_category=EntityCategory.DIAGNOSTIC),

            # settings
            GeEspressoWaterHardnessSelect(self),
            GeEspressoRangeNumber(self, ErdCode.ESPRESSO_STANDBY_TIMEOUT, ErdCode.ESPRESSO_REQUESTED_STANDBY_TIMEOUT, erd_override="STANDBY_TIMEOUT", icon_override="mdi:power-sleep", device_class_override=NumberDeviceClass.DURATION, uom_override=UnitOfTime.MINUTES, scale=60),
            GeEspressoRangeNumber(self, ErdCode.ESPRESSO_STEAM_DURATION, ErdCode.ESPRESSO_REQUESTED_STEAM_DURATION, erd_override="STEAM_DURATION", icon_override="mdi:kettle-steam", device_class_override=NumberDeviceClass.DURATION, uom_override=UnitOfTime.SECONDS),
        ]

        # rinse volume reports 0/0/0 when the machine doesn't support it
        rinse = self.try_get_erd_value(ErdCode.ESPRESSO_RINSE_VOLUME)
        if rinse is None or rinse.max > 0:
            em_entities.append(GeEspressoRangeNumber(self, ErdCode.ESPRESSO_RINSE_VOLUME, ErdCode.ESPRESSO_REQUESTED_RINSE_VOLUME, erd_override="RINSE_VOLUME", icon_override="mdi:water", device_class_override=NumberDeviceClass.VOLUME, uom_override=UnitOfVolume.MILLILITERS))

        for current, requested in DRINK_PARAMETER_CODES:
            for field in ("temperature", "volume", "grind_time"):
                if GeEspressoDrinkNumber.has_range(self, current, field):
                    em_entities.append(GeEspressoDrinkNumber(self, current, requested, field))

        entities = base_entities + em_entities
        return entities
