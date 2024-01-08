"""GE Home Sensor Entities - Abstract Fridge"""
import importlib
import sys
import os
import abc
import logging
from typing import Any, Dict, List, Optional

from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.util.unit_conversion import TemperatureConverter
from gehomesdk import (
    ErdCode,
    ErdOnOff,
    ErdFullNotFull,
    FridgeDoorStatus,
    FridgeSetPointLimits,
    FridgeSetPoints,
    FridgeIceBucketStatus,
    IceMakerControlStatus
)
from ...const import DOMAIN
from ..common import GeAbstractWaterHeater
from .const import *

_LOGGER = logging.getLogger(__name__)

class GeAbstractFridge(GeAbstractWaterHeater):
    """Mock a fridge or freezer as a water heater."""

    # These values are from the Fisher & Paykel RF610AA in imperial units
    # They're to be used as hardcoded limits when ErdCode.SETPOINT_LIMITS is unavailable.
    temp_limits = {}
    temp_limits["fridge_min"] = 32
    temp_limits["fridge_max"] = 46
    temp_limits["freezer_min"] = -6
    temp_limits["freezer_max"] = 7

    @property
    def heater_type(self) -> str:
        raise NotImplementedError

    @property
    def turbo_erd_code(self) -> str:
        raise NotImplementedError

    @property
    def turbo_mode(self) -> str:
        raise NotImplementedError

    @property
    def operation_list(self) -> List[str]:
        try:
            return [OP_MODE_NORMAL, OP_MODE_SABBATH, self.turbo_mode]
        except:
            _LOGGER.debug("Turbo mode not supported.")
            return [OP_MODE_NORMAL, OP_MODE_SABBATH]

    @property
    def unique_id(self) -> str:
        return f"{DOMAIN}_{self.serial_number}_{self.heater_type}"

    @property
    def name(self) -> Optional[str]:
        return f"{self.serial_or_mac} {self.heater_type.title()}"

    @property
    def target_temps(self) -> FridgeSetPoints:
        """Get the current temperature settings tuple."""
        return self.appliance.get_erd_value(ErdCode.TEMPERATURE_SETTING)

    @property
    def target_temperature(self) -> int:
        """Return the temperature we try to reach."""
        return getattr(self.target_temps, self.heater_type)

    @property
    def current_temperature(self) -> int:
        """Return the current temperature."""
        try:
            current_temps = self.appliance.get_erd_value(ErdCode.CURRENT_TEMPERATURE)
            current_temp = getattr(current_temps, self.heater_type)
            if current_temp is None:
                _LOGGER.exception(f"{self.name} has None for current_temperature (available: {self.available})!")
            return current_temp
        except:
            _LOGGER.debug("Device doesn't report current temperature.")
            return None

    async def async_set_temperature(self, **kwargs):
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return
        if not self.min_temp <= target_temp <= self.max_temp:
            raise ValueError("Tried to set temperature out of device range")

        if self.heater_type == HEATER_TYPE_FRIDGE:
            new_temp = FridgeSetPoints(fridge=target_temp, freezer=self.target_temps.freezer)
        elif self.heater_type == HEATER_TYPE_FREEZER:
            new_temp = FridgeSetPoints(fridge=self.target_temps.fridge, freezer=target_temp)
        else:
            raise ValueError("Invalid heater_type")

        await self.appliance.async_set_erd_value(ErdCode.TEMPERATURE_SETTING, new_temp)

    @property
    def supported_features(self):
        return GE_FRIDGE_SUPPORT

    @property
    def setpoint_limits(self) -> FridgeSetPointLimits:
        return self.appliance.get_erd_value(ErdCode.SETPOINT_LIMITS)

    @property
    def min_temp(self):
        """Return the minimum temperature if available, otherwise use hardcoded limits."""
        try:
            return getattr(self.setpoint_limits, f"{self.heater_type}_min")
        except:
            _LOGGER.debug("No temperature setpoint limits available. Using hardcoded limits.")
            return TemperatureConverter.convert(self.temp_limits[f"{self.heater_type}_min"], UnitOfTemperature.FAHRENHEIT, self.temperature_unit)

    @property
    def max_temp(self):
        """Return the maximum temperature if available, otherwise use hardcoded limits."""
        try:
            return getattr(self.setpoint_limits, f"{self.heater_type}_max")
        except:
            _LOGGER.debug("No temperature setpoint limits available. Using hardcoded limits.")
            return TemperatureConverter.convert(self.temp_limits[f"{self.heater_type}_max"], UnitOfTemperature.FAHRENHEIT, self.temperature_unit)

    @property
    def current_operation(self) -> str:
        """Get the current operation mode."""
        if self.appliance.get_erd_value(ErdCode.SABBATH_MODE):
            return OP_MODE_SABBATH
        try:
            if self.appliance.get_erd_value(self.turbo_erd_code):
                return self.turbo_mode
        except:
            _LOGGER.debug("Turbo mode not supported.")
        return OP_MODE_NORMAL

    async def async_set_sabbath_mode(self, sabbath_on: bool = True):
        """Set sabbath mode if it's changed"""
        if self.appliance.get_erd_value(ErdCode.SABBATH_MODE) == sabbath_on:
            return
        await self.appliance.async_set_erd_value(ErdCode.SABBATH_MODE, sabbath_on)

    async def async_set_operation_mode(self, operation_mode):
        """Set the operation mode."""
        if operation_mode not in self.operation_list:
            raise ValueError("Invalid operation mode")
        if operation_mode == self.current_operation:
            return
        sabbath_mode = operation_mode == OP_MODE_SABBATH
        await self.async_set_sabbath_mode(sabbath_mode)
        if not sabbath_mode:
            await self.appliance.async_set_erd_value(self.turbo_erd_code, operation_mode == self.turbo_mode)

    @property
    def door_status(self) -> FridgeDoorStatus:
        """Shorthand to get door status."""
        return self.appliance.get_erd_value(ErdCode.DOOR_STATUS)

    @property
    def ice_maker_state_attrs(self) -> Dict[str, Any]:
        """Get state attributes for the ice maker, if applicable."""
        data = {}

        if self.api.has_erd_code(ErdCode.ICE_MAKER_BUCKET_STATUS):
            erd_val: FridgeIceBucketStatus = self.appliance.get_erd_value(ErdCode.ICE_MAKER_BUCKET_STATUS)
            ice_bucket_status = getattr(erd_val, f"state_full_{self.heater_type}")
            if ice_bucket_status != ErdFullNotFull.NA:
                data["ice_bucket"] = self._stringify(ice_bucket_status)

        if self.api.has_erd_code(ErdCode.ICE_MAKER_CONTROL):
            erd_val: IceMakerControlStatus = self.appliance.get_erd_value(ErdCode.ICE_MAKER_CONTROL)
            ice_control_status = getattr(erd_val, f"status_{self.heater_type}")
            if ice_control_status != ErdOnOff.NA:
                data["ice_maker"] = self._stringify(ice_control_status)

        return data

    @property
    def door_state_attrs(self) -> Dict[str, Any]:
        """Get state attributes for the doors."""
        return {}

    @property
    def other_state_attrs(self) -> Dict[str, Any]:
        """Other state attributes for the entity"""
        return {}

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        door_attrs = self.door_state_attrs
        ice_maker_attrs = self.ice_maker_state_attrs
        other_state_attrs = self.other_state_attrs
        return {**door_attrs, **ice_maker_attrs, **other_state_attrs}
