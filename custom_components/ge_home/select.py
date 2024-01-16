"""GE Home Select Entities"""
import logging
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .devices import ApplianceApi
from .entities import GeErdSelect
from .update_coordinator import GeHomeUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable
):
    """GE Home selects."""
    _LOGGER.debug("Adding GE Home selects")
    coordinator: GeHomeUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    registry = er.async_get(hass)

    @callback
    def async_devices_discovered(apis: list[ApplianceApi]):
        _LOGGER.debug(f"Found {len(apis):d} appliance APIs")
        entities = [
            entity
            for api in apis
            for entity in api.entities
            if isinstance(entity, GeErdSelect)
            and entity.erd_code in api.appliance._property_cache
            if not registry.async_is_registered(entity.entity_id)
        ]
        _LOGGER.debug(f"Found {len(entities):d} unregistered selects")
        async_add_entities(entities)

    #if we're already initialized at this point, call device
    #discovery directly, otherwise add a callback based on the
    #ready signal
    if coordinator.initialized:
        async_devices_discovered(coordinator.appliance_apis.values())
    else:    
        # add the ready signal and register the remove callback
        coordinator.add_signal_remove_callback(
            async_dispatcher_connect(hass, coordinator.signal_ready, async_devices_discovered))
