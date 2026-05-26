import logging
from typing import List

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from gehomesdk.erd import ErdCode, ErdApplianceType

from .base import ApplianceApi
from ..entities import GeSacClimate, GeErdSensor, GeErdSwitch, GeErdSelect, ErdOnOffBoolConverter, GeErdBinarySensor, TurboQuietModeOptionsConverter


_LOGGER = logging.getLogger(__name__)


class BiacApi(ApplianceApi):
    """API class for Built-In AC objects"""
    APPLIANCE_TYPE = ErdApplianceType.BUILT_IN_AIR_CONDITIONER

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        sac_entities = [
            GeSacClimate(self),
            GeErdSensor(self, ErdCode.AC_TARGET_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.AC_AMBIENT_TEMPERATURE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.AC_FAN_SETTING, icon_override="mdi:fan", entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSensor(self, ErdCode.AC_OPERATION_MODE, entity_category=EntityCategory.DIAGNOSTIC),
            GeErdSwitch(self, ErdCode.AC_POWER_STATUS, bool_converter=ErdOnOffBoolConverter(), icon_on_override="mdi:power-on", icon_off_override="mdi:power-off"),
            GeErdBinarySensor(self, ErdCode.AC_FILTER_STATUS, device_class_override=BinarySensorDeviceClass.PROBLEM, entity_category=EntityCategory.DIAGNOSTIC),
        ]

        if self.has_erd_code(ErdCode.AC_TURBO_QUIET_MODE):
            available_modes = self.try_get_erd_value(ErdCode.AC_AVAILABLE_TURBO_QUIET_MODES)
            sac_entities.append(
                GeErdSelect(
                    self,
                    ErdCode.AC_TURBO_QUIET_STATUS,
                    TurboQuietModeOptionsConverter(
                        has_turbo=available_modes.has_turbo if available_modes else True,
                        has_quiet=available_modes.has_quiet if available_modes else True,
                    ),
                    control_erd_code=ErdCode.AC_TURBO_QUIET_MODE,
                    icon_override="mdi:fan-speed-2",
                    entity_category=EntityCategory.CONFIG,
                )
            )

        entities = base_entities + sac_entities
        return entities

