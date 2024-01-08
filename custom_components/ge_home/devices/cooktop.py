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
            cooktop_status: CooktopStatus = self.appliance.get_erd_value(ErdCode.COOKTOP_STATUS)
            cooktop_entities.append(GeErdBinarySensor(self, ErdCode.COOKTOP_STATUS))
            
            for (k, v) in cooktop_status.burners.items():
                if v.exists:
                    prop = self._camel_to_snake(k)
                    cooktop_entities.append(GeErdPropertyBinarySensor(self, ErdCode.COOKTOP_STATUS, prop+".on"))
                    cooktop_entities.append(GeErdPropertyBinarySensor(self, ErdCode.COOKTOP_STATUS, prop+".synchronized"))                    
                    if not v.on_off_only:
                        cooktop_entities.append(GeErdPropertySensor(self, ErdCode.COOKTOP_STATUS, prop+".power_pct", icon_override="mdi:fire", device_class_override=SensorDeviceClass.POWER_FACTOR, data_type_override=ErdDataType.INT))

        return base_entities + cooktop_entities

    def _camel_to_snake(self, s):
        return ''.join(['_'+c.lower() if c.isupper() else c for c in s]).lstrip('_')    
