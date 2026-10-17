import logging
from propcache.api import cached_property
from typing import Optional

from homeassistant.components.number import NumberDeviceClass, NumberMode
from homeassistant.const import EntityCategory, UnitOfTemperature, UnitOfTime, UnitOfVolume
from gehomesdk import ErdCodeType, ErdEspressoDrinkParameters, ErdEspressoRange

from ...devices import ApplianceApi
from ..common import GeErdNumber

_LOGGER = logging.getLogger(__name__)

class GeEspressoRangeNumber(GeErdNumber):
    """Number backed by an espresso range ERD (value/min/max), written through its requested ERD"""

    def __init__(
        self,
        api: ApplianceApi,
        erd_code: ErdCodeType,
        requested_erd_code: ErdCodeType,
        erd_override: Optional[str] = None,
        icon_override: Optional[str] = None,
        device_class_override: Optional[str] = None,
        uom_override: Optional[str] = None,
        scale: float = 1,
        step_value: float = 1,
        entity_category: Optional[EntityCategory] = EntityCategory.CONFIG
    ):
        super().__init__(
            api,
            erd_code,
            erd_override=erd_override,
            icon_override=icon_override,
            device_class_override=device_class_override,
            uom_override=uom_override,
            step_value=step_value,
            mode=NumberMode.BOX,
            entity_category=entity_category
        )
        self._requested_erd_code = requested_erd_code
        self._scale = scale

    @property
    def _range(self) -> Optional[ErdEspressoRange]:
        return self.api.try_get_erd_value(self.erd_code)

    @property
    def native_value(self) -> float | None: # type: ignore
        r = self._range
        return r.value / self._scale if r is not None else None

    @property
    def native_min_value(self) -> float: # type: ignore
        r = self._range
        return r.min / self._scale if r is not None else 0

    @property
    def native_max_value(self) -> float: # type: ignore
        r = self._range
        return r.max / self._scale if r is not None else 0

    async def async_set_native_value(self, value):
        try:
            await self.appliance.async_set_erd_value(self._requested_erd_code, int(round(value * self._scale)))
        except:
            _LOGGER.warning(f"Could not set {self.name} to {value}")

_DRINK_FIELDS = {
    "temperature": (NumberDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, 1, "mdi:thermometer"),
    "volume": (NumberDeviceClass.VOLUME, UnitOfVolume.MILLILITERS, 1, "mdi:cup"),
    "grind_time": (NumberDeviceClass.DURATION, UnitOfTime.SECONDS, 0.1, "mdi:grain"),
}

class GeEspressoDrinkNumber(GeErdNumber):
    """One field (temperature, volume or grind time) of a drink's stored parameters"""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, requested_erd_code: ErdCodeType, field: str):
        device_class, uom, step, icon = _DRINK_FIELDS[field]
        super().__init__(
            api,
            erd_code,
            # ESPRESSO_AMERICANO_PARAMETERS -> "Americano"
            erd_override=str(getattr(erd_code, "name", erd_code)).removeprefix("ESPRESSO_").removesuffix("_PARAMETERS"),
            icon_override=icon,
            device_class_override=device_class,
            uom_override=uom,
            step_value=step,
            mode=NumberMode.BOX,
            entity_category=EntityCategory.CONFIG
        )
        self._requested_erd_code = requested_erd_code
        self._field = field

    @staticmethod
    def has_range(api: ApplianceApi, erd_code: ErdCodeType, field: str) -> bool:
        """Drinks report min == max for fields they don't use (e.g. hot water has no grind)"""
        value: Optional[ErdEspressoDrinkParameters] = api.try_get_erd_value(erd_code)
        if value is None:
            return True
        return getattr(value, f"min_{field}") != getattr(value, f"max_{field}")

    @cached_property
    def unique_id(self) -> Optional[str]:
        return f"{super().unique_id}_{self._field}"

    @cached_property
    def name(self) -> Optional[str]:
        return f"{super().name} {self._field.replace('_', ' ').title()}"

    @property
    def _parameters(self) -> Optional[ErdEspressoDrinkParameters]:
        return self.api.try_get_erd_value(self.erd_code)

    @property
    def native_value(self) -> float | None: # type: ignore
        p = self._parameters
        return float(getattr(p, self._field)) if p is not None else None

    @property
    def native_min_value(self) -> float: # type: ignore
        p = self._parameters
        return float(getattr(p, f"min_{self._field}")) if p is not None else 0

    @property
    def native_max_value(self) -> float: # type: ignore
        p = self._parameters
        return float(getattr(p, f"max_{self._field}")) if p is not None else 0

    async def async_set_native_value(self, value):
        p = self._parameters
        if p is None:
            _LOGGER.warning(f"Could not set {self.name}, current parameters unknown")
            return
        # the machine works in whole mL and whole degrees C
        if self._field in ("volume", "temperature"):
            value = int(round(value))
        try:
            await self.appliance.async_set_erd_value(self._requested_erd_code, p._replace(**{self._field: value}))
        except:
            _LOGGER.warning(f"Could not set {self.name} to {value}")
