import abc
import logging
from propcache.api import cached_property
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from homeassistant.components.water_heater import WaterHeaterEntity
from homeassistant.const import UnitOfTemperature
from gehomesdk import ErdCode, ErdMeasurementUnits
from ...const import DOMAIN
from .ge_erd_entity import GeEntity
from .native_temperature import NATIVE_TEMPERATURES

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
        return f"{DOMAIN}_{self.entity_identifier}_{self.heater_type}"

    @cached_property
    def name(self) -> Optional[str]:
        return f"{self.entity_identifier} {self.heater_type.title()}"

    @cached_property
    def native_temperature_unit(self):
        #It appears that the GE API is alwasy Fehrenheit
        #measurement_system = self.appliance.get_erd_value(ErdCode.TEMPERATURE_UNIT)
        #if measurement_system == ErdMeasurementUnits.METRIC:
        #    return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    # Releases before 2026.11 only read the old names. Type checkers see the
    # 2026.11+ class, where those names are final.
    if not TYPE_CHECKING and not NATIVE_TEMPERATURES:

        @property
        def temperature_unit(self):
            return self.native_temperature_unit

        @property
        def current_temperature(self):
            return self.native_current_temperature

        @property
        def target_temperature(self):
            return self.native_target_temperature

    @property
    def supported_features(self):
        raise NotImplementedError
