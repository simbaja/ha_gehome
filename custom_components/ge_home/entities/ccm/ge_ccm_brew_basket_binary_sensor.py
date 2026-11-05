"""Brew basket missing/not locked binary sensor for Cafe Speciality Grind and Brew.

ERD 0x904F (COFFEE_BREWER_V2_BREW_BASKET_MISSING_OR_NOT_LOCKED)
  b'\\x01' = basket missing or not locked (problem state)
  b'\\x00' = basket present and locked (normal state)

The ERD code is not registered in the gehomesdk, so the value is decoded
as raw bytes.  This class interprets the byte value directly.
"""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from ..common.ge_erd_binary_sensor import GeErdBinarySensor

ERD_CCM_BREW_BASKET_MISSING = "0x904F"


class GeCcmBrewBasketMissingBinarySensor(GeErdBinarySensor):
    """Binary sensor that detects when the brew basket is missing or not locked."""

    def __init__(self, api):
        super().__init__(
            api,
            erd_code=ERD_CCM_BREW_BASKET_MISSING,
            erd_override="Brew Basket Missing Or Not Locked",
            device_class_override=BinarySensorDeviceClass.PROBLEM,
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @property
    def is_on(self) -> bool | None:  # type: ignore
        """Return True if the brew basket is missing or not locked."""
        try:
            value = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if isinstance(value, (bytes, bytearray)):
            return value == b"\x01"
        return None
