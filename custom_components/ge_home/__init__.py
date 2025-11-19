"""The ge_home integration."""

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_REGION, EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from .const import DOMAIN
from .exceptions import HaAuthError, HaCannotConnect
from .update_coordinator import GeHomeUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:

        new = {**config_entry.data}
        new[CONF_REGION] = "US"

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True    


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ge_home from a config entry."""

    coordinators = hass.data.setdefault(DOMAIN, {})  # type: dict[str, GeHomeUpdateCoordinator]

    #try to get existing coordinator
    existing: GeHomeUpdateCoordinator | None = coordinators.get(entry.entry_id)

    # try to unload the existing coordinator
    if existing:
        try:
            _LOGGER.debug("Found existing coordinator, resetting before setup.")
            await existing.async_reset()
        except Exception:
            _LOGGER.warning("Could not reset existing coordinator.", exc_info=True)
        finally:
            coordinators.pop(entry.entry_id, None)

    coordinator = GeHomeUpdateCoordinator(hass, entry)
    coordinators[entry.entry_id] = coordinator

    try:
        if not await coordinator.async_setup():
            return False
    except HaCannotConnect:
        raise ConfigEntryNotReady("Could not connect to SmartHQ")
    except HaAuthError:
        raise ConfigEntryAuthFailed("Could not authenticate to SmartHQ")
    except Exception as exc:
        _LOGGER.exception("Unexpected error during coordinator setup")
        raise ConfigEntryNotReady from exc
            
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, coordinator._shutdown)

    _LOGGER.debug("Coordinator setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    coordinator: GeHomeUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    ok = await coordinator.async_reset()
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return ok


async def async_update_options(hass, config_entry):
    """Update options."""
    await hass.config_entries.async_reload(config_entry.entry_id)
