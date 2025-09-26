import logging
from ...entities.common.ge_erd_select import GeErdSelect
from ...erd.haier_hood_converters import HaierHoodFanSpeedConverter

_LOGGER = logging.getLogger(__name__)

class GeHaierHoodFan(GeErdSelect):
    """Haier hood fan speed as a Select entity."""

    def __init__(self, api, erd_code, command_erd_code):
        super().__init__(api, erd_code, HaierHoodFanSpeedConverter())
        self._command_erd_code = command_erd_code

    @property
    def name(self) -> str:
        return f"{self.serial_number} Hood Fan"

    async def async_select_option(self, option: str) -> None:
        """Set the fan speed by writing to the command ERD."""
        _LOGGER.debug(f"Setting hood fan speed to {option} using {self._command_erd_code}")
        if self.current_option != option:
            value = self._converter.from_option_string(option)
            await self.appliance.async_set_erd_value(self._command_erd_code, value)