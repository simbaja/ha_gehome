"""Clean brew basket binary sensor for Cafe Speciality Grind and Brew.

ERD 0x902C (COFFEE_BREWER_V2_CLEAN_BREW_BASKET)
  b'\\x01' = basket needs cleaning (after brew completes)
  b'\\x00' = basket is clean (basket has been opened since last brew)

The ERD code is not registered in the gehomesdk, so the value is decoded
as raw bytes.  This class interprets the byte value directly.
"""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import EntityCategory

from ..common.ge_erd_binary_sensor import GeErdBinarySensor

ERD_CCM_CLEAN_BREW_BASKET = "0x902C"


class GeCcmCleanBrewBasketBinarySensor(GeErdBinarySensor):
    """Binary sensor that detects when the brew basket needs cleaning."""

    def __init__(self, api):
        super().__init__(
            api,
            erd_code=ERD_CCM_CLEAN_BREW_BASKET,
            erd_override="Clean Brew Basket",
            device_class_override=BinarySensorDeviceClass.PROBLEM,
            entity_category=EntityCategory.DIAGNOSTIC,
        )

    @property
    def is_on(self) -> bool | None:  # type: ignore
        """Return True if the brew basket needs cleaning."""
        try:
            value = self.appliance.get_erd_value(self.erd_code)
        except KeyError:
            return None
        if isinstance(value, (bytes, bytearray)):
            return value == b"\x01"
        return None
