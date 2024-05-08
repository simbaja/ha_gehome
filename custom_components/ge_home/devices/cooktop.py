import logging
from typing import List
from gehomesdk.erd.erd_data_type import ErdDataType

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import Entity
from gehomesdk import (
    ErdCode, 
    ErdApplianceType, 
    ErdCooktopConfig, 
    CooktopStatus
)

from .base import ApplianceApi
from ..entities import (
    GeErdBinarySensor, 
    GeErdPropertySensor,
    GeErdPropertyBinarySensor
)

_LOGGER = logging.getLogger(__name__)

class CooktopApi(ApplianceApi):
    """API class for cooktop objects"""
    APPLIANCE_TYPE = ErdApplianceType.COOKTOP

    def get_all_entities(self) -> List[Entity]:
        base_entities = super().get_all_entities()

        cooktop_config = ErdCooktopConfig.NONE
        if self.has_erd_code(ErdCode.COOKTOP_CONFIG):
            cooktop_config: ErdCooktopConfig = self.appliance.get_erd_value(ErdCode.COOKTOP_CONFIG)

        _LOGGER.debug(f"Cooktop Config: {cooktop_config}")
        cooktop_entities = []

        if cooktop_config == ErdCooktopConfig.PRESENT:
            # attempt to get the cooktop status using legacy status
            cooktop_status_erd = ErdCode.COOKTOP_STATUS
            cooktop_status: CooktopStatus = self.try_get_erd_value(ErdCode.COOKTOP_STATUS)

            # if we didn't get it, try using the new version
            if cooktop_status is None:
                cooktop_status_erd = ErdCode.COOKTOP_STATUS_EXT
                cooktop_status: CooktopStatus = self.try_get_erd_value(ErdCode.COOKTOP_STATUS_EXT)

            # if we got a status through either mechanism, we can add the entities
            if cooktop_status is not None:
                cooktop_entities.append(GeErdBinarySensor(self, cooktop_status_erd))
            
                for (k, v) in cooktop_status.burners.items():
                    if v.exists:
                        prop = self._camel_to_snake(k)
                        cooktop_entities.append(GeErdPropertyBinarySensor(self, cooktop_status_erd, prop+".on"))
                        cooktop_entities.append(GeErdPropertyBinarySensor(self, cooktop_status_erd, prop+".synchronized"))                    
                        if not v.on_off_only:
                            cooktop_entities.append(GeErdPropertySensor(self, cooktop_status_erd, prop+".power_pct", icon_override="mdi:fire", device_class_override=SensorDeviceClass.POWER_FACTOR, data_type_override=ErdDataType.INT))

        return base_entities + cooktop_entities

    def _camel_to_snake(self, s):
        return ''.join(['_'+c.lower() if c.isupper() else c for c in s]).lstrip('_')    
