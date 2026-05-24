import logging
from typing import List

from homeassistant.const import EntityCategory
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    CooktopStatus,
    ErdCode,
    ErdApplianceType,
    ErdCooktopConfig,
    ErdDataType,
)
from ..entities import (
    GeCooktopStatusBinarySensor,
    GeErdPropertyBinarySensor,
    GeErdPropertySensor,
    GeErdBinarySensor,
    GeErdButton,
    GeErdSensor,
    GeErdTimerSensor
)
from .base import ApplianceApi

_LOGGER = logging.getLogger(__name__)


def build_cooktop_entities(api: ApplianceApi) -> List[Entity]:
    """Create cooktop entities if this appliance reports a cooktop."""

    cooktop_config = ErdCooktopConfig.NONE
    if api.has_erd_code(ErdCode.COOKTOP_CONFIG):
        cooktop_config: ErdCooktopConfig = api.appliance.get_erd_value(
            ErdCode.COOKTOP_CONFIG
        )

    if cooktop_config != ErdCooktopConfig.PRESENT:
        return []

    # attempt to get cooktop status, preferring extended data when present
    cooktop_status_erd = ErdCode.COOKTOP_STATUS_EXT
    cooktop_status: CooktopStatus | None = api.try_get_erd_value(
        ErdCode.COOKTOP_STATUS_EXT
    )

    # if we didn't get it, fall back to the legacy status code
    if cooktop_status is None:
        cooktop_status_erd = ErdCode.COOKTOP_STATUS
        cooktop_status = api.try_get_erd_value(ErdCode.COOKTOP_STATUS)

    # if we got a status through either mechanism, we can add the entities
    if cooktop_status is None:
        return []

    cooktop_entities: List[Entity] = [
        GeCooktopStatusBinarySensor(api, cooktop_status_erd)
    ]

    for burner_name, burner_state in cooktop_status.burners.items():
        if burner_state.exists:
            prop = _camel_to_snake(burner_name)
            cooktop_entities.append(
                GeErdPropertyBinarySensor(api, cooktop_status_erd, prop + ".on")
            )
            cooktop_entities.append(
                GeErdPropertyBinarySensor(
                    api,
                    cooktop_status_erd,
                    prop + ".synchronized",
                    entity_category=EntityCategory.DIAGNOSTIC,
                )
            )
            if not burner_state.on_off_only:
                cooktop_entities.append(
                    GeErdPropertySensor(
                        api,
                        cooktop_status_erd,
                        prop + ".power_pct",
                        icon_override="mdi:fire",
                        device_class_override=SensorDeviceClass.POWER_FACTOR,
                        data_type_override=ErdDataType.INT,
                    )
                )

    # Add cooktop lock status
    if api.has_erd_code(ErdCode.COOKTOP_GAS_VALVE_LOCK_STATUS):
        cooktop_entities.append(
            GeErdBinarySensor(
                api,
                ErdCode.COOKTOP_GAS_VALVE_LOCK_STATUS,
                device_class_override=BinarySensorDeviceClass.LOCK,
                entity_category=EntityCategory.DIAGNOSTIC,
            )
        )

    # Add cooktop lock control
    if api.has_erd_code(ErdCode.COOKTOP_GAS_VALVE_LOCK_CONTROL):
        cooktop_entities.append(
            GeErdButton(
                api,
                ErdCode.COOKTOP_GAS_VALVE_LOCK_CONTROL,
                entity_category=EntityCategory.CONFIG,
            )
        )

    # Add cooktop elapsed cook time
    if api.has_erd_code(ErdCode.COOKTOP_ELAPSED_COOK_TIME):
        cooktop_entities.append(
            GeErdSensor(
                api,
                ErdCode.COOKTOP_ELAPSED_COOK_TIME,
                suggested_uom="h",
            )
        )

    return cooktop_entities


def _camel_to_snake(value: str) -> str:
    return "".join(["_" + c.lower() if c.isupper() else c for c in value]).lstrip("_")


class CooktopApi(ApplianceApi):
    """API class for cooktop objects"""

    APPLIANCE_TYPE = ErdApplianceType.COOKTOP

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()
        cooktop_entities = build_cooktop_entities(self)

        if self.has_erd_code(ErdCode.UPPER_OVEN_KITCHEN_TIMER):
            cooktop_entities.append(
                GeErdTimerSensor(
                    self,
                    ErdCode.UPPER_OVEN_KITCHEN_TIMER,
                    erd_override="cooktop_kitchen_timer",
                    suggested_uom="h",
                )
            )

        return base_entities + cooktop_entities
