"""GE Home Sensor Entities - Oven"""
import logging
from propcache.api import cached_property
from typing import Any, Dict, List, Optional, Set

from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from gehomesdk import (
    ErdCode,
    ErdMeasurementUnits,
    ErdOvenCookMode,
    OVEN_COOK_MODE_MAP,
    OvenCookSetting
)

from ...const import DOMAIN
from ...devices import ApplianceApi
from ..common import GeAbstractWaterHeater
from .const import *

_LOGGER = logging.getLogger(__name__)

class GeOven(GeAbstractWaterHeater):
    """GE Appliance Oven"""

    def __init__(self, api: ApplianceApi, oven_select: str = UPPER_OVEN, two_cavity: bool = False, temperature_erd_code: str = "RAW_TEMPERATURE"):
        if oven_select not in (UPPER_OVEN, LOWER_OVEN):
            raise ValueError(f"Invalid `oven_select` value ({oven_select})")

        self._oven_select = oven_select
        self._two_cavity = two_cavity
        self._temperature_erd_code = temperature_erd_code
        super().__init__(api)

    @cached_property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_or_mac}_{self.oven_select.lower()}"

    @cached_property
    def name(self) -> str | None:
        if self._two_cavity:
            oven_title = self.oven_select.replace("_", " ").title()
        else:
            oven_title = "Oven"

        return f"{self.serial_or_mac} {oven_title}"

    @property
    def icon(self) -> str | None:
        return "mdi:stove"
    
    @property
    def supported_features(self):
        if self.remote_enabled:
            return GE_OVEN_SUPPORT
        else:
            return SUPPORT_NONE

    @cached_property
    def temperature_unit(self):
        # GE appliances always report temperatures in Fahrenheit regardless of
        # the configured measurement system (and may report METRIC while still
        # sending Fahrenheit), so we hard-code Fahrenheit for them.
        return UnitOfTemperature.FAHRENHEIT

    @property
    def oven_select(self) -> str:
        return self._oven_select

    def get_erd_code(self, suffix: str) -> ErdCode:
        """Return the appropriate ERD code for this oven_select"""
        return ErdCode[f"{self.oven_select}_{suffix}"]

    @property
    def remote_enabled(self) -> bool:
        """Returns whether the oven is remote enabled"""
        value = self.get_erd_value("REMOTE_ENABLED")
        return value == True

    @property
    def current_temperature(self) -> int | None: # type: ignore
        #RAW_TEMPERATURE tracks the cavity more accurately than
        #DISPLAY_TEMPERATURE, so it's preferred when the appliance has it
        #(see constructor).  However, some ovens advertise the raw ERD but
        #never populate it (it stays 0); in that case fall back to
        #DISPLAY_TEMPERATURE so current_temperature isn't stuck at 0.
        current_temp = self.get_erd_value(self._temperature_erd_code)
        if not current_temp and self._temperature_erd_code != "DISPLAY_TEMPERATURE":
            if self.api.has_erd_code(self.get_erd_code("DISPLAY_TEMPERATURE")):
                current_temp = self.get_erd_value("DISPLAY_TEMPERATURE")
        # Kept numeric (not None) for the same reason as target_temperature
        # (#457): consumers float() this value. When there is no reading, fall
        # back to the metric-aware idle placeholder so it shows 0 in the user's
        # unit rather than -17.8C (0F) for metric users.
        return current_temp or self._idle_temperature_placeholder

    @property
    def current_operation(self) -> str | None: # type: ignore
        cook_setting = self.current_cook_setting
        cook_mode = cook_setting.cook_mode
        # TODO: simplify this lookup nonsense somehow
        current_state = OVEN_COOK_MODE_MAP.inverse[cook_mode]
        try:
            return COOK_MODE_OP_MAP[current_state]
        except KeyError:
            _LOGGER.debug(f"Unable to map {current_state} to an operation mode")
            return OP_MODE_COOK_UNK

    @cached_property
    def operation_list(self) -> List[str]:
        #lookup all the available cook modes
        erd_code = self.get_erd_code("AVAILABLE_COOK_MODES")
        cook_modes: Set[ErdOvenCookMode] = self.appliance.get_erd_value(erd_code)
        _LOGGER.debug(f"Available Cook Modes: {cook_modes}")

        #get the extended cook modes and add them to the list
        ext_erd_code = self.get_erd_code("EXTENDED_COOK_MODES")
        ext_cook_modes: Set[ErdOvenCookMode] | None = self.api.try_get_erd_value(ext_erd_code)
        _LOGGER.debug(f"Extended Cook Modes: {ext_cook_modes}")
        if ext_cook_modes:
            cook_modes = cook_modes.union(ext_cook_modes)

        #make sure that we limit them to the list of known codes
        cook_modes = cook_modes.intersection(COOK_MODE_OP_MAP.keys())
        
        _LOGGER.debug(f"Final Cook Modes: {cook_modes}")
        op_modes = [o for o in (COOK_MODE_OP_MAP[c] for c in cook_modes) if o]
        op_modes = [OP_MODE_OFF] + op_modes
        return op_modes

    @property
    def current_cook_setting(self) -> OvenCookSetting:
        """Get the current cook mode."""
        erd_code = self.get_erd_code("COOK_MODE")
        return self.appliance.get_erd_value(erd_code)

    @property
    def _idle_temperature_placeholder(self) -> int:
        """Numeric placeholder for when the oven reports no reading/setpoint.

        target_temperature and current_temperature must stay numeric, never
        None, or downstream consumers that float() them crash (e.g. Google
        Assistant device-state serialization, #457).

        The oven transmits temperatures in Fahrenheit and Home Assistant
        converts to the user's unit, so a raw 0 renders as -17.8C (0F) for
        metric users. Return the Fahrenheit value that renders as 0 in the
        user's configured unit instead: 32F = 0C for a metric locale, 0F for
        an imperial one. This keeps an idle oven showing a clean 0 in the
        user's own unit while staying a real (float-able) number.
        """
        if self.api.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return 32
        return 0

    @property
    def target_temperature(self) -> int | None: # type: ignore
        """Return the temperature we try to reach."""
        cook_mode = self.current_cook_setting
        if cook_mode.temperature:
            return cook_mode.temperature
        # No active setpoint (oven off). Must stay numeric, not None:
        # downstream consumers such as Google Assistant float() this value and
        # crash on None (#457). Use the metric-aware idle placeholder so it
        # shows 0 in the user's unit rather than -17.8C (0F) for metric users.
        return self._idle_temperature_placeholder

    @property
    def min_temp(self) -> int:
        """Return the minimum temperature."""
        min_temp, _ = self.appliance.get_erd_value(ErdCode.OVEN_MODE_MIN_MAX_TEMP)
        return min_temp

    @property
    def max_temp(self) -> int:
        """Return the maximum temperature."""
        _, max_temp = self.appliance.get_erd_value(ErdCode.OVEN_MODE_MIN_MAX_TEMP)
        return max_temp

    async def async_set_operation_mode(self, operation_mode: str):
        """Set the operation mode."""

        erd_cook_mode = COOK_MODE_OP_MAP.inverse[operation_mode]
        # Pick a temperature to set.  If there's not one already set, default to
        # good old 350F.
        if operation_mode == OP_MODE_OFF:
            target_temp = 0
        elif self.target_temperature:
            target_temp = self.target_temperature
        elif self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            target_temp = 350
        else:
            target_temp = 177

        new_cook_mode = OvenCookSetting(OVEN_COOK_MODE_MAP[erd_cook_mode], target_temp)
        erd_code = self.get_erd_code("COOK_MODE")
        await self.appliance.async_set_erd_value(erd_code, new_cook_mode)

    async def async_set_temperature(self, **kwargs):
        """Set the cook temperature"""

        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return

        current_op = self.current_operation
        if current_op is not None and current_op != OP_MODE_OFF:
            erd_cook_mode = COOK_MODE_OP_MAP.inverse[current_op]
        else:
            erd_cook_mode = ErdOvenCookMode.BAKE_NOOPTION

        new_cook_mode = OvenCookSetting(OVEN_COOK_MODE_MAP[erd_cook_mode], target_temp)
        erd_code = self.get_erd_code("COOK_MODE")
        await self.appliance.async_set_erd_value(erd_code, new_cook_mode)

    def get_erd_value(self, suffix: str) -> Any:
        erd_code = self.get_erd_code(suffix)
        return self.appliance.get_erd_value(erd_code)

    def _attr_temperature(self, suffix: str):
        """Convert an oven temperature ERD (Fahrenheit) to the user's unit for
        the state attributes, treating 0 as "no reading".

        Home Assistant unit-converts the numeric current/target fields, but
        attribute values are passed through verbatim, so a raw Fahrenheit
        number (e.g. 167) would otherwise sit unconverted next to the Celsius
        fields. Convert here, mirroring the diagnostic temperature sensors.
        """
        value = self.get_erd_value(suffix)
        if not value:
            return None
        if self.api.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return round((value - 32) * 5 / 9, 1)
        return value

    @property
    def display_state(self) -> Optional[str]:
        erd_code = self.get_erd_code("CURRENT_STATE")
        erd_value = self.appliance.get_erd_value(erd_code)
        return self._stringify(erd_value, temp_units=self.temperature_unit)

    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]: # type: ignore
        probe_present = False
        if self.api.has_erd_code(self.get_erd_code("PROBE_PRESENT")):
            probe_present: bool = self.get_erd_value("PROBE_PRESENT")
        data = {
            "display_state": self.display_state,
            "probe_present": probe_present,
            "display_temperature": self._attr_temperature("DISPLAY_TEMPERATURE"),
        }
        if self.api.has_erd_code(self.get_erd_code("RAW_TEMPERATURE")):
            data["raw_temperature"] = self._attr_temperature("RAW_TEMPERATURE")
        if probe_present:
            data["probe_temperature"] = self._attr_temperature("PROBE_DISPLAY_TEMP")

        elapsed_time = None
        cook_time_remaining = None
        kitchen_timer = None
        delay_time = None
        if self.api.has_erd_code(self.get_erd_code("ELAPSED_COOK_TIME")):
            elapsed_time = self.get_erd_value("ELAPSED_COOK_TIME")
        if self.api.has_erd_code(self.get_erd_code("COOK_TIME_REMAINING")):
            cook_time_remaining = self.get_erd_value("COOK_TIME_REMAINING")
        if self.api.has_erd_code(self.get_erd_code("KITCHEN_TIMER")):
            kitchen_timer = self.get_erd_value("KITCHEN_TIMER")
        if self.api.has_erd_code(self.get_erd_code("DELAY_TIME_REMAINING")):
            delay_time = self.get_erd_value("DELAY_TIME_REMAINING")
        if elapsed_time:
            data["cook_time_elapsed"] = self._stringify(elapsed_time)
        if cook_time_remaining:
            data["cook_time_remaining"] = self._stringify(cook_time_remaining)
        if kitchen_timer:
            data["cook_time_remaining"] = self._stringify(kitchen_timer)
        if delay_time:
            data["delay_time_remaining"] = self._stringify(delay_time)
        return data
