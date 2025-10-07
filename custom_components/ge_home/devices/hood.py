from __future__ import annotations
import logging
from typing import List

from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType, ErdOnOff, ErdBrand, GeAppliance
# The direct import of GeHomeUpdateCoordinator has been removed from here to prevent the circular import.
from ..update_coordinator import GeHomeUpdateCoordinator

from .base import ApplianceApi
from ..entities import (
    GeHoodLightLevelSelect,
    GeHoodFanSpeedSelect,
    GeErdTimerSensor,
    GeErdSwitch,
    ErdOnOffBoolConverter,
    # Haier-specific
    GeHaierHoodFan,
    GeHaierHoodLight,
)
from ..erd.haier_hood_codes import (
    ERD_HAIER_HOOD_FAN_STATUS,
    ERD_HAIER_HOOD_LIGHT_STATUS,
    ERD_HAIER_HOOD_FAN_COMMAND,
    ERD_HAIER_HOOD_LIGHT_COMMAND,
)
from ..erd.registry_compat import ensure_haier_hood_handlers_for_appliance

_LOGGER = logging.getLogger(__name__)


class HoodApi(ApplianceApi):
    """API class for Hood objects"""
    APPLIANCE_TYPE = ErdApplianceType.HOOD

    def __init__(self, coordinator: GeHomeUpdateCoordinator, appliance: GeAppliance):
        super().__init__(coordinator, appliance)
        # Determine and store the brand once during initialization
        self._brand = self.try_get_erd_value(ErdCode.BRAND)

    @ApplianceApi.appliance.setter
    def appliance(self, value: GeAppliance):
        """Overrides the base appliance setter to re-apply patches on reconnect."""
        # Call the parent's setter first to update the internal appliance object
        super(HoodApi, HoodApi).appliance.fset(self, value)

        # After the new appliance object is in place, re-apply the patch if it's a Haier hood.
        # This check uses the stored brand, as the new `value` object may not be initialized yet.
        if self._brand == ErdBrand.HEIER_FPA:
            try:
                _LOGGER.debug(f"Re-patching Haier hood handlers for new appliance instance: {value.mac_addr}")
                ensure_haier_hood_handlers_for_appliance(value)
            except Exception:
                _LOGGER.exception("Failed to re-patch Haier hood ERD handlers on reconnect")

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()
        entities: List[Entity] = []

        # Always expose Delay Off if present (GE style)
        entities.append(
            GeErdSwitch(
                self,
                ErdCode.HOOD_DELAY_OFF,
                bool_converter=ErdOnOffBoolConverter(),
                icon_on_override="mdi:power-on",
                icon_off_override="mdi:power-off",
            )
        )

        # Use the stored brand from __init__
        if self._brand == ErdBrand.HEIER_FPA:
            # Haier/F&P hood -- add our direct ERD selects and make sure encoding/decoding is wired
            try:
                ensure_haier_hood_handlers_for_appliance(self.appliance)
            except Exception:
                _LOGGER.exception("Failed to ensure Haier hood ERD handlers")

            entities.extend([
                GeHaierHoodFan(self, ERD_HAIER_HOOD_FAN_STATUS, ERD_HAIER_HOOD_FAN_COMMAND),
                GeHaierHoodLight(self, ERD_HAIER_HOOD_LIGHT_STATUS, ERD_HAIER_HOOD_LIGHT_COMMAND),
            ])
        else:
            # GE/Monogram/etc will keep upstream behavior (availability ERDs)
            try:
                fan_avail = self.try_get_erd_value(ErdCode.HOOD_FAN_SPEED_AVAILABILITY)
                light_avail = self.try_get_erd_value(ErdCode.HOOD_LIGHT_LEVEL_AVAILABILITY)
                timer_avail: ErdOnOff = self.try_get_erd_value(ErdCode.HOOD_TIMER_AVAILABILITY)
            except Exception:
                fan_avail = light_avail = timer_avail = None

            if getattr(fan_avail, "is_available", False):
                entities.append(GeHoodFanSpeedSelect(self, ErdCode.HOOD_FAN_SPEED))

            if getattr(light_avail, "is_available", False):
                entities.append(GeHoodLightLevelSelect(self, ErdCode.HOOD_LIGHT_LEVEL))

            if timer_avail == ErdOnOff.ON:
                entities.append(GeErdTimerSensor(self, ErdCode.HOOD_TIMER))

        return base_entities + entities