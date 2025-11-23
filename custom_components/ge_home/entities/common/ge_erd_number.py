import logging
from propcache.api import cached_property
from typing import Optional

from homeassistant.components.number import (
    NumberEntity,
    NumberMode,
    NumberDeviceClass,
)
from homeassistant.const import UnitOfTemperature, EntityCategory
from gehomesdk import ErdCodeType, ErdCodeClass, ErdDataType

from .ge_erd_entity import GeErdEntity
from ...devices import ApplianceApi

_LOGGER = logging.getLogger(__name__)

class GeErdNumber(GeErdEntity, NumberEntity):
    """GE Entity for numbers"""

    def __init__(
        self, 
        api: ApplianceApi, 
        erd_code: ErdCodeType, 
        erd_override: Optional[str] = None, 
        icon_override: Optional[str] = None, 
        device_class_override: Optional[str] = None,
        uom_override: Optional[str] = None,
        data_type_override: Optional[ErdDataType] = None,
        min_value: float = 1,
        max_value: float = 100,
        step_value: float = 1,
        mode: NumberMode = NumberMode.AUTO,
        entity_category: Optional[EntityCategory] = None
    ):
        super().__init__(api, erd_code, erd_override, icon_override, device_class_override, entity_category)
        self._uom_override = uom_override
        self._data_type_override = data_type_override
        self._native_min_value = min_value
        self._native_max_value = max_value
        self._native_step = step_value
        self._mode = mode

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available

    @property
    def native_value(self) -> float | None: # type: ignore
        try:
            value = self.appliance.get_erd_value(self.erd_code)
            return self._convert_value_from_device(value)
        except KeyError:
            return None

    @cached_property
    def native_unit_of_measurement(self) -> Optional[str]:
        return self._get_uom()

    @property
    def _data_type(self) -> ErdDataType:
        if self._data_type_override is not None:
            return self._data_type_override

        return self.appliance.get_erd_code_data_type(self.erd_code)

    @cached_property
    def native_min_value(self) -> float:
        return self._native_min_value

    @cached_property
    def native_max_value(self) -> float:
        return self._native_max_value

    @cached_property
    def native_step(self) -> float:
        return self._native_step

    @cached_property
    def mode(self) -> NumberMode:
        return self._mode
    
    @cached_property
    def device_class(self) -> NumberDeviceClass | None:
        # Use GeEntity’s logic, but adapt to HA’s NumberDeviceClass expectations
        dc = super(GeErdEntity, self).device_class  # call GeEntity version

        if isinstance(dc, str):
            try:
                return NumberDeviceClass(dc)
            except ValueError:
                return None

        return dc    

    def _convert_value_from_device(self, value) -> float | None:
        """Convert to expected data type"""
        try:
            if self._data_type == ErdDataType.INT:
                return float(round(value))
            else:
                return float(value)
        except:
            return None

    def _get_uom(self):
        """Select appropriate units"""
        
        #if we have an override, just use it
        if self._uom_override:
            return self._uom_override

        if self.device_class == NumberDeviceClass.TEMPERATURE:
            #NOTE: it appears that the API only sets temperature in Fahrenheit,
            #so we'll hard code this UOM instead of using the device configured
            #settings
            return UnitOfTemperature.FAHRENHEIT
        
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

    async def async_set_native_value(self, value):
        """Sets the ERD value, assumes that the data type is correct"""

        if self._data_type == ErdDataType.INT:
            value = int(round(value))

        try:
            await self.appliance.async_set_erd_value(self.erd_code, value) 
        except:
            _LOGGER.warning(f"Could not set {self.name} to {value}")
