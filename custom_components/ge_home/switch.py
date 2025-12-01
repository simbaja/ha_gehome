"""GE Home Switch Entities"""
import logging
from collections.abc import Collection
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import entity_registry as er
from homeassistant.components.switch import SwitchEntity

from .entities import GeErdSwitch
from .const import DOMAIN
from .devices import ApplianceApi
from .update_coordinator import GeHomeUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: Callable):
    """GE Home Switches."""
    _LOGGER.debug('Adding GE Home switches')
    coordinator: GeHomeUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    registry = er.async_get(hass)

    @callback
    def async_devices_discovered(apis: Collection[ApplianceApi]):
        """Add new switch entities from the device API."""
        _LOGGER.debug(f'Found {len(apis):d} appliance APIs')
        
        new_entities = []
        for api in apis:
            for entity in api.entities:
                # Skip if the entity is already registered
                if registry.async_is_registered(entity.entity_id):
                    continue

                # Check if it's a switch entity we should add
                if isinstance(entity, SwitchEntity):
                    # Special handling for GeErdSwitch: it requires the erd_code to be in the property cache
                    if isinstance(entity, GeErdSwitch):
                        if entity.erd_code in api.appliance._property_cache:
                            new_entities.append(entity)
                    else:
                        # For other switche types add them directly
                        new_entities.append(entity)

        _LOGGER.debug(f'Found {len(new_entities):d} unregistered switches to register')
        async_add_entities(new_entities)

    # If we're already initialized at this point, call device
    # discovery directly, otherwise add a callback based on the
    # ready signal
    if coordinator.initialized:
        async_devices_discovered(coordinator.appliance_apis.values())
    else:
        # Add the ready signal and register the remove callback
        coordinator.add_signal_remove_callback(
            async_dispatcher_connect(hass, coordinator.signal_ready, async_devices_discovered))