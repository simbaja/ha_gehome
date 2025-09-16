import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .devices import get_appliance_api_type
_LOGGER = logging.getLogger(__name__)

class GeHomeUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage GE Home updates."""

    def __init__(self, hass, client):
        super().__init__(
            hass,
            _LOGGER,
            name="ge_home",
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self._appliance_apis = {}

    @property
    def appliance_apis(self):
        return self._appliance_apis

    async def async_setup(self):
        """Compatibility shim for __init__.py"""
        _LOGGER.debug("Running GeHomeUpdateCoordinator.async_setup()")
        self.regenerate_appliance_apis()
        return True

    def regenerate_appliance_apis(self):
        """Rebuild appliance_apis dict, creating API wrappers as needed."""
        for jid, appliance in self.client.appliances.items():  # FIXED from .keys()
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
