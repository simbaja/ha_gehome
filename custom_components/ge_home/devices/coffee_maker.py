import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import (
    GeAppliance,
    ErdCode, 
    ErdApplianceType,
    ErdCcmBrewSettings
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import ApplianceApi
from ..entities import (
    GeCcmPotNotPresentBinarySensor,
    GeErdSensor, 
    GeErdBinarySensor,
    GeErdButton,
    GeCcmBrewStrengthSelect,
    GeCcmBrewTemperatureNumber,
    GeCcmBrewCupsNumber,
    GeCcmBrewSettingsButton
)

_LOGGER = logging.getLogger(__name__)


class CcmApi(ApplianceApi):
    """API class for Cafe Coffee Maker objects"""
    APPLIANCE_TYPE = ErdApplianceType.CAFE_COFFEE_MAKER

    def __init__(self, coordinator: DataUpdateCoordinator, appliance: GeAppliance):
        super().__init__(coordinator, appliance)

        self._brew_strengh_entity = GeCcmBrewStrengthSelect(self)
        self._brew_temperature_entity = GeCcmBrewTemperatureNumber(self)
        self._brew_cups_entity = GeCcmBrewCupsNumber(self)

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        ccm_entities = [
            GeErdBinarySensor(self, ErdCode.CCM_IS_BREWING),                      
            GeErdBinarySensor(self, ErdCode.CCM_IS_DESCALING),
            GeCcmBrewSettingsButton(self),
            GeErdButton(self, ErdCode.CCM_CANCEL_DESCALING),
            GeErdButton(self, ErdCode.CCM_START_DESCALING),
            GeErdButton(self, ErdCode.CCM_CANCEL_BREWING),
            self._brew_strengh_entity,
            self._brew_temperature_entity,
            self._brew_cups_entity,
            GeErdSensor(self, ErdCode.CCM_CURRENT_WATER_TEMPERATURE),
            GeErdBinarySensor(self, ErdCode.CCM_OUT_OF_WATER, device_class_override="problem"),
            GeCcmPotNotPresentBinarySensor(self, ErdCode.CCM_POT_PRESENT, device_class_override="problem")
        ]

        entities = base_entities + ccm_entities
        return entities

    async def start_brewing(self) -> None:
        """Aggregate brew settings and start brewing."""

        new_mode = ErdCcmBrewSettings(self._brew_cups_entity.native_value,
                                      self._brew_strengh_entity.brew_strength,
                                      self._brew_temperature_entity.native_value)
        await self.appliance.async_set_erd_value(ErdCode.CCM_BREW_SETTINGS, new_mode)