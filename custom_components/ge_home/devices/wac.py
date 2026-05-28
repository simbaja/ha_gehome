import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk import ErdCode, ErdApplianceType

from .base import ApplianceApi
from ..entities import GeWacClimate, GeErdSensor, GeErdBinarySensor, GeErdSwitch, ErdOnOffBoolConverter

_LOGGER = logging.getLogger(__name__)

# gehomesdk 2026.5 renamed/removed these codes (STATE was renamed,
# POWER's address is now a struct with no scalar replacement). Resolve
# via getattr so this module imports on both pre- and post-2026.5 SDKs.
_DEMAND_RESPONSE_STATE = (
    getattr(ErdCode, "RESOURCE_DEMAND_RESPONSE_STATE", None)
    or getattr(ErdCode, "WAC_DEMAND_RESPONSE_STATE", None)
)
_DEMAND_RESPONSE_POWER = getattr(ErdCode, "WAC_DEMAND_RESPONSE_POWER", None)


class WacApi(ApplianceApi):
    """API class for Window AC objects"""
    APPLIANCE_TYPE = ErdApplianceType.AIR_CONDITIONER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        wac_entities = [
            GeWacClimate(self),
            GeErdSensor(self, ErdCode.AC_TARGET_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.AC_AMBIENT_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.AC_FAN_SETTING, icon_override="mdi:fan", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.AC_OPERATION_MODE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSwitch(self, ErdCode.AC_POWER_STATUS, bool_converter=ErdOnOffBoolConverter(), icon_on_override="mdi:power-on", icon_off_override="mdi:power-off"),
            GeErdBinarySensor(self, ErdCode.AC_FILTER_STATUS, device_class_override="problem", entity_category=EntityCategory.DIAGNOSTIC),
        ]
        if _DEMAND_RESPONSE_STATE is not None:
            wac_entities.append(
                GeErdSensor(self, _DEMAND_RESPONSE_STATE, entity_category=EntityCategory.DIAGNOSTIC)
            )
        if _DEMAND_RESPONSE_POWER is not None:
            wac_entities.append(
                GeErdSensor(self, _DEMAND_RESPONSE_POWER, uom_override="kW", entity_category=EntityCategory.DIAGNOSTIC)
            )
        entities = base_entities + wac_entities
        return entities
        
