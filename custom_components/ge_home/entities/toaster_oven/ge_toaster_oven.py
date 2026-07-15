"""GE Home water-heater-style entity for toaster ovens."""

import logging
from propcache.api import cached_property
from typing import Any, Dict, List, Optional

from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from gehomesdk import ErdCode

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeAbstractWaterHeater
from .const import (
    GE_TOASTER_OVEN_SUPPORT,
    TOASTER_OVEN_COOK_MODE_MAP,
    TOASTER_OVEN_COOK_MODE_MAP_REVERSE,
)

_LOGGER = logging.getLogger(__name__)


class GeToasterOven(GeAbstractWaterHeater):
    """GE Appliance toaster oven."""

    SETTING_ERD = "0x9207"
    SETTING_CONTROL_ERD = "0x9208"
    DEFAULT_TEMPERATURE = 350
    DEFAULT_COOK_TIME_SECONDS = 600
    MIN_TEMPERATURE = 80
    MAX_TEMPERATURE = 450

    def __init__(self, api: ApplianceApi):
        self._setting_erd = api.appliance.translate_erd_code(self.SETTING_ERD)
        self._setting_control_erd = api.appliance.translate_erd_code(
            self.SETTING_CONTROL_ERD
        )
        self._remote_enabled_erd = api.appliance.translate_erd_code(
            ErdCode.UPPER_OVEN_REMOTE_ENABLED
        )
        super().__init__(api)

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_toaster_oven"

    @cached_property
    def name(self) -> str | None:
        return f"{self.serial_or_mac} Toaster Oven"

    @property
    def icon(self) -> str | None:
        return "mdi:toaster-oven"

    @property
    def heater_type(self) -> str:
        return "toaster_oven"

    @property
    def supported_features(self):
        return GE_TOASTER_OVEN_SUPPORT

    @cached_property
    def temperature_unit(self):
        return UnitOfTemperature.FAHRENHEIT

    @property
    def remote_enabled(self) -> bool:
        try:
            return self.appliance.get_erd_value(self._remote_enabled_erd) == True
        except KeyError:
            return False

    @property
    def current_temperature(self) -> int | None:  # type: ignore
        return None

    @property
    def current_operation(self) -> str | None:  # type: ignore
        setting = self._current_setting
        if setting is None:
            return None
        return TOASTER_OVEN_COOK_MODE_MAP_REVERSE.get(setting["mode"])

    @cached_property
    def operation_list(self) -> List[str]:
        return list(TOASTER_OVEN_COOK_MODE_MAP.keys())

    @property
    def target_temperature(self) -> int | None:  # type: ignore
        setting = self._current_setting
        if setting is None:
            return None
        return setting["temperature"]

    @property
    def min_temp(self) -> int:
        return self.MIN_TEMPERATURE

    @property
    def max_temp(self) -> int:
        return self.MAX_TEMPERATURE

    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:  # type: ignore
        setting = self._current_setting
        if setting is None:
            return None
        return {
            "remote_enabled": self.remote_enabled,
            "cook_time": setting["cook_time"],
        }

    async def async_set_operation_mode(self, operation_mode: str):
        """Set the operation mode."""
        if operation_mode not in TOASTER_OVEN_COOK_MODE_MAP:
            _LOGGER.debug("Unknown toaster oven mode: %s", operation_mode)
            return

        setting = self._current_setting or self._default_setting
        setting["mode"] = TOASTER_OVEN_COOK_MODE_MAP[operation_mode]
        await self._write_setting(setting)

    async def async_set_temperature(self, **kwargs):
        """Set the cook temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return

        setting = self._current_setting or self._default_setting
        setting["temperature"] = max(
            self.min_temp, min(self.max_temp, int(target_temp))
        )
        await self._write_setting(setting)

    @property
    def _current_setting(self) -> Optional[Dict[str, Any]]:
        raw = self.appliance.get_raw_erd_value(self._setting_erd)
        if raw is None:
            return None
        try:
            data = bytes.fromhex(raw)
        except ValueError:
            return None
        if len(data) < 10:
            return None
        return {
            "temperature": int.from_bytes(data[0:4], "big"),
            "cook_time": int.from_bytes(data[4:8], "big"),
            "mode": int.from_bytes(data[8:10], "big"),
            "options": data[10:].hex().upper(),
        }

    @property
    def _default_setting(self) -> Dict[str, Any]:
        return {
            "temperature": self.DEFAULT_TEMPERATURE,
            "cook_time": self.DEFAULT_COOK_TIME_SECONDS,
            "mode": TOASTER_OVEN_COOK_MODE_MAP[self.operation_list[0]],
            "options": "0000",
        }

    async def _write_setting(self, setting: Dict[str, Any]) -> None:
        try:
            options = bytes.fromhex(str(setting.get("options", "0000")))
        except ValueError:
            options = b"\x00\x00"

        payload = (
            int(setting["temperature"]).to_bytes(4, "big")
            + int(setting["cook_time"]).to_bytes(4, "big")
            + int(setting["mode"]).to_bytes(2, "big")
            + options
        ).hex().upper()
        _LOGGER.debug("Setting toaster oven mode to %s", payload)
        await self.appliance.client.async_set_erd_value(
            self.appliance,
            self._setting_control_erd,
            payload,
        )
