import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from gehomesdk.clients.websocket_client import GeWebsocketClient
from gehomesdk.erd import ErdApplianceType
from .devices import get_appliance_api_type
_LOGGER = logging.getLogger(__name__)


class GeHomeUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage GE Home updates."""

    def __init__(self, hass, entry):
        super().__init__(
            hass,
            _LOGGER,
            name="ge_home",
            update_interval=timedelta(seconds=30),
        )
        self.hass = hass
        self.entry = entry
        self.client: GeWebsocketClient | None = None
        self._appliance_apis = {}

    @property
    def appliance_apis(self):
        return self._appliance_apis

    async def async_setup(self):
        """Initialize the GE SDK client and connect."""
        _LOGGER.debug("Running GeHomeUpdateCoordinator.async_setup()")

        # Build the GE client from the config entry credentials
        username = self.entry.data.get("username")
        password = self.entry.data.get("password")

        if not username or not password:
            _LOGGER.error("Missing GE Home credentials in config entry")
            return False

        self.client = GeWebsocketClient(username=username, password=password)
        await self.client.async_get_credentials()
        await self.client.async_connect()

        self.regenerate_appliance_apis()
        return True

    def regenerate_appliance_apis(self):
        """Rebuild appliance_apis dict, creating API wrappers as needed."""
        if not self.client or not self.client.appliances:
            return

        for jid, appliance in self.client.appliances.items():
            if jid not in self._appliance_apis:
                api_type = get_appliance_api_type(appliance.appliance_type)
                _LOGGER.debug(f"Adding appliance api for {jid} ({appliance.appliance_type})")
                self._appliance_apis[jid] = api_type(appliance)

    async def _async_update_data(self):
        """Called by HA to refresh data."""
        self.regenerate_appliance_apis()
        for api in self._appliance_apis.values():
            api.async_update()
        return self._appliance_apis
