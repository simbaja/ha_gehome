import logging

from homeassistant.components.switch import SwitchEntity

from gehomesdk import ErdCodeType
from ...devices import ApplianceApi
from .ge_erd_binary_sensor import GeErdBinarySensor
from .bool_converter import BoolConverter

_LOGGER = logging.getLogger(__name__)

class GeErdBinarySensorSwitch(GeErdBinarySensor, SwitchEntity):
    """Switch that uses separate ERD codes for reading state and writing control."""
    device_class = "switch"

    def __init__(self, api: ApplianceApi, state_erd_code: ErdCodeType, control_erd_code: ErdCodeType, bool_converter: BoolConverter = BoolConverter(), erd_override: str = None, icon_on_override: str = None, icon_off_override: str = None, device_class_override: str = None):
        # Use the state ERD code for the base initialization (for entity ID, etc.)
        super().__init__(api, state_erd_code, erd_override, icon_on_override, icon_off_override, device_class_override)
        self._state_erd_code = state_erd_code
        self._control_erd_code = control_erd_code
        self._converter = bool_converter

    @property
    def is_on(self) -> bool:
        """Return True if switch is on based on state ERD code."""
        return self._converter.boolify(self.appliance.get_erd_value(self._state_erd_code))


    async def async_turn_on(self, **kwargs):
        """Turn the switch on using control ERD code."""
        _LOGGER.debug(f"Turning on {self.unique_id}")
        await self.appliance.async_set_erd_value(self._control_erd_code, self._converter.true_value())

    async def async_turn_off(self, **kwargs):
        """Turn the switch off using control ERD code."""
        _LOGGER.debug(f"Turning off {self.unique_id}")
        await self.appliance.async_set_erd_value(self._control_erd_code, self._converter.false_value())
