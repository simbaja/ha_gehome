"""The ge_home integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, CONF_REGION
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN
from .exceptions import HaAuthError, HaCannotConnect
from .update_coordinator import GeHomeUpdateCoordinator

# Attempt global Haier hood ERD registration; if the running SDK doesn't support it,
# our HoodApi path will fall back to per-appliance patching at runtime.
from .erd import registry_compat  # noqa: F401

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        new[CONF_REGION] = "US"
        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ge_home from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # try to get existing coordinator
    existing: GeHomeUpdateCoordinator | None = dict.get(hass.data[DOMAIN], entry.entry_id)

    coordinator = GeHomeUpdateCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # try to unload the existing coordinator
    try:
        if existing:
            await coordinator.async_reset()
    except Exception:
        _LOGGER.warning("Could not reset existing coordinator.")

    try:
        if not await coordinator.async_setup():
            return False
    except HaCannotConnect as exc:
        raise ConfigEntryNotReady("Could not connect to SmartHQ") from exc
    except HaAuthError as exc:
        raise ConfigEntryAuthFailed("Could not authenticate to SmartHQ") from exc

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, coordinator.shutdown)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: GeHomeUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    ok = await coordinator.async_reset()
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(config_entry.entry_id)
