import logging
from typing import List

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory
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
    GeCcmBrewSettingsButton,
    GeCcmGrinderSwitch,
    GeCcmBrewBasketMissingBinarySensor,
    GeCcmCleanBrewBasketBinarySensor,
    GeCcmGrinderMissingBinarySensor,
)

_LOGGER = logging.getLogger(__name__)


class CcmApi(ApplianceApi):
    """API class for Cafe Coffee Maker objects"""
    APPLIANCE_TYPE = ErdApplianceType.CAFE_COFFEE_MAKER

    def __init__(self, coordinator: DataUpdateCoordinator, appliance: GeAppliance):
        super().__init__(coordinator, appliance)

        # These cached entities are used by start_brewing(). They are only
        # created when the appliance actually reports the corresponding ERD
        # codes, so that models like the Speciality Grind and Brew (which lack
        # the standard CCM_BREW_TEMPERATURE / CCM_BREW_STRENGTH / CCM_BREW_CUPS
        # codes) don't crash during initialization.
        self._brew_strengh_entity = None
        self._brew_temperature_entity = None
        self._brew_cups_entity = None

        if self.has_erd_code(ErdCode.CCM_BREW_STRENGTH):
            self._brew_strengh_entity = GeCcmBrewStrengthSelect(self)
        if self.has_erd_code(ErdCode.CCM_BREW_TEMPERATURE):
            self._brew_temperature_entity = GeCcmBrewTemperatureNumber(self)
        if self.has_erd_code(ErdCode.CCM_BREW_CUPS):
            self._brew_cups_entity = GeCcmBrewCupsNumber(self)

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        ccm_entities = [
            GeErdBinarySensor(self, ErdCode.CCM_IS_BREWING, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdBinarySensor(self, ErdCode.CCM_OUT_OF_WATER, device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
            GeCcmPotNotPresentBinarySensor(self, ErdCode.CCM_POT_PRESENT, device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
        ]

        # Standard coffee maker entities — only add if the appliance reports
        # the corresponding ERD code.  The Grind and Brew does not have these.
        if self._brew_strengh_entity is not None:
            ccm_entities.append(self._brew_strengh_entity)
        if self._brew_temperature_entity is not None:
            ccm_entities.append(self._brew_temperature_entity)
        if self._brew_cups_entity is not None:
            ccm_entities.append(self._brew_cups_entity)

        if self.has_erd_code(ErdCode.CCM_BREW_SETTINGS):
            ccm_entities.append(GeCcmBrewSettingsButton(self))
        if self.has_erd_code(ErdCode.CCM_CANCEL_BREWING):
            ccm_entities.append(GeErdButton(self, ErdCode.CCM_CANCEL_BREWING))
        if self.has_erd_code(ErdCode.CCM_IS_DESCALING):
            ccm_entities.append(GeErdBinarySensor(self, ErdCode.CCM_IS_DESCALING, entity_category=EntityCategory.DIAGNOSTIC))
        if self.has_erd_code(ErdCode.CCM_START_DESCALING):
            ccm_entities.append(GeErdButton(self, ErdCode.CCM_START_DESCALING, entity_category=EntityCategory.CONFIG))
        if self.has_erd_code(ErdCode.CCM_CANCEL_DESCALING):
            ccm_entities.append(GeErdButton(self, ErdCode.CCM_CANCEL_DESCALING, entity_category=EntityCategory.CONFIG))
        if self.has_erd_code(ErdCode.CCM_CURRENT_WATER_TEMPERATURE):
            ccm_entities.append(GeErdSensor(self, ErdCode.CCM_CURRENT_WATER_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC))

        # Grind and Brew specific entities (raw ERD codes not in the SDK)
        ccm_entities.append(GeCcmGrinderSwitch(self))
        ccm_entities.append(GeCcmBrewBasketMissingBinarySensor(self))
        ccm_entities.append(GeCcmCleanBrewBasketBinarySensor(self))
        ccm_entities.append(GeCcmGrinderMissingBinarySensor(self))

        entities = base_entities + ccm_entities
        return entities

    async def start_brewing(self) -> None:
        """Aggregate brew settings and start brewing."""

        if self._brew_cups_entity is None or self._brew_strengh_entity is None or self._brew_temperature_entity is None:
            _LOGGER.warning("Cannot start brewing: brew settings entities not available for this model")
            return

        new_mode = ErdCcmBrewSettings(self._brew_cups_entity.native_value,
                                      self._brew_strengh_entity.brew_strength,
                                      self._brew_temperature_entity.native_value)
        await self.appliance.async_set_erd_value(ErdCode.CCM_BREW_SETTINGS, new_mode)
