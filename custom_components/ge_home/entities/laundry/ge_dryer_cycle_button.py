import logging
from propcache.api import cached_property
from datetime import timedelta

from gehomesdk import ErdCode
from ..common import GeErdButton

_LOGGER = logging.getLogger(__name__)

class GeDryerCycleButton(GeErdButton):
    """A button to start a dryer cycle."""

    def __init__(self, api):
        super().__init__(api, ErdCode.LAUNDRY_MACHINE_STATE)

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID for the button."""
        return f"{self.serial_or_mac}_start_cycle_button"

    @cached_property
    def name(self) -> str:
        """Return the name of the button."""
        return f"{self.serial_or_mac} Start Cycle"

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:play-circle"

    @property
    def available(self) -> bool:
        """The button is only available if remote start is enabled on the appliance."""
        try:
            return self.appliance.get_erd_value(ErdCode.LAUNDRY_REMOTE_STATUS)
        except:
            return False

    async def async_press(self) -> None:
        """Send the start command by setting the delay time to zero."""
        _LOGGER.debug(f"Sending START command to {self.unique_id}")
        await self.appliance.async_set_erd_value(
            ErdCode.LAUNDRY_REMOTE_DELAY_CONTROL, 
            timedelta(seconds=0)
        )