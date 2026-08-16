"""GE Home water-heater-style entity for toaster ovens."""

from gehomesdk import ErdToasterOvenSize
from datetime import timedelta
import logging
from propcache.api import cached_property
from typing import Any, Dict, List, Optional

from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from gehomesdk import ErdCode, ErdToasterOvenCookMode, ToasterOvenCookSetting

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeAbstractWaterHeater
from .const import GE_TOASTER_OVEN_SUPPORT

_LOGGER = logging.getLogger(__name__)

class GeToasterOven(GeAbstractWaterHeater):
    """GE Appliance toaster oven."""

    DEFAULT_TEMPERATURE = 350
    DEFAULT_COOK_TIME_SECONDS = 600
    MIN_TEMPERATURE = 80
    MAX_TEMPERATURE = 450

    def __init__(self, api: ApplianceApi):
        self._setting_erd = api.appliance.translate_erd_code(
            ErdCode.TOASTER_OVEN_COOK_SETTING
        )
        self._setting_control_erd = api.appliance.translate_erd_code(
            ErdCode.TOASTER_OVEN_COOK_SETTING_CONTROL
        )
        self._remote_enabled_erd = api.appliance.translate_erd_code(
            ErdCode.UPPER_OVEN_REMOTE_ENABLED
        )
        super().__init__(api)

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.entity_identifier}_toaster_oven"

    @cached_property
    def name(self) -> str | None:
        return f"{self.entity_identifier} Toaster Oven"

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
        if setting is None or setting.cook_mode is None:
            return None
        return setting.cook_mode.stringify()

    @cached_property
    def operation_list(self) -> List[str]:
        return [m for mode in ErdToasterOvenCookMode if (m := mode.stringify()) is not None]

    @property
    def target_temperature(self) -> int | None:  # type: ignore
        setting = self._current_setting
        if setting is None:
            return None
        return setting.temperature

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
            "cook_time": int(setting.cook_time.total_seconds()),
        }

    async def async_set_operation_mode(self, operation_mode: str):
        """Set the operation mode."""
        mode_name = operation_mode.replace(" ", "_").upper()
        try:
            mode = ErdToasterOvenCookMode[mode_name]
        except KeyError:
            _LOGGER.debug("Unknown toaster oven mode: %s", operation_mode)
            return

        setting = self._current_setting or self._default_setting
        new_setting = setting._replace(cook_mode=mode)
        await self._write_setting(new_setting)

    async def async_set_temperature(self, **kwargs):
        """Set the cook temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return

        target_temp = max(self.min_temp, min(self.max_temp, int(target_temp)))
        setting = self._current_setting or self._default_setting
        new_setting = setting._replace(temperature=target_temp)
        await self._write_setting(new_setting)

    @property
    def _current_setting(self) -> Optional[ToasterOvenCookSetting]:
        try:
            setting = self.appliance.get_erd_value(self._setting_erd)
        except KeyError:
            return None
        if not isinstance(setting, ToasterOvenCookSetting):
            return None
        return setting

    @property
    def _default_setting(self) -> ToasterOvenCookSetting:
        return ToasterOvenCookSetting(
            cook_mode=ErdToasterOvenCookMode.BAKE,
            temperature=self.DEFAULT_TEMPERATURE,
            cook_time=timedelta(seconds=self.DEFAULT_COOK_TIME_SECONDS),
            shade=0,
            size=ErdToasterOvenSize.MEDIUM,
            item_count=0,
            preferences=0,
            raw_string="00" * 12
        )

    async def _write_setting(self, setting: ToasterOvenCookSetting) -> None:
        _LOGGER.debug("Setting toaster oven setting to %s", setting)
        await self.appliance.async_set_erd_value(
            self._setting_control_erd,
            setting,
        )
