import logging
from ...entities.common.ge_erd_select import GeErdSelect
from ...erd.haier_hood_codes import ERD_HAIER_HOOD_FAN_SPEED
from ...erd.haier_hood_converters import HaierHoodFanSpeedConverter

_LOGGER = logging.getLogger(__name__)

class GeHaierHoodFan(GeErdSelect):
    """Haier hood fan speed as a Select entity, with raw-byte fallback."""

    def __init__(self, api, erd_code=ERD_HAIER_HOOD_FAN_SPEED):
        super().__init__(api, erd_code, HaierHoodFanSpeedConverter())

    @property
    def name(self) -> str:
        return f"{self.serial_number} 0x5B13"

    async def async_select_option(self, option: str) -> None:
        """
        Encode and write directly as raw ERD bytes so this works even when the SDK
        registry doesn't know these custom ERDs.
        """
        try:
            # Convert UI option -> bytes payload
            value_obj = self._converter.from_option_string(option)
            if hasattr(value_obj, "to_bytes"):
                payload = value_obj.to_bytes()
            elif isinstance(value_obj, (bytes, bytearray)):
                payload = bytes(value_obj)
            else:
                # Best effort: ask the converter for bytes if it exposes a helper
                payload = self._converter.to_bytes(value_obj)  # type: ignore[attr-defined]
            await self.appliance.async_set_erd_value_raw(self.erd_code, payload)
        except Exception as e:
            _LOGGER.warning(
                "Haier hood fan: raw write failed (%s), falling back to default set_erd_value", e
            )
            # Fall back to the normal path (uses SDK registry if available)
            await super().async_select_option(option)
