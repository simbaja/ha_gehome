"""The ge_home integration."""

import logging
import voluptuous as vol
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_USERNAME, CONF_REGION, EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from .const import DOMAIN
from .exceptions import HaAuthError, HaCannotConnect
from .update_coordinator import GeHomeUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entry to the latest schema."""

    old_version: int = config_entry.version
    data: dict[str, Any] = dict(config_entry.data)

    # --- Migrate from version 1 to 2
    if old_version == 1:
        _LOGGER.debug(f"GE Home: Migrating entry {config_entry.entry_id} from v1 to v2")

        # Apply default US region if missing
        data[CONF_REGION] = "US"

        hass.config_entries.async_update_entry(
            config_entry,
            data=data,
            version=2,
        )

        _LOGGER.info(f"GE Home: Migration of entry {config_entry.entry_id} to v2 successful")
        old_version = 2

    # --- Migrate any version 2 to 3
    if old_version == 2:
        _LOGGER.debug(f"GE Home: Migrating entry {config_entry.entry_id} from v{old_version} to v3")

        # Normalize username
        username: str = data[CONF_USERNAME].strip().lower()
        data[CONF_USERNAME] = username

        # Normalize region
        region: str = data[CONF_REGION].strip().upper()
        data[CONF_REGION] = region

        # Determine unique_id
        unique_id: str = (config_entry.unique_id or username).strip().lower()

        # Update entry: data, version, and unique_id in one call
        hass.config_entries.async_update_entry(
            config_entry,
            data=data,
            version=3,
            unique_id=unique_id,
        )

        _LOGGER.info (
            f"GE Home: Migration of entry {config_entry.entry_id} to v3 successful "
            f"(unique_id='{unique_id}')"
        )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ge_home from a config entry."""

    coordinators: dict[str, GeHomeUpdateCoordinator] = hass.data.setdefault(DOMAIN, {})

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
        _LOGGER.exception("Unexpected error during coordinator setup", exc_info=True)
        raise ConfigEntryNotReady from exc
            
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, coordinator.shutdown)

    _LOGGER.debug("Coordinator setup complete")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    coordinator: GeHomeUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    ok = await coordinator.async_reset()
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry):
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)
