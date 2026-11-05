import logging
from typing import List, Optional

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
    GeCcmGrindBrewStrengthSelect,
    GeCcmGrindBrewTemperatureNumber,
    GeCcmGrindBrewCupsNumber,
    GeCcmGrindBrewStartButton,
)

_LOGGER = logging.getLogger(__name__)

ERD_CCM_GRIND_BREW_SETTINGS = "0x9051"


class CcmApi(ApplianceApi):
    """API class for Cafe Coffee Maker objects"""
    APPLIANCE_TYPE = ErdApplianceType.CAFE_COFFEE_MAKER

    def __init__(self, coordinator: DataUpdateCoordinator, appliance: GeAppliance):
        super().__init__(coordinator, appliance)

        # Standard coffee maker entities (3-byte brew settings at 0x900b).
        # Only created when the appliance reports the corresponding ERD codes.
        self._brew_strengh_entity = None
        self._brew_temperature_entity = None
        self._brew_cups_entity = None

        # Grind and Brew entities (12-byte adhoc brew settings at 0x9051).
        # Only created when 0x9051 is present and the standard codes are absent.
        self._grind_brew_strength_entity = None
        self._grind_brew_temperature_entity = None
        self._grind_brew_cups_entity = None

        is_grind_and_brew = self.has_erd_code(ERD_CCM_GRIND_BREW_SETTINGS)

        if self.has_erd_code(ErdCode.CCM_BREW_STRENGTH):
            self._brew_strengh_entity = GeCcmBrewStrengthSelect(self)
        if self.has_erd_code(ErdCode.CCM_BREW_TEMPERATURE):
            self._brew_temperature_entity = GeCcmBrewTemperatureNumber(self)
        if self.has_erd_code(ErdCode.CCM_BREW_CUPS):
            self._brew_cups_entity = GeCcmBrewCupsNumber(self)

        if is_grind_and_brew:
            self._grind_brew_strength_entity = GeCcmGrindBrewStrengthSelect(self)
            self._grind_brew_temperature_entity = GeCcmGrindBrewTemperatureNumber(self)
            self._grind_brew_cups_entity = GeCcmGrindBrewCupsNumber(self)

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

        # Grind and Brew brew control entities (12-byte adhoc settings at 0x9051)
        if self._grind_brew_strength_entity is not None:
            ccm_entities.append(self._grind_brew_strength_entity)
            ccm_entities.append(self._grind_brew_temperature_entity)
            ccm_entities.append(self._grind_brew_cups_entity)
            ccm_entities.append(GeCcmGrindBrewStartButton(self))

        entities = base_entities + ccm_entities
        return entities

    async def start_brewing(self) -> None:
        """Aggregate brew settings and start brewing.

        For standard coffee makers, this writes a 3-byte ErdCcmBrewSettings
        to ERD 0x900b.  For the Grind and Brew, this assembles a 12-byte
        payload from the strength/temperature/cups entities and writes it
        to ERD 0x9051, preserving existing toggle/bloom bytes from the
        current device value.
        """
        if self._brew_cups_entity is not None and self._brew_strengh_entity is not None and self._brew_temperature_entity is not None:
            new_mode = ErdCcmBrewSettings(self._brew_cups_entity.native_value,
                                          self._brew_strengh_entity.brew_strength,
                                          self._brew_temperature_entity.native_value)
            await self.appliance.async_set_erd_value(ErdCode.CCM_BREW_SETTINGS, new_mode)
        elif self._grind_brew_strength_entity is not None:
            await self._start_grind_brew()
        else:
            _LOGGER.warning("Cannot start brewing: brew settings entities not available for this model")

    async def _start_grind_brew(self) -> None:
        """Assemble the 12-byte adhoc brew settings and write to 0x9051."""
        try:
            current_raw = self.appliance.get_erd_value(ERD_CCM_GRIND_BREW_SETTINGS)
        except KeyError:
            current_raw = None

        # Start from current device bytes to preserve toggle/bloom settings,
        # or default to a sensible payload if no current value exists.
        if isinstance(current_raw, (bytes, bytearray)) and len(current_raw) >= 12:
            payload = bytearray(current_raw[:12])
        else:
            # Default: gold off, bloom off, single off, medium, 200°F,
            # 10 oz, 6 cups, no bloom time
            payload = bytearray(b'\x00\x00\x00\x00\x01\xc8\x0a\x06\x00\x00\x00\x00')

        # Overwrite the bytes we control
        payload[4] = self._grind_brew_strength_entity.brew_strength_index
        payload[5] = int(self._grind_brew_temperature_entity.native_value or 200)
        # Derive ounces from cups (8 oz/cup is a reasonable default)
        cups = int(self._grind_brew_cups_entity.native_value or 6)
        payload[6] = cups * 2  # rough ounces mapping
        payload[7] = cups

        hex_value = payload.hex()
        _LOGGER.info("Starting Grind and Brew with 0x9051 payload: %s", hex_value)
        await self.appliance.client.async_set_erd_value(
            self.appliance, ERD_CCM_GRIND_BREW_SETTINGS, hex_value
        )
