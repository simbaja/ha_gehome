import abc
import logging
from propcache.api import cached_property
from typing import Any, Dict, List, Optional

from homeassistant.components.water_heater import WaterHeaterEntity
from homeassistant.const import UnitOfTemperature
from gehomesdk import ErdCode, ErdMeasurementUnits
from ...const import DOMAIN
from .ge_erd_entity import GeEntity

_LOGGER = logging.getLogger(__name__)

class GeAbstractWaterHeater(GeEntity, WaterHeaterEntity, metaclass=abc.ABCMeta):
    """Mock temperature/operation mode supporting device as a water heater"""

    @property
    def icon(self) ->str | None: # type: ignore
        return super().icon
    
    @property
    def available(self) -> bool: # type: ignore
        return super().available
    
    @property
    def heater_type(self) -> str:
        raise NotImplementedError

    @cached_property
    def operation_list(self) -> List[str]:
        raise NotImplementedError

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_{self.heater_type}"

    @cached_property
    def name(self) -> Optional[str]:
        return f"{self.serial_or_mac} {self.heater_type.title()}"

    @cached_property
    def temperature_unit(self):
        #It appears that the GE API is alwasy Fehrenheit
        #measurement_system = self.appliance.get_erd_value(ErdCode.TEMPERATURE_UNIT)
        #if measurement_system == ErdMeasurementUnits.METRIC:
        #    return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def supported_features(self):
        raise NotImplementedError
