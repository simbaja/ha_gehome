import logging
from ...entities.common.ge_erd_select import GeErdSelect
from ...erd.haier_hood_converters import HaierHoodLightLevelConverter

_LOGGER = logging.getLogger(__name__)

class GeHaierHoodLight(GeErdSelect):
    """Haier hood light level as a Select entity."""

    def __init__(self, api, erd_code, command_erd_code):
        super().__init__(api, erd_code, HaierHoodLightLevelConverter())
        self._command_erd_code = command_erd_code

    @property
    def name(self) -> str:
        return f"{self.serial_number} Hood Light"

    async def async_select_option(self, option: str) -> None:
        """Set the light level by writing to the command ERD."""
        _LOGGER.debug(f"Setting hood light level to {option} using {self._command_erd_code}")
        if self.current_option != option:
            value = self._converter.from_option_string(option)
            await self.appliance.async_set_erd_value(self._command_erd_code, value)