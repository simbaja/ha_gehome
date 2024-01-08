import logging
from typing import Optional
from gehomesdk.erd.erd_data_type import ErdDataType
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass

from homeassistant.const import UnitOfTemperature
from gehomesdk import ErdCodeType, ErdCodeClass
from .ge_erd_entity import GeErdEntity
from ...devices import ApplianceApi

_LOGGER = logging.getLogger(__name__)

class GeErdSensor(GeErdEntity, SensorEntity):
    """GE Entity for sensors"""

    def __init__(
        self, 
        api: ApplianceApi, 
        erd_code: ErdCodeType, 
        erd_override: str = None, 
        icon_override: str = None, 
        device_class_override: str = None,
        state_class_override: str = None,
        uom_override: str = None,
        data_type_override: ErdDataType = None
    ):
        super().__init__(api, erd_code, erd_override, icon_override, device_class_override)
        self._uom_override = uom_override
        self._state_class_override = state_class_override
        self._data_type_override = data_type_override

    @property
    def native_value(self):
        try:
            value = self.appliance.get_erd_value(self.erd_code)

            # if it's a numeric data type, return it directly            
            if self._data_type in [ErdDataType.INT, ErdDataType.FLOAT]:
                return self._convert_numeric_value_from_device(value)

            # otherwise, return a stringified version
            # TODO: perhaps enhance so that there's a list of variables available
            #       for the stringify function to consume...
            return self._stringify(value, temp_units=self._temp_units)
        except KeyError:
            return None

    @property
    def native_unit_of_measurement(self) -> Optional[str]:
        return self._get_uom()

    @property
    def state_class(self) -> Optional[str]:
        return self._get_state_class()

    @property
    def _data_type(self) -> ErdDataType:
        if self._data_type_override is not None:
            return self._data_type_override

        return self.appliance.get_erd_code_data_type(self.erd_code)

    @property
    def _temp_units(self) -> Optional[str]:
        #based on testing, all API values are in Fahrenheit, so we'll redefine
        #this property to be the configured temperature unit and set the native
        #unit differently
        return self.api.hass.config.units.temperature_unit

        #if self._measurement_system == ErdMeasurementUnits.METRIC:
        #    return UnitOfTemperature.CELSIUS
        #return UnitOfTemperature.FAHRENHEIT

    def _convert_numeric_value_from_device(self, value):
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

        if (
            self.erd_code_class
            in [ErdCodeClass.RAW_TEMPERATURE, ErdCodeClass.NON_ZERO_TEMPERATURE]
            or self.device_class == SensorDeviceClass.TEMPERATURE
        ):
            #NOTE: it appears that the API only sets temperature in Fahrenheit,
            #so we'll hard code this UOM instead of using the device configured
            #settings
            return UnitOfTemperature.FAHRENHEIT
        if (
            self.erd_code_class == ErdCodeClass.BATTERY
            or self.device_class == SensorDeviceClass.BATTERY
        ):
            return "%"
        if self.erd_code_class == ErdCodeClass.PERCENTAGE:
            return "%"
        if self.device_class == SensorDeviceClass.POWER_FACTOR:
            return "%"
        if self.erd_code_class == ErdCodeClass.HUMIDITY:
            return "%"
        if self.erd_code_class == ErdCodeClass.FLOW_RATE:
            #if self._measurement_system == ErdMeasurementUnits.METRIC:
            #    return "lpm"
            return "gpm" 
        if self.erd_code_class == ErdCodeClass.LIQUID_VOLUME:       
            #if self._measurement_system == ErdMeasurementUnits.METRIC:
            #    return "l"
            return "gal"
        return None

    def _get_device_class(self) -> Optional[str]:
        if self._device_class_override:
            return self._device_class_override
        if self.erd_code_class in [
            ErdCodeClass.RAW_TEMPERATURE,
            ErdCodeClass.NON_ZERO_TEMPERATURE,
        ]:
            return SensorDeviceClass.TEMPERATURE
        if self.erd_code_class == ErdCodeClass.BATTERY:
            return SensorDeviceClass.BATTERY
        if self.erd_code_class == ErdCodeClass.POWER:
            return SensorDeviceClass.POWER
        if self.erd_code_class == ErdCodeClass.ENERGY:
            return SensorDeviceClass.ENERGY
        if self.erd_code_class == ErdCodeClass.HUMIDITY:
            return SensorDeviceClass.HUMIDITY

        return None

    def _get_state_class(self) -> Optional[str]:
        if self._state_class_override:
            return self._state_class_override

        if self.device_class in [SensorDeviceClass.TEMPERATURE, SensorDeviceClass.ENERGY]:
            return SensorStateClass.MEASUREMENT
        if self.erd_code_class in [ErdCodeClass.FLOW_RATE, ErdCodeClass.PERCENTAGE, ErdCodeClass.HUMIDITY]:
            return SensorStateClass.MEASUREMENT
        if self.erd_code_class in [ErdCodeClass.LIQUID_VOLUME]:
            return SensorStateClass.TOTAL_INCREASING
        
        return None

    def _get_icon(self):
        if self.erd_code_class == ErdCodeClass.DOOR:
            if self.state.lower().endswith("open"):
                return "mdi:door-open"
            if self.state.lower().endswith("closed"):
                return "mdi:door-closed"
        return super()._get_icon()

    async def set_value(self, value):
        """Sets the ERD value, assumes that the data type is correct"""
        try:
            await self.appliance.async_set_erd_value(self.erd_code, value) 
        except:
            _LOGGER.warning(f"Could not set {self.name} to {value}")