import logging
from propcache.api import cached_property

from gehomesdk import ErdCode
from ..common import GeErdButton

_LOGGER = logging.getLogger(__name__)

class GeDryerWrinkleCareButton(GeErdButton):
    """A button to start Wrinkle Care (a remote, no-heat extended tumble) on a dryer."""

    def __init__(self, api):
        super().__init__(api, ErdCode.LAUNDRY_DRYER_REMOTE_START_EXTENDED_TUMBLE)

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID for the button."""
        return f"{self.entity_identifier}_wrinkle_care_button"

    @cached_property
    def name(self) -> str:
        """Return the name of the button."""
        return f"{self.entity_identifier} Wrinkle Care"

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:tumble-dryer"

    @property
    def available(self) -> bool:
        """The button is only available if remote control is enabled on the appliance."""
        try:
            return bool(self.appliance.get_erd_value(ErdCode.LAUNDRY_REMOTE_STATUS))
        except:
            return False

    async def async_press(self) -> None:
        """Send START_EXTENDED_TUMBLE (0). The SDK's converter for this ERD is read-only, so send the raw value."""
        _LOGGER.debug(f"Sending WRINKLE CARE command to {self.unique_id}")
        await self.appliance.client.async_set_erd_value(
            self.appliance,
            ErdCode.LAUNDRY_DRYER_REMOTE_START_EXTENDED_TUMBLE,
            "00"
        )
