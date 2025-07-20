import logging
from gehomesdk import ErdCode, LaundryMachineState
from ..common import GeErdSwitch

_LOGGER = logging.getLogger(__name__)

class WasherCycleConverter:
    """Converter for the washer's machine state to a switch state."""
    def from_erd_value(self, value: LaundryMachineState) -> bool:
        """
        Get a bool from the ERD value.
        The switch is considered ON if the washer is ready for remote start (RPP).
        """
        if value is None:
            return None
        return value == LaundryMachineState.RPP

    def to_erd_value(self, value: bool) -> LaundryMachineState:
        """
        Get the ERD value from a bool.
        True sends the START command, False sends the PAUSE command.
        """
        return LaundryMachineState.START if value else LaundryMachineState.PAUSE

class GeWasherCycleSwitch(GeErdSwitch):
    """A switch for starting a washer cycle."""

    def __init__(self, api, erd_code: ErdCode = ErdCode.LAUNDRY_MACHINE_STATE):
        super().__init__(api, erd_code, WasherCycleConverter())

    @property
    def unique_id(self) -> str:
        """Return a unique ID for the switch."""
        return f"{super().unique_id}_cycle_switch"

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        # Use a run/pause icon if the washer is running
        try:
            if self.appliance.get_erd_value(self.erd_code) == LaundryMachineState.RUN:
                return "mdi:pause-circle"
        except:
            pass
        return "mdi:play-circle"