"""The AC target temperature diagnostic sensor; why it reads the setpoint in either byte order is in
entities/common/ac_temperature.py."""
from typing import Any, Optional

from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from ..common.ac_temperature import normalize_ac_target_temperature
from ..common.ge_erd_sensor import GeErdSensor


class GeAcTargetTemperatureSensor(GeErdSensor):
    """The AC target temperature diagnostic sensor, same entity as before, read in either byte order."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType, **kwargs):
        super().__init__(api, erd_code, **kwargs)

    @property
    def native_value(self) -> Optional[Any]:  # type: ignore
        return normalize_ac_target_temperature(super().native_value)
