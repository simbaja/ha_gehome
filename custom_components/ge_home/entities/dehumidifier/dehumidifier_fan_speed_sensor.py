from typing import Optional
from propcache.api import cached_property

from gehomesdk import ErdCodeType, ErdDataType, ErdAcFanSetting

from ...devices import ApplianceApi
from ..common import GeErdSensor
from .dehumidifier_fan_options import DehumidifierFanSettingOptionsConverter

class GeDehumidifierFanSpeedSensor(GeErdSensor):
    def __init__(
        self, 
        api: ApplianceApi, 
        erd_code: ErdCodeType, 
        erd_override: Optional[str] = None, 
        icon_override: Optional[str] = None, 
        device_class_override: Optional[str] = None,
        state_class_override: Optional[str] = None,
        uom_override: Optional[str] = None,
        data_type_override: Optional[ErdDataType] = None
    ):
    
        super().__init__(
            api, 
            erd_code, 
            erd_override, 
            icon_override, 
            device_class_override,
            state_class_override,
            uom_override,
            data_type_override
        )

        self._converter = DehumidifierFanSettingOptionsConverter()

    @cached_property
    def native_value(self):
        try:
            value: ErdAcFanSetting = self.appliance.get_erd_value(self.erd_code)
            return self._converter.to_option_string(value)
        except KeyError:
            return None

