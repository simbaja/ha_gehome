import logging
from ...entities.common.ge_erd_select import GeErdSelect
from ...erd.haier_hood_codes import ERD_HAIER_HOOD_FAN_SPEED
from ...erd.haier_hood_converters import HaierHoodFanSpeedConverter

_LOGGER = logging.getLogger(__name__)

class GeHaierHoodFan(GeErdSelect):
    """Haier hood fan speed as a Select entity."""

    def __init__(self, api, erd_code=ERD_HAIER_HOOD_FAN_SPEED):
        super().__init__(api, erd_code, HaierHoodFanSpeedConverter())

    @property
    def name(self) -> str:
        return f"{self.serial_number} 0x5B13"

    async def async_select_option(self, option: str) -> None:
        """Set the fan speed."""
        # The patched converter should handle encoding, so we use the standard path.
        await super().async_select_option(option)