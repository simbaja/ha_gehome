import logging
from datetime import timedelta
from typing import Optional

from homeassistant.components.number import NumberDeviceClass, NumberMode
from homeassistant.const import EntityCategory, UnitOfTime
from gehomesdk import ErdCodeType

from .ge_erd_number import GeErdNumber
from ...devices import ApplianceApi

_LOGGER = logging.getLogger(__name__)


class GeErdTimerNumber(GeErdNumber):
    """GeErdNumber subclass for timer/timedelta ERDs. Values are displayed and set in minutes."""

    def __init__(
        self,
        api: ApplianceApi,
        erd_code: ErdCodeType,
        erd_override: Optional[str] = None,
        min_value: float = 0,
        max_value: float = 1440,
        step_value: float = 1,
        entity_category: Optional[EntityCategory] = None,
    ):
        super().__init__(
            api,
            erd_code,
            erd_override=erd_override,
            device_class_override=NumberDeviceClass.DURATION,
            uom_override=UnitOfTime.MINUTES,
            min_value=min_value,
            max_value=max_value,
            step_value=step_value,
            mode=NumberMode.BOX,
            entity_category=entity_category,
        )

    def _convert_value_from_device(self, value) -> Optional[float]:
        if value is None:
            return None
        try:
            if isinstance(value, timedelta):
                return float(round(value.total_seconds() / 60))
            return float(round(value))
        except Exception:
            return None

    async def async_set_native_value(self, value: float) -> None:
        td = timedelta(minutes=int(round(value)))
        try:
            await self.appliance.async_set_erd_value(self.erd_code, td)
        except Exception:
            _LOGGER.warning(f"Could not set {self.name} to {value} minutes")
