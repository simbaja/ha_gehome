"""Grinder missing/not locked binary sensor for Cafe Speciality Grind and Brew.

ERD 0x902B (COFFEE_BREWER_V2_GRINDER_MISSING_OR_NOT_LOCKED)
  b'\\x00' = grinder missing or not locked (problem state)
  b'\\x01' = grinder present and locked (normal state)

Note: the polarity is inverted compared to the brew basket sensor —
a value of 0x00 indicates the problem state here.
"""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from ..common.ge_erd_binary_sensor import GeErdBinarySensor

ERD_CCM_GRINDER_MISSING = "0x902B"


class GeCcmGrinderMissingBinarySensor(GeErdBinarySensor):
    """Binary sensor that detects when the grinder is missing or not locked."""

    def __init__(self, api):
        super().__init__(
            api,
            erd_code=ERD_CCM_GRINDER_MISSING,
            erd_override="Grinder Missing Or Not Locked",
            device_class_override=BinarySensorDeviceClass.PROBLEM,
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @property
    def is_on(self) -> bool | None:  # type: ignore
        """Return True if the grinder is missing or not locked (value is 0x00)."""
        try:
            value = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if isinstance(value, (bytes, bytearray)):
            return value == b"\x00"
        return None
