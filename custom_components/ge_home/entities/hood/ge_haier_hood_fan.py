import logging
from typing import Any, List, Optional

from homeassistant.components.fan import FanEntity, FanEntityFeature
from gehomesdk import ErdCodeType

from ...devices import ApplianceApi
from ..common import GeEntity
from .const import FAN_SPEED_MAP, FAN_SPEED_MAP_REVERSE

_LOGGER = logging.getLogger(__name__)

class GeHaierHoodFan(GeEntity, FanEntity):
    """A fan entity for a Haier Hood appliance."""

    def __init__(self, api: ApplianceApi, erd_code: ErdCodeType):
        # Correctly call the parent constructor with ONLY the api object
        super().__init__(api)
        # Store the ERD code on this instance for the other methods to use
        self.erd_code = erd_code

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features. We use preset modes for clearer control."""
        return FanEntityFeature.PRESET_MODE

    @property
    def is_on(self) -> bool:
        """Return True if the fan is on."""
        return self.appliance.get_erd_value(self.erd_code) > 0

    @property
    def preset_modes(self) -> List[str]:
        """Return the list of available preset modes (speeds)."""
        return [mode for mode in FAN_SPEED_MAP if mode != "Off"]

    @property
    def preset_mode(self) -> Optional[str]:
        """Return the current preset mode."""
        speed = self.appliance.get_erd_value(self.erd_code)
        if speed == FAN_SPEED_MAP["Off"]:
            return None
        return FAN_SPEED_MAP_REVERSE.get(speed)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the fan speed."""
        if preset_mode not in self.preset_modes:
            raise ValueError(f"Invalid preset mode: {preset_mode}")

        speed = FAN_SPEED_MAP[preset_mode]
        _LOGGER.debug(f"Setting {self.unique_id} preset mode to {preset_mode} (speed {speed})")
        await self.appliance.async_set_erd_value(self.erd_code, speed)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the fan on, defaulting to the 'Low' speed."""
        _LOGGER.debug(f"Turning on {self.unique_id} to Low speed")
        await self.async_set_preset_mode("Low")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        _LOGGER.debug(f"Turning off {self.unique_id}")
        await self.appliance.async_set_erd_value(self.erd_code, FAN_SPEED_MAP["Off"])

    @property
    def icon(self) -> str:
        return "mdi:fan"