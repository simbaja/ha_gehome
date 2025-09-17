"""The ge_home integration."""

import logging
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_REGION
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN
from .exceptions import HaAuthError, HaCannotConnect
from .update_coordinator import GeHomeUpdateCoordinator

# === Register custom Haier hood ERD converters with the SDK ===
try:
    # Prefer the object-style registry if available
    try:
        from gehomesdk.erd.erd_value_registry import ERD_VALUE_REGISTRY as _ERD_REG
    except Exception:  # fallback to class-style API
        from gehomesdk.erd.erd_value_registry import ErdValueRegistry as _ERD_REG

    from .erd.haier_hood_codes import (
        ERD_HAIER_HOOD_FAN_SPEED,
        ERD_HAIER_HOOD_LIGHT_LEVEL,
    )
    from .erd.haier_hood_converters import (
        HaierHoodFanSpeedConverter,
        HaierHoodLightLevelConverter,
    )

    # Some SDKs expose .register on the object; some as a @staticmethod on the class.
    if hasattr(_ERD_REG, "register"):
        _ERD_REG.register(ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())
        _ERD_REG.register(ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())
    else:
        # Extremely old SDKs (unlikely), try function style
        from gehomesdk.erd.erd_value_registry import register as _erd_register  # type: ignore
        _erd_register(ERD_HAIER_HOOD_FAN_SPEED, HaierHoodFanSpeedConverter())
        _erd_register(ERD_HAIER_HOOD_LIGHT_LEVEL, HaierHoodLightLevelConverter())
except Exception as _e:
    # Never block integration startup because of registration; we’ll just lack the feature.
    logging.getLogger(__name__).warning(
        "GE Home: Failed to register Haier hood ERD converters: %s", _e
    )

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
    hass.data.setdefault(DOMAIN, {})

    existing: GeHomeUpdateCoordinator = dict.get(hass.data[DOMAIN], entry.entry_id)

    coordinator = GeHomeUpdateCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    try:
        if existing:
            await coordinator.async_reset()
    except Exception:
        _LOGGER.warning("Could not reset existing coordinator.")

    try:
        if not await coordinator.async_setup():
            return False
    except HaCannotConnect:
        raise ConfigEntryNotReady("Could not connect to SmartHQ")
    except HaAuthError:
        raise ConfigEntryAuthFailed("Could not authenticate to SmartHQ")

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, coordinator.shutdown)
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
