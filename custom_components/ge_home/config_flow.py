"""Config flow for GE Home integration."""

import logging
from typing import Dict, Optional

import aiohttp
import asyncio
import async_timeout

from gehomesdk import (
    GeAuthFailedError, 
    GeNotAuthenticatedError, 
    GeGeneralServerError, 
    async_get_oauth2_token,
    LOGIN_REGIONS
)
import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_REGION
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, VALIDATE_DATA_TIMEOUT, CONFIG_FLOW_VERSION
from .exceptions import HaAuthError, HaCannotConnect

_LOGGER = logging.getLogger(__name__)

GEHOME_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str, 
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_REGION): vol.In(LOGIN_REGIONS.keys())
    }
)

def _normalize_username(username: Optional[str]) -> str:
    """Trim whitespace and lowercase the username."""
    if username is None or username.strip() == "":
        raise HaAuthError("Username is required")
    return username.strip().lower()

def _normalize_password(password: Optional[str]) -> str:
    """Trim whitespace from password."""
    if password is None or password.strip() == "":
        raise HaAuthError("Password is required")
    return password.strip()

def _normalize_region(region: Optional[str]) -> str:
    """Ensure valid region."""
    if region is None or not region.upper() in LOGIN_REGIONS.keys():
        raise HaAuthError("Invalid region")
    return region.upper()

def _get_user_schema(user_input: Optional[Dict] = None) -> vol.Schema:
    """Return the user step schema, prefilled with previous input if available."""
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")): str,
            vol.Required(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")): str,
            vol.Required(CONF_REGION, default=user_input.get(CONF_REGION, "")): vol.In(LOGIN_REGIONS.keys())
        }
    )

async def validate_input(hass: core.HomeAssistant, data: dict):
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    username = _normalize_username(data.get(CONF_USERNAME))
    password = _normalize_password(data.get(CONF_PASSWORD))
    region = _normalize_region(data.get(CONF_REGION))

    try:
        async with async_timeout.timeout(VALIDATE_DATA_TIMEOUT):
            await async_get_oauth2_token(session, username, password, region)
    except (asyncio.TimeoutError, aiohttp.ClientError) as err:
        _LOGGER.warning(f"Connection failure for user {username} in region {region}: {err}")
        raise HaCannotConnect("Connection failure")
    except (GeAuthFailedError, GeNotAuthenticatedError):
        _LOGGER.warning(f"Authentication failure for user {username} in region {region}")
        raise HaAuthError("Authentication failure")
    except GeGeneralServerError:
        _LOGGER.warning(f"Server error for user {username} in region {region}")
        raise HaCannotConnect("Cannot connect (server error)")
    except Exception as err:
        _LOGGER.exception(f"Unknown connection failure for user {username} in region {region}")
        raise HaCannotConnect("Unknown connection failure") from err

    return {"title": username.lower()}

class GeHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GE Home."""

    VERSION = CONFIG_FLOW_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_PUSH

    async def _async_validate_input(self, user_input: dict):
        """Map validation to HA-friendly error codes."""
        try:
            info = await validate_input(self.hass, user_input)
            return info, {}
        except HaCannotConnect:
            return None, {"base": "cannot_connect"}
        except HaAuthError:
            return None, {"base": "invalid_auth"}
        except Exception:
            return None, {"base": "unknown"}

    async def async_step_user(self, user_input: Optional[Dict] = None):
        """Handle the initial step."""
        errors = {}

        if user_input:
            username = _normalize_username(user_input.get(CONF_USERNAME))

            # test uniqueness and abort if not unique
            await self.async_set_unique_id(username)
            self._abort_if_unique_id_configured()
        
            try:
                info, errors = await self._async_validate_input(user_input)
                if info:
                    return self.async_create_entry(title=info["title"], data=user_input)

            except Exception as err:
                _LOGGER.exception(f"Unexpected error in user step: {err}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=_get_user_schema(user_input),
            errors=errors
        )

    async def async_step_reauth(self, user_input: Optional[dict] = None):
        """Handle re-auth if login is invalid."""
        errors = {}

        if user_input:
            username = _normalize_username(user_input.get(CONF_USERNAME))
            _, errors = await self._async_validate_input(user_input)

            if not errors:
                for entry in self._async_current_entries():
                    if entry.unique_id == username:
                        self.hass.config_entries.async_update_entry(
                            entry, data=user_input
                        )
                        await self.hass.config_entries.async_reload(entry.entry_id)
                        return self.async_abort(reason="reauth_successful")

            if errors.get("base") != "invalid_auth":
                return self.async_abort(reason=errors.get("base") or "unknown")

        return self.async_show_form(
            step_id="reauth",
            data_schema=_get_user_schema(user_input),
            errors=errors
        )


