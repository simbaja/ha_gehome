import logging
from typing import Any
from datetime import timedelta

from gehomesdk import ErdCode, ErdMachineState
from homeassistant.components.button import ButtonEntity
from ..common import GeErdButton

_LOGGER = logging.getLogger(__name__)

class GeDryerCycleButton(GeErdButton):
    """A button to start a dryer cycle."""

    def __init__(self, api):
        super().__init__(api, ErdCode.LAUNDRY_MACHINE_STATE)

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the button."""
        return f"{self.serial_or_mac}_start_cycle_button"

    @property
    def name(self) -> str:
        """Return the name of the button."""
        return f"{self.serial_or_mac} Start Cycle"

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:play-circle"

    @property
    def available(self) -> bool:
        """The button is only available to press if the machine is in Delay Run."""
        try:
            return str(self.appliance.get_erd_value(self.erd_code)) == "Delay Run"
        except:
            return False

    async def async_press(self) -> None:
        """Send the start command by setting the delay time to zero."""
        _LOGGER.debug(f"Sending START command to {self.unique_id}")
        await self.appliance.async_set_erd_value(
            ErdCode.LAUNDRY_REMOTE_DELAY_CONTROL, 
            timedelta(seconds=0)
        )