import logging
from ...entities.common.ge_erd_select import GeErdSelect
from ...erd.haier_hood_codes import ERD_HAIER_HOOD_LIGHT_LEVEL
from ...erd.haier_hood_converters import HaierHoodLightLevelConverter

_LOGGER = logging.getLogger(__name__)

class GeHaierHoodLight(GeErdSelect):
    """Haier hood light level as a Select entity."""

    def __init__(self, api, erd_code=ERD_HAIER_HOOD_LIGHT_LEVEL):
        super().__init__(api, erd_code, HaierHoodLightLevelConverter())

    @property
    def name(self) -> str:
        return f"{self.serial_number} 0x5B15"

    async def async_select_option(self, option: str) -> None:
        """Set the light level."""
        # The patched converter should handle encoding, so we use the standard path.
        await super().async_select_option(option)