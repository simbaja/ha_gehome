import logging
from typing import Optional
from gehomesdk.erd.erd_data_type import ErdDataType
from homeassistant.components.number import (
    NumberEntity,
    NumberDeviceClass,
)
from homeassistant.const import TEMP_FAHRENHEIT
from gehomesdk import ErdCodeType, ErdCodeClass
from .ge_erd_entity import GeErdEntity
from ...devices import ApplianceApi

_LOGGER = logging.getLogger(__name__)

class GeErdNumber(GeErdEntity, NumberEntity):
    """GE Entity for numbers"""

    def __init__(
        self, 
        api: ApplianceApi, 
        erd_code: ErdCodeType, 
        erd_override: str = None, 
        icon_override: str = None, 
        device_class_override: str = None,
        uom_override: str = None,
        data_type_override: ErdDataType = None,
        min_value: float = 1,
        max_value: float = 100,
        step_value: float = 1,
        mode: str = "auto"
    ):
        super().__init__(api, erd_code, erd_override, icon_override, device_class_override)
        self._uom_override = uom_override
        self._data_type_override = data_type_override
        self._native_min_value = min_value
        self._native_max_value = max_value
        self._native_step = step_value
        self._mode = mode

    @property
    def native_value(self):
        try:
            value = self.appliance.get_erd_value(self.erd_code)
            return self._convert_value_from_device(value)
        except KeyError:
            return None

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        return self._get_uom()

    @property
    def _data_type(self) -> ErdDataType:
        if self._data_type_override is not None:
            return self._data_type_override

        return self.appliance.get_erd_code_data_type(self.erd_code)

    @property
    def native_min_value(self) -> float:
        return self._convert_value_from_device(self._native_min_value)

    @property
    def native_max_value(self) -> float:
        return self._convert_value_from_device(self._native_max_value)

    @property
    def native_step(self) -> float:
        return self._native_step

    @property
    def mode(self) -> float:
        return self._mode

    def _convert_value_from_device(self, value):
        """Convert to expected data type"""

        if self._data_type == ErdDataType.INT:
            return int(round(value))
        else:
            return value

    def _get_uom(self):
        """Select appropriate units"""
        
        #if we have an override, just use it
        if self._uom_override:
            return self._uom_override

        if self.device_class == NumberDeviceClass.TEMPERATURE:
            #NOTE: it appears that the API only sets temperature in Fahrenheit,
            #so we'll hard code this UOM instead of using the device configured
            #settings
            return TEMP_FAHRENHEIT
        
        return None

    def _get_device_class(self) -> Optional[str]:
        if self._device_class_override:
            return self._device_class_override
        
        if self.erd_code_class in [
            ErdCodeClass.RAW_TEMPERATURE,
            ErdCodeClass.NON_ZERO_TEMPERATURE,
        ]:
            return NumberDeviceClass.TEMPERATURE

        return None

    def _get_icon(self):
        if self.erd_code_class == ErdCodeClass.DOOR:
            if self.state.lower().endswith("open"):
                return "mdi:door-open"
            if self.state.lower().endswith("closed"):
                return "mdi:door-closed"
        return super()._get_icon()

    async def async_set_native_value(self, value):
        """Sets the ERD value, assumes that the data type is correct"""

        if self._data_type == ErdDataType.INT:
            value = int(round(value))

        try:
            await self.appliance.async_set_erd_value(self.erd_code, value) 
        except:
            _LOGGER.warning(f"Could not set {self.name} to {value}")
